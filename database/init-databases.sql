-- init-databases.sql
-- Script de inicialização dos bancos de dados para ASPI e n8n

-- Criar banco de dados para n8n (se não existir)
CREATE DATABASE n8n_db;

-- Garantir que o usuário aspi tem permissões em ambos os bancos
GRANT ALL PRIVILEGES ON DATABASE aspi_db TO aspi;
GRANT ALL PRIVILEGES ON DATABASE n8n_db TO aspi;

-- Conectar ao banco aspi_db e criar extensões necessárias
\c aspi_db;

-- Extensões úteis para PostgreSQL
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- Criar schema para o sistema ASPI se não existir
CREATE SCHEMA IF NOT EXISTS public;

-- Garantir permissões no schema
GRANT ALL ON SCHEMA public TO aspi;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO aspi;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO aspi;

-- Conectar ao banco n8n_db e configurar
\c n8n_db;

-- Extensões para n8n
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Garantir permissões para n8n
GRANT ALL ON SCHEMA public TO aspi;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO aspi;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO aspi;

-- Voltar ao banco principal
\c aspi_db;

-- Inserir dados iniciais básicos se necessário
INSERT INTO public.datasets (external_id, name, display_name, source_type, status, created_at, updated_at)
VALUES 
  ('carga-energia', 'Carga de Energia', 'Carga de Energia do SIN', 'ons', 'active', NOW(), NOW()),
  ('cmo-horario', 'CMO Horário', 'Custo Marginal de Operação Horário', 'ons', 'active', NOW(), NOW()),
  ('bandeira-tarifaria', 'Bandeira Tarifária', 'Bandeiras Tarifárias', 'ons', 'active', NOW(), NOW())
ON CONFLICT (external_id) DO NOTHING;

-- Mensagem de confirmação
SELECT 'Bancos de dados ASPI e n8n inicializados com sucesso!' as status;