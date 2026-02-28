"""
Filter components.

Reusable filter components for the dashboard.
"""

import streamlit as st
from datetime import date, timedelta
from typing import Tuple, List, Optional
from donabedian.dashboard import config


def period_filter(key: str = "period") -> int:
    """
    Create period selection filter.
    
    Args:
        key: Unique key for the widget
        
    Returns:
        Number of days selected
    """
    st.sidebar.subheader("📅 Período")
    
    period_option = st.sidebar.selectbox(
        "Selecione o período",
        options=list(config.PERIOD_OPTIONS.keys()),
        index=1,  # Default to "Últimos 30 dias"
        key=key,
    )
    
    return config.PERIOD_OPTIONS[period_option]


def date_range_filter(key: str = "date_range") -> Tuple[date, date]:
    """
    Create custom date range filter.
    
    Args:
        key: Unique key for the widget
        
    Returns:
        Tuple of (start_date, end_date)
    """
    st.sidebar.subheader("📅 Período Personalizado")
    
    col1, col2 = st.sidebar.columns(2)
    
    with col1:
        start_date = st.date_input(
            "Data Inicial",
            value=date.today() - timedelta(days=30),
            key=f"{key}_start",
        )
    
    with col2:
        end_date = st.date_input(
            "Data Final",
            value=date.today(),
            key=f"{key}_end",
        )
    
    return start_date, end_date


def pillar_filter(pillars: List[dict], key: str = "pillars") -> List[int]:
    """
    Create pillar multi-select filter.
    
    Args:
        pillars: List of pillar dictionaries with 'id' and 'name'
        key: Unique key for the widget
        
    Returns:
        List of selected pillar IDs
    """
    st.sidebar.subheader("🎯 Pilares")
    
    pillar_options = {p["name"]: p["id"] for p in pillars}
    
    selected_names = st.sidebar.multiselect(
        "Selecione os pilares",
        options=list(pillar_options.keys()),
        default=list(pillar_options.keys()),  # All selected by default
        key=key,
    )
    
    return [pillar_options[name] for name in selected_names]


def triad_filter(key: str = "triad") -> Optional[str]:
    """
    Create triad dimension filter.
    
    Args:
        key: Unique key for the widget
        
    Returns:
        Selected triad dimension or None for all
    """
    st.sidebar.subheader("🔺 Tríade de Donabedian")
    
    options = ["Todas"] + list(config.TRIAD_NAMES.values())
    
    selected = st.sidebar.selectbox(
        "Selecione a dimensão",
        options=options,
        index=0,  # Default to "Todas"
        key=key,
    )
    
    if selected == "Todas":
        return None
    
    # Reverse lookup
    for key_name, value in config.TRIAD_NAMES.items():
        if value == selected:
            return key_name
    
    return None


def status_filter(key: str = "status") -> Optional[List[str]]:
    """
    Create status multi-select filter.
    
    Args:
        key: Unique key for the widget
        
    Returns:
        List of selected statuses or None for all
    """
    st.sidebar.subheader("🚦 Status")
    
    status_options = ["GREEN", "YELLOW", "RED"]
    
    selected = st.sidebar.multiselect(
        "Selecione os status",
        options=status_options,
        default=status_options,  # All selected by default
        key=key,
    )
    
    return selected if selected else None


def indicator_selector(indicators: List[dict], key: str = "indicator") -> Optional[int]:
    """
    Create indicator selector.
    
    Args:
        indicators: List of indicator dictionaries with 'id' and 'name'
        key: Unique key for the widget
        
    Returns:
        Selected indicator ID or None
    """
    st.sidebar.subheader("📊 Indicador")
    
    indicator_options = {f"{i['name']} (ID: {i['id']})": i['id'] for i in indicators}
    
    selected = st.sidebar.selectbox(
        "Selecione o indicador",
        options=["Nenhum"] + list(indicator_options.keys()),
        index=0,
        key=key,
    )
    
    if selected == "Nenhum":
        return None
    
    return indicator_options[selected]

