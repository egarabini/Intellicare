"""Configurações da UI Florence."""

import os
from typing import Final

# API Configuration
API_BASE_URL: Final[str] = os.getenv("FLORENCE_API_URL", "http://localhost:8002")

# Page Configuration
PAGE_TITLE: Final[str] = "Florence - Análise Clínica"
PAGE_ICON: Final[str] = "🏥"
LAYOUT: Final[str] = "wide"
INITIAL_SIDEBAR_STATE: Final[str] = "expanded"

# Cache Configuration
CACHE_TTL: Final[int] = 300  # 5 minutos
MAX_UPLOAD_SIZE: Final[int] = 10  # MB

# Chart Configuration
CHART_CONFIG: Final[dict] = {
    "displayModeBar": True,
    "displaylogo": False,
    "modeBarButtonsToRemove": ["lasso2d", "select2d"],
}

# Status Colors
STATUS_COLORS: Final[dict] = {
    "normal": "#28a745",      # Verde
    "low": "#ffc107",         # Amarelo
    "high": "#ffc107",        # Amarelo
    "critical_low": "#dc3545",  # Vermelho
    "critical_high": "#dc3545", # Vermelho
    "panic": "#6c757d",       # Cinza escuro
}

# Theme Colors
THEME_COLORS: Final[dict] = {
    "primary": "#0066cc",     # Azul IntelliCare
    "secondary": "#6c757d",   # Cinza
    "success": "#28a745",     # Verde
    "warning": "#ffc107",     # Amarelo
    "danger": "#dc3545",      # Vermelho
    "info": "#17a2b8",        # Azul claro
}

# Export Configuration
EXPORT_FORMATS: Final[list] = ["Excel (.xlsx)", "PDF (.pdf)", "JSON (.json)"]

# Pagination
ITEMS_PER_PAGE: Final[int] = 20

# Date Format
DATE_FORMAT: Final[str] = "%d/%m/%Y"
DATETIME_FORMAT: Final[str] = "%d/%m/%Y %H:%M:%S"

