"""Modelos de dados do intellicare-pierre."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class SearchStatus(str, Enum):
    """Status de uma operacao de busca."""
    SUCCESS = "success"
    NO_RESULTS = "no_results"
    RATE_LIMITED = "rate_limited"
    SOURCE_UNAVAILABLE = "source_unavailable"
    ERROR = "error"


# ──────────────────────────────────────
# Web Search (Tavily)
# ──────────────────────────────────────

@dataclass
class WebSearchResult:
    """Um resultado de busca web."""
    title: str
    url: str
    content: str
    published_date: Optional[str] = None
    relevance_score: float = 0.0
    source_type: str = "other"  # guideline | article | news | regulatory | other


@dataclass
class WebSearchResponse:
    """Resposta completa de web_search."""
    status: SearchStatus
    results: list[WebSearchResult] = field(default_factory=list)
    answer: Optional[str] = None
    total_results: int = 0
    query_time_ms: int = 0
    cached: bool = False


# ──────────────────────────────────────
# Medical Literature (PubMed, BIREME, SciELO)
# ──────────────────────────────────────

@dataclass
class MedicalArticle:
    """Um artigo de literatura medica."""
    title: str
    authors: list[str] = field(default_factory=list)
    journal: str = ""
    year: int = 0
    abstract: str = ""
    conclusion: Optional[str] = None
    study_type: str = "other"  # rct | meta_analysis | systematic_review | guideline | other
    url: str = ""
    evidence_level: Optional[str] = None  # A | B | C | D
    doi: Optional[str] = None
    pmid: Optional[str] = None


@dataclass
class LiteratureSearchResponse:
    """Resposta completa de search_medical_literature."""
    status: SearchStatus
    articles: list[MedicalArticle] = field(default_factory=list)
    total_found: int = 0
    returned: int = 0
    database_used: str = ""
    query_time_ms: int = 0
    cached: bool = False


# ──────────────────────────────────────
# Regulatory (ANVISA, ANS, CFM, COFEN)
# ──────────────────────────────────────

@dataclass
class RegulatoryResult:
    """Um resultado de verificacao regulatoria."""
    title: str
    authority: str  # ANVISA | ANS | CFM | COFEN
    document_type: str = ""
    status: Optional[str] = None  # aprovado | suspenso | cancelado | em_analise
    publication_date: Optional[str] = None
    url: str = ""
    key_information: Optional[str] = None
    contraindications: Optional[str] = None


@dataclass
class RegulatoryResponse:
    """Resposta completa de check_regulatory."""
    status: SearchStatus
    results: list[RegulatoryResult] = field(default_factory=list)
    query_time_ms: int = 0
    source: str = ""
    cached: bool = False


# ──────────────────────────────────────
# Text Analysis (Qwen via Ollama)
# ──────────────────────────────────────

@dataclass
class TextAnalysisResult:
    """Resultado de analyze_text."""
    analysis: str = ""
    key_points: list[str] = field(default_factory=list)
    confidence: float = 0.0
    model_used: str = ""
    processing_time_ms: int = 0


# ──────────────────────────────────────
# Document Summary
# ──────────────────────────────────────

@dataclass
class SummaryResult:
    """Resultado de summarize_document."""
    summary: str = ""
    key_actions: list[str] = field(default_factory=list)
    source_url: Optional[str] = None
    document_title: Optional[str] = None
    summary_type: str = ""
    processing_time_ms: int = 0


# ──────────────────────────────────────
# Translation
# ──────────────────────────────────────

@dataclass
class TranslationResult:
    """Resultado de translate_to_portuguese."""
    translated_text: str = ""
    source_language_detected: str = ""
    medical_terms_preserved: list[str] = field(default_factory=list)
    confidence: float = 0.0
    processing_time_ms: int = 0
