# 🚀 AIDE - Guia de Execução Rápida

## 📋 O que foi implementado

### ✅ Requisitos do Trabalho Atendidos:

1. **✅ Machine Learning Tradicional**
   - 3 algoritmos implementados (Random Forest, XGBoost, XGBoost Tuned)
   - Pipeline completo com treino/teste/validação
   - Cross-validation com Time Series Split

2. **✅ Análise de Overfitting/Underfitting**
   - Learning curves implementadas
   - Diagnóstico automático
   - Métricas de comparação treino vs teste

3. **✅ Interpretabilidade**
   - SHAP values integrados
   - Feature importance
   - Explicação de predições individuais

4. **✅ Clustering & Anomalias**
   - K-Means com 4 clusters
   - Isolation Forest para anomalias
   - Silhouette score para validação

5. **✅ Interface Dupla**
   - **Básica**: Para usuários leigos com visualizações simples
   - **Avançada**: Para cientistas de dados com ML completo

6. **✅ EDA Completa**
   - Estatísticas descritivas
   - Distribuições e correlações
   - Análise temporal

## 🔧 Como Executar (Passo a Passo)

### Opção 1: Execução Rápida (Recomendado)

```bash
# 1. Entre no diretório do projeto
cd aide_project

# 2. Crie o diretório ML (importante!)
mkdir -p app/ml
touch app/ml/__init__.py

# 3. Copie o arquivo energy_ml_pipeline.py para app/ml/
# (cole o conteúdo do artifact "Módulo ML Completo" neste arquivo)

# 4. Atualize o main.py
# (substitua pelo conteúdo do artifact "main.py Atualizado")

# 5. Instale as dependências de ML
pip install scikit-learn xgboost shap lime joblib plotly

# 6. Execute a aplicação
streamlit run app/main.py
```

### Opção 2: Setup Completo com Script

```bash
# 1. Torne o script executável
chmod +x setup_and_run.sh

# 2. Execute
./setup_and_run.sh
```

### Opção 3: Docker (se configurado)

```bash
# 1. Build e execute
docker-compose up -d

# 2. Acesse
# http://localhost:8501
```

## 📁 Estrutura de Arquivos Necessários

```
app/
├── main.py                 # ⚠️ ATUALIZAR com o novo código
├── ml/                     # ⚠️ CRIAR esta pasta
│   ├── __init__.py        # ⚠️ CRIAR arquivo vazio
│   └