"""Utilitários de formatação para a UI Florence."""

from datetime import datetime
from typing import Any, Dict
from florence.ui.config import DATE_FORMAT, DATETIME_FORMAT, STATUS_COLORS


def format_date(dt: datetime) -> str:
    """Formata data.
    
    Args:
        dt: Data/hora
        
    Returns:
        Data formatada
    """
    return dt.strftime(DATE_FORMAT)


def format_datetime(dt: datetime) -> str:
    """Formata data e hora.
    
    Args:
        dt: Data/hora
        
    Returns:
        Data/hora formatada
    """
    return dt.strftime(DATETIME_FORMAT)


def format_lab_value(value: float, unit: str = "") -> str:
    """Formata valor de exame.
    
    Args:
        value: Valor do exame
        unit: Unidade de medida
        
    Returns:
        Valor formatado
    """
    formatted = f"{value:.2f}"
    if unit:
        formatted += f" {unit}"
    return formatted


def format_reference_range(min_val: float, max_val: float, unit: str = "") -> str:
    """Formata faixa de referência.
    
    Args:
        min_val: Valor mínimo
        max_val: Valor máximo
        unit: Unidade de medida
        
    Returns:
        Faixa formatada
    """
    formatted = f"{min_val:.2f} - {max_val:.2f}"
    if unit:
        formatted += f" {unit}"
    return formatted


def get_status_color(status: str) -> str:
    """Obtém cor para status.
    
    Args:
        status: Status do exame
        
    Returns:
        Código de cor hexadecimal
    """
    return STATUS_COLORS.get(status.lower(), "#6c757d")


def get_status_emoji(status: str) -> str:
    """Obtém emoji para status.
    
    Args:
        status: Status do exame
        
    Returns:
        Emoji representando o status
    """
    status_lower = status.lower()
    if status_lower == "normal":
        return "✅"
    elif status_lower in ["low", "high"]:
        return "⚠️"
    elif status_lower in ["critical_low", "critical_high"]:
        return "🔴"
    elif status_lower == "panic":
        return "🚨"
    else:
        return "❓"


def format_significance(significance: str) -> str:
    """Formata significância clínica.
    
    Args:
        significance: Significância
        
    Returns:
        Significância formatada com emoji
    """
    sig_lower = significance.lower()
    if sig_lower == "normal":
        return "✅ Normal"
    elif sig_lower == "atencao":
        return "⚠️ Atenção"
    elif sig_lower == "urgente":
        return "🔴 Urgente"
    elif sig_lower == "critico":
        return "🚨 Crítico"
    else:
        return f"❓ {significance}"


def format_percentage(value: float) -> str:
    """Formata porcentagem.
    
    Args:
        value: Valor (0-1)
        
    Returns:
        Porcentagem formatada
    """
    return f"{value * 100:.1f}%"


def format_duration_ms(ms: float) -> str:
    """Formata duração em milissegundos.
    
    Args:
        ms: Duração em ms
        
    Returns:
        Duração formatada
    """
    if ms < 1000:
        return f"{ms:.0f}ms"
    else:
        return f"{ms / 1000:.2f}s"


def truncate_text(text: str, max_length: int = 100) -> str:
    """Trunca texto longo.
    
    Args:
        text: Texto original
        max_length: Comprimento máximo
        
    Returns:
        Texto truncado
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."


def format_protocol_score(score: float) -> str:
    """Formata score de relevância de protocolo.
    
    Args:
        score: Score (0-1)
        
    Returns:
        Score formatado com emoji
    """
    percentage = score * 100
    if percentage >= 90:
        emoji = "🟢"
    elif percentage >= 70:
        emoji = "🟡"
    else:
        emoji = "🔴"
    return f"{emoji} {percentage:.1f}%"

