"""BIREMEClient — busca em BVS/BIREME (literatura latina PT-BR/ES)."""

from __future__ import annotations

import logging
import time
from typing import Optional

import httpx

from superz.models import LiteratureSearchResponse, MedicalArticle, SearchStatus

logger = logging.getLogger(__name__)

BASE_URL = "https://pesquisa.bvsalud.org/portal/"


class BIREMEClient:
    """
    Cliente para BVS/BIREME API (Biblioteca Virtual em Saude).
    Foco em literatura em portugues e espanhol.

    API: iAH search interface (JSON).
    """

    def __init__(self, timeout: float = 30.0):
        self._timeout = timeout

    async def search(
        self,
        query: str,
        max_results: int = 5,
        language: str = "pt",
        database: str = "MEDLINE,LILACS,IBECS",
    ) -> LiteratureSearchResponse:
        """Busca BVS/BIREME com filtros de idioma e base."""
        t0 = time.monotonic()

        try:
            params = {
                "q": query,
                "lang": language,
                "count": max_results,
                "output": "json",
                "db": database,
            }

            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.get(f"{BASE_URL}", params=params)
                resp.raise_for_status()

            # BIREME pode retornar HTML ou JSON dependendo do endpoint
            try:
                data = resp.json()
            except Exception:
                # Se nao for JSON, tentar extrair dados do HTML
                logger.warning("BIREME retornou formato nao-JSON")
                return LiteratureSearchResponse(
                    status=SearchStatus.NO_RESULTS,
                    database_used="bireme",
                    query_time_ms=int((time.monotonic() - t0) * 1000),
                )

            articles = self._parse_results(data)

            return LiteratureSearchResponse(
                status=SearchStatus.SUCCESS if articles else SearchStatus.NO_RESULTS,
                articles=articles,
                total_found=data.get("diapiSearchResult", {}).get("numFound", len(articles)),
                returned=len(articles),
                database_used="bireme",
                query_time_ms=int((time.monotonic() - t0) * 1000),
            )
        except Exception as e:
            logger.error("BIREME search falhou: %s", e)
            return LiteratureSearchResponse(
                status=SearchStatus.SOURCE_UNAVAILABLE,
                database_used="bireme",
                query_time_ms=int((time.monotonic() - t0) * 1000),
            )

    def _parse_results(self, data: dict) -> list[MedicalArticle]:
        """Parseia resultados da BVS API."""
        articles = []
        docs = data.get("diapiSearchResult", {}).get("docs", [])
        if not docs:
            # Tentar formato alternativo
            docs = data.get("response", {}).get("docs", [])

        for doc in docs:
            try:
                title = doc.get("ti", [""])[0] if isinstance(doc.get("ti"), list) else doc.get("ti", "")
                authors = doc.get("au", []) if isinstance(doc.get("au"), list) else []
                journal = doc.get("ta", [""])[0] if isinstance(doc.get("ta"), list) else doc.get("ta", "")
                abstract = doc.get("ab", [""])[0] if isinstance(doc.get("ab"), list) else doc.get("ab", "")

                year = 0
                da = doc.get("da", "")
                if da and len(str(da)) >= 4:
                    try:
                        year = int(str(da)[:4])
                    except ValueError:
                        pass

                url = doc.get("ur", [""])[0] if isinstance(doc.get("ur"), list) else doc.get("ur", "")
                doi = doc.get("doi", "")

                articles.append(MedicalArticle(
                    title=title,
                    authors=authors[:5],
                    journal=journal,
                    year=year,
                    abstract=abstract,
                    url=url,
                    doi=doi if doi else None,
                    study_type="other",
                    evidence_level="D",
                ))
            except Exception as e:
                logger.warning("Falha ao parsear artigo BIREME: %s", e)
                continue

        return articles

    async def is_available(self) -> bool:
        """Verifica se BVS/BIREME esta acessivel."""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(BASE_URL, params={"q": "test", "count": 1, "output": "json"})
                return resp.status_code == 200
        except Exception:
            return False
