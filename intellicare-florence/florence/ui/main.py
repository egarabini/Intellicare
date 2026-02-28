"""Florence UI - Aplicação Principal.

Interface web para análise clínica com Florence.
"""

import streamlit as st
from florence.ui.config import (
    PAGE_TITLE,
    PAGE_ICON,
    LAYOUT,
    INITIAL_SIDEBAR_STATE,
    API_BASE_URL,
)
from florence.ui.utils.api_client import FlorenceAPIClient
from florence.ui.utils.cache import get_cached_health, get_cached_info


# Configuração da página
st.set_page_config(
    page_title=PAGE_TITLE,
    page_icon=PAGE_ICON,
    layout=LAYOUT,
    initial_sidebar_state=INITIAL_SIDEBAR_STATE,
)


def init_session_state():
    """Inicializa session state."""
    if "api_client" not in st.session_state:
        st.session_state.api_client = FlorenceAPIClient(API_BASE_URL)
    
    if "analysis_history" not in st.session_state:
        st.session_state.analysis_history = []


def render_sidebar():
    """Renderiza sidebar com navegação e informações."""
    with st.sidebar:
        st.image("https://via.placeholder.com/200x80/0066cc/ffffff?text=Florence", use_column_width=True)
        
        st.markdown("---")
        
        st.markdown("### 🏥 Florence")
        st.markdown("**Análise Clínica Inteligente**")
        
        st.markdown("---")
        
        # Status da API
        st.markdown("### 📡 Status da API")
        try:
            health = get_cached_health(st.session_state.api_client)
            if health.get("status") == "healthy":
                st.success("✅ API Online")
            else:
                st.warning("⚠️ API com problemas")
        except Exception as e:
            st.error("❌ API Offline")
            st.caption(f"Erro: {str(e)}")
        
        st.markdown("---")
        
        # Informações do módulo
        st.markdown("### ℹ️ Informações")
        try:
            info = get_cached_info(st.session_state.api_client)
            st.caption(f"**Versão**: {info.get('version', 'N/A')}")
            st.caption(f"**Módulo**: {info.get('module_name', 'N/A')}")
        except Exception:
            st.caption("Informações indisponíveis")
        
        st.markdown("---")
        
        # Links úteis
        st.markdown("### 📚 Documentação")
        st.markdown("[📖 Guia de Uso](docs/GUIA_USO_FLORENCE.md)")
        st.markdown("[🔌 API Reference](docs/API_REFERENCE.md)")
        st.markdown("[🤖 RAG Protocolos](docs/RAG_PROTOCOLOS.md)")
        
        st.markdown("---")
        
        # Configurações
        st.markdown("### ⚙️ Configurações")
        st.caption(f"**API URL**: {API_BASE_URL}")
        
        if st.button("🔄 Limpar Cache"):
            from florence.ui.utils.cache import clear_all_caches
            clear_all_caches()
            st.success("Cache limpo!")
            st.rerun()


def main():
    """Função principal da aplicação."""
    # Inicializar session state
    init_session_state()
    
    # Renderizar sidebar
    render_sidebar()
    
    # Conteúdo principal
    st.title("🏥 Florence - Análise Clínica")
    
    st.markdown("""
    Bem-vindo ao **Florence**, o módulo de análise clínica inteligente do IntelliCare.
    
    ### 🎯 Funcionalidades
    
    - **🏠 Home**: Dashboard com visão geral e KPIs
    - **🔬 Análise**: Interpretação de exames laboratoriais
    - **📈 Tendências**: Visualização de tendências temporais
    - **🤖 RAG**: Consulta a protocolos clínicos
    - **📄 Relatórios**: Exportação de análises
    
    ### 🚀 Como Usar
    
    1. Navegue pelas páginas usando o menu lateral
    2. Insira os dados dos exames
    3. Visualize as análises e interpretações
    4. Consulte protocolos clínicos relevantes
    5. Exporte relatórios em PDF ou Excel
    
    ### 📊 Recursos Disponíveis
    
    - **27 exames** laboratoriais suportados
    - **6 painéis** clínicos (Hemograma, Metabólico, Lipídico, Hepático, Renal, Tireoidiano)
    - **8 padrões** de correlação clínica
    - **10 protocolos** clínicos indexados (RAG)
    
    ### ⚠️ Aviso Importante
    
    **Florence é uma ferramenta de SUPORTE DIAGNÓSTICO, NÃO substitui um médico.**
    
    - ✅ Use para auxiliar na interpretação de exames
    - ✅ Use para detectar padrões clínicos
    - ✅ Use para consultar protocolos baseados em evidências
    - ❌ NÃO use como única fonte de decisão clínica
    - ❌ NÃO use sem supervisão de profissional qualificado
    
    ---
    
    **Versão**: 1.0.0  
    **Última Atualização**: 2026-02-24
    """)
    
    # Quick stats
    st.markdown("---")
    st.subheader("📊 Estatísticas Rápidas")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Análises Hoje", "0", "0")
    
    with col2:
        st.metric("Exames Críticos", "0", "0")
    
    with col3:
        st.metric("Protocolos RAG", "10", "0")
    
    with col4:
        st.metric("Tempo Médio", "< 200ms", "0ms")


if __name__ == "__main__":
    main()

