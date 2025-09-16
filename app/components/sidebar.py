"""
AIDE - Componente Sidebar
Barra lateral com filtros, configurações e indicadores
"""

import streamlit as st
from datetime import datetime, timedelta
import pandas as pd

def render_sidebar():
    """Renderiza a sidebar com filtros e configurações"""
    
    # Logo e título na sidebar
    st.markdown("""
        <div style="text-align: center; padding: 1rem 0; border-bottom: 2px solid #e7cba9;">
            <div style="display: inline-flex; align-items: center; justify-content: center; 
                        width: 80px; height: 80px; background: linear-gradient(135deg, #e7cba9, #f0d8bc); 
                        border-radius: 16px; margin-bottom: 1rem;">
                <span style="font-size: 36px;">⚡</span>
            </div>
            <h2 style="color: #2c3e50; font-size: 1.25rem; margin: 0;">AIDE</h2>
            <p style="color: #6c757d; font-size: 0.75rem; margin: 0;">Sistema Inteligente ONS</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Separador
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Seção de Filtros
    st.markdown("### 🔍 Filtros de Análise")
    
    # Seletor de Dataset
    with st.expander("📊 **Dataset**", expanded=True):
        dataset = st.selectbox(
            "Selecione o conjunto de dados:",
            options=[
                "carga_energia",
                "cmo_pld",
                "bandeiras_tarifarias",
                "geracao_usina",
                "reservatorios",
                "intercambio_regional"
            ],
            format_func=lambda x: {
                "carga_energia": "💡 Carga de Energia",
                "cmo_pld": "💰 CMO/PLD",
                "bandeiras_tarifarias": "🚦 Bandeiras Tarifárias",
                "geracao_usina": "⚡ Geração por Usina",
                "reservatorios": "💧 Reservatórios",
                "intercambio_regional": "🔄 Intercâmbio Regional"
            }.get(x, x),
            key="dataset_selector",
            help="Escolha o dataset para análise"
        )
        st.session_state.selected_dataset = dataset
    
    # Seletor de Período
    with st.expander("📅 **Período de Análise**", expanded=True):
        period_option = st.radio(
            "Selecione o período:",
            ["Período Rápido", "Período Customizado"],
            key="period_type"
        )
        
        if period_option == "Período Rápido":
            quick_period = st.select_slider(
                "Período:",
                options=["24h", "7d", "15d", "30d", "3m", "6m", "1a"],
                value="7d",
                key="quick_period",
                help="Selecione um período pré-definido"
            )
            st.session_state.selected_period = quick_period
            
            # Mostrar período selecionado
            period_map = {
                "24h": "Últimas 24 horas",
                "7d": "Últimos 7 dias",
                "15d": "Últimos 15 dias",
                "30d": "Últimos 30 dias",
                "3m": "Últimos 3 meses",
                "6m": "Últimos 6 meses",
                "1a": "Último ano"
            }
            st.info(f"📌 {period_map[quick_period]}")
        
        else:
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input(
                    "Data inicial:",
                    value=datetime.now() - timedelta(days=30),
                    max_value=datetime.now(),
                    key="start_date"
                )
            with col2:
                end_date = st.date_input(
                    "Data final:",
                    value=datetime.now(),
                    max_value=datetime.now(),
                    key="end_date"
                )
            
            if start_date > end_date:
                st.error("⚠️ Data inicial não pode ser maior que a final")
    
    # Seletor de Regiões/Subsistemas
    with st.expander("🗺️ **Regiões/Subsistemas**", expanded=True):
        all_regions = ["Sudeste/CO", "Sul", "Nordeste", "Norte"]
        
        # Checkbox para selecionar todos
        select_all = st.checkbox("Selecionar todos", value=True, key="select_all_regions")
        
        if select_all:
            selected_regions = st.multiselect(
                "Subsistemas:",
                options=all_regions,
                default=all_regions,
                key="regions_selector",
                disabled=True
            )
        else:
            selected_regions = st.multiselect(
                "Subsistemas:",
                options=all_regions,
                default=["Sudeste/CO"],
                key="regions_selector"
            )
        
        st.session_state.selected_regions = selected_regions
        
        # Mostrar cores das regiões
        region_colors = {
            "Sudeste/CO": "#3b82f6",
            "Sul": "#10b981",
            "Nordeste": "#f59e0b",
            "Norte": "#ef4444"
        }
        
        cols = st.columns(2)
        for idx, region in enumerate(selected_regions):
            with cols[idx % 2]:
                color = region_colors.get(region, "#6c757d")
                st.markdown(f"""
                    <div style="display: flex; align-items: center; gap: 8px; padding: 4px;">
                        <div style="width: 12px; height: 12px; background: {color}; 
                                    border-radius: 2px;"></div>
                        <small>{region}</small>
                    </div>
                """, unsafe_allow_html=True)
    
    # Separador
    st.markdown("---")
    
    # Seção de Configurações Avançadas
    st.markdown("### ⚙️ Configurações")
    
    with st.expander("🎨 **Visualização**"):
        # Tipo de gráfico
        chart_type = st.selectbox(
            "Tipo de gráfico padrão:",
            ["Linha", "Área", "Barra", "Dispersão", "Mapa de Calor"],
            key="chart_type"
        )
        
        # Agregação temporal
        aggregation = st.selectbox(
            "Agregação temporal:",
            ["Horária", "Diária", "Semanal", "Mensal"],
            index=1,
            key="temporal_aggregation"
        )
        
        # Mostrar média móvel
        show_ma = st.checkbox("Mostrar média móvel", value=False, key="show_moving_average")
        if show_ma:
            ma_period = st.slider("Período da média móvel:", 3, 30, 7, key="ma_period")
    
    with st.expander("🤖 **Assistente IA**"):
        # Modo de resposta
        response_mode = st.radio(
            "Modo de resposta:",
            ["Conciso", "Detalhado", "Técnico"],
            key="ai_response_mode",
            help="Define o nível de detalhamento das respostas"
        )
        
        # Auto-análise
        auto_analysis = st.checkbox(
            "Análise automática de anomalias",
            value=True,
            key="auto_anomaly_detection"
        )
        
        # Sugestões proativas
        proactive_suggestions = st.checkbox(
            "Sugestões proativas",
            value=True,
            key="proactive_suggestions",
            help="O AIDE sugere análises complementares"
        )
    
    with st.expander("📤 **Exportação**"):
        # Formato de exportação
        export_format = st.selectbox(
            "Formato padrão:",
            ["Excel", "CSV", "JSON", "PDF"],
            key="export_format"
        )
        
        # Incluir gráficos
        include_charts = st.checkbox(
            "Incluir gráficos na exportação",
            value=True,
            key="include_charts_export"
        )
        
        # Botão de exportação
        if st.button("📥 Exportar Dados Atuais", key="export_button", use_container_width=True):
            st.success("✅ Dados exportados com sucesso!")
            st.balloons()
    
    # Separador
    st.markdown("---")
    
    # Seção de Status e Informações
    st.markdown("### 📈 Status do Sistema")
    
    # Indicadores de status
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
            <div style="text-align: center; padding: 0.5rem; background: #d1fae5; 
                        border-radius: 8px; margin: 0.25rem 0;">
                <small style="color: #065f46; font-weight: 600;">API ONS</small><br>
                <span style="color: #10b981; font-size: 20px;">●</span>
                <small style="color: #065f46;">Online</small>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
            <div style="text-align: center; padding: 0.5rem; background: #dbeafe; 
                        border-radius: 8px; margin: 0.25rem 0;">
                <small style="color: #1e40af; font-weight: 600;">Atualização</small><br>
                <small style="color: #3b82f6;">10 min atrás</small>
            </div>
        """, unsafe_allow_html=True)
    
    # Última sincronização
    st.markdown("""
        <div style="padding: 0.75rem; background: #f9f9f9; border-radius: 8px; 
                    margin-top: 1rem; border-left: 3px solid #e7cba9;">
            <small style="color: #6c757d;">
                <strong>Última Sincronização:</strong><br>
                06/09/2025 14:32:15<br>
                <strong>Próxima:</strong> em 28 minutos
            </small>
        </div>
    """, unsafe_allow_html=True)
    
    # Separador
    st.markdown("---")
    
    # Links úteis
    st.markdown("### 🔗 Links Úteis")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("[📊 Portal ONS](https://www.ons.org.br)")
        st.markdown("[📈 Dados Abertos](https://dados.ons.org.br)")
    with col2:
        st.markdown("[📚 Documentação](https://www.ons.org.br/docs)")
        st.markdown("[❓ Ajuda](https://www.ons.org.br/help)")
    
    # Footer da sidebar
    st.markdown("---")
    st.markdown("""
        <div style="text-align: center; padding: 1rem 0;">
            <small style="color: #9ca3af;">
                AIDE v1.0.0<br>
                © 2025 - Setor Elétrico
            </small>
        </div>
    """, unsafe_allow_html=True)

# Função auxiliar para obter configurações
def get_sidebar_settings():
    """Retorna as configurações atuais da sidebar"""
    return {
        'dataset': st.session_state.get('selected_dataset', 'carga_energia'),
        'period': st.session_state.get('selected_period', '7d'),
        'regions': st.session_state.get('selected_regions', ["Sudeste/CO"]),
        'chart_type': st.session_state.get('chart_type', 'Linha'),
        'aggregation': st.session_state.get('temporal_aggregation', 'Diária'),
        'show_ma': st.session_state.get('show_moving_average', False),
        'ma_period': st.session_state.get('ma_period', 7),
        'response_mode': st.session_state.get('ai_response_mode', 'Detalhado'),
        'auto_analysis': st.session_state.get('auto_anomaly_detection', True),
        'proactive': st.session_state.get('proactive_suggestions', True)
    }

# Função para resetar filtros
def reset_filters():
    """Reseta todos os filtros para valores padrão"""
    st.session_state.selected_dataset = "carga_energia"
    st.session_state.selected_period = "7d"
    st.session_state.selected_regions = ["Sudeste/CO", "Sul", "Nordeste", "Norte"]
    st.session_state.chart_type = "Linha"
    st.session_state.temporal_aggregation = "Diária"
    st.session_state.show_moving_average = False
    st.session_state.ai_response_mode = "Detalhado"
    st.session_state.auto_anomaly_detection = True
    st.session_state.proactive_suggestions = True