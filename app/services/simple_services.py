"""
ONS Service Simplificado - Sem dependência SQLAlchemy
Versão temporária para contornar incompatibilidade Python 3.13 + SQLAlchemy
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import asyncio


class SimpleONSService:
    """
    Versão simplificada do ONS Service sem SQLAlchemy
    """
    
    def __init__(self):
        self.base_url = "https://dados.ons.org.br/api/v1/"
        self.timeout = 30
    
    async def get_historical_data(self, 
                                dataset: str = 'carga_energia',
                                start_date: str = '2023-01-01',
                                end_date: str = '2024-12-31') -> pd.DataFrame:
        """
        Gera dados simulados baseados em padrões reais do ONS
        """
        print(f"📊 Gerando dados simulados para {dataset}...")
        
        # Criar dataset sintético baseado em padrões reais do setor elétrico
        dates = pd.date_range(start=start_date, end=end_date, freq='H')
        n_samples = len(dates)
        
        # Limitar para não sobrecarregar
        if n_samples > 10000:
            dates = dates[:10000]
            n_samples = 10000
        
        # Padrões sazonais e tendências
        hour = dates.hour
        day_of_year = dates.dayofyear
        day_of_week = dates.dayofweek
        
        # Simular carga baseada em padrões reais
        base_load = 70000  # MW base
        seasonal = 5000 * np.sin(2 * np.pi * day_of_year / 365)  # Sazonalidade anual
        daily = 8000 * np.sin(2 * np.pi * hour / 24)  # Padrão diário
        weekend_effect = -2000 * (day_of_week >= 5)  # Redução fins de semana
        noise = np.random.normal(0, 1000, n_samples)
        
        load = base_load + seasonal + daily + weekend_effect + noise
        
        # Outras variáveis correlacionadas
        temperature = 25 + 5 * np.sin(2 * np.pi * day_of_year / 365) + np.random.normal(0, 2, n_samples)
        cmo = 100 + 50 * np.sin(2 * np.pi * day_of_year / 365) + np.random.normal(0, 20, n_samples)
        
        # Simular subsistemas brasileiros
        subsystems = ['SE/CO', 'Sul', 'NE', 'Norte']
        weights = [0.6, 0.2, 0.15, 0.05]  # Pesos realísticos
        
        df = pd.DataFrame({
            'timestamp': dates,
            'din_instante': dates,  # Compatibilidade ONS
            'load_mw': load,
            'val_cargaenergiamwmed': load,  # Compatibilidade ONS
            'temperature': temperature,
            'cmo': cmo,
            'hour': hour,
            'day_of_week': day_of_week,
            'month': dates.month,
            'is_weekend': (day_of_week >= 5).astype(int),
            'nom_subsistema': np.random.choice(subsystems, n_samples, p=weights),
            'id_subsistema': np.random.choice(['SE', 'S', 'NE', 'N'], n_samples, p=weights)
        })
        
        print(f"✅ Gerados {len(df)} registros de dados simulados")
        return df


class SimpleCacheService:
    """
    Cache service simplificado em memória
    """
    
    def __init__(self):
        self._cache = {}
    
    async def get(self, key: str):
        """Obter do cache"""
        return self._cache.get(key)
    
    async def set(self, key: str, value: Any, ttl: int = 3600):
        """Definir no cache"""
        self._cache[key] = value
        # TTL ignorado na versão simplificada
        return True


# Instâncias globais
simple_ons_service = SimpleONSService()
simple_cache_service = SimpleCacheService()