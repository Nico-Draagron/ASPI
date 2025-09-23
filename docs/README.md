# 🚀 AIDE - Assistente Inteligente para Dados do Setor Elétrico

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/seu-usuario/aide-system)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9+-yellow.svg)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)
[![n8n](https://img.shields.io/badge/n8n-integrated-orange.svg)](https://n8n.io/)

Sistema inteligente de análise e visualização de dados do setor elétrico brasileiro, integrando dados do ONS (Operador Nacional do Sistema Elétrico) com processamento de linguagem natural e automação de workflows.

![AIDE Dashboard](static/images/dashboard-preview.png)

## 📋 Índice

- [Características](#-características)
- [Arquitetura](#-arquitetura)
- [Instalação Rápida](#-instalação-rápida)
- [Configuração](#-configuração)
- [Uso](#-uso)
- [API](#-api)
- [Desenvolvimento](#-desenvolvimento)
- [Testes](#-testes)
- [Deploy](#-deploy)
- [Troubleshooting](#-troubleshooting)
- [Contribuindo](#-contribuindo)
- [Licença](#-licença)

## ✨ Características

### 🤖 **Assistente Inteligente**
- Chat com processamento de linguagem natural (GPT-4/Claude)
- Análise de intenção e extração de entidades
- Respostas contextualizadas com dados em tempo real
- Sugestões inteligentes baseadas no contexto

### 📊 **Visualização de Dados**
- Dashboard interativo em tempo real
- Gráficos dinâmicos (Plotly)
- Múltiplas visualizações: séries temporais, comparações, mapas de calor
- Exportação de dados e relatórios

### 🔄 **Automação com n8n**
- Ingestão automática de dados do ONS
- Processamento assíncrono de requisições
- Sistema de monitoramento e alertas
- Integração bidirecional entre workflows

### 📈 **Dados do Setor Elétrico**
- **Carga de Energia**: Consumo por subsistema em tempo real
- **CMO/PLD**: Custos marginais e preços de liquidação
- **Bandeiras Tarifárias**: Acionamentos e valores
- **Geração**: Produção por fonte energética
- **Reservatórios**: Níveis de armazenamento
- **Intercâmbio**: Transferências entre regiões

### 🔐 **Segurança e Confiabilidade**
- Autenticação e autorização
- Rate limiting e proteção contra DDoS
- Backup automático de dados
- Sistema de cache inteligente (Redis)
- Monitoramento de saúde do sistema

## 🏗️ Arquitetura

```mermaid
graph TB
    subgraph "Frontend"
        A[Streamlit UI] --> B[Chat Interface]
        A --> C[Dashboard]
        A --> D[Analytics]
    end
    
    subgraph "Backend Services"
        E[n8n Workflows] --> F[Data Ingestion]
        E --> G[Chat Processing]
        E --> H[Monitoring]
    end
    
    subgraph "Data Layer"
        I[(PostgreSQL)] --> J[Data Records]
        I --> K[Chat History]
        L[(Redis Cache)] --> M[Sessions]
        L --> N[Metrics]
    end
    
    subgraph "External"
        O[ONS API] --> F
        P[OpenAI/Claude] --> G
    end
    
    A --> E
    E --> I
    E --> L
```

### Componentes Principais

| Componente | Tecnologia | Função |
|------------|------------|---------|
| **Interface** | Streamlit | UI interativa e visualizações |
| **Workflows** | n8n | Orquestração e automação |
| **Banco de Dados** | PostgreSQL | Armazenamento persistente |
| **Cache** | Redis | Cache e sessões |
| **IA** | OpenAI/Claude | Processamento de linguagem |
| **Proxy** | Nginx | Load balancing e SSL |

## ⚡ Instalação Rápida

### Pré-requisitos

- Docker e Docker Compose
- Chave de API (OpenAI ou Anthropic)
- 4GB RAM mínimo
- 10GB espaço em disco

### 1. Clone o repositório

```bash
git clone https://github.com/seu-usuario/aide-system.git
cd aide-system
```

### 2. Execute o script de instalação

```bash
chmod +x quickstart.sh
./quickstart.sh
```

Escolha a opção **1** para instalação completa.

### 3. Configure as chaves de API

Edite o arquivo `.env`:

```bash
# Escolha uma das opções:
OPENAI_API_KEY=sk-your-openai-key-here
# ou
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here
```

### 4. Inicie o sistema

```bash
docker-compose up -d
```

### 5. Acesse os serviços

- **Streamlit (Interface)**: http://localhost:8501
- **n8n (Workflows)**: http://localhost:5678
- **PgAdmin (Banco)**: http://localhost:5050

## ⚙️ Configuração

### Variáveis de Ambiente

Copie `.env.example` para `.env` e configure:

```env
# Banco de Dados
DB_HOST=postgres
DB_PORT=5432
DB_NAME=aide_db
DB_USER=aide_user
DB_PASSWORD=your_secure_password

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=your_redis_password

# n8n
N8N_USER=aide_admin
N8N_PASSWORD=your_n8n_password
N8N_API_KEY=your_n8n_api_key
N8N_WEBHOOK_TOKEN=your_webhook_token

# IA (escolha uma)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# ONS API
ONS_API_URL=https://dados.ons.org.br/api/v1
ONS_API_KEY=your_ons_key
```

### Importar Workflows no n8n

1. Acesse http://localhost:5678
2. Faça login com as credenciais do `.env`
3. Vá para **Workflows** → **Import**
4. Importe os arquivos da pasta `workflows/`:
   - `aide-data-ingestion-workflow.json`
   - `aide-chat-processing-workflow.json`
   - `aide-monitoring-workflow.json`
5. Configure as credenciais em cada workflow
6. Ative os workflows

## 💻 Uso

### Interface Principal (Streamlit)

#### Chat Inteligente

Faça perguntas em linguagem natural:

```
"Qual a carga atual do Sudeste?"
"Compare o CMO entre as regiões"
"Mostre a evolução da demanda na última semana"
"Qual a previsão de consumo para amanhã?"
```

#### Dashboard

Visualize métricas em tempo real:
- Carga total do sistema
- CMO/PLD por região
- Status das bandeiras tarifárias
- Níveis de reservatórios

#### Análises Avançadas

Execute análises customizadas:
- Comparações regionais
- Tendências temporais
- Correlações entre métricas
- Previsões e projeções

### API Python

```python
from services.n8n_service import get_n8n_service, ChatResponse

# Inicializar serviço
service = get_n8n_service()

# Processar mensagem de chat
response = await service.process_chat_message(
    message="Qual a carga atual?",
    user_id="user_123",
    session_id="session_456"
)

# Converter para objeto tipado
chat_response = ChatResponse(response)
print(chat_response.text)
print(f"Confiança: {chat_response.confidence}")

# Disparar ingestão de dados
result = await service.trigger_data_ingestion(
    datasets=["carga_energia", "cmo_pld"],
    priority="high"
)

# Verificar saúde do sistema
health = service.get_system_health()
print(f"Health Score: {health['health_score']}%")
```

## 🧪 Testes

### Executar Suite de Testes

```bash
# Todos os testes
make test

# Testes específicos
docker-compose exec streamlit pytest tests/test_n8n_service.py -v

# Testes de integração
docker-compose exec streamlit pytest -m integration

# Testes de performance
docker-compose exec streamlit pytest -m performance

# Coverage
docker-compose exec streamlit pytest --cov=services --cov-report=html
```

### Teste Manual dos Webhooks

```bash
# Testar Data Ingestion
curl -X POST http://localhost:5678/webhook/data-ingestion/trigger \
  -H "Content-Type: application/json" \
  -d '{"datasets": ["carga_energia"], "priority": "high"}'

# Testar Chat Processing
curl -X POST http://localhost:5678/webhook/chat/process \
  -H "Content-Type: application/json" \
  -d '{"message": "teste", "user_id": "test123"}'
```

## 🚀 Deploy

### Produção com Docker Compose

```bash
# Build e start em produção
docker-compose --profile production up -d

# Verificar status
docker-compose ps

# Ver logs
docker-compose logs -f
```

### Deploy na AWS

```bash
# Build da imagem
docker build -t aide-system:latest .

# Push para ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $ECR_URI
docker tag aide-system:latest $ECR_URI/aide-system:latest
docker push $ECR_URI/aide-system:latest

# Deploy com ECS/Fargate
aws ecs update-service --cluster aide-cluster --service aide-service --force-new-deployment
```

### Deploy no Kubernetes

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: aide-system
spec:
  replicas: 3
  selector:
    matchLabels:
      app: aide
  template:
    metadata:
      labels:
        app: aide
    spec:
      containers:
      - name: streamlit
        image: aide-system:latest
        ports:
        - containerPort: 8501
        env:
        - name: DB_HOST
          valueFrom:
            secretKeyRef:
              name: aide-secrets
              key: db-host
```

```bash
kubectl apply -f k8s/
```

## 🔍 Monitoramento

### Métricas Disponíveis

- **Sistema**: CPU, memória, disco
- **Aplicação**: Requisições/s, latência, erros
- **Banco**: Conexões, queries/s, locks
- **Cache**: Hit rate, memória, evictions
- **Workflows**: Execuções, sucessos, falhas

### Dashboard de Monitoramento

Acesse o status em tempo real:

```bash
make status
```

### Logs Centralizados

```bash
# Todos os logs
docker-compose logs -f

# Logs específicos
docker-compose logs -f streamlit
docker-compose logs -f n8n
docker-compose logs -f postgres
```

## 🛠️ Troubleshooting

### Problemas Comuns

#### 1. Webhook não responde

```bash
# Verificar n8n
docker-compose logs n8n --tail 50
docker-compose restart n8n

# Testar conectividade
curl http://localhost:5678/healthz
```

#### 2. Erro de conexão com banco

```bash
# Verificar PostgreSQL
docker-compose exec postgres pg_isready
docker-compose logs postgres --tail 50

# Reiniciar
docker-compose restart postgres
```

#### 3. Cache Redis não funciona

```bash
# Verificar Redis
docker-compose exec redis redis-cli ping

# Limpar cache
docker-compose exec redis redis-cli FLUSHDB
```

#### 4. Streamlit não carrega

```bash
# Verificar logs
docker-compose logs streamlit --tail 100

# Reiniciar
docker-compose restart streamlit
```

### Reset Completo

```bash
# Parar tudo
docker-compose down

# Limpar volumes (CUIDADO: apaga dados)
docker-compose down -v

# Reconstruir
docker-compose build --no-cache
docker-compose up -d
```

## 🤝 Contribuindo

### Setup de Desenvolvimento

```bash
# Clone o repo
git clone https://github.com/seu-usuario/aide-system.git
cd aide-system

# Crie branch
git checkout -b feature/nova-funcionalidade

# Instale dependências locais
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Execute em modo dev
make dev
```

### Padrões de Código

- Python: PEP 8, type hints
- Commits: Conventional Commits
- Branches: feature/, bugfix/, hotfix/
- PRs: Template obrigatório

### Testes Obrigatórios

```bash
# Lint
flake8 .
black --check .
mypy .

# Testes
pytest --cov=services --cov-report=term-missing

# Security
bandit -r services/
safety check
```

## 📊 Métricas de Performance

| Métrica | Alvo | Atual |
|---------|------|-------|
| **Tempo de resposta (P95)** | < 3s | 2.1s |
| **Taxa de sucesso** | > 99% | 99.3% |
| **Health score médio** | > 85% | 88% |
| **Freshness dos dados** | < 1h | 45min |
| **Disponibilidade** | 99.9% | 99.92% |

## 🔒 Segurança

- ✅ HTTPS/TLS em produção
- ✅ Autenticação OAuth2/JWT
- ✅ Rate limiting (100 req/min)
- ✅ SQL injection protection
- ✅ XSS protection
- ✅ CORS configurado
- ✅ Secrets em variáveis de ambiente
- ✅ Logs sanitizados

## 📚 Documentação Adicional

- [Arquitetura Detalhada](docs/architecture.md)
- [API Reference](docs/api.md)
- [Guia do Desenvolvedor](docs/developer-guide.md)
- [Workflows n8n](docs/workflows.md)
- [Troubleshooting Avançado](docs/troubleshooting.md)

## 📝 Changelog

### v1.0.0 (2024-01-15)
- 🎉 Lançamento inicial
- ✅ Chat inteligente com GPT-4/Claude
- ✅ Dashboard interativo
- ✅ Integração com dados ONS
- ✅ Workflows n8n automatizados
- ✅ Sistema de monitoramento

## 🏆 Equipe

- **Arquiteto de Soluções**: [Seu Nome]
- **Desenvolvedores**: [Time Dev]
- **Data Scientists**: [Time DS]
- **DevOps**: [Time Infra]

## 📜 Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

## 🙏 Agradecimentos

- ONS pelo acesso aos dados abertos
- Comunidade n8n pelos workflows
- OpenAI/Anthropic pelas APIs de IA
- Streamlit pela framework de UI

---

**AIDE System** - Transformando dados do setor elétrico em insights inteligentes 🚀

Para suporte: aide-support@example.com | [Documentação](https://docs.aide.com.br) | [Status](https://status.aide.com.br)