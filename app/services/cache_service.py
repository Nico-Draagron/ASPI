"""
ASPI - Cache Service
Serviço de cache usando Redis
"""

import redis
import json
import pickle
from typing import Any, Optional, Dict, List
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class CacheService:
    """Serviço de cache com Redis"""
    
    def __init__(self, host='localhost', port=6379, password='redis123', db=0):
        """Inicializa conexão com Redis"""
        try:
            self.redis_client = redis.Redis(
                host=host,
                port=port,
                password=password,
                db=db,
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5
            )
            # Teste de conexão
            self.redis_client.ping()
            self.connected = True
            logger.info("✅ Conectado ao Redis")
        except Exception as e:
            logger.error(f"❌ Erro ao conectar no Redis: {e}")
            self.redis_client = None
            self.connected = False
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Define um valor no cache"""
        if not self.connected:
            return False
        
        try:
            # Serializar o valor
            if isinstance(value, (dict, list)):
                serialized_value = json.dumps(value, default=str)
            else:
                serialized_value = str(value)
            
            if ttl:
                self.redis_client.setex(key, ttl, serialized_value)
            else:
                self.redis_client.set(key, serialized_value)
            
            return True
        except Exception as e:
            logger.error(f"Erro ao definir cache {key}: {e}")
            return False
    
    def get(self, key: str) -> Optional[Any]:
        """Obtém um valor do cache"""
        if not self.connected:
            return None
        
        try:
            value = self.redis_client.get(key)
            if value is None:
                return None
            
            # Tentar deserializar como JSON
            try:
                return json.loads(value)
            except:
                return value
        except Exception as e:
            logger.error(f"Erro ao obter cache {key}: {e}")
            return None
    
    def delete(self, key: str) -> bool:
        """Remove um valor do cache"""
        if not self.connected:
            return False
        
        try:
            self.redis_client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Erro ao deletar cache {key}: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """Verifica se uma chave existe no cache"""
        if not self.connected:
            return False
        
        try:
            return bool(self.redis_client.exists(key))
        except Exception as e:
            logger.error(f"Erro ao verificar cache {key}: {e}")
            return False
    
    def get_keys(self, pattern: str = "*") -> List[str]:
        """Obtém todas as chaves que correspondem ao padrão"""
        if not self.connected:
            return []
        
        try:
            return self.redis_client.keys(pattern)
        except Exception as e:
            logger.error(f"Erro ao obter chaves {pattern}: {e}")
            return []
    
    def clear_pattern(self, pattern: str) -> int:
        """Remove todas as chaves que correspondem ao padrão"""
        if not self.connected:
            return 0
        
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                return self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Erro ao limpar padrão {pattern}: {e}")
            return 0
    
    def flush_all(self) -> bool:
        """Limpa todo o cache"""
        if not self.connected:
            return False
        
        try:
            self.redis_client.flushdb()
            return True
        except Exception as e:
            logger.error(f"Erro ao limpar cache: {e}")
            return False
    
    def get_info(self) -> Dict[str, Any]:
        """Obtém informações do Redis"""
        if not self.connected:
            return {"connected": False, "error": "Não conectado"}
        
        try:
            info = self.redis_client.info()
            return {
                "connected": True,
                "version": info.get("redis_version"),
                "memory_used": info.get("used_memory_human"),
                "keyspace": info.get("db0", {}),
                "clients": info.get("connected_clients"),
                "uptime": info.get("uptime_in_seconds")
            }
        except Exception as e:
            logger.error(f"Erro ao obter info do Redis: {e}")
            return {"connected": False, "error": str(e)}
    
    def set_session_data(self, session_id: str, data: Dict[str, Any], ttl: int = 3600) -> bool:
        """Define dados de sessão"""
        return self.set(f"session:{session_id}", data, ttl)
    
    def get_session_data(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Obtém dados de sessão"""
        return self.get(f"session:{session_id}")
    
    def cache_ons_data(self, dataset_id: str, data: Any, ttl: int = 1800) -> bool:
        """Cache específico para dados ONS"""
        key = f"ons:data:{dataset_id}:{datetime.now().strftime('%Y%m%d_%H')}"
        return self.set(key, data, ttl)
    
    def get_ons_data(self, dataset_id: str) -> Optional[Any]:
        """Obtém dados ONS do cache"""
        # Buscar dados da hora atual primeiro
        current_hour = datetime.now().strftime('%Y%m%d_%H')
        key = f"ons:data:{dataset_id}:{current_hour}"
        
        data = self.get(key)
        if data:
            return data
        
        # Se não encontrar, buscar da hora anterior
        previous_hour = (datetime.now() - timedelta(hours=1)).strftime('%Y%m%d_%H')
        key_prev = f"ons:data:{dataset_id}:{previous_hour}"
        return self.get(key_prev)

# Cache global
_cache_service = None

def get_cache_service() -> CacheService:
    """Obtém instância global do cache service"""
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService()
    return _cache_service

# Funções de conveniência
def cache_set(key: str, value: Any, ttl: Optional[int] = None) -> bool:
    """Função de conveniência para definir cache"""
    return get_cache_service().set(key, value, ttl)

def cache_get(key: str) -> Optional[Any]:
    """Função de conveniência para obter cache"""
    return get_cache_service().get(key)

def cache_delete(key: str) -> bool:
    """Função de conveniência para deletar cache"""
    return get_cache_service().delete(key)
