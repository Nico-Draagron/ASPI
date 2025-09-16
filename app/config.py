"""
app/config.py
Configurações centralizadas do sistema AIDE
"""

import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from pathlib import Path
from datetime import timedelta
import json
import logging
from functools import lru_cache

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# =================== Paths ===================

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"
CACHE_DIR = BASE_DIR / "cache"
ASSETS_DIR = BASE_DIR / "app" / "assets"

# Criar diretórios se não existirem
for directory in [DATA_DIR, LOGS_DIR, CACHE_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# =================== Environment ===================

class Environment:
    """Ambientes de execução"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"

ENVIRONMENT = os.getenv("ENVIRONMENT", Environment.DEVELOPMENT)
DEBUG = ENVIRONMENT == Environment.DEVELOPMENT

# =================== Database Configuration ===================

@dataclass
class DatabaseConfig:
    """Configurações do banco de dados"""
    host: str = os.getenv("DB_HOST", "localhost")
    port: int = int(os.getenv("DB_PORT", "5432"))
    database: str = os.getenv("DB_NAME", "aide_db")
    username: str = os.getenv("DB_USER", "aide_user")
    password: str = os.getenv("DB_PASSWORD", "")
    
    # Pool settings
    pool_size: int = int(os.getenv("DB_POOL_SIZE", "10"))
    max_overflow: int = int(os.getenv("DB_MAX_OVERFLOW", "20"))
    pool_timeout: int = int(os.getenv("DB_POOL_TIMEOUT", "30"))
    
    # Options
    echo: bool = DEBUG
    echo_pool: bool = False
    
    @property
    def url(self) -> str:
        """Retorna URL de conexão"""
        return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"
    
    @property
    def async_url(self) -> str:
        """Retorna URL de conexão assíncrona"""
        return f"postgresql+asyncpg://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"

# =================== Redis Configuration ===================

@dataclass
class RedisConfig:
    """Configurações do Redis"""
    host: str = os.getenv("REDIS_HOST", "localhost")
    port: int = int(os.getenv("REDIS_PORT", "6379"))
    password: str = os.getenv("REDIS_PASSWORD", "")
    db: int = int(os.getenv("REDIS_DB", "0"))
    
    # TTL settings (em segundos)
    cache_ttl: int = int(os.getenv("REDIS_CACHE_TTL", "300"))  # 5 minutos
    session_ttl: int = int(os.getenv("REDIS_SESSION_TTL", "3600"))  # 1 hora
    
    # Pool settings
    max_connections: int = int(os.getenv("REDIS_MAX_CONNECTIONS", "50"))
    
    @property
    def url(self) -> str:
        """Retorna URL de conexão"""
        if self.password:
            return f"redis://:{self.password}@{self.host}:{self.port}/{self.db}"
        return f"redis://{self.host}:{self.port}/{self.db}"

# =================== AI Configuration ===================

@dataclass
class AIConfig:
    """Configurações de IA"""
    # OpenAI
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")
    openai_temperature: float = float(os.getenv("OPENAI_TEMPERATURE", "0.7"))
    openai_max_tokens: int = int(os.getenv("OPENAI_MAX_TOKENS", "1000"))
    
    # Claude/Anthropic
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    claude_model: str = os.getenv("CLAUDE_MODEL", "claude-3-sonnet-20240229")
    claude_temperature: float = float(os.getenv("CLAUDE_TEMPERATURE", "0.7"))
    claude_max_tokens: int = int(os.getenv("CLAUDE_MAX_TOKENS", "1500"))
    
    # Google Gemini
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-pro")
    
    # General settings
    default_provider: str = os.getenv("AI_DEFAULT_PROVIDER", "openai")
    enable_streaming: bool = os.getenv("AI_ENABLE_STREAMING", "false").lower() == "true"
    max_retries: int = int(os.getenv("AI_MAX_RETRIES", "3"))
    timeout: int = int(os.getenv("AI_TIMEOUT", "30"))

# =================== n8n Configuration ===================

@dataclass
class N8NConfig:
    """Configurações do n8n"""
    base_url: str = os.getenv("N8N_BASE_URL", "http://localhost:5678")
    api_key: str = os.getenv("N8N_API_KEY", "")
    webhook_token: str = os.getenv("N8N_WEBHOOK_TOKEN", "")
    
    # Workflow IDs
    workflow_data_ingestion: str = os.getenv("N8N_WORKFLOW_DATA_INGESTION", "")
    workflow_chat: str = os.getenv("N8N_WORKFLOW_CHAT", "")
    workflow_monitoring: str = os.getenv("N8N_WORKFLOW_MONITORING", "")
    workflow_backup: str = os.getenv("N8N_WORKFLOW_BACKUP", "")
    
    # Settings
    enable_webhooks: bool = os.getenv("N8N_ENABLE_WEBHOOKS", "true").lower() == "true"
    webhook_timeout: int = int(os.getenv("N8N_WEBHOOK_TIMEOUT", "30"))

# =================== ONS API Configuration ===================

@dataclass
class ONSConfig:
    """Configurações da API ONS"""
    base_url: str = os.getenv("ONS_API_URL", "https://dados.ons.org.br/api/v1")
    api_key: str = os.getenv("ONS_API_KEY", "")
    
    # Datasets prioritários
    priority_datasets: List[str] = field(default_factory=lambda: [
        "carga_energia",
        "cmo_pld",
        "bandeiras_tarifarias",
        "geracao_usina",
        "reservatorios"
    ])
    
    # Update settings
    update_interval_hours: int = int(os.getenv("ONS_UPDATE_INTERVAL", "1"))
    batch_size: int = int(os.getenv("ONS_BATCH_SIZE", "100"))
    max_retries: int = int(os.getenv("ONS_MAX_RETRIES", "3"))
    timeout: int = int(os.getenv("ONS_TIMEOUT", "60"))

# =================== Streamlit Configuration ===================

@dataclass
class StreamlitConfig:
    """Configurações do Streamlit"""
    page_title: str = "AIDE - Assistente Inteligente ONS"
    page_icon: str = "⚡"
    layout: str = "wide"
    initial_sidebar_state: str = "expanded"
    
    # Theme
    primary_color: str = "#e7cba9"
    background_color: str = "#FFFFFF"
    secondary_background_color: str = "#f8f9fa"
    text_color: str = "#2c3e50"
    font: str = "Inter"
    
    # Features
    enable_chat: bool = True
    enable_export: bool = True
    enable_analytics: bool = True
    enable_monitoring: bool = True
    
    # Cache
    cache_ttl_seconds: int = 300
    max_entries: int = 100

# =================== Security Configuration ===================

@dataclass
class SecurityConfig:
    """Configurações de segurança"""
    secret_key: str = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    
    # JWT
    jwt_secret: str = os.getenv("JWT_SECRET", secret_key)
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = int(os.getenv("JWT_EXPIRATION", "60"))
    
    # CORS
    cors_origins: List[str] = field(default_factory=lambda: [
        "http://localhost:8501",
        "http://localhost:3000",
        "https://aide.app"
    ])
    
    # Rate limiting
    rate_limit_enabled: bool = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
    rate_limit_requests: int = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
    rate_limit_period: int = int(os.getenv("RATE_LIMIT_PERIOD", "60"))  # segundos
    
    # Encryption
    encrypt_sensitive_data: bool = True
    encryption_key: str = os.getenv("ENCRYPTION_KEY", "")

# =================== Monitoring Configuration ===================

@dataclass
class MonitoringConfig:
    """Configurações de monitoramento"""
    enable_monitoring: bool = os.getenv("ENABLE_MONITORING", "true").lower() == "true"
    
    # Metrics
    metrics_interval: int = int(os.getenv("METRICS_INTERVAL", "300"))  # 5 minutos
    health_check_interval: int = int(os.getenv("HEALTH_CHECK_INTERVAL", "60"))
    
    # Alerting
    enable_alerts: bool = os.getenv("ENABLE_ALERTS", "true").lower() == "true"
    alert_email: str = os.getenv("ALERT_EMAIL", "")
    alert_webhook: str = os.getenv("ALERT_WEBHOOK", "")
    
    # Telegram
    telegram_bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    telegram_chat_id: str = os.getenv("TELEGRAM_CHAT_ID", "")
    
    # Slack
    slack_webhook: str = os.getenv("SLACK_WEBHOOK", "")
    slack_channel: str = os.getenv("SLACK_CHANNEL", "#aide-alerts")
    
    # Thresholds
    cpu_threshold: float = float(os.getenv("CPU_THRESHOLD", "80"))
    memory_threshold: float = float(os.getenv("MEMORY_THRESHOLD", "80"))
    disk_threshold: float = float(os.getenv("DISK_THRESHOLD", "80"))
    error_rate_threshold: float = float(os.getenv("ERROR_RATE_THRESHOLD", "5"))

# =================== Logging Configuration ===================

@dataclass
class LoggingConfig:
    """Configurações de logging"""
    level: str = os.getenv("LOG_LEVEL", "INFO")
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # File logging
    enable_file_logging: bool = True
    log_file: str = str(LOGS_DIR / "aide.log")
    max_bytes: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5
    
    # Console logging
    enable_console_logging: bool = True
    
    # Sentry
    sentry_dsn: str = os.getenv("SENTRY_DSN", "")
    sentry_environment: str = ENVIRONMENT
    sentry_traces_sample_rate: float = float(os.getenv("SENTRY_TRACES_RATE", "0.1"))

# =================== Feature Flags ===================

@dataclass
class FeatureFlags:
    """Feature flags do sistema"""
    enable_ai_chat: bool = os.getenv("FEATURE_AI_CHAT", "true").lower() == "true"
    enable_data_export: bool = os.getenv("FEATURE_DATA_EXPORT", "true").lower() == "true"
    enable_advanced_analytics: bool = os.getenv("FEATURE_ADVANCED_ANALYTICS", "true").lower() == "true"
    enable_real_time_updates: bool = os.getenv("FEATURE_REAL_TIME", "false").lower() == "true"
    enable_multi_language: bool = os.getenv("FEATURE_MULTI_LANGUAGE", "false").lower() == "true"
    enable_dark_mode: bool = os.getenv("FEATURE_DARK_MODE", "true").lower() == "true"
    enable_api_access: bool = os.getenv("FEATURE_API_ACCESS", "false").lower() == "true"
    enable_notifications: bool = os.getenv("FEATURE_NOTIFICATIONS", "true").lower() == "true"

# =================== Main Configuration Class ===================

@dataclass
class Config:
    """Configuração principal do sistema"""
    # Environment
    environment: str = ENVIRONMENT
    debug: bool = DEBUG
    
    # Components
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    redis: RedisConfig = field(default_factory=RedisConfig)
    ai: AIConfig = field(default_factory=AIConfig)
    n8n: N8NConfig = field(default_factory=N8NConfig)
    ons: ONSConfig = field(default_factory=ONSConfig)
    streamlit: StreamlitConfig = field(default_factory=StreamlitConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    features: FeatureFlags = field(default_factory=FeatureFlags)
    
    # Paths
    base_dir: Path = BASE_DIR
    data_dir: Path = DATA_DIR
    logs_dir: Path = LOGS_DIR
    cache_dir: Path = CACHE_DIR
    assets_dir: Path = ASSETS_DIR
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte configuração para dicionário"""
        return {
            "environment": self.environment,
            "debug": self.debug,
            "database": {
                "host": self.database.host,
                "port": self.database.port,
                "database": self.database.database
            },
            "redis": {
                "host": self.redis.host,
                "port": self.redis.port
            },
            "features": {
                "ai_chat": self.features.enable_ai_chat,
                "data_export": self.features.enable_data_export,
                "analytics": self.features.enable_advanced_analytics
            }
        }
    
    def validate(self) -> bool:
        """Valida configurações"""
        errors = []
        
        # Validar database
        if not self.database.password and self.environment == Environment.PRODUCTION:
            errors.append("Database password is required in production")
        
        # Validar AI keys
        if self.features.enable_ai_chat:
            if not self.ai.openai_api_key and not self.ai.anthropic_api_key:
                errors.append("At least one AI API key is required when AI chat is enabled")
        
        # Validar security
        if self.security.secret_key == "dev-secret-key-change-in-production" and self.environment == Environment.PRODUCTION:
            errors.append("Secret key must be changed in production")
        
        if errors:
            for error in errors:
                logger.error(f"Configuration error: {error}")
            return False
        
        logger.info("Configuration validated successfully")
        return True
    
    def save_to_file(self, filepath: Path):
        """Salva configuração em arquivo"""
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    @classmethod
    def load_from_file(cls, filepath: Path) -> 'Config':
        """Carrega configuração de arquivo"""
        with open(filepath, 'r') as f:
            data = json.load(f)
        # Implementar lógica de parsing
        return cls()

# =================== Singleton Instance ===================

@lru_cache(maxsize=1)
def get_config() -> Config:
    """Retorna instância singleton da configuração"""
    config = Config()
    
    # Validar em produção
    if config.environment == Environment.PRODUCTION:
        if not config.validate():
            raise ValueError("Invalid configuration for production environment")
    
    logger.info(f"Configuration loaded for environment: {config.environment}")
    return config

# =================== Helper Functions ===================

def get_database_url() -> str:
    """Retorna URL do banco de dados"""
    return get_config().database.url

def get_redis_url() -> str:
    """Retorna URL do Redis"""
    return get_config().redis.url

def is_production() -> bool:
    """Verifica se está em produção"""
    return get_config().environment == Environment.PRODUCTION

def is_debug() -> bool:
    """Verifica se está em modo debug"""
    return get_config().debug

def get_feature_flag(flag_name: str) -> bool:
    """Retorna valor de uma feature flag"""
    return getattr(get_config().features, f"enable_{flag_name}", False)

# =================== Constants ===================

# Regiões do SIN
REGIONS = {
    "SE/CO": "Sudeste/Centro-Oeste",
    "S": "Sul",
    "NE": "Nordeste",
    "N": "Norte"
}

# Tipos de dados
DATA_TYPES = {
    "carga_energia": "Carga de Energia",
    "cmo_pld": "CMO/PLD",
    "bandeiras_tarifarias": "Bandeiras Tarifárias",
    "geracao_usina": "Geração por Usina",
    "reservatorios": "Reservatórios",
    "intercambio": "Intercâmbio Regional"
}

# Unidades
UNITS = {
    "energy": "MWh",
    "power": "MW",
    "price": "R$/MWh",
    "percentage": "%",
    "volume": "hm³",
    "flow": "m³/s"
}

# Export formats
EXPORT_FORMATS = ["CSV", "Excel", "JSON", "PDF", "HTML"]

# Time aggregations
TIME_AGGREGATIONS = ["Hourly", "Daily", "Weekly", "Monthly", "Yearly"]

# Bandeiras tarifárias
BANDEIRAS = {
    "verde": {"name": "Verde", "value": 0.00, "color": "#10b981"},
    "amarela": {"name": "Amarela", "value": 2.989, "color": "#fbbf24"},
    "vermelha_1": {"name": "Vermelha 1", "value": 6.500, "color": "#f87171"},
    "vermelha_2": {"name": "Vermelha 2", "value": 9.795, "color": "#dc2626"}
}

# Inicializar configuração ao importar
config = get_config()