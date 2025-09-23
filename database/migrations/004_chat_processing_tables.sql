-- Tabelas adicionais para o chat-processing.json
-- Execute no banco aspi_db

-- Tabela para histórico de chat (formato mais avançado)
CREATE TABLE IF NOT EXISTS chat_history (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(100) NOT NULL,
    user_id VARCHAR(100) NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Índices para chat_history
CREATE INDEX IF NOT EXISTS idx_chat_history_session ON chat_history (session_id);
CREATE INDEX IF NOT EXISTS idx_chat_history_user ON chat_history (user_id);
CREATE INDEX IF NOT EXISTS idx_chat_history_created ON chat_history (created_at);

-- Tabela para templates de queries
CREATE TABLE IF NOT EXISTS query_templates (
    id SERIAL PRIMARY KEY,
    intent_type VARCHAR(50) NOT NULL,
    query_template TEXT NOT NULL,
    parameters JSONB DEFAULT '{}',
    dataset_id VARCHAR(50),
    description TEXT,
    priority INTEGER DEFAULT 1,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Índices para query_templates
CREATE INDEX IF NOT EXISTS idx_query_templates_intent ON query_templates (intent_type);
CREATE INDEX IF NOT EXISTS idx_query_templates_active ON query_templates (active);
CREATE INDEX IF NOT EXISTS idx_query_templates_priority ON query_templates (priority);

-- Tabela para datasets disponíveis
CREATE TABLE IF NOT EXISTS datasets (
    id SERIAL PRIMARY KEY,
    external_id VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    display_name VARCHAR(200),
    source_type VARCHAR(50),
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'maintenance')),
    last_updated TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Índices para datasets
CREATE INDEX IF NOT EXISTS idx_datasets_external_id ON datasets (external_id);
CREATE INDEX IF NOT EXISTS idx_datasets_status ON datasets (status);
CREATE INDEX IF NOT EXISTS idx_datasets_source_type ON datasets (source_type);

-- Tabela para registros de dados
CREATE TABLE IF NOT EXISTS data_records (
    id SERIAL PRIMARY KEY,
    dataset_id VARCHAR(100) NOT NULL,
    period_start TIMESTAMP WITH TIME ZONE NOT NULL,
    period_end TIMESTAMP WITH TIME ZONE,
    subsystem VARCHAR(50),
    metric_name VARCHAR(100),
    value DECIMAL(15,4),
    unit VARCHAR(20),
    processed_data JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Índices para data_records
CREATE INDEX IF NOT EXISTS idx_data_records_dataset_period ON data_records (dataset_id, period_start);
CREATE INDEX IF NOT EXISTS idx_data_records_subsystem ON data_records (subsystem);
CREATE INDEX IF NOT EXISTS idx_data_records_metric ON data_records (metric_name);
CREATE INDEX IF NOT EXISTS idx_data_records_period ON data_records (period_start);

-- Inserir templates de query padrão
INSERT INTO query_templates (intent_type, query_template, dataset_id, description, priority) VALUES
('carga_energia', 
 'SELECT period_start, subsystem, value, unit FROM data_records WHERE dataset_id = ''carga_energia'' AND period_start BETWEEN $1 AND $2 ORDER BY period_start DESC',
 'carga_energia',
 'Query padrão para carga de energia',
 1),
('cmo_pld',
 'SELECT period_start, subsystem, value, unit, processed_data FROM data_records WHERE dataset_id IN (''cmo'', ''pld'') AND period_start BETWEEN $1 AND $2 ORDER BY period_start DESC',
 'cmo_pld',
 'Query padrão para CMO/PLD',
 1),
('bandeiras',
 'SELECT period_start, value, processed_data->''bandeira'' as bandeira FROM data_records WHERE dataset_id = ''bandeiras_tarifarias'' AND period_start >= $1 ORDER BY period_start DESC',
 'bandeiras_tarifarias',
 'Query padrão para bandeiras tarifárias',
 1),
('geracao',
 'SELECT period_start, subsystem, metric_name, value, unit FROM data_records WHERE dataset_id LIKE ''%geracao%'' AND period_start BETWEEN $1 AND $2 ORDER BY period_start DESC',
 'geracao',
 'Query padrão para geração',
 1)
ON CONFLICT DO NOTHING;

-- Inserir datasets padrão
INSERT INTO datasets (external_id, name, display_name, source_type, status) VALUES
('carga_energia', 'Carga de Energia', 'Carga de Energia do SIN', 'ons', 'active'),
('cmo_horario', 'CMO Horário', 'Custo Marginal de Operação Horário', 'ons', 'active'),
('pld_horario', 'PLD Horário', 'Preço de Liquidação das Diferenças Horário', 'ons', 'active'),
('bandeiras_tarifarias', 'Bandeira Tarifária', 'Bandeiras Tarifárias', 'aneel', 'active'),
('geracao_solar', 'Geração Solar', 'Geração de Energia Solar', 'ons', 'active'),
('geracao_eolica', 'Geração Eólica', 'Geração de Energia Eólica', 'ons', 'active'),
('geracao_hidrica', 'Geração Hídrica', 'Geração de Energia Hídrica', 'ons', 'active'),
('intercambio', 'Intercâmbio', 'Intercâmbio entre Subsistemas', 'ons', 'active')
ON CONFLICT (external_id) DO NOTHING;

-- Inserir dados de exemplo para teste
INSERT INTO data_records (dataset_id, period_start, subsystem, metric_name, value, unit, processed_data) VALUES
('carga_energia', NOW() - INTERVAL '1 hour', 'Sudeste', 'Carga Verificada', 25420.5, 'MWmed', '{"fonte": "tempo_real"}'),
('carga_energia', NOW() - INTERVAL '1 hour', 'Sul', 'Carga Verificada', 8750.2, 'MWmed', '{"fonte": "tempo_real"}'),
('carga_energia', NOW() - INTERVAL '1 hour', 'Nordeste', 'Carga Verificada', 12340.8, 'MWmed', '{"fonte": "tempo_real"}'),
('carga_energia', NOW() - INTERVAL '1 hour', 'Norte', 'Carga Verificada', 4120.3, 'MWmed', '{"fonte": "tempo_real"}'),
('cmo_horario', NOW() - INTERVAL '1 hour', 'Sudeste', 'CMO', 185.50, 'R$/MWh', '{"patamar": "pesada"}'),
('cmo_horario', NOW() - INTERVAL '1 hour', 'Sul', 'CMO', 180.25, 'R$/MWh', '{"patamar": "pesada"}'),
('bandeiras_tarifarias', DATE_TRUNC('month', NOW()), 'SIN', 'Bandeira', 4.77, 'R$/100kWh', '{"bandeira": "vermelha", "patamar": "2"}')
ON CONFLICT DO NOTHING;

-- Verificar se as tabelas foram criadas
SELECT 
    table_name,
    (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = t.table_name) as column_count
FROM information_schema.tables t
WHERE table_schema = 'public' 
AND table_name IN ('chat_history', 'query_templates', 'datasets', 'data_records')
ORDER BY table_name;