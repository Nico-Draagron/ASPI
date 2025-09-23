"""
AIDE - Componente de Visualizações
Gráficos interativos e dashboards para análise de dados do setor elétrico
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json

class VisualizationEngine:
    """Motor de visualização para gráficos do AIDE"""
    
    def __init__(self):
        # Paleta de cores principal
        self.colors = {
            'primary': '#e7cba9',
            'secondary': '#cfe4f9',
            'success': '#10b981',
            'warning': '#f59e0b',
            'danger': '#ef4444',
            'info': '#3b82f6',
            'dark': '#2c3e50',
            'light': '#f8f9fa'
        }
        
        # Cores por subsistema
        self.subsystem_colors = {
            'Sudeste/CO': '#3b82f6',
            'Sul': '#10b981',
            'Nordeste': '#f59e0b',
            'Norte': '#ef4444'
        }
        
        # Cores por fonte de energia
        self.source_colors = {
            'Hidrelétrica': '#3b82f6',
            'Solar': '#fbbf24',
            'Eólica': '#10b981',
            'Térmica': '#ef4444',
            'Nuclear': '#8b5cf6',
            'Biomassa': '#84cc16'
        }
        
        # Configuração padrão dos layouts
        self.default_layout = {
            'font': {'family': 'Inter, sans-serif', 'size': 12},
            'plot_bgcolor': 'white',
            'paper_bgcolor': 'white',
            'margin': dict(l=60, r=30, t=60, b=60),
            'hovermode': 'x unified',
            'showlegend': True,
            'legend': dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        }
    
    def create_time_series(self, 
                          data: pd.DataFrame, 
                          title: str,
                          y_label: str,
                          series_column: str = 'region',
                          value_column: str = 'value',
                          show_forecast: bool = False) -> go.Figure:
        """Cria gráfico de série temporal"""
        
        fig = go.Figure()
        
        # Adicionar séries
        for series in data[series_column].unique():
            series_data = data[data[series_column] == series]
            
            color = self.subsystem_colors.get(series, self.colors['primary'])
            
            # Linha principal
            fig.add_trace(go.Scatter(
                x=series_data['date'],
                y=series_data[value_column],
                mode='lines',
                name=series,
                line=dict(color=color, width=2.5),
                hovertemplate=f'<b>{series}</b><br>%{{x}}<br>%{{y:.1f}}<extra></extra>'
            ))
            
            # Se houver previsão
            if show_forecast and 'forecast' in series_data.columns:
                forecast_data = series_data[series_data['forecast'] == True]
                if not forecast_data.empty:
                    fig.add_trace(go.Scatter(
                        x=forecast_data['date'],
                        y=forecast_data[value_column],
                        mode='lines',
                        name=f'{series} (Previsão)',
                        line=dict(color=color, width=2.5, dash='dash'),
                        hovertemplate=f'<b>{series} (Previsão)</b><br>%{{x}}<br>%{{y:.1f}}<extra></extra>'
                    ))
        
        # Adicionar anotações para eventos importantes
        annotations = []
        if 'events' in data.columns:
            events = data[data['events'].notna()]
            for _, event in events.iterrows():
                annotations.append(dict(
                    x=event['date'],
                    y=event[value_column],
                    text=event['events'],
                    showarrow=True,
                    arrowhead=2,
                    arrowsize=1,
                    arrowwidth=2,
                    arrowcolor=self.colors['warning'],
                    ax=0,
                    ay=-40
                ))
        
        # Layout
        fig.update_layout(
            title=title,
            xaxis_title="Data",
            yaxis_title=y_label,
            height=450,
            **self.default_layout,
            annotations=annotations
        )
        
        # Adicionar range selector
        fig.update_xaxes(
            rangeselector=dict(
                buttons=list([
                    dict(count=1, label="1d", step="day", stepmode="backward"),
                    dict(count=7, label="7d", step="day", stepmode="backward"),
                    dict(count=1, label="1m", step="month", stepmode="backward"),
                    dict(count=3, label="3m", step="month", stepmode="backward"),
                    dict(step="all", label="Tudo")
                ]),
                bgcolor=self.colors['secondary'],
                activecolor=self.colors['primary']
            ),
            rangeslider=dict(visible=False),
            type="date"
        )
        
        return fig
    
    def create_heatmap(self,
                      data: pd.DataFrame,
                      title: str,
                      x_label: str = "Hora",
                      y_label: str = "Dia") -> go.Figure:
        """Cria mapa de calor"""
        
        # Preparar dados para o heatmap
        pivot_data = data.pivot(index=y_label.lower(), columns=x_label.lower(), values='value')
        
        fig = go.Figure(data=go.Heatmap(
            z=pivot_data.values,
            x=pivot_data.columns,
            y=pivot_data.index,
            colorscale=[
                [0, self.colors['secondary']],
                [0.5, self.colors['primary']],
                [1, self.colors['danger']]
            ],
            colorbar=dict(
                title="MW",
                titleside="right",
                tickmode="linear",
                tick0=0,
                dtick=1000
            ),
            hovertemplate='%{y}<br>%{x}h<br>%{z:.0f} MW<extra></extra>'
        ))
        
        fig.update_layout(
            title=title,
            xaxis_title=x_label,
            yaxis_title=y_label,
            height=400,
            **self.default_layout
        )
        
        return fig
    
    def create_gauge(self,
                    value: float,
                    title: str,
                    min_value: float = 0,
                    max_value: float = 100,
                    thresholds: Optional[Dict] = None) -> go.Figure:
        """Cria gráfico de gauge/velocímetro"""
        
        if thresholds is None:
            thresholds = {
                'low': max_value * 0.3,
                'medium': max_value * 0.7,
                'high': max_value
            }
        
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=value,
            title={'text': title, 'font': {'size': 18}},
            delta={'reference': thresholds['medium']},
            gauge={
                'axis': {'range': [min_value, max_value]},
                'bar': {'color': self.colors['primary']},
                'steps': [
                    {'range': [min_value, thresholds['low']], 'color': self.colors['success']},
                    {'range': [thresholds['low'], thresholds['medium']], 'color': self.colors['warning']},
                    {'range': [thresholds['medium'], thresholds['high']], 'color': self.colors['danger']}
                ],
                'threshold': {
                    'line': {'color': self.colors['dark'], 'width': 4},
                    'thickness': 0.75,
                    'value': value
                }
            }
        ))
        
        fig.update_layout(
            height=250,
            margin=dict(l=20, r=20, t=40, b=20),
            paper_bgcolor='white'
        )
        
        return fig
    
    def create_sankey(self,
                     sources: List[str],
                     targets: List[str],
                     values: List[float],
                     title: str) -> go.Figure:
        """Cria diagrama Sankey para fluxo de energia"""
        
        # Criar lista única de nós
        nodes = list(set(sources + targets))
        node_dict = {node: i for i, node in enumerate(nodes)}
        
        # Mapear sources e targets para índices
        source_indices = [node_dict[s] for s in sources]
        target_indices = [node_dict[t] for t in targets]
        
        # Cores dos nós
        node_colors = []
        for node in nodes:
            if node in self.subsystem_colors:
                node_colors.append(self.subsystem_colors[node])
            elif node in self.source_colors:
                node_colors.append(self.source_colors[node])
            else:
                node_colors.append(self.colors['primary'])
        
        fig = go.Figure(data=[go.Sankey(
            node=dict(
                pad=15,
                thickness=20,
                line=dict(color="black", width=0.5),
                label=nodes,
                color=node_colors,
                hovertemplate='%{label}<br>%{value:.0f} MW<extra></extra>'
            ),
            link=dict(
                source=source_indices,
                target=target_indices,
                value=values,
                color='rgba(231, 203, 169, 0.3)',
                hovertemplate='%{source.label} → %{target.label}<br>%{value:.0f} MW<extra></extra>'
            )
        )])
        
        fig.update_layout(
            title=title,
            height=500,
            font=dict(size=12),
            paper_bgcolor='white'
        )
        
        return fig
    
    def create_radar_chart(self,
                          categories: List[str],
                          values: Dict[str, List[float]],
                          title: str) -> go.Figure:
        """Cria gráfico radar para comparação multidimensional"""
        
        fig = go.Figure()
        
        for name, data in values.items():
            color = self.subsystem_colors.get(name, self.colors['primary'])
            
            fig.add_trace(go.Scatterpolar(
                r=data,
                theta=categories,
                fill='toself',
                name=name,
                line=dict(color=color, width=2),
                fillcolor=color.replace(')', ', 0.1)').replace('rgb', 'rgba') if 'rgb' in color else color + '20',
                hovertemplate='%{theta}<br>%{r:.1f}<extra></extra>'
            ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, max([max(v) for v in values.values()])]
                )
            ),
            showlegend=True,
            title=title,
            height=400,
            **self.default_layout
        )
        
        return fig
    
    def create_waterfall(self,
                        categories: List[str],
                        values: List[float],
                        title: str) -> go.Figure:
        """Cria gráfico waterfall para análise de contribuições"""
        
        fig = go.Figure(go.Waterfall(
            name="",
            orientation="v",
            measure=["relative"] * (len(values) - 1) + ["total"],
            x=categories,
            y=values,
            textposition="outside",
            text=[f"{v:+.0f}" if i < len(values)-1 else f"{v:.0f}" 
                  for i, v in enumerate(values)],
            connector={"line": {"color": self.colors['primary']}},
            increasing={"marker": {"color": self.colors['success']}},
            decreasing={"marker": {"color": self.colors['danger']}},
            totals={"marker": {"color": self.colors['info']}},
            hovertemplate='%{x}<br>%{y:.0f} MW<extra></extra>'
        ))
        
        fig.update_layout(
            title=title,
            height=400,
            showlegend=False,
            **self.default_layout
        )
        
        return fig
    
    def create_3d_surface(self,
                         data: pd.DataFrame,
                         title: str) -> go.Figure:
        """Cria gráfico 3D de superfície"""
        
        fig = go.Figure(data=[go.Surface(
            z=data.values,
            x=data.columns,
            y=data.index,
            colorscale=[
                [0, self.colors['secondary']],
                [0.5, self.colors['primary']],
                [1, self.colors['danger']]
            ],
            contours={
                "z": {"show": True, "usecolormap": True, "highlightcolor": "limegreen", "project": {"z": True}}
            }
        )])
        
        fig.update_layout(
            title=title,
            autosize=False,
            width=800,
            height=600,
            scene=dict(
                xaxis_title="Hora",
                yaxis_title="Dia",
                zaxis_title="Carga (MW)",
                camera=dict(
                    eye=dict(x=1.5, y=1.5, z=1.3)
                )
            ),
            margin=dict(l=65, r=50, b=65, t=90)
        )
        
        return fig

def render_main_chart():
    """Renderiza o gráfico principal do dashboard"""
    viz = VisualizationEngine()
    
    # Container principal
    with st.container():
        st.markdown("### 📈 Análise Visual Avançada")
        
        # Seletor de tipo de visualização
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            chart_type = st.selectbox(
                "Tipo de Visualização:",
                ["Série Temporal", "Mapa de Calor", "Diagrama Sankey", 
                 "Gráfico Radar", "Waterfall", "Superfície 3D"],
                key="main_chart_type"
            )
        
        with col2:
            data_source = st.selectbox(
                "Fonte de Dados:",
                ["Carga de Energia", "CMO/PLD", "Geração por Fonte", 
                 "Intercâmbio Regional", "Eficiência do Sistema"],
                key="main_data_source"
            )
        
        with col3:
            if st.button("🔄 Atualizar", key="refresh_main_chart"):
                st.rerun()
        
        # Gerar visualização baseada na seleção
        if chart_type == "Série Temporal":
            # Dados simulados
            dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
            data = []
            
            for region in ['Sudeste/CO', 'Sul', 'Nordeste', 'Norte']:
                for date in dates:
                    data.append({
                        'date': date,
                        'region': region,
                        'value': np.random.normal(20000, 2000) if region == 'Sudeste/CO' 
                                else np.random.normal(10000, 1000)
                    })
            
            df = pd.DataFrame(data)
            
            fig = viz.create_time_series(
                df, 
                f"{data_source} - Últimos 30 dias",
                "MW" if "Carga" in data_source else "R$/MWh",
                series_column='region',
                value_column='value'
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        elif chart_type == "Mapa de Calor":
            # Dados simulados para heatmap
            hours = list(range(24))
            days = pd.date_range(end=datetime.now(), periods=7, freq='D').strftime('%d/%m')
            
            data = []
            for day in days:
                for hour in hours:
                    data.append({
                        'dia': day,
                        'hora': hour,
                        'value': np.random.normal(70000, 5000) + (2000 if 14 <= hour <= 20 else 0)
                    })
            
            df = pd.DataFrame(data)
            
            fig = viz.create_heatmap(
                df,
                f"Padrão de {data_source} - Semana",
                x_label="Hora do Dia",
                y_label="Data"
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        elif chart_type == "Diagrama Sankey":
            # Fluxo de energia
            sources = ['Hidrelétrica', 'Solar', 'Eólica', 'Térmica', 'Nuclear',
                      'Sudeste/CO', 'Sudeste/CO', 'Sudeste/CO']
            targets = ['Sudeste/CO', 'Sudeste/CO', 'Nordeste', 'Sul', 'Sudeste/CO',
                      'Sul', 'Nordeste', 'Norte']
            values = [30000, 5000, 8000, 4000, 2000,
                     2500, 1200, 3900]
            
            fig = viz.create_sankey(
                sources, targets, values,
                "Fluxo de Energia no SIN"
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        elif chart_type == "Gráfico Radar":
            categories = ['Eficiência', 'Disponibilidade', 'Custo', 
                         'Sustentabilidade', 'Confiabilidade', 'Flexibilidade']
            
            values = {
                'Sudeste/CO': [85, 92, 70, 78, 88, 75],
                'Sul': [82, 88, 75, 85, 85, 72],
                'Nordeste': [78, 85, 65, 90, 82, 80],
                'Norte': [75, 80, 60, 92, 78, 68]
            }
            
            fig = viz.create_radar_chart(
                categories, values,
                "Análise Multidimensional por Subsistema"
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        elif chart_type == "Waterfall":
            categories = ['Geração Base', 'Hidrelétrica', 'Solar', 'Eólica', 
                          'Importação', 'Térmica Acionada', 'Perdas', 'Carga Total']
            values = [50000, 15000, 5000, 8000, 3000, -2000, -6155, 72845]
            
            fig = viz.create_waterfall(
                categories, values,
                "Composição da Carga Total do SIN"
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        elif chart_type == "Superfície 3D":
            # Dados 3D simulados
            hours = list(range(24))
            days = list(range(7))
            
            data = np.zeros((7, 24))
            for i in days:
                for j in hours:
                    data[i, j] = np.random.normal(70000, 5000) + (3000 if 14 <= j <= 20 else 0)
            
            df = pd.DataFrame(data, 
                            index=[f"Dia {i+1}" for i in days],
                            columns=[f"{h:02d}:00" for h in hours])
            
            fig = viz.create_3d_surface(df, "Padrão de Carga Semanal - Visualização 3D")
            
            st.plotly_chart(fig, use_container_width=True)
        
        # Insights automáticos
        with st.expander("💡 **Insights Automáticos**", expanded=True):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.info("""
                    **📊 Padrão Identificado:**
                    Pico consistente entre 15h-18h com 
                    aumento médio de 12% na demanda.
                """)
            
            with col2:
                st.warning("""
                    **⚠️ Anomalia Detectada:**
                    Consumo 8% acima do esperado no 
                    Nordeste nas últimas 48h.
                """)
            
            with col3:
                st.success("""
                    **✅ Oportunidade:**
                    Potencial de economia de R$ 2.3M 
                    com otimização de despacho.
                """)

def create_comparison_chart(data1: pd.DataFrame, 
                           data2: pd.DataFrame,
                           title: str) -> go.Figure:
    """Cria gráfico de comparação entre dois períodos"""
    viz = VisualizationEngine()
    
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.1,
        subplot_titles=("Período Atual", "Período Anterior")
    )
    
    # Período atual
    for region in data1['region'].unique():
        region_data = data1[data1['region'] == region]
        fig.add_trace(
            go.Scatter(
                x=region_data['date'],
                y=region_data['value'],
                name=f"{region} (Atual)",
                line=dict(color=viz.subsystem_colors.get(region), width=2)
            ),
            row=1, col=1
        )
    
    # Período anterior
    for region in data2['region'].unique():
        region_data = data2[data2['region'] == region]
        fig.add_trace(
            go.Scatter(
                x=region_data['date'],
                y=region_data['value'],
                name=f"{region} (Anterior)",
                line=dict(color=viz.subsystem_colors.get(region), width=2, dash='dash')
            ),
            row=2, col=1
        )
    
    fig.update_layout(
        title=title,
        height=600,
        showlegend=True,
        hovermode='x unified'
    )
    
    fig.update_xaxes(title_text="Data", row=2, col=1)
    fig.update_yaxes(title_text="MW", row=1, col=1)
    fig.update_yaxes(title_text="MW", row=2, col=1)
    
    return fig

def render_mini_dashboard():
    """Renderiza um mini dashboard com múltiplos gráficos pequenos"""
    viz = VisualizationEngine()
    
    st.markdown("### 🎯 Dashboard Compacto")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Gauge de eficiência
        fig = viz.create_gauge(
            value=87.5,
            title="Eficiência do Sistema",
            min_value=0,
            max_value=100,
            thresholds={'low': 60, 'medium': 80, 'high': 100}
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Gauge de reservatórios
        fig = viz.create_gauge(
            value=58.3,
            title="Nível dos Reservatórios SE/CO",
            min_value=0,
            max_value=100,
            thresholds={'low': 30, 'medium': 50, 'high': 100}
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Mini gráficos de linha
    col1, col2, col3 = st.columns(3)
    
    with col1:
        data = pd.DataFrame({
            'x': range(24),
            'y': np.random.normal(70000, 5000, 24)
        })
        
        fig = px.area(data, x='x', y='y', 
                      title="Carga Últimas 24h",
                      color_discrete_sequence=[viz.colors['primary']])
        fig.update_layout(height=200, showlegend=False)
        fig.update_xaxis(title="Hora")
        fig.update_yaxis(title="MW")
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        data = pd.DataFrame({
            'x': range(24),
            'y': np.random.normal(150, 10, 24)
        })
        
        fig = px.line(data, x='x', y='y',
                     title="CMO Médio 24h",
                     color_discrete_sequence=[viz.colors['info']])
        fig.update_layout(height=200, showlegend=False)
        fig.update_xaxis(title="Hora")
        fig.update_yaxis(title="R$/MWh")
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col3:
        data = pd.DataFrame({
            'Fonte': ['Hidro', 'Solar', 'Eólica', 'Térmica'],
            'Geração': [45, 12, 17, 26]
        })
        
        fig = px.pie(data, values='Geração', names='Fonte',
                    title="Mix de Geração",
                    color_discrete_map={
                        'Hidro': viz.source_colors['Hidrelétrica'],
                        'Solar': viz.source_colors['Solar'],
                        'Eólica': viz.source_colors['Eólica'],
                        'Térmica': viz.source_colors['Térmica']
                    })
        fig.update_layout(height=200)
        fig.update_traces(textposition='inside', textinfo='percent')
        
        st.plotly_chart(fig, use_container_width=True)

# Exportar classes e funções
__all__ = ['VisualizationEngine', 'render_main_chart', 'create_comparison_chart', 'render_mini_dashboard']