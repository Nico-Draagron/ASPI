#!/bin/bash
# quickstart.sh - Script de instalação e configuração rápida do AIDE

set -e  # Parar em caso de erro

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Função de log
log() {
    echo -e "${GREEN}[AIDE Setup]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Banner
clear
cat << "EOF"
    ___    ________  ______
   /   |  /  _/ __ \/ ____/
  / /| |  / // / / / __/   
 / ___ |_/ // /_/ / /___   
/_/  |_/___/_____/_____/   
                           
Assistente Inteligente para Dados do Setor Elétrico
Version 1.0.0
EOF

echo ""
log "Iniciando configuração do sistema AIDE..."
echo ""

# Verificar requisitos
log "Verificando requisitos do sistema..."

# Docker
if ! command -v docker &> /dev/null; then
    error "Docker não está instalado. Por favor, instale o Docker primeiro."
fi

# Docker Compose
if ! command -v docker-compose &> /dev/null; then
    error "Docker Compose não está instalado. Por favor, instale o Docker Compose primeiro."
fi

# Git
if ! command -v git &> /dev/null; then
    warning "Git não está instalado. Continuando sem Git..."
fi

log "✓ Requisitos verificados"

# Criar estrutura de diretórios
log "Criando estrutura de diretórios..."

mkdir -p aide-system/{services,models,utils,workflows,scripts,backups,logs,static}
cd aide-system

# Criar arquivo .env
log "Configurando variáveis de ambiente..."

if [ ! -f .env ]; then
    cat > .env << EOL
# Database
DB_HOST=postgres
DB_PORT=5432
DB_NAME=aide_db
DB_USER=aide_user
DB_PASSWORD=$(openssl rand -base64 32)

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=$(openssl rand -base64 16)

# n8n
N8N_USER=aide_admin
N8N_PASSWORD=$(openssl rand -base64 16)
N8N_API_KEY=$(openssl rand -hex 32)
N8N_WEBHOOK_TOKEN=$(openssl rand -hex 32)

# OpenAI/Anthropic
OPENAI_API_KEY=
ANTHROPIC_API_KEY=

# ONS API
ONS_API_URL=https://dados.ons.org.br/api/v1
ONS_API_KEY=

# App Settings
APP_ENV=production
APP_SECRET_KEY=$(openssl rand -hex 32)
EOL
    
    log "✓ Arquivo .env criado"
    warning "IMPORTANTE: Adicione suas chaves de API no arquivo .env"
else
    log "✓ Arquivo .env já existe"
fi

# Criar requirements.txt
log "Criando requirements.txt..."

cat > requirements.txt << EOL
streamlit==1.29.0
pandas==2.1.0
plotly==5.17.0
aiohttp==3.9.0
requests==2.31.0
redis==5.0.0
psycopg2-binary==2.9.9
python-dotenv==1.0.0
sqlalchemy==2.0.23
alembic==1.12.1
pytest==7.4.3
pytest-asyncio==0.21.1
numpy==1.24.3
scipy==1.11.4
scikit-learn==1.3.2
EOL

log "✓ Requirements.txt criado"

# Baixar arquivos do repositório (simulado)
log "Baixando arquivos do sistema..."

# Docker Compose
if [ ! -f docker-compose.yml ]; then
    log "Criando docker-compose.yml..."
    # Aqui você colocaria o conteúdo do docker-compose.yml
    touch docker-compose.yml
    log "✓ docker-compose.yml criado (adicione o conteúdo manualmente)"
fi

# Criar Makefile
log "Criando Makefile..."

cat > Makefile << 'EOL'
.PHONY: help install start stop restart status logs clean test

help:
	@echo "AIDE System - Comandos disponíveis:"
	@echo "  make install  - Instalar e configurar o sistema"
	@echo "  make start    - Iniciar todos os serviços"
	@echo "  make stop     - Parar todos os serviços"
	@echo "  make restart  - Reiniciar todos os serviços"
	@echo "  make status   - Ver status dos serviços"
	@echo "  make logs     - Ver logs dos serviços"
	@echo "  make clean    - Limpar volumes e dados"
	@echo "  make test     - Executar testes"

install:
	@./quickstart.sh

start:
	docker-compose up -d
	@echo "Sistema iniciado! Acesse:"
	@echo "  - Streamlit: http://localhost:8501"
	@echo "  - n8n: http://localhost:5678"
	@echo "  - PgAdmin: http://localhost:5050"

stop:
	docker-compose down

restart:
	docker-compose restart

status:
	@docker-compose ps

logs:
	docker-compose logs -f --tail=100

clean:
	docker-compose down -v
	rm -rf backups/* logs/*

test:
	@./run_tests.sh
EOL

log "✓ Makefile criado"

# Criar script de teste
log "Criando scripts de teste..."

cat > run_tests.sh << 'EOL'
#!/bin/bash
echo "Executando testes do sistema AIDE..."

# Testar conexão com PostgreSQL
echo -n "PostgreSQL: "
docker-compose exec -T postgres pg_isready -U aide_user -d aide_db &> /dev/null && echo "✓ OK" || echo "✗ ERRO"

# Testar conexão com Redis
echo -n "Redis: "
docker-compose exec -T redis redis-cli ping &> /dev/null && echo "✓ OK" || echo "✗ ERRO"

# Testar n8n
echo -n "n8n: "
curl -s http://localhost:5678/healthz &> /dev/null && echo "✓ OK" || echo "✗ ERRO"

# Testar Streamlit
echo -n "Streamlit: "
curl -s http://localhost:8501/_stcore/health &> /dev/null && echo "✓ OK" || echo "✗ ERRO"

echo ""
echo "Testes concluídos!"
EOL

chmod +x run_tests.sh

log "✓ Scripts de teste criados"

# Criar script de inicialização do banco
log "Criando script SQL de inicialização..."

mkdir -p scripts
cat > scripts/init.sql << 'EOL'
-- Script de inicialização do banco AIDE
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Criar tabelas (versão simplificada)
CREATE TABLE IF NOT EXISTS datasets (
    id SERIAL PRIMARY KEY,
    external_id VARCHAR(100) UNIQUE,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS data_records (
    id BIGSERIAL PRIMARY KEY,
    dataset_id VARCHAR(100),
    value DECIMAL(20, 6),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Inserir dados de exemplo
INSERT INTO datasets (external_id, name) VALUES 
    ('carga_energia', 'Carga de Energia'),
    ('cmo_pld', 'CMO/PLD')
ON CONFLICT DO NOTHING;

SELECT 'Banco de dados inicializado!' as message;
EOL

log "✓ Script SQL criado"

# Menu de opções
echo ""
echo "=========================================="
echo "Escolha uma opção para continuar:"
echo "=========================================="
echo "1) Instalação completa (Docker + configuração)"
echo "2) Apenas criar estrutura de arquivos"
echo "3) Iniciar serviços agora"
echo "4) Ver instruções de configuração"
echo "5) Sair"
echo ""
read -p "Opção [1-5]: " option

case $option in
    1)
        log "Iniciando instalação completa..."
        
        # Verificar se existe chave de API
        if grep -q "OPENAI_API_KEY=$" .env || grep -q "ANTHROPIC_API_KEY=$" .env; then
            warning "Por favor, adicione sua chave de API (OpenAI ou Anthropic) no arquivo .env"
            read -p "Deseja adicionar agora? [s/N]: " add_key
            if [ "$add_key" = "s" ] || [ "$add_key" = "S" ]; then
                read -p "Digite sua chave OpenAI (ou pressione Enter para pular): " openai_key
                if [ ! -z "$openai_key" ]; then
                    sed -i.bak "s/OPENAI_API_KEY=.*/OPENAI_API_KEY=$openai_key/" .env
                fi
                
                read -p "Digite sua chave Anthropic (ou pressione Enter para pular): " anthropic_key
                if [ ! -z "$anthropic_key" ]; then
                    sed -i.bak "s/ANTHROPIC_API_KEY=.*/ANTHROPIC_API_KEY=$anthropic_key/" .env
                fi
            fi
        fi
        
        log "Construindo imagens Docker..."
        docker-compose build
        
        log "Iniciando serviços..."
        docker-compose up -d
        
        log "Aguardando serviços iniciarem..."
        sleep 10
        
        log "Verificando status dos serviços..."
        ./run_tests.sh
        
        echo ""
        log "✓ Instalação concluída com sucesso!"
        echo ""
        echo "=========================================="
        echo "AIDE está pronto para uso!"
        echo "=========================================="
        echo "Acesse os serviços em:"
        echo "  📊 Streamlit (Interface): http://localhost:8501"
        echo "  🔄 n8n (Workflows): http://localhost:5678"
        echo "  🗄️ PgAdmin (Banco): http://localhost:5050"
        echo ""
        echo "Credenciais n8n:"
        echo "  Usuário: aide_admin"
        echo "  Senha: $(grep N8N_PASSWORD .env | cut -d'=' -f2)"
        echo ""
        echo "Próximos passos:"
        echo "  1. Acesse o n8n e importe os workflows"
        echo "  2. Configure as credenciais no n8n"
        echo "  3. Acesse o Streamlit e comece a usar!"
        echo ""
        ;;
        
    2)
        log "Estrutura de arquivos criada com sucesso!"
        echo ""
        echo "Para continuar a instalação:"
        echo "  1. Adicione suas chaves de API no arquivo .env"
        echo "  2. Execute: docker-compose up -d"
        echo "  3. Acesse: http://localhost:8501"
        ;;
        
    3)
        log "Iniciando serviços..."
        docker-compose up -d
        sleep 5
        ./run_tests.sh
        ;;
        
    4)
        echo ""
        echo "=========================================="
        echo "Instruções de Configuração"
        echo "=========================================="
        echo ""
        echo "1. CONFIGURAR CHAVES DE API:"
        echo "   Edite o arquivo .env e adicione:"
        echo "   - OPENAI_API_KEY=sk-... (ou)"
        echo "   - ANTHROPIC_API_KEY=sk-ant-..."
        echo ""
        echo "2. INICIAR O SISTEMA:"
        echo "   docker-compose up -d"
        echo ""
        echo "3. IMPORTAR WORKFLOWS NO N8N:"
        echo "   - Acesse http://localhost:5678"
        echo "   - Faça login com as credenciais"
        echo "   - Importe os arquivos .json da pasta workflows/"
        echo ""
        echo "4. CONFIGURAR CREDENCIAIS NO N8N:"
        echo "   - PostgreSQL: Use as configurações do .env"
        echo "   - Redis: Use as configurações do .env"
        echo "   - OpenAI/Anthropic: Use sua API key"
        echo ""
        echo "5. ACESSAR O SISTEMA:"
        echo "   http://localhost:8501"
        echo ""
        ;;
        
    5)
        log "Saindo..."
        exit 0
        ;;
        
    *)
        error "Opção inválida!"
        ;;
esac

echo ""
log "Script concluído. Use 'make help' para ver comandos disponíveis."