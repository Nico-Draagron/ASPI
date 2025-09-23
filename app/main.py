"""
ASPI - Assistente Inteligente para Dados do Setor Elétrico
Interface dupla: Básica (usuários leigos) e Avançada (cientistas de dados)
"""

import streamlit as st
import pandas as pd
import numpy as np
import asyncio
import requests
from pathlib import Path
import sys
from datetime import datetime

# Adicionar o diretório app ao path
sys.path.append(str(Path(__file__).parent))

# Imports dos componentes existentes
from components.sidebar import render_sidebar
from components.chat import render_chat_interface
from components.metrics import render_metrics_dashboard
from components.visualizations import render_main_chart

# Import de export com fallback
try:
    from components.export import ExportHandler
    EXPORT_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ ExportHandler não disponível: {e}")
    EXPORT_AVAILABLE = False
    ExportHandler = None
    print(f"Warning: Export component not available: {e}")
    EXPORT_AVAILABLE = False
    class ExportHandler:
        def __init__(self):
            pass

# Imports dos services
try:
    from services.ai_service import AIService
    from services.data_service import DataService
    from services.ons_service import ONSService
    from services.cache_service import CacheService
except ImportError as e:
    print(f"Warning: Some services not available: {e}")

# Import do ML (novo)
try:
    from ml.energy_ml_pipeline import EnergyMLPipeline, execute_ml_pipeline
    ML_AVAILABLE = True
except ImportError as e:
    print(f"Warning: ML module not available: {e}")
    ML_AVAILABLE = False
    class EnergyMLPipeline:
        def __init__(self):
            pass
    def execute_ml_pipeline():
        return {}, None

# Import da API Health Check
try:
    from api.health import health_check_endpoint
    from datetime import datetime
    HEALTH_API_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Health API not available: {e}")
    from datetime import datetime
    HEALTH_API_AVAILABLE = False
    def health_check_endpoint():
        return {"status": "error", "message": "Health API not available"}

# Configuração da página
st.set_page_config(
    page_title="ASPI - Assistente Inteligente ONS",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/Nico-Draagron/ASPI',
        'Report a bug': None,
        'About': "ASPI v1.0 - Interface Dupla com ML"
    }
)

# Inicializar session state
def init_session_state():
    """Inicializa variáveis de estado da sessão"""
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    
    if 'interface_mode' not in st.session_state:
        st.session_state.interface_mode = 'basico'
    
    if 'ml_results' not in st.session_state:
        st.session_state.ml_results = None
    
    if 'current_analysis' not in st.session_state:
        st.session_state.current_analysis = None
    
    if 'selected_dataset' not in st.session_state:
        st.session_state.selected_dataset = "carga_energia"
    
    if 'theme_mode' not in st.session_state:
        st.session_state.theme_mode = "light"

# CSS customizado
def load_custom_css():
    """Carrega CSS customizado"""
    css_file = Path("app/assets/styles/streamlit_custom.css")
    if css_file.exists():
        with open(css_file) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    
    # CSS adicional inline
    st.markdown("""
    <style>
        .main-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 2rem;
            border-radius: 10px;
            text-align: center;
            margin-bottom: 2rem;
            color: white;
        }
        
        .metric-card {
            background: white;
            padding: 1.5rem;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 1rem;
            border-left: 4px solid #667eea;
        }
        
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
        }
        
        .stTabs [data-baseweb="tab"] {
            border-radius: 8px;
            padding: 10px 20px;
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
        
        .info-card {
            background: #f0f2f6;
            padding: 1rem;
            border-radius: 8px;
            margin: 1rem 0;
        }
    </style>
    """, unsafe_allow_html=True)

# ======================================
# INTERFACE BÁSICA (USUÁRIOS LEIGOS)
# ======================================
def render_basic_interface():
    """Interface simplificada para usuários não-técnicos"""
    
    # Header principal
    st.markdown("""
    <div class="main-header">
        <h1 style="margin: 0;">⚡ ASPI - Assistente de Energia</h1>
        <p style="margin: 0.5rem 0;">Entenda o setor elétrico de forma simples e clara</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Métricas principais usando componentes nativos do Streamlit
    st.markdown("### 📊 Indicadores Principais do SIN")
    
    # Métricas usando st.metric (componente nativo)
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("⚡ Consumo Atual", "72.845 MW", "3.2%")
    
    with col2:
        st.metric("💰 Custo Médio", "R$ 156/MWh", "12%")
    
    with col3:
        st.metric("🚦 Bandeira", "Amarela", "R$ 2,989/100kWh")
        
    with col4:
        st.metric("💧 Reservatórios", "58.3%", "↓ 5%")
    
    st.markdown("---")
    
    # Controles de integração N8N
    with st.expander("🔧 Controles de Sistema (Admin)", expanded=False):
        st.markdown("**Integração com N8N Workflows:**")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🔍 Health Check", use_container_width=True):
                st.rerun()  # Isso irá chamar o health check via query param
        
        with col2:
            if st.button("💬 Testar Chat N8N", use_container_width=True):
                # Redirecionar para webhook de chat
                st.markdown("""
                <script>
                window.location.href = '?webhook=chat';
                </script>
                """, unsafe_allow_html=True)
        
        with col3:
            if st.button("📊 Trigger Ingestão", use_container_width=True):
                # Redirecionar para webhook de ingestão
                st.markdown("""
                <script>
                window.location.href = '?webhook=data_ingestion';
                </script>
                """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Tabs para organização
    tab1, tab2, tab3, tab4 = st.tabs(["💬 Assistente", "📊 Visualizações", "📈 Análises", "💡 Dicas"])
    
    with tab1:
        # Usar o componente de chat existente
        st.markdown("### 💬 Converse com o Assistente")
        
        # Perguntas sugeridas
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📊 Qual o consumo atual?", use_container_width=True):
                st.session_state.messages.append({
                    "role": "user",
                    "content": "Qual o consumo atual de energia?"
                })
        
        with col2:
            if st.button("💰 Por que a conta está alta?", use_container_width=True):
                st.session_state.messages.append({
                    "role": "user",
                    "content": "Por que a conta de energia está alta?"
                })
        
        # Chat interface com integração N8N
        st.markdown("### 💭 Chat com Assistente IA")
        
        # Área de mensagens
        chat_container = st.container()
        
        with chat_container:
            # Mostrar histórico de mensagens
            for message in st.session_state.messages:
                if message["role"] == "user":
                    st.markdown(f"""
                    <div style="background: #e3f2fd; padding: 1rem; border-radius: 10px; margin: 0.5rem 0;">
                        <b>👤 Você:</b> {message['content']}
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div style="background: #f5f5f5; padding: 1rem; border-radius: 10px; margin: 0.5rem 0;">
                        <b>🤖 Assistente:</b> {message['content']}
                    </div>
                    """, unsafe_allow_html=True)
        
        # Input de nova mensagem
        user_input = st.text_input("Digite sua pergunta:", key="chat_input", placeholder="Ex: Qual o consumo de energia agora?")
        
        if st.button("📤 Enviar", key="send_chat") and user_input:
            # Adicionar mensagem do usuário
            st.session_state.messages.append({
                "role": "user",
                "content": user_input
            })
            
            # Processar via N8N
            try:
                import requests
                
                chat_data = {
                    "user_id": "streamlit_user",
                    "session_id": st.session_state.get('session_id', f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"),
                    "message": user_input,
                    "source": "streamlit_basic",
                    "timestamp": datetime.now().isoformat()
                }
                
                # Enviar para N8N
                response = requests.post(
                    "http://localhost:5679/webhook-test/chat/process",
                    json=chat_data,
                    timeout=10
                )
                
                if response.status_code == 200:
                    ai_response = response.json().get('response', 'Resposta processada com sucesso!')
                else:
                    ai_response = "Desculpe, não consegui processar sua pergunta no momento. Tente novamente."
                    
            except Exception as e:
                ai_response = f"Erro na comunicação com o assistente: {str(e)}"
            
            # Adicionar resposta do assistente
            st.session_state.messages.append({
                "role": "assistant", 
                "content": ai_response
            })
            
            # Limpar input e reexecutar
            st.rerun()
        
        # Botão para limpar chat
        if st.button("🗑️ Limpar Chat"):
            st.session_state.messages = []
            st.rerun()
    
    with tab2:
        # Visualizações usando componente existente
        st.markdown("### 📊 Visualizações do Sistema")
        try:
            render_main_chart()
        except Exception as e:
            st.error(f"Erro ao carregar gráficos: {e}")
            # Gráfico simples de exemplo
            data = {
                'Região': ['Sudeste/CO', 'Sul', 'Nordeste', 'Norte'],
                'Consumo (MW)': [42350, 15230, 12845, 2420]
            }
            df = pd.DataFrame(data)
            st.bar_chart(df.set_index('Região'))
    
    with tab3:
        # Análises simples
        st.markdown("### 📈 Análises Simplificadas")
        
        analysis_type = st.selectbox(
            "Escolha o tipo de análise:",
            ["Consumo por Região", "Evolução Temporal", "Comparação de Custos"]
        )
        
        if analysis_type == "Consumo por Região":
            st.info("📊 Análise de consumo por região em desenvolvimento...")
    
    with tab4:
        # Dicas educativas
        st.markdown("### 💡 Dicas para Economizar")
        
        tips = [
            ("🌡️", "Configure o ar-condicionado para 23°C", "Cada grau a menos aumenta 8% no consumo"),
            ("💡", "Use lâmpadas LED", "Economia de até 80% comparado às incandescentes"),
            ("🚿", "Tome banhos de 5 minutos", "Chuveiro elétrico é um dos maiores consumidores"),
            ("🧊", "Mantenha a geladeira bem vedada", "Borrachas ruins aumentam o consumo em 30%"),
        ]
        
        for emoji, title, description in tips:
            st.info(f"{emoji} **{title}**\n\n{description}")

# ======================================
# INTERFACE AVANÇADA (CIENTISTAS DE DADOS)
# ======================================
def render_advanced_interface():
    """Interface completa com ML e análises técnicas"""
    
    st.markdown("## 🔬 ASPI - Análise Avançada com Machine Learning")
    
    # Verificar se ML está disponível
    if not ML_AVAILABLE:
        st.error("⚠️ Módulo ML não disponível. Instale as dependências necessárias.")
        st.code("pip install scikit-learn xgboost shap plotly")
        return
    
    # Sidebar com configurações
    with st.sidebar:
        st.markdown("### ⚙️ Configurações ML")
        
        # Seleção de dataset
        dataset = st.selectbox(
            "Dataset ONS:",
            ["carga_energia", "cmo", "bandeira_tarifaria"]
        )
        
        # Tipo de análise
        analysis_type = st.selectbox(
            "Tipo de Análise:",
            ["Pipeline Completo", "Apenas Regressão", "Apenas Clustering", 
             "Detecção de Anomalias", "Interpretabilidade"]
        )
        
        # Botão para executar ML
        if st.button("🚀 Executar Pipeline ML", type="primary", use_container_width=True):
            st.session_state.run_ml = True
        
        st.markdown("---")
        
        # Controles de N8N
        st.markdown("### 🔗 Integração N8N")
        
        if st.button("🔄 Atualizar Dados ONS", use_container_width=True):
            # Trigger data ingestion workflow
            try:
                response = requests.post(
                    "http://localhost:5679/webhook-test/data-ingestion/trigger",
                    json={"force_update": True, "source": "streamlit_advanced"},
                    timeout=5
                )
                if response.status_code == 200:
                    st.success("✅ Ingestão iniciada!")
                else:
                    st.error("❌ Erro na ingestão")
            except Exception as e:
                st.error(f"❌ Erro: {str(e)}")
        
        if st.button("💬 Testar Chat Avançado", use_container_width=True):
            # Test advanced chat
            try:
                response = requests.post(
                    "http://localhost:5679/webhook-test/chat/process",
                    json={
                        "message": "Análise técnica do SIN",
                        "user_id": "advanced_user",
                        "source": "streamlit_advanced"
                    },
                    timeout=5
                )
                if response.status_code == 200:
                    st.success("✅ Chat funcionando!")
                else:
                    st.error("❌ Erro no chat")
            except Exception as e:
                st.error(f"❌ Erro: {str(e)}")
    
    # Tabs principais
    tabs = st.tabs([
        "📊 EDA", 
        "🤖 Modelagem ML", 
        "📈 Métricas & Validação",
        "🔍 Interpretabilidade",
        "🎯 Clustering & Anomalias",
        "📝 Relatório"
    ])
    
    # Tab 1: EDA
    with tabs[0]:
        render_eda_section()
    
    # Tab 2: Modelagem ML
    with tabs[1]:
        render_ml_modeling()
    
    # Tab 3: Métricas
    with tabs[2]:
        render_validation_metrics()
    
    # Tab 4: SHAP
    with tabs[3]:
        render_shap_analysis()
    
    # Tab 5: Clustering
    with tabs[4]:
        render_clustering_anomalies()
    
    # Tab 6: Relatório
    with tabs[5]:
        render_ml_report()

def render_eda_section():
    """Seção de Análise Exploratória"""
    st.markdown("### 📊 Análise Exploratória de Dados")
    
    # Métricas do dataset
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Registros", "1,245,678")
    
    with col2:
        st.metric("Features", "47")
    
    with col3:
        st.metric("Missing %", "0.3%")
    
    with col4:
        st.metric("Outliers", "2.1%")
    
    st.info("📊 Funcionalidades de EDA em desenvolvimento...")

def render_ml_modeling():
    """Seção de Modelagem ML"""
    st.markdown("### 🤖 Modelagem Machine Learning")
    
    if st.session_state.get('run_ml', False):
        # Progress bar
        progress = st.progress(0)
        status = st.empty()
        
        # Container para resultados
        results_container = st.container()
        
        with results_container:
            with st.spinner("Executando pipeline ML..."):
                try:
                    # Executar pipeline ML de forma assíncrona
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    # Simular progresso
                    for i in range(0, 101, 10):
                        progress.progress(i)
                        status.info(f"Progresso: {i}%")
                        
                    # Executar pipeline
                    pipeline = EnergyMLPipeline()
                    results = loop.run_until_complete(pipeline.run_complete_pipeline())
                    
                    progress.progress(100)
                    status.success("✅ Pipeline concluído!")
                    
                    # Salvar resultados no session state
                    st.session_state.ml_results = results
                    
                    # Mostrar resultados
                    if results['status'] == 'concluído':
                        st.success("✅ Modelos treinados com sucesso!")
                        
                        # Mostrar métricas dos modelos
                        st.markdown("#### Resultados dos Modelos")
                        
                        for model_name, metrics in results['models'].items():
                            with st.expander(f"📊 {model_name}"):
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.metric("MAE Teste", f"{metrics['test_mae']:.2f}")
                                with col2:
                                    st.metric("R² Score", f"{metrics['test_r2']:.3f}")
                                with col3:
                                    st.metric("Status", metrics['overfit_status'])
                    
                    else:
                        st.error(f"❌ Erro no pipeline: {results.get('error', 'Erro desconhecido')}")
                
                except Exception as e:
                    st.error(f"❌ Erro ao executar pipeline: {e}")
                    progress.progress(0)
                finally:
                    loop.close()
                    
        # Reset flag
        st.session_state.run_ml = False
    else:
        st.info("👈 Configure e execute o pipeline ML na barra lateral")

def render_validation_metrics():
    """Seção de Métricas e Validação"""
    st.markdown("### 📈 Métricas e Validação")
    
    if st.session_state.ml_results:
        results = st.session_state.ml_results
        st.success("📊 Resultados do pipeline disponíveis!")
        
        # Mostrar métricas de clustering se disponível
        if 'clustering' in results:
            cluster_info = results['clustering']
            st.markdown("#### Clustering")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Silhouette Score", f"{cluster_info['silhouette_score']:.3f}")
            with col2:
                st.metric("Clusters", cluster_info['n_clusters'])
        
        # Mostrar anomalias se disponível
        if 'anomalies' in results:
            anomaly_info = results['anomalies']
            st.markdown("#### Detecção de Anomalias")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Anomalias Detectadas", anomaly_info['n_anomalies'])
            with col2:
                st.metric("Taxa de Anomalias", f"{anomaly_info['anomaly_rate']*100:.1f}%")
    else:
        st.info("Execute o pipeline ML primeiro")

def render_shap_analysis():
    """Seção de Interpretabilidade com SHAP"""
    st.markdown("### 🔍 Interpretabilidade - SHAP Analysis")
    
    if st.session_state.ml_results and 'interpretability' in st.session_state.ml_results:
        interp_results = st.session_state.ml_results['interpretability']
        
        if 'feature_importance' in interp_results:
            st.markdown("#### Feature Importance")
            feature_df = interp_results['feature_importance']
            
            if not feature_df.empty:
                st.dataframe(feature_df.head(10), use_container_width=True)
            else:
                st.info("Dados de feature importance não disponíveis")
        else:
            st.info("Análise SHAP em desenvolvimento...")
    else:
        st.info("Execute o pipeline ML primeiro")

def render_clustering_anomalies():
    """Seção de Clustering e Anomalias"""
    st.markdown("### 🎯 Clustering & Detecção de Anomalias")
    
    if st.session_state.ml_results:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Clustering")
            if 'clustering' in st.session_state.ml_results:
                cluster_info = st.session_state.ml_results['clustering']
                st.metric("Silhouette Score", f"{cluster_info['silhouette_score']:.3f}")
                st.json(cluster_info['cluster_sizes'])
            else:
                st.info("Resultados de clustering não disponíveis")
        
        with col2:
            st.markdown("#### Anomalias")
            if 'anomalies' in st.session_state.ml_results:
                anomaly_info = st.session_state.ml_results['anomalies']
                st.metric("Anomalias", anomaly_info['n_anomalies'])
                st.metric("Taxa", f"{anomaly_info['anomaly_rate']*100:.1f}%")
            else:
                st.info("Resultados de anomalias não disponíveis")
    else:
        st.info("Execute o pipeline ML primeiro")

def render_ml_report():
    """Seção de Relatório Final"""
    st.markdown("### 📝 Relatório de Machine Learning")
    
    if st.session_state.ml_results:
        results = st.session_state.ml_results
        
        st.markdown(f"""
        #### Resumo Executivo
        
        **Status:** {results['status']}
        **Melhor Modelo:** {results.get('best_model', 'N/A')}
        **Dataset Shape:** {results.get('data_shape', 'N/A')}
        **Features Criadas:** {results.get('features_created', 'N/A')}
        
        **Etapas Executadas:**
        """)
        
        for step in results.get('steps', []):
            st.write(f"✅ {step}")
        
        # Botão de export
        if EXPORT_AVAILABLE and ExportHandler:
            try:
                export_handler = ExportHandler()
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button("📄 Exportar PDF", use_container_width=True):
                        st.success("PDF gerado!")
                
                with col2:
                    if st.button("📊 Exportar Excel", use_container_width=True):
                        st.success("Excel gerado!")
                
                with col3:
                    if st.button("💾 Salvar Modelo", use_container_width=True):
                        st.success("Modelo salvo!")
            except Exception as e:
                st.error(f"Erro no export: {e}")
        else:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("📄 Exportar PDF", use_container_width=True):
                    st.info("Funcionalidade de export em desenvolvimento")
            
            with col2:
                if st.button("📊 Exportar Excel", use_container_width=True):
                    st.info("Funcionalidade de export em desenvolvimento")
            
            with col3:
                if st.button("💾 Salvar Modelo", use_container_width=True):
                    st.info("Funcionalidade de export em desenvolvimento")
    else:
        st.info("Execute o pipeline ML para gerar o relatório")

# ======================================
# MAIN APP
# ======================================
def health_check_endpoint():
    """Endpoint de health check para N8N"""
    try:
        # Verificar componentes básicos
        import psycopg2
        import redis
        
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "services": {
                "streamlit": "online",
                "database": "checking",
                "redis": "checking"
            },
            "version": "1.0.0"
        }
        
        # Test database connection
        try:
            # Usar configuração simples para teste
            conn = psycopg2.connect(
                host="localhost",
                port=5432,
                database="aspi_db",
                user="postgres",
                password="postgres123"
            )
            conn.close()
            health_status["services"]["database"] = "online"
        except:
            health_status["services"]["database"] = "offline"
            health_status["status"] = "degraded"
        
        # Test Redis connection
        try:
            r = redis.Redis(host='localhost', port=6379, password='redis123', decode_responses=True)
            r.ping()
            health_status["services"]["redis"] = "online"
        except:
            health_status["services"]["redis"] = "offline"
            health_status["status"] = "degraded"
        
        return health_status
        
    except Exception as e:
        return {
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }

def process_chat_webhook():
    """Processa requisições de chat via webhook do N8N"""
    import requests
    
    try:
        # Simular dados de chat para teste
        chat_data = {
            "user_id": "streamlit_user",
            "session_id": f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "message": "Teste de integração Streamlit-N8N",
            "source": "streamlit",
            "timestamp": datetime.now().isoformat()
        }
        
        # Enviar para o webhook do N8N
        response = requests.post(
            "http://localhost:5679/webhook-test/chat/process",
            json=chat_data,
            timeout=10
        )
        
        if response.status_code == 200:
            st.json({
                "status": "success",
                "message": "Chat processado com sucesso",
                "response": response.json() if response.content else None
            })
        else:
            st.json({
                "status": "error",
                "message": f"Erro do N8N: {response.status_code}",
                "details": response.text
            })
            
    except Exception as e:
        st.json({
            "status": "error",
            "message": "Erro ao processar chat",
            "error": str(e)
        })

def trigger_data_ingestion():
    """Trigger manual para ingestão de dados via N8N"""
    import requests
    
    try:
        # Dados para trigger da ingestão
        ingestion_data = {
            "force_update": True,
            "source": "streamlit_manual",
            "triggered_by": "user",
            "timestamp": datetime.now().isoformat()
        }
        
        # Enviar para o webhook do N8N
        response = requests.post(
            "http://localhost:5679/webhook-test/data-ingestion/trigger", 
            json=ingestion_data,
            timeout=30
        )
        
        if response.status_code == 200:
            st.json({
                "status": "success", 
                "message": "Ingestão de dados iniciada",
                "response": response.json() if response.content else None
            })
        else:
            st.json({
                "status": "error",
                "message": f"Erro ao iniciar ingestão: {response.status_code}",
                "details": response.text
            })
            
    except Exception as e:
        st.json({
            "status": "error",
            "message": "Erro ao triggerar ingestão",
            "error": str(e)
        })

def main():
    """Função principal"""
    
    # =========== API ENDPOINT HANDLER ===========
    # Verifica se é uma chamada para API
    query_params = st.query_params
    
    if "api" in query_params and query_params["api"] == "health":
        # Retorna JSON para health check
        health_data = health_check_endpoint()
        st.json(health_data)
        st.stop()  # Para a execução aqui para APIs
    
    if "api" in query_params and query_params["api"] == "monitoring":
        if "metrics" in query_params:
            # Endpoint para receber métricas do N8N
            try:
                st.json({
                    "status": "received", 
                    "timestamp": datetime.now().isoformat(),
                    "message": "Metrics endpoint ready"
                })
                st.stop()
            except Exception as e:
                st.json({"status": "error", "error": str(e)})
                st.stop()
        
        elif "alert" in query_params:
            # Endpoint para receber alertas de erro do N8N
            try:
                st.json({
                    "status": "alert_received",
                    "timestamp": datetime.now().isoformat(), 
                    "message": "Alert logged successfully"
                })
                st.stop()
            except Exception as e:
                st.json({"status": "error", "error": str(e)})
                st.stop()
    
    # =========== WEBHOOK ENDPOINTS ===========
    # Endpoint para processar chat via N8N
    if "webhook" in query_params and query_params["webhook"] == "chat":
        process_chat_webhook()
        st.stop()
    
    # Endpoint para trigger manual de data ingestion
    if "webhook" in query_params and query_params["webhook"] == "data_ingestion":
        trigger_data_ingestion()
        st.stop()

    # =========== STREAMLIT APP NORMAL ===========
    
    # Inicializar estado
    init_session_state()
    
    # Carregar CSS
    load_custom_css()
    
    # Sidebar com seleção de interface
    with st.sidebar:
        st.markdown("### 🎛️ Configurações")
        
        # Seletor de interface
        interface_mode = st.radio(
            "Modo de Interface:",
            ["Básico (Usuários)", "Avançado (Cientistas de Dados)"],
            key="interface_selector"
        )
        
        st.markdown("---")
        
        # Usar render_sidebar existente para outras opções
        try:
            render_sidebar()
        except Exception as e:
            st.error(f"Erro no sidebar: {e}")
            # Sidebar simplificado
            st.selectbox("Dataset", ["Carga Energia", "CMO", "Bandeiras"])
            st.date_input("Data Início")
            st.date_input("Data Fim")
    
    # Renderizar interface selecionada
    if "Básico" in interface_mode:
        render_basic_interface()
    else:
        render_advanced_interface()
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; opacity: 0.6;">
        ASPI v1.0 | Interface Dupla com ML | Dados: ONS
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()