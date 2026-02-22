"""
Data formatters.

Utility functions for formatting data for display.
"""

from datetime import date, datetime
from typing import Any, Optional
from donabedian.dashboard import config


def format_score(score: float) -> str:
    """
    Format score value.
    
    Args:
        score: Score value (0-100)
        
    Returns:
        Formatted string
    """
    return config.NUMBER_FORMAT["score"].format(score)


def format_percentage(value: float) -> str:
    """
    Format percentage value.
    
    Args:
        value: Percentage value
        
    Returns:
        Formatted string with % symbol
    """
    return config.NUMBER_FORMAT["percentage"].format(value)


def format_value(value: float) -> str:
    """
    Format numeric value.
    
    Args:
        value: Numeric value
        
    Returns:
        Formatted string
    """
    return config.NUMBER_FORMAT["value"].format(value)


def format_integer(value: int) -> str:
    """
    Format integer with thousands separator.
    
    Args:
        value: Integer value
        
    Returns:
        Formatted string
    """
    return config.NUMBER_FORMAT["integer"].format(value)


def format_date(date_value: Any) -> str:
    """
    Format date value.
    
    Args:
        date_value: Date value (date, datetime, or ISO string)
        
    Returns:
        Formatted date string
    """
    if isinstance(date_value, str):
        try:
            date_value = datetime.fromisoformat(date_value.replace('Z', '+00:00')).date()
        except:
            return date_value
    
    if isinstance(date_value, datetime):
        date_value = date_value.date()
    
    if isinstance(date_value, date):
        return date_value.strftime(config.DATE_FORMAT)
    
    return str(date_value)


def format_status(status: str) -> str:
    """
    Format status value for display.
    
    Args:
        status: Status value ('green', 'yellow', 'red')
        
    Returns:
        Formatted status string
    """
    status_map = {
        "green": "✅ Verde",
        "yellow": "⚠️ Amarelo",
        "red": "❌ Vermelho",
    }
    
    return status_map.get(status.lower(), status.upper())


def format_trend_direction(direction: str) -> str:
    """
    Format trend direction for display.
    
    Args:
        direction: Trend direction
        
    Returns:
        Formatted string with icon
    """
    icon = config.TREND_ICONS.get(direction, "❓")
    
    direction_map = {
        "improving": "Melhorando",
        "stable": "Estável",
        "declining": "Piorando",
        "insufficient_data": "Dados Insuficientes",
    }
    
    label = direction_map.get(direction, direction)
    
    return f"{icon} {label}"


def format_pillar_name(pillar_id: int) -> str:
    """
    Get pillar name from ID.
    
    Args:
        pillar_id: Pillar ID (1-7)
        
    Returns:
        Pillar name in Portuguese
    """
    return config.PILLAR_NAMES.get(pillar_id, f"Pilar {pillar_id}")


def format_triad_name(triad_dimension: str) -> str:
    """
    Get triad dimension name in Portuguese.
    
    Args:
        triad_dimension: Triad dimension ('structure', 'process', 'outcome')
        
    Returns:
        Dimension name in Portuguese
    """
    return config.TRIAD_NAMES.get(triad_dimension, triad_dimension.capitalize())


def truncate_text(text: str, max_length: int = 50) -> str:
    """
    Truncate text to maximum length.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        
    Returns:
        Truncated text with ellipsis if needed
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - 3] + "..."

