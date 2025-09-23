# ASPI - Assistente Inteligente para Dados do Setor Elétrico

Sistema avançado de análise de dados do setor elétrico brasileiro com funcionalidades de chat inteligente, workflows automatizados e integração com APIs do ONS.

## 🎯 Características Principais

- **🤖 Chat Inteligente**: Interface conversacional com IA para consultas sobre dados do setor elétrico
- **📊 Análise de Dados**: Visualizações interativas e relatórios personalizados
- **⚡ Workflows Automatizados**: Coleta e processamento automático de dados usando n8n
- **🗄️ Banco de Dados Robusto**: PostgreSQL com modelos SQLAlchemy 2.0+
- **⚡ Cache Inteligente**: Redis para performance otimizada
- **🐳 Container Ready**: Ambiente Docker completo
- **📈 Monitoramento**: Sistema de métricas e alertas integrado

## 🏗️ Arquitetura do Sistema

```
ASPI/
├── app/                      # 🚀 Aplicação Principal
│   ├── models/              # 📋 Modelos SQLAlchemy 2.0+
│   │   ├── database.py      # Configuração do banco
│   │   ├── geracao.py       # Dados de geração
│   │   ├── carga.py         # Dados de carga
│   │   └── preco.py         # Dados de preços
│   ├── utils/               # 🛠️ Utilitários
│   │   ├── ons_api.py       # Cliente API ONS
│   │   ├── data_processor.py # Processamento de dados
│   │   └── chat_handler.py  # Manipulador de chat
│   ├── config.py            # ⚙️ Configurações
│   └── main.py              # 🎛️ Interface Streamlit
├── workflows/               # 🔄 Automação n8n
│   └── n8n/                # Workflows JSON
│       ├── data-ingestion.json    # Coleta de dados
│       ├── chat-processing.json   # Processamento chat
│       └── monitoring.json        # Monitoramento
├── tests/                   # 🧪 Testes
├── docs/                    # 📚 Documentação
├── monitoring/              # 📊 Scripts de monitoramento
├── database/                # 🗄️ Scripts SQL
│   └── init-databases.sql   # Inicialização do banco
├── docker-compose.yml       # 🐳 Orquestração Docker
├── requirements.txt         # 📦 Dependências Python
└── .env.example            # 🔧 Configurações de exemplo
```

## 🚀 Instalação e Configuração

### Pré-requisitos

- 🐳 **Docker** e **Docker Compose**
- 🐍 **Python 3.11+**
- 📦 **Git**
- 🔑 **API Keys** (OpenAI ou Anthropic para chat IA)

### 📥 Configuração Rápida (Recomendado)

1. **Clone o repositório:**
```bash
git clone <repository-url>
cd ASPI
```

2. **Configure as variáveis de ambiente:**
```bash
# Copie o arquivo de exemplo
cp .env.example .env

# Edite o arquivo .env e configure:
# - OPENAI_API_KEY (necessário para chat IA)
# - Outras configurações conforme necessário
```

3. **Inicie toda a infraestrutura:**
```bash
# Inicia PostgreSQL, Redis, n8n e aplicação
docker-compose up -d
```

4. **Aguarde os serviços iniciarem (2-3 minutos):**
```bash
# Verifique o status dos serviços
docker-compose ps
```

5. **Acesse as aplicações:**
- 🎛️ **ASPI Streamlit**: http://localhost:8501
- 🔄 **n8n Workflows**: http://localhost:5678
- 📊 **Monitoramento**: http://localhost:8000

### 💻 Desenvolvimento Local

Para desenvolvimento sem Docker:

1. **Configure o ambiente Python:**
```bash
# Crie ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows

# Instale dependências
pip install -r requirements.txt
```

2. **Configure serviços externos:**
```bash
# Inicie apenas PostgreSQL e Redis
docker-compose up -d postgres redis

# Configure o banco de dados
python -m app.models.database init
```

3. **Execute a aplicação:**
```bash
streamlit run app/main.py
```

## 🔧 Configuração Avançada

### 🔑 Configuração de API Keys

Edite o arquivo `.env`:

```env
# Necessário para funcionalidades de IA
OPENAI_API_KEY=sk-your-openai-api-key-here

# Ou use Anthropic como alternativa
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here
```

### 🗄️ Configuração de Banco de Dados

O sistema usa PostgreSQL com duas bases:
- `aspi_db`: Dados principais da aplicação
- `n8n_db`: Dados dos workflows n8n

### 🔄 Configuração de Workflows n8n

1. Acesse n8n em http://localhost:5678
2. Crie conta admin (primeira vez)
3. Importe os workflows de `workflows/n8n/`

## 📊 Fonte de Dados

O sistema integra com:

- **🏢 ONS (Operador Nacional do Sistema Elétrico)**
  - Dados de geração por fonte
  - Carga de energia por região
  - Preços de liquidação
  - Dados operacionais em tempo real

- **📈 APIs Externas**
  - Dados meteorológicos
  - Preços de commodities
  - Informações regulamentares

## 🔄 Workflows Disponíveis

### 1. 📥 Data Ingestion (`data-ingestion.json`)
- Coleta automática de dados do ONS
- Processamento e limpeza de dados
- Armazenamento no PostgreSQL
- Atualização de cache Redis

### 2. 💬 Chat Processing (`chat-processing.json`)
- Processamento de consultas via chat
- Integração com APIs de IA
- Análise de contexto e dados
- Resposta formatada para usuário

### 3. 📊 Monitoring (`monitoring.json`)
- Monitoramento de sistema
- Alertas automáticos
- Métricas de performance
- Relatórios de saúde

## 🧪 Testes

```bash
# Execute todos os testes
python -m pytest tests/

# Testes específicos
python -m pytest tests/test_models.py
python -m pytest tests/test_api.py

# Cobertura de código
python -m pytest --cov=app tests/
```

## 📊 Monitoramento

O sistema inclui:

- **📈 Métricas Prometheus**: http://localhost:8000
- **📊 Dashboard Grafana**: Configurável
- **🚨 Alertas**: Via webhook ou email
- **📝 Logs Estruturados**: JSON format

## 🔒 Segurança

- 🔐 **Autenticação JWT**
- 🛡️ **Validação de entrada**
- 🔒 **Sanitização de dados**
- 🌐 **CORS configurado**
- 🔑 **API Keys protegidas**

## 🚀 Deploy em Produção

### 🐳 Docker Swarm

```bash
# Inicialize swarm
docker swarm init

# Deploy stack
docker stack deploy -c docker-compose.yml aspi
```

### ☁️ Kubernetes

Consulte `docs/kubernetes/` para manifests.

## 🛠️ Troubleshooting

### Problemas Comuns

1. **Serviços não iniciam:**
```bash
# Verifique logs
docker-compose logs

# Reinicie serviços
docker-compose restart
```

2. **Erro de conexão com banco:**
```bash
# Verifique se PostgreSQL está rodando
docker-compose ps postgres

# Teste conexão
docker-compose exec postgres psql -U aspi aspi_db
```

3. **Workflows n8n não funcionam:**
```bash
# Verifique n8n
docker-compose logs n8n

# Acesse interface n8n
# http://localhost:5678
```

## 🤝 Contribuição

1. 🍴 **Fork** o projeto
2. 🌿 **Crie** uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. ✅ **Commit** suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. 📤 **Push** para a branch (`git push origin feature/AmazingFeature`)
5. 🔄 **Abra** um Pull Request

### 📋 Guidelines

- Siga PEP 8 para código Python
- Adicione testes para novas funcionalidades
- Documente mudanças no README
- Use type hints em Python

## 📄 Licença

Este projeto está sob a licença **MIT**. Veja o arquivo `LICENSE` para detalhes.

## 📞 Suporte

- 📧 **Email**: suporte@aspi.com.br
- 🐛 **Issues**: [GitHub Issues](link-para-issues)
- 📚 **Documentação**: [Wiki do Projeto](link-para-wiki)

---

**Desenvolvido com ❤️ para o setor elétrico brasileiro**