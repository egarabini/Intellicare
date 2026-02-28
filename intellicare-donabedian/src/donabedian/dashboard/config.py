"""
Dashboard configuration.

Configuration settings for the Streamlit dashboard.
"""

import os
from typing import Dict, Any


# API Configuration
API_BASE_URL = os.getenv("DONABEDIAN_API_URL", "http://localhost:8003/api/v1")

# Dashboard Settings
DEFAULT_PERIOD_DAYS = 30
CACHE_TTL_SECONDS = 300  # 5 minutes

# Page Configuration
PAGE_TITLE = "IntelliCare Donabedian"
PAGE_ICON = "📊"
LAYOUT = "wide"
INITIAL_SIDEBAR_STATE = "expanded"

# Theme Colors (matching Donabedian quality framework)
COLORS = {
    "green": "#28a745",
    "yellow": "#ffc107",
    "red": "#dc3545",
    "primary": "#007bff",
    "secondary": "#6c757d",
    "success": "#28a745",
    "info": "#17a2b8",
    "warning": "#ffc107",
    "danger": "#dc3545",
}

# Status Colors
STATUS_COLORS = {
    "green": COLORS["green"],
    "yellow": COLORS["yellow"],
    "red": COLORS["red"],
}

# Pillar Colors (7 distinct colors for radar chart)
PILLAR_COLORS = [
    "#1f77b4",  # Eficácia
    "#ff7f0e",  # Efetividade
    "#2ca02c",  # Eficiência
    "#d62728",  # Otimidade
    "#9467bd",  # Aceitabilidade
    "#8c564b",  # Legitimidade
    "#e377c2",  # Equidade
]

# Triad Colors
TRIAD_COLORS = {
    "structure": "#3498db",
    "process": "#2ecc71",
    "outcome": "#e74c3c",
}

# Chart Configuration
CHART_CONFIG: Dict[str, Any] = {
    "displayModeBar": True,
    "displaylogo": False,
    "modeBarButtonsToRemove": ["pan2d", "lasso2d", "select2d"],
}

# Plotly Layout Defaults
PLOTLY_LAYOUT_DEFAULTS = {
    "font": {"family": "Arial, sans-serif", "size": 12},
    "margin": {"l": 50, "r": 50, "t": 50, "b": 50},
    "paper_bgcolor": "rgba(0,0,0,0)",
    "plot_bgcolor": "rgba(0,0,0,0)",
}

# Period Options (in days)
PERIOD_OPTIONS = {
    "Últimos 7 dias": 7,
    "Últimos 30 dias": 30,
    "Últimos 90 dias": 90,
    "Últimos 180 dias": 180,
    "Último ano": 365,
}

# Pillar Names (Portuguese)
PILLAR_NAMES = {
    1: "Eficácia",
    2: "Efetividade",
    3: "Eficiência",
    4: "Otimidade",
    5: "Aceitabilidade",
    6: "Legitimidade",
    7: "Equidade",
}

# Triad Dimension Names (Portuguese)
TRIAD_NAMES = {
    "structure": "Estrutura",
    "process": "Processo",
    "outcome": "Resultado",
}

# Trend Direction Icons
TREND_ICONS = {
    "improving": "📈",
    "stable": "➡️",
    "declining": "📉",
    "insufficient_data": "❓",
}

# Trend Direction Colors
TREND_COLORS = {
    "improving": COLORS["success"],
    "stable": COLORS["info"],
    "declining": COLORS["danger"],
    "insufficient_data": COLORS["secondary"],
}

# Number Formatting
NUMBER_FORMAT = {
    "score": "{:.1f}",
    "percentage": "{:.1f}%",
    "value": "{:.2f}",
    "integer": "{:,}",
}

# Date Format
DATE_FORMAT = "%d/%m/%Y"

# Export Settings
EXPORT_FORMATS = ["CSV", "Excel", "JSON"]

