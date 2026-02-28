"""FHIR Search Engine — translates FHIR search params to SQL queries.

Provides:
    - SearchFilter, SearchRequest, SearchResult (Pydantic models)
    - FHIRSQLBuilder — builds SQLAlchemy WHERE expressions from SearchRequest
    - SEARCH_PARAMS registry — known search parameters by ResourceType
    - parse_search_params — parse query string into SearchRequest
"""

from .models import SearchFilter, SearchRequest, SearchResult
from .parser import parse_search_params
from .search_params import SEARCH_PARAMS, SearchParamDef, get_search_param
from .sql_builder import FHIRSQLBuilder

__all__ = [
    "SearchFilter",
    "SearchRequest",
    "SearchResult",
    "parse_search_params",
    "SEARCH_PARAMS",
    "SearchParamDef",
    "get_search_param",
    "FHIRSQLBuilder",
]
