# Estrutura do Pipeline ML - ASPI

## Organização Atual vs Proposta

### Estrutura Atual (Funcional)
```
app/ml/
├── energy_ml_pipeline_fixed.py     # Pipeline principal (MANTER)
├── energy_ml_pipeline.py           # Arquivo corrompido
├── energy_ml_pipeline_simple.py    # Versão simplificada
└── __init__.py                     # Interface do módulo
```

### Estrutura Proposta (Otimizada)
```
app/ml/
├── __init__.py                     # Interface principal
├── core/
│   ├── __init__.py
│   ├── pipeline.py                 # Pipeline principal
│   ├── data_processor.py           # Preparação de dados
│   └── model_manager.py            # Gerenciamento de modelos
├── models/
│   ├── __init__.py
│   ├── regression.py               # Random Forest, XGBoost
│   ├── clustering.py               # K-Means
│   └── anomaly_detection.py        # Isolation Forest
├── interpretability/
│   ├── __init__.py
│   └── shap_explainer.py           # Explicações SHAP
├── utils/
│   ├── __init__.py
│   ├── metrics.py                  # Métricas e avaliação
│   └── visualization.py           # Visualizações ML
└── energy_ml_pipeline_fixed.py    # ATUAL - Manter para compatibilidade
```

## Recomendação para o Prazo

**MANTER ESTRUTURA ATUAL** - O arquivo `energy_ml_pipeline_fixed.py` está:
✅ Funcional e testado
✅ Integrado com o Streamlit
✅ Atende todos os requisitos acadêmicos
✅ Pipeline completo (4 algoritmos + SHAP)

**Melhorias Futuras** (pós-entrega):
- Refatoração modular
- Separação de responsabilidades
- Testes unitários
- Documentação API

## Configuração Atual do Pipeline

### Componentes Principais
1. **EnergyMLPipeline** - Classe principal
2. **Data Preparation** - Limpeza e feature engineering
3. **Model Training** - Random Forest + XGBoost
4. **Clustering** - K-Means
5. **Anomaly Detection** - Isolation Forest
6. **Interpretability** - SHAP explanations

### Integração
- Interface via `execute_ml_pipeline()`
- Compatibilidade com Streamlit
- Persistência de modelos
- Tratamento de erros robusto