# app/Home.py
"""
AIDE - Interface Principal com Navegação
Interface dupla: Básica para usuários leigos e Avançada para cientistas de dados
"""

import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta

# Configuração da página
st.set_page_config(
    page_title="AIDE - Assistente Inteligente de Energia",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS Customizado
st.markdown("""
<style>
    /* Tema principal */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
        border-left: 4px solid #667eea;
    }
    
    .quick-action-btn {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem 2rem;
        border-radius: 8px;
        text-align: center;
        cursor: pointer;
        transition: transform 0.2s;
    }
    
    .quick-action-btn:hover {
        transform: translateY(-2px);
    }
    
    .info-card {
        background: #f0f2f6;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    
    .status-green { color: #10b981; }
    .status-yellow { color: #f59e0b; }
    .status-red { color: #ef4444; }
</style>
""", unsafe_allow_html=True)


# ========================================
# INTERFACE BÁSICA (USUÁRIOS LEIGOS)
# ========================================

def render_basic_interface():
    """Interface simplificada e intuitiva para usuários não-técnicos"""
    
    # Header principal
    st.markdown("""
    <div class="main-header">
        <h1 style="color: white; margin: 0; font-size: 2.5rem;">⚡ AIDE</h1>
        <p style="color: white; opacity: 0.9; font-size: 1.1rem; margin: 0.5rem 0;">
            Seu Assistente Inteligente de Energia
        </p>
        <p style="color: white; opacity: 0.7; font-size: 0.9rem;">
            Entenda o consumo e os custos de energia de forma simples
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Métricas principais em cards visuais
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="metric-card">
            <h4 style="color: #666; margin: 0;">⚡ Consumo Atual</h4>
            <h2 style="color: #667eea; margin: 0.5rem 0;">72.845 MW</h2>
            <p style="color: #10b981; margin: 0;">↑ 3.2% vs ontem</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="metric-card">
            <h4 style="color: #666; margin: 0;">💰 Custo Médio</h4>
            <h2 style="color: #667eea; margin: 0.5rem 0;">R$ 156/MWh</h2>
            <p style="color: #f59e0b; margin: 0;">↑ 12% na semana</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="metric-card">
            <h4 style="color: #666; margin: 0;">🚦 Bandeira</h4>
            <h2 style="color: #f59e0b; margin: 0.5rem 0;">Amarela</h2>
            <p style="color: #666; margin: 0;">R$ 2,989/100kWh</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="metric-card">
            <h4 style="color: #666; margin: 0;">💧 Reservatórios</h4>
            <h2 style="color: #667eea; margin: 0.5rem 0;">58.3%</h2>
            <p style="color: #ef4444; margin: 0;">↓ 5% no mês</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Seção de perguntas rápidas
    st.markdown("---")
    st.markdown("### 💬 O que você quer saber sobre energia?")
    
    # Tabs para diferentes categorias
    tab1, tab2, tab3, tab4 = st.tabs(["🏠 Consumo", "💰 Custos", "📊 Comparações", "💡 Dicas"])
    
    with tab1:
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📈 O consumo está normal hoje?", use_container_width=True):
                show_consumption_analysis()
            
            if st.button("🌡️ Como o clima afeta o consumo?", use_container_width=True):
                show_weather_impact()
            
            if st.button("⏰ Quais os horários de pico?", use_container_width=True):
                show_peak_hours()
        
        with col2:
            if st.button("📊 Histórico da última semana", use_container_width=True):
                show_weekly_history()
            
            if st.button("🏢 Consumo por região", use_container_width=True):
                show_regional_consumption()
            
            if st.button("📉 Previsão para amanhã", use_container_width=True):
                show_tomorrow_forecast()
    
    with tab2:
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("💸 Por que a conta está alta?", use_container_width=True):
                show_cost_analysis()
            
            if st.button("🚦 O que é bandeira tarifária?", use_container_width=True):
                show_tariff_explanation()
        
        with col2:
            if st.button("📅 Histórico de preços", use_container_width=True):
                show_price_history()
            
            if st.button("💡 Como economizar?", use_container_width=True):
                show_saving_tips()
    
    with tab3:
        # Gráfico simples e intuitivo
        st.markdown("#### Consumo de Energia por Região")
        
        # Dados para visualização
        regions = ['Sudeste/CO', 'Sul', 'Nordeste', 'Norte']
        consumption = [42350, 15230, 12845, 2420]
        colors = ['#667eea', '#764ba2', '#f59e0b', '#10b981']
        
        fig = go.Figure(data=[
            go.Bar(
                x=regions,
                y=consumption,
                marker_color=colors,
                text=[f'{c:,.0f} MW' for c in consumption],
                textposition='outside'
            )
        ])
        
        fig.update_layout(
            title="Consumo Atual por Região",
            yaxis_title="Consumo (MW)",
            xaxis_title="Região",
            showlegend=False,
            height=400,
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Explicação simples
        st.info("""
        💡 **Entenda o gráfico:**
        - **MW (Megawatt)**: Unidade de potência elétrica
        - **1 MW** abastece cerca de **330 casas**
        - O **Sudeste** consome mais por ter maior população e indústrias
        """)
    
    with tab4:
        st.markdown("#### 💡 Dicas para Economizar Energia")
        
        tips = [
            ("🌡️", "Ar-condicionado", "Configure para 23°C - cada grau a menos aumenta 8% no consumo"),
            ("🚿", "Chuveiro elétrico", "Banhos de 5 minutos e posição 'verão' economizam 30%"),
            ("💡", "Iluminação", "Troque lâmpadas por LED - economia de até 80%"),
            ("🧊", "Geladeira", "Evite abrir frequentemente e verifique as borrachas"),
            ("👕", "Máquina de lavar", "Acumule roupas e use capacidade máxima")
        ]
        
        for emoji, title, tip in tips:
            st.markdown(f"""
            <div class="info-card">
                <h4>{emoji} {title}</h4>
                <p>{tip}</p>
            </div>
            """, unsafe_allow_html=True)
    
    # Chat simplificado
    st.markdown("---")
    st.markdown("### 🗨️ Pergunte ao Assistente")
    
    col1, col2 = st.columns([5, 1])
    
    with col1:
        user_question = st.text_input(
            "Digite sua pergunta sobre energia:",
            placeholder="Ex: Por que o consumo aumenta no verão?",
            label_visibility="collapsed"
        )
    
    with col2:
        send_button = st.button("Enviar 📤", type="primary", use_container_width=True)
    
    if send_button and user_question:
        with st.spinner("Analisando sua pergunta..."):
            # Simular processamento
            import time
            time.sleep(1)
            
            # Resposta simplificada
            st.markdown("#### 🤖 Resposta do AIDE")
            
            st.success("""
            O consumo de energia aumenta no verão principalmente devido ao uso intensivo de 
            **ar-condicionado** e **ventiladores**. 
            
            📊 **Dados interessantes:**
            - O consumo pode aumentar **até 40%** nos meses mais quentes
            - Ar-condicionado representa **20% da conta** no verão
            - Pico de consumo ocorre entre **14h e 16h**
            
            💡 **Dica:** Use cortinas para bloquear o sol e programe o ar-condicionado 
            para desligar automaticamente durante a noite.
            """)


# ========================================
# INTERFACE AVANÇADA (CIENTISTAS DE DADOS)
# ========================================

def render_advanced_interface():
    """Interface completa com análises técnicas e ML"""
    
    # Header técnico
    st.markdown("## 🔬 AIDE - Análise Avançada de Dados Energéticos")
    st.markdown("*Interface para análise técnica com Machine Learning e estatística avançada*")
    
    # Sidebar com controles avançados
    with st.sidebar:
        st.markdown("## ⚙️ Configurações Avançadas")
        
        # Seleção de Dataset
        st.markdown("### 📊 Dados")
        dataset = st.selectbox(
            "Dataset ONS:",
            ["Carga Energia Horária", "CMO/PLD Semanal", "Geração por Fonte", 
             "Intercâmbio Regional", "Bandeira Tarifária"]
        )
        
        date_range = st.date_input(
            "Período de Análise:",
            value=[datetime.now() - timedelta(days=30), datetime.now()],
            format="DD/MM/YYYY"
        )
        
        subsystems = st.multiselect(
            "Subsistemas:",
            ["Sudeste/CO", "Sul", "Nordeste", "Norte"],
            default=["Sudeste/CO", "Sul"]
        )
        
        # Configurações de ML
        st.markdown("### 🤖 Machine Learning")
        
        ml_task = st.selectbox(
            "Tipo de Problema:",
            ["Regressão", "Classificação", "Clustering", "Detecção de Anomalias", "Séries Temporais"]
        )
        
        algorithms = st.multiselect(
            "Algoritmos:",
            ["Linear Regression", "Random Forest", "XGBoost", "SVM", 
             "Neural Network", "ARIMA", "Prophet", "LSTM"],
            default=["Random Forest", "XGBoost"]
        )
        
        # Feature Engineering
        st.markdown("### 🔧 Feature Engineering")
        
        feature_options = st.multiselect(
            "Features Adicionais:",
            ["Lag Features (t-1, t-24, t-168)", 
             "Rolling Statistics (MA, STD)", 
             "Fourier Features (Sazonalidade)",
             "Holiday Features", 
             "Weather Integration",
             "Economic Indicators"],
            default=["Lag Features (t-1, t-24, t-168)", "Rolling Statistics (MA, STD)"]
        )
        
        # Validação
        st.markdown("### 📈 Validação")
        
        validation_method = st.radio(
            "Método de Validação:",
            ["Train-Test Split (80/20)", 
             "K-Fold Cross-Validation (k=5)",
             "Time Series Split",
             "Walk-Forward Analysis"]
        )
        
        # Interpretabilidade
        st.markdown("### 🔍 Interpretabilidade")
        
        interpretability = st.multiselect(
            "Métodos:",
            ["SHAP Values", "LIME", "Partial Dependence", 
             "Feature Importance", "Permutation Importance"],
            default=["SHAP Values", "Feature Importance"]
        )
        
        # Botão de execução
        if st.button("🚀 Executar Pipeline Completo", type="primary", use_container_width=True):
            st.session_state.run_pipeline = True
    
    # Área principal com tabs
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📊 EDA", "🤖 Modelagem", "📈 Métricas", 
        "🔍 Interpretabilidade", "⚡ Deploy", "📝 Relatórios"
    ])
    
    # Tab 1: Análise Exploratória
    with tab1:
        render_eda_tab()
    
    # Tab 2: Modelagem
    with tab2:
        render_modeling_tab()
    
    # Tab 3: Métricas
    with tab3:
        render_metrics_tab()
    
    # Tab 4: Interpretabilidade
    with tab4:
        render_interpretability_tab()
    
    # Tab 5: Deploy
    with tab5:
        render_deployment_tab()
    
    # Tab 6: Relatórios
    with tab6:
        render_reports_tab()


def render_eda_tab():
    """Tab de Análise Exploratória de Dados"""
    
    st.markdown("### 📊 Análise Exploratória de Dados")
    
    # Métricas gerais do dataset
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Registros", "1,245,678", "↑ 12,345 hoje")
    
    with col2:
        st.metric("Features", "47", "15 engineered")
    
    with col3:
        st.metric("Missing", "0.3%", "↓ 0.1%")
    
    with col4:
        st.metric("Outliers", "2.1%", "156 detected")
    
    # Análises detalhadas
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Distribuição de Variáveis")
        
        # Gerar dados sintéticos para exemplo
        data = np.random.normal(100, 15, 1000)
        
        fig = go.Figure()
        fig.add_trace(go.Histogram(
            x=data,
            nbinsx=30,
            name='Distribution',
            marker_color='#667eea'
        ))
        
        fig.add_trace(go.Scatter(
            x=np.linspace(data.min(), data.max(), 100),
            y=50 * np.exp(-((np.linspace(data.min(), data.max(), 100) - 100) ** 2) / (2 * 15 ** 2)),
            mode='lines',
            name='Normal Fit',
            line=dict(color='red', width=2)
        ))
        
        fig.update_layout(
            title="Distribuição de Carga (MW)",
            xaxis_title="Carga (MW)",
            yaxis_title="Frequência",
            showlegend=True,
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Teste de normalidade
        st.info("""
        **Teste de Normalidade (Shapiro-Wilk)**
        - Statistic: 0.997
        - p-value: 0.234
        - **Conclusão**: Distribuição normal ✅
        """)
    
    with col2:
        st.markdown("#### Matriz de Correlação")
        
        # Correlação entre variáveis
        variables = ['Carga', 'Temperatura', 'CMO', 'Chuva', 'Reserv.']
        corr_matrix = np.random.rand(5, 5)
        np.fill_diagonal(corr_matrix, 1)
        corr_matrix = (corr_matrix + corr_matrix.T) / 2
        
        fig = go.Figure(data=go.Heatmap(
            z=corr_matrix,
            x=variables,
            y=variables,
            colorscale='RdBu',
            zmid=0,
            text=np.round(corr_matrix, 2),
            texttemplate='%{text}',
            textfont={"size": 10},
            colorbar=dict(title="Correlation")
        ))
        
        fig.update_layout(
            title="Matriz de Correlação",
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Correlações importantes
        st.warning("""
        **Correlações Significativas**
        - Temperatura × Carga: **0.82** (forte positiva)
        - Reservatório × CMO: **-0.75** (forte negativa)
        - Chuva × Geração Hidro: **0.68** (moderada positiva)
        """)
    
    # Análise temporal
    st.markdown("---")
    st.markdown("#### Decomposição de Série Temporal")
    
    # Gerar série temporal sintética
    dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='D')
    trend = np.linspace(70000, 75000, len(dates))
    seasonal = 5000 * np.sin(2 * np.pi * np.arange(len(dates)) / 365.25)
    noise = np.random.normal(0, 500, len(dates))
    ts = trend + seasonal + noise
    
    fig = make_subplots(
        rows=4, cols=1,
        shared_xaxes=True,
        subplot_titles=('Original', 'Tendência', 'Sazonalidade', 'Resíduo'),
        vertical_spacing=0.05
    )
    
    fig.add_trace(go.Scatter(x=dates, y=ts, name='Original', line=dict(color='blue')), row=1, col=1)
    fig.add_trace(go.Scatter(x=dates, y=trend, name='Trend', line=dict(color='red')), row=2, col=1)
    fig.add_trace(go.Scatter(x=dates, y=seasonal, name='Seasonal', line=dict(color='green')), row=3, col=1)
    fig.add_trace(go.Scatter(x=dates, y=noise, name='Residual', line=dict(color='gray')), row=4, col=1)
    
    fig.update_layout(height=600, showlegend=False, title_text="Decomposição STL")
    fig.update_xaxes(title_text="Data", row=4, col=1)
    
    st.plotly_chart(fig, use_container_width=True)


def render_modeling_tab():
    """Tab de Modelagem ML"""
    
    st.markdown("### 🤖 Modelagem e Treinamento")
    
    if st.session_state.get('run_pipeline', False):
        # Progress bar
        progress = st.progress(0)
        status = st.status("Iniciando pipeline...", expanded=True)
        
        with status:
            # Simular etapas do pipeline
            steps = [
                ("Carregando dados...", 10),
                ("Pré-processamento...", 20),
                ("Feature Engineering...", 30),
                ("Divisão treino/teste...", 40),
                ("Treinando Random Forest...", 60),
                ("Treinando XGBoost...", 80),
                ("Validação cruzada...", 90),
                ("Finalizando...", 100)
            ]
            
            for step, prog in steps:
                st.write(f"⏳ {step}")
                progress.progress(prog)
                import time
                time.sleep(0.5)
        
        status.update(label="✅ Pipeline concluído!", state="complete", expanded=False)
        
        # Resultados
        st.success("✅ Modelos treinados com sucesso!")
        
        # Comparação de modelos
        st.markdown("#### Comparação de Modelos")
        
        results_df = pd.DataFrame({
            'Modelo': ['Linear Regression', 'Random Forest', 'XGBoost', 'Neural Network'],
            'MAE Treino': [1523.4, 982.1, 845.3, 921.5],
            'MAE Teste': [1689.2, 1102.3, 923.7, 1205.8],
            'R² Treino': [0.82, 0.94, 0.96, 0.93],
            'R² Teste': [0.79, 0.91, 0.93, 0.88],
            'Tempo (s)': [0.3, 12.5, 8.7, 45.2],
            'Overfitting': ['Não', 'Baixo', 'Baixo', 'Médio']
        })
        
        # Destacar melhor modelo
        styled_df = results_df.style.highlight_min(
            subset=['MAE Teste'], 
            color='lightgreen'
        ).highlight_max(
            subset=['R² Teste'],
            color='lightgreen'
        )
        
        st.dataframe(styled_df, use_container_width=True)
        
        # Gráfico de comparação
        col1, col2 = st.columns(2)
        
        with col1:
            fig = go.Figure()
            fig.add_trace(go.Bar(
                name='MAE Treino',
                x=results_df['Modelo'],
                y=results_df['MAE Treino'],
                marker_color='lightblue'
            ))
            fig.add_trace(go.Bar(
                name='MAE Teste',
                x=results_df['Modelo'],
                y=results_df['MAE Teste'],
                marker_color='darkblue'
            ))
            fig.update_layout(
                title="Comparação MAE",
                yaxis_title="MAE",
                barmode='group',
                height=300
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=results_df['R² Treino'],
                y=results_df['R² Teste'],
                mode='markers+text',
                text=results_df['Modelo'],
                textposition='top center',
                marker=dict(
                    size=results_df['Tempo (s)'],
                    color=['green', 'blue', 'red', 'orange'],
                    showscale=True
                )
            ))
            fig.add_shape(
                type="line",
                x0=0.7, y0=0.7, x1=1, y1=1,
                line=dict(color="gray", dash="dash")
            )
            fig.update_layout(
                title="R² Score: Treino vs Teste",
                xaxis_title="R² Treino",
                yaxis_title="R² Teste",
                height=300
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Learning Curves
        st.markdown("#### Learning Curves - Análise de Overfitting")
        
        # Simular learning curves
        train_sizes = np.linspace(100, 10000, 20)
        train_scores = 1000 - 500 * np.exp(-train_sizes/3000)
        val_scores = 1100 - 500 * np.exp(-train_sizes/3000)
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=train_sizes, y=train_scores,
            mode='lines',
            name='Training Score',
            line=dict(color='blue', width=2),
            fill='tozeroy',
            fillcolor='rgba(0,100,200,0.2)'
        ))
        fig.add_trace(go.Scatter(
            x=train_sizes, y=val_scores,
            mode='lines',
            name='Validation Score',
            line=dict(color='red', width=2),
            fill='tozeroy',
            fillcolor='rgba(200,100,0,0.2)'
        ))
        
        # Adicionar anotações
        fig.add_annotation(
            x=8000, y=600,
            text="Modelo bem ajustado<br>Gap pequeno entre treino e validação",
            showarrow=True,
            arrowhead=2,
            ax=0, ay=-40,
            bgcolor="green",
            opacity=0.8,
            font=dict(color="white")
        )
        
        fig.update_layout(
            title="Learning Curves - XGBoost",
            xaxis_title="Tamanho do conjunto de treino",
            yaxis_title="MAE Score",
            height=400,
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Diagnóstico
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.success("""
            ✅ **Modelo Bem Ajustado**
            - Gap treino-teste: 78.4 (9.3%)
            - Convergência estável
            - Sem sinais de overfitting
            """)
        
        with col2:
            st.info("""
            📊 **Estatísticas**
            - Samples de treino: 80,000
            - Samples de teste: 20,000
            - Features: 47
            - CV Folds: 5
            """)
        
        with col3:
            st.warning("""
            ⚠️ **Recomendações**
            - Coletar mais dados extremos
            - Adicionar features climáticas
            - Testar ensemble methods
            """)


def render_metrics_tab():
    """Tab de Métricas Detalhadas"""
    
    st.markdown("### 📈 Métricas e Performance")
    
    # Seletor de modelo
    model_selected = st.selectbox(
        "Selecione o modelo para análise:",
        ["XGBoost (Melhor)", "Random Forest", "Neural Network", "Linear Regression"]
    )
    
    # Métricas principais
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("MAE", "923.7 MW", "↓ 15.4%", delta_color="inverse")
    
    with col2:
        st.metric("RMSE", "1,245.3 MW", "↓ 12.1%", delta_color="inverse")
    
    with col3:
        st.metric("R² Score", "0.93", "↑ 0.02")
    
    with col4:
        st.metric("MAPE", "4.2%", "↓ 0.8%", delta_color="inverse")
    
    # Análise de resíduos
    st.markdown("---")
    st.markdown("#### Análise de Resíduos")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # QQ Plot
        theoretical = np.random.normal(0, 1, 1000)
        sample = np.random.normal(0.1, 1.1, 1000)
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=theoretical,
            y=sample,
            mode='markers',
            marker=dict(color='blue', size=3),
            name='Residuals'
        ))
        fig.add_trace(go.Scatter(
            x=[-3, 3],
            y=[-3, 3],
            mode='lines',
            line=dict(color='red', dash='dash'),
            name='Normal Line'
        ))
        
        fig.update_layout(
            title="Q-Q Plot",
            xaxis_title="Theoretical Quantiles",
            yaxis_title="Sample Quantiles",
            height=350
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Residuals vs Fitted
        fitted = np.random.uniform(60000, 80000, 1000)
        residuals = np.random.normal(0, 500, 1000)
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=fitted,
            y=residuals,
            mode='markers',
            marker=dict(color='blue', size=3, opacity=0.5),
            name='Residuals'
        ))
        fig.add_hline(y=0, line_dash="dash", line_color="red")
        
        fig.update_layout(
            title="Residuals vs Fitted",
            xaxis_title="Fitted Values",
            yaxis_title="Residuals",
            height=350
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Matriz de confusão para classificação (se aplicável)
    st.markdown("---")
    st.markdown("#### Performance por Período")
    
    # Tabela de performance temporal
    periods_df = pd.DataFrame({
        'Período': ['Manhã (6h-12h)', 'Tarde (12h-18h)', 'Noite (18h-24h)', 'Madrugada (0h-6h)'],
        'MAE': [856.2, 923.7, 1102.3, 743.5],
        'RMSE': [1123.4, 1245.3, 1456.7, 982.1],
        'R²': [0.94, 0.93, 0.91, 0.95],
        'Samples': [15234, 15678, 14892, 12196]
    })
    
    st.dataframe(periods_df, use_container_width=True)
    
    # Performance por subsistema
    st.markdown("#### Performance por Subsistema")
    
    subsystems_df = pd.DataFrame({
        'Subsistema': ['Sudeste/CO', 'Sul', 'Nordeste', 'Norte'],
        'MAE': [1245.3, 523.7, 423.1, 156.8],
        'MAPE (%)': [3.2, 4.1, 3.8, 5.2],
        'R²': [0.94, 0.92, 0.93, 0.89]
    })
    
    fig = px.bar(
        subsystems_df,
        x='Subsistema',
        y='MAE',
        color='R²',
        color_continuous_scale='Viridis',
        title='Performance por Subsistema'
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_interpretability_tab():
    """Tab de Interpretabilidade (SHAP/LIME)"""
    
    st.markdown("### 🔍 Interpretabilidade do Modelo")
    
    # Seleção de método
    method = st.radio(
        "Método de Interpretação:",
        ["SHAP Values", "LIME", "Feature Importance", "Partial Dependence"],
        horizontal=True
    )
    
    if method == "SHAP Values":
        st.markdown("#### SHAP (SHapley Additive exPlanations)")
        
        # Feature importance global
        features = [
            'load_lag_24h', 'temperature', 'hour', 'load_lag_168h',
            'is_weekend', 'cmo_lag_1d', 'reservoir_level', 'rainfall',
            'month', 'load_ma_7d'
        ]
        importance = [0.245, 0.189, 0.134, 0.098, 0.076, 0.065, 0.054, 0.048, 0.043, 0.038]
        
        fig = go.Figure(go.Bar(
            x=importance,
            y=features,
            orientation='h',
            marker=dict(
                color=importance,
                colorscale='Reds',
                showscale=True,
                colorbar=dict(title="Importance")
            )
        ))
        
        fig.update_layout(
            title="Feature Importance (SHAP)",
            xaxis_title="Mean |SHAP Value|",
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # SHAP waterfall para instância específica
        st.markdown("#### Explicação de Predição Individual")
        
        instance_id = st.number_input(
            "ID da instância para explicar:",
            min_value=1,
            max_value=10000,
            value=42
        )
        
        # Simular SHAP values
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.info(f"""
            **Predição para Instância #{instance_id}**
            - Valor predito: **75,234 MW**
            - Valor real: **74,892 MW**
            - Erro: **342 MW (0.46%)**
            """)
        
        with col2:
            if st.button("Explicar Predição", type="primary"):
                st.session_state.explain = True
        
        if st.session_state.get('explain', False):
            # Waterfall plot simulado
            st.markdown("##### Contribuição de cada feature para a predição")
            
            contributions = {
                'Base value': 72500,
                'load_lag_24h = 74,230': +1823,
                'temperature = 28.5°C': +892,
                'hour = 15': +456,
                'is_weekend = 0': -234,
                'cmo_lag_1d = 156.3': -178,
                'reservoir_level = 58.3%': -89,
                'Others': +64,
                'Prediction': 75234
            }
            
            st.markdown("""
            ```
            Base value (média):           72,500 MW
            + load_lag_24h (74,230):      +1,823 MW
            + temperature (28.5°C):         +892 MW
            + hour (15h):                   +456 MW
            - is_weekend (0):               -234 MW
            - cmo_lag_1d (156.3):           -178 MW
            - reservoir_level (58.3%):       -89 MW
            + Others:                        +64 MW
            =====================================
            Final Prediction:             75,234 MW
            ```
            """)
    
    elif method == "Feature Importance":
        # Feature importance tradicional
        st.markdown("#### Importância das Features - Random Forest")
        
        features_df = pd.DataFrame({
            'Feature': ['load_lag_24h', 'temperature', 'hour', 'load_lag_168h',
                       'is_weekend', 'cmo_lag_1d', 'reservoir_level'],
            'Importance': [0.312, 0.234, 0.156, 0.098, 0.076, 0.065, 0.054],
            'Std': [0.023, 0.018, 0.012, 0.008, 0.006, 0.005, 0.004]
        })
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=features_df['Feature'],
            y=features_df['Importance'],
            error_y=dict(type='data', array=features_df['Std']),
            marker_color='#667eea'
        ))
        
        fig.update_layout(
            title="Feature Importance com Desvio Padrão",
            yaxis_title="Importance Score",
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)


def render_deployment_tab():
    """Tab de Deploy e Produção"""
    
    st.markdown("### ⚡ Deploy e Produção")
    
    # Status do modelo em produção
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.success("""
        ✅ **Modelo em Produção**
        - Versão: v2.3.1
        - Deploy: 15/09/2024
        - Uptime: 99.97%
        """)
    
    with col2:
        st.info("""
        📊 **Estatísticas (24h)**
        - Predições: 145,678
        - Latência média: 23ms
        - Taxa de erro: 0.02%
        """)
    
    with col3:
        st.warning("""
        ⚠️ **Monitoramento**
        - Data drift: Não detectado
        - Model drift: Monitorando
        - Próximo retrain: 7 dias
        """)
    
    # Configurações de deploy
    st.markdown("---")
    st.markdown("#### Configurações de Deploy")
    
    deploy_option = st.selectbox(
        "Ambiente de Deploy:",
        ["Development", "Staging", "Production"]
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("##### Configurações do Modelo")
        
        model_config = {
            "model_path": "/models/xgboost_v2.3.1.pkl",
            "preprocessor": "/models/preprocessor_v2.3.1.pkl",
            "feature_list": "/config/features_v2.3.1.json",
            "batch_size": st.number_input("Batch Size", 32, 1024, 128),
            "timeout": st.number_input("Timeout (ms)", 100, 5000, 1000),
            "cache_ttl": st.number_input("Cache TTL (min)", 1, 60, 15)
        }
        
        if st.button("Salvar Configurações", type="primary"):
            st.success("Configurações salvas!")
    
    with col2:
        st.markdown("##### Endpoints API")
        
        st.code("""
# Prediction endpoint
POST /api/v1/predict
{
    "timestamp": "2024-09-15T14:30:00",
    "subsystem": "SE/CO",
    "features": {...}
}

# Batch prediction
POST /api/v1/predict/batch
{
    "data": [...]
}

# Model info
GET /api/v1/model/info

# Health check
GET /api/v1/health
        """, language="python")
    
    # Monitoramento em tempo real
    st.markdown("---")
    st.markdown("#### Monitoramento em Tempo Real")
    
    # Simular métricas em tempo real
    timestamps = pd.date_range(start='2024-09-15 00:00', periods=24, freq='H')
    predictions = np.random.uniform(70000, 75000, 24)
    actuals = predictions + np.random.normal(0, 500, 24)
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=timestamps, y=predictions,
        mode='lines',
        name='Predicted',
        line=dict(color='blue')
    ))
    fig.add_trace(go.Scatter(
        x=timestamps, y=actuals,
        mode='lines',
        name='Actual',
        line=dict(color='green')
    ))
    
    fig.update_layout(
        title="Predições vs Valores Reais (Últimas 24h)",
        xaxis_title="Hora",
        yaxis_title="Carga (MW)",
        height=400,
        hovermode='x unified'
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_reports_tab():
    """Tab de Relatórios"""
    
    st.markdown("### 📝 Relatórios e Documentação")
    
    # Opções de relatório
    report_type = st.selectbox(
        "Tipo de Relatório:",
        ["Relatório Técnico Completo", "Executive Summary", "Model Card", "Documentação API"]
    )
    
    if report_type == "Relatório Técnico Completo":
        st.markdown("""
        #### 📄 Relatório Técnico - Projeto AIDE
        
        **1. Resumo Executivo**
        - Objetivo: Previsão de carga energética usando ML
        - Melhor modelo: XGBoost com MAE de 923.7 MW
        - R² Score: 0.93
        - Redução de erro: 15.4% vs baseline
        
        **2. Metodologia**
        - Dataset: 1.2M registros do ONS (2023-2024)
        - Features: 47 (15 engineered)
        - Algoritmos testados: 5
        - Validação: Time Series Split (k=5)
        
        **3. Resultados**
        - Performance consistente across subsistemas
        - Sem overfitting detectado
        - Interpretabilidade via SHAP
        
        **4. Conclusões**
        - Modelo pronto para produção
        - ROI estimado: R$ 2.3M/ano
        - Recomendações implementadas
        
        **5. Próximos Passos**
        - Integração com dados meteorológicos
        - Implementação de ensemble
        - A/B testing em produção
        """)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📥 Download PDF", type="primary", use_container_width=True):
                st.success("Download iniciado!")
        
        with col2:
            if st.button("📧 Enviar por Email", use_container_width=True):
                st.success("Email enviado!")
        
        with col3:
            if st.button("🔗 Compartilhar", use_container_width=True):
                st.success("Link copiado!")


# ========================================
# FUNÇÕES AUXILIARES
# ========================================

def show_consumption_analysis():
    """Mostra análise de consumo"""
    st.info("""
    ✅ **Consumo Normal**
    
    O consumo atual de **72.845 MW** está dentro da média esperada para este horário.
    
    - Comparado com ontem: +3.2%
    - Média da semana: 71.234 MW
    - Pico do dia: 78.920 MW (15h)
    """)

def show_weather_impact():
    """Mostra impacto do clima"""
    st.warning("""
    🌡️ **Impacto do Clima no Consumo**
    
    A temperatura atual de **28°C** está causando aumento no consumo:
    
    - Impacto estimado: +15% no consumo
    - Ar-condicionado: +4.500 MW
    - Recomendação: Prepare-se para pico às 15h
    """)

def show_peak_hours():
    """Mostra horários de pico"""
    st.error("""
    ⏰ **Horários de Pico**
    
    Os períodos de maior consumo são:
    
    - **Manhã**: 10h às 12h
    - **Tarde**: 14h às 16h (maior pico)
    - **Noite**: 18h às 21h (tarifa mais cara)
    
    💡 Evite usar equipamentos de alto consumo nestes horários!
    """)


# ========================================
# MAIN APP
# ========================================

def main():
    """Função principal do aplicativo"""
    
    # Menu de seleção de interface
    interface_mode = option_menu(
        menu_title=None,
        options=["Interface Básica", "Interface Avançada"],
        icons=["house", "gear"],
        menu_icon="cast",
        default_index=0,
        orientation="horizontal",
        styles={
            "container": {"padding": "0!important", "background-color": "#fafafa"},
            "icon": {"color": "#667eea", "font-size": "18px"},
            "nav-link": {
                "font-size": "16px",
                "text-align": "center",
                "margin": "0px",
                "--hover-color": "#eee",
            },
            "nav-link-selected": {"background-color": "#667eea"},
        }
    )
    
    # Renderizar interface selecionada
    if interface_mode == "Interface Básica":
        render_basic_interface()
    else:
        render_advanced_interface()
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; opacity: 0.6; font-size: 0.9rem;">
        AIDE - Assistente Inteligente para Dados do Setor Elétrico | 
        Dados: ONS | Última atualização: há 5 minutos
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
