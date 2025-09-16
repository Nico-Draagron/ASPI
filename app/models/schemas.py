"""
models/schemas.py
Schemas Pydantic para validação e serialização de dados
"""

from pydantic import BaseModel, Field, validator, ConfigDict
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, date
from decimal import Decimal
from enum import Enum

# =================== Enums ===================

class RegionEnum(str, Enum):
    """Subsistemas do SIN"""
    SUDESTE_CO = "SE/CO"
    SUL = "S"
    NORDESTE = "NE"
    NORTE = "N"
    BRASIL = "BR"

class DatasetTypeEnum(str, Enum):
    """Tipos de dataset"""
    CARGA_ENERGIA = "carga_energia"
    CMO_PLD = "cmo_pld"
    BANDEIRAS_TARIFARIAS = "bandeiras_tarifarias"
    GERACAO = "geracao"
    RESERVATORIOS = "reservatorios"
    INTERCAMBIO = "intercambio"

class BandeiraEnum(str, Enum):
    """Bandeiras tarifárias"""
    VERDE = "verde"
    AMARELA = "amarela"
    VERMELHA_1 = "vermelha_1"
    VERMELHA_2 = "vermelha_2"
    ESCASSEZ = "escassez"

class ChatRoleEnum(str, Enum):
    """Roles do chat"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class StatusEnum(str, Enum):
    """Status genérico"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"

# =================== Base Schemas ===================

class BaseSchema(BaseModel):
    """Schema base com configurações padrão"""
    model_config = ConfigDict(
        from_attributes=True,
        validate_assignment=True,
        use_enum_values=True,
        json_encoders={
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat(),
            Decimal: lambda v: float(v)
        }
    )

class TimestampedSchema(BaseSchema):
    """Schema com timestamps"""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

# =================== Dataset Schemas ===================

class DatasetBase(BaseSchema):
    """Base para dataset"""
    external_id: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=255)
    display_name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    source_type: str = "ONS"
    category: Optional[str] = None
    tags: List[str] = []
    
    @validator('tags')
    def validate_tags(cls, v):
        return [tag.lower().strip() for tag in v if tag.strip()]

class DatasetCreate(DatasetBase):
    """Schema para criar dataset"""
    source_url: Optional[str] = None
    update_frequency: str = "daily"
    is_critical: bool = False
    auto_update: bool = True

class DatasetUpdate(BaseSchema):
    """Schema para atualizar dataset"""
    display_name: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    auto_update: Optional[bool] = None
    status: Optional[StatusEnum] = None

class DatasetResponse(DatasetBase, TimestampedSchema):
    """Schema de resposta para dataset"""
    id: int
    status: StatusEnum
    last_updated: Optional[datetime] = None
    row_count: int = 0
    size_bytes: int = 0
    metadata: Dict[str, Any] = {}

# =================== Data Record Schemas ===================

class DataRecordBase(BaseSchema):
    """Base para registro de dados"""
    dataset_id: int
    timestamp: datetime
    region: Optional[RegionEnum] = None
    metric_type: str
    value: float
    unit: str
    
    @validator('value')
    def validate_value(cls, v):
        if v is None or np.isnan(v) or np.isinf(v):
            raise ValueError('Invalid value')
        return v

class DataRecordCreate(DataRecordBase):
    """Schema para criar registro"""
    metadata: Dict[str, Any] = {}
    quality_flag: str = "verified"
    source: str = "ONS"

class DataRecordResponse(DataRecordBase, TimestampedSchema):
    """Schema de resposta para registro"""
    id: int
    year: Optional[int] = None
    month: Optional[int] = None
    day: Optional[int] = None
    hour: Optional[int] = None
    processed_data: Dict[str, Any] = {}

# =================== Carga Energia Schemas ===================

class CargaEnergiaBase(BaseSchema):
    """Base para carga de energia"""
    subsistema: RegionEnum
    timestamp: datetime
    carga_mw: float
    
    @validator('carga_mw')
    def validate_carga(cls, v):
        if v < 0:
            raise ValueError('Carga não pode ser negativa')
        if v > 100000:  # Limite máximo razoável
            raise ValueError('Carga excede limite máximo')
        return v

class CargaEnergiaCreate(CargaEnergiaBase):
    """Schema para criar carga"""
    carga_mwh: Optional[float] = None

class CargaEnergiaResponse(CargaEnergiaBase):
    """Schema de resposta para carga"""
    id: int
    max_daily: Optional[float] = None
    min_daily: Optional[float] = None
    avg_daily: Optional[float] = None
    std_dev: Optional[float] = None

class CargaEnergiaAnalysis(BaseSchema):
    """Schema para análise de carga"""
    period_start: datetime
    period_end: datetime
    regions: List[RegionEnum]
    metrics: Dict[str, float]
    patterns: List[str]
    anomalies: List[Dict[str, Any]]
    forecast: Optional[Dict[str, Any]] = None

# =================== CMO/PLD Schemas ===================

class CMOBase(BaseSchema):
    """Base para CMO"""
    subsistema: RegionEnum
    timestamp: datetime
    cmo_medio: float
    
    @validator('cmo_medio')
    def validate_cmo(cls, v):
        if v < 0:
            raise ValueError('CMO não pode ser negativo')
        if v > 10000:  # Limite máximo razoável
            raise ValueError('CMO excede limite máximo')
        return v

class CMOCreate(CMOBase):
    """Schema para criar CMO"""
    cmo_leve: Optional[float] = None
    cmo_media: Optional[float] = None
    cmo_pesada: Optional[float] = None
    patamar: Optional[str] = None

class CMOResponse(CMOBase):
    """Schema de resposta para CMO"""
    id: int
    cmo_leve: Optional[float] = None
    cmo_media: Optional[float] = None
    cmo_pesada: Optional[float] = None
    spread: Optional[float] = None

# =================== Bandeira Tarifária Schemas ===================

class BandeiraBase(BaseSchema):
    """Base para bandeira tarifária"""
    competencia: date
    bandeira: BandeiraEnum
    valor_adicional: Decimal
    
    @validator('valor_adicional')
    def validate_valor(cls, v):
        if v < 0:
            raise ValueError('Valor adicional não pode ser negativo')
        return v

class BandeiraCreate(BandeiraBase):
    """Schema para criar bandeira"""
    motivo: Optional[str] = None

class BandeiraResponse(BandeiraBase):
    """Schema de resposta para bandeira"""
    id: int
    motivo: Optional[str] = None
    impacto_estimado: Optional[float] = None

# =================== Chat Schemas ===================

class ChatMessageBase(BaseSchema):
    """Base para mensagem de chat"""
    content: str = Field(..., min_length=1, max_length=5000)
    role: ChatRoleEnum
    
    @validator('content')
    def validate_content(cls, v):
        return v.strip()

class ChatMessageCreate(ChatMessageBase):
    """Schema para criar mensagem"""
    user_id: str
    session_id: Optional[str] = None
    metadata: Dict[str, Any] = {}

class ChatMessageResponse(ChatMessageBase, TimestampedSchema):
    """Schema de resposta para mensagem"""
    id: int
    user_id: str
    session_id: str
    intent: Optional[str] = None
    confidence: Optional[float] = None
    entities: Dict[str, Any] = {}
    response_time_ms: Optional[int] = None

class ChatRequest(BaseSchema):
    """Schema para requisição de chat"""
    message: str = Field(..., min_length=1, max_length=2000)
    user_id: str
    session_id: Optional[str] = None
    context: Dict[str, Any] = {}

class ChatResponse(BaseSchema):
    """Schema para resposta de chat"""
    response: str
    session_id: str
    intent: Optional[str] = None
    confidence: Optional[float] = None
    data: Optional[Dict[str, Any]] = None
    visualizations: Optional[List[Dict]] = None
    suggestions: List[str] = []
    processing_time_ms: int

# =================== Analysis Schemas ===================

class AnalysisRequest(BaseSchema):
    """Schema para requisição de análise"""
    dataset_type: DatasetTypeEnum
    start_date: datetime
    end_date: datetime
    regions: Optional[List[RegionEnum]] = None
    metrics: List[str] = []
    aggregation: str = "daily"
    include_forecast: bool = False

class AnalysisResponse(BaseSchema):
    """Schema para resposta de análise"""
    request_id: str
    status: StatusEnum
    results: Dict[str, Any]
    insights: List[str]
    recommendations: List[str]
    confidence_score: float
    execution_time_ms: int

class MetricValue(BaseSchema):
    """Schema para valor de métrica"""
    name: str
    value: float
    unit: str
    timestamp: datetime
    region: Optional[RegionEnum] = None
    metadata: Dict[str, Any] = {}

# =================== Query Schemas ===================

class SQLQueryRequest(BaseSchema):
    """Schema para requisição de query SQL"""
    natural_language: str = Field(..., min_length=5, max_length=500)
    dataset_hints: Optional[List[DatasetTypeEnum]] = None
    limit: int = Field(default=100, le=1000)

class SQLQueryResponse(BaseSchema):
    """Schema para resposta de query SQL"""
    sql: str
    natural_language: str
    confidence: float
    warnings: List[str] = []
    estimated_rows: Optional[int] = None

# =================== Export Schemas ===================

class ExportRequest(BaseSchema):
    """Schema para requisição de exportação"""
    dataset_type: DatasetTypeEnum
    format: str = Field(..., pattern="^(csv|excel|json|pdf|html)$")
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    regions: Optional[List[RegionEnum]] = None
    include_charts: bool = False
    include_analysis: bool = False

class ExportResponse(BaseSchema):
    """Schema para resposta de exportação"""
    export_id: str
    status: StatusEnum
    file_url: Optional[str] = None
    file_size_bytes: Optional[int] = None
    format: str
    created_at: datetime

# =================== Monitoring Schemas ===================

class HealthCheckResponse(BaseSchema):
    """Schema para health check"""
    status: str = Field(..., pattern="^(healthy|degraded|unhealthy)$")
    timestamp: datetime
    version: str
    services: Dict[str, str]
    metrics: Dict[str, Any] = {}

class MetricReport(BaseSchema):
    """Schema para relatório de métrica"""
    metric_name: str
    value: float
    unit: Optional[str] = None
    status: StatusEnum
    threshold: Optional[float] = None
    timestamp: datetime
    metadata: Dict[str, Any] = {}

class SystemStatus(BaseSchema):
    """Schema para status do sistema"""
    health_score: int = Field(..., ge=0, le=100)
    status: str
    uptime_seconds: int
    active_users: int
    active_sessions: int
    queue_size: int
    error_rate: float
    response_time_avg_ms: float
    last_update: datetime

# =================== Validation Schemas ===================

class ValidationError(BaseSchema):
    """Schema para erro de validação"""
    field: str
    message: str
    value: Any

class ValidationResponse(BaseSchema):
    """Schema para resposta de validação"""
    valid: bool
    errors: List[ValidationError] = []
    warnings: List[str] = []

# =================== Pagination Schemas ===================

class PaginationParams(BaseSchema):
    """Schema para parâmetros de paginação"""
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    sort_by: Optional[str] = None
    sort_order: str = Field(default="desc", pattern="^(asc|desc)$")

class PaginatedResponse(BaseSchema):
    """Schema para resposta paginada"""
    items: List[Any]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_previous: bool

# =================== Helper Functions ===================

def validate_date_range(start_date: datetime, end_date: datetime) -> bool:
    """Valida intervalo de datas"""
    if start_date > end_date:
        raise ValueError("Data inicial não pode ser maior que data final")
    
    max_range = 365  # dias
    if (end_date - start_date).days > max_range:
        raise ValueError(f"Intervalo máximo permitido é {max_range} dias")
    
    return True

def sanitize_input(text: str) -> str:
    """Sanitiza entrada de texto"""
    import re
    # Remove caracteres perigosos
    text = re.sub(r'[<>\"\'%;()&+]', '', text)
    return text.strip()[:5000]  # Limita tamanho

# =================== Response Models ===================

class APIResponse(BaseSchema):
    """Schema padrão para respostas da API"""
    success: bool
    data: Optional[Any] = None
    message: Optional[str] = None
    errors: List[str] = []
    metadata: Dict[str, Any] = {}
    timestamp: datetime = Field(default_factory=datetime.now)

class ErrorResponse(BaseSchema):
    """Schema para respostas de erro"""
    error: str
    detail: Optional[str] = None
    status_code: int
    timestamp: datetime = Field(default_factory=datetime.now)
    trace_id: Optional[str] = None