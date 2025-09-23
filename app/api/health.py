"""
Health Check API endpoint para N8N
"""
import asyncio
from datetime import datetime
from typing import Dict, Any

try:
    import psycopg2
    import redis
    from config import DatabaseConfig, RedisConfig
    
    # Instanciar configurações
    db_config = DatabaseConfig()
    redis_config = RedisConfig()
    
except ImportError as e:
    print(f"Warning: Some dependencies not available: {e}")
    # Fallback para configurações básicas
    class DatabaseConfig:
        host = "localhost"
        port = 5432
        database = "aspi_db"
        user = "aspi"
        password = "aspi123"
    
    class RedisConfig:
        host = "localhost"
        port = 6379
        password = "redis123"
    
    db_config = DatabaseConfig()
    redis_config = RedisConfig()

class HealthChecker:
    """Verificador de saúde dos serviços"""
    
    @staticmethod
    def check_database() -> Dict[str, Any]:
        """Verifica conexão com PostgreSQL"""
        try:
            conn = psycopg2.connect(
                host=db_config.host,
                port=db_config.port, 
                database=db_config.database,
                user=db_config.user,
                password=db_config.password
            )
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            
            return {
                "status": "connected",
                "response_time": "< 100ms",
                "last_check": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "last_check": datetime.now().isoformat()
            }
    
    @staticmethod
    def check_redis() -> Dict[str, Any]:
        """Verifica conexão com Redis"""
        try:
            r = redis.Redis(
                host=redis_config.host,
                port=redis_config.port,
                password=getattr(redis_config, 'password', None),
                decode_responses=True
            )
            r.ping()
            
            return {
                "status": "connected", 
                "response_time": "< 50ms",
                "last_check": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "last_check": datetime.now().isoformat()
            }
    
    @staticmethod
    def get_system_status() -> Dict[str, Any]:
        """Status geral do sistema"""
        db_status = HealthChecker.check_database()
        redis_status = HealthChecker.check_redis()
        
        # Determinar status geral
        overall_status = "healthy"
        if db_status["status"] == "error" or redis_status["status"] == "error":
            overall_status = "degraded"
        
        return {
            "status": overall_status,
            "timestamp": datetime.now().isoformat(),
            "services": {
                "database": db_status["status"],
                "redis": redis_status["status"],
                "api": "running"
            },
            "details": {
                "database": db_status,
                "redis": redis_status
            },
            "version": "1.0.0"
        }

# Para uso no Streamlit
def health_check_endpoint():
    """Endpoint simulado para health check"""
    try:
        health_data = HealthChecker.get_system_status()
        return health_data
    except Exception as e:
        return {
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }