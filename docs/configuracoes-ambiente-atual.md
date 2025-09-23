# ================================
# CONFIGURAÇÕES DE AMBIENTE ATUAIS
# Sistema ASPI - Status: 2025-09-22
# ================================

## 🌐 URLs dos Webhooks

### N8N Base Configuration:
- **URL Base**: http://localhost:5678
- **Porta**: 5678
- **Status**: ✅ Online

### Webhook Endpoints:
- **Chat Processing**: http://localhost:5678/webhook-test/chat/process
- **Admin Interface**: http://localhost:5678
- **Credentials**: admin / admin123

## 🖥️ Frontend/API Streamlit

### Streamlit Configuration:
- **URL Frontend**: http://localhost:8502
- **Porta**: 8502  
- **Status**: ✅ Online (HTTP 200)
- **Arquivo Principal**: app/main.py

## 🗄️ Bancos de Dados

### PostgreSQL:
- **Host Externo**: localhost:5432
- **Host Docker**: postgres:5432 (172.25.0.3)
- **Database**: aspi_db
- **User/Pass**: aspi / aspi123

### Redis:
- **Host Externo**: localhost:6379
- **Host Docker**: redis:6379 (172.25.0.2)
- **Password**: redis123
- **Database**: 0

## 🔗 Integração Frontend ↔ n8n

### Para o Streamlit conectar ao n8n:
```python
# URL do webhook para chamadas do frontend
CHAT_API_URL = "http://localhost:5678/webhook-test/chat/process"

# Exemplo de requisição
import requests
response = requests.post(
    CHAT_API_URL,
    json={
        "message": "Qual é a demanda de energia hoje?",
        "user_id": "user_123",
        "session_id": "session_456"
    }
)
```

## 🌍 URLs de Acesso Público

### Para uso em desenvolvimento:
- **Frontend**: http://localhost:8502
- **API/Webhook**: http://localhost:5678/webhook-test/chat/process
- **Admin n8n**: http://localhost:5678

### Para configuração em produção:
- Substitua `localhost` pelo seu domínio/IP público
- Configure SSL/HTTPS
- Ajuste portas conforme necessário

## ⚙️ Variáveis de Ambiente Resumidas

```env
# URLs Principais
N8N_WEBHOOK_URL=http://localhost:5678/webhook-test/chat/process
STREAMLIT_URL=http://localhost:8502
N8N_BASE_URL=http://localhost:5678

# Banco de Dados
DATABASE_URL=postgresql://aspi:aspi123@localhost:5432/aspi_db
REDIS_URL=redis://:redis123@localhost:6379/0

# Portas
N8N_PORT=5678
STREAMLIT_PORT=8502
POSTGRES_PORT=5432
REDIS_PORT=6379
```

## 🔧 Status dos Serviços
- ✅ **n8n**: Online (localhost:5678)
- ✅ **Streamlit**: Online (localhost:8502)  
- ✅ **PostgreSQL**: Online (localhost:5432)
- ✅ **Redis**: Online (localhost:6379)
- ✅ **Docker Network**: aspi_aspi_network funcionando