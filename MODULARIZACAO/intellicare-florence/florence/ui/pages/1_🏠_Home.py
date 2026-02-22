"""Página Home - Dashboard Principal."""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from florence.ui.utils.api_client import FlorenceAPIClient
from florence.ui.utils.cache import get_cached_resources, get_cached_protocols
from florence.ui.config import API_BASE_URL, THEME_COLORS


# Configuração da página
st.set_page_config(
    page_title="Home - Florence",
    page_icon="🏠",
    layout="wide",
)


def init_session_state():
    """Inicializa session state."""
    if "api_client" not in st.session_state:
        st.session_state.api_client = FlorenceAPIClient(API_BASE_URL)


def create_status_pie_chart():
    """Cria gráfico de pizza de distribuição de status."""
    # Dados de exemplo (em produção, viriam da API)
    data = {
        "Status": ["Normal", "Borderline", "Anormal", "Crítico"],
        "Quantidade": [65, 20, 12, 3]
    }
    
    fig = px.pie(
        data,
        values="Quantidade",
        names="Status",
        title="Distribuição de Status dos Exames",
        color="Status",
        color_discrete_map={
            "Normal": "#28a745",
            "Borderline": "#ffc107",
            "Anormal": "#dc3545",
            "Crítico": "#6c757d"
        }
    )
    
    fig.update_traces(textposition='inside', textinfo='percent+label')
    
    return fig


def create_analyses_timeline():
    """Cria gráfico de linha de análises por dia."""
    # Dados de exemplo (últimos 30 dias)
    dates = [(datetime.now() - timedelta(days=i)).strftime("%d/%m") for i in range(29, -1, -1)]
    values = [12, 15, 10, 18, 22, 19, 25, 20, 17, 23, 28, 24, 21, 26, 30, 
              27, 25, 29, 32, 28, 26, 31, 35, 30, 28, 33, 36, 32, 30, 34]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=dates,
        y=values,
        mode='lines+markers',
        name='Análises',
        line=dict(color=THEME_COLORS["primary"], width=2),
        marker=dict(size=6)
    ))
    
    fig.update_layout(
        title="Análises Realizadas (Últimos 30 Dias)",
        xaxis_title="Data",
        yaxis_title="Quantidade",
        hovermode='x unified'
    )
    
    return fig


def create_top_exams_chart():
    """Cria gráfico de barras dos exames mais solicitados."""
    # Dados de exemplo
    exams = ["Hemoglobina", "Glicemia", "Creatinina", "Colesterol", "TSH"]
    counts = [145, 132, 98, 87, 76]
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=counts,
        y=exams,
        orientation='h',
        marker=dict(color=THEME_COLORS["primary"])
    ))
    
    fig.update_layout(
        title="Top 5 Exames Mais Solicitados",
        xaxis_title="Quantidade",
        yaxis_title="Exame",
        height=300
    )
    
    return fig


def main():
    """Função principal da página."""
    init_session_state()
    
    st.title("🏠 Dashboard - Visão Geral")
    
    st.markdown("---")
    
    # KPIs principais
    st.subheader("📊 Indicadores Principais")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="📋 Total de Análises",
            value="1.234",
            delta="+45 hoje",
            delta_color="normal"
        )
    
    with col2:
        st.metric(
            label="🔴 Exames Críticos",
            value="12",
            delta="+3 hoje",
            delta_color="inverse"
        )
    
    with col3:
        st.metric(
            label="🤖 Protocolos RAG",
            value="10",
            delta="0",
            delta_color="off"
        )
    
    with col4:
        st.metric(
            label="⚡ Tempo Médio",
            value="185ms",
            delta="-15ms",
            delta_color="normal"
        )
    
    st.markdown("---")
    
    # Gráficos principais
    col1, col2 = st.columns(2)
    
    with col1:
        st.plotly_chart(create_analyses_timeline(), use_container_width=True)
    
    with col2:
        st.plotly_chart(create_status_pie_chart(), use_container_width=True)
    
    st.markdown("---")
    
    # Recursos disponíveis
    st.subheader("📚 Recursos Disponíveis")
    
    try:
        resources = get_cached_resources(st.session_state.api_client)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.info(f"**🔬 Exames**: {len(resources.get('labs', []))}")
        
        with col2:
            st.info(f"**📊 Painéis**: {len(resources.get('panels', []))}")
        
        with col3:
            st.info(f"**🔗 Correlações**: {len(resources.get('correlations', []))}")
    
    except Exception as e:
        st.error(f"❌ Erro ao carregar recursos: {str(e)}")
    
    st.markdown("---")
    
    # Top exames
    st.plotly_chart(create_top_exams_chart(), use_container_width=True)


if __name__ == "__main__":
    main()

