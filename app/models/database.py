"""
models/database.py
Modelos SQLAlchemy para o banco de dados PostgreSQL
"""

from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Date, Boolean, Text, 
    ForeignKey, Index, UniqueConstraint, CheckConstraint, JSON, ARRAY,
    DECIMAL, BigInteger, Enum as SQLEnum, Time
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID, JSONB, TIMESTAMP
from datetime import datetime, date
import enum
from sqlalchemy.orm import Mapped, mapped_column
import uuid

from typing import Any
Base: Any = declarative_base()

# =================== Enums ===================

class DataSourceType(enum.Enum):
    """Tipos de fonte de dados"""
    ONS = "ons"
    ANEEL = "aneel"
    CCEE = "ccee"
    EPE = "epe"
    MANUAL = "manual"
    API = "api"

class DatasetStatus(enum.Enum):
    """Status do dataset"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    UPDATING = "updating"
    ERROR = "error"
    DEPRECATED = "deprecated"

class BandeiraTarifaria(enum.Enum):
    """Tipos de bandeira tarifária"""
    VERDE = "verde"
    AMARELA = "amarela"
    VERMELHA_1 = "vermelha_1"
    VERMELHA_2 = "vermelha_2"
    ESCASSEZ = "escassez"

class RegionType(enum.Enum):
    """Subsistemas do SIN"""
    SUDESTE_CO = "SE/CO"
    SUL = "S"
    NORDESTE = "NE"
    NORTE = "N"
    BRASIL = "BR"

# =================== Mixins ===================

class TimestampMixin:
    """Mixin para timestamps automáticos"""
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

class SoftDeleteMixin:
    """Mixin para soft delete"""
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False)

# =================== Modelos Principais ===================

class Dataset(Base, TimestampMixin, SoftDeleteMixin):
    """Datasets disponíveis no sistema"""
    __tablename__ = 'datasets'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, unique=True, index=True)
    display_name: Mapped[str | None] = mapped_column(String(300))
    description: Mapped[str | None] = mapped_column(Text)
    # Fonte e tipo
    source_type: Mapped[DataSourceType] = mapped_column(SQLEnum(DataSourceType), nullable=False, default=DataSourceType.ONS)
    source_url: Mapped[str | None] = mapped_column(String(500))
    api_endpoint: Mapped[str | None] = mapped_column(String(500))
    # Metadados
    meta_data: Mapped[dict] = mapped_column(JSONB, default={})
    fields_schema: Mapped[dict] = mapped_column(JSONB, default={})
    tags: Mapped[list[str]] = mapped_column(ARRAY(String), default=[])
    category: Mapped[str | None] = mapped_column(String(100), index=True)
    # Status e atualização
    status: Mapped[DatasetStatus] = mapped_column(SQLEnum(DatasetStatus), default=DatasetStatus.ACTIVE, nullable=False)
    last_updated: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True))
    update_frequency: Mapped[str | None] = mapped_column(String(50))  # hourly, daily, weekly, monthly
    next_update: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True))
    # Estatísticas
    row_count: Mapped[int] = mapped_column(BigInteger, default=0)
    size_bytes: Mapped[int] = mapped_column(BigInteger, default=0)
    # Configurações
    is_critical: Mapped[bool] = mapped_column(Boolean, default=False)
    auto_update: Mapped[bool] = mapped_column(Boolean, default=True)
    retention_days: Mapped[int] = mapped_column(Integer, default=365)
    # Relacionamentos
    records: Mapped[list["DataRecord"]] = relationship("DataRecord", back_populates="dataset", cascade="all, delete-orphan")
    # Relacionamentos
    # ...
    
    # Índices
    __table_args__ = (
        Index('idx_dataset_status_category', 'status', 'category'),
        Index('idx_dataset_source_type', 'source_type'),
        Index('idx_dataset_tags', 'tags', postgresql_using='gin'),
    )

class DataRecord(Base, TimestampMixin):
    """Registros de dados processados"""
    __tablename__ = 'data_records'
    
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    dataset_id: Mapped[int] = mapped_column(Integer, ForeignKey('datasets.id'), nullable=False)

    # Dimensões temporais
    timestamp: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, index=True)
    period_start: Mapped[datetime | None] = mapped_column(Date, index=True)
    period_end: Mapped[datetime | None] = mapped_column(Date)
    year: Mapped[int | None] = mapped_column(Integer, index=True)
    month: Mapped[int | None] = mapped_column(Integer, index=True)
    day: Mapped[int | None] = mapped_column(Integer)
    hour: Mapped[int | None] = mapped_column(Integer)

    # Dimensões geográficas
    region: Mapped[str | None] = mapped_column(String(100), index=True)
    subsystem: Mapped[RegionType | None] = mapped_column(SQLEnum(RegionType))
    state: Mapped[str | None] = mapped_column(String(2))
    city: Mapped[str | None] = mapped_column(String(100))

    # Métricas
    metric_type: Mapped[str | None] = mapped_column(String(100), index=True)
    metric_name: Mapped[str | None] = mapped_column(String(255))
    value: Mapped[float] = mapped_column(DECIMAL(20, 6), nullable=False)
    unit: Mapped[str | None] = mapped_column(String(50))

    # Dados estruturados
    raw_data: Mapped[dict] = mapped_column(JSONB, default={})
    processed_data: Mapped[dict] = mapped_column(JSONB, default={})
    meta_data: Mapped[dict] = mapped_column(JSONB, default={})

    # Qualidade
    quality_flag: Mapped[str | None] = mapped_column(String(20))  # verified, estimated, error
    source: Mapped[str | None] = mapped_column(String(100))
    version: Mapped[str | None] = mapped_column(String(20))

    # Relacionamentos
    dataset: Mapped["Dataset"] = relationship("Dataset", back_populates="records")
    
    # Índices e constraints
    __table_args__ = (
        Index('idx_data_record_temporal', 'dataset_id', 'timestamp', 'region'),
        Index('idx_data_record_metric', 'metric_type', 'timestamp'),
        Index('idx_data_record_year_month', 'year', 'month'),
        Index('idx_data_record_meta_data', 'meta_data', postgresql_using='gin'),
        UniqueConstraint('dataset_id', 'timestamp', 'region', 'metric_type', 
                        name='uq_data_record_unique'),
    )

class CargaEnergia(Base, TimestampMixin):
    """Dados específicos de carga de energia"""
    __tablename__ = 'carga_energia'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    
    # Identificação
    
    # Temporal
    
    # Valores
    
    # Estatísticas
    
    # Metadados
    id_subsistema: Mapped[str] = mapped_column(String(3), nullable=False)
    nom_subsistema: Mapped[str] = mapped_column(String(60), nullable=False)
    din_instante: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, index=True)
    val_cargaenergiamwmed: Mapped[float] = mapped_column(Float, nullable=False)
    val_cargaenergiamwh: Mapped[float | None] = mapped_column(Float)
    max_daily: Mapped[float | None] = mapped_column(Float)
    min_daily: Mapped[float | None] = mapped_column(Float)
    avg_daily: Mapped[float | None] = mapped_column(Float)
    std_dev: Mapped[float | None] = mapped_column(Float)
    meta_data: Mapped[dict] = mapped_column(JSONB, default={})
    
    __table_args__ = (
        Index('idx_carga_energia_subsistema_data', 'id_subsistema', 'din_instante'),
        UniqueConstraint('id_subsistema', 'din_instante', name='uq_carga_energia'),
    )

class CMO(Base, TimestampMixin):
    """Custo Marginal de Operação"""
    __tablename__ = 'cmo'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    
    # Identificação
    
    # Temporal
    
    # Valores por patamar
    
    # Semi-horário
    
    # Metadados
    id_subsistema: Mapped[str] = mapped_column(String(3), nullable=False)
    nom_subsistema: Mapped[str] = mapped_column(String(20), nullable=False)
    din_instante: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, index=True)
    val_cmoleve: Mapped[float | None] = mapped_column(DECIMAL(10, 2))
    val_cmomedia: Mapped[float | None] = mapped_column(DECIMAL(10, 2))
    val_cmopesada: Mapped[float | None] = mapped_column(DECIMAL(10, 2))
    val_cmomediasemanal: Mapped[float | None] = mapped_column(DECIMAL(10, 2))
    val_cmo: Mapped[float | None] = mapped_column(DECIMAL(10, 2))
    patamar: Mapped[str | None] = mapped_column(String(20))
    meta_data: Mapped[dict] = mapped_column(JSONB, default={})
    
    __table_args__ = (
        Index('idx_cmo_subsistema_data', 'id_subsistema', 'din_instante'),
    )

class BandeiraTarifariaAcionamento(Base, TimestampMixin):
    """Acionamento de bandeiras tarifárias"""
    __tablename__ = 'bandeira_tarifaria_acionamento'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Datas
    
    # Bandeira
    
    # Valores
    
    # Metadados
    dat_geracao_conjunto_dados: Mapped[date] = mapped_column(Date, nullable=False)
    dat_competencia: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    nom_bandeira_acionada: Mapped[str] = mapped_column(String(100), nullable=False)
    tipo_bandeira: Mapped[BandeiraTarifaria] = mapped_column(SQLEnum(BandeiraTarifaria), nullable=False)
    vlr_adicional_bandeira: Mapped[float] = mapped_column(DECIMAL(10, 2), nullable=False)
    vlr_adicional_kwh: Mapped[float | None] = mapped_column(DECIMAL(10, 4))
    motivo_acionamento: Mapped[str | None] = mapped_column(Text)
    meta_data: Mapped[dict] = mapped_column(JSONB, default={})
    
    __table_args__ = (
        UniqueConstraint('dat_competencia', name='uq_bandeira_competencia'),
    )

class Reservatorio(Base, TimestampMixin):
    """Níveis de reservatórios"""
    __tablename__ = 'reservatorios'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    
    # Identificação
    nome_reservatorio: Mapped[str] = mapped_column(String(100), nullable=False)
    codigo_reservatorio: Mapped[str | None] = mapped_column(String(20), unique=True)
    subsistema: Mapped[RegionType] = mapped_column(SQLEnum(RegionType), nullable=False)
    bacia = Column(String(100))
    rio = Column(String(100))
    
    # Temporal
    data_medicao: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    
    # Níveis
    nivel_atual: Mapped[float | None] = mapped_column(DECIMAL(10, 2))  # metros
    volume_util: Mapped[float | None] = mapped_column(DECIMAL(15, 2))  # hm³
    volume_util_percentual: Mapped[float | None] = mapped_column(DECIMAL(5, 2))  # %
    
    # Vazões
    vazao_afluente: Mapped[float | None] = mapped_column(DECIMAL(10, 2))  # m³/s
    vazao_defluente: Mapped[float | None] = mapped_column(DECIMAL(10, 2))  # m³/s
    vazao_vertida: Mapped[float | None] = mapped_column(DECIMAL(10, 2))  # m³/s
    vazao_turbinada: Mapped[float | None] = mapped_column(DECIMAL(10, 2))  # m³/s
    
    # Energia
    energia_armazenada: Mapped[float | None] = mapped_column(DECIMAL(15, 2))  # MWmês
    energia_armazenada_percentual: Mapped[float | None] = mapped_column(DECIMAL(5, 2))  # %
    
    # Metadados
    meta_data: Mapped[dict] = mapped_column(JSONB, default={})
    
    __table_args__ = (
        Index('idx_reservatorio_data', 'codigo_reservatorio', 'data_medicao'),
        UniqueConstraint('codigo_reservatorio', 'data_medicao', 
                        name='uq_reservatorio_medicao'),
    )

class GeracaoUsina(Base, TimestampMixin):
    """Geração por usina"""
    __tablename__ = 'geracao_usina'
    
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    # Identificação
    nome_usina: Mapped[str] = mapped_column(String(100), nullable=False)
    codigo_usina: Mapped[str | None] = mapped_column(String(20), index=True)
    tipo_usina: Mapped[str | None] = mapped_column(String(50))  # UHE, UTE, EOL, UFV, UTN
    fonte_geracao: Mapped[str | None] = mapped_column(String(50))  # Hídrica, Térmica, Eólica, Solar, Nuclear
    subsistema: Mapped[RegionType | None] = mapped_column(SQLEnum(RegionType))

    # Temporal
    data_hora: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, index=True)

    # Geração
    geracao_mw: Mapped[float] = mapped_column(DECIMAL(10, 2), nullable=False)
    geracao_mwmed: Mapped[float | None] = mapped_column(DECIMAL(10, 2))
    capacidade_instalada: Mapped[float | None] = mapped_column(DECIMAL(10, 2))
    fator_capacidade: Mapped[float | None] = mapped_column(DECIMAL(5, 2))  # %

    # Status
    status_operacao: Mapped[str | None] = mapped_column(String(20))  # operando, parada, manutenção
    disponibilidade: Mapped[float | None] = mapped_column(DECIMAL(5, 2))  # %

    # Metadados
    meta_data: Mapped[dict] = mapped_column(JSONB, default={})
    
    __table_args__ = (
        Index('idx_geracao_usina_temporal', 'codigo_usina', 'data_hora'),
        Index('idx_geracao_fonte', 'fonte_geracao', 'data_hora'),
    )

class IntercambioRegional(Base, TimestampMixin):
    """Intercâmbio entre subsistemas"""
    __tablename__ = 'intercambio_regional'
    
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    # Identificação
    subsistema_origem: Mapped[RegionType] = mapped_column(SQLEnum(RegionType), nullable=False)
    subsistema_destino: Mapped[RegionType] = mapped_column(SQLEnum(RegionType), nullable=False)

    # Temporal
    data_hora: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, index=True)

    # Valores
    valor_mw: Mapped[float] = mapped_column(DECIMAL(10, 2), nullable=False)
    valor_mwmed: Mapped[float | None] = mapped_column(DECIMAL(10, 2))
    capacidade_maxima: Mapped[float | None] = mapped_column(DECIMAL(10, 2))
    utilizacao_percentual: Mapped[float | None] = mapped_column(DECIMAL(5, 2))

    # Limites
    limite_tecnico: Mapped[float | None] = mapped_column(DECIMAL(10, 2))
    limite_operacional: Mapped[float | None] = mapped_column(DECIMAL(10, 2))

    # Metadados
    restricoes: Mapped[dict] = mapped_column(JSONB, default={})
    meta_data: Mapped[dict] = mapped_column(JSONB, default={})

    __table_args__ = (
        Index('idx_intercambio_subsistemas', 'subsistema_origem', 
              'subsistema_destino', 'data_hora'),
        CheckConstraint('subsistema_origem != subsistema_destino', 
                       name='ck_intercambio_diferentes'),
    )

# =================== Tabelas de Suporte ===================

class ChatHistory(Base, TimestampMixin, SoftDeleteMixin):
    """Histórico de conversas do chat"""
    __tablename__ = 'chat_history'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    session_id = Column(String(100), nullable=False, index=True)
    user_id = Column(String(100), nullable=False, index=True)
    
    # Mensagem
    role = Column(String(20), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    
    # Análise
    intent = Column(String(50))
    confidence = Column(Float)
    entities = Column(JSONB, default={})
    
    # Resposta
    response_time_ms = Column(Integer)
    tokens_used = Column(Integer)
    model_used = Column(String(50))
    
    # Metadados
    meta_data = Column(JSONB, default={})
    
    __table_args__ = (
        Index('idx_chat_history_session', 'session_id', 'created_at'),
        Index('idx_chat_history_user', 'user_id', 'created_at'),
    )

class MonitoringMetrics(Base, TimestampMixin):
    """Métricas de monitoramento do sistema"""
    __tablename__ = 'monitoring_metrics'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    
    # Identificação
    metric_name = Column(String(100), nullable=False, index=True)
    metric_type = Column(String(50))  # health, performance, business
    
    # Status
    status = Column(String(20), nullable=False)  # ok, warning, error, critical
    value: Mapped[float | None] = mapped_column(DECIMAL(20, 6), nullable=False)
    unit = Column(String(20))
    
    # Detalhes
    message = Column(Text)
    severity = Column(String(20))  # low, medium, high, critical
    details = Column(JSONB, default={})
    
    # Timestamps
    timestamp = Column(TIMESTAMP(timezone=True), nullable=False, index=True)
    
    __table_args__ = (
        Index('idx_monitoring_status', 'status', 'timestamp'),
        Index('idx_monitoring_metric_time', 'metric_name', 'timestamp'),
    )

class JobQueue(Base, TimestampMixin):
    """Fila de jobs para processamento"""
    __tablename__ = 'job_queue'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    job_id = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False)
    
    # Job info
    job_type = Column(String(50), nullable=False)  # ingestion, processing, export
    job_name = Column(String(255), nullable=False)
    priority = Column(Integer, default=5)  # 1-10, 1 = highest
    
    # Status
    status = Column(String(20), default='pending')  # pending, running, completed, failed
    progress = Column(Integer, default=0)  # 0-100
    
    # Execução
    scheduled_at = Column(TIMESTAMP(timezone=True))
    started_at = Column(TIMESTAMP(timezone=True))
    completed_at = Column(TIMESTAMP(timezone=True))
    
    # Payload e resultado
    payload = Column(JSONB, default={})
    result = Column(JSONB, default={})
    error = Column(Text)
    
    # Retry
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    
    __table_args__ = (
        Index('idx_job_queue_status', 'status', 'priority'),
        Index('idx_job_queue_type', 'job_type', 'status'),
    )

class ErrorLog(Base, TimestampMixin):
    """Log de erros do sistema"""
    __tablename__ = 'error_logs'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    
    # Identificação
    error_id = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True)
    error_type = Column(String(100), nullable=False)
    error_code = Column(String(50))
    
    # Detalhes
    message = Column(Text, nullable=False)
    stack_trace = Column(Text)
    context = Column(JSONB, default={})
    
    # Origem
    source = Column(String(100))  # module/service that generated the error
    user_id = Column(String(100))
    session_id = Column(String(100))
    
    # Severidade
    severity = Column(String(20), nullable=False)  # debug, info, warning, error, critical
    
    # Resolução
    resolved = Column(Boolean, default=False)
    resolved_at = Column(TIMESTAMP(timezone=True))
    resolution_notes = Column(Text)
    
    __table_args__ = (
        Index('idx_error_log_severity', 'severity', 'created_at'),
        Index('idx_error_log_type', 'error_type', 'created_at'),
        Index('idx_error_log_resolved', 'resolved', 'created_at'),
    )

# =================== Views e Tabelas Materializadas ===================

class DatasetSummary(Base):
    """View materializada com resumo dos datasets"""
    __tablename__ = 'mv_dataset_summary'
    
    dataset_id = Column(Integer, primary_key=True)
    dataset_name = Column(String(255))
    total_records = Column(BigInteger)
    last_update = Column(TIMESTAMP(timezone=True))
    avg_daily_records = Column(Float)
    data_quality_score = Column(Float)
    
    __table_args__ = (
        {'info': {'is_view': True}},
    )