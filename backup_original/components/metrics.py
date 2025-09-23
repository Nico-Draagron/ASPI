"""
AIDE - Componente de Métricas
Cards de KPIs e indicadores do sistema elétrico
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import plotly.graph_objects as go

class MetricsDisplay:
    """Classe para gerenciar exibição de métricas"""
    
    def __init__(self):
        self.metric_colors = {
            'positive': '#10b981',
            'negative': '#ef4444',
            'neutral': '#6c757d',
            'warning': '#f59e0b'
        }
        
        self.subsystem_colors = {
            'Sudeste/CO': '#3b82f6',
            'Sul': '#10b981',
            'Nordeste': '#f59e0b',
            'Norte': '#ef4444'
        }
    
    def calculate_delta(self, current: float, previous: float) -> Tuple[float, str]:
        """Calcula a variação percentual e determina a direção"""
        if previous == 0:
            return 0, 'neutral'
        
        delta = ((current - previous) / previous) * 100
        
        if delta > 0:
            direction = 'positive'
        elif delta < 0:
            direction = 'negative'
        else:
            direction = 'neutral'
        
        return delta, direction
    
    def format_value(self, value: float, unit: str = '', precision: int = 1) -> str:
        """Formata valores com unidades apropriadas"""
        if value >= 1e9:
            return f"{value/1e9:.{precision}f}G{unit}"
        elif value >= 1e6:
            return f"{value/1e6:.{precision}f}M{unit}"
        elif value >= 1e3:
            return f"{value/1e3:.{precision}f}k{unit}"
        else:
            return f"{value:.{precision}f}{unit}"
    
    def render_metric_card(self, title: str, value: str, delta: Optional[str] = None, 
                          delta_color: str = 'neutral', icon: str = '📊',
                          subtitle: Optional[str] = None) -> str:
        """Renderiza um card de métrica individual"""
        
        delta_html = ''
        if delta:
            bg_color = {
                'positive': '#d1fae5',
                'negative': '#fee2e2',
                'neutral': '#f3f4f6',
                'warning': '#fed7aa'
            }.get(delta_color, '#f3f4f6')
            
            text_color = self.metric_colors.get(delta_color, '#6c757d')
            
            delta_html = f"""
                <div class="metric-delta" style="font-size: 0.875rem; font-weight: 500; 
                            padding: 0.25rem 0.5rem; border-radius: 6px; display: inline-block;
                            background: {bg_color}; color: {text_color};">
                    {delta}
                </div>
            """
        
        subtitle_html = ''
        if subtitle:
            subtitle_html = f'<div style="color: #9ca3af; font-size: 0.75rem; margin-top: 0.25rem;">{subtitle}</div>'
        
        return f"""
            <div class="metric-card" style="background: #FFFFFF; border: 1px solid #e9ecef; 
                        border-radius: 12px; padding: 1.25rem; margin: 0.5rem; 
                        transition: all 0.3s ease; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);">
                <div style="display: flex; align-items: start; justify-content: space-between;">
                    <div style="flex: 1;">
                        <div class="metric-label" style="color: #6c757d; font-size: 0.875rem; 
                                    font-weight: 500; text-transform: uppercase; letter-spacing: 0.5px; 
                                    margin-bottom: 0.5rem;">
                            {title}
                        </div>
                        <div class="metric-value" style="color: #2c3e50; font-size: 2rem; 
                                    font-weight: 700; margin: 0.25rem 0;">
                            {value}
                        </div>
                        {delta_html}
                        {subtitle_html}
                    </div>
                    <div style="font-size: 2rem; opacity: 0.8;">{icon}</div>
                </div>
            </div>
        """
    
    def render_mini_chart(self, data: List[float], title: str, color: str = '#e7cba9') -> go.Figure:
        """Cria um mini gráfico sparkline"""
        fig = go.Figure()
        
        x = list(range(len(data)))
        
        # Linha principal
        fig.add_trace(go.Scatter(
            x=x,
            y=data,
            mode='lines',
            line=dict(color=color, width=2),
            fill='tozeroy',
            fillcolor=f'rgba({int(color[1:3], 16)}, {int(color[3:5], 16)}, {int(color[5:7], 16)}, 0.1)',
            showlegend=False,
            hovertemplate='%{y:.1f}<extra></extra>'
        ))
        
        # Ponto final
        fig.add_trace(go.Scatter(
            x=[x[-1]],
            y=[data[-1]],
            mode='markers',
            marker=dict(size=6, color=color),
            showlegend=False,
            hovertemplate='%{y:.1f}<extra></extra>'
        ))
        
        fig.update_layout(
            height=60,
            margin=dict(l=0, r=0, t=0, b=0),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            hovermode='x'
        )
        
        return fig
    
    def get_system_metrics(self) -> Dict:
        """Obtém métricas do sistema (simulado)"""
        return {
            'carga_total': {
                'value': 72845.3,
                'previous': 70562.1,
                'unit': 'MW',
                'history': np.random.normal(72000, 2000, 24).tolist()
            },
            'cmo_medio': {
                'value': 142.30,
                'previous': 131.15,
                'unit': 'R$/MWh',
                'history': np.random.normal(140, 10, 24).tolist()
            },
            'reservatorios': {
                'value': 58.3,
                'previous': 56.2,
                'unit': '%',
                'history': np.random.normal(58, 2, 24).tolist()
            },
            'geracao_renovavel': {
                'value': 78.5,
                'previous': 75.2,
                'unit': '%',
                'history': np.random.normal(78, 3, 24).tolist()
            }
        }
    
    def get_regional_metrics(self) -> Dict:
        """Obtém métricas regionais (simulado)"""
        return {
            'Sudeste/CO': {
                'carga': 42350,
                'cmo': 142.30,
                'reservatorio': 58.3,
                'intercambio': -1110
            },
            'Sul': {
                'carga': 15230,
                'cmo': 138.45,
                'reservatorio': 72.1,
                'intercambio': -2000
            },
            'Nordeste': {
                'carga': 9845,
                'cmo': 155.20,
                'reservatorio': 45.6,
                'intercambio': 1230
            },
            'Norte': {
                'carga': 5420,
                'cmo': 162.80,
                'reservatorio': 89.2,
                'intercambio': 3890
            }
        }

def render_metrics_dashboard():
    """Renderiza o dashboard completo de métricas"""
    metrics = MetricsDisplay()
    
    st.markdown("### 📊 Indicadores Principais do SIN")
    
    # Obter dados
    system_metrics = metrics.get_system_metrics()
    regional_metrics = metrics.get_regional_metrics()
    
    # Tabs para diferentes visualizações
    tab1, tab2, tab3 = st.tabs(["🎯 Visão Geral", "🗺️ Regional", "📈 Tendências"])
    
    with tab1:
        # Métricas principais
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            carga = system_metrics['carga_total']
            delta, direction = metrics.calculate_delta(carga['value'], carga['previous'])
            
            st.markdown(metrics.render_metric_card(
                title="Carga Total SIN",
                value=f"{carga['value']:.0f} MW",
                delta=f"{'↑' if delta > 0 else '↓'} {abs(delta):.1f}%",
                delta_color=direction,
                icon="⚡",
                subtitle="vs. dia anterior"
            ), unsafe_allow_html=True)
            
            # Mini chart
            fig = metrics.render_mini_chart(carga['history'], "Últimas 24h", "#3b82f6")
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        
        with col2:
            cmo = system_metrics['cmo_medio']
            delta, direction = metrics.calculate_delta(cmo['value'], cmo['previous'])
            
            # Inverter direção para CMO (menor é melhor)
            direction = 'negative' if direction == 'positive' else 'positive' if direction == 'negative' else 'neutral'
            
            st.markdown(metrics.render_metric_card(
                title="CMO Médio Nacional",
                value=f"R$ {cmo['value']:.2f}",
                delta=f"{'↑' if delta > 0 else '↓'} {abs(delta):.1f}%",
                delta_color=direction,
                icon="💰",
                subtitle="R$/MWh"
            ), unsafe_allow_html=True)
            
            fig = metrics.render_mini_chart(cmo['history'], "Últimas 24h", "#e7cba9")
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        
        with col3:
            reserv = system_metrics['reservatorios']
            delta, direction = metrics.calculate_delta(reserv['value'], reserv['previous'])
            
            st.markdown(metrics.render_metric_card(
                title="Reservatórios SE/CO",
                value=f"{reserv['value']:.1f}%",
                delta=f"{'↑' if delta > 0 else '↓'} {abs(delta):.1f} pp",
                delta_color=direction,
                icon="💧",
                subtitle="Energia armazenada"
            ), unsafe_allow_html=True)
            
            fig = metrics.render_mini_chart(reserv['history'], "Últimas 24h", "#10b981")
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        
        with col4:
            renov = system_metrics['geracao_renovavel']
            delta, direction = metrics.calculate_delta(renov['value'], renov['previous'])
            
            st.markdown(metrics.render_metric_card(
                title="Geração Renovável",
                value=f"{renov['value']:.1f}%",
                delta=f"{'↑' if delta > 0 else '↓'} {abs(delta):.1f} pp",
                delta_color=direction,
                icon="🌱",
                subtitle="Do total gerado"
            ), unsafe_allow_html=True)
            
            fig = metrics.render_mini_chart(renov['history'], "Últimas 24h", "#22c55e")
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        
        # Status das bandeiras
        st.markdown("#### 🚦 Status das Bandeiras Tarifárias")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.success("✅ **Bandeira Verde Acionada**")
            st.markdown("Sem cobrança adicional na tarifa")
        
        with col2:
            st.info("📅 **Vigência:** Setembro/2025")
            st.markdown("Válida até 30/09/2025")
        
        with col3:
            st.warning("📊 **Próxima Revisão:** 25/09")
            st.markdown("Probabilidade verde: 75%")
    
    with tab2:
        # Métricas regionais
        st.markdown("#### 🗺️ Indicadores por Subsistema")
        
        for region, data in regional_metrics.items():
            with st.expander(f"**{region}**", expanded=True):
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric(
                        "Carga",
                        f"{data['carga']:,.0f} MW",
                        f"{(data['carga']/72845*100):.1f}% do SIN"
                    )
                
                with col2:
                    st.metric(
                        "CMO",
                        f"R$ {data['cmo']:.2f}",
                        f"{data['cmo']-142.30:+.2f} vs média"
                    )
                
                with col3:
                    st.metric(
                        "Reservatório",
                        f"{data['reservatorio']:.1f}%",
                        "Normal" if data['reservatorio'] > 50 else "Baixo"
                    )
                
                with col4:
                    intercambio_label = "Exportador" if data['intercambio'] > 0 else "Importador"
                    st.metric(
                        "Intercâmbio",
                        f"{abs(data['intercambio']):,.0f} MW",
                        intercambio_label
                    )
    
    with tab3:
        # Análise de tendências
        st.markdown("#### 📈 Análise de Tendências")
        
        # Seletor de métrica
        metric_option = st.selectbox(
            "Selecione a métrica para análise:",
            ["Carga de Energia", "CMO/PLD", "Reservatórios", "Geração Renovável"],
            key="trend_metric"
        )
        
        # Gráfico de tendência
        dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
        
        fig = go.Figure()
        
        # Dados simulados baseados na métrica selecionada
        if metric_option == "Carga de Energia":
            for region in regional_metrics.keys():
                values = np.random.normal(
                    regional_metrics[region]['carga'], 
                    regional_metrics[region]['carga'] * 0.05, 
                    30
                )
                fig.add_trace(go.Scatter(
                    x=dates,
                    y=values,
                    mode='lines+markers',
                    name=region,
                    line=dict(width=2.5)
                ))
            y_title = "Carga (MW)"
        
        elif metric_option == "CMO/PLD":
            for region in regional_metrics.keys():
                values = np.random.normal(
                    regional_metrics[region]['cmo'], 
                    10, 
                    30
                )
                fig.add_trace(go.Scatter(
                    x=dates,
                    y=values,
                    mode='lines+markers',
                    name=region,
                    line=dict(width=2.5)
                ))
            y_title = "CMO (R$/MWh)"
        
        elif metric_option == "Reservatórios":
            for region in regional_metrics.keys():
                values = np.random.normal(
                    regional_metrics[region]['reservatorio'], 
                    2, 
                    30
                )
                fig.add_trace(go.Scatter(
                    x=dates,
                    y=values,
                    mode='lines+markers',
                    name=region,
                    line=dict(width=2.5)
                ))
            y_title = "Nível (%)"
        
        else:  # Geração Renovável
            sources = ['Hidrelétrica', 'Solar', 'Eólica', 'Biomassa']
            for source in sources:
                values = np.random.normal(20, 5, 30)
                fig.add_trace(go.Scatter(
                    x=dates,
                    y=values,
                    mode='lines+markers',
                    name=source,
                    line=dict(width=2.5)
                ))
            y_title = "Geração (%)"
        
        fig.update_layout(
            title=f"Tendência - {metric_option} (30 dias)",
            xaxis_title="Data",
            yaxis_title=y_title,
            height=400,
            hovermode='x unified',
            plot_bgcolor='white',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Insights automáticos
        st.markdown("#### 💡 Insights Automáticos")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.info("""
                **📊 Padrões Identificados:**
                - Pico de consumo às 15h-18h
                - Redução de 15% nos finais de semana
                - Correlação de 0.82 com temperatura
            """)
        
        with col2:
            st.warning("""
                **⚠️ Alertas:**
                - CMO acima da média em 12%
                - Reservatórios NE abaixo de 50%
                - Previsão de alta demanda próxima semana
            """)

# Função auxiliar para obter métricas específicas
def get_metric_value(metric_type: str, region: Optional[str] = None) -> Dict:
    """Obtém valor de uma métrica específica"""
    metrics = MetricsDisplay()
    
    if region:
        regional = metrics.get_regional_metrics()
        if region in regional and metric_type in regional[region]:
            return {
                'value': regional[region][metric_type],
                'unit': {
                    'carga': 'MW',
                    'cmo': 'R$/MWh',
                    'reservatorio': '%',
                    'intercambio': 'MW'
                }.get(metric_type, '')
            }
    else:
        system = metrics.get_system_metrics()
        if metric_type in system:
            return {
                'value': system[metric_type]['value'],
                'unit': system[metric_type]['unit'],
                'history': system[metric_type].get('history', [])
            }
    
    return {'value': 0, 'unit': ''}

# Exportar classes e funções
__all__ = ['MetricsDisplay', 'render_metrics_dashboard', 'get_metric_value']