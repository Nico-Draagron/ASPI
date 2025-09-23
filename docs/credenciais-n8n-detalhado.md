# 🔐 Guia Detalhado: Criando Credenciais no n8n

## 📋 Visão Geral
Você precisa criar exatamente 3 credenciais no n8n para o chat-processing funcionar:
1. **ASPI PostgreSQL** - Para acessar o banco de dados
2. **ASPI Redis** - Para cache e sessões
3. **OpenAI API** - Para inteligência artificial

---

## 🚀 Passo 1: Acessar Interface de Credenciais

### 1.1 Abrir n8n
1. Abra seu navegador
2. Vá para: `http://localhost:5678`
3. Faça login:
   - **Usuário**: `admin`
   - **Senha**: `admin123`

### 1.2 Navegar para Credenciais
1. No menu lateral esquerdo, clique em **"Settings"** (⚙️)
2. Clique em **"Credentials"**
3. Você verá uma lista (provavelmente vazia) de credenciais

---

## 🗄️ Credencial 1: PostgreSQL (Banco de Dados)

### 1.3 Criar Credencial PostgreSQL
1. Clique no botão **"Add Credential"** (+ azul)
2. Na busca, digite: `postgres`
3. Selecione **"Postgres"** da lista
4. Preencha os campos **EXATAMENTE** assim:

```
┌─────────────────────────────────────┐
│ CONFIGURAÇÃO POSTGRESQL             │
├─────────────────────────────────────┤
│ Name: ASPI PostgreSQL               │
│ Host: postgres                      │
│ Database: aspi_db                   │
│ User: aspi                          │
│ Password: aspi123                   │
│ Port: 5432                          │
│ SSL: Disable                        │
│ Schema: public                      │
└─────────────────────────────────────┘
```

### ⚠️ Campos Importantes:
- **Name**: Deve ser exatamente `ASPI PostgreSQL` (com espaço)
- **Host**: Use `postgres` (nome do container Docker)
- **SSL**: Certifique-se de estar **desabilitado**

### 1.4 Testar Conexão PostgreSQL
1. Clique no botão **"Test"** 
2. Deve aparecer: ✅ **"Connection successful"**
3. Se der erro, verifique se os containers estão rodando:
   ```bash
   docker ps | grep postgres
   ```
4. Clique **"Save"**

---

## 🔴 Credencial 2: Redis (Cache)

### 2.1 Criar Credencial Redis
1. Clique **"Add Credential"** novamente
2. Digite na busca: `redis`
3. Selecione **"Redis"**
4. Preencha **EXATAMENTE** assim:

```
┌─────────────────────────────────────┐
│ CONFIGURAÇÃO REDIS                  │
├─────────────────────────────────────┤
│ Name: ASPI Redis                    │
│ Host: redis                         │
│ Port: 6379                          │
│ Password: redis123                  │
│ Database: 0                         │
└─────────────────────────────────────┘
```

### ⚠️ Campos Importantes:
- **Name**: Deve ser exatamente `ASPI Redis` (com espaço)
- **Host**: Use `redis` (nome do container Docker)
- **Password**: `redis123` (conforme configurado no Docker)

### 2.2 Testar Conexão Redis
1. Clique **"Test"**
2. Deve aparecer: ✅ **"Connection successful"**
3. Se der erro, verifique:
   ```bash
   docker ps | grep redis
   docker logs aspi-redis
   ```
4. Clique **"Save"**

---

## 🤖 Credencial 3: OpenAI API

### 3.1 Obter Chave OpenAI (se não tiver)
1. Vá para: https://platform.openai.com/api-keys
2. Faça login na sua conta OpenAI
3. Clique **"Create new secret key"**
4. Copie a chave (começa com `sk-`)
5. **IMPORTANTE**: Guarde em local seguro (só aparece uma vez)

### 3.2 Criar Credencial OpenAI
1. No n8n, clique **"Add Credential"**
2. Digite: `openai`
3. Selecione **"OpenAI"**
4. Preencha:

```
┌─────────────────────────────────────┐
│ CONFIGURAÇÃO OPENAI                 │
├─────────────────────────────────────┤
│ Name: OpenAI API                    │
│ API Key: sk-xxxxxxxxxxxxxxxxxxxxxxx │
│ Base URL: https://api.openai.com/v1 │
│ Organization ID: (deixar vazio)     │
└─────────────────────────────────────┘
```

### ⚠️ Campos Importantes:
- **Name**: Exatamente `OpenAI API` (com espaço)
- **API Key**: Sua chave real da OpenAI
- **Base URL**: Deixar o padrão ou vazio

### 3.3 Testar API OpenAI
1. Clique **"Test"**
2. Deve aparecer: ✅ **"Connection successful"**
3. Se der erro 401: Chave inválida ou sem créditos
4. Se der erro 429: Limite de rate excedido
5. Clique **"Save"**

---

## 📋 Verificação Final

### 4.1 Listar Credenciais Criadas
Na tela de Credentials, você deve ver:

```
✅ ASPI PostgreSQL (Postgres)
✅ ASPI Redis (Redis)  
✅ OpenAI API (OpenAI)
```

### 4.2 Testar Conectividade Manual
Execute estes comandos no PowerShell para verificar:

```powershell
# Testar PostgreSQL
docker exec -it aspi-postgres psql -U aspi -d aspi_db -c "SELECT 1;"

# Testar Redis
docker exec -it aspi-redis redis-cli -a redis123 ping

# Testar n8n
curl http://localhost:5678
```

---

## 🔧 Solução de Problemas

### Erro: "Could not connect to PostgreSQL"
**Causa**: Container não está rodando ou configuração errada
**Solução**:
```bash
docker ps | grep postgres
docker restart aspi-postgres
```

### Erro: "Redis connection failed"
**Causa**: Senha incorreta ou container inativo
**Solução**:
```bash
docker logs aspi-redis
docker exec -it aspi-redis redis-cli -a redis123 info
```

### Erro: "OpenAI API authentication failed"
**Possíveis causas**:
1. ❌ Chave API incorreta
2. ❌ Sem créditos na conta OpenAI
3. ❌ Chave revogada/expirada

**Soluções**:
1. Verificar chave em: https://platform.openai.com/api-keys
2. Verificar créditos em: https://platform.openai.com/account/billing
3. Gerar nova chave se necessário

---

## 🎯 Próximo Passo

Após criar as 3 credenciais com sucesso:

1. **Importar o workflow**: `chat-processing.json`
2. **Configurar nós**: Selecionar as credenciais criadas
3. **Ativar workflow**: Toggle ON
4. **Testar**: `python scripts/test_chat_processing.py`

---

## 📞 Verificação Rápida

Execute este teste para confirmar que tudo está funcionando:

```python
# Salve como test_credentials.py
import psycopg2
import redis
import openai

# Teste PostgreSQL
try:
    conn = psycopg2.connect(
        host="localhost", port=5432, 
        database="aspi_db", user="aspi", password="aspi123"
    )
    print("✅ PostgreSQL: OK")
    conn.close()
except: print("❌ PostgreSQL: ERRO")

# Teste Redis  
try:
    r = redis.Redis(host="localhost", port=6379, password="redis123", db=0)
    r.ping()
    print("✅ Redis: OK")
except: print("❌ Redis: ERRO")

# Teste OpenAI (substitua SUA_CHAVE)
try:
    openai.api_key = "SUA_CHAVE_AQUI"
    openai.Model.list()
    print("✅ OpenAI: OK")
except: print("❌ OpenAI: ERRO")
```

**Status**: ✅ Credenciais configuradas | 🎯 Pronto para importar workflow