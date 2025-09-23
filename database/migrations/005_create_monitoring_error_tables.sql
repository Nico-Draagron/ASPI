-- SQL para criar as tabelas faltantes
-- Execute no PostgreSQL: docker exec -it aspi-postgres psql -U aspi -d aspi_db

-- =====================================================
-- TABELA: monitoring_metrics
-- =====================================================
CREATE TABLE monitoring_metrics (
    id SERIAL PRIMARY KEY,
    metric_name VARCHAR(100) NOT NULL,
    metric_value NUMERIC(15,4) NOT NULL,
    metric_type VARCHAR(50) NOT NULL, -- 'counter', 'gauge', 'histogram'
    labels JSONB DEFAULT '{}',
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    source VARCHAR(50) DEFAULT 'system',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índices para monitoring_metrics
CREATE INDEX idx_monitoring_metrics_name ON monitoring_metrics(metric_name);
CREATE INDEX idx_monitoring_metrics_timestamp ON monitoring_metrics(timestamp);
CREATE INDEX idx_monitoring_metrics_type ON monitoring_metrics(metric_type);
CREATE INDEX idx_monitoring_metrics_source ON monitoring_metrics(source);

-- =====================================================
-- TABELA: error_logs
-- =====================================================
CREATE TABLE error_logs (
    id SERIAL PRIMARY KEY,
    error_type VARCHAR(50) NOT NULL,
    error_code VARCHAR(20),
    error_message TEXT NOT NULL,
    stack_trace TEXT,
    request_id VARCHAR(100),
    user_id VARCHAR(100),
    session_id VARCHAR(100),
    endpoint VARCHAR(200),
    http_method VARCHAR(10),
    http_status_code INTEGER,
    user_agent TEXT,
    ip_address INET,
    context JSONB DEFAULT '{}',
    severity VARCHAR(20) DEFAULT 'error', -- 'error', 'warning', 'critical'
    resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMPTZ,
    resolved_by VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índices para error_logs
CREATE INDEX idx_error_logs_type ON error_logs(error_type);
CREATE INDEX idx_error_logs_created ON error_logs(created_at);
CREATE INDEX idx_error_logs_severity ON error_logs(severity);
CREATE INDEX idx_error_logs_resolved ON error_logs(resolved);
CREATE INDEX idx_error_logs_request_id ON error_logs(request_id);
CREATE INDEX idx_error_logs_user_id ON error_logs(user_id);
CREATE INDEX idx_error_logs_session_id ON error_logs(session_id);

-- =====================================================
-- COMENTÁRIOS E CONSTRAINTS
-- =====================================================

-- Adicionar constraints de verificação
ALTER TABLE monitoring_metrics 
ADD CONSTRAINT monitoring_metrics_type_check 
CHECK (metric_type IN ('counter', 'gauge', 'histogram', 'summary'));

ALTER TABLE error_logs 
ADD CONSTRAINT error_logs_severity_check 
CHECK (severity IN ('error', 'warning', 'critical', 'info'));

ALTER TABLE error_logs 
ADD CONSTRAINT error_logs_http_method_check 
CHECK (http_method IN ('GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS', 'HEAD'));

-- Comentários nas tabelas
COMMENT ON TABLE monitoring_metrics IS 'Tabela para armazenar métricas de monitoramento do sistema';
COMMENT ON TABLE error_logs IS 'Tabela para armazenar logs de erro e exceções do sistema';

-- =====================================================
-- INSERIR DADOS DE EXEMPLO
-- =====================================================

-- Exemplo de métricas de monitoramento
INSERT INTO monitoring_metrics (metric_name, metric_value, metric_type, labels, source) VALUES
('requests_total', 150, 'counter', '{"endpoint": "/chat/process", "method": "POST"}', 'n8n'),
('response_time_ms', 245.5, 'gauge', '{"endpoint": "/chat/process"}', 'n8n'),
('database_connections', 5, 'gauge', '{"database": "aspi_db"}', 'postgres'),
('redis_memory_usage_mb', 128.7, 'gauge', '{"instance": "aspi-redis"}', 'redis');

-- Exemplo de log de erro
INSERT INTO error_logs (
    error_type, error_code, error_message, request_id, 
    user_id, endpoint, http_method, http_status_code, 
    severity, context
) VALUES (
    'DatabaseError', 'DB001', 'Connection timeout to PostgreSQL',
    'req_1695377400000_abc123', 'user_123', '/chat/process',
    'POST', 500, 'error',
    '{"query": "SELECT * FROM datasets", "timeout": 30}'
);

-- =====================================================
-- VERIFICAÇÃO
-- =====================================================

-- Verificar se as tabelas foram criadas
SELECT table_name, 
       (SELECT COUNT(*) FROM information_schema.columns 
        WHERE table_name = t.table_name AND table_schema = 'public') as column_count
FROM information_schema.tables t 
WHERE table_schema = 'public' 
  AND table_name IN ('monitoring_metrics', 'error_logs')
ORDER BY table_name;