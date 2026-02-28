"""SciELOClient — busca em SciELO (journals latinoamericanos)."""

from __future__ import annotations

import logging
import time
from typing import Optional

import httpx

from pierre.models import LiteratureSearchResponse, MedicalArticle, SearchStatus

logger = logging.getLogger(__name__)

BASE_URL = "https://search.scielo.org/"


class SciELOClient:
    """
    Cliente para SciELO API.
    Foco em journals brasileiros e latino-americanos open access.
    """

    def __init__(self, timeout: float = 30.0):
        self._timeout = timeout

    async def search(
        self,
        query: str,
        max_results: int = 5,
        language: str = "pt",
    ) -> LiteratureSearchResponse:
        """Busca SciELO."""
        t0 = time.monotonic()

        try:
            params = {
                "q": query,
                "lang": language,
                "count": max_results,
                "output": "json",
                "format": "json",
            }

            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.get(BASE_URL, params=params)
                resp.raise_for_status()

            try:
                data = resp.json()
            except Exception:
                return LiteratureSearchResponse(
                    status=SearchStatus.NO_RESULTS,
                    database_used="scielo",
                    query_time_ms=int((time.monotonic() - t0) * 1000),
                )

            articles = self._parse_results(data)

            return LiteratureSearchResponse(
                status=SearchStatus.SUCCESS if articles else SearchStatus.NO_RESULTS,
                articles=articles,
                total_found=len(articles),
                returned=len(articles),
                database_used="scielo",
                query_time_ms=int((time.monotonic() - t0) * 1000),
            )
        except Exception as e:
            logger.error("SciELO search falhou: %s", e)
            return LiteratureSearchResponse(
                status=SearchStatus.SOURCE_UNAVAILABLE,
                database_used="scielo",
                query_time_ms=int((time.monotonic() - t0) * 1000),
            )

    def _parse_results(self, data: dict) -> list[MedicalArticle]:
        """Parseia resultados SciELO."""
        articles = []
        docs = data.get("response", {}).get("docs", [])

        for doc in docs:
            try:
                title = doc.get("ti", [""])[0] if isinstance(doc.get("ti"), list) else doc.get("ti", "")
                authors = doc.get("au", []) if isinstance(doc.get("au"), list) else []
                journal = doc.get("ta", [""])[0] if isinstance(doc.get("ta"), list) else doc.get("ta", "")

                year = 0
                da = doc.get("da", "")
                if da and len(str(da)) >= 4:
                    try:
                        year = int(str(da)[:4])
                    except ValueError:
                        pass

                url = doc.get("fulltext_html", "") or doc.get("ur", "")
                if isinstance(url, list):
                    url = url[0] if url else ""

                articles.append(MedicalArticle(
                    title=title,
                    authors=authors[:5],
                    journal=journal,
                    year=year,
                    url=url,
                    study_type="other",
                    evidence_level="D",
                ))
            except Exception as e:
                logger.warning("Falha ao parsear artigo SciELO: %s", e)
                continue

        return articles

    async def is_available(self) -> bool:
        """Verifica se SciELO esta acessivel."""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(BASE_URL, params={"q": "test", "count": 1, "output": "json"})
                return resp.status_code == 200
        except Exception:
            return False
