-- Tabelas para o sistema de monitoramento
-- Adicionar ao database aspi_db existente

-- Tabela para métricas de sistema
CREATE TABLE IF NOT EXISTS system_metrics (
    id SERIAL PRIMARY KEY,
    metric_name VARCHAR(100) NOT NULL,
    metric_type VARCHAR(50) NOT NULL, -- 'postgres', 'redis', 'http', 'system'
    status VARCHAR(20) NOT NULL, -- 'ok', 'warning', 'error'
    value DECIMAL(15,4),
    threshold DECIMAL(15,4),
    message TEXT,
    severity VARCHAR(20) NOT NULL, -- 'low', 'medium', 'high', 'critical'
    details JSONB,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    INDEX idx_metric_name (metric_name),
    INDEX idx_timestamp (timestamp),
    INDEX idx_status (status),
    INDEX idx_severity (severity)
);

-- Tabela para alertas
CREATE TABLE IF NOT EXISTS system_alerts (
    id SERIAL PRIMARY KEY,
    alert_type VARCHAR(50) NOT NULL,
    title VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    severity VARCHAR(20) NOT NULL,
    status VARCHAR(20) DEFAULT 'active', -- 'active', 'acknowledged', 'resolved'
    metric_id INTEGER REFERENCES system_metrics(id),
    triggered_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    acknowledged_at TIMESTAMP WITH TIME ZONE,
    resolved_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB,
    
    INDEX idx_alert_type (alert_type),
    INDEX idx_severity (severity),
    INDEX idx_status (status),
    INDEX idx_triggered_at (triggered_at)
);

-- Tabela para log de erros
CREATE TABLE IF NOT EXISTS error_logs (
    id SERIAL PRIMARY KEY,
    workflow VARCHAR(100),
    component VARCHAR(100),
    error_type VARCHAR(50),
    message TEXT NOT NULL,
    stack_trace TEXT,
    severity VARCHAR(20) NOT NULL,
    context JSONB,
    resolved BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    resolved_at TIMESTAMP WITH TIME ZONE,
    
    INDEX idx_workflow (workflow),
    INDEX idx_error_type (error_type),
    INDEX idx_severity (severity),
    INDEX idx_created_at (created_at),
    INDEX idx_resolved (resolved)
);

-- View para dashboard de saúde do sistema
CREATE OR REPLACE VIEW system_health_dashboard AS
SELECT 
    m.metric_name,
    m.metric_type,
    m.status,
    m.value,
    m.threshold,
    m.message,
    m.severity,
    m.timestamp,
    CASE 
        WHEN m.timestamp > NOW() - INTERVAL '5 minutes' THEN 'recent'
        WHEN m.timestamp > NOW() - INTERVAL '1 hour' THEN 'ok'
        ELSE 'stale'
    END as freshness,
    COUNT(a.id) as active_alerts
FROM system_metrics m
LEFT JOIN system_alerts a ON m.id = a.metric_id AND a.status = 'active'
WHERE m.id IN (
    SELECT MAX(id) 
    FROM system_metrics 
    GROUP BY metric_name
)
GROUP BY m.id, m.metric_name, m.metric_type, m.status, m.value, 
         m.threshold, m.message, m.severity, m.timestamp;

-- Dados iniciais para configuração
INSERT INTO datasets (name, description, external_id, source_type, endpoint_url) VALUES
('system_health', 'Métricas de saúde do sistema', 'system_health', 'INTERNAL', '/api/health')
ON CONFLICT (external_id) DO NOTHING;