"""Testes do BIREMEClient — 2 testes."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import httpx
import pytest

from pierre.models import SearchStatus
from pierre.search.bireme_client import BIREMEClient


@pytest.mark.asyncio
async def test_bireme_search_pt():
    """Busca BIREME em portugues retorna artigos."""
    client = BIREMEClient()

    mock_response = httpx.Response(
        status_code=200,
        json={
            "diapiSearchResult": {
                "numFound": 1,
                "docs": [
                    {
                        "ti": ["Diabetes mellitus tipo 2 e nefropatia"],
                        "au": ["Silva JA", "Oliveira MR"],
                        "ta": ["Rev Bras Nefrol"],
                        "ab": ["Estudo sobre diabetes e doenca renal cronica no Brasil"],
                        "da": "20240115",
                        "ur": ["https://example.com/artigo1"],
                        "doi": "10.5935/0101-2800.2024001",
                    }
                ],
            }
        },
        request=httpx.Request("GET", "https://pesquisa.bvsalud.org/portal/"),
    )

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_response):
        response = await client.search("diabetes nefropatia", language="pt")

    assert response.status == SearchStatus.SUCCESS
    assert len(response.articles) == 1
    assert "Diabetes" in response.articles[0].title
    assert response.database_used == "bireme"


@pytest.mark.asyncio
async def test_bireme_unavailable():
    """BIREME indisponivel retorna SOURCE_UNAVAILABLE."""
    client = BIREMEClient()

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock, side_effect=Exception("Timeout")):
        response = await client.search("any query")

    assert response.status == SearchStatus.SOURCE_UNAVAILABLE
    assert response.database_used == "bireme"
