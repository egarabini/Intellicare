"""
Cache utilities.

Utilities for caching API responses in Streamlit.
"""

import streamlit as st
from typing import Dict, Any, Callable
from functools import wraps
from donabedian.dashboard import config


def cache_api_call(ttl: int = config.CACHE_TTL_SECONDS):
    """
    Decorator to cache API calls.
    
    Args:
        ttl: Time to live in seconds
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        @st.cache_data(ttl=ttl)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    return decorator


@st.cache_data(ttl=config.CACHE_TTL_SECONDS)
def get_cached_dashboard_overview(api_client, period_days: int) -> Dict[str, Any]:
    """
    Get cached dashboard overview.
    
    Args:
        api_client: API client instance
        period_days: Number of days to look back
        
    Returns:
        Dashboard overview data
    """
    return api_client.get_dashboard_overview(period_days)


@st.cache_data(ttl=config.CACHE_TTL_SECONDS)
def get_cached_dashboard_pillars(api_client, period_days: int) -> Dict[str, Any]:
    """
    Get cached pillars dashboard.
    
    Args:
        api_client: API client instance
        period_days: Number of days to look back
        
    Returns:
        Pillars dashboard data
    """
    return api_client.get_dashboard_pillars(period_days)


@st.cache_data(ttl=config.CACHE_TTL_SECONDS)
def get_cached_dashboard_indicators(api_client, period_days: int) -> Dict[str, Any]:
    """
    Get cached indicators dashboard.
    
    Args:
        api_client: API client instance
        period_days: Number of days to look back
        
    Returns:
        Indicators dashboard data
    """
    return api_client.get_dashboard_indicators(period_days)


@st.cache_data(ttl=config.CACHE_TTL_SECONDS)
def get_cached_indicator_trend(api_client, indicator_id: int, period_days: int) -> Dict[str, Any]:
    """
    Get cached indicator trend.
    
    Args:
        api_client: API client instance
        indicator_id: Indicator ID
        period_days: Number of days to analyze
        
    Returns:
        Indicator trend data
    """
    return api_client.get_indicator_trend(indicator_id, period_days)


@st.cache_data(ttl=config.CACHE_TTL_SECONDS)
def get_cached_pillar_trend(api_client, pillar_id: int, period_days: int) -> Dict[str, Any]:
    """
    Get cached pillar trend.
    
    Args:
        api_client: API client instance
        pillar_id: Pillar ID
        period_days: Number of days to analyze
        
    Returns:
        Pillar trend data
    """
    return api_client.get_pillar_trend(pillar_id, period_days)


@st.cache_data(ttl=600)  # Cache for 10 minutes
def get_cached_pillars(api_client) -> list:
    """
    Get cached list of pillars.
    
    Args:
        api_client: API client instance
        
    Returns:
        List of pillars
    """
    return api_client.get_pillars()


@st.cache_data(ttl=600)  # Cache for 10 minutes
def get_cached_indicators(api_client, page: int = 1, page_size: int = 100) -> Dict[str, Any]:
    """
    Get cached list of indicators.
    
    Args:
        api_client: API client instance
        page: Page number
        page_size: Items per page
        
    Returns:
        Paginated indicators data
    """
    return api_client.get_indicators(page, page_size)


def clear_all_caches():
    """Clear all Streamlit caches."""
    st.cache_data.clear()
    st.cache_resource.clear()

