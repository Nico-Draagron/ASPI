"""
services/data_service.py
Serviço principal de manipulação e análise de dados
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
import asyncio
import aiohttp
from sqlalchemy import create_engine, text, and_, or_, func
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.exc import SQLAlchemyError
import logging
from functools import lru_cache
import json
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

from models.database import (
    Dataset, DataRecord, CargaEnergia, CMO, 
    BandeiraTarifariaAcionamento, Reservatorio,
    GeracaoUsina, IntercambioRegional, RegionType
)
from utils.validators import validate_date_range, validate_region
from utils.formatters import format_number, format_percentage

# Configuração de logging
logger = logging.getLogger(__name__)

@dataclass
class QueryResult:
    """Resultado de uma query de dados"""
    success: bool
    data: Optional[pd.DataFrame]
    metadata: Dict[str, Any]
    error: Optional[str] = None
    warnings: List[str] = None
    execution_time_ms: float = 0

@dataclass
class AnalysisResult:
    """Resultado de uma análise"""
    metrics: Dict[str, Any]
    insights: List[str]
    visualizations: List[Dict]
    recommendations: List[str]
    confidence_score: float

class DataService:
    """Serviço principal de manipulação de dados"""
    
    def __init__(self, db_url: str = None):
        """
        Inicializa o serviço de dados
        
        Args:
            db_url: URL de conexão com o banco
        """
        self.db_url = db_url or os.getenv('DATABASE_URL')
        self.engine = create_engine(self.db_url)
        self.SessionLocal = sessionmaker(bind=self.engine)
        
        # Cache de queries
        self.query_cache = {}
        self.cache_ttl = 300  # 5 minutos
        
        # Configurações de análise
        self.anomaly_threshold = 3  # z-score
        self.trend_window = 7  # dias
        
    # =================== Métodos de Query ===================
    
    def get_carga_energia(self,
                         start_date: datetime,
                         end_date: datetime,
                         regions: Optional[List[str]] = None,
                         aggregation: str = 'hourly') -> QueryResult:
        """
        Obtém dados de carga de energia
        
        Args:
            start_date: Data inicial
            end_date: Data final
            regions: Lista de regiões
            aggregation: Nível de agregação (hourly, daily, weekly, monthly)
            
        Returns:
            Resultado da query
        """
        start_time = datetime.now()
        
        try:
            with self.SessionLocal() as session:
                query = session.query(CargaEnergia)
                
                # Filtros
                query = query.filter(
                    and_(
                        CargaEnergia.din_instante >= start_date,
                        CargaEnergia.din_instante <= end_date
                    )
                )
                
                if regions:
                    query = query.filter(CargaEnergia.nom_subsistema.in_(regions))
                
                # Executar query
                results = query.all()
                
                # Converter para DataFrame
                df = pd.DataFrame([{
                    'timestamp': r.din_instante,
                    'region': r.nom_subsistema,
                    'load_mw': r.val_cargaenergiamwmed,
                    'subsystem_id': r.id_subsistema
                } for r in results])
                
                if not df.empty:
                    # Aplicar agregação
                    df = self._apply_aggregation(df, aggregation, 'timestamp', 'load_mw')
                    
                    # Calcular métricas
                    metadata = self._calculate_load_metrics(df)
                else:
                    metadata = {'message': 'Nenhum dado encontrado'}
                
                execution_time = (datetime.now() - start_time).total_seconds() * 1000
                
                return QueryResult(
                    success=True,
                    data=df,
                    metadata=metadata,
                    execution_time_ms=execution_time
                )
                
        except Exception as e:
            logger.error(f"Erro ao buscar carga de energia: {e}")
            return QueryResult(
                success=False,
                data=None,
                metadata={},
                error=str(e),
                execution_time_ms=(datetime.now() - start_time).total_seconds() * 1000
            )
    
    def get_cmo_pld(self,
                   start_date: datetime,
                   end_date: datetime,
                   regions: Optional[List[str]] = None,
                   patamar: Optional[str] = None) -> QueryResult:
        """
        Obtém dados de CMO/PLD
        
        Args:
            start_date: Data inicial
            end_date: Data final
            regions: Lista de regiões
            patamar: Patamar de carga (leve, media, pesada)
            
        Returns:
            Resultado da query
        """
        start_time = datetime.now()
        
        try:
            with self.SessionLocal() as session:
                query = session.query(CMO)
                
                # Filtros
                query = query.filter(
                    and_(
                        CMO.din_instante >= start_date,
                        CMO.din_instante <= end_date
                    )
                )
                
                if regions:
                    query = query.filter(CMO.nom_subsistema.in_(regions))
                
                if patamar:
                    query = query.filter(CMO.patamar == patamar)
                
                results = query.all()
                
                # Converter para DataFrame
                df = pd.DataFrame([{
                    'timestamp': r.din_instante,
                    'region': r.nom_subsistema,
                    'cmo_leve': r.val_cmoleve,
                    'cmo_media': r.val_cmomedia,
                    'cmo_pesada': r.val_cmopesada,
                    'cmo_semanal': r.val_cmomediasemanal,
                    'patamar': r.patamar
                } for r in results])
                
                if not df.empty:
                    metadata = self._calculate_cmo_metrics(df)
                else:
                    metadata = {'message': 'Nenhum dado encontrado'}
                
                execution_time = (datetime.now() - start_time).total_seconds() * 1000
                
                return QueryResult(
                    success=True,
                    data=df,
                    metadata=metadata,
                    execution_time_ms=execution_time
                )
                
        except Exception as e:
            logger.error(f"Erro ao buscar CMO/PLD: {e}")
            return QueryResult(
                success=False,
                data=None,
                metadata={},
                error=str(e),
                execution_time_ms=(datetime.now() - start_time).total_seconds() * 1000
            )
    
    def get_bandeiras_tarifarias(self,
                                year: Optional[int] = None) -> QueryResult:
        """
        Obtém histórico de bandeiras tarifárias
        
        Args:
            year: Ano específico (opcional)
            
        Returns:
            Resultado da query
        """
        start_time = datetime.now()
        
        try:
            with self.SessionLocal() as session:
                query = session.query(BandeiraTarifariaAcionamento)
                
                if year:
                    query = query.filter(
                        func.extract('year', BandeiraTarifariaAcionamento.dat_competencia) == year
                    )
                
                query = query.order_by(BandeiraTarifariaAcionamento.dat_competencia.desc())
                results = query.all()
                
                df = pd.DataFrame([{
                    'competencia': r.dat_competencia,
                    'bandeira': r.nom_bandeira_acionada,
                    'tipo': r.tipo_bandeira.value if r.tipo_bandeira else None,
                    'valor_adicional': float(r.vlr_adicional_bandeira),
                    'motivo': r.motivo_acionamento
                } for r in results])
                
                if not df.empty:
                    metadata = self._calculate_bandeira_metrics(df)
                else:
                    metadata = {'message': 'Nenhum dado encontrado'}
                
                execution_time = (datetime.now() - start_time).total_seconds() * 1000
                
                return QueryResult(
                    success=True,
                    data=df,
                    metadata=metadata,
                    execution_time_ms=execution_time
                )
                
        except Exception as e:
            logger.error(f"Erro ao buscar bandeiras tarifárias: {e}")
            return QueryResult(
                success=False,
                data=None,
                metadata={},
                error=str(e),
                execution_time_ms=(datetime.now() - start_time).total_seconds() * 1000
            )
    
    # =================== Métodos de Análise ===================
    
    def analyze_load_patterns(self,
                             df: pd.DataFrame,
                             region: Optional[str] = None) -> AnalysisResult:
        """
        Analisa padrões de carga de energia
        
        Args:
            df: DataFrame com dados de carga
            region: Região específica para análise
            
        Returns:
            Resultado da análise
        """
        if df.empty:
            return AnalysisResult(
                metrics={},
                insights=[],
                visualizations=[],
                recommendations=[],
                confidence_score=0.0
            )
        
        # Filtrar por região se especificado
        if region and 'region' in df.columns:
            df = df[df['region'] == region]
        
        metrics = {}
        insights = []
        visualizations = []
        recommendations = []
        
        # Métricas básicas
        if 'load_mw' in df.columns:
            metrics['avg_load'] = df['load_mw'].mean()
            metrics['max_load'] = df['load_mw'].max()
            metrics['min_load'] = df['load_mw'].min()
            metrics['std_dev'] = df['load_mw'].std()
            metrics['cv'] = (metrics['std_dev'] / metrics['avg_load']) * 100
            
            # Análise de tendência
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df = df.sort_values('timestamp')
                
                # Tendência linear
                x = np.arange(len(df))
                y = df['load_mw'].values
                slope, intercept = np.polyfit(x, y, 1)
                metrics['trend_slope'] = slope
                
                if slope > 0:
                    insights.append(f"Tendência de alta na carga: {slope:.2f} MW por período")
                elif slope < 0:
                    insights.append(f"Tendência de baixa na carga: {slope:.2f} MW por período")
                
                # Sazonalidade
                if len(df) > 24:
                    df['hour'] = df['timestamp'].dt.hour
                    hourly_avg = df.groupby('hour')['load_mw'].mean()
                    
                    peak_hour = hourly_avg.idxmax()
                    valley_hour = hourly_avg.idxmin()
                    
                    metrics['peak_hour'] = int(peak_hour)
                    metrics['valley_hour'] = int(valley_hour)
                    metrics['peak_valley_ratio'] = hourly_avg.max() / hourly_avg.min()
                    
                    insights.append(f"Pico de consumo às {peak_hour}h")
                    insights.append(f"Vale de consumo às {valley_hour}h")
                    
                    # Visualização de padrão diário
                    visualizations.append({
                        'type': 'line',
                        'data': {
                            'x': list(range(24)),
                            'y': hourly_avg.tolist(),
                            'name': 'Padrão Diário Médio'
                        },
                        'layout': {
                            'title': 'Padrão de Carga Diário',
                            'xaxis': {'title': 'Hora'},
                            'yaxis': {'title': 'Carga (MW)'}
                        }
                    })
            
            # Detecção de anomalias
            anomalies = self._detect_anomalies(df['load_mw'])
            if len(anomalies) > 0:
                metrics['anomaly_count'] = len(anomalies)
                insights.append(f"Detectadas {len(anomalies)} anomalias na carga")
                recommendations.append("Investigar períodos com anomalias detectadas")
            
            # Análise de volatilidade
            if metrics['cv'] > 20:
                insights.append(f"Alta volatilidade na carga (CV: {metrics['cv']:.1f}%)")
                recommendations.append("Considerar estratégias de balanceamento de carga")
            
            # Recomendações baseadas em padrões
            if metrics.get('peak_valley_ratio', 1) > 1.5:
                recommendations.append("Grande variação entre pico e vale - avaliar tarifação horária")
            
            if metrics['max_load'] > metrics['avg_load'] * 1.3:
                recommendations.append("Picos significativos detectados - verificar capacidade de reserva")
        
        # Calcular score de confiança
        confidence_score = min(len(df) / 100, 1.0)  # Baseado na quantidade de dados
        
        return AnalysisResult(
            metrics=metrics,
            insights=insights,
            visualizations=visualizations,
            recommendations=recommendations,
            confidence_score=confidence_score
        )
    
    def compare_regions(self,
                       df: pd.DataFrame,
                       metric: str = 'load_mw') -> AnalysisResult:
        """
        Compara métricas entre regiões
        
        Args:
            df: DataFrame com dados
            metric: Métrica para comparação
            
        Returns:
            Resultado da análise comparativa
        """
        if df.empty or 'region' not in df.columns or metric not in df.columns:
            return AnalysisResult(
                metrics={},
                insights=[],
                visualizations=[],
                recommendations=[],
                confidence_score=0.0
            )
        
        metrics = {}
        insights = []
        visualizations = []
        recommendations = []
        
        # Agrupar por região
        regional_stats = df.groupby('region')[metric].agg([
            'mean', 'std', 'min', 'max', 'count'
        ]).round(2)
        
        metrics['regional_comparison'] = regional_stats.to_dict()
        
        # Identificar região com maior/menor valor
        max_region = regional_stats['mean'].idxmax()
        min_region = regional_stats['mean'].idxmin()
        
        insights.append(f"Maior {metric} médio: {max_region} ({regional_stats.loc[max_region, 'mean']:.2f})")
        insights.append(f"Menor {metric} médio: {min_region} ({regional_stats.loc[min_region, 'mean']:.2f})")
        
        # Calcular disparidade
        disparity = (regional_stats['mean'].max() / regional_stats['mean'].min()) - 1
        metrics['regional_disparity'] = disparity * 100
        
        if disparity > 0.5:
            insights.append(f"Alta disparidade regional: {disparity*100:.1f}%")
            recommendations.append("Avaliar necessidade de rebalanceamento inter-regional")
        
        # Visualização comparativa
        visualizations.append({
            'type': 'bar',
            'data': {
                'x': regional_stats.index.tolist(),
                'y': regional_stats['mean'].tolist(),
                'name': f'{metric} Médio'
            },
            'layout': {
                'title': f'Comparação Regional - {metric}',
                'xaxis': {'title': 'Região'},
                'yaxis': {'title': metric}
            }
        })
        
        # Análise de correlação entre regiões
        if 'timestamp' in df.columns:
            pivot_df = df.pivot_table(
                values=metric,
                index='timestamp',
                columns='region',
                aggfunc='mean'
            )
            
            if not pivot_df.empty:
                correlation_matrix = pivot_df.corr()
                metrics['regional_correlation'] = correlation_matrix.to_dict()
                
                # Identificar correlações fortes
                for i in range(len(correlation_matrix.columns)):
                    for j in range(i+1, len(correlation_matrix.columns)):
                        corr_value = correlation_matrix.iloc[i, j]
                        if abs(corr_value) > 0.8:
                            region1 = correlation_matrix.columns[i]
                            region2 = correlation_matrix.columns[j]
                            insights.append(
                                f"Forte correlação entre {region1} e {region2}: {corr_value:.2f}"
                            )
        
        confidence_score = min(len(df) / (100 * regional_stats.shape[0]), 1.0)
        
        return AnalysisResult(
            metrics=metrics,
            insights=insights,
            visualizations=visualizations,
            recommendations=recommendations,
            confidence_score=confidence_score
        )
    
    def forecast_demand(self,
                       df: pd.DataFrame,
                       periods: int = 7,
                       method: str = 'linear') -> Dict:
        """
        Previsão de demanda
        
        Args:
            df: DataFrame com dados históricos
            periods: Número de períodos para prever
            method: Método de previsão (linear, moving_average, exponential)
            
        Returns:
            Previsão com intervalos de confiança
        """
        if df.empty or 'load_mw' not in df.columns:
            return {'error': 'Dados insuficientes para previsão'}
        
        # Preparar dados
        if 'timestamp' in df.columns:
            df = df.sort_values('timestamp')
        
        values = df['load_mw'].values
        
        forecast = {}
        
        if method == 'linear':
            # Regressão linear simples
            x = np.arange(len(values))
            slope, intercept = np.polyfit(x, values, 1)
            
            future_x = np.arange(len(values), len(values) + periods)
            predictions = slope * future_x + intercept
            
            # Calcular erro padrão
            residuals = values - (slope * x + intercept)
            std_error = np.std(residuals)
            
            forecast['predictions'] = predictions.tolist()
            forecast['upper_bound'] = (predictions + 1.96 * std_error).tolist()
            forecast['lower_bound'] = (predictions - 1.96 * std_error).tolist()
            
        elif method == 'moving_average':
            # Média móvel
            window = min(7, len(values) // 3)
            ma = pd.Series(values).rolling(window=window).mean()
            last_ma = ma.iloc[-1]
            
            predictions = [last_ma] * periods
            std_error = pd.Series(values).rolling(window=window).std().iloc[-1]
            
            forecast['predictions'] = predictions
            forecast['upper_bound'] = [p + 1.96 * std_error for p in predictions]
            forecast['lower_bound'] = [p - 1.96 * std_error for p in predictions]
            
        elif method == 'exponential':
            # Suavização exponencial simples
            alpha = 0.3
            s = [values[0]]
            
            for i in range(1, len(values)):
                s.append(alpha * values[i] + (1 - alpha) * s[-1])
            
            last_s = s[-1]
            predictions = [last_s] * periods
            
            # Erro baseado em resíduos
            residuals = values[1:] - s[:-1]
            std_error = np.std(residuals)
            
            forecast['predictions'] = predictions
            forecast['upper_bound'] = [p + 1.96 * std_error for p in predictions]
            forecast['lower_bound'] = [p - 1.96 * std_error for p in predictions]
        
        forecast['method'] = method
        forecast['periods'] = periods
        forecast['confidence_level'] = 95
        forecast['base_date'] = df['timestamp'].max().isoformat() if 'timestamp' in df.columns else None
        
        return forecast
    
    # =================== Métodos Auxiliares ===================
    
    def _apply_aggregation(self,
                          df: pd.DataFrame,
                          aggregation: str,
                          date_column: str,
                          value_column: str) -> pd.DataFrame:
        """Aplica agregação temporal aos dados"""
        df[date_column] = pd.to_datetime(df[date_column])
        
        freq_map = {
            'hourly': 'H',
            'daily': 'D',
            'weekly': 'W',
            'monthly': 'M'
        }
        
        if aggregation in freq_map:
            df = df.set_index(date_column)
            df = df.resample(freq_map[aggregation])[value_column].agg(['mean', 'min', 'max', 'std'])
            df = df.reset_index()
        
        return df
    
    def _detect_anomalies(self,
                         series: pd.Series,
                         threshold: Optional[float] = None) -> np.ndarray:
        """Detecta anomalias usando Z-score"""
        if threshold is None:
            threshold = self.anomaly_threshold
        
        z_scores = np.abs(stats.zscore(series.dropna()))
        return np.where(z_scores > threshold)[0]
    
    def _calculate_load_metrics(self, df: pd.DataFrame) -> Dict:
        """Calcula métricas de carga"""
        metrics = {}
        
        if 'load_mw' in df.columns:
            metrics['total_records'] = len(df)
            metrics['avg_load'] = df['load_mw'].mean()
            metrics['max_load'] = df['load_mw'].max()
            metrics['min_load'] = df['load_mw'].min()
            metrics['std_dev'] = df['load_mw'].std()
            
            if 'region' in df.columns:
                metrics['regions'] = df['region'].unique().tolist()
                metrics['records_by_region'] = df['region'].value_counts().to_dict()
        
        return metrics
    
    def _calculate_cmo_metrics(self, df: pd.DataFrame) -> Dict:
        """Calcula métricas de CMO"""
        metrics = {}
        
        cmo_columns = ['cmo_leve', 'cmo_media', 'cmo_pesada', 'cmo_semanal']
        available_columns = [col for col in cmo_columns if col in df.columns]
        
        if available_columns:
            for col in available_columns:
                if df[col].notna().any():
                    metrics[f'{col}_avg'] = df[col].mean()
                    metrics[f'{col}_max'] = df[col].max()
                    metrics[f'{col}_min'] = df[col].min()
        
        if 'region' in df.columns:
            metrics['regions'] = df['region'].unique().tolist()
        
        return metrics
    
    def _calculate_bandeira_metrics(self, df: pd.DataFrame) -> Dict:
        """Calcula métricas de bandeiras tarifárias"""
        metrics = {}
        
        if 'tipo' in df.columns:
            metrics['bandeira_counts'] = df['tipo'].value_counts().to_dict()
            
        if 'valor_adicional' in df.columns:
            metrics['avg_adicional'] = df['valor_adicional'].mean()
            metrics['total_adicional'] = df['valor_adicional'].sum()
        
        if 'competencia' in df.columns:
            df['competencia'] = pd.to_datetime(df['competencia'])
            metrics['periodo'] = {
                'inicio': df['competencia'].min().isoformat(),
                'fim': df['competencia'].max().isoformat()
            }
        
        return metrics
    
    # =================== Cache Methods ===================
    
    @lru_cache(maxsize=100)
    def get_cached_query(self, query_hash: str) -> Optional[QueryResult]:
        """Obtém resultado de query do cache"""
        if query_hash in self.query_cache:
            cached_data, timestamp = self.query_cache[query_hash]
            if (datetime.now() - timestamp).seconds < self.cache_ttl:
                return cached_data
        return None
    
    def cache_query_result(self, query_hash: str, result: QueryResult):
        """Armazena resultado de query no cache"""
        self.query_cache[query_hash] = (result, datetime.now())

# =================== Funções Helper ===================

def get_data_service() -> DataService:
    """Retorna instância singleton do serviço de dados"""
    if 'data_service' not in globals():
        globals()['data_service'] = DataService()
    return globals()['data_service']

def analyze_electricity_data(
    dataset: str,
    start_date: datetime,
    end_date: datetime,
    regions: Optional[List[str]] = None
) -> Dict:
    """
    Analisa dados do setor elétrico
    
    Args:
        dataset: Nome do dataset
        start_date: Data inicial
        end_date: Data final
        regions: Regiões para análise
        
    Returns:
        Análise completa dos dados
    """
    service = get_data_service()
    
    # Buscar dados baseado no dataset
    if dataset == 'carga_energia':
        result = service.get_carga_energia(start_date, end_date, regions)
    elif dataset == 'cmo_pld':
        result = service.get_cmo_pld(start_date, end_date, regions)
    elif dataset == 'bandeiras':
        result = service.get_bandeiras_tarifarias()
    else:
        return {'error': f'Dataset {dataset} não reconhecido'}
    
    if not result.success:
        return {'error': result.error}
    
    # Realizar análise
    analysis = service.analyze_load_patterns(result.data)
    
    # Comparação regional se múltiplas regiões
    if regions and len(regions) > 1:
        comparison = service.compare_regions(result.data)
        analysis.insights.extend(comparison.insights)
        analysis.recommendations.extend(comparison.recommendations)
    
    return {
        'data': result.data.to_dict() if result.data is not None else None,
        'metadata': result.metadata,
        'analysis': {
            'metrics': analysis.metrics,
            'insights': analysis.insights,
            'recommendations': analysis.recommendations,
            'confidence': analysis.confidence_score
        },
        'execution_time_ms': result.execution_time_ms
    }