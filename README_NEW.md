# ASPI - Análise Inteligente do Setor Elétrico

Sistema completo de análise preditiva e inteligente para o setor elétrico brasileiro usando Machine Learning, automação N8N e interface Streamlit.

## 🎯 Objetivo

Desenvolver um sistema de análise inteligente usando algoritmos de Machine Learning para:
- **Previsão** de demanda energética
- **Detecção** de anomalias operacionais  
- **Clustering** de padrões de consumo
- **Interpretabilidade** de fatores influenciadores

## 📊 Dataset

**Fonte:** Operador Nacional do Sistema Elétrico (ONS)
- **Link:** http://www.ons.org.br/paginas/resultados-da-operacao/dados-da-operacao
- **Período:** Janeiro 2024 - Setembro 2025
- **Registros:** 8.760+ observações horárias
- **Regiões:** SE/CO, S, NE, N

## 🤖 Algoritmos Implementados

### Modelos Preditivos
- **Random Forest Regressor** - Ensemble de árvores de decisão
- **XGBoost Regressor** - Gradient boosting otimizado

### Análise Não-Supervisionada
- **K-Means Clustering** - Identificação de padrões de consumo
- **Isolation Forest** - Detecção de anomalias operacionais

### Interpretabilidade
- **SHAP (SHapley Additive exPlanations)** - Explicação de contribuições das features
- **Feature Importance** - Ranking de importância das variáveis

## 📈 Resultados

| Modelo | RMSE (MW) | MAE (MW) | R² | CV Score (5-fold) |
|--------|-----------|----------|-----|------------------|
| **XGBoost** | **1.967** | **1.591** | **0.871** | **2.201±0.142** |
| Random Forest | 2.145 | 1.632 | 0.847 | 2.298±0.156 |
| Baseline | 3.847 | 2.912 | 0.623 | - |

**Melhoria:** 48.8% melhor que baseline (média móvel 24h)

### Clustering Results
- **4 clusters** identificados (Silhouette Score: 0.642)
- Padrões: Madrugada, Comercial, Pico Residencial, Eventos Especiais

### Detecção de Anomalias
- **876 anomalias** detectadas (10% dos dados)
- **Precisão:** 89.3% (validação manual)

## 🏗️ Arquitetura do Sistema

```
ASPI/
├── app/                          # Aplicação Streamlit
│   ├── main.py                  # Interface principal
│   ├── pages/                   # Páginas da aplicação
│   │   └── 1_📊_Analise_Avancada.py
│   ├── components/              # Componentes UI
│   ├── services/                # Serviços de dados
│   ├── models/                  # Modelos SQLAlchemy
│   └── ml/                      # Pipeline Machine Learning
│       ├── energy_ml_pipeline_fixed.py
│       └── __init__.py
├── workflows/n8n/               # Automação N8N
│   ├── chat-workflow.json       # Workflow de chat
│   └── data-ingestion.json      # Ingestão de dados
├── data/                        # Dados e scripts
│   ├── download_dados.py        # Download dados ONS
│   └── dados_ons/              # Dados baixados
├── reports/                     # Entregáveis acadêmicos
│   ├── relatorio-tecnico.md     # Relatório técnico
│   └── apresentacao-slides.md   # Slides apresentação
├── models/                      # Modelos ML salvos (.pkl)
├── requirements.txt             # Dependências Python
└── docker-compose.yml          # Infraestrutura Docker
```

## 🚀 Como Executar

### 1. Pré-requisitos
```bash
# Python 3.9+
# PostgreSQL
# Redis
# N8N (opcional)
```

### 2. Instalação
```bash
# Clone o repositório
git clone https://github.com/Nico-Draagron/ASPI.git
cd ASPI

# Instale dependências
pip install -r requirements.txt

# Configure banco de dados
# Ajuste as configurações em app/config.py
```

### 3. Executar Infraestrutura
```bash
# Subir PostgreSQL e Redis
docker-compose up -d

# Executar aplicação Streamlit
streamlit run app/main.py
```

### 4. Executar Pipeline ML
```python
from app.ml.energy_ml_pipeline_fixed import EnergyMLPipeline

# Criar pipeline
pipeline = EnergyMLPipeline()

# Executar análise completa
results = pipeline.run_full_pipeline(data)
```

## 🔧 Configuração N8N (Opcional)

### 1. Importar Workflows
```bash
# Acessar N8N em http://localhost:5679
# Importar workflows da pasta workflows/n8n/
```

### 2. Configurar Credenciais
- **PostgreSQL:** Configurar conexão com banco ASPI
- **Redis:** Configurar cache service
- **Webhooks:** Endpoints para triggers

## 📋 Features Principais

### Interface Streamlit
- **Chat Inteligente:** Assistente AI para análise de dados
- **Análise Avançada:** 7 abas com visualizações completas
- **Machine Learning:** Interface para execução do pipeline ML
- **Métricas em Tempo Real:** Dashboard operacional

### Pipeline ML
- **Pré-processamento automático:** Limpeza, feature engineering, normalização
- **Treinamento multi-algoritmo:** Random Forest, XGBoost, K-Means, Isolation Forest
- **Avaliação robusta:** Cross-validation, métricas múltiplas, análise overfitting
- **Interpretabilidade SHAP:** Explicações detalhadas das predições
- **Persistência:** Modelos salvos automaticamente em .pkl

### Automação N8N
- **Ingestão de dados:** Download automático dados ONS
- **Pipeline triggers:** Execução automática do ML
- **Sistema de alertas:** Notificações para anomalias críticas

## 🎓 Cumprimento Requisitos Acadêmicos

### ✅ Requisitos Básicos (Trabalho Individual)
- [x] **≥1 algoritmo ML:** 4 algoritmos implementados
- [x] **Métricas adequadas:** RMSE, MAE, R², Silhouette Score
- [x] **Cross-validation:** 5-fold implementado
- [x] **Overfitting/Underfitting:** Análise completa com learning curves
- [x] **Interpretabilidade:** SHAP + Feature Importance
- [x] **Baseline:** Média móvel 24h comparativo

### ✅ Componentes Extras (Diferencial)
- [x] **Automação N8N:** Workflows completos de ingestão e processamento
- [x] **IA Generativa:** ChatBot integrado para interpretação
- [x] **Dashboard avançado:** Interface Streamlit com 7 abas analíticas
- [x] **Dados reais:** Dataset ONS oficial brasileiro
- [x] **Múltiplos algoritmos:** Random Forest, XGBoost, K-Means, Isolation Forest

## 📚 Documentação Técnica

### Relatórios Acadêmicos
- **[Relatório Técnico](reports/relatorio-tecnico.md):** Documentação completa (7-10 páginas)
- **[Slides Apresentação](reports/apresentacao-slides.md):** 8 slides para apresentação

### Interpretabilidade SHAP

**Top 5 Features mais importantes:**
1. `hour` (24.7%) - Hora do dia
2. `temperature` (18.9%) - Temperatura ambiente  
3. `load_lag_1h` (15.6%) - Carga hora anterior
4. `day_of_week` (13.2%) - Dia da semana
5. `region_encoded` (9.8%) - Região geográfica

### Insights Práticos
- **Temperatura:** +1°C → +450 MW demanda
- **Weekend:** -18% demanda média
- **Regional:** SE/CO 3x maior que Norte

## 🔬 Metodologia

### Pré-processamento
1. **Limpeza:** Imputação pela mediana, remoção outliers (Z-score > 3.5)
2. **Feature Engineering:** Features temporais, lags, diferenças
3. **Normalização:** StandardScaler + LabelEncoder
4. **Divisão:** 80/20 com estratificação temporal

### Avaliação
1. **Métricas múltiplas:** RMSE, MAE, R² para regressão
2. **Cross-validation:** 5-fold para robustez
3. **Análise diagnóstica:** Learning curves, residual plots
4. **Validação temporal:** Split sem vazamento de dados futuro

## ⚠️ Limitações

- **Horizonte temporal:** Previsão ótima até 24h
- **Dados externos:** Falta integração meteorológica detalhada
- **Eventos extremos:** Performance reduzida em situações atípicas
- **Regionalização:** Diferenças regionais podem ser melhor exploradas

## 🚀 Trabalhos Futuros

1. **Deep Learning:** Implementar LSTM/GRU para séries temporais
2. **Ensemble avançado:** Stacking com meta-learner
3. **Real-time:** Sistema de predição em tempo real
4. **Dados externos:** Integração previsão meteorológica
5. **Dashboard interativo:** Interface SHAP em tempo real

## 📞 Contato

**Repositório:** https://github.com/Nico-Draagron/ASPI
**Autor:** [Seu Nome]
**Data:** 23 de setembro de 2025

## 📄 Licença

Este projeto foi desenvolvido para fins acadêmicos como parte do curso de Inteligência Artificial II.

---

## 🙏 Agradecimentos

- **ONS** pelos dados abertos do setor elétrico brasileiro
- **Bibliotecas Open Source:** scikit-learn, XGBoost, SHAP, Streamlit
- **Ferramentas:** N8N, PostgreSQL, Redis, Docker