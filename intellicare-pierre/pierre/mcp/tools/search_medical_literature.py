"""Tool: search_medical_literature — Busca PubMed, BIREME, SciELO."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from pierre.models import LiteratureSearchResponse, SearchStatus
from pierre.integrations.knowledge_client import KnowledgeClient
from pierre.search.bireme_client import BIREMEClient
from pierre.search.pubmed_client import PubMedClient
from pierre.search.scielo_client import SciELOClient


async def handle_search_medical_literature(
    pubmed: PubMedClient,
    bireme: BIREMEClient,
    scielo: SciELOClient,
    arguments: dict[str, Any],
    knowledge_client: KnowledgeClient | None = None,
) -> dict:
    """Executa busca em literatura medica e retorna resultado."""
    query = arguments["query"]
    database = arguments.get("database", "pubmed")
    max_results = arguments.get("max_results", 5)
    study_type = arguments.get("study_type", "any")
    date_from = arguments.get("date_from")
    language = arguments.get("language", "any")

    if database == "pubmed":
        response = await pubmed.search(query, max_results, study_type, date_from, language)
    elif database == "bireme":
        response = await bireme.search(query, max_results, language)
    elif database == "scielo":
        response = await scielo.search(query, max_results, language)
    elif database == "all":
        # Buscar em todas e combinar
        responses = []
        per_db = max(1, max_results // 3)

        try:
            r_pubmed = await pubmed.search(query, per_db, study_type, date_from, language)
            responses.append(r_pubmed)
        except Exception:
            pass

        try:
            r_bireme = await bireme.search(query, per_db, language)
            responses.append(r_bireme)
        except Exception:
            pass

        try:
            r_scielo = await scielo.search(query, per_db, language)
            responses.append(r_scielo)
        except Exception:
            pass

        all_articles = []
        dbs_used = []
        for r in responses:
            all_articles.extend(r.articles)
            if r.database_used:
                dbs_used.append(r.database_used)

        response = LiteratureSearchResponse(
            status=SearchStatus.SUCCESS if all_articles else SearchStatus.NO_RESULTS,
            articles=all_articles[:max_results],
            total_found=sum(r.total_found for r in responses),
            returned=min(len(all_articles), max_results),
            database_used="+".join(dbs_used) if dbs_used else "all",
            query_time_ms=max((r.query_time_ms for r in responses), default=0),
        )
    else:
        response = await pubmed.search(query, max_results, study_type, date_from, language)

    knowledge_results: list[dict[str, Any]] = []
    knowledge_warning: str | None = None
    if knowledge_client is not None:
        try:
            knowledge_results = await knowledge_client.query_rag(
                query=query,
                top_k=min(max_results, 5),
                source="protocol",
            )
        except Exception as exc:
            knowledge_warning = f"knowledge_integration_error: {exc}"

    payload = {
        "status": response.status.value,
        "articles": [asdict(a) for a in response.articles],
        "total_found": response.total_found,
        "returned": response.returned,
        "database_used": response.database_used,
        "query_time_ms": response.query_time_ms,
        "cached": response.cached,
    }
    if knowledge_results:
        payload["knowledge_results"] = knowledge_results
    if knowledge_warning:
        payload["knowledge_warning"] = knowledge_warning
    return payload
