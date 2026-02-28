"""Página de Análise de Exames."""

import streamlit as st
from datetime import datetime
from typing import Dict, Any
from florence.ui.utils.api_client import FlorenceAPIClient
from florence.ui.utils.cache import get_cached_resources
from florence.ui.config import API_BASE_URL
from florence.ui.components.charts import create_lab_bar_chart, create_gauge_chart, create_radar_chart
from florence.ui.components.tables import interpretation_table, correlation_table, protocol_table, history_table


# Configuração da página
st.set_page_config(
    page_title="Análise - Florence",
    page_icon="🔬",
    layout="wide",
)


def init_session_state():
    """Inicializa session state."""
    if "api_client" not in st.session_state:
        st.session_state.api_client = FlorenceAPIClient(API_BASE_URL)
    
    if "analysis_history" not in st.session_state:
        st.session_state.analysis_history = []
    
    if "current_analysis" not in st.session_state:
        st.session_state.current_analysis = None


def render_input_form():
    """Renderiza formulário de entrada."""
    st.subheader("📝 Dados do Paciente e Exames")
    
    # Patient ID
    patient_id = st.text_input(
        "ID do Paciente",
        placeholder="Ex: PAC-12345",
        help="Identificador único do paciente"
    )
    
    # Obter recursos disponíveis
    try:
        resources = get_cached_resources(st.session_state.api_client)
        available_labs = resources.get("labs", [])
    except Exception:
        st.error("❌ Erro ao carregar recursos da API")
        available_labs = []
    
    # Seleção de exames
    selected_labs = st.multiselect(
        "Selecione os Exames",
        options=available_labs,
        help="Escolha os exames que deseja analisar"
    )
    
    # Inputs de valores
    lab_values = {}
    
    if selected_labs:
        st.markdown("### 🔢 Valores dos Exames")
        
        # Criar colunas para inputs
        num_cols = 3
        cols = st.columns(num_cols)
        
        for i, lab in enumerate(selected_labs):
            col_idx = i % num_cols
            with cols[col_idx]:
                value = st.number_input(
                    lab,
                    min_value=0.0,
                    step=0.1,
                    format="%.2f",
                    key=f"lab_{lab}"
                )
                lab_values[lab] = value
    
    # Opções de análise
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        include_rag = st.checkbox(
            "🤖 Incluir Consulta RAG",
            value=False,
            help="Consultar protocolos clínicos relevantes"
        )
    
    with col2:
        rag_query = None
        if include_rag:
            rag_query = st.text_input(
                "Query RAG (opcional)",
                placeholder="Ex: protocolo para diabetes",
                help="Deixe vazio para auto-geração"
            )
    
    # Botão de análise
    st.markdown("---")
    analyze_button = st.button("🔬 Analisar", type="primary", use_container_width=True)
    
    return patient_id, lab_values, include_rag, rag_query, analyze_button


def perform_analysis(patient_id: str, lab_values: Dict[str, float], 
                     include_rag: bool, rag_query: str = None):
    """Executa análise."""
    if not patient_id:
        st.error("❌ Por favor, informe o ID do paciente")
        return None
    
    if not lab_values:
        st.error("❌ Por favor, selecione e informe valores para os exames")
        return None
    
    try:
        with st.spinner("🔄 Analisando..."):
            if include_rag:
                # Análise com RAG
                result = st.session_state.api_client.analyze_with_rag(
                    patient_id=patient_id,
                    results=lab_values,
                    rag_query=rag_query if rag_query else None
                )
            else:
                # Análise simples
                result = st.session_state.api_client.analyze_labs(
                    patient_id=patient_id,
                    results=lab_values
                )
            
            # Adicionar timestamp
            result["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            result["patient_id"] = patient_id
            result["results"] = lab_values
            
            return result
    
    except Exception as e:
        st.error(f"❌ Erro na análise: {str(e)}")
        return None


def render_results(analysis: Dict[str, Any]):
    """Renderiza resultados da análise."""
    if not analysis:
        return
    
    st.markdown("---")
    st.subheader("📊 Resultados da Análise")
    
    # Interpretações
    st.markdown("### 🔬 Interpretações dos Exames")
    interpretations = analysis.get("interpretations", [])
    interpretation_table(interpretations)
    
    # Gráfico de barras
    if interpretations:
        st.plotly_chart(create_lab_bar_chart(interpretations), use_container_width=True)
    
    # Correlações
    st.markdown("---")
    st.markdown("### 🔗 Correlações Clínicas Detectadas")
    correlations = analysis.get("correlations", [])
    correlation_table(correlations)
    
    # Protocolos RAG (se disponível)
    if "rag_results" in analysis:
        st.markdown("---")
        st.markdown("### 🤖 Protocolos Clínicos Relevantes")
        
        rag_results = analysis.get("rag_results", {})
        protocols = rag_results.get("protocols", [])
        
        if protocols:
            protocol_table(protocols)
        else:
            st.info("Nenhum protocolo encontrado")


def main():
    """Função principal da página."""
    init_session_state()
    
    st.title("🔬 Análise de Exames Laboratoriais")
    
    # Formulário de entrada
    patient_id, lab_values, include_rag, rag_query, analyze_button = render_input_form()
    
    # Executar análise
    if analyze_button:
        result = perform_analysis(patient_id, lab_values, include_rag, rag_query)
        
        if result:
            st.session_state.current_analysis = result
            # Adicionar ao histórico
            st.session_state.analysis_history.insert(0, result)
            # Limitar histórico a 10 análises
            st.session_state.analysis_history = st.session_state.analysis_history[:10]
            st.success("✅ Análise concluída com sucesso!")
    
    # Exibir resultados
    if st.session_state.current_analysis:
        render_results(st.session_state.current_analysis)
    
    # Histórico
    if st.session_state.analysis_history:
        st.markdown("---")
        with st.expander("📜 Histórico de Análises", expanded=False):
            history_table(st.session_state.analysis_history)


if __name__ == "__main__":
    main()

