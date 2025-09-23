# 🚀 Configuração do Chat Processing (Avançado) no n8n

## 📋 Visão Geral
O `chat-processing.json` é um workflow avançado que oferece:
- 🧠 Análise inteligente de intenções
- 📊 Consultas SQL dinâmicas baseadas no contexto
- ⚡ Verificação automática de atualização de dados
- 📈 Geração automática de visualizações
- 💾 Cache inteligente e persistência completa

## ✅ Pré-requisitos Atendidos
- ✅ **PostgreSQL**: Rodando na porta 5432
- ✅ **Redis**: Rodando na porta 6379
- ✅ **n8n**: Rodando na porta 5678
- ✅ **Tabelas criadas**: chat_history, query_templates, datasets, data_records

## 🔐 Credenciais Necessárias

### 1. PostgreSQL (ASPI Database)
```
Nome da Credencial: ASPI PostgreSQL
Tipo: PostgreSQL
Host: postgres
Porta: 5432
Database: aspi_db
Usuário: aspi
Senha: aspi123
SSL Mode: disable
```

### 2. Redis (ASPI Cache)
```
Nome da Credencial: ASPI Redis
Tipo: Redis
Host: redis
Porta: 6379
Senha: redis123
Database: 0
```

### 3. OpenAI API
```
Nome da Credencial: OpenAI API
Tipo: OpenAI
API Key: [SUA_CHAVE_OPENAI]
Base URL: https://api.openai.com/v1 (padrão)
```

## 📥 Importar Workflow

### Passo 1: Acessar n8n
1. Abra: http://localhost:5678
2. Login: `admin` / `admin123`

### Passo 2: Importar JSON
1. Clique no botão **"+"** (New)
2. Selecione **"Import from File"**
3. Navegue até: `C:\Users\maris\Desktop\ASPI\workflows\n8n\chat-processing.json`
4. Clique **"Import"**

### Passo 3: Configurar Credenciais nos Nós

#### Nós que precisam de PostgreSQL:
- **Buscar Histórico Chat**
- **Buscar Template Query** 
- **Verificar Idade Dados**
- **Executar Query**
- **Salvar Mensagem User**
- **Salvar Resposta IA**

#### Nós que precisam de Redis:
- **Buscar Sessão Cache**
- **Atualizar Cache Sessão**

#### Nós que precisam de OpenAI:
- **Claude/GPT Response**

### Passo 4: Configurar Cada Nó

1. **Clique em cada nó** que mostra um ⚠️ (alerta de credencial)
2. No campo **"Credential to connect with"**:
   - Para PostgreSQL: Selecione **"ASPI PostgreSQL"**
   - Para Redis: Selecione **"ASPI Redis"**
   - Para OpenAI: Selecione **"OpenAI API"**
3. Se a credencial não existir, clique **"Create New"**

## 🆔 Criando as Credenciais

### PostgreSQL
1. Vá em **Settings** → **Credentials**
2. Clique **"Add Credential"**
3. Procure por **"Postgres"**
4. Preencha:
   ```
   Name: ASPI PostgreSQL
   Host: postgres
   Database: aspi_db
   User: aspi
   Password: aspi123
   Port: 5432
   SSL: Disable
   ```
5. Clique **"Save"**

### Redis
1. **"Add Credential"** → **"Redis"**
2. Preencha:
   ```
   Name: ASPI Redis
   Host: redis
   Port: 6379
   Password: redis123
   Database: 0
   ```
3. **"Save"**

### OpenAI
1. **"Add Credential"** → **"OpenAI"**
2. Preencha:
   ```
   Name: OpenAI API
   API Key: sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```
3. **"Save"**

## ⚙️ Configurações do Workflow

### Webhook Settings
- **Path**: `/chat/process`
- **Method**: POST
- **Response Mode**: Response Node
- **CORS**: Habilitado para `*`

### Payload Esperado
```json
{
  "message": "Qual a carga atual do Sudeste?",
  "user_id": "user123",
  "session_id": "session001",
  "source": "web",
  "language": "pt-BR",
  "force_refresh": false
}
```

## 🧪 Testando o Workflow

### 1. Ativar o Workflow
- No n8n, clique no **toggle** no canto superior direito
- Status deve ficar **"Active"**

### 2. Teste via Script Python
Crie um arquivo `test_chat_processing.py`:

```python
import requests
import json

url = "http://localhost:5678/webhook/chat/process"
payload = {
    "message": "Como está a carga de energia do Sudeste hoje?",
    "user_id": "teste_user_001",
    "session_id": "sessao_teste_001",
    "source": "web"
}

response = requests.post(url, json=payload)
print(f"Status: {response.status_code}")
print(f"Resposta: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
```

### 3. Teste via curl
```bash
curl -X POST http://localhost:5678/webhook/chat/process \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Qual o CMO atual?",
    "user_id": "teste123",
    "session_id": "sessao123"
  }'
```

## 📊 Resposta Esperada

```json
{
  "session_id": "sessao123",
  "user_id": "teste123",
  "request_id": "req_1234567890_abc123",
  "response": {
    "text": "Com base nos dados mais recentes, o CMO atual está...",
    "intent": "cmo_pld",
    "confidence": 0.95,
    "data_summary": {
      "avg_price": "185.50",
      "max_price": "200.25",
      "subsystems": ["Sudeste", "Sul"]
    },
    "visualization": {
      "type": "bar",
      "title": "CMO por Subsistema",
      "data": { /* dados do gráfico */ }
    },
    "suggestions": [
      "Comparar patamares de carga",
      "Ver histórico semanal",
      "Analisar tendência de preços"
    ],
    "metadata": {
      "processing_time_ms": 1250,
      "tokens_used": 450,
      "model": "gpt-4-turbo-preview"
    }
  },
  "success": true
}
```

## 🔧 Troubleshooting

### Erro: "Credential not found"
**Solução**: Verifique se as credenciais foram criadas com os nomes exatos:
- `ASPI PostgreSQL`
- `ASPI Redis` 
- `OpenAI API`

### Erro: "Connection refused" (PostgreSQL/Redis)
**Solução**: Verifique se os containers estão rodando:
```bash
docker ps | grep -E "(postgres|redis)"
```

### Erro: "Table does not exist"
**Solução**: Execute novamente o script de migração:
```bash
docker exec -i aspi-postgres psql -U aspi -d aspi_db -f /docker-entrypoint-initdb.d/migrations/004_chat_processing_tables.sql
```

### Erro: OpenAI API Key inválida
**Solução**: 
1. Verifique se a chave está correta
2. Teste a chave separadamente
3. Verifique se tem créditos disponíveis

## 🚀 Próximos Passos

1. **✅ Criar credenciais** no n8n
2. **✅ Importar workflow** chat-processing.json
3. **✅ Configurar todos os nós** com credenciais
4. **✅ Ativar o workflow**
5. **✅ Testar com dados reais**
6. **🔄 Integrar com frontend** Streamlit

## 📈 Funcionalidades Avançadas

### Análise de Intenções
O workflow identifica automaticamente:
- `carga_energia` - Perguntas sobre consumo
- `cmo_pld` - Perguntas sobre preços
- `bandeiras` - Perguntas sobre tarifas
- `geracao` - Perguntas sobre produção
- `comparacao` - Análises comparativas
- `previsao` - Projeções futuras

### Queries Dinâmicas
- Templates configuráveis por intenção
- Parâmetros automáticos baseados no contexto
- Otimização de performance

### Visualizações Automáticas
- Gráficos de linha para séries temporais
- Gráficos de barra para comparações
- Configuração automática baseada nos dados

### Cache Inteligente
- Sessões persistentes no Redis
- Contexto de conversa mantido
- Dados frescos verificados automaticamente

---

**Status**: ✅ Pronto para configuração | 🎯 Workflow profissional para produção