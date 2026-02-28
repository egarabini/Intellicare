"""
intellicare_auth.smart — SMART-on-FHIR App Launch Framework.

Fornece:
- SmartConfiguration (well-known endpoint)
- EHR Launch / Standalone Launch context
- SMART scopes → AccessPolicy translation
- FastAPI router para /.well-known/smart-configuration
"""

from .models import SmartConfiguration, LaunchContext, SmartTokenClaims
from .scope_translator import smart_scopes_to_rules, parse_smart_scopes
from .launch_handler import EHRLaunchHandler, StandaloneLaunchHandler
from .router import smart_router

__all__ = [
    "SmartConfiguration",
    "LaunchContext",
    "SmartTokenClaims",
    "smart_scopes_to_rules",
    "parse_smart_scopes",
    "EHRLaunchHandler",
    "StandaloneLaunchHandler",
    "smart_router",
]
