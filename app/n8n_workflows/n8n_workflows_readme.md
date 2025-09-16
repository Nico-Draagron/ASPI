# 🔄 n8n Workflows - AIDE System

## 📋 Visão Geral

O AIDE utiliza n8n para automação e orquestração de processos críticos do sistema. Os workflows são responsáveis por:

- 📊 **Ingestão de Dados**: Coleta automática de dados do ONS
- 💬 **Processamento de Chat**: Integração com IA para responder perguntas
- 📈 **Monitoramento**: Verificação contínua da saúde do sistema
- 💾 **Backup**: Backup automático de dados e configurações
- 📑 **Relatórios**: Geração automática de relatórios

## 🚀 Configuração Inicial

### 1. Instalação do n8n

```bash
# Via Docker (recomendado)
docker run -d \
  --name n8n \
  -p 5678:5678 \
  -e N8N_BASIC_AUTH_ACTIVE=true \
  -e N8N_BASIC_AUTH_USER=aide \
  -e N8N_BASIC_AUTH_PASSWORD=your_password \
  -e N8N_HOST=localhost \
  -e N8N_PORT=5678 \
  -e N8N_PROTOCOL=http \
  -e WEBHOOK_URL=http://localhost:5678 \
  -v ~/.n8n:/home/node/.n8n \
  n8nio/n8n

# Via npm
npm install n8n -g
n8n start
```

### 2. Configuração de Credenciais

No n8n, configure as seguintes credenciais:

#### PostgreSQL
```json
{
  "name": "AIDE PostgreSQL",
  "host": "localhost",
  "port": 5432,
  "database": "aide_db",
  "user": "aide_user",
  "password": "your_password"
}
```

#### Redis
```json
{
  "name": "AIDE Redis",
  "host": "localhost",
  "port": 6379,
  "password": "your_redis_password"
}
```

#### OpenAI/Claude
```json
{
  "name": "OpenAI API",
  "apiKey": "your_openai_api_key"
}
```

#### Telegram Bot (Opcional)
```json
{
  "name": "AIDE Telegram Bot",
  "accessToken": "your_bot_token"
}
```

#### Slack (Opcional)
```json
{
  "name": "AIDE Slack",
  "accessToken": "your_slack_token"
}
```

### 3. Importação dos Workflows

1. Acesse n8n em `http://localhost:5678`
2. Vá para **Workflows** → **Import**
3. Importe cada arquivo JSON da pasta `n8n_workflows/`:
   - `data_ingestion.json`
   - `chat_processing.json`
   - `monitoring.json`
   - `backup_workflow.json`

### 4. Configuração de Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto:

```env
# n8n Configuration
N8N_BASE_URL=http://localhost:5678
N8N_API_KEY=your_n8n_api_key
N8N_WEBHOOK_TOKEN=your_webhook_token

# Workflow IDs
N8N_WORKFLOW_DATA_INGESTION=aide-data-ingestion
N8N_WORKFLOW_CHAT=aide-chat-processing
N8N_WORKFLOW_MONITORING=aide-monitoring
N8N_WORKFLOW_BACKUP=aide-backup

# Alert Channels
TELEGRAM_CHAT_ID=your_telegram_chat_id
SLACK_CHANNEL=#aide-alerts
WEBHOOK_ALERT_URL=https://your-webhook-url.com/alerts

# ONS API
ONS_API_URL=https://dados.ons.org.br/api/v1
ONS_API_KEY=your_ons_api_key
```

## 📊 Workflows Disponíveis

### 1. Data Ingestion Workflow

**Arquivo**: `data_ingestion.json`

**Funcionalidades**:
- Executa a cada hora automaticamente
- Verifica novos dados no ONS
- Compara com dados existentes no BD
- Prioriza datasets críticos
- Processa em lotes para otimização
- Notifica sucesso/falha via Telegram

**Trigger Manual via Python**:
```python
from services.n8n_service import get_n8n_service

service = get_n8n_service()
result = await service.trigger_data_ingestion(
    datasets=['carga_energia', 'cmo_pld'],
    force_update=True
)
```

**Webhook URL**: `http://localhost:5678/webhook/data-ingestion`

### 2. Chat Processing Workflow

**Arquivo**: `chat_processing.json`

**Funcionalidades**:
- Processa mensagens de chat em tempo real
- Analisa intenção e entidades
- Busca dados relevantes no BD
- Integra com Claude/GPT para respostas
- Mantém histórico de conversas
- Cache de sessões no Redis

**Uso via Python**:
```python
from services.n8n_service import process_chat_streamlit

response = process_chat_streamlit(
    message="Qual a carga atual do Sudeste?",
    user_id="user123",
    session_id="session456"
)

print(response['response']['text'])
```

**Webhook URL**: `http://localhost:5678/webhook/chat/process`

### 3. Monitoring Workflow

**Arquivo**: `monitoring.json`

**Funcionalidades**:
- Verifica saúde do sistema a cada 5 minutos
- Monitora:
  - Disponibilidade do PostgreSQL
  - Status do Redis
  - Freshness dos dados
  - Taxa de erros
  - Uso de disco
  - Tempo de resposta da API
- Alertas multi-canal (Telegram, Slack, Webhook)
- Gera relatórios de saúde

**Verificação Manual**:
```python
from services.n8n_service import check_system_health_streamlit

health = check_system_health_streamlit()
print(f"Health Score: {health['health_score']}%")
print(f"Status: {health['status']}")
```

**Webhook URL**: `http://localhost:5678/webhook/monitoring`

### 4. Backup Workflow

**Arquivo**: `backup_workflow.json`

**Funcionalidades**:
- Backup diário automático às 2h
- Backup de:
  - Banco PostgreSQL
  - Cache Redis
  - Logs do sistema
  - Configurações
- Upload para S3/Google Drive
- Retenção configurável
- Notificações de sucesso/falha

## 🔧 Integração com Código Python

### Exemplo Completo de Integração

```python
# app/main.py
import streamlit as st
from services.n8n_service import get_n8n_service, WorkflowType
import asyncio

# Inicializar serviço
n8n_service = get_n8n_service()

# Interface Streamlit
st.title("AIDE - Sistema Inteligente")

# Verificar saúde do sistema
if st.sidebar.button("🔍 Verificar Sistema"):
    health = n8n_service.get_system_health()
    
    if health['health_score'] > 80:
        st.success(f"✅ Sistema Saudável: {health['health_score']}%")
    elif health['health_score'] > 60:
        st.warning(f"⚠️ Sistema Degradado: {health['health_score']}%")
    else:
        st.error(f"❌ Sistema Crítico: {health['health_score']}%")
    
    # Mostrar métricas
    for metric in health['metrics']:
        st.metric(metric['name'], metric['value'], metric['status'])

# Chat com IA
user_message = st.text_input("Digite sua pergunta:")

if user_message:
    with st.spinner("Processando..."):
        # Processar via n8n
        response = n8n_service.process_chat_message_sync(
            message=user_message,
            user_id=st.session_state.get('user_id', 'anonymous'),
            session_id=st.session_state.get('session_id')
        )
        
        if response['success']:
            st.write(response['response']['text'])
            
            # Mostrar visualização se disponível
            if response['response'].get('visualization'):
                st.plotly_chart(response['response']['visualization'])
        else:
            st.error(response.get('fallback_response'))

# Atualizar dados
if st.sidebar.button("🔄 Atualizar Dados"):
    result = asyncio.run(
        n8n_service.trigger_data_ingestion(['carga_energia'])
    )
    
    if result['success']:
        st.success(f"Atualização iniciada: {result['execution_id']}")
    else:
        st.error(f"Erro: {result['error']}")
```

### Decorador para Workflows Customizados

```python
from services.n8n_service import n8n_webhook, WorkflowType

@n8n_webhook(WorkflowType.DATA_INGESTION)
async def process_custom_data(data: dict):
    """Função que automaticamente dispara workflow n8n"""
    
    # Processar dados
    processed = transform_data(data)
    
    # O decorador automaticamente envia para n8n
    return {
        'data': processed,
        'timestamp': datetime.now().isoformat()
    }
```

## 📈 Monitoramento e Logs

### Visualizar Execuções

```python
# Obter histórico de execuções
history = n8n_service.get_execution_history(
    WorkflowType.DATA_INGESTION,
    limit=10
)

for execution in history:
    print(f"ID: {execution['id']}")
    print(f"Status: {execution['status']}")
    print(f"Tempo: {execution['execution_time']}ms")
```

### Dashboard de Monitoramento

Acesse o dashboard n8n em `http://localhost:5678/workflows` para:
- Ver execuções em tempo real
- Analisar logs detalhados
- Debugar workflows
- Ver métricas de performance

## 🛠️ Troubleshooting

### Problemas Comuns

#### 1. Webhook não responde
```bash
# Verificar se n8n está rodando
docker ps | grep n8n

# Ver logs
docker logs n8n

# Testar webhook
curl -X POST http://localhost:5678/webhook/chat/process \
  -H "Content-Type: application/json" \
  -d '{"message": "teste", "user_id": "test"}'
```

#### 2. Erro de autenticação
```python
# Verificar credenciais
print(n8n_service.base_url)
print(n8n_service.headers)

# Testar conexão
response = requests.get(f"{n8n_service.base_url}/api/v1/workflows")
print(response.status_code)
```

#### 3. Timeout em workflows
```python
# Aumentar timeout
workflow_config.timeout = 60  # segundos

# Ou configurar globalmente
N8N_DEFAULT_TIMEOUT=60
```

## 🔐 Segurança

### Boas Práticas

1. **Use HTTPS em produção**
   ```env
   N8N_PROTOCOL=https
   N8N_HOST=aide.yourdomain.com
   ```

2. **Tokens seguros para webhooks**
   ```python
   # Validar token no webhook
   if request.headers.get('X-Webhook-Token') != WEBHOOK_TOKEN:
       return {"error": "Unauthorized"}, 401
   ```

3. **Rate limiting**
   ```python
   from functools import wraps
   from flask_limiter import Limiter
   
   @limiter.limit("10 per minute")
   def webhook_endpoint():
       pass
   ```

4. **Criptografia de dados sensíveis**
   ```python
   from cryptography.fernet import Fernet
   
   key = Fernet.generate_key()
   cipher = Fernet(key)
   encrypted = cipher.encrypt(sensitive_data.encode())
   ```

## 📚 Recursos Adicionais

- [Documentação n8n](https://docs.n8n.io)
- [n8n Community Nodes](https://www.npmjs.com/search?q=n8n-nodes)
- [Exemplos de Workflows](https://n8n.io/workflows)
- [API Reference](https://docs.n8n.io/api/)

## 🤝 Suporte

Para problemas ou dúvidas:
1. Verifique os logs: `docker logs n8n`
2. Consulte o dashboard n8n
3. Abra uma issue no repositório
4. Contate a equipe de desenvolvimento

---

**Última atualização**: Janeiro 2024
**Versão**: 1.0.0
**Autor**: Equipe AIDE