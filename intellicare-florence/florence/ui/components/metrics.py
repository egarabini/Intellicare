"""Componentes de métricas reutilizáveis."""

import streamlit as st
from typing import Optional


def metric_card(label: str, value: str, delta: Optional[str] = None, 
                delta_color: str = "normal", help_text: Optional[str] = None):
    """Renderiza card de métrica.
    
    Args:
        label: Rótulo da métrica
        value: Valor da métrica
        delta: Variação (opcional)
        delta_color: Cor da variação (normal, inverse, off)
        help_text: Texto de ajuda (opcional)
    """
    st.metric(
        label=label,
        value=value,
        delta=delta,
        delta_color=delta_color,
        help=help_text
    )


def kpi_row(kpis: list):
    """Renderiza linha de KPIs.
    
    Args:
        kpis: Lista de dicionários com {label, value, delta, delta_color, help}
    """
    cols = st.columns(len(kpis))
    
    for col, kpi in zip(cols, kpis):
        with col:
            metric_card(
                label=kpi.get("label", ""),
                value=kpi.get("value", ""),
                delta=kpi.get("delta"),
                delta_color=kpi.get("delta_color", "normal"),
                help_text=kpi.get("help")
            )


def status_badge(status: str) -> str:
    """Retorna badge HTML para status.
    
    Args:
        status: Status do exame
        
    Returns:
        HTML do badge
    """
    status_lower = status.lower()
    
    if status_lower == "normal":
        color = "#28a745"
        emoji = "✅"
    elif status_lower in ["low", "high"]:
        color = "#ffc107"
        emoji = "⚠️"
    elif status_lower in ["critical_low", "critical_high"]:
        color = "#dc3545"
        emoji = "🔴"
    elif status_lower == "panic":
        color = "#6c757d"
        emoji = "🚨"
    else:
        color = "#6c757d"
        emoji = "❓"
    
    return f'<span style="background-color: {color}; color: white; padding: 4px 8px; border-radius: 4px; font-weight: bold;">{emoji} {status.upper()}</span>'


def info_box(title: str, content: str, box_type: str = "info"):
    """Renderiza caixa de informação.
    
    Args:
        title: Título da caixa
        content: Conteúdo
        box_type: Tipo (info, success, warning, error)
    """
    if box_type == "success":
        st.success(f"**{title}**\n\n{content}")
    elif box_type == "warning":
        st.warning(f"**{title}**\n\n{content}")
    elif box_type == "error":
        st.error(f"**{title}**\n\n{content}")
    else:
        st.info(f"**{title}**\n\n{content}")


def progress_indicator(current: int, total: int, label: str = "Progresso"):
    """Renderiza indicador de progresso.
    
    Args:
        current: Valor atual
        total: Valor total
        label: Rótulo
    """
    percentage = (current / total) * 100 if total > 0 else 0
    st.progress(percentage / 100, text=f"{label}: {current}/{total} ({percentage:.1f}%)")


def summary_card(title: str, items: list, card_type: str = "info"):
    """Renderiza card de sumário.
    
    Args:
        title: Título do card
        items: Lista de itens (strings)
        card_type: Tipo (info, success, warning, error)
    """
    content = "\n".join([f"- {item}" for item in items])
    info_box(title, content, card_type)

