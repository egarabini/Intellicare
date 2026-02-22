"""Página de Exportação de Relatórios."""

import streamlit as st
import pandas as pd
import json
from datetime import datetime
from typing import Dict, Any
from florence.ui.config import API_BASE_URL


# Configuração da página
st.set_page_config(
    page_title="Relatórios - Florence",
    page_icon="📄",
    layout="wide",
)


def init_session_state():
    """Inicializa session state."""
    if "analysis_history" not in st.session_state:
        st.session_state.analysis_history = []


def export_to_excel(analysis: Dict[str, Any]) -> bytes:
    """Exporta análise para Excel."""
    # Criar DataFrames
    interpretations = pd.DataFrame(analysis.get("interpretations", []))
    correlations = pd.DataFrame(analysis.get("correlations", []))
    
    # Criar Excel em memória
    from io import BytesIO
    output = BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Sheet 1: Informações gerais
        info_df = pd.DataFrame({
            "Campo": ["Patient ID", "Data/Hora", "Número de Exames"],
            "Valor": [
                analysis.get("patient_id", "N/A"),
                analysis.get("timestamp", "N/A"),
                len(analysis.get("results", {}))
            ]
        })
        info_df.to_excel(writer, sheet_name='Informações', index=False)
        
        # Sheet 2: Interpretações
        if not interpretations.empty:
            interpretations.to_excel(writer, sheet_name='Interpretações', index=False)
        
        # Sheet 3: Correlações
        if not correlations.empty:
            correlations.to_excel(writer, sheet_name='Correlações', index=False)
        
        # Sheet 4: Resultados brutos
        results_df = pd.DataFrame(list(analysis.get("results", {}).items()), 
                                 columns=["Exame", "Valor"])
        results_df.to_excel(writer, sheet_name='Resultados', index=False)
    
    output.seek(0)
    return output.getvalue()


def export_to_json(analysis: Dict[str, Any]) -> str:
    """Exporta análise para JSON."""
    return json.dumps(analysis, indent=2, ensure_ascii=False)


def generate_pdf_content(analysis: Dict[str, Any]) -> str:
    """Gera conteúdo HTML para PDF."""
    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            h1 {{ color: #0066cc; }}
            h2 {{ color: #333; border-bottom: 2px solid #0066cc; }}
            table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #0066cc; color: white; }}
            .normal {{ color: green; }}
            .warning {{ color: orange; }}
            .critical {{ color: red; }}
        </style>
    </head>
    <body>
        <h1>Florence - Relatório de Análise Clínica</h1>
        
        <h2>Informações do Paciente</h2>
        <p><strong>Patient ID:</strong> {analysis.get('patient_id', 'N/A')}</p>
        <p><strong>Data/Hora:</strong> {analysis.get('timestamp', 'N/A')}</p>
        
        <h2>Interpretações dos Exames</h2>
        <table>
            <tr>
                <th>Exame</th>
                <th>Valor</th>
                <th>Referência</th>
                <th>Status</th>
            </tr>
    """
    
    for interp in analysis.get("interpretations", []):
        status_class = "normal" if interp.get("status") == "normal" else "warning"
        html += f"""
            <tr>
                <td>{interp.get('lab_name', '')}</td>
                <td>{interp.get('value', '')} {interp.get('unit', '')}</td>
                <td>{interp.get('reference_min', '')} - {interp.get('reference_max', '')} {interp.get('unit', '')}</td>
                <td class="{status_class}">{interp.get('status', '').upper()}</td>
            </tr>
        """
    
    html += """
        </table>
        
        <h2>Correlações Detectadas</h2>
        <ul>
    """
    
    for corr in analysis.get("correlations", []):
        html += f"<li><strong>{corr.get('pattern_name', '')}</strong>: {corr.get('description', '')}</li>"
    
    html += """
        </ul>
    </body>
    </html>
    """
    
    return html


def render_export_section():
    """Renderiza seção de exportação."""
    st.subheader("📤 Exportar Análise")
    
    if not st.session_state.analysis_history:
        st.info("Nenhuma análise disponível para exportação. Realize uma análise primeiro.")
        return
    
    # Seleção de análise
    analysis_options = [
        f"{a.get('timestamp', 'N/A')} - {a.get('patient_id', 'N/A')}"
        for a in st.session_state.analysis_history
    ]
    
    selected_idx = st.selectbox(
        "Selecione a Análise",
        options=range(len(analysis_options)),
        format_func=lambda i: analysis_options[i]
    )
    
    selected_analysis = st.session_state.analysis_history[selected_idx]
    
    # Preview
    with st.expander("👁️ Preview da Análise", expanded=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Patient ID", selected_analysis.get("patient_id", "N/A"))
        
        with col2:
            st.metric("Data/Hora", selected_analysis.get("timestamp", "N/A"))
        
        with col3:
            st.metric("Exames", len(selected_analysis.get("results", {})))
        
        # Tabela de interpretações
        interpretations = selected_analysis.get("interpretations", [])
        if interpretations:
            df = pd.DataFrame(interpretations)
            st.dataframe(df, use_container_width=True)
    
    # Botões de exportação
    st.markdown("---")
    st.markdown("### 📥 Formatos de Exportação")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Excel
        excel_data = export_to_excel(selected_analysis)
        st.download_button(
            label="📊 Exportar Excel",
            data=excel_data,
            file_name=f"florence_analise_{selected_analysis.get('patient_id', 'unknown')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    
    with col2:
        # JSON
        json_data = export_to_json(selected_analysis)
        st.download_button(
            label="📋 Exportar JSON",
            data=json_data,
            file_name=f"florence_analise_{selected_analysis.get('patient_id', 'unknown')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            use_container_width=True
        )
    
    with col3:
        # PDF (HTML)
        pdf_html = generate_pdf_content(selected_analysis)
        st.download_button(
            label="📄 Exportar HTML",
            data=pdf_html,
            file_name=f"florence_analise_{selected_analysis.get('patient_id', 'unknown')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
            mime="text/html",
            use_container_width=True
        )


def main():
    """Função principal da página."""
    init_session_state()
    
    st.title("📄 Exportação de Relatórios")
    
    st.markdown("""
    Exporte suas análises em diferentes formatos:
    
    - 📊 **Excel**: Planilha com múltiplas abas (informações, interpretações, correlações, resultados)
    - 📋 **JSON**: Formato estruturado para integração com outros sistemas
    - 📄 **HTML**: Relatório formatado para impressão ou conversão para PDF
    """)
    
    st.markdown("---")
    
    render_export_section()


if __name__ == "__main__":
    main()

