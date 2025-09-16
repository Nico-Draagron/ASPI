"""
services/ons_service.py
Serviço de integração com a API do ONS (Operador Nacional do Sistema)
"""

import aiohttp
import asyncio
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging
import json
from functools import lru_cache
import hashlib
from urllib.parse import urljoin, urlencode
import xml.etree.ElementTree as ET
from io import StringIO, BytesIO
import zipfile
import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from models.database import Dataset, DataRecord, CargaEnergia, CMO
from app.config import get_config

# Configuração de logging
logger = logging.getLogger(__name__)
config = get_config()

@dataclass
class ONSDataset:
    """Dataset do ONS"""
    id: str
    name: str
    description: str
    url: str
    format: str  # json, csv, xml, zip
    update_frequency: str
    last_update: Optional[datetime] = None
    fields: Optional[List[Dict]] = None

@dataclass
class ONSResponse:
    """Resposta da API ONS"""
    success: bool
    data: Optional[Any]
    metadata: Dict[str, Any]
    error: Optional[str] = None
    raw_response: Optional[str] = None

class ONSService:
    """Serviço de integração com ONS"""
    
    # URLs base conhecidas do ONS
    BASE_URLS = {
        'api': 'https://dados.ons.org.br/api/v1/',
        'portal': 'https://dados.ons.org.br/',
        'sintegre': 'https://sintegre.ons.org.br/',
        'historico': 'http://www.ons.org.br/historico/'
    }
    
    # Endpoints específicos
    ENDPOINTS = {
        'carga_energia': {
            'diaria': 'carga_energia/diaria',
            'horaria': 'carga_energia/horaria',
            'mensal': 'carga_energia/mensal',
            'curva_carga': 'curva_carga'
        },
        'cmo_pld': {
            'semanal': 'cmo/semanal',
            'semi_horario': 'cmo/semi_horario',
            'pld': 'pld/horario'
        },
        'bandeiras': {
            'acionamento': 'bandeiras_tarifarias/acionamento',
            'historico': 'bandeiras_tarifarias/historico'
        },
        'geracao': {
            'usina': 'geracao/usina',
            'fonte': 'geracao/fonte',
            'verificada': 'geracao/verificada'
        },
        'reservatorios': {
            'energia_armazenada': 'reservatorios/energia_armazenada',
            'volume_util': 'reservatorios/volume_util'
        },
        'intercambio': {
            'verificado': 'intercambio/verificado',
            'limites': 'intercambio/limites'
        }
    }
    
    def __init__(self):
        """Inicializa o serviço ONS"""
        self.api_key = config.ons.api_key
        self.base_url = config.ons.base_url
        self.timeout = config.ons.timeout
        self.batch_size = config.ons.batch_size
        
        # Headers padrão
        self.headers = {
            'Accept': 'application/json',
            'User-Agent': 'AIDE-System/1.0',
            'X-API-Key': self.api_key
        }
        
        # Cache de datasets
        self.datasets_cache = {}
        self.cache_ttl = 3600  # 1 hora
        
    # =================== Métodos Principais ===================
    
    async def fetch_dataset(self,
                          dataset_id: str,
                          start_date: Optional[datetime] = None,
                          end_date: Optional[datetime] = None,
                          **kwargs) -> ONSResponse:
        """
        Busca dados de um dataset específico
        
        Args:
            dataset_id: ID do dataset
            start_date: Data inicial
            end_date: Data final
            **kwargs: Parâmetros adicionais
            
        Returns:
            Resposta com os dados
        """
        try:
            # Determinar endpoint
            endpoint = self._get_endpoint(dataset_id)
            if not endpoint:
                return ONSResponse(
                    success=False,
                    data=None,
                    metadata={},
                    error=f"Dataset {dataset_id} não encontrado"
                )
            
            # Preparar parâmetros
            params = self._prepare_params(start_date, end_date, **kwargs)
            
            # Fazer requisição
            async with aiohttp.ClientSession() as session:
                url = urljoin(self.base_url, endpoint)
                
                async with session.get(
                    url,
                    params=params,
                    headers=self.headers,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    
                    if response.status == 200:
                        # Processar resposta baseado no formato
                        content_type = response.headers.get('Content-Type', '')
                        
                        if 'json' in content_type:
                            data = await response.json()
                        elif 'csv' in content_type:
                            text = await response.text()
                            data = self._parse_csv(text)
                        elif 'xml' in content_type:
                            text = await response.text()
                            data = self._parse_xml(text)
                        else:
                            data = await response.read()
                        
                        # Processar dados específicos do dataset
                        processed_data = self._process_dataset_data(dataset_id, data)
                        
                        return ONSResponse(
                            success=True,
                            data=processed_data,
                            metadata={
                                'dataset_id': dataset_id,
                                'records_count': len(processed_data) if isinstance(processed_data, list) else 1,
                                'start_date': start_date.isoformat() if start_date else None,
                                'end_date': end_date.isoformat() if end_date else None
                            }
                        )
                    else:
                        error_text = await response.text()
                        return ONSResponse(
                            success=False,
                            data=None,
                            metadata={'status_code': response.status},
                            error=f"HTTP {response.status}: {error_text}"
                        )
                        
        except asyncio.TimeoutError:
            return ONSResponse(
                success=False,
                data=None,
                metadata={},
                error=f"Timeout ao buscar dataset {dataset_id}"
            )
        except Exception as e:
            logger.error(f"Erro ao buscar dataset {dataset_id}: {e}")
            return ONSResponse(
                success=False,
                data=None,
                metadata={},
                error=str(e)
            )
    
    async def fetch_carga_energia(self,
                                 start_date: datetime,
                                 end_date: datetime,
                                 subsystems: Optional[List[str]] = None,
                                 frequency: str = 'hourly') -> pd.DataFrame:
        """
        Busca dados de carga de energia
        
        Args:
            start_date: Data inicial
            end_date: Data final
            subsystems: Lista de subsistemas
            frequency: Frequência dos dados (hourly, daily, monthly)
            
        Returns:
            DataFrame com dados de carga
        """
        endpoint_map = {
            'hourly': 'carga_energia/horaria',
            'daily': 'carga_energia/diaria',
            'monthly': 'carga_energia/mensal'
        }
        
        endpoint = endpoint_map.get(frequency, 'carga_energia/horaria')
        
        response = await self.fetch_dataset(
            endpoint,
            start_date,
            end_date,
            subsistemas=subsystems
        )
        
        if response.success and response.data:
            # Converter para DataFrame
            df = pd.DataFrame(response.data)
            
            # Padronizar colunas
            column_mapping = {
                'din_instante': 'timestamp',
                'nom_subsistema': 'subsystem',
                'val_cargaenergiamwmed': 'load_mw',
                'val_cargaenergiamwh': 'load_mwh'
            }
            
            df = df.rename(columns=column_mapping)
            
            # Converter timestamp
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # Filtrar por subsistemas se especificado
            if subsystems and 'subsystem' in df.columns:
                df = df[df['subsystem'].isin(subsystems)]
            
            return df
        
        return pd.DataFrame()
    
    async def fetch_cmo_pld(self,
                           start_date: datetime,
                           end_date: datetime,
                           price_type: str = 'cmo',
                           frequency: str = 'weekly') -> pd.DataFrame:
        """
        Busca dados de CMO/PLD
        
        Args:
            start_date: Data inicial
            end_date: Data final
            price_type: Tipo de preço (cmo, pld)
            frequency: Frequência (weekly, semi_hourly, hourly)
            
        Returns:
            DataFrame com dados de preço
        """
        endpoint_map = {
            ('cmo', 'weekly'): 'cmo/semanal',
            ('cmo', 'semi_hourly'): 'cmo/semi_horario',
            ('pld', 'hourly'): 'pld/horario'
        }
        
        endpoint = endpoint_map.get((price_type, frequency), 'cmo/semanal')
        
        response = await self.fetch_dataset(
            endpoint,
            start_date,
            end_date
        )
        
        if response.success and response.data:
            df = pd.DataFrame(response.data)
            
            # Padronizar colunas
            column_mapping = {
                'din_instante': 'timestamp',
                'nom_subsistema': 'subsystem',
                'val_cmomediasemanal': 'cmo_avg',
                'val_cmoleve': 'cmo_light',
                'val_cmomedia': 'cmo_medium',
                'val_cmopesada': 'cmo_heavy',
                'val_pldhorario': 'pld_hourly'
            }
            
            df = df.rename(columns=column_mapping)
            
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            return df
        
        return pd.DataFrame()
    
    async def fetch_generation_by_source(self,
                                        date: datetime,
                                        sources: Optional[List[str]] = None) -> Dict:
        """
        Busca geração por fonte
        
        Args:
            date: Data de referência
            sources: Lista de fontes (hidro, termo, eolica, solar, nuclear)
            
        Returns:
            Dicionário com geração por fonte
        """
        response = await self.fetch_dataset(
            'geracao/fonte',
            start_date=date,
            end_date=date,
            fontes=sources
        )
        
        if response.success and response.data:
            # Processar dados por fonte
            generation = {}
            
            for record in response.data:
                source = record.get('fonte_geracao', 'unknown')
                value = record.get('val_geracao_mw', 0)
                
                if source not in generation:
                    generation[source] = 0
                generation[source] += value
            
            return generation
        
        return {}
    
    async def fetch_reservoirs_level(self,
                                    date: Optional[datetime] = None,
                                    subsystems: Optional[List[str]] = None) -> pd.DataFrame:
        """
        Busca níveis de reservatórios
        
        Args:
            date: Data de referência
            subsystems: Lista de subsistemas
            
        Returns:
            DataFrame com níveis dos reservatórios
        """
        if not date:
            date = datetime.now()
        
        response = await self.fetch_dataset(
            'reservatorios/energia_armazenada',
            start_date=date,
            end_date=date,
            subsistemas=subsystems
        )
        
        if response.success and response.data:
            df = pd.DataFrame(response.data)
            
            # Padronizar colunas
            column_mapping = {
                'nom_subsistema': 'subsystem',
                'val_energiaarmazenada_mwmes': 'stored_energy',
                'val_energiaarmazenada_percentual': 'percentage',
                'din_instante': 'timestamp'
            }
            
            df = df.rename(columns=column_mapping)
            
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            return df
        
        return pd.DataFrame()
    
    # =================== Métodos de Processamento ===================
    
    def _process_dataset_data(self, dataset_id: str, raw_data: Any) -> List[Dict]:
        """
        Processa dados brutos do dataset
        
        Args:
            dataset_id: ID do dataset
            raw_data: Dados brutos
            
        Returns:
            Lista de registros processados
        """
        if not raw_data:
            return []
        
        # Se já for uma lista de dicionários, retornar
        if isinstance(raw_data, list) and all(isinstance(item, dict) for item in raw_data):
            return raw_data
        
        # Se for DataFrame, converter para lista de dicts
        if isinstance(raw_data, pd.DataFrame):
            return raw_data.to_dict('records')
        
        # Se for string (CSV ou JSON), processar
        if isinstance(raw_data, str):
            try:
                # Tentar JSON primeiro
                return json.loads(raw_data)
            except:
                # Tentar CSV
                return self._parse_csv(raw_data)
        
        # Se for bytes (arquivo binário), processar
        if isinstance(raw_data, bytes):
            return self._process_binary_data(raw_data)
        
        return [{'data': raw_data}]
    
    def _parse_csv(self, csv_text: str) -> List[Dict]:
        """Parse CSV para lista de dicionários"""
        try:
            df = pd.read_csv(StringIO(csv_text))
            return df.to_dict('records')
        except Exception as e:
            logger.error(f"Erro ao parsear CSV: {e}")
            return []
    
    def _parse_xml(self, xml_text: str) -> List[Dict]:
        """Parse XML para lista de dicionários"""
        try:
            root = ET.fromstring(xml_text)
            records = []
            
            for child in root:
                record = {}
                for element in child:
                    record[element.tag] = element.text
                records.append(record)
            
            return records
        except Exception as e:
            logger.error(f"Erro ao parsear XML: {e}")
            return []
    
    def _process_binary_data(self, data: bytes) -> List[Dict]:
        """Processa dados binários (ZIP, Excel, etc)"""
        try:
            # Tentar como ZIP
            with zipfile.ZipFile(BytesIO(data)) as zf:
                records = []
                for filename in zf.namelist():
                    if filename.endswith('.csv'):
                        with zf.open(filename) as f:
                            df = pd.read_csv(f)
                            records.extend(df.to_dict('records'))
                    elif filename.endswith('.json'):
                        with zf.open(filename) as f:
                            content = json.load(f)
                            if isinstance(content, list):
                                records.extend(content)
                            else:
                                records.append(content)
                return records
        except:
            pass
        
        try:
            # Tentar como Excel
            df = pd.read_excel(BytesIO(data))
            return df.to_dict('records')
        except:
            pass
        
        return []
    
    # =================== Métodos Auxiliares ===================
    
    def _get_endpoint(self, dataset_id: str) -> Optional[str]:
        """Obtém endpoint para um dataset"""
        # Verificar endpoints conhecidos
        for category, endpoints in self.ENDPOINTS.items():
            if dataset_id in endpoints:
                return endpoints[dataset_id]
            
            # Verificar se o dataset_id é um endpoint direto
            for endpoint_key, endpoint_value in endpoints.items():
                if endpoint_value == dataset_id:
                    return endpoint_value
        
        # Se não encontrar, assumir que é um path direto
        return dataset_id
    
    def _prepare_params(self,
                       start_date: Optional[datetime],
                       end_date: Optional[datetime],
                       **kwargs) -> Dict:
        """Prepara parâmetros para requisição"""
        params = {}
        
        # Datas
        if start_date:
            params['data_inicio'] = start_date.strftime('%Y-%m-%d')
        
        if end_date:
            params['data_fim'] = end_date.strftime('%Y-%m-%d')
        
        # Adicionar outros parâmetros
        for key, value in kwargs.items():
            if value is not None:
                if isinstance(value, list):
                    params[key] = ','.join(str(v) for v in value)
                else:
                    params[key] = value
        
        return params
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def _fetch_with_retry(self, url: str, params: Dict) -> Dict:
        """Fetch com retry automático"""
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, headers=self.headers) as response:
                response.raise_for_status()
                return await response.json()
    
    # =================== Métodos de Cache ===================
    
    @lru_cache(maxsize=100)
    def _get_cached_endpoint(self, dataset_id: str) -> Optional[str]:
        """Cache de endpoints"""
        return self._get_endpoint(dataset_id)
    
    def clear_cache(self):
        """Limpa cache"""
        self.datasets_cache.clear()
        self._get_cached_endpoint.cache_clear()
    
    # =================== Métodos de Validação ===================
    
    def validate_dataset_id(self, dataset_id: str) -> bool:
        """Valida se dataset existe"""
        return self._get_endpoint(dataset_id) is not None
    
    def get_available_datasets(self) -> List[Dict]:
        """Retorna lista de datasets disponíveis"""
        datasets = []
        
        for category, endpoints in self.ENDPOINTS.items():
            for key, endpoint in endpoints.items():
                datasets.append({
                    'id': key,
                    'category': category,
                    'endpoint': endpoint,
                    'name': key.replace('_', ' ').title()
                })
        
        return datasets
    
    def get_dataset_info(self, dataset_id: str) -> Optional[ONSDataset]:
        """Obtém informações sobre um dataset"""
        endpoint = self._get_endpoint(dataset_id)
        
        if not endpoint:
            return None
        
        # Encontrar categoria
        category = None
        for cat, endpoints in self.ENDPOINTS.items():
            if dataset_id in endpoints:
                category = cat
                break
        
        return ONSDataset(
            id=dataset_id,
            name=dataset_id.replace('_', ' ').title(),
            description=f"Dataset {dataset_id} from ONS",
            url=urljoin(self.base_url, endpoint),
            format='json',
            update_frequency='daily' if 'diaria' in endpoint else 'hourly'
        )

# =================== Funções Helper ===================

def get_ons_service() -> ONSService:
    """Retorna instância singleton do serviço ONS"""
    if 'ons_service' not in globals():
        globals()['ons_service'] = ONSService()
    return globals()['ons_service']

async def fetch_latest_data(dataset_id: str, hours: int = 24) -> pd.DataFrame:
    """
    Busca dados mais recentes de um dataset
    
    Args:
        dataset_id: ID do dataset
        hours: Horas para buscar
        
    Returns:
        DataFrame com dados
    """
    service = get_ons_service()
    
    end_date = datetime.now()
    start_date = end_date - timedelta(hours=hours)
    
    response = await service.fetch_dataset(dataset_id, start_date, end_date)
    
    if response.success and response.data:
        return pd.DataFrame(response.data)
    
    return pd.DataFrame()

def get_available_datasets() -> List[Dict]:
    """Retorna lista de datasets disponíveis"""
    service = get_ons_service()
    return service.get_available_datasets()