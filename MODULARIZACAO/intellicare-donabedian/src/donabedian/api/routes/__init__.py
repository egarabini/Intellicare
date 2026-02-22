"""
API routes for intellicare-donabedian.

Exports all route modules for easy registration in the main app.
"""

from donabedian.api.routes import health, pillars, indicators, indicator_pillars, measurements, assessment, dashboard, trends

__all__ = [
    "health",
    "pillars",
    "indicators",
    "indicator_pillars",
    "measurements",
    "assessment",
    "dashboard",
    "trends",
]
