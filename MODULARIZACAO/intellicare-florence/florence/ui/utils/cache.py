"""Utilitários de cache para a UI Florence."""

import streamlit as st
from typing import Any, Dict
from florence.ui.config import CACHE_TTL
from florence.ui.utils.api_client import FlorenceAPIClient


@st.cache_data(ttl=CACHE_TTL)
def get_cached_health(client: FlorenceAPIClient) -> Dict[str, Any]:
    """Obtém health check com cache.
    
    Args:
        client: Cliente API
        
    Returns:
        Status de saúde
    """
    return client.get_health()


@st.cache_data(ttl=CACHE_TTL)
def get_cached_info(client: FlorenceAPIClient) -> Dict[str, Any]:
    """Obtém informações do módulo com cache.
    
    Args:
        client: Cliente API
        
    Returns:
        Informações do módulo
    """
    return client.get_info()


@st.cache_data(ttl=CACHE_TTL)
def get_cached_resources(client: FlorenceAPIClient) -> Dict[str, Any]:
    """Obtém recursos disponíveis com cache.
    
    Args:
        client: Cliente API
        
    Returns:
        Recursos (painéis, exames, correlações)
    """
    return client.get_resources()


@st.cache_data(ttl=CACHE_TTL)
def get_cached_protocols(client: FlorenceAPIClient) -> Dict[str, Any]:
    """Obtém protocolos indexados com cache.
    
    Args:
        client: Cliente API
        
    Returns:
        Lista de protocolos
    """
    return client.get_protocols()


def clear_all_caches():
    """Limpa todos os caches."""
    st.cache_data.clear()

