"""
Metric components.

Reusable metric display components.
"""

import streamlit as st
from typing import Optional
from donabedian.dashboard import config


def display_score_metric(
    label: str,
    score: float,
    delta: Optional[float] = None,
    help_text: Optional[str] = None
):
    """
    Display a score metric with color coding.
    
    Args:
        label: Metric label
        score: Score value (0-100)
        delta: Optional delta value to show change
        help_text: Optional help text
    """
    # Determine color based on score
    if score >= 75:
        color = "green"
    elif score >= 50:
        color = "yellow"
    else:
        color = "red"
    
    # Format score
    score_str = config.NUMBER_FORMAT["score"].format(score)
    
    # Display metric
    st.metric(
        label=label,
        value=score_str,
        delta=f"{delta:+.1f}" if delta is not None else None,
        help=help_text,
    )


def display_status_badge(status: str) -> str:
    """
    Get HTML for status badge.
    
    Args:
        status: Status value ('green', 'yellow', 'red')
        
    Returns:
        HTML string for badge
    """
    status_lower = status.lower()
    
    status_labels = {
        "green": "✅ VERDE",
        "yellow": "⚠️ AMARELO",
        "red": "❌ VERMELHO",
    }
    
    label = status_labels.get(status_lower, status.upper())
    
    return f'<span class="status-{status_lower}">{label}</span>'


def display_trend_indicator(direction: str) -> str:
    """
    Get HTML for trend direction indicator.
    
    Args:
        direction: Trend direction ('improving', 'stable', 'declining', 'insufficient_data')
        
    Returns:
        HTML string for trend indicator
    """
    icon = config.TREND_ICONS.get(direction, "❓")
    color = config.TREND_COLORS.get(direction, config.COLORS["secondary"])
    
    direction_labels = {
        "improving": "Melhorando",
        "stable": "Estável",
        "declining": "Piorando",
        "insufficient_data": "Dados Insuficientes",
    }
    
    label = direction_labels.get(direction, direction)
    
    return f'<span style="color: {color}; font-weight: bold;">{icon} {label}</span>'


def create_metric_card(
    title: str,
    value: str,
    subtitle: Optional[str] = None,
    color: str = "primary"
):
    """
    Create a styled metric card.
    
    Args:
        title: Card title
        value: Main value to display
        subtitle: Optional subtitle
        color: Color theme ('primary', 'success', 'warning', 'danger')
    """
    card_color = config.COLORS.get(color, config.COLORS["primary"])
    
    html = f"""
    <div style="
        background-color: {card_color}15;
        border-left: 4px solid {card_color};
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 0.5rem 0;
    ">
        <div style="color: {card_color}; font-size: 0.875rem; font-weight: 600; margin-bottom: 0.25rem;">
            {title}
        </div>
        <div style="font-size: 1.5rem; font-weight: bold; margin-bottom: 0.25rem;">
            {value}
        </div>
        {f'<div style="color: #6c757d; font-size: 0.875rem;">{subtitle}</div>' if subtitle else ''}
    </div>
    """
    
    st.markdown(html, unsafe_allow_html=True)


def display_top_performers(
    performers: list,
    title: str = "Top Performers",
    is_bottom: bool = False
):
    """
    Display top or bottom performers list.
    
    Args:
        performers: List of performer dictionaries with 'name' and 'score'
        title: Section title
        is_bottom: If True, shows bottom performers (red theme)
    """
    st.subheader(title)
    
    for i, performer in enumerate(performers, 1):
        name = performer.get("indicator_name", performer.get("name", "Unknown"))
        score = performer.get("score", 0)
        
        # Determine color
        if is_bottom:
            color = "danger"
        else:
            color = "success"
        
        # Create card
        create_metric_card(
            title=f"#{i} {name}",
            value=config.NUMBER_FORMAT["score"].format(score),
            color=color
        )

