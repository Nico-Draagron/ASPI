"""
AIDE - Componente de Exportação
Sistema de exportação de dados e relatórios
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import json
import base64
from io import BytesIO, StringIO
import plotly.graph_objects as go
from typing import Dict, List, Optional, Any
import zipfile

class ExportManager:
    """Gerenciador de exportação de dados e relatórios"""
    
    def __init__(self):
        self.supported_formats = ['Excel', 'CSV', 'JSON', 'PDF', 'HTML']
        self.export_history = []
    
    def prepare_dataframe(self, data: Any) -> pd.DataFrame:
        """Prepara dados para exportação em DataFrame"""
        if isinstance(data, pd.DataFrame):
            return data
        elif isinstance(data, dict):
            return pd.DataFrame(data)
        elif isinstance(data, list):
            return pd.DataFrame(data)
        else:
            raise ValueError("Formato de dados não suportado")
    
    def export_to_excel(self, 
                       data: Dict[str, pd.DataFrame], 
                       metadata: Optional[Dict] = None) -> BytesIO:
        """Exporta dados para Excel com múltiplas abas"""
        output = BytesIO()
        
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            workbook = writer.book
            
            # Formatos customizados
            header_format = workbook.add_format({
                'bold': True,
                'text_wrap': True,
                'valign': 'center',
                'fg_color': '#e7cba9',
                'border': 1
            })
            
            cell_format = workbook.add_format({
                'border': 1,
                'valign': 'vcenter'
            })
            
            # Adicionar aba de metadados
            if metadata:
                meta_df = pd.DataFrame([metadata]).T
                meta_df.columns = ['Valor']
                meta_df.to_excel(writer, sheet_name='Informações', index=True)
                
                worksheet = writer.sheets['Informações']
                worksheet.set_column('A:A', 30)
                worksheet.set_column('B:B', 50)
            
            # Adicionar cada dataset como uma aba
            for sheet_name, df in data.items():
                df.to_excel(writer, sheet_name=sheet_name[:31], index=False)
                
                # Formatar a planilha
                worksheet = writer.sheets[sheet_name[:31]]
                
                # Aplicar formato ao cabeçalho
                for col_num, value in enumerate(df.columns.values):
                    worksheet.write(0, col_num, value, header_format)
                
                # Ajustar largura das colunas
                for i, col in enumerate(df.columns):
                    column_width = max(df[col].astype(str).map(len).max(), len(col)) + 2
                    worksheet.set_column(i, i, min(column_width, 50))
                
                # Adicionar gráfico se aplicável
                if len(df) > 1 and df.select_dtypes(include=[np.number]).shape[1] > 0:
                    chart = workbook.add_chart({'type': 'line'})
                    
                    # Configurar o gráfico
                    for i, col in enumerate(df.select_dtypes(include=[np.number]).columns):
                        chart.add_series({
                            'name': col,
                            'categories': [sheet_name[:31], 1, 0, len(df), 0],
                            'values': [sheet_name[:31], 1, i+1, len(df), i+1],
                            'line': {'width': 2}
                        })
                    
                    chart.set_title({'name': f'Análise - {sheet_name}'})
                    chart.set_x_axis({'name': 'Período'})
                    chart.set_y_axis({'name': 'Valores'})
                    chart.set_size({'width': 720, 'height': 400})
                    
                    worksheet.insert_chart(f'A{len(df)+3}', chart)
        
        output.seek(0)
        return output
    
    def export_to_csv(self, data: pd.DataFrame) -> str:
        """Exporta dados para CSV"""
        return data.to_csv(index=False)
    
    def export_to_json(self, 
                      data: pd.DataFrame, 
                      metadata: Optional[Dict] = None) -> str:
        """Exporta dados para JSON"""
        export_data = {
            'metadata': metadata or {
                'exported_at': datetime.now().isoformat(),
                'source': 'AIDE - ONS Data',
                'version': '1.0'
            },
            'data': data.to_dict(orient='records')
        }
        return json.dumps(export_data, indent=2, ensure_ascii=False, default=str)
    
    def export_to_html(self, 
                      data: pd.DataFrame,
                      charts: Optional[List[go.Figure]] = None,
                      title: str = "Relatório AIDE") -> str:
        """Exporta dados e gráficos para HTML"""
        
        html_template = f"""
        <!DOCTYPE html>
        <html lang="pt-BR">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{title}</title>
            <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
            <style>
                body {{
                    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                    margin: 0;
                    padding: 20px;
                    background-color: #f8f9fa;
                }}
                .container {{
                    max-width: 1200px;
                    margin: 0 auto;
                    background-color: white;
                    padding: 30px;
                    border-radius: 12px;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                }}
                .header {{
                    background: linear-gradient(135deg, #e7cba9 0%, #f4e4d4 100%);
                    padding: 20px;
                    border-radius: 8px;
                    margin-bottom: 30px;
                }}
                h1 {{
                    color: #2c3e50;
                    margin: 0;
                }}
                .subtitle {{
                    color: #5a6c7d;
                    margin-top: 10px;
                }}
                .data-table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin: 20px 0;
                }}
                .data-table th {{
                    background: #e7cba9;
                    color: #2c3e50;
                    padding: 12px;
                    text-align: left;
                    font-weight: 600;
                }}
                .data-table td {{
                    padding: 10px 12px;
                    border-bottom: 1px solid #e9ecef;
                }}
                .data-table tr:hover {{
                    background-color: rgba(231, 203, 169, 0.1);
                }}
                .chart-container {{
                    margin: 30px 0;
                    padding: 20px;
                    border: 1px solid #e9ecef;
                    border-radius: 8px;
                }}
                .footer {{
                    text-align: center;
                    color: #6c757d;
                    margin-top: 40px;
                    padding-top: 20px;
                    border-top: 1px solid #e9ecef;
                }}
                .metadata {{
                    background: #f8f9fa;
                    padding: 15px;
                    border-radius: 8px;
                    margin: 20px 0;
                }}
                .metadata-item {{
                    display: flex;
                    justify-content: space-between;
                    padding: 5px 0;
                }}
                .badge {{
                    display: inline-block;
                    padding: 4px 8px;
                    border-radius: 4px;
                    font-size: 12px;
                    font-weight: 600;
                }}
                .badge-success {{
                    background: #d1fae5;
                    color: #065f46;
                }}
                .badge-warning {{
                    background: #fed7aa;
                    color: #92400e;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>⚡ {title}</h1>
                    <div class="subtitle">
                        Relatório gerado pelo AIDE - Assistente Inteligente para Dados do Setor Elétrico
                    </div>
                </div>
                
                <div class="metadata">
                    <div class="metadata-item">
                        <strong>Data de Geração:</strong>
                        <span>{datetime.now().strftime('%d/%m/%Y %H:%M')}</span>
                    </div>
                    <div class="metadata-item">
                        <strong>Fonte de Dados:</strong>
                        <span class="badge badge-success">ONS - Operador Nacional do Sistema</span>
                    </div>
                    <div class="metadata-item">
                        <strong>Registros:</strong>
                        <span>{len(data)} linhas</span>
                    </div>
                </div>
        """
        
        # Adicionar tabela de dados
        html_template += f"""
                <h2>📊 Dados</h2>
                {data.to_html(classes='data-table', index=False)}
        """
        
        # Adicionar gráficos se fornecidos
        if charts:
            html_template += "<h2>📈 Visualizações</h2>"
            for i, chart in enumerate(charts):
                html_template += f"""
                <div class="chart-container">
                    <div id="chart_{i}"></div>
                    <script>
                        Plotly.newPlot('chart_{i}', {chart.to_json()});
                    </script>
                </div>
                """
        
        # Footer
        html_template += """
                <div class="footer">
                    <p>© 2025 AIDE - Sistema Inteligente de Análise de Dados do Setor Elétrico</p>
                    <p>Desenvolvido com tecnologia de IA para o ONS</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html_template
    
    def create_download_link(self, 
                           data: Any, 
                           filename: str, 
                           mime_type: str = 'text/plain') -> str:
        """Cria link de download para arquivo"""
        if isinstance(data, str):
            b64 = base64.b64encode(data.encode()).decode()
        elif isinstance(data, bytes):
            b64 = base64.b64encode(data).decode()
        elif isinstance(data, BytesIO):
            b64 = base64.b64encode(data.getvalue()).decode()
        else:
            raise ValueError("Tipo de dados não suportado para download")
        
        return f'<a href="data:{mime_type};base64,{b64}" download="{filename}">📥 Baixar {filename}</a>'
    
    def create_report_package(self,
                            datasets: Dict[str, pd.DataFrame],
                            charts: Optional[List[go.Figure]] = None,
                            metadata: Optional[Dict] = None) -> BytesIO:
        """Cria pacote ZIP com todos os arquivos do relatório"""
        zip_buffer = BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Adicionar metadados
            report_metadata = metadata or {}
            report_metadata.update({
                'generated_at': datetime.now().isoformat(),
                'generator': 'AIDE v1.0',
                'source': 'ONS - Portal de Dados Abertos'
            })
            
            zip_file.writestr('metadata.json', json.dumps(report_metadata, indent=2, default=str))
            
            # Adicionar cada dataset em diferentes formatos
            for name, df in datasets.items():
                # CSV
                csv_data = df.to_csv(index=False)
                zip_file.writestr(f'data/{name}.csv', csv_data)
                
                # JSON
                json_data = df.to_json(orient='records', indent=2, default_handler=str)
                zip_file.writestr(f'data/{name}.json', json_data)
            
            # Adicionar relatório HTML se houver gráficos
            if charts:
                html_report = self.export_to_html(
                    next(iter(datasets.values())),
                    charts,
                    "Relatório Completo AIDE"
                )
                zip_file.writestr('relatorio.html', html_report)
            
            # Adicionar README
            readme_content = """
# Relatório AIDE - Assistente Inteligente para Dados do Setor Elétrico

## Conteúdo do Pacote

### 📁 data/
Contém os datasets exportados em diferentes formatos:
- `.csv` - Formato tabular para análise em planilhas
- `.json` - Formato estruturado para integração com sistemas

### 📄 metadata.json
Informações sobre a geração do relatório

### 📊 relatorio.html
Relatório visual completo com gráficos interativos

## Como Usar

1. **Dados CSV**: Abra com Excel, Google Sheets ou qualquer editor de planilhas
2. **Dados JSON**: Use em aplicações ou análises programáticas
3. **Relatório HTML**: Abra em qualquer navegador web para visualização interativa

## Suporte

Para dúvidas ou suporte, acesse: https://www.ons.org.br

---
Gerado automaticamente pelo AIDE v1.0
            """
            zip_file.writestr('README.md', readme_content)
        
        zip_buffer.seek(0)
        return zip_buffer

def render_export_interface():
    """Renderiza interface de exportação"""
    export_manager = ExportManager()
    
    st.markdown("### 📤 Central de Exportação")
    
    # Tabs de exportação
    tab1, tab2, tab3 = st.tabs(["🎯 Exportação Rápida", "📊 Relatório Personalizado", "📦 Pacote Completo"])
    
    with tab1:
        st.markdown("#### Exportação Rápida de Dados")
        
        col1, col2 = st.columns(2)
        
        with col1:
            export_format = st.selectbox(
                "Formato de exportação:",
                export_manager.supported_formats,
                key="quick_export_format"
            )
            
            dataset_option = st.selectbox(
                "Dataset:",
                ["Carga de Energia", "CMO/PLD", "Bandeiras Tarifárias", "Dados Customizados"],
                key="quick_dataset"
            )
        
        with col2:
            period = st.selectbox(
                "Período:",
                ["Hoje", "Última Semana", "Último Mês", "Último Ano", "Customizado"],
                key="quick_period"
            )
            
            include_charts = st.checkbox(
                "Incluir visualizações",
                value=True,
                key="quick_include_charts"
            )
        
        # Dados simulados para demonstração
        sample_data = pd.DataFrame({
            'Data': pd.date_range(start='2025-09-01', periods=7, freq='D'),
            'Subsistema': ['SE/CO'] * 7,
            'Carga (MW)': np.random.normal(42000, 2000, 7),
            'CMO (R$/MWh)': np.random.normal(142, 10, 7),
            'Temperatura (°C)': np.random.normal(25, 3, 7)
        })
        
        # Preview dos dados
        with st.expander("👁️ Preview dos Dados", expanded=True):
            st.dataframe(sample_data, use_container_width=True)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Registros", len(sample_data))
            with col2:
                st.metric("Colunas", len(sample_data.columns))
            with col3:
                st.metric("Período", f"{sample_data['Data'].min().date()} a {sample_data['Data'].max().date()}")
        
        # Botão de exportação
        if st.button("🚀 Exportar Agora", type="primary", key="quick_export_button"):
            with st.spinner("Preparando exportação..."):
                if export_format == "Excel":
                    output = export_manager.export_to_excel(
                        {'Dados': sample_data},
                        {'Tipo': dataset_option, 'Período': period}
                    )
                    st.success("✅ Arquivo Excel gerado com sucesso!")
                    st.markdown(
                        export_manager.create_download_link(
                            output, 
                            f"aide_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        ),
                        unsafe_allow_html=True
                    )
                
                elif export_format == "CSV":
                    csv_data = export_manager.export_to_csv(sample_data)
                    st.success("✅ Arquivo CSV gerado com sucesso!")
                    st.download_button(
                        label="📥 Baixar CSV",
                        data=csv_data,
                        file_name=f"aide_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
                
                elif export_format == "JSON":
                    json_data = export_manager.export_to_json(sample_data)
                    st.success("✅ Arquivo JSON gerado com sucesso!")
                    st.download_button(
                        label="📥 Baixar JSON",
                        data=json_data,
                        file_name=f"aide_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json"
                    )
                
                elif export_format == "HTML":
                    html_data = export_manager.export_to_html(sample_data, title=dataset_option)
                    st.success("✅ Relatório HTML gerado com sucesso!")
                    st.download_button(
                        label="📥 Baixar HTML",
                        data=html_data,
                        file_name=f"aide_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
                        mime="text/html"
                    )
    
    with tab2:
        st.markdown("#### Gerador de Relatório Personalizado")
        
        # Configurações do relatório
        col1, col2 = st.columns(2)
        
        with col1:
            report_title = st.text_input(
                "Título do Relatório:",
                value="Análise do Sistema Elétrico Nacional",
                key="report_title"
            )
            
            report_author = st.text_input(
                "Autor:",
                value="AIDE - Sistema Inteligente",
                key="report_author"
            )
        
        with col2:
            report_type = st.selectbox(
                "Tipo de Relatório:",
                ["Executivo", "Técnico Detalhado", "Análise Comparativa", "Dashboard Visual"],
                key="report_type"
            )
            
            report_frequency = st.selectbox(
                "Frequência:",
                ["Único", "Diário", "Semanal", "Mensal"],
                key="report_frequency"
            )
        
        # Seleção de seções
        st.markdown("##### 📑 Seções do Relatório")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            include_summary = st.checkbox("Resumo Executivo", value=True)
            include_load = st.checkbox("Análise de Carga", value=True)
            include_cost = st.checkbox("Análise de Custos", value=True)
        
        with col2:
            include_generation = st.checkbox("Mix de Geração", value=True)
            include_reservoirs = st.checkbox("Situação Hídrica", value=False)
            include_interchange = st.checkbox("Intercâmbio Regional", value=False)
        
        with col3:
            include_forecast = st.checkbox("Previsões", value=False)
            include_anomalies = st.checkbox("Anomalias Detectadas", value=True)
            include_recommendations = st.checkbox("Recomendações", value=True)
        
        # Template de relatório
        if st.button("📝 Gerar Relatório Personalizado", key="custom_report_button"):
            with st.spinner("Gerando relatório personalizado..."):
                # Simular geração de relatório
                st.success("✅ Relatório personalizado gerado com sucesso!")
                
                # Preview do relatório
                st.markdown(f"""
                    <div style="border: 2px solid #e7cba9; border-radius: 8px; padding: 20px; margin-top: 20px;">
                        <h3>{report_title}</h3>
                        <p><strong>Autor:</strong> {report_author}</p>
                        <p><strong>Data:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
                        <p><strong>Tipo:</strong> {report_type}</p>
                        <hr>
                        <h4>Seções Incluídas:</h4>
                        <ul>
                            {'<li>Resumo Executivo</li>' if include_summary else ''}
                            {'<li>Análise de Carga</li>' if include_load else ''}
                            {'<li>Análise de Custos</li>' if include_cost else ''}
                            {'<li>Mix de Geração</li>' if include_generation else ''}
                            {'<li>Anomalias Detectadas</li>' if include_anomalies else ''}
                            {'<li>Recomendações</li>' if include_recommendations else ''}
                        </ul>
                    </div>
                """, unsafe_allow_html=True)
                
                # Botão de download
                st.download_button(
                    label="📥 Baixar Relatório Completo",
                    data="[Conteúdo do relatório seria gerado aqui]",
                    file_name=f"relatorio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                    mime="application/pdf"
                )
    
    with tab3:
        st.markdown("#### Pacote Completo de Dados")
        
        st.info("""
            📦 **O Pacote Completo inclui:**
            - ✅ Todos os datasets selecionados em múltiplos formatos
            - ✅ Visualizações interativas
            - ✅ Relatório HTML completo
            - ✅ Metadados e documentação
            - ✅ Arquivo README com instruções
        """)
        
        # Seleção de datasets
        st.markdown("##### Selecione os Datasets:")
        
        col1, col2 = st.columns(2)
        
        with col1:
            ds_carga = st.checkbox("💡 Carga de Energia", value=True, key="pkg_carga")
            ds_cmo = st.checkbox("💰 CMO/PLD", value=True, key="pkg_cmo")
            ds_bandeiras = st.checkbox("🚦 Bandeiras Tarifárias", value=True, key="pkg_bandeiras")
        
        with col2:
            ds_geracao = st.checkbox("⚡ Geração por Fonte", value=False, key="pkg_geracao")
            ds_reserv = st.checkbox("💧 Reservatórios", value=False, key="pkg_reserv")
            ds_intercambio = st.checkbox("🔄 Intercâmbio", value=False, key="pkg_intercambio")
        
        # Opções adicionais
        st.markdown("##### Opções Adicionais:")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            compress_level = st.select_slider(
                "Nível de Compressão:",
                options=["Baixo", "Médio", "Alto"],
                value="Médio",
                key="compress_level"
            )
        
        with col2:
            include_raw = st.checkbox("Incluir dados brutos", value=False)
            include_processed = st.checkbox("Incluir dados processados", value=True)
        
        with col3:
            encrypt = st.checkbox("Criptografar pacote", value=False)
            if encrypt:
                password = st.text_input("Senha:", type="password", key="pkg_password")
        
        # Estimativa de tamanho
        selected_count = sum([ds_carga, ds_cmo, ds_bandeiras, ds_geracao, ds_reserv, ds_intercambio])
        estimated_size = selected_count * np.random.randint(100, 500)  # KB simulado
        
        st.markdown(f"""
            <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 20px 0;">
                <h5>📊 Resumo do Pacote</h5>
                <p><strong>Datasets selecionados:</strong> {selected_count}</p>
                <p><strong>Tamanho estimado:</strong> ~{estimated_size} KB</p>
                <p><strong>Formato:</strong> ZIP compactado</p>
            </div>
        """, unsafe_allow_html=True)
        
        # Botão de geração
        if st.button("🎁 Gerar Pacote Completo", type="primary", key="generate_package"):
            with st.spinner("Preparando pacote completo..."):
                # Simular criação do pacote
                progress = st.progress(0)
                
                for i in range(101):
                    progress.progress(i)
                    if i == 25:
                        st.text("📊 Coletando datasets...")
                    elif i == 50:
                        st.text("📈 Gerando visualizações...")
                    elif i == 75:
                        st.text("📝 Criando documentação...")
                    elif i == 90:
                        st.text("📦 Compactando arquivos...")
                
                # Criar pacote (simulado)
                datasets = {}
                if ds_carga:
                    datasets['carga_energia'] = sample_data
                if ds_cmo:
                    datasets['cmo_pld'] = sample_data
                
                package = export_manager.create_report_package(
                    datasets,
                    metadata={'title': 'Pacote Completo AIDE', 'created_by': report_author}
                )
                
                st.success("✅ Pacote completo gerado com sucesso!")
                
                st.download_button(
                    label="📥 Baixar Pacote ZIP",
                    data=package,
                    file_name=f"aide_package_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                    mime="application/zip"
                )
    
    # Histórico de exportações
    with st.expander("📜 Histórico de Exportações"):
        history_data = pd.DataFrame({
            'Data/Hora': [
                datetime.now() - timedelta(hours=i) 
                for i in range(5)
            ],
            'Tipo': ['Excel', 'CSV', 'Relatório HTML', 'Pacote ZIP', 'JSON'],
            'Dataset': ['Carga de Energia', 'CMO/PLD', 'Completo', 'Múltiplos', 'Bandeiras'],
            'Tamanho': ['2.3 MB', '456 KB', '1.2 MB', '5.8 MB', '234 KB'],
            'Status': ['✅ Concluído'] * 5
        })
        
        st.dataframe(history_data, use_container_width=True, hide_index=True)

# Função auxiliar para scheduling de exportações
def schedule_export(frequency: str, config: Dict) -> bool:
    """Agenda exportação automática"""
    schedules = {
        'Diário': '00:00',
        'Semanal': 'Segunda-feira 00:00',
        'Mensal': 'Dia 1, 00:00'
    }
    
    if frequency in schedules:
        st.success(f"✅ Exportação agendada para: {schedules[frequency]}")
        return True
    return False

# Exportar classes e funções
__all__ = ['ExportManager', 'render_export_interface', 'schedule_export']