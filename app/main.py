"""
AIDE - Assistente Inteligente para Dados do Setor Elétrico
Aplicativo Principal Streamlit
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import numpy as np

# Importar componentes (serão criados posteriormente)
from components.sidebar import render_sidebar
from components.chat import render_chat_interface
from components.metrics import render_metrics_dashboard
from components.visualizations import render_main_chart

# Configuração da página
st.set_page_config(
    page_title="AIDE - Assistente Inteligente ONS",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://www.ons.org.br',
        'Report a bug': None,
        'About': "AIDE - Assistente Inteligente para Dados do Setor Elétrico v1.0"
    }
)

# Carregar CSS customizado
def load_css():
    """Carrega o CSS customizado"""
    with open('app/assets/styles/streamlit_custom.css') as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Inicializar estado da sessão
def init_session_state():
    """Inicializa variáveis de estado da sessão"""
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    
    if 'current_analysis' not in st.session_state:
        st.session_state.current_analysis = None
    
    if 'selected_dataset' not in st.session_state:
        st.session_state.selected_dataset = "carga_energia"
    
    if 'selected_period' not in st.session_state:
        st.session_state.selected_period = "7d"
    
    if 'selected_regions' not in st.session_state:
        st.session_state.selected_regions = ["Sudeste/CO", "Sul", "Nordeste", "Norte"]
    
    if 'theme_mode' not in st.session_state:
        st.session_state.theme_mode = "light"

def render_header():
    """Renderiza o cabeçalho principal da aplicação"""
    header_col1, header_col2, header_col3 = st.columns([1, 4, 1])
    
    with header_col1:
        # Placeholder para logo
        st.markdown("""
            <div style="display: flex; align-items: center; justify-content: center; 
                        width: 100px; height: 100px; background: linear-gradient(135deg, #e7cba9, #f0d8bc); 
                        border-radius: 20px; margin: auto;">
                <span style="font-size: 48px;">⚡</span>
            </div>
        """, unsafe_allow_html=True)
    
    with header_col2:
        st.markdown("""
            <div class="main-header">
                <h1 class="header-title">
                    AIDE - Assistente Inteligente para Dados do Setor Elétrico
                </h1>
                <p class="header-subtitle">
                    Análise em tempo real dos dados do ONS com inteligência artificial
                </p>
            </div>
        """, unsafe_allow_html=True)
    
    with header_col3:
        # Status de conexão
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("""
                <div style="text-align: center; padding: 10px;">
                    <div style="width: 12px; height: 12px; background: #10b981; 
                                border-radius: 50%; margin: auto; animation: pulse 2s infinite;">
                    </div>
                    <small style="color: #6c757d;">Online</small>
                </div>
            """, unsafe_allow_html=True)
        with col2:
            if st.button("🌙", key="theme_toggle", help="Alternar tema"):
                st.session_state.theme_mode = "dark" if st.session_state.theme_mode == "light" else "light"
                st.rerun()

def render_quick_insights():
    """Renderiza cards com insights rápidos"""
    st.markdown("### 📊 Insights Rápidos do Sistema")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
            <div class="metric-card">
                <div class="metric-label">Carga Total SIN</div>
                <div class="metric-value">72.845 MW</div>
                <div class="metric-delta positive">↑ 3.2% vs ontem</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
            <div class="metric-card">
                <div class="metric-label">CMO Médio SE/CO</div>
                <div class="metric-value">R$ 142,30</div>
                <div class="metric-delta negative">↑ 8.5% vs semana</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
            <div class="metric-card">
                <div class="metric-label">Bandeira Tarifária</div>
                <div class="metric-value">Verde</div>
                <div class="metric-delta positive">Sem adicional</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
            <div class="metric-card">
                <div class="metric-label">Reservatórios SE/CO</div>
                <div class="metric-value">58.3%</div>
                <div class="metric-delta positive">↑ 2.1% vs mês</div>
            </div>
        """, unsafe_allow_html=True)

def render_main_dashboard():
    """Renderiza o dashboard principal com gráficos"""
    tab1, tab2, tab3, tab4 = st.tabs(["📈 Carga de Energia", "💰 CMO/PLD", "🚦 Bandeiras", "📊 Análise Comparativa"])
    
    with tab1:
        col1, col2 = st.columns([3, 1])
        with col1:
            # Gráfico de carga de energia
            dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
            
            fig = go.Figure()
            for region in st.session_state.selected_regions:
                values = np.random.normal(20000, 2000, 30) + np.random.randint(-1000, 1000, 30)
                fig.add_trace(go.Scatter(
                    x=dates,
                    y=values,
                    mode='lines',
                    name=region,
                    line=dict(width=2.5)
                ))
            
            fig.update_layout(
                title="Evolução da Carga de Energia por Subsistema (MWmed)",
                xaxis_title="Data",
                yaxis_title="Carga (MWmed)",
                height=400,
                hovermode='x unified',
                plot_bgcolor='white',
                paper_bgcolor='white',
                font=dict(family="Inter, sans-serif"),
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                )
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("#### 📊 Resumo do Período")
            st.info("""
                **Período:** Últimos 30 dias  
                **Maior carga:** SE/CO - 45.230 MW  
                **Menor carga:** Norte - 8.450 MW  
                **Média SIN:** 72.845 MW
            """)
            
            st.markdown("#### 🎯 Destaques")
            st.success("✅ Carga estável em todos os subsistemas")
            st.warning("⚠️ Pico esperado para próxima semana")
    
    with tab2:
        # CMO/PLD Dashboard
        col1, col2 = st.columns([2, 1])
        with col1:
            # Gráfico de barras CMO por patamar
            patamares = ['Leve', 'Médio', 'Pesado']
            subsistemas = ['SE/CO', 'Sul', 'NE', 'Norte']
            
            data = []
            for subsistema in subsistemas:
                for patamar in patamares:
                    data.append({
                        'Subsistema': subsistema,
                        'Patamar': patamar,
                        'CMO': np.random.uniform(100, 200)
                    })
            
            df = pd.DataFrame(data)
            fig = px.bar(df, x='Subsistema', y='CMO', color='Patamar',
                        title='CMO por Subsistema e Patamar de Carga (R$/MWh)',
                        color_discrete_map={'Leve': '#cfe4f9', 'Médio': '#e7cba9', 'Pesado': '#ffa500'})
            
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("#### 💡 Análise CMO")
            st.metric("CMO Médio Nacional", "R$ 156,80", "+12,30")
            st.metric("Spread Máximo", "R$ 45,20", "-5,10")
            
            with st.expander("ℹ️ Sobre o CMO"):
                st.write("""
                O **Custo Marginal de Operação (CMO)** representa o custo 
                de produzir 1 MWh adicional de energia no sistema.
                """)
    
    with tab3:
        # Histórico de Bandeiras
        st.markdown("### 🚦 Histórico de Bandeiras Tarifárias")
        
        # Timeline de bandeiras
        months = pd.date_range(end=datetime.now(), periods=12, freq='M')
        bandeiras = ['Verde', 'Verde', 'Amarela', 'Verde', 'Verde', 'Vermelha P1', 
                    'Vermelha P2', 'Amarela', 'Verde', 'Verde', 'Verde', 'Verde']
        valores = [0, 0, 2.989, 0, 0, 6.500, 9.795, 2.989, 0, 0, 0, 0]
        
        fig = go.Figure()
        colors = {'Verde': '#10b981', 'Amarela': '#fbbf24', 'Vermelha P1': '#f87171', 'Vermelha P2': '#dc2626'}
        
        for i, (month, bandeira, valor) in enumerate(zip(months, bandeiras, valores)):
            color = colors.get(bandeira.split()[0], '#gray')
            fig.add_trace(go.Bar(
                x=[month],
                y=[valor if valor > 0 else 0.5],
                name=bandeira,
                marker_color=color,
                text=f"{bandeira}<br>R$ {valor:.2f}",
                textposition='outside',
                showlegend=i == bandeiras.index(bandeira)
            ))
        
        fig.update_layout(
            title="Evolução das Bandeiras Tarifárias - Últimos 12 Meses",
            xaxis_title="Mês",
            yaxis_title="Valor Adicional (R$/100 kWh)",
            height=400,
            barmode='group'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with tab4:
        # Análise Comparativa
        st.markdown("### 📊 Análise Comparativa Regional")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Mapa de calor correlação
            st.markdown("#### Correlação entre Subsistemas")
            
            corr_data = np.random.rand(4, 4)
            np.fill_diagonal(corr_data, 1)
            corr_data = (corr_data + corr_data.T) / 2
            
            fig = px.imshow(corr_data,
                           labels=dict(x="Subsistema", y="Subsistema", color="Correlação"),
                           x=['SE/CO', 'Sul', 'NE', 'Norte'],
                           y=['SE/CO', 'Sul', 'NE', 'Norte'],
                           color_continuous_scale='RdBu',
                           aspect="auto")
            
            fig.update_layout(height=350)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Ranking de eficiência
            st.markdown("#### 🏆 Ranking de Eficiência Energética")
            
            ranking_data = pd.DataFrame({
                'Subsistema': ['SE/CO', 'Sul', 'Nordeste', 'Norte'],
                'Eficiência': [92, 88, 85, 79],
                'Tendência': ['↑', '↔', '↑', '↓']
            })
            
            for idx, row in ranking_data.iterrows():
                color = '#10b981' if row['Tendência'] == '↑' else '#fbbf24' if row['Tendência'] == '↔' else '#ef4444'
                st.markdown(f"""
                    <div style="display: flex; align-items: center; padding: 10px; 
                                background: linear-gradient(90deg, {color}20 0%, transparent 100%); 
                                border-radius: 8px; margin: 5px 0;">
                        <span style="font-size: 24px; margin-right: 15px;">#{idx+1}</span>
                        <div style="flex: 1;">
                            <strong>{row['Subsistema']}</strong><br>
                            <small>Eficiência: {row['Eficiência']}%</small>
                        </div>
                        <span style="font-size: 20px; color: {color};">{row['Tendência']}</span>
                    </div>
                """, unsafe_allow_html=True)

def render_chat_section():
    """Renderiza a seção de chat com o assistente"""
    st.markdown("### 💬 Converse com o AIDE")
    
    # Container do chat
    chat_container = st.container()
    
    with chat_container:
        # Histórico de mensagens
        for message in st.session_state.messages:
            if message["role"] == "user":
                st.markdown(f"""
                    <div class="user-message">
                        <strong>👤 Você:</strong><br>
                        {message["content"]}
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                    <div class="assistant-message">
                        <strong>⚡ AIDE:</strong><br>
                        {message["content"]}
                    </div>
                """, unsafe_allow_html=True)
    
    # Input do usuário
    col1, col2 = st.columns([5, 1])
    with col1:
        user_input = st.text_input(
            "Digite sua pergunta sobre o setor elétrico:",
            placeholder="Ex: Qual foi a carga média do Sudeste na última semana?",
            key="user_input",
            label_visibility="collapsed"
        )
    
    with col2:
        send_button = st.button("Enviar 📤", type="primary", use_container_width=True)
    
    if send_button and user_input:
        # Adicionar mensagem do usuário
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        # Simular resposta do assistente
        response = f"""Analisando sua pergunta sobre: "{user_input}"
        
Com base nos dados do ONS, posso informar que:
- A carga média do Sudeste/CO na última semana foi de 42.350 MWmed
- Houve um crescimento de 3,2% em relação à semana anterior
- O pico de consumo ocorreu na quinta-feira às 15h com 48.230 MW

Gostaria de ver um gráfico detalhado dessa análise?"""
        
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.rerun()

def main():
    """Função principal do aplicativo"""
    # Inicializar estado
    init_session_state()
    
    # Carregar CSS (comentado pois o arquivo ainda não existe)
    # load_css()
    
    # Aplicar CSS inline
    st.markdown("""
        <style>
        /* Inserir o CSS aqui temporariamente */
        .stApp {
            background-color: #FFFFFF;
        }
        
        .metric-card {
            background: #FFFFFF;
            border: 1px solid #e9ecef;
            border-radius: 12px;
            padding: 1.25rem;
            margin: 0.5rem;
            transition: all 0.3s ease;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        }
        
        .metric-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(231, 203, 169, 0.15);
            border-color: #e7cba9;
        }
        
        .metric-label {
            color: #6c757d;
            font-size: 0.875rem;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 0.5rem;
        }
        
        .metric-value {
            color: #2c3e50;
            font-size: 2rem;
            font-weight: 700;
            margin: 0.25rem 0;
        }
        
        .metric-delta {
            font-size: 0.875rem;
            font-weight: 500;
            padding: 0.25rem 0.5rem;
            border-radius: 6px;
            display: inline-block;
        }
        
        .metric-delta.positive {
            color: #10b981;
            background: #d1fae5;
        }
        
        .metric-delta.negative {
            color: #ef4444;
            background: #fee2e2;
        }
        
        .user-message {
            background: linear-gradient(135deg, #cfe4f9 0%, #e8f4fd 100%);
            padding: 1rem 1.25rem;
            border-radius: 12px 12px 4px 12px;
            margin: 0.75rem 0;
            border-left: 3px solid #3b82f6;
        }
        
        .assistant-message {
            background: linear-gradient(135deg, #f9f7f4 0%, #ffffff 100%);
            padding: 1rem 1.25rem;
            border-radius: 12px 12px 12px 4px;
            margin: 0.75rem 0;
            border-left: 3px solid #e7cba9;
        }
        
        .main-header {
            background: linear-gradient(135deg, #e7cba9 0%, #f4e4d4 100%);
            padding: 1.5rem 2rem;
            border-radius: 16px;
            margin-bottom: 2rem;
            box-shadow: 0 4px 6px rgba(231, 203, 169, 0.1);
        }
        
        .header-title {
            color: #2c3e50;
            font-size: 2rem;
            font-weight: 700;
            margin: 0;
        }
        
        .header-subtitle {
            color: #5a6c7d;
            font-size: 1rem;
            margin-top: 0.5rem;
            font-weight: 400;
        }
        
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Renderizar sidebar
    with st.sidebar:
        render_sidebar()
    
    # Renderizar conteúdo principal
    render_header()
    
    # Quick insights
    render_quick_insights()
    
    # Separador
    st.markdown("---")
    
    # Dashboard principal
    render_main_dashboard()
    
    # Separador
    st.markdown("---")
    
    # Seção de chat
    render_chat_section()
    
    # Footer
    st.markdown("---")
    st.markdown("""
        <div style="text-align: center; color: #6c757d; padding: 2rem 0;">
            <p>AIDE - Assistente Inteligente para Dados do Setor Elétrico v1.0</p>
            <p style="font-size: 0.875rem;">Dados fornecidos pelo ONS - Operador Nacional do Sistema Elétrico</p>
        </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()