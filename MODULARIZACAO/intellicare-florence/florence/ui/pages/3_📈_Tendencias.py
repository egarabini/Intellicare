"""Página de Visualização de Tendências."""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from typing import Dict, Any, List
from florence.ui.utils.api_client import FlorenceAPIClient
from florence.ui.config import API_BASE_URL, THEME_COLORS
from florence.ui.components.charts import create_trend_line_chart


# Configuração da página
st.set_page_config(
    page_title="Tendências - Florence",
    page_icon="📈",
    layout="wide",
)


def init_session_state():
    """Inicializa session state."""
    if "api_client" not in st.session_state:
        st.session_state.api_client = FlorenceAPIClient(API_BASE_URL)
    
    if "trend_data" not in st.session_state:
        st.session_state.trend_data = None


def create_sample_template() -> pd.DataFrame:
    """Cria template de exemplo para download."""
    dates = [(datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(30, 0, -1)]
    
    data = {
        "date": dates,
        "patient_id": ["PAC-001"] * 30,
        "hemoglobin": [14.5 + (i % 3) * 0.5 for i in range(30)],
        "glucose": [95 + (i % 5) * 5 for i in range(30)],
        "creatinine": [0.9 + (i % 2) * 0.1 for i in range(30)],
    }
    
    return pd.DataFrame(data)


def render_upload_section():
    """Renderiza seção de upload."""
    st.subheader("📤 Upload de Dados Históricos")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        uploaded_file = st.file_uploader(
            "Selecione arquivo CSV ou Excel",
            type=["csv", "xlsx"],
            help="Arquivo com colunas: date, patient_id, exame1, exame2, ..."
        )
    
    with col2:
        st.markdown("### 📥 Template")
        template_df = create_sample_template()
        
        csv = template_df.to_csv(index=False)
        st.download_button(
            label="⬇️ Baixar Template CSV",
            data=csv,
            file_name="template_tendencias.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    if uploaded_file:
        try:
            # Ler arquivo
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
            
            # Validar colunas obrigatórias
            required_cols = ["date", "patient_id"]
            missing_cols = [col for col in required_cols if col not in df.columns]
            
            if missing_cols:
                st.error(f"❌ Colunas obrigatórias faltando: {', '.join(missing_cols)}")
                return None
            
            # Converter data
            df["date"] = pd.to_datetime(df["date"])
            
            # Preview
            st.success(f"✅ Arquivo carregado: {len(df)} registros")
            with st.expander("👁️ Preview dos Dados", expanded=True):
                st.dataframe(df.head(10), use_container_width=True)
            
            return df
        
        except Exception as e:
            st.error(f"❌ Erro ao ler arquivo: {str(e)}")
            return None
    
    return None


def render_selection_section(df: pd.DataFrame):
    """Renderiza seção de seleção."""
    st.markdown("---")
    st.subheader("🎯 Seleção de Análise")
    
    # Obter colunas de exames (excluir date e patient_id)
    exam_cols = [col for col in df.columns if col not in ["date", "patient_id"]]
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        selected_exams = st.multiselect(
            "Exames para Análise",
            options=exam_cols,
            default=exam_cols[:3] if len(exam_cols) >= 3 else exam_cols,
            help="Selecione até 5 exames"
        )
    
    with col2:
        # Filtro de período
        min_date = df["date"].min().date()
        max_date = df["date"].max().date()
        
        date_range = st.date_input(
            "Período",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date,
            help="Selecione o período para análise"
        )
    
    with col3:
        aggregation = st.selectbox(
            "Agregação",
            options=["Diário", "Semanal", "Mensal"],
            help="Nível de agregação dos dados"
        )
    
    return selected_exams, date_range, aggregation


def create_multi_line_chart(df: pd.DataFrame, exams: List[str]) -> go.Figure:
    """Cria gráfico de linhas múltiplas."""
    fig = go.Figure()
    
    for exam in exams:
        fig.add_trace(go.Scatter(
            x=df["date"],
            y=df[exam],
            mode='lines+markers',
            name=exam,
            line=dict(width=2),
            marker=dict(size=6)
        ))
    
    fig.update_layout(
        title="Evolução Temporal dos Exames",
        xaxis_title="Data",
        yaxis_title="Valor",
        hovermode='x unified',
        height=500
    )
    
    return fig


def create_heatmap(df: pd.DataFrame, exams: List[str]) -> go.Figure:
    """Cria heatmap de correlação."""
    # Calcular correlação
    corr_matrix = df[exams].corr()
    
    fig = go.Figure(data=go.Heatmap(
        z=corr_matrix.values,
        x=corr_matrix.columns,
        y=corr_matrix.columns,
        colorscale='RdBu',
        zmid=0,
        text=corr_matrix.values.round(2),
        texttemplate='%{text}',
        textfont={"size": 10},
    ))
    
    fig.update_layout(
        title="Correlação entre Exames",
        height=400
    )
    
    return fig


def create_box_plot(df: pd.DataFrame, exams: List[str]) -> go.Figure:
    """Cria box plot de distribuição."""
    fig = go.Figure()
    
    for exam in exams:
        fig.add_trace(go.Box(
            y=df[exam],
            name=exam,
            boxmean='sd'
        ))
    
    fig.update_layout(
        title="Distribuição dos Valores",
        yaxis_title="Valor",
        height=400
    )
    
    return fig


def main():
    """Função principal da página."""
    init_session_state()
    
    st.title("📈 Visualização de Tendências")
    
    # Upload de dados
    df = render_upload_section()
    
    if df is not None:
        # Seleção
        selected_exams, date_range, aggregation = render_selection_section(df)
        
        if selected_exams:
            # Filtrar dados
            if len(date_range) == 2:
                mask = (df["date"].dt.date >= date_range[0]) & (df["date"].dt.date <= date_range[1])
                filtered_df = df[mask]
            else:
                filtered_df = df
            
            # Gráficos
            st.markdown("---")
            st.subheader("📊 Visualizações")
            
            # Line chart
            st.plotly_chart(create_multi_line_chart(filtered_df, selected_exams), use_container_width=True)
            
            # Heatmap e Box plot
            col1, col2 = st.columns(2)
            
            with col1:
                st.plotly_chart(create_heatmap(filtered_df, selected_exams), use_container_width=True)
            
            with col2:
                st.plotly_chart(create_box_plot(filtered_df, selected_exams), use_container_width=True)


if __name__ == "__main__":
    main()

