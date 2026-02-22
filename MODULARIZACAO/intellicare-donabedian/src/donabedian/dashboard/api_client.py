"""
API Client for Donabedian Dashboard.

HTTP client to consume the REST API endpoints.
"""

import os
from typing import Dict, List, Any, Optional
from datetime import date
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class DonabedianAPIClient:
    """Client for Donabedian REST API."""
    
    def __init__(self, base_url: Optional[str] = None):
        """
        Initialize API client.
        
        Args:
            base_url: Base URL of the API (default: from env or localhost:8003)
        """
        self.base_url = base_url or os.getenv(
            "DONABEDIAN_API_URL", 
            "http://localhost:8003/api/v1"
        )
        
        # Configure session with retries
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
    
    def _get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Make GET request to API.
        
        Args:
            endpoint: API endpoint (without base URL)
            params: Query parameters
            
        Returns:
            Response JSON data
            
        Raises:
            requests.HTTPError: If request fails
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        response = self.session.get(url, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    
    def _post(self, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Make POST request to API.
        
        Args:
            endpoint: API endpoint (without base URL)
            data: Request body data
            
        Returns:
            Response JSON data
            
        Raises:
            requests.HTTPError: If request fails
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        response = self.session.post(url, json=data, timeout=30)
        response.raise_for_status()
        return response.json()
    
    # Health & Info
    def get_health(self) -> Dict[str, Any]:
        """Get API health status."""
        return self._get("health")
    
    def get_info(self) -> Dict[str, Any]:
        """Get module information."""
        return self._get("info")
    
    # Dashboard endpoints
    def get_dashboard_overview(self, period_days: int = 30) -> Dict[str, Any]:
        """
        Get dashboard overview.
        
        Args:
            period_days: Number of days to look back (default: 30)
            
        Returns:
            Dashboard overview data
        """
        return self._get("dashboard", params={"period_days": period_days})
    
    def get_dashboard_pillars(self, period_days: int = 30) -> Dict[str, Any]:
        """
        Get pillars dashboard.
        
        Args:
            period_days: Number of days to look back (default: 30)
            
        Returns:
            Pillars dashboard data
        """
        return self._get("dashboard/pillars", params={"period_days": period_days})
    
    def get_dashboard_indicators(self, period_days: int = 30) -> Dict[str, Any]:
        """
        Get indicators dashboard.
        
        Args:
            period_days: Number of days to look back (default: 30)
            
        Returns:
            Indicators dashboard data
        """
        return self._get("dashboard/indicators", params={"period_days": period_days})
    
    # Assessment endpoints
    def calculate_assessment(
        self,
        period_start: date,
        period_end: date,
        pillar_ids: Optional[List[int]] = None,
        indicator_ids: Optional[List[int]] = None,
    ) -> Dict[str, Any]:
        """
        Calculate quality assessment.
        
        Args:
            period_start: Start date of period
            period_end: End date of period
            pillar_ids: Optional list of pillar IDs to filter
            indicator_ids: Optional list of indicator IDs to filter
            
        Returns:
            Quality assessment data
        """
        data = {
            "period_start": period_start.isoformat(),
            "period_end": period_end.isoformat(),
        }
        if pillar_ids:
            data["pillar_ids"] = pillar_ids
        if indicator_ids:
            data["indicator_ids"] = indicator_ids
        
        return self._post("assess", data=data)
    
    # Trends endpoints
    def get_indicator_trend(self, indicator_id: int, period_days: int = 90) -> Dict[str, Any]:
        """
        Get temporal trend for indicator.

        Args:
            indicator_id: Indicator ID
            period_days: Number of days to analyze (default: 90)

        Returns:
            Indicator trend data
        """
        return self._get(f"trends/{indicator_id}", params={"period_days": period_days})

    def get_pillar_trend(self, pillar_id: int, period_days: int = 90) -> Dict[str, Any]:
        """
        Get temporal trend for pillar.

        Args:
            pillar_id: Pillar ID
            period_days: Number of days to analyze (default: 90)

        Returns:
            Pillar trend data
        """
        return self._get(f"trends/pillar/{pillar_id}", params={"period_days": period_days})

    # CRUD endpoints (for reference data)
    def get_pillars(self) -> List[Dict[str, Any]]:
        """Get all pillars."""
        return self._get("pillars")

    def get_indicators(self, page: int = 1, page_size: int = 100) -> Dict[str, Any]:
        """
        Get indicators with pagination.

        Args:
            page: Page number (default: 1)
            page_size: Items per page (default: 100)

        Returns:
            Paginated indicators data
        """
        return self._get("indicators", params={"page": page, "page_size": page_size})

