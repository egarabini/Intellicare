"""RegulatoryClient — verificacao regulatoria ANVISA/ANS/CFM/COFEN."""

from __future__ import annotations

import logging
import time
from dataclasses import asdict
from typing import Any, Optional

from pierre.cache.search_cache import SearchCache
from pierre.models import RegulatoryResponse, RegulatoryResult, SearchStatus

logger = logging.getLogger(__name__)

# Dominios oficiais por autoridade regulatoria
AUTHORITY_DOMAINS: dict[str, list[str]] = {
    "anvisa": ["anvisa.gov.br", "consultas.anvisa.gov.br"],
    "ans": ["ans.gov.br"],
    "cfm": ["cfm.org.br", "portal.cfm.org.br"],
    "cofen": ["cofen.gov.br"],
}


class RegulatoryClient:
    """
    Cliente para verificacao regulatoria brasileira.
    Usa Tavily web search focado em dominios de autoridades regulatorias.
    """

    def __init__(self, tavily_client: Any, cache: SearchCache):
        self._tavily = tavily_client
        self._cache = cache

    async def check(
        self,
        query: str,
        authority: str = "all",
        document_type: str = "any",
    ) -> RegulatoryResponse:
        """Busca regulatoria via Tavily focado em dominios oficiais."""
        t0 = time.monotonic()

        # Cache check
        params = {"authority": authority, "document_type": document_type}
        cached = await self._cache.get("regulatory", query, params)
        if cached:
            results = [RegulatoryResult(**r) for r in cached.get("results", [])]
            return RegulatoryResponse(
                status=SearchStatus.SUCCESS if results else SearchStatus.NO_RESULTS,
                results=results,
                query_time_ms=int((time.monotonic() - t0) * 1000),
                source="cache",
                cached=True,
            )

        # Build domain list
        if authority == "all":
            domains = []
            for domain_list in AUTHORITY_DOMAINS.values():
                domains.extend(domain_list)
        else:
            domains = AUTHORITY_DOMAINS.get(authority, [])

        # Enhance query with regulatory context
        enhanced_query = f"{query} regulamentacao aprovacao Brasil"
        if document_type != "any":
            type_map = {
                "bula": "bula profissional",
                "resolucao": "resolucao normativa",
                "nota_tecnica": "nota tecnica",
                "lista_cobertura": "rol de procedimentos cobertura",
            }
            enhanced_query += f" {type_map.get(document_type, document_type)}"

        try:
            # Use Tavily with domain focus
            tavily_response = await self._tavily.search(
                query=enhanced_query,
                max_results=5,
                search_depth="advanced",
                include_domains=domains if domains else None,
            )

            results = []
            for r in tavily_response.results:
                # Detect authority from URL
                detected_authority = self._detect_authority(r.url)
                results.append(RegulatoryResult(
                    title=r.title,
                    authority=detected_authority,
                    document_type=self._detect_doc_type(r.title, r.content),
                    status=self._detect_status(r.content),
                    publication_date=r.published_date,
                    url=r.url,
                    key_information=r.content[:500] if r.content else None,
                ))

            response = RegulatoryResponse(
                status=SearchStatus.SUCCESS if results else SearchStatus.NO_RESULTS,
                results=results,
                query_time_ms=int((time.monotonic() - t0) * 1000),
                source="tavily+web",
            )

            # Cache save
            cache_data = {"results": [asdict(r) for r in results]}
            await self._cache.set("regulatory", query, params, cache_data)

            return response

        except Exception as e:
            logger.error("Regulatory check falhou: %s", e)
            return RegulatoryResponse(
                status=SearchStatus.SOURCE_UNAVAILABLE,
                query_time_ms=int((time.monotonic() - t0) * 1000),
                source="error",
            )

    @staticmethod
    def _detect_authority(url: str) -> str:
        """Detecta autoridade pela URL."""
        url_lower = url.lower()
        for auth, domains in AUTHORITY_DOMAINS.items():
            for domain in domains:
                if domain in url_lower:
                    return auth.upper()
        return "OUTRO"

    @staticmethod
    def _detect_doc_type(title: str, content: str) -> str:
        """Detecta tipo de documento pelo titulo/conteudo."""
        text = (title + " " + content).lower()
        if "bula" in text:
            return "bula"
        if "resolucao" in text or "rdc" in text:
            return "resolucao"
        if "nota tecnica" in text or "nota técnica" in text:
            return "nota_tecnica"
        if "rol" in text and ("cobertura" in text or "procedimento" in text):
            return "lista_cobertura"
        return "outro"

    @staticmethod
    def _detect_status(content: str) -> Optional[str]:
        """Detecta status regulatorio pelo conteudo."""
        content_lower = content.lower()
        if any(w in content_lower for w in ["aprovado", "aprovada", "registrado", "registrada", "deferido"]):
            return "aprovado"
        if any(w in content_lower for w in ["suspenso", "suspensa", "suspensao"]):
            return "suspenso"
        if any(w in content_lower for w in ["cancelado", "cancelada", "revogado", "revogada"]):
            return "cancelado"
        if any(w in content_lower for w in ["em analise", "em análise", "petição"]):
            return "em_analise"
        return None

    async def is_available(self) -> bool:
        """Disponivel se Tavily estiver disponivel."""
        return await self._tavily.is_available()
