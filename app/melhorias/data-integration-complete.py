# app/services/data_preparation_service.py
"""
Serviço de preparação e integração de dados reais do ONS
Conecta com a pasta data/ e prepara dados para ML e contexto do agente
"""

import pandas as pd
import numpy as np
from pathlib import Path
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import asyncio
import psycopg2
from sqlalchemy import create_engine, text

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ONSDataPreparation:
    """
    Classe para preparar dados reais do ONS para ML e contexto do agente
    """
    
    def __init__(self, data_dir: str = "data/dados_ons"):
        self.data_dir = Path(data_dir)
        self.processed_dir = Path("data/processed")
        self.processed_dir.mkdir(exist_ok=True)
        
        # Mapeamento dos arquivos baixados
        self.data_mapping = {
            'carga_energia': {
                'files': ['carga-mensal.csv', 'carga-diaria.csv', 'curva-carga.csv'],
                'key_columns': ['id_subsistema', 'nom_subsistema', 'din_instante', 'val_cargaenergiamwmed'],
                'description': 'Dados de consumo/carga de energia por subsistema'
            },
            'cmo': {
                'files': ['cmo-semanal.csv', 'cmo-semi-horario.csv'],
                'key_columns': ['id_subsistema', 'val_cmomediasemanal', 'val_cmoleve', 'val_cmomedia', 'val_cmopesada'],
                'description': 'Custo Marginal de Operação - preço da energia'
            },
            'bandeiras': {
                'files': ['dm-bandeira-tarifaria-acionamento.csv'],
                'key_columns': ['DatCompetencia', 'NomBandeiraAcionada', 'VlrAdicionalBandeira'],
                'description': 'Histórico de bandeiras tarifárias'
            }
        }
        
        # Conhecimento do domínio para o agente
        self.domain_knowledge = self._load_domain_knowledge()
    
    def _load_domain_knowledge(self) -> Dict:
        """
        Carrega conhecimento específico do setor elétrico
        """
        return {
            "subsistemas": {
                "SE/CO": "Sudeste/Centro-Oeste - maior consumidor, 60% da carga nacional",
                "Sul": "Sul - forte presença de hidrelétricas e eólicas",
                "NE": "Nordeste - crescimento em solar e eólica",
                "Norte": "Norte - abundância hídrica, Belo Monte"
            },
            "conceitos": {
                "MWmed": "Megawatt médio - potência média em um período",
                "MWh": "Megawatt-hora - energia consumida/gerada",
                "CMO": "Custo Marginal de Operação - custo para produzir 1 MWh adicional",
                "PLD": "Preço de Liquidação das Diferenças - preço spot da energia",
                "Bandeira Verde": "Condições favoráveis, sem custo adicional",
                "Bandeira Amarela": "Condições menos favoráveis, adicional moderado",
                "Bandeira Vermelha": "Condições críticas, adicional alto"
            },
            "padroes": {
                "pico_consumo": "18h-21h dias úteis",
                "vale_consumo": "23h-5h e fins de semana",
                "sazonalidade": "Maior consumo no verão (ar condicionado) e inverno (aquecimento Sul)",
                "correlacoes": {
                    "temperatura_carga": 0.65,
                    "chuva_cmo": -0.72,
                    "reservatorio_bandeira": -0.83
                }
            },
            "limites_criticos": {
                "reservatorio_minimo": 20,  # %
                "cmo_alto": 200,  # R$/MWh
                "carga_maxima_historica": 100000  # MW
            }
        }
    
    def load_and_prepare_ons_data(self, dataset_type: str = 'carga_energia') -> pd.DataFrame:
        """
        Carrega e prepara dados reais do ONS
        """
        logger.info(f"Carregando dados ONS: {dataset_type}")
        
        if dataset_type not in self.data_mapping:
            raise ValueError(f"Dataset {dataset_type} não reconhecido")
        
        dataset_info = self.data_mapping[dataset_type]
        dfs = []
        
        # Carregar todos os arquivos do dataset
        for file_name in dataset_info['files']:
            file_path = self.data_dir / file_name
            
            if file_path.exists():
                logger.info(f"  Lendo {file_name}...")
                try:
                    df = pd.read_csv(file_path, encoding='utf-8')
                    dfs.append(df)
                except Exception as e:
                    logger.warning(f"  Erro ao ler {file_name}: {e}")
                    # Tentar com encoding alternativo
                    try:
                        df = pd.read_csv(file_path, encoding='latin-1')
                        dfs.append(df)
                    except:
                        continue
        
        if not dfs:
            logger.warning(f"Nenhum arquivo encontrado para {dataset_type}, gerando dados sintéticos")
            return self._generate_synthetic_data(dataset_type)
        
        # Combinar dataframes
        combined_df = pd.concat(dfs, ignore_index=True)
        
        # Processar conforme tipo de dataset
        if dataset_type == 'carga_energia':
            combined_df = self._process_carga_energia(combined_df)
        elif dataset_type == 'cmo':
            combined_df = self._process_cmo(combined_df)
        elif dataset_type == 'bandeiras':
            combined_df = self._process_bandeiras(combined_df)
        
        logger.info(f"Dados carregados: {combined_df.shape[0]} registros, {combined_df.shape[1]} colunas")
        
        return combined_df
    
    def _process_carga_energia(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Processa dados de carga de energia
        """
        # Padronizar nomes de colunas
        column_mapping = {
            'din_instante': 'timestamp',
            'nom_subsistema': 'subsystem',
            'val_cargaenergiamwmed': 'load_mw',
            'id_subsistema': 'subsystem_id'
        }
        
        df = df.rename(columns={k: v for k, v in column_mapping.items() if k in df.columns})
        
        # Converter timestamp
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        
        # Validar conforme regras ONS
        if 'load_mw' in df.columns:
            # Carga não pode ser negativa ou zero (conforme documentação ONS)
            df = df[df['load_mw'] > 0]
        
        # Adicionar features temporais
        if 'timestamp' in df.columns:
            df['year'] = df['timestamp'].dt.year
            df['month'] = df['timestamp'].dt.month
            df['day'] = df['timestamp'].dt.day
            df['hour'] = df['timestamp'].dt.hour
            df['weekday'] = df['timestamp'].dt.weekday
            df['is_weekend'] = df['weekday'].isin([5, 6]).astype(int)
            
            # Identificar patamares de carga (conforme ONS)
            df['load_level'] = pd.cut(
                df['hour'],
                bins=[0, 7, 18, 21, 24],
                labels=['madrugada', 'dia', 'ponta', 'noite'],
                include_lowest=True
            )
        
        return df
    
    def _process_cmo(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Processa dados de CMO
        """
        column_mapping = {
            'din_instante': 'timestamp',
            'nom_subsistema': 'subsystem',
            'val_cmomediasemanal': 'cmo_avg',
            'val_cmoleve': 'cmo_light',
            'val_cmomedia': 'cmo_medium',
            'val_cmopesada': 'cmo_heavy'
        }
        
        df = df.rename(columns={k: v for k, v in column_mapping.items() if k in df.columns})
        
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        
        # CMO pode ter valores negativos (conforme documentação ONS)
        # mas vamos sinalizar valores anômalos
        cmo_cols = ['cmo_avg', 'cmo_light', 'cmo_medium', 'cmo_heavy']
        for col in cmo_cols:
            if col in df.columns:
                df[f'{col}_anomaly'] = (df[col] < 0) | (df[col] > 1000)
        
        return df
    
    def _process_bandeiras(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Processa dados de bandeiras tarifárias
        """
        column_mapping = {
            'DatCompetencia': 'timestamp',
            'NomBandeiraAcionada': 'flag_name',
            'VlrAdicionalBandeira': 'additional_cost'
        }
        
        df = df.rename(columns={k: v for k, v in column_mapping.items() if k in df.columns})
        
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        
        # Mapear bandeiras para valores numéricos (para ML)
        if 'flag_name' in df.columns:
            flag_mapping = {
                'Verde': 0,
                'Amarela': 1,
                'Vermelha Patamar 1': 2,
                'Vermelha Patamar 2': 3
            }
            df['flag_level'] = df['flag_name'].map(flag_mapping)
        
        return df
    
    def _generate_synthetic_data(self, dataset_type: str) -> pd.DataFrame:
        """
        Gera dados sintéticos realistas quando não há dados reais
        """
        logger.info(f"Gerando dados sintéticos para {dataset_type}")
        
        # Gerar série temporal
        dates = pd.date_range(start='2023-01-01', end='2024-12-31', freq='H')
        subsystems = ['SE/CO', 'Sul', 'NE', 'Norte']
        
        data = []
        for date in dates[:5000]:  # Limitar para teste
            for subsystem in subsystems:
                if dataset_type == 'carga_energia':
                    # Padrão de carga realista
                    base_load = {'SE/CO': 40000, 'Sul': 15000, 'NE': 12000, 'Norte': 3000}[subsystem]
                    
                    # Variação sazonal
                    seasonal = np.sin(2 * np.pi * date.dayofyear / 365) * 0.15
                    
                    # Variação diária
                    daily = np.sin(2 * np.pi * (date.hour - 6) / 24) * 0.2
                    
                    # Pico no horário de ponta
                    if 18 <= date.hour <= 21:
                        daily += 0.15
                    
                    # Fim de semana
                    weekend_factor = 0.85 if date.weekday() >= 5 else 1.0
                    
                    load = base_load * (1 + seasonal + daily) * weekend_factor
                    load += np.random.normal(0, base_load * 0.02)  # Ruído
                    
                    data.append({
                        'timestamp': date,
                        'subsystem': subsystem,
                        'load_mw': max(0, load),
                        'temperature': 20 + 10 * seasonal + np.random.normal(0, 2)
                    })
                    
                elif dataset_type == 'cmo':
                    # CMO inversamente proporcional à disponibilidade hídrica
                    base_cmo = 150
                    seasonal_factor = 1 - seasonal  # Inverso da carga
                    cmo = base_cmo * (1 + seasonal_factor * 0.5)
                    
                    data.append({
                        'timestamp': date,
                        'subsystem': subsystem,
                        'cmo_avg': max(0, cmo + np.random.normal(0, 10)),
                        'cmo_light': max(0, cmo * 0.8),
                        'cmo_medium': max(0, cmo),
                        'cmo_heavy': max(0, cmo * 1.3)
                    })
        
        return pd.DataFrame(data)
    
    def prepare_ml_dataset(self) -> pd.DataFrame:
        """
        Prepara dataset completo para ML combinando todas as fontes
        """
        logger.info("Preparando dataset completo para ML")
        
        # Carregar datasets
        carga_df = self.load_and_prepare_ons_data('carga_energia')
        cmo_df = self.load_and_prepare_ons_data('cmo')
        
        # Merge datasets
        if not carga_df.empty and not cmo_df.empty:
            # Agregar CMO para match com carga (diferentes frequências)
            if 'timestamp' in cmo_df.columns:
                cmo_df['date'] = cmo_df['timestamp'].dt.date
                cmo_daily = cmo_df.groupby(['date', 'subsystem']).agg({
                    'cmo_avg': 'mean',
                    'cmo_light': 'mean',
                    'cmo_medium': 'mean',
                    'cmo_heavy': 'mean'
                }).reset_index()
                
                carga_df['date'] = carga_df['timestamp'].dt.date
                
                ml_df = pd.merge(
                    carga_df,
                    cmo_daily,
                    on=['date', 'subsystem'],
                    how='left'
                )
            else:
                ml_df = carga_df
        else:
            ml_df = carga_df if not carga_df.empty else cmo_df
        
        # Feature engineering específico do domínio
        ml_df = self._add_domain_features(ml_df)
        
        # Salvar dataset processado
        output_path = self.processed_dir / 'ml_dataset.csv'
        ml_df.to_csv(output_path, index=False)
        logger.info(f"Dataset ML salvo em {output_path}")
        
        return ml_df
    
    def _add_domain_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Adiciona features baseadas em conhecimento do domínio elétrico
        """
        if df.empty:
            return df
        
        # Eficiência operacional (relação carga/custo)
        if 'load_mw' in df.columns and 'cmo_avg' in df.columns:
            df['operational_efficiency'] = df['load_mw'] / (df['cmo_avg'] + 1)
        
        # Stress do sistema (carga como % da capacidade)
        if 'load_mw' in df.columns and 'subsystem' in df.columns:
            capacity = {
                'SE/CO': 50000,
                'Sul': 20000,
                'NE': 15000,
                'Norte': 5000
            }
            df['system_stress'] = df.apply(
                lambda x: x['load_mw'] / capacity.get(x['subsystem'], 30000),
                axis=1
            )
        
        # Indicador de criticidade
        if 'system_stress' in df.columns:
            df['criticality'] = pd.cut(
                df['system_stress'],
                bins=[0, 0.6, 0.8, 0.9, 1.0, 2.0],
                labels=['baixa', 'normal', 'atencao', 'critica', 'emergencia']
            )
        
        return df
    
    def generate_context_for_agent(self, current_data: Dict) -> str:
        """
        Gera contexto rico para o agente IA entender o domínio
        """
        context = []
        
        # Conhecimento base
        context.append("CONHECIMENTO DO SETOR ELÉTRICO BRASILEIRO:")
        context.append(json.dumps(self.domain_knowledge, indent=2, ensure_ascii=False))
        
        # Dados atuais
        if current_data:
            context.append("\nSITUAÇÃO ATUAL DO SISTEMA:")
            
            if 'load_mw' in current_data:
                load = current_data['load_mw']
                context.append(f"- Carga atual: {load:.0f} MW")
                
                # Interpretar carga
                if load > 80000:
                    context.append("  ⚠️ ALERTA: Carga muito alta, próxima ao limite")
                elif load > 70000:
                    context.append("  ⚡ Carga elevada, sistema sob pressão")
                else:
                    context.append("  ✅ Carga dentro da normalidade")
            
            if 'cmo_avg' in current_data:
                cmo = current_data['cmo_avg']
                context.append(f"- CMO médio: R$ {cmo:.2f}/MWh")
                
                # Interpretar CMO
                if cmo > 300:
                    context.append("  🔴 CMO muito alto - escassez hídrica severa")
                elif cmo > 200:
                    context.append("  🟡 CMO elevado - acionamento térmico significativo")
                else:
                    context.append("  🟢 CMO normal - condições hídricas favoráveis")
            
            if 'subsystem' in current_data:
                subsystem = current_data['subsystem']
                context.append(f"- Subsistema: {subsystem}")
                context.append(f"  {self.domain_knowledge['subsistemas'].get(subsystem, '')}")
        
        # Recomendações baseadas no contexto
        context.append("\nRECOMENDAÇÕES CONTEXTUALIZADAS:")
        
        if current_data.get('system_stress', 0) > 0.8:
            context.append("- Sistema sob stress: considerar medidas de redução de demanda")
        
        if current_data.get('cmo_avg', 0) > 200:
            context.append("- CMO alto: provável acionamento de bandeira vermelha")
        
        if current_data.get('hour', 0) in range(18, 22):
            context.append("- Horário de ponta: consumo deve ser minimizado")
        
        return "\n".join(context)
    
    def save_to_database(self, df: pd.DataFrame, table_name: str = 'ml_training_data'):
        """
        Salva dados processados no banco PostgreSQL
        """
        try:
            # Usar configurações do .env
            engine = create_engine('postgresql://aide_user:aide_secure_password@localhost:5432/aide_db')
            
            df.to_sql(
                table_name,
                engine,
                if_exists='replace',
                index=False,
                method='multi'
            )
            
            logger.info(f"Dados salvos na tabela {table_name}")
            
        except Exception as e:
            logger.error(f"Erro ao salvar no banco: {e}")
            # Fallback para CSV
            fallback_path = self.processed_dir / f"{table_name}.csv"
            df.to_csv(fallback_path, index=False)
            logger.info(f"Dados salvos em CSV: {fallback_path}")


# Função auxiliar para executar o download de dados ONS
async def download_ons_data():
    """
    Executa o script de download de dados ONS
    """
    import subprocess
    
    try:
        # Executar script de download
        result = subprocess.run(
            ['python', 'data/download_dados.py'],
            capture_output=True,
            text=True,
            timeout=300  # 5 minutos timeout
        )
        
        if result.returncode == 0:
            logger.info("Download de dados ONS concluído com sucesso")
            return True
        else:
            logger.error(f"Erro no download: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error("Timeout no download de dados")
        return False
    except Exception as e:
        logger.error(f"Erro ao executar download: {e}")
        return False


# Função principal para preparar tudo
async def prepare_complete_dataset():
    """
    Função principal que baixa e prepara todos os dados
    """
    logger.info("=" * 60)
    logger.info("INICIANDO PREPARAÇÃO COMPLETA DE DADOS")
    logger.info("=" * 60)
    
    # 1. Baixar dados do ONS (se necessário)
    data_dir = Path("data/dados_ons")
    if not data_dir.exists() or len(list(data_dir.glob("*.csv"))) < 3:
        logger.info("Baixando dados do ONS...")
        success = await download_ons_data()
        if not success:
            logger.warning("Download falhou, usando dados sintéticos")
    
    # 2. Preparar dados
    prep_service = ONSDataPreparation()
    
    # 3. Criar dataset ML
    ml_dataset = prep_service.prepare_ml_dataset()
    
    # 4. Salvar no banco
    prep_service.save_to_database(ml_dataset)
    
    # 5. Gerar contexto exemplo
    sample_data = {
        'load_mw': 72000,
        'cmo_avg': 180,
        'subsystem': 'SE/CO',
        'hour': 15,
        'system_stress': 0.75
    }
    
    context = prep_service.generate_context_for_agent(sample_data)
    
    logger.info("\n" + "=" * 60)
    logger.info("CONTEXTO GERADO PARA O AGENTE:")
    logger.info("=" * 60)
    print(context)
    
    return ml_dataset, context


if __name__ == "__main__":
    # Executar preparação completa
    asyncio.run(prepare_complete_dataset())
