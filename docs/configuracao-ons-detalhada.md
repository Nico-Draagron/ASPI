# =====================================================
# CONFIGURAÇÕES ONS - Resumo Técnico
# =====================================================

## 🌐 URLs Base Configuradas:

### APIs Principais:
- **Dados Portal**: https://dados.ons.org.br/api/v1
- **API Carga**: https://apicarga.ons.org.br/prd  
- **CKAN Datasets**: https://dados.ons.org.br/api/3/action/package_show?id=
- **Portal Histórico**: http://www.ons.org.br/historico/
- **Sintegre**: https://sintegre.ons.org.br/

### Configuração no .env:
```env
# ONS API Configuration
ONS_BASE_URL=https://dados.ons.org.br/api/v1
ONS_API_CARGA_URL=https://apicarga.ons.org.br/prd
ONS_API_KEY=                    # Não é obrigatório para a maioria dos endpoints
ONS_TIMEOUT=60
ONS_MAX_RETRIES=3
```

## 📥 PROCESSO DE DOWNLOAD:

### 1. Script Principal (download_dados.py):
- **Localização**: `data/download_dados.py`
- **Função**: Download paralelo de datasets
- **Período Padrão**: 2024-01-01 até hoje
- **Workers**: 4 threads simultâneas
- **Output**: `data/dados_ons/`

### 2. Fluxo de Download:

```
┌─────────────────────────────────────┐
│ FLUXO DE DOWNLOAD ONS               │
├─────────────────────────────────────┤
│ 1. Identifica tipo de dataset       │
│    ├─ API REST: carga programada    │
│    └─ CKAN: datasets históricos     │
│                                     │
│ 2. Para APIs REST:                  │
│    ├─ Monta params (data início/fim)│
│    ├─ Faz requisição HTTP           │
│    ├─ Converte JSON → DataFrame     │
│    └─ Salva CSV com append          │
│                                     │
│ 3. Para CKAN:                       │
│    ├─ Consulta metadados dataset    │
│    ├─ Lista recursos (arquivos)     │
│    ├─ Download arquivos grandes     │
│    └─ Salva por diretório           │
└─────────────────────────────────────┘
```

## 🗄️ ESTRUTURA DE DADOS:

### Diretórios Criados:
```
data/dados_ons/
├── carga-mensal/           # Dados mensais de carga
├── cmo-semanal/           # CMO semanal
├── cmo-semi-horario/      # CMO semi-horário
├── curva-carga/           # Curva de carga histórica
├── cargaProgramada/       # Carga programada (API)
└── cargaVerificada/       # Carga verificada (API)
```

## 🔄 TIPOS DE DOWNLOAD:

### A) APIs REST (Tempo Real):
```python
# Exemplo: Carga Verificada
URL = "https://apicarga.ons.org.br/prd/cargaVerificada"
PARAMS = {
    "cod_areacarga": "BR",      # Brasil
    "dat_inicio": "2024-01-01",
    "dat_fim": "2025-09-22"
}
```

### B) CKAN Datasets (Históricos):
```python
# Exemplo: Curva de Carga
URL = "https://dados.ons.org.br/api/3/action/package_show?id=curva-carga"
# Retorna metadados + URLs dos arquivos CSV/ZIP
```

## 📊 DADOS DISPONÍVEIS:

### 1. Carga de Energia:
- **cargaProgramada**: Carga programada por subsistema
- **cargaVerificada**: Carga verificada (real)
- **curva-carga**: Curva histórica detalhada
- **carga-mensal**: Consolidado mensal
- **carga-diaria**: Dados diários

### 2. Preços (CMO/PLD):
- **cmo-semanal**: CMO semanal por subsistema
- **cmo-semi-horario**: CMO a cada 30 minutos
- **pld-horario**: PLD horário

### 3. Geração:
- **geracao-usina**: Geração por usina
- **geracao-fonte**: Geração por fonte (hidro, térmica, eólica, solar)
- **geracao-verificada**: Geração verificada

### 4. Sistema:
- **reservatorios**: Níveis de reservatórios
- **intercambio**: Intercâmbio entre subsistemas
- **bandeiras-tarifarias**: Acionamento de bandeiras

## ⚙️ CONFIGURAÇÃO DE PRODUÇÃO:

### No docker-compose.yml:
```yaml
environment:
  - ONS_API_URL=https://dados.ons.org.br/api/v1
  - ONS_API_KEY=${ONS_API_KEY:-}
  - ONS_TIMEOUT=60
  - ONS_MAX_RETRIES=3
```

### No ons_service.py:
```python
class ONSService:
    BASE_URLS = {
        'api': 'https://dados.ons.org.br/api/v1/',
        'portal': 'https://dados.ons.org.br/',
        'sintegre': 'https://sintegre.ons.org.br/',
        'historico': 'http://www.ons.org.br/historico/'
    }
    
    # 20+ endpoints configurados para diferentes tipos de dados
```

## 🔐 AUTENTICAÇÃO:

### API Key (Opcional):
- A maioria dos endpoints ONS são **públicos**
- Alguns endpoints podem requerer registro
- Rate limiting aplicado por IP
- Recomendado: implementar cache e retry

### Headers Padrão:
```python
headers = {
    'Accept': 'application/json',
    'User-Agent': 'AIDE-System/1.0',
    'X-API-Key': api_key  # Se disponível
}
```

## 📈 PERFORMANCE:

### Otimizações Implementadas:
- **Threading**: 4 workers paralelos
- **Caching**: LRU cache para endpoints
- **Retry**: 3 tentativas com backoff exponencial
- **Streaming**: Download de arquivos grandes
- **Progress Bar**: tqdm para acompanhamento
- **Deduplicação**: Remove registros duplicados

### Limites:
- **Timeout**: 60 segundos por request
- **Rate Limit**: ~100 requests/minuto
- **Tamanho**: Sem limite para CKAN datasets
- **Concorrência**: 4 threads recomendadas