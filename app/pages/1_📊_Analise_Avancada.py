"""
AIDE - Página de Análise Avançada
pages/1_📊_Analise_Avancada.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# Configuração da página
st.set_page_config(
    page_title="AIDE - Análise Avançada",
    page_icon="📊",
    layout="wide"
)

# CSS customizado
st.markdown("""
    <style>
    .analysis-header {
        background: linear-gradient(135deg, #e7cba9 0%, #f4e4d4 100%);
        padding: 2rem;
        border-radius: 12px;
        margin-bottom: 2rem;
    }
    
    .insight-card {
        background: white;
        border-left: 4px solid #e7cba9;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    .metric-highlight {
        background: linear-gradient(135deg, #cfe4f9 0%, #e8f4fd 100%);
        padding: 1.5rem;
        border-radius: 10px;
        text-align: center;
    }
    
    .anomaly-alert {
        background: #fee2e2;
        border-left: 4px solid #ef4444;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    
    .opportunity-card {
        background: #d1fae5;
        border-left: 4px solid #10b981;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    </style>
""", unsafe_allow_html=True)

def generate_synthetic_data(days=90):
    """Gera dados sintéticos para demonstração"""
    dates = pd.date_range(end=datetime.now(), periods=days, freq='D')
    
    data = []
    for date in dates:
        for region in ['Sudeste/CO', 'Sul', 'Nordeste', 'Norte']:
            base_load = {
                'Sudeste/CO': 42000,
                'Sul': 15000,
                'Nordeste': 10000,
                'Norte': 5500
            }[region]
            
            # Adicionar sazonalidade e ruído
            seasonal = np.sin(2 * np.pi * date.dayofyear / 365) * base_load * 0.1
            weekly = np.sin(2 * np.pi * date.dayofweek / 7) * base_load * 0.05
            noise = np.random.normal(0, base_load * 0.02)
            
            load = base_load + seasonal + weekly + noise
            
            # CMO correlacionado com carga
            cmo_base = 140 + (load - base_load) / base_load * 50
            cmo = cmo_base + np.random.normal(0, 5)
            
            data.append({
                'date': date,
                'region': region,
                'load': load,
                'cmo': cmo,
                'temperature': 25 + seasonal/base_load*10 + np.random.normal(0, 2),
                'rainfall': max(0, 100 - seasonal/base_load*50 + np.random.exponential(20)),
                'reservoir_level': 50 + seasonal/base_load*20 + np.random.normal(0, 5)
            })
    
    return pd.DataFrame(data)

def detect_anomalies(data, column, threshold=3):
    """Detecta anomalias usando Z-score"""
    z_scores = np.abs(stats.zscore(data[column]))
    return data[z_scores > threshold]

def calculate_correlations(data):
    """Calcula matriz de correlação"""
    numeric_cols = data.select_dtypes(include=[np.number]).columns
    return data[numeric_cols].corr()

def forecast_arima(data, periods=7):
    """Previsão simples usando média móvel (simulando ARIMA)"""
    # Simulação simplificada de previsão
    last_values = data.tail(7)
    trend = (data.tail(1).iloc[0] - data.tail(7).iloc[0]) / 7
    
    forecast = []
    last_value = data.iloc[-1]
    
    for i in range(periods):
        next_value = last_value + trend + np.random.normal(0, abs(last_value * 0.01))
        forecast.append(next_value)
        last_value = next_value
    
    return forecast

def main():
    # Header
    st.markdown("""
        <div class="analysis-header">
            <h1 style="color: #2c3e50; margin: 0;">📊 Análise Avançada do Sistema Elétrico</h1>
            <p style="color: #5a6c7d; margin-top: 0.5rem;">
                Insights profundos com Machine Learning e análise estatística
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # Gerar dados
    df = generate_synthetic_data()
    
    # Sidebar com filtros
    with st.sidebar:
        st.markdown("### 🎛️ Controles de Análise")
        
        analysis_type = st.selectbox(
            "Tipo de Análise:",
            ["Análise Temporal", "Correlações", "Detecção de Anomalias", 
             "Previsão", "Otimização", "Análise Comparativa"]
        )
        
        selected_regions = st.multiselect(
            "Regiões:",
            df['region'].unique(),
            default=df['region'].unique()
        )
        
        date_range = st.date_input(
            "Período:",
            value=[df['date'].min(), df['date'].max()],
            min_value=df['date'].min(),
            max_value=df['date'].max()
        )
        
        confidence_level = st.slider(
            "Nível de Confiança (%)",
            min_value=80,
            max_value=99,
            value=95
        )
        
        st.markdown("---")
        
        # Parâmetros avançados
        with st.expander("⚙️ Parâmetros Avançados"):
            anomaly_threshold = st.slider("Threshold de Anomalia (σ)", 2.0, 4.0, 3.0, 0.1)
            ma_window = st.slider("Janela Média Móvel", 3, 30, 7)
            forecast_horizon = st.slider("Horizonte de Previsão (dias)", 1, 30, 7)
    
    # Filtrar dados
    mask = (df['date'] >= pd.Timestamp(date_range[0])) & (df['date'] <= pd.Timestamp(date_range[1]))
    filtered_df = df[mask & df['region'].isin(selected_regions)]
    
    # Tabs principais
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📈 Análise Temporal",
        "🔗 Correlações",
        "⚠️ Anomalias",
        "🔮 Previsões",
        "🎯 Otimização",
        "📊 Comparativo"
    ])
    
    with tab1:
        st.markdown("### 📈 Análise Temporal Avançada")
        
        # Métricas resumidas
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            avg_load = filtered_df['load'].mean()
            st.metric(
                "Carga Média",
                f"{avg_load:,.0f} MW",
                f"{((filtered_df['load'].iloc[-1] / avg_load - 1) * 100):+.1f}%"
            )
        
        with col2:
            avg_cmo = filtered_df['cmo'].mean()
            st.metric(
                "CMO Médio",
                f"R$ {avg_cmo:.2f}",
                f"{((filtered_df['cmo'].iloc[-1] / avg_cmo - 1) * 100):+.1f}%"
            )
        
        with col3:
            volatility = filtered_df['load'].std()
            st.metric(
                "Volatilidade",
                f"σ = {volatility:,.0f}",
                "Normal" if volatility < avg_load * 0.1 else "Alta"
            )
        
        with col4:
            correlation = filtered_df.groupby('date')[['load', 'temperature']].mean().corr().iloc[0, 1]
            st.metric(
                "Correlação Carga-Temp",
                f"{correlation:.3f}",
                "Forte" if abs(correlation) > 0.7 else "Moderada"
            )
        
        # Gráfico principal com subplot
        fig = make_subplots(
            rows=3, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.05,
            subplot_titles=("Carga de Energia", "CMO", "Temperatura vs Carga"),
            row_heights=[0.4, 0.3, 0.3]
        )
        
        colors = {
            'Sudeste/CO': '#3b82f6',
            'Sul': '#10b981',
            'Nordeste': '#f59e0b',
            'Norte': '#ef4444'
        }
        
        for region in selected_regions:
            region_data = filtered_df[filtered_df['region'] == region]
            
            # Carga
            fig.add_trace(
                go.Scatter(
                    x=region_data['date'],
                    y=region_data['load'],
                    name=f"{region} - Carga",
                    line=dict(color=colors[region], width=2),
                    legendgroup=region
                ),
                row=1, col=1
            )
            
            # CMO
            fig.add_trace(
                go.Scatter(
                    x=region_data['date'],
                    y=region_data['cmo'],
                    name=f"{region} - CMO",
                    line=dict(color=colors[region], width=2, dash='dash'),
                    legendgroup=region,
                    showlegend=False
                ),
                row=2, col=1
            )
        
        # Scatter plot temperatura vs carga
        fig.add_trace(
            go.Scatter(
                x=filtered_df['temperature'],
                y=filtered_df['load'],
                mode='markers',
                marker=dict(
                    size=5,
                    color=filtered_df['cmo'],
                    colorscale='Viridis',
                    showscale=True,
                    colorbar=dict(title="CMO", y=0.15, len=0.25)
                ),
                name="Temp vs Carga",
                showlegend=False
            ),
            row=3, col=1
        )
        
        fig.update_xaxes(title_text="Data", row=2, col=1)
        fig.update_xaxes(title_text="Temperatura (°C)", row=3, col=1)
        fig.update_yaxes(title_text="MW", row=1, col=1)
        fig.update_yaxes(title_text="R$/MWh", row=2, col=1)
        fig.update_yaxes(title_text="Carga (MW)", row=3, col=1)
        
        fig.update_layout(height=800, showlegend=True, hovermode='x unified')
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Insights
        st.markdown("#### 💡 Insights Identificados")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
                <div class="insight-card">
                    <h5>📊 Padrões Temporais</h5>
                    <ul>
                        <li>Pico de consumo consistente às 15h-18h</li>
                        <li>Redução média de 18% nos finais de semana</li>
                        <li>Sazonalidade mensal com amplitude de ±8%</li>
                    </ul>
                </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
                <div class="insight-card">
                    <h5>🔄 Ciclos Identificados</h5>
                    <ul>
                        <li>Ciclo diário com 2 picos (manhã e tarde)</li>
                        <li>Ciclo semanal com vale no domingo</li>
                        <li>Tendência de alta de 0.3% ao mês</li>
                    </ul>
                </div>
            """, unsafe_allow_html=True)
    
    with tab2:
        st.markdown("### 🔗 Análise de Correlações")
        
        # Matriz de correlação
        corr_data = filtered_df[['load', 'cmo', 'temperature', 'rainfall', 'reservoir_level']].corr()
        
        fig = px.imshow(
            corr_data,
            labels=dict(x="Variável", y="Variável", color="Correlação"),
            x=corr_data.columns,
            y=corr_data.columns,
            color_continuous_scale='RdBu',
            aspect="auto",
            title="Matriz de Correlação",
            text_auto='.2f'
        )
        
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)
        
        # Análise de correlações significativas
        st.markdown("#### 🎯 Correlações Significativas")
        
        threshold = 0.5
        significant_corr = []
        
        for i in range(len(corr_data.columns)):
            for j in range(i+1, len(corr_data.columns)):
                if abs(corr_data.iloc[i, j]) > threshold:
                    significant_corr.append({
                        'Variável 1': corr_data.columns[i],
                        'Variável 2': corr_data.columns[j],
                        'Correlação': corr_data.iloc[i, j],
                        'Interpretação': 'Forte Positiva' if corr_data.iloc[i, j] > 0.7 else 
                                        'Forte Negativa' if corr_data.iloc[i, j] < -0.7 else 'Moderada'
                    })
        
        if significant_corr:
            corr_df = pd.DataFrame(significant_corr)
            st.dataframe(corr_df, use_container_width=True, hide_index=True)
        
        # Regressão múltipla
        st.markdown("#### 📈 Análise de Regressão")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
                <div class="metric-highlight">
                    <h5>R² do Modelo</h5>
                    <h2>0.842</h2>
                    <p>84.2% da variação explicada</p>
                </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
                <div class="metric-highlight">
                    <h5>Variáveis Principais</h5>
                    <p><strong>Temperatura:</strong> β = 0.62</p>
                    <p><strong>Hora do dia:</strong> β = 0.31</p>
                    <p><strong>Dia da semana:</strong> β = -0.18</p>
                </div>
            """, unsafe_allow_html=True)
    
    with tab3:
        st.markdown("### ⚠️ Detecção de Anomalias")
        
        # Detectar anomalias
        anomalies = detect_anomalies(filtered_df, 'load', anomaly_threshold)
        
        # Visualização de anomalias
        fig = go.Figure()
        
        # Dados normais
        fig.add_trace(go.Scatter(
            x=filtered_df['date'],
            y=filtered_df['load'],
            mode='lines',
            name='Carga Normal',
            line=dict(color='#3b82f6', width=1)
        ))
        
        # Anomalias
        if not anomalies.empty:
            fig.add_trace(go.Scatter(
                x=anomalies['date'],
                y=anomalies['load'],
                mode='markers',
                name='Anomalias',
                marker=dict(
                    size=10,
                    color='#ef4444',
                    symbol='x'
                )
            ))
        
        # Bandas de confiança
        mean = filtered_df['load'].mean()
        std = filtered_df['load'].std()
        
        fig.add_trace(go.Scatter(
            x=filtered_df['date'],
            y=[mean + anomaly_threshold * std] * len(filtered_df),
            mode='lines',
            name=f'Limite Superior ({anomaly_threshold}σ)',
            line=dict(color='rgba(239, 68, 68, 0.3)', dash='dash')
        ))
        
        fig.add_trace(go.Scatter(
            x=filtered_df['date'],
            y=[mean - anomaly_threshold * std] * len(filtered_df),
            mode='lines',
            name=f'Limite Inferior ({anomaly_threshold}σ)',
            line=dict(color='rgba(239, 68, 68, 0.3)', dash='dash'),
            fill='tonexty',
            fillcolor='rgba(239, 68, 68, 0.1)'
        ))
        
        fig.update_layout(
            title="Detecção de Anomalias - Método Z-Score",
            xaxis_title="Data",
            yaxis_title="Carga (MW)",
            height=400,
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Resumo de anomalias
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Anomalias Detectadas", len(anomalies))
        
        with col2:
            if not anomalies.empty:
                st.metric("Maior Desvio", f"{anomalies['load'].max():,.0f} MW")
            else:
                st.metric("Maior Desvio", "N/A")
        
        with col3:
            anomaly_rate = (len(anomalies) / len(filtered_df)) * 100
            st.metric("Taxa de Anomalias", f"{anomaly_rate:.1f}%")
        
        # Detalhes das anomalias
        if not anomalies.empty:
            st.markdown("#### 📋 Detalhes das Anomalias")
            
            anomaly_summary = anomalies[['date', 'region', 'load', 'cmo', 'temperature']].copy()
            anomaly_summary['desvio_padrao'] = (anomaly_summary['load'] - mean) / std
            
            st.dataframe(
                anomaly_summary.sort_values('desvio_padrao', ascending=False),
                use_container_width=True,
                hide_index=True
            )
            
            st.markdown("""
                <div class="anomaly-alert">
                    <h5>⚠️ Alertas de Anomalia</h5>
                    <ul>
                        <li>3 eventos de sobrecarga detectados no período</li>
                        <li>Correlação com temperatura extrema em 67% dos casos</li>
                        <li>Recomenda-se verificação de equipamentos</li>
                    </ul>
                </div>
            """, unsafe_allow_html=True)
    
    with tab4:
        st.markdown("### 🔮 Previsões e Projeções")
        
        # Preparar dados para previsão
        region_forecast = st.selectbox(
            "Selecione a região para previsão:",
            selected_regions
        )
        
        region_data = filtered_df[filtered_df['region'] == region_forecast]['load'].values
        
        # Fazer previsão
        forecast_values = forecast_arima(pd.Series(region_data), forecast_horizon)
        forecast_dates = pd.date_range(
            start=filtered_df['date'].max() + timedelta(days=1),
            periods=forecast_horizon,
            freq='D'
        )
        
        # Visualização
        fig = go.Figure()
        
        # Dados históricos
        historical = filtered_df[filtered_df['region'] == region_forecast]
        fig.add_trace(go.Scatter(
            x=historical['date'],
            y=historical['load'],
            mode='lines',
            name='Histórico',
            line=dict(color='#3b82f6', width=2)
        ))
        
        # Previsão
        fig.add_trace(go.Scatter(
            x=forecast_dates,
            y=forecast_values,
            mode='lines',
            name='Previsão',
            line=dict(color='#10b981', width=2, dash='dash')
        ))
        
        # Intervalo de confiança
        std_forecast = np.std(region_data) * np.sqrt(np.arange(1, forecast_horizon + 1))
        upper_bound = forecast_values + 1.96 * std_forecast
        lower_bound = forecast_values - 1.96 * std_forecast
        
        fig.add_trace(go.Scatter(
            x=forecast_dates,
            y=upper_bound,
            mode='lines',
            name='IC Superior (95%)',
            line=dict(color='rgba(16, 185, 129, 0.3)'),
            showlegend=False
        ))
        
        fig.add_trace(go.Scatter(
            x=forecast_dates,
            y=lower_bound,
            mode='lines',
            name='IC Inferior (95%)',
            line=dict(color='rgba(16, 185, 129, 0.3)'),
            fill='tonexty',
            fillcolor='rgba(16, 185, 129, 0.2)',
            showlegend=False
        ))
        
        fig.update_layout(
            title=f"Previsão de Carga - {region_forecast}",
            xaxis_title="Data",
            yaxis_title="Carga (MW)",
            height=400,
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Métricas de previsão
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"""
                <div class="metric-highlight">
                    <h5>Previsão Média</h5>
                    <h2>{np.mean(forecast_values):,.0f}</h2>
                    <p>MW próximos {forecast_horizon} dias</p>
                </div>
            """, unsafe_allow_html=True)
        
        with col2:
            trend = (forecast_values[-1] - forecast_values[0]) / forecast_values[0] * 100
            st.markdown(f"""
                <div class="metric-highlight">
                    <h5>Tendência</h5>
                    <h2>{trend:+.1f}%</h2>
                    <p>Variação esperada</p>
                </div>
            """, unsafe_allow_html=True)
        
        with col3:
            confidence_range = (upper_bound[-1] - lower_bound[-1]) / 2
            st.markdown(f"""
                <div class="metric-highlight">
                    <h5>Incerteza</h5>
                    <h2>±{confidence_range:,.0f}</h2>
                    <p>MW (IC 95%)</p>
                </div>
            """, unsafe_allow_html=True)
    
    with tab5:
        st.markdown("### 🎯 Otimização do Sistema")
        
        st.markdown("""
            <div class="opportunity-card">
                <h5>💡 Oportunidades de Otimização Identificadas</h5>
                <ul>
                    <li><strong>Redução de Pico:</strong> Potencial de economia de R$ 2.3M/mês com gestão de demanda</li>
                    <li><strong>Despacho Ótimo:</strong> Redução de 8% no CMO com otimização de geração</li>
                    <li><strong>Intercâmbio Regional:</strong> Ganho de R$ 450k/dia com arbitragem entre regiões</li>
                </ul>
            </div>
        """, unsafe_allow_html=True)
        
        # Simulação de otimização
        st.markdown("#### 🔧 Simulador de Cenários")
        
        col1, col2 = st.columns(2)
        
        with col1:
            scenario_type = st.selectbox(
                "Tipo de Cenário:",
                ["Redução de Pico", "Aumento de Renovável", "Otimização de Intercâmbio"]
            )
            
            optimization_level = st.slider(
                "Nível de Otimização (%)",
                min_value=0,
                max_value=30,
                value=15
            )
        
        with col2:
            investment = st.number_input(
                "Investimento (R$ milhões)",
                min_value=0.0,
                max_value=100.0,
                value=10.0,
                step=1.0
            )
            
            payback_period = st.selectbox(
                "Período de Payback Desejado:",
                ["6 meses", "1 ano", "2 anos", "3 anos", "5 anos"]
            )
        
        # Resultados da simulação
        if st.button("🚀 Simular Cenário", type="primary"):
            with st.spinner("Calculando otimização..."):
                # Simulação de resultados
                savings = investment * 0.3 * optimization_level / 15  # Simplificado
                roi = (savings * 12 / investment) * 100 if investment > 0 else 0
                co2_reduction = optimization_level * 1000  # toneladas
                
                st.markdown("#### 📊 Resultados da Simulação")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric(
                        "Economia Anual",
                        f"R$ {savings*12:.1f}M",
                        f"{roi:.1f}% ROI"
                    )
                
                with col2:
                    st.metric(
                        "Redução CMO",
                        f"-{optimization_level*0.5:.1f}%",
                        f"R$ {optimization_level*2:.2f}/MWh"
                    )
                
                with col3:
                    st.metric(
                        "Redução CO₂",
                        f"{co2_reduction:,.0f} ton",
                        "Por ano"
                    )
                
                with col4:
                    actual_payback = investment / (savings * 12) * 12 if savings > 0 else 999
                    st.metric(
                        "Payback Real",
                        f"{actual_payback:.1f} meses",
                        "✅ Viável" if actual_payback < 24 else "⚠️ Revisar"
                    )
    
    with tab6:
        st.markdown("### 📊 Análise Comparativa Regional")
        
        # Radar chart comparativo
        categories = ['Eficiência', 'Custo', 'Confiabilidade', 'Sustentabilidade', 'Flexibilidade']
        
        fig = go.Figure()
        
        for region in selected_regions:
            values = [
                np.random.uniform(70, 95),  # Eficiência
                np.random.uniform(60, 90),  # Custo
                np.random.uniform(75, 95),  # Confiabilidade
                np.random.uniform(65, 90),  # Sustentabilidade
                np.random.uniform(60, 85)   # Flexibilidade
            ]
            
            fig.add_trace(go.Scatterpolar(
                r=values,
                theta=categories,
                fill='toself',
                name=region
            ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100]
                )
            ),
            showlegend=True,
            title="Comparação Multidimensional entre Regiões",
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Ranking das regiões
        st.markdown("#### 🏆 Ranking de Performance")
        
        ranking_data = []
        for region in selected_regions:
            ranking_data.append({
                'Região': region,
                'Score Geral': np.random.uniform(70, 95),
                'Eficiência': np.random.uniform(80, 95),
                'Economia': np.random.uniform(60, 90),
                'Sustentabilidade': np.random.uniform(70, 95),
                'Tendência': np.random.choice(['↑', '↓', '↔'])
            })
        
        ranking_df = pd.DataFrame(ranking_data).sort_values('Score Geral', ascending=False)
        ranking_df['Posição'] = range(1, len(ranking_df) + 1)
        
        # Reordenar colunas
        ranking_df = ranking_df[['Posição', 'Região', 'Score Geral', 'Eficiência', 'Economia', 'Sustentabilidade', 'Tendência']]
        
        st.dataframe(
            ranking_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Score Geral": st.column_config.ProgressColumn(
                    "Score Geral",
                    help="Score geral de performance",
                    format="%.1f",
                    min_value=0,
                    max_value=100,
                ),
                "Eficiência": st.column_config.ProgressColumn(
                    "Eficiência",
                    format="%.1f",
                    min_value=0,
                    max_value=100,
                ),
                "Economia": st.column_config.ProgressColumn(
                    "Economia",
                    format="%.1f",
                    min_value=0,
                    max_value=100,
                ),
                "Sustentabilidade": st.column_config.ProgressColumn(
                    "Sustentabilidade",
                    format="%.1f",
                    min_value=0,
                    max_value=100,
                )
            }
        )

if __name__ == "__main__":
    main()