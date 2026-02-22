"""Componentes de tabelas reutilizáveis."""

import streamlit as st
import pandas as pd
from typing import List, Dict, Any
from florence.ui.utils.formatters import (
    get_status_emoji,
    format_lab_value,
    format_reference_range,
    format_protocol_score
)


def interpretation_table(interpretations: List[Dict[str, Any]]):
    """Renderiza tabela de interpretações.
    
    Args:
        interpretations: Lista de interpretações
    """
    if not interpretations:
        st.info("Nenhuma interpretação disponível")
        return
    
    # Preparar dados
    data = []
    for interp in interpretations:
        lab_name = interp.get("lab_name", "")
        value = interp.get("value", 0)
        unit = interp.get("unit", "")
        status = interp.get("status", "normal")
        min_ref = interp.get("reference_min", 0)
        max_ref = interp.get("reference_max", 0)
        
        data.append({
            "Status": get_status_emoji(status),
            "Exame": lab_name,
            "Valor": format_lab_value(value, unit),
            "Referência": format_reference_range(min_ref, max_ref, unit),
            "Classificação": status.upper()
        })
    
    df = pd.DataFrame(data)
    
    # Renderizar tabela
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Status": st.column_config.TextColumn("", width="small"),
            "Exame": st.column_config.TextColumn("Exame", width="medium"),
            "Valor": st.column_config.TextColumn("Valor", width="small"),
            "Referência": st.column_config.TextColumn("Referência", width="medium"),
            "Classificação": st.column_config.TextColumn("Status", width="small"),
        }
    )


def correlation_table(correlations: List[Dict[str, Any]]):
    """Renderiza tabela de correlações.
    
    Args:
        correlations: Lista de correlações
    """
    if not correlations:
        st.info("Nenhuma correlação detectada")
        return
    
    for corr in correlations:
        pattern_name = corr.get("pattern_name", "")
        description = corr.get("description", "")
        significance = corr.get("significance", "normal")
        labs_involved = corr.get("labs_involved", [])
        
        # Card de correlação
        with st.container():
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"**{pattern_name}**")
                st.caption(description)
                if labs_involved:
                    st.caption(f"Exames: {', '.join(labs_involved)}")
            
            with col2:
                if significance.lower() == "critico":
                    st.error(f"🚨 {significance}")
                elif significance.lower() == "urgente":
                    st.warning(f"🔴 {significance}")
                elif significance.lower() == "atencao":
                    st.info(f"⚠️ {significance}")
                else:
                    st.success(f"✅ {significance}")
            
            st.markdown("---")


def protocol_table(protocols: List[Dict[str, Any]]):
    """Renderiza tabela de protocolos.
    
    Args:
        protocols: Lista de protocolos
    """
    if not protocols:
        st.info("Nenhum protocolo encontrado")
        return
    
    for i, protocol in enumerate(protocols):
        title = protocol.get("title", "")
        score = protocol.get("score", 0.0)
        content = protocol.get("content", "")
        metadata = protocol.get("metadata", {})
        
        with st.expander(f"{i+1}. {title} - {format_protocol_score(score)}"):
            # Metadata
            col1, col2, col3 = st.columns(3)
            
            with col1:
                specialty = metadata.get("specialty", "N/A")
                st.caption(f"**Especialidade**: {specialty}")
            
            with col2:
                version = metadata.get("version", "N/A")
                st.caption(f"**Versão**: {version}")
            
            with col3:
                st.caption(f"**Relevância**: {format_protocol_score(score)}")
            
            st.markdown("---")
            
            # Conteúdo
            st.markdown(content[:500] + "..." if len(content) > 500 else content)
            
            # Botão para ver completo
            if len(content) > 500:
                if st.button(f"Ver protocolo completo", key=f"protocol_{i}"):
                    st.markdown(content)


def history_table(history: List[Dict[str, Any]]):
    """Renderiza tabela de histórico de análises.
    
    Args:
        history: Lista de análises anteriores
    """
    if not history:
        st.info("Nenhuma análise no histórico")
        return
    
    # Preparar dados
    data = []
    for h in history:
        timestamp = h.get("timestamp", "")
        patient_id = h.get("patient_id", "")
        num_labs = len(h.get("results", {}))
        num_abnormal = len([i for i in h.get("interpretations", []) 
                           if i.get("status", "").lower() != "normal"])
        
        data.append({
            "Data/Hora": timestamp,
            "Paciente": patient_id,
            "Exames": num_labs,
            "Anormais": num_abnormal
        })
    
    df = pd.DataFrame(data)
    
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Data/Hora": st.column_config.TextColumn("Data/Hora", width="medium"),
            "Paciente": st.column_config.TextColumn("Paciente", width="small"),
            "Exames": st.column_config.NumberColumn("Exames", width="small"),
            "Anormais": st.column_config.NumberColumn("Anormais", width="small"),
        }
    )

