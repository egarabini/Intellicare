"""Testes do PubMedClient — 4 testes."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from superz.models import SearchStatus
from superz.search.pubmed_client import PubMedClient

# XML de exemplo PubMed
PUBMED_XML_SAMPLE = """<?xml version="1.0"?>
<PubmedArticleSet>
  <PubmedArticle>
    <MedlineCitation>
      <PMID>38234567</PMID>
      <Article>
        <ArticleTitle>Safety of Metformin in CKD Patients with eGFR 30-45</ArticleTitle>
        <Journal>
          <Title>N Engl J Med</Title>
          <JournalIssue>
            <PubDate><Year>2024</Year></PubDate>
          </JournalIssue>
        </Journal>
        <AuthorList>
          <Author><LastName>Smith</LastName><Initials>J</Initials></Author>
          <Author><LastName>Jones</LastName><Initials>A</Initials></Author>
        </AuthorList>
        <Abstract>
          <AbstractText Label="BACKGROUND">Metformin use in CKD is debated.</AbstractText>
          <AbstractText Label="CONCLUSION">Metformin appears safe in CKD with eGFR above 30.</AbstractText>
        </Abstract>
      </Article>
      <PublicationTypeList>
        <PublicationType>Meta-Analysis</PublicationType>
      </PublicationTypeList>
    </MedlineCitation>
    <ArticleIdList>
      <ArticleId IdType="doi">10.1056/NEJMoa2024567</ArticleId>
    </ArticleIdList>
  </PubmedArticle>
</PubmedArticleSet>"""


@pytest.mark.asyncio
async def test_pubmed_search_success(pubmed_client):
    """Busca PubMed retorna artigos parseados corretamente."""
    with patch.object(pubmed_client, "_esearch", new_callable=AsyncMock) as mock_search, \
         patch.object(pubmed_client, "_efetch", new_callable=AsyncMock) as mock_fetch:
        mock_search.return_value = ["38234567"]
        mock_fetch.return_value = PUBMED_XML_SAMPLE

        response = await pubmed_client.search("metformin CKD eGFR 30")

    assert response.status == SearchStatus.SUCCESS
    assert len(response.articles) == 1
    article = response.articles[0]
    assert article.pmid == "38234567"
    assert "Metformin" in article.title
    assert article.journal == "N Engl J Med"
    assert article.year == 2024
    assert article.study_type == "meta_analysis"
    assert article.evidence_level == "A"
    assert article.doi == "10.1056/NEJMoa2024567"
    assert article.conclusion == "Metformin appears safe in CKD with eGFR above 30."


@pytest.mark.asyncio
async def test_pubmed_search_with_date_filter(pubmed_client):
    """Filtro de data e construido corretamente na query."""
    query = pubmed_client._build_query("SGLT2 CKD", "rct", "2020", "en")
    assert "Randomized Controlled Trial[pt]" in query
    assert "English[la]" in query
    assert "2020/01/01:3000[dp]" in query


@pytest.mark.asyncio
async def test_pubmed_search_study_type_filter(pubmed_client):
    """Filtro de study type e aplicado."""
    query = pubmed_client._build_query("diabetes", "meta_analysis", None, "any")
    assert "Meta-Analysis[pt]" in query


@pytest.mark.asyncio
async def test_pubmed_search_unavailable(pubmed_client):
    """PubMed indisponivel retorna SOURCE_UNAVAILABLE."""
    with patch.object(pubmed_client, "_esearch", new_callable=AsyncMock) as mock_search:
        mock_search.side_effect = Exception("Connection timeout")
        response = await pubmed_client.search("any query")

    assert response.status == SearchStatus.SOURCE_UNAVAILABLE
    assert response.database_used == "pubmed"
