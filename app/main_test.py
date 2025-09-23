"""
Teste simples para verificar se Streamlit funciona
"""

import streamlit as st
import sys
from pathlib import Path

# Adicionar o diretório app ao path
sys.path.append(str(Path(__file__).parent))

def main():
    """Função principal de teste"""
    
    # Configuração da página
    st.set_page_config(
        page_title="ASPI - Teste",
        page_icon="⚡",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Título principal
    st.title("⚡ ASPI - Teste de Funcionamento")
    
    # Teste básico
    st.write("Se você está vendo esta mensagem, o Streamlit está funcionando!")
    
    # Teste de sidebar
    with st.sidebar:
        st.markdown("### Sidebar Teste")
        teste_input = st.text_input("Digite algo:")
        if teste_input:
            st.write(f"Você digitou: {teste_input}")
    
    # Teste de componentes básicos
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Coluna 1")
        st.button("Botão Teste")
        st.selectbox("Selecione uma opção", ["Opção 1", "Opção 2", "Opção 3"])
    
    with col2:
        st.markdown("#### Coluna 2")
        st.slider("Slider teste", 0, 100, 50)
        st.checkbox("Checkbox teste")
    
    # Teste de importação
    st.markdown("---")
    st.markdown("### Teste de Importações")
    
    import_results = {}
    
    # Teste imports principais
    try:
        from services.data_service import DataService
        import_results["DataService"] = "✅ OK"
    except Exception as e:
        import_results["DataService"] = f"❌ Erro: {e}"
    
    try:
        from components.sidebar import render_sidebar
        import_results["render_sidebar"] = "✅ OK"
    except Exception as e:
        import_results["render_sidebar"] = f"❌ Erro: {e}"
    
    try:
        from components.chat import render_chat_interface
        import_results["render_chat_interface"] = "✅ OK"
    except Exception as e:
        import_results["render_chat_interface"] = f"❌ Erro: {e}"
    
    # Mostrar resultados
    for component, status in import_results.items():
        st.write(f"**{component}**: {status}")

if __name__ == "__main__":
    main()