-- database/migrations/001_initial_schema.sql
-- Criação inicial do schema do banco de dados AIDE

-- ===========================================
-- Extensions
-- ===========================================
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";
CREATE EXTENSION IF NOT EXISTS "postgres_fdw";

-- ===========================================
-- Custom Types
-- ===========================================
CREATE TYPE data_source_type AS ENUM ('ons', 'aneel', 'ccee', 'epe', 'manual', 'api');
CREATE TYPE dataset_status AS ENUM ('active', 'inactive', 'updating', 'error', 'deprecated');
CREATE TYPE bandeira_tarifaria AS ENUM ('verde', 'amarela', 'vermelha_1', 'vermelha_2', 'escassez');
CREATE TYPE region_type AS ENUM ('SE/CO', 'S', 'NE', 'N', 'BR');
CREATE TYPE chat_role AS ENUM ('user', 'assistant', 'system');
CREATE TYPE job_status AS ENUM ('pending', 'running', 'completed', 'failed', 'cancelled');

-- ===========================================
-- Tables
-- ===========================================

-- Datasets table
CREATE TABLE IF NOT EXISTS datasets (
    id SERIAL PRIMARY KEY,
    external_id VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    display_name VARCHAR(255) NOT NULL,
    description TEXT,
    source_type data_source_type DEFAULT 'ons',
    source_url VARCHAR(500),
    api_endpoint VARCHAR(500),
    metadata JSONB DEFAULT '{}',
    fields_schema JSONB DEFAULT '{}',
    tags TEXT[] DEFAULT '{}',
    category VARCHAR(100),
    status dataset_status DEFAULT 'active',
    last_updated TIMESTAMP WITH TIME ZONE,
    update_frequency VARCHAR(50),
    next_update TIMESTAMP WITH TIME ZONE,
    row_count BIGINT DEFAULT 0,
    size_bytes BIGINT DEFAULT 0,
    is_critical BOOLEAN DEFAULT FALSE,
    auto_update BOOLEAN DEFAULT TRUE,
    retention_days INTEGER DEFAULT 365,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE,
    is_deleted BOOLEAN DEFAULT FALSE
);

CREATE INDEX idx_datasets_external_id ON datasets(external_id);
CREATE INDEX idx_datasets_name ON datasets(name);
CREATE INDEX idx_datasets_status_category ON datasets(status, category);
CREATE INDEX idx_datasets_source_type ON datasets(source_type);
CREATE INDEX idx_datasets_tags ON datasets USING gin(tags);

-- Data records table
CREATE TABLE IF NOT EXISTS data_records (
    id BIGSERIAL PRIMARY KEY,
    dataset_id INTEGER REFERENCES datasets(id) ON DELETE CASCADE,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    period_start DATE,
    period_end DATE,
    year INTEGER,
    month INTEGER,
    day INTEGER,
    hour INTEGER,
    region VARCHAR(100),
    subsystem region_type,
    state VARCHAR(2),
    city VARCHAR(100),
    metric_type VARCHAR(100),
    metric_name VARCHAR(255),
    value DECIMAL(20, 6) NOT NULL,
    unit VARCHAR(50),
    raw_data JSONB DEFAULT '{}',
    processed_data JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    quality_flag VARCHAR(20),
    source VARCHAR(100),
    version VARCHAR(20),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_data_records_temporal ON data_records(dataset_id, timestamp, region);
CREATE INDEX idx_data_records_metric ON data_records(metric_type, timestamp);
CREATE INDEX idx_data_records_year_month ON data_records(year, month);
CREATE INDEX idx_data_records_metadata ON data_records USING gin(metadata);
CREATE UNIQUE INDEX uq_data_records_unique ON data_records(dataset_id, timestamp, region, metric_type) 
    WHERE region IS NOT NULL AND metric_type IS NOT NULL;

-- Carga de energia table
CREATE TABLE IF NOT EXISTS carga_energia (
    id BIGSERIAL PRIMARY KEY,
    id_subsistema VARCHAR(3) NOT NULL,
    nom_subsistema VARCHAR(60) NOT NULL,
    din_instante TIMESTAMP WITH TIME ZONE NOT NULL,
    val_cargaenergiamwmed FLOAT NOT NULL,
    val_cargaenergiamwh FLOAT,
    max_daily FLOAT,
    min_daily FLOAT,
    avg_daily FLOAT,
    std_dev FLOAT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_carga_energia_subsistema_data ON carga_energia(id_subsistema, din_instante);
CREATE UNIQUE INDEX uq_carga_energia ON carga_energia(id_subsistema, din_instante);

-- CMO table
CREATE TABLE IF NOT EXISTS cmo (
    id BIGSERIAL PRIMARY KEY,
    id_subsistema VARCHAR(3) NOT NULL,
    nom_subsistema VARCHAR(20) NOT NULL,
    din_instante TIMESTAMP WITH TIME ZONE NOT NULL,
    val_cmoleve DECIMAL(10, 2),
    val_cmomedia DECIMAL(10, 2),
    val_cmopesada DECIMAL(10, 2),
    val_cmomediasemanal DECIMAL(10, 2),
    val_cmo DECIMAL(10, 2),
    patamar VARCHAR(20),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_cmo_subsistema_data ON cmo(id_subsistema, din_instante);

-- Bandeira tarifária table
CREATE TABLE IF NOT EXISTS bandeira_tarifaria_acionamento (
    id SERIAL PRIMARY KEY,
    dat_geracao_conjunto_dados DATE NOT NULL,
    dat_competencia DATE NOT NULL,
    nom_bandeira_acionada VARCHAR(100) NOT NULL,
    tipo_bandeira bandeira_tarifaria NOT NULL,
    vlr_adicional_bandeira DECIMAL(10, 2) NOT NULL,
    vlr_adicional_kwh DECIMAL(10, 4),
    motivo_acionamento TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX uq_bandeira_competencia ON bandeira_tarifaria_acionamento(dat_competencia);
CREATE INDEX idx_bandeira_competencia ON bandeira_tarifaria_acionamento(dat_competencia);

-- Reservatórios table
CREATE TABLE IF NOT EXISTS reservatorios (
    id BIGSERIAL PRIMARY KEY,
    nome_reservatorio VARCHAR(100) NOT NULL,
    codigo_reservatorio VARCHAR(20) UNIQUE,
    subsistema region_type NOT NULL,
    bacia VARCHAR(100),
    rio VARCHAR(100),
    data_medicao DATE NOT NULL,
    nivel_atual DECIMAL(10, 2),
    volume_util DECIMAL(15, 2),
    volume_util_percentual DECIMAL(5, 2),
    vazao_afluente DECIMAL(10, 2),
    vazao_defluente DECIMAL(10, 2),
    vazao_vertida DECIMAL(10, 2),
    vazao_turbinada DECIMAL(10, 2),
    energia_armazenada DECIMAL(15, 2),
    energia_armazenada_percentual DECIMAL(5, 2),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_reservatorio_data ON reservatorios(codigo_reservatorio, data_medicao);
CREATE UNIQUE INDEX uq_reservatorio_medicao ON reservatorios(codigo_reservatorio, data_medicao);

-- Geração por usina table
CREATE TABLE IF NOT EXISTS geracao_usina (
    id BIGSERIAL PRIMARY KEY,
    nome_usina VARCHAR(100) NOT NULL,
    codigo_usina VARCHAR(20),
    tipo_usina VARCHAR(50),
    fonte_geracao VARCHAR(50),
    subsistema region_type,
    data_hora TIMESTAMP WITH TIME ZONE NOT NULL,
    geracao_mw DECIMAL(10, 2) NOT NULL,
    geracao_mwmed DECIMAL(10, 2),
    capacidade_instalada DECIMAL(10, 2),
    fator_capacidade DECIMAL(5, 2),
    status_operacao VARCHAR(20),
    disponibilidade DECIMAL(5, 2),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_geracao_usina_temporal ON geracao_usina(codigo_usina, data_hora);
CREATE INDEX idx_geracao_fonte ON geracao_usina(fonte_geracao, data_hora);

-- Intercâmbio regional table
CREATE TABLE IF NOT EXISTS intercambio_regional (
    id BIGSERIAL PRIMARY KEY,
    subsistema_origem region_type NOT NULL,
    subsistema_destino region_type NOT NULL,
    data_hora TIMESTAMP WITH TIME ZONE NOT NULL,
    valor_mw DECIMAL(10, 2) NOT NULL,
    valor_mwmed DECIMAL(10, 2),
    capacidade_maxima DECIMAL(10, 2),
    utilizacao_percentual DECIMAL(5, 2),
    limite_tecnico DECIMAL(10, 2),
    limite_operacional DECIMAL(10, 2),
    restricoes JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT ck_intercambio_diferentes CHECK (subsistema_origem != subsistema_destino)
);

CREATE INDEX idx_intercambio_subsistemas ON intercambio_regional(subsistema_origem, subsistema_destino, data_hora);

-- Chat history table
CREATE TABLE IF NOT EXISTS chat_history (
    id BIGSERIAL PRIMARY KEY,
    session_id VARCHAR(100) NOT NULL,
    user_id VARCHAR(100) NOT NULL,
    role chat_role NOT NULL,
    content TEXT NOT NULL,
    intent VARCHAR(50),
    confidence FLOAT,
    entities JSONB DEFAULT '{}',
    response_time_ms INTEGER,
    tokens_used INTEGER,
    model_used VARCHAR(50),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE,
    is_deleted BOOLEAN DEFAULT FALSE
);

CREATE INDEX idx_chat_history_session ON chat_history(session_id, created_at);
CREATE INDEX idx_chat_history_user ON chat_history(user_id, created_at);

-- Monitoring metrics table
CREATE TABLE IF NOT EXISTS monitoring_metrics (
    id BIGSERIAL PRIMARY KEY,
    metric_name VARCHAR(100) NOT NULL,
    metric_type VARCHAR(50),
    status VARCHAR(20) NOT NULL,
    value DECIMAL(20, 6),
    unit VARCHAR(20),
    message TEXT,
    severity VARCHAR(20),
    details JSONB DEFAULT '{}',
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_monitoring_status ON monitoring_metrics(status, timestamp);
CREATE INDEX idx_monitoring_metric_time ON monitoring_metrics(metric_name, timestamp);

-- Job queue table
CREATE TABLE IF NOT EXISTS job_queue (
    id BIGSERIAL PRIMARY KEY,
    job_id UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    job_type VARCHAR(50) NOT NULL,
    job_name VARCHAR(255) NOT NULL,
    priority INTEGER DEFAULT 5,
    status job_status DEFAULT 'pending',
    progress INTEGER DEFAULT 0,
    scheduled_at TIMESTAMP WITH TIME ZONE,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    payload JSONB DEFAULT '{}',
    result JSONB DEFAULT '{}',
    error TEXT,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_job_queue_status ON job_queue(status, priority);
CREATE INDEX idx_job_queue_type ON job_queue(job_type, status);

-- Error logs table
CREATE TABLE IF NOT EXISTS error_logs (
    id BIGSERIAL PRIMARY KEY,
    error_id UUID DEFAULT uuid_generate_v4() UNIQUE,
    error_type VARCHAR(100) NOT NULL,
    error_code VARCHAR(50),
    message TEXT NOT NULL,
    stack_trace TEXT,
    context JSONB DEFAULT '{}',
    source VARCHAR(100),
    user_id VARCHAR(100),
    session_id VARCHAR(100),
    severity VARCHAR(20) NOT NULL,
    resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolution_notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_error_log_severity ON error_logs(severity, created_at);
CREATE INDEX idx_error_log_type ON error_logs(error_type, created_at);
CREATE INDEX idx_error_log_resolved ON error_logs(resolved, created_at);

-- ===========================================
-- Materialized Views
-- ===========================================

-- Dataset summary view
CREATE MATERIALIZED VIEW mv_dataset_summary AS
SELECT 
    d.id as dataset_id,
    d.name as dataset_name,
    d.display_name,
    COUNT(dr.id) as total_records,
    MAX(dr.timestamp) as last_update,
    AVG(dr.value) as avg_value,
    MIN(dr.value) as min_value,
    MAX(dr.value) as max_value,
    COUNT(DISTINCT dr.region) as unique_regions,
    d.status,
    d.last_updated
FROM datasets d
LEFT JOIN data_records dr ON d.id = dr.dataset_id
GROUP BY d.id, d.name, d.display_name, d.status, d.last_updated;

CREATE UNIQUE INDEX idx_mv_dataset_summary_id ON mv_dataset_summary(dataset_id);

-- Daily load summary
CREATE MATERIALIZED VIEW mv_daily_load_summary AS
SELECT 
    DATE(din_instante) as date,
    nom_subsistema,
    AVG(val_cargaenergiamwmed) as avg_load,
    MAX(val_cargaenergiamwmed) as max_load,
    MIN(val_cargaenergiamwmed) as min_load,
    STDDEV(val_cargaenergiamwmed) as std_dev
FROM carga_energia
GROUP BY DATE(din_instante), nom_subsistema;

CREATE UNIQUE INDEX idx_mv_daily_load ON mv_daily_load_summary(date, nom_subsistema);

-- ===========================================
-- Functions and Triggers
-- ===========================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_datasets_updated_at BEFORE UPDATE ON datasets
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_data_records_updated_at BEFORE UPDATE ON data_records
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_carga_energia_updated_at BEFORE UPDATE ON carga_energia
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_cmo_updated_at BEFORE UPDATE ON cmo
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_chat_history_updated_at BEFORE UPDATE ON chat_history
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_job_queue_updated_at BEFORE UPDATE ON job_queue
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to refresh materialized views
CREATE OR REPLACE FUNCTION refresh_materialized_views()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_dataset_summary;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_daily_load_summary;
END;
$$ LANGUAGE plpgsql;

-- ===========================================
-- Initial Data
-- ===========================================

-- Insert initial datasets
INSERT INTO datasets (external_id, name, display_name, description, category, tags) VALUES
('carga_energia_diaria', 'Carga de Energia Diária', 'Carga de Energia - Diária', 'Dados diários de carga de energia por subsistema', 'energia', ARRAY['carga', 'energia', 'diário']),
('carga_energia_horaria', 'Carga de Energia Horária', 'Carga de Energia - Horária', 'Dados horários de carga de energia por subsistema', 'energia', ARRAY['carga', 'energia', 'horário']),
('cmo_semanal', 'CMO Semanal', 'Custo Marginal de Operação - Semanal', 'CMO médio semanal por subsistema', 'precos', ARRAY['cmo', 'preço', 'semanal']),
('bandeiras_tarifarias', 'Bandeiras Tarifárias', 'Bandeiras Tarifárias', 'Histórico de acionamento das bandeiras tarifárias', 'tarifas', ARRAY['bandeira', 'tarifa']),
('reservatorios_sin', 'Reservatórios SIN', 'Reservatórios do SIN', 'Níveis dos reservatórios do Sistema Interligado Nacional', 'hidrologia', ARRAY['reservatório', 'água', 'energia armazenada'])
ON CONFLICT (external_id) DO NOTHING;

-- ===========================================
-- Permissions (adjust as needed)
-- ===========================================
-- GRANT SELECT ON ALL TABLES IN SCHEMA public TO aide_readonly;
-- GRANT ALL ON ALL TABLES IN SCHEMA public TO aide_app;
-- GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO aide_app;