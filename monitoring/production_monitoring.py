# monitoring_dashboard.py
"""
Dashboard de Monitoramento em Tempo Real para o Sistema AIDE
Executa em paralelo ao sistema principal para monitoramento de produção
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import psycopg2
import redis
import requests
from datetime import datetime, timedelta
import time
import json
import os
from typing import Dict, List, Tuple, Optional
import numpy as np

# ============= Configuração da Página =============

st.set_page_config(
    page_title="AIDE - Monitoring Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS para o dashboard
st.markdown("""
<style>
    .metric-container {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    
    .health-score-high {
        color: #00cc44;
        font-size: 48px;
        font-weight: bold;
    }
    
    .health-score-medium {
        color: #ffaa00;
        font-size: 48px;
        font-weight: bold;
    }
    
    .health-score-low {
        color: #ff3333;
        font-size: 48px;
        font-weight: bold;
    }
    
    .status-indicator {
        display: inline-block;
        width: 12px;
        height: 12px;
        border-radius: 50%;
        margin-right: 5px;
    }
    
    .status-healthy { background-color: #00cc44; }
    .status-warning { background-color: #ffaa00; }
    .status-critical { background-color: #ff3333; }
    
    .alert-box {
        padding: 15px;
        border-radius: 5px;
        margin: 10px 0;
    }
    
    .alert-critical {
        background-color: #ffe6e6;
        border-left: 4px solid #ff3333;
    }
    
    .alert-warning {
        background-color: #fff3cd;
        border-left: 4px solid #ffaa00;
    }
</style>
""", unsafe_allow_html=True)

# ============= Conexões =============

@st.cache_resource
def get_db_connection():
    """Criar conexão com PostgreSQL."""
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        database=os.getenv("DB_NAME", "aide_db"),
        user=os.getenv("DB_USER", "aide_user"),
        password=os.getenv("DB_PASSWORD", "aide_secure_password_123")
    )

@st.cache_resource
def get_redis_connection():
    """Criar conexão com Redis."""
    return redis.Redis(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=int(os.getenv("REDIS_PORT", "6379")),
        password=os.getenv("REDIS_PASSWORD", ""),
        decode_responses=True
    )

# ============= Funções de Coleta de Métricas =============

def get_system_health() -> Dict:
    """Obter saúde geral do sistema."""
    try:
        r = get_redis_connection()
        health_data = r.get("health:latest")
        if health_data:
            return json.loads(health_data)
    except:
        pass
    
    return {
        "health_score": 0,
        "status": "unknown",
        "timestamp": datetime.now().isoformat()
    }

def get_database_metrics() -> Dict:
    """Coletar métricas do banco de dados."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        metrics = {}
        
        # Tamanho do banco
        cur.execute("""
            SELECT pg_database_size('aide_db')/1024/1024 as size_mb
        """)
        metrics['db_size_mb'] = cur.fetchone()[0]
        
        # Número de conexões ativas
        cur.execute("""
            SELECT count(*) FROM pg_stat_activity 
            WHERE state = 'active'
        """)
        metrics['active_connections'] = cur.fetchone()[0]
        
        # Queries longas
        cur.execute("""
            SELECT count(*) FROM pg_stat_activity 
            WHERE state = 'active' 
            AND now() - query_start > interval '5 seconds'
        """)
        metrics['long_queries'] = cur.fetchone()[0]
        
        # Total de registros
        cur.execute("SELECT COUNT(*) FROM data_records")
        metrics['total_records'] = cur.fetchone()[0]
        
        # Registros das últimas 24h
        cur.execute("""
            SELECT COUNT(*) FROM data_records 
            WHERE created_at > NOW() - INTERVAL '24 hours'
        """)
        metrics['recent_records'] = cur.fetchone()[0]
        
        cur.close()
        conn.close()
        
        return metrics
    except Exception as e:
        st.error(f"Erro ao coletar métricas do banco: {e}")
        return {}

def get_redis_metrics() -> Dict:
    """Coletar métricas do Redis."""
    try:
        r = get_redis_connection()
        info = r.info()
        
        return {
            'used_memory_mb': info.get('used_memory', 0) / (1024 * 1024),
            'connected_clients': info.get('connected_clients', 0),
            'total_commands': info.get('total_commands_processed', 0),
            'keyspace_hits': info.get('keyspace_hits', 0),
            'keyspace_misses': info.get('keyspace_misses', 0),
            'hit_rate': (info.get('keyspace_hits', 0) / 
                        max(1, info.get('keyspace_hits', 0) + info.get('keyspace_misses', 0))) * 100
        }
    except Exception as e:
        st.error(f"Erro ao coletar métricas do Redis: {e}")
        return {}

def get_workflow_metrics() -> Dict:
    """Coletar métricas dos workflows n8n."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Métricas de ingestão
        cur.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN status = 'success' THEN 1 END) as success,
                COUNT(CASE WHEN status = 'error' THEN 1 END) as errors,
                AVG(CASE WHEN value IS NOT NULL THEN value END) as avg_time
            FROM monitoring_metrics
            WHERE metric_name LIKE 'ingestion_%'
                AND timestamp > NOW() - INTERVAL '1 hour'
        """)
        ingestion = cur.fetchone()
        
        # Métricas de chat
        cur.execute("""
            SELECT 
                COUNT(*) as total_messages,
                AVG(CAST(details->>'processing_time_ms' AS FLOAT)) as avg_time
            FROM monitoring_metrics
            WHERE metric_name = 'chat_request'
                AND timestamp > NOW() - INTERVAL '1 hour'
        """)
        chat = cur.fetchone()
        
        cur.close()
        conn.close()
        
        return {
            'ingestion': {
                'total': ingestion[0] if ingestion else 0,
                'success': ingestion[1] if ingestion else 0,
                'errors': ingestion[2] if ingestion else 0,
                'avg_time': ingestion[3] if ingestion else 0
            },
            'chat': {
                'total': chat[0] if chat else 0,
                'avg_time': chat[1] if chat else 0
            }
        }
    except Exception as e:
        st.error(f"Erro ao coletar métricas de workflows: {e}")
        return {}

def get_error_logs(limit: int = 10) -> List[Dict]:
    """Obter logs de erro recentes."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT 
                workflow,
                error_message,
                severity,
                created_at
            FROM error_logs
            ORDER BY created_at DESC
            LIMIT %s
        """, (limit,))
        
        errors = []
        for row in cur.fetchall():
            errors.append({
                'workflow': row[0],
                'message': row[1],
                'severity': row[2],
                'timestamp': row[3]
            })
        
        cur.close()
        conn.close()
        
        return errors
    except:
        return []

def get_active_alerts() -> List[Dict]:
    """Obter alertas ativos."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT 
                metric_name,
                status,
                message,
                severity,
                timestamp
            FROM monitoring_metrics
            WHERE status != 'ok'
                AND timestamp > NOW() - INTERVAL '30 minutes'
            ORDER BY 
                CASE severity 
                    WHEN 'critical' THEN 1
                    WHEN 'high' THEN 2
                    WHEN 'medium' THEN 3
                    ELSE 4
                END,
                timestamp DESC
        """)
        
        alerts = []
        for row in cur.fetchall():
            alerts.append({
                'metric': row[0],
                'status': row[1],
                'message': row[2],
                'severity': row[3],
                'timestamp': row[4]
            })
        
        cur.close()
        conn.close()
        
        return alerts
    except:
        return []

def get_performance_timeseries() -> pd.DataFrame:
    """Obter série temporal de performance."""
    try:
        conn = get_db_connection()
        
        query = """
            SELECT 
                DATE_TRUNC('minute', timestamp) as time,
                AVG(CASE WHEN metric_name = 'api_response_time' THEN value END) as api_time,
                AVG(CASE WHEN metric_name = 'chat_request' THEN value END) as chat_time,
                COUNT(CASE WHEN status = 'error' THEN 1 END) as errors
            FROM monitoring_metrics
            WHERE timestamp > NOW() - INTERVAL '1 hour'
            GROUP BY time
            ORDER BY time
        """
        
        df = pd.read_sql(query, conn)
        conn.close()
        
        return df
    except:
        return pd.DataFrame()

# ============= Dashboard Principal =============

st.title("📊 AIDE - Production Monitoring Dashboard")

# Auto-refresh
refresh_interval = st.sidebar.selectbox(
    "Auto-refresh",
    options=[5, 10, 30, 60],
    index=1
)

placeholder = st.empty()

while True:
    with placeholder.container():
        
        # Header com status geral
        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
        
        with col1:
            health = get_system_health()
            health_score = health.get('health_score', 0)
            
            if health_score >= 80:
                score_class = "health-score-high"
                status_class = "status-healthy"
                status_text = "Sistema Operacional"
            elif health_score >= 50:
                score_class = "health-score-medium"
                status_class = "status-warning"
                status_text = "Sistema Degradado"
            else:
                score_class = "health-score-low"
                status_class = "status-critical"
                status_text = "Sistema Crítico"
            
            st.markdown(f"""
                <div style="text-align: center;">
                    <h2>Health Score</h2>
                    <div class="{score_class}">{health_score}%</div>
                    <p><span class="status-indicator {status_class}"></span>{status_text}</p>
                    <small>Última atualização: {datetime.now().strftime('%H:%M:%S')}</small>
                </div>
            """, unsafe_allow_html=True)
        
        with col2:
            db_metrics = get_database_metrics()
            st.metric(
                "Database Size",
                f"{db_metrics.get('db_size_mb', 0):.1f} MB",
                delta=f"{db_metrics.get('recent_records', 0)} new records"
            )
            st.metric(
                "Active Connections",
                db_metrics.get('active_connections', 0),
                delta=db_metrics.get('long_queries', 0)
            )
        
        with col3:
            redis_metrics = get_redis_metrics()
            st.metric(
                "Redis Memory",
                f"{redis_metrics.get('used_memory_mb', 0):.1f} MB",
                delta=f"{redis_metrics.get('connected_clients', 0)} clients"
            )
            st.metric(
                "Cache Hit Rate",
                f"{redis_metrics.get('hit_rate', 0):.1f}%"
            )
        
        with col4:
            workflow_metrics = get_workflow_metrics()
            ingestion = workflow_metrics.get('ingestion', {})
            chat = workflow_metrics.get('chat', {})
            
            st.metric(
                "Workflows (1h)",
                ingestion.get('total', 0) + chat.get('total', 0),
                delta=f"{ingestion.get('errors', 0)} errors"
            )
            st.metric(
                "Avg Response",
                f"{chat.get('avg_time', 0):.0f} ms"
            )
        
        st.markdown("---")
        
        # Alertas Ativos
        alerts = get_active_alerts()
        if alerts:
            st.subheader("🚨 Alertas Ativos")
            
            for alert in alerts[:5]:
                severity = alert['severity']
                alert_class = 'alert-critical' if severity == 'critical' else 'alert-warning'
                
                st.markdown(f"""
                    <div class="alert-box {alert_class}">
                        <strong>{alert['metric']}</strong> - {alert['status'].upper()}<br>
                        {alert['message']}<br>
                        <small>{alert['timestamp'].strftime('%H:%M:%S')}</small>
                    </div>
                """, unsafe_allow_html=True)
        
        # Gráficos de Performance
        st.subheader("📈 Performance Metrics")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Gráfico de série temporal
            df_perf = get_performance_timeseries()
            if not df_perf.empty:
                fig = go.Figure()
                
                fig.add_trace(go.Scatter(
                    x=df_perf['time'],
                    y=df_perf['api_time'],
                    name='API Response Time',
                    line=dict(color='#667eea', width=2)
                ))
                
                fig.add_trace(go.Scatter(
                    x=df_perf['time'],
                    y=df_perf['chat_time'],
                    name='Chat Processing',
                    line=dict(color='#764ba2', width=2)
                ))
                
                fig.update_layout(
                    title="Response Time (Last Hour)",
                    xaxis_title="Time",
                    yaxis_title="Time (ms)",
                    height=300,
                    showlegend=True,
                    hovermode='x unified'
                )
                
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Gráfico de distribuição de workflows
            workflow_data = workflow_metrics.get('ingestion', {})
            
            fig = go.Figure(data=[
                go.Bar(
                    x=['Success', 'Errors', 'Pending'],
                    y=[
                        workflow_data.get('success', 0),
                        workflow_data.get('errors', 0),
                        workflow_data.get('total', 0) - workflow_data.get('success', 0) - workflow_data.get('errors', 0)
                    ],
                    marker_color=['#00cc44', '#ff3333', '#ffaa00']
                )
            ])
            
            fig.update_layout(
                title="Workflow Status (Last Hour)",
                yaxis_title="Count",
                height=300,
                showlegend=False
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        # Sistema de Métricas Detalhadas
        st.subheader("📊 System Metrics")
        
        # Criar gauge charts para métricas principais
        fig = make_subplots(
            rows=1, cols=4,
            specs=[[{'type': 'indicator'}, {'type': 'indicator'}, 
                   {'type': 'indicator'}, {'type': 'indicator'}]],
            subplot_titles=("CPU Usage", "Memory Usage", "Disk I/O", "Network Traffic")
        )
        
        # CPU Usage (simulado)
        cpu_usage = np.random.uniform(20, 80)
        fig.add_trace(
            go.Indicator(
                mode="gauge+number",
                value=cpu_usage,
                domain={'x': [0, 1], 'y': [0, 1]},
                gauge={'axis': {'range': [0, 100]},
                      'bar': {'color': "darkblue"},
                      'steps': [
                          {'range': [0, 50], 'color': "lightgray"},
                          {'range': [50, 80], 'color': "yellow"},
                          {'range': [80, 100], 'color': "red"}]},
                title={'text': "CPU %"}
            ),
            row=1, col=1
        )
        
        # Memory Usage
        memory_usage = redis_metrics.get('used_memory_mb', 0) / 100 * 100  # Percentual
        fig.add_trace(
            go.Indicator(
                mode="gauge+number",
                value=min(memory_usage, 100),
                domain={'x': [0, 1], 'y': [0, 1]},
                gauge={'axis': {'range': [0, 100]},
                      'bar': {'color': "purple"}},
                title={'text': "Memory %"}
            ),
            row=1, col=2
        )
        
        # Disk I/O (simulado)
        disk_io = np.random.uniform(100, 500)
        fig.add_trace(
            go.Indicator(
                mode="gauge+number",
                value=disk_io,
                domain={'x': [0, 1], 'y': [0, 1]},
                gauge={'axis': {'range': [0, 1000]},
                      'bar': {'color': "green"}},
                title={'text': "MB/s"}
            ),
            row=1, col=3
        )
        
        # Network Traffic (simulado)
        network_traffic = np.random.uniform(50, 200)
        fig.add_trace(
            go.Indicator(
                mode="gauge+number",
                value=network_traffic,
                domain={'x': [0, 1], 'y': [0, 1]},
                gauge={'axis': {'range': [0, 500]},
                      'bar': {'color': "orange"}},
                title={'text': "Mbps"}
            ),
            row=1, col=4
        )
        
        fig.update_layout(height=250, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
        
        # Logs de Erro
        st.subheader("📝 Recent Error Logs")
        
        errors = get_error_logs(5)
        if errors:
            error_df = pd.DataFrame(errors)
            error_df['timestamp'] = pd.to_datetime(error_df['timestamp'])
            
            # Colorir por severidade
            def color_severity(val):
                if val == 'critical':
                    return 'background-color: #ffe6e6'
                elif val == 'high':
                    return 'background-color: #fff3cd'
                return ''
            
            styled_df = error_df.style.applymap(
                color_severity, 
                subset=['severity']
            )
            
            st.dataframe(
                styled_df,
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("Nenhum erro registrado nas últimas 24 horas")
        
        # Estatísticas Adicionais
        st.subheader("📊 Statistics")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown("""
                **Database Stats**
                - Total Records: {:,}
                - Today's Records: {:,}
                - Active Queries: {}
            """.format(
                db_metrics.get('total_records', 0),
                db_metrics.get('recent_records', 0),
                db_metrics.get('active_connections', 0)
            ))
        
        with col2:
            st.markdown("""
                **Cache Stats**
                - Hit Rate: {:.1f}%
                - Total Commands: {:,}
                - Memory Used: {:.1f} MB
            """.format(
                redis_metrics.get('hit_rate', 0),
                redis_metrics.get('total_commands', 0),
                redis_metrics.get('used_memory_mb', 0)
            ))
        
        with col3:
            ingestion = workflow_metrics.get('ingestion', {})
            st.markdown("""
                **Ingestion Stats**
                - Total: {}
                - Success: {}
                - Errors: {}
            """.format(
                ingestion.get('total', 0),
                ingestion.get('success', 0),
                ingestion.get('errors', 0)
            ))
        
        with col4:
            chat = workflow_metrics.get('chat', {})
            st.markdown("""
                **Chat Stats**
                - Messages: {}
                - Avg Time: {:.0f} ms
                - Active Sessions: N/A
            """.format(
                chat.get('total', 0),
                chat.get('avg_time', 0)
            ))
    
    # Aguardar antes do próximo refresh
    time.sleep(refresh_interval)