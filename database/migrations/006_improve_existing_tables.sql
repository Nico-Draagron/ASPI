-- =====================================================
-- SCRIPT SQL - MELHORAR TABELAS EXISTENTES NO ASPI
-- =====================================================

-- =====================================================
-- 1. ADICIONAR CAMPOS FALTANTES EM TABELAS EXISTENTES
-- =====================================================

-- Adicionar campos faltantes na tabela datasets
DO $$
BEGIN
    -- Adicionar colunas se não existirem
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='datasets' AND column_name='row_count') THEN
        ALTER TABLE datasets ADD COLUMN row_count BIGINT DEFAULT 0;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='datasets' AND column_name='update_frequency') THEN
        ALTER TABLE datasets ADD COLUMN update_frequency VARCHAR(50);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='datasets' AND column_name='deleted_at') THEN
        ALTER TABLE datasets ADD COLUMN deleted_at TIMESTAMPTZ;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='datasets' AND column_name='description') THEN
        ALTER TABLE datasets ADD COLUMN description TEXT;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='datasets' AND column_name='source_url') THEN
        ALTER TABLE datasets ADD COLUMN source_url VARCHAR(500);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='datasets' AND column_name='fields_schema') THEN
        ALTER TABLE datasets ADD COLUMN fields_schema JSONB DEFAULT '{}';
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='datasets' AND column_name='tags') THEN
        ALTER TABLE datasets ADD COLUMN tags TEXT[] DEFAULT '{}';
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='datasets' AND column_name='category') THEN
        ALTER TABLE datasets ADD COLUMN category VARCHAR(100);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='datasets' AND column_name='size_bytes') THEN
        ALTER TABLE datasets ADD COLUMN size_bytes BIGINT DEFAULT 0;
    END IF;
END $$;

-- Adicionar campos faltantes na tabela data_records
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='data_records' AND column_name='year') THEN
        ALTER TABLE data_records ADD COLUMN year INTEGER;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='data_records' AND column_name='month') THEN
        ALTER TABLE data_records ADD COLUMN month INTEGER;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='data_records' AND column_name='day') THEN
        ALTER TABLE data_records ADD COLUMN day INTEGER;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='data_records' AND column_name='hour') THEN
        ALTER TABLE data_records ADD COLUMN hour INTEGER;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='data_records' AND column_name='region') THEN
        ALTER TABLE data_records ADD COLUMN region VARCHAR(100);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='data_records' AND column_name='metric_type') THEN
        ALTER TABLE data_records ADD COLUMN metric_type VARCHAR(100);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='data_records' AND column_name='raw_data') THEN
        ALTER TABLE data_records ADD COLUMN raw_data JSONB DEFAULT '{}';
    END IF;
END $$;

-- =====================================================
-- 2. ADICIONAR ÍNDICES IMPORTANTES
-- =====================================================

-- Criar índices se não existirem
CREATE INDEX IF NOT EXISTS idx_data_records_dataset_new ON data_records(dataset_id);
CREATE INDEX IF NOT EXISTS idx_data_records_period_new ON data_records(period_start DESC);
CREATE INDEX IF NOT EXISTS idx_data_records_subsystem_new ON data_records(subsystem);
CREATE INDEX IF NOT EXISTS idx_data_records_year_month ON data_records(year, month);
CREATE INDEX IF NOT EXISTS idx_data_records_metric_type ON data_records(metric_type);
CREATE INDEX IF NOT EXISTS idx_datasets_category ON datasets(category);
CREATE INDEX IF NOT EXISTS idx_datasets_update_frequency ON datasets(update_frequency);

-- =====================================================
-- 3. MELHORAR TABELAS EXISTENTES DE MONITORAMENTO
-- =====================================================

-- Adicionar campos úteis na monitoring_metrics se não existirem
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='monitoring_metrics' AND column_name='status') THEN
        ALTER TABLE monitoring_metrics ADD COLUMN status VARCHAR(20) DEFAULT 'unknown';
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='monitoring_metrics' AND column_name='message') THEN
        ALTER TABLE monitoring_metrics ADD COLUMN message TEXT;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='monitoring_metrics' AND column_name='details') THEN
        ALTER TABLE monitoring_metrics ADD COLUMN details JSONB DEFAULT '{}';
    END IF;
END $$;

-- Adicionar índices na monitoring_metrics se não existirem
CREATE INDEX IF NOT EXISTS idx_monitoring_metrics_status ON monitoring_metrics(status);

-- =====================================================
-- 4. POPULAR DADOS INICIAIS ADICIONAIS
-- =====================================================

-- Inserir templates de query adicionais
INSERT INTO query_templates (intent_type, query_template, parameters, dataset_id, description, priority, active)
VALUES 
    ('status_sistema', 
     'SELECT COUNT(*) as total_records, MAX(period_start) as latest_data, dataset_id FROM data_records GROUP BY dataset_id',
     '{}',
     'all',
     'Query para verificar status geral do sistema',
     5,
     true),
     
    ('historico_precos',
     'SELECT DATE(period_start) as data, AVG(value) as preco_medio FROM data_records WHERE dataset_id LIKE ''%cmo%'' OR dataset_id LIKE ''%pld%'' GROUP BY DATE(period_start) ORDER BY data DESC LIMIT 30',
     '{}',
     'cmo_pld',
     'Histórico de preços dos últimos 30 dias',
     8,
     true),
     
    ('carga_por_regiao',
     'SELECT subsystem, DATE(period_start) as data, SUM(value) as carga_total FROM data_records WHERE dataset_id LIKE ''%carga%'' AND period_start >= CURRENT_DATE - INTERVAL ''7 days'' GROUP BY subsystem, DATE(period_start) ORDER BY data DESC',
     '{}',
     'carga_energia',
     'Carga por região nos últimos 7 dias',
     7,
     true),
     
    ('metricas_performance',
     'SELECT metric_name, AVG(metric_value) as valor_medio, MAX(timestamp) as ultima_medicao FROM monitoring_metrics WHERE timestamp >= CURRENT_DATE - INTERVAL ''1 day'' GROUP BY metric_name',
     '{}',
     'monitoring',
     'Métricas de performance das últimas 24h',
     6,
     true)
ON CONFLICT (intent_type) DO NOTHING;

-- =====================================================
-- 5. CRIAR/ATUALIZAR VIEWS ÚTEIS
-- =====================================================

-- View para últimos dados de cada dataset
CREATE OR REPLACE VIEW v_latest_data AS
SELECT DISTINCT ON (dataset_id) 
    dataset_id,
    period_start,
    subsystem,
    metric_name,
    value,
    unit,
    year,
    month,
    day
FROM data_records
ORDER BY dataset_id, period_start DESC;

-- View para status dos datasets
CREATE OR REPLACE VIEW v_dataset_status AS
SELECT 
    d.external_id,
    d.name,
    d.category,
    d.last_updated,
    COUNT(dr.id) as record_count,
    MAX(dr.period_start) as latest_data,
    d.row_count,
    d.size_bytes,
    CASE 
        WHEN MAX(dr.period_start) > NOW() - INTERVAL '24 hours' THEN 'recent'
        WHEN MAX(dr.period_start) > NOW() - INTERVAL '7 days' THEN 'ok'
        WHEN MAX(dr.period_start) > NOW() - INTERVAL '30 days' THEN 'stale'
        ELSE 'very_old'
    END as data_freshness,
    CASE 
        WHEN d.status = 'active' AND COUNT(dr.id) > 0 THEN 'operational'
        WHEN d.status = 'active' AND COUNT(dr.id) = 0 THEN 'no_data'
        ELSE 'inactive'
    END as operational_status
FROM datasets d
LEFT JOIN data_records dr ON d.external_id = dr.dataset_id
GROUP BY d.id, d.external_id, d.name, d.category, d.last_updated, d.row_count, d.size_bytes, d.status;

-- View para resumo de erros
CREATE OR REPLACE VIEW v_error_summary AS
SELECT 
    error_type,
    severity,
    COUNT(*) as error_count,
    COUNT(CASE WHEN resolved = false THEN 1 END) as unresolved_count,
    MAX(created_at) as last_occurrence,
    AVG(CASE WHEN resolved = true THEN EXTRACT(EPOCH FROM (resolved_at - created_at)) END) as avg_resolution_time_seconds
FROM error_logs
WHERE created_at > NOW() - INTERVAL '30 days'
GROUP BY error_type, severity
ORDER BY error_count DESC;

-- View para métricas de sistema
CREATE OR REPLACE VIEW v_system_health AS
SELECT 
    metric_name,
    metric_type,
    AVG(metric_value) as avg_value,
    MIN(metric_value) as min_value,
    MAX(metric_value) as max_value,
    COUNT(*) as measurements,
    MAX(timestamp) as last_measurement,
    source
FROM monitoring_metrics
WHERE timestamp > NOW() - INTERVAL '24 hours'
GROUP BY metric_name, metric_type, source
ORDER BY metric_name;

-- =====================================================
-- 6. ATUALIZAR DADOS EXISTENTES
-- =====================================================

-- Atualizar campos year, month, day, hour nos data_records existentes
UPDATE data_records 
SET 
    year = EXTRACT(YEAR FROM period_start),
    month = EXTRACT(MONTH FROM period_start),
    day = EXTRACT(DAY FROM period_start),
    hour = EXTRACT(HOUR FROM period_start)
WHERE year IS NULL AND period_start IS NOT NULL;

-- Atualizar row_count nos datasets
UPDATE datasets 
SET row_count = (
    SELECT COUNT(*) 
    FROM data_records 
    WHERE data_records.dataset_id = datasets.external_id
)
WHERE row_count = 0 OR row_count IS NULL;

-- =====================================================
-- 7. CRIAR FUNÇÕES ÚTEIS
-- =====================================================

-- Função para buscar dados mais recentes
CREATE OR REPLACE FUNCTION get_latest_data(dataset_name TEXT, hours_back INTEGER DEFAULT 24)
RETURNS TABLE(
    dataset_id TEXT,
    period_start TIMESTAMPTZ,
    subsystem VARCHAR,
    metric_name VARCHAR,
    value NUMERIC,
    unit VARCHAR
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        dr.dataset_id::TEXT,
        dr.period_start,
        dr.subsystem,
        dr.metric_name,
        dr.value,
        dr.unit
    FROM data_records dr
    WHERE dr.dataset_id = dataset_name 
      AND dr.period_start > NOW() - (hours_back || ' hours')::INTERVAL
    ORDER BY dr.period_start DESC;
END;
$$ LANGUAGE plpgsql;

-- Função para inserir métrica de monitoramento
CREATE OR REPLACE FUNCTION insert_monitoring_metric(
    p_metric_name TEXT,
    p_value NUMERIC,
    p_metric_type TEXT DEFAULT 'gauge',
    p_source TEXT DEFAULT 'system',
    p_labels JSONB DEFAULT '{}'
) RETURNS VOID AS $$
BEGIN
    INSERT INTO monitoring_metrics (
        metric_name, 
        metric_value, 
        metric_type, 
        source, 
        labels
    ) VALUES (
        p_metric_name, 
        p_value, 
        p_metric_type, 
        p_source, 
        p_labels
    );
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- 8. VERIFICAÇÃO FINAL E RELATÓRIO
-- =====================================================

-- Verificar todas as tabelas e seus tamanhos
SELECT 
    schemaname,
    tablename,
    attname as column_name,
    n_distinct,
    correlation
FROM pg_stats 
WHERE schemaname = 'public' 
  AND tablename IN ('datasets', 'data_records', 'monitoring_metrics', 'error_logs', 'query_templates')
ORDER BY tablename, attname;

-- Relatório de status das tabelas
SELECT 
    t.table_name,
    (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = t.table_name AND table_schema = 'public') as column_count,
    CASE t.table_name
        WHEN 'datasets' THEN (SELECT COUNT(*) FROM datasets)
        WHEN 'data_records' THEN (SELECT COUNT(*) FROM data_records)
        WHEN 'monitoring_metrics' THEN (SELECT COUNT(*) FROM monitoring_metrics)
        WHEN 'error_logs' THEN (SELECT COUNT(*) FROM error_logs)
        WHEN 'query_templates' THEN (SELECT COUNT(*) FROM query_templates)
        ELSE 0
    END as record_count
FROM information_schema.tables t
WHERE t.table_schema = 'public' 
  AND t.table_type = 'BASE TABLE'
  AND t.table_name IN ('datasets', 'data_records', 'monitoring_metrics', 'error_logs', 'query_templates', 'chat_history')
ORDER BY t.table_name;

-- Mensagem de conclusão
SELECT 'Banco de dados atualizado com sucesso! ✅' as status,
       NOW() as execution_time;