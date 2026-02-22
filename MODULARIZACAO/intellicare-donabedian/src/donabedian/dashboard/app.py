"""
IntelliCare Donabedian Dashboard.

Main Streamlit application for quality assessment visualization.
"""

import streamlit as st
from donabedian.dashboard import config
from donabedian.dashboard.api_client import DonabedianAPIClient


# Page configuration
st.set_page_config(
    page_title=config.PAGE_TITLE,
    page_icon=config.PAGE_ICON,
    layout=config.LAYOUT,
    initial_sidebar_state=config.INITIAL_SIDEBAR_STATE,
)


# Initialize API client
@st.cache_resource
def get_api_client() -> DonabedianAPIClient:
    """Get cached API client instance."""
    return DonabedianAPIClient(config.API_BASE_URL)


# Custom CSS
def load_custom_css():
    """Load custom CSS styles."""
    st.markdown("""
        <style>
        /* Main container */
        .main {
            padding: 1rem;
        }
        
        /* Metric cards */
        .metric-card {
            background-color: #f8f9fa;
            border-radius: 0.5rem;
            padding: 1rem;
            margin: 0.5rem 0;
        }
        
        /* Status badges */
        .status-green {
            background-color: #28a745;
            color: white;
            padding: 0.25rem 0.5rem;
            border-radius: 0.25rem;
            font-weight: bold;
        }
        
        .status-yellow {
            background-color: #ffc107;
            color: black;
            padding: 0.25rem 0.5rem;
            border-radius: 0.25rem;
            font-weight: bold;
        }
        
        .status-red {
            background-color: #dc3545;
            color: white;
            padding: 0.25rem 0.5rem;
            border-radius: 0.25rem;
            font-weight: bold;
        }
        
        /* Headers */
        h1 {
            color: #007bff;
            margin-bottom: 1rem;
        }
        
        h2 {
            color: #6c757d;
            margin-top: 1.5rem;
            margin-bottom: 1rem;
        }
        
        /* Sidebar */
        .css-1d391kg {
            padding-top: 1rem;
        }
        </style>
    """, unsafe_allow_html=True)


def check_api_connection():
    """Check API connection and display status."""
    try:
        client = get_api_client()
        health = client.get_health()
        
        if health.get("status") == "healthy":
            st.sidebar.success("✅ API Conectada")
            return True
        else:
            st.sidebar.error("❌ API com problemas")
            return False
    except Exception as e:
        st.sidebar.error(f"❌ Erro ao conectar: {str(e)}")
        return False


def main():
    """Main application entry point."""
    # Load custom CSS
    load_custom_css()
    
    # Sidebar
    st.sidebar.title("🏥 IntelliCare Donabedian")
    st.sidebar.markdown("---")
    
    # Check API connection
    api_connected = check_api_connection()
    
    if not api_connected:
        st.warning("⚠️ Não foi possível conectar à API. Verifique se o serviço está rodando.")
        st.info(f"URL da API: `{config.API_BASE_URL}`")
        st.code("docker compose up -d", language="bash")
        return
    
    # Main content
    st.title("📊 Dashboard de Qualidade Donabedian")
    
    st.markdown("""
    Bem-vindo ao **Dashboard de Avaliação de Qualidade** baseado no framework de **Avedis Donabedian**.
    
    Este dashboard permite visualizar e analisar a qualidade dos serviços de saúde através de:
    
    - **7 Pilares de Qualidade**: Eficácia, Efetividade, Eficiência, Otimidade, Aceitabilidade, Legitimidade, Equidade
    - **Tríade de Donabedian**: Estrutura → Processo → Resultado
    - **Indicadores de Qualidade**: Métricas específicas com metas e status
    - **Análise Temporal**: Tendências e evolução ao longo do tempo
    """)
    
    st.markdown("---")
    
    # Quick stats
    st.subheader("📈 Navegação")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.info("🏠 **Home**\nVisão geral e KPIs")
    
    with col2:
        st.info("📊 **Pilares**\nAnálise dos 7 pilares")
    
    with col3:
        st.info("📈 **Indicadores**\nDetalhamento de métricas")
    
    with col4:
        st.info("📉 **Trends**\nAnálise temporal")
    
    st.markdown("---")
    
    st.markdown("""
    ### 🚀 Como usar
    
    1. Use o menu lateral para navegar entre as páginas
    2. Selecione o período de análise desejado
    3. Explore os gráficos interativos
    4. Exporte os dados quando necessário
    
    ### 📚 Sobre o Framework Donabedian
    
    O framework de Donabedian é um modelo clássico de avaliação de qualidade em saúde que considera três dimensões:
    
    - **Estrutura**: Recursos disponíveis (instalações, equipamentos, pessoal)
    - **Processo**: Atividades realizadas (procedimentos, protocolos)
    - **Resultado**: Efeitos sobre a saúde dos pacientes
    
    Os **7 Pilares de Qualidade** (Donabedian, 1990) complementam essa visão:
    
    1. **Eficácia**: Capacidade de produzir melhorias na saúde
    2. **Efetividade**: Grau em que melhorias são alcançadas
    3. **Eficiência**: Custo-benefício das melhorias
    4. **Otimidade**: Equilíbrio entre benefícios e custos
    5. **Aceitabilidade**: Conformidade com preferências dos pacientes
    6. **Legitimidade**: Conformidade com preferências sociais
    7. **Equidade**: Distribuição justa dos serviços
    """)


if __name__ == "__main__":
    main()

