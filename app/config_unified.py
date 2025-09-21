# ASPI - Configuration
# Arquivo de configuração unificado do projeto

import os
from pathlib import Path
from typing import Dict, Any

# Configurações do Projeto
PROJECT_NAME = "ASPI - Assistente Inteligente para Dados do Setor Elétrico"
VERSION = "1.0.0"
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

# Caminhos
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
WORKFLOWS_DIR = BASE_DIR / "workflows"
LOGS_DIR = BASE_DIR / "logs"

# Configurações do Streamlit
STREAMLIT_CONFIG = {
    "page_title": "ASPI - Sistema Inteligente",
    "page_icon": "⚡",
    "layout": "wide",
    "initial_sidebar_state": "expanded"
}

# Configurações do Banco de Dados
DATABASE_CONFIG = {
    "url": os.getenv("DATABASE_URL", "postgresql://aspi:aspi@localhost:5432/aspi_db"),
    "echo": DEBUG,
    "pool_size": int(os.getenv("DB_POOL_SIZE", "10")),
    "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "20"))
}

# Configurações do Redis (Cache)
REDIS_CONFIG = {
    "url": os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    "decode_responses": True,
    "max_connections": int(os.getenv("REDIS_MAX_CONNECTIONS", "20"))
}

# Configurações do n8n
N8N_CONFIG = {
    "base_url": os.getenv("N8N_BASE_URL", "http://localhost:5678"),
    "api_key": os.getenv("N8N_API_KEY", ""),
    "webhook_token": os.getenv("N8N_WEBHOOK_TOKEN", ""),
    "timeout": int(os.getenv("N8N_TIMEOUT", "30")),
    "max_retries": int(os.getenv("N8N_MAX_RETRIES", "3"))
}

# Configurações de IA
AI_CONFIG = {
    "openai_api_key": os.getenv("OPENAI_API_KEY", ""),
    "anthropic_api_key": os.getenv("ANTHROPIC_API_KEY", ""),
    "default_model": os.getenv("DEFAULT_AI_MODEL", "gpt-4"),
    "max_tokens": int(os.getenv("AI_MAX_TOKENS", "2000")),
    "temperature": float(os.getenv("AI_TEMPERATURE", "0.7"))
}

# Configurações do ONS
ONS_CONFIG = {
    "base_url": "https://dados.ons.org.br/api/3/action/package_show?id=",
    "api_carga_url": "https://apicarga.ons.org.br/prd",
    "timeout": int(os.getenv("ONS_TIMEOUT", "60")),
    "max_retries": int(os.getenv("ONS_MAX_RETRIES", "3"))
}

# Configurações de Logging
LOGGING_CONFIG = {
    "level": os.getenv("LOG_LEVEL", "INFO"),
    "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    "file_path": LOGS_DIR / "aspi.log" if LOGS_DIR else None
}

# Configurações de Monitoramento
MONITORING_CONFIG = {
    "enabled": os.getenv("MONITORING_ENABLED", "True").lower() == "true",
    "prometheus_port": int(os.getenv("PROMETHEUS_PORT", "8000")),
    "health_check_interval": int(os.getenv("HEALTH_CHECK_INTERVAL", "60"))
}

# Datasets ONS Disponíveis
DATASETS_CONFIG = {
    "api_datasets": [
        "cargaProgramada",
        "cargaVerificada"
    ],
    "ckan_datasets": [
        "curva-carga",
        "cmo-semi-horario", 
        "cmo-semanal",
        "carga-mensal",
        "carga-diaria",
        "balanco-dessem-geral",
        "balanco-dessem-detalhe"
    ]
}

def get_config() -> Dict[str, Any]:
    """Retorna configuração completa do sistema."""
    return {
        "project": {
            "name": PROJECT_NAME,
            "version": VERSION,
            "debug": DEBUG
        },
        "paths": {
            "base_dir": str(BASE_DIR),
            "data_dir": str(DATA_DIR),
            "workflows_dir": str(WORKFLOWS_DIR),
            "logs_dir": str(LOGS_DIR) if LOGS_DIR else None
        },
        "streamlit": STREAMLIT_CONFIG,
        "database": DATABASE_CONFIG,
        "redis": REDIS_CONFIG,
        "n8n": N8N_CONFIG,
        "ai": AI_CONFIG,
        "ons": ONS_CONFIG,
        "logging": LOGGING_CONFIG,
        "monitoring": MONITORING_CONFIG,
        "datasets": DATASETS_CONFIG
    }