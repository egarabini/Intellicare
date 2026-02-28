"""PubMedClient — busca em PubMed via NCBI E-utilities."""

from __future__ import annotations

import logging
import time
from typing import Optional
from xml.etree import ElementTree as ET

import httpx

from pierre.models import LiteratureSearchResponse, MedicalArticle, SearchStatus

logger = logging.getLogger(__name__)

BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"


class PubMedClient:
    """
    Cliente para PubMed via NCBI E-utilities API.

    Endpoints:
    - esearch.fcgi — busca de PMIDs
    - efetch.fcgi  — busca de abstracts por PMID (XML)

    API Key: gratuita — sem key: 3 req/s, com key: 10 req/s.
    """

    def __init__(self, api_key: str = "", timeout: float = 30.0):
        self._api_key = api_key
        self._timeout = timeout

    async def search(
        self,
        query: str,
        max_results: int = 5,
        study_type: str = "any",
        date_from: Optional[str] = None,
        language: str = "any",
    ) -> LiteratureSearchResponse:
        """Pipeline: esearch → efetch → parse XML → list[MedicalArticle]."""
        t0 = time.monotonic()

        try:
            # 1. Build query
            full_query = self._build_query(query, study_type, date_from, language)

            # 2. esearch: query → list[pmid]
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                pmids = await self._esearch(client, full_query, max_results)
                if not pmids:
                    return LiteratureSearchResponse(
                        status=SearchStatus.NO_RESULTS,
                        database_used="pubmed",
                        query_time_ms=int((time.monotonic() - t0) * 1000),
                    )

                # 3. efetch: pmids → XML abstracts
                xml_data = await self._efetch(client, pmids)

            # 4. Parse XML → articles
            articles = self._parse_articles(xml_data)

            return LiteratureSearchResponse(
                status=SearchStatus.SUCCESS,
                articles=articles,
                total_found=len(articles),
                returned=len(articles),
                database_used="pubmed",
                query_time_ms=int((time.monotonic() - t0) * 1000),
            )
        except Exception as e:
            logger.error("PubMed search falhou: %s", e)
            return LiteratureSearchResponse(
                status=SearchStatus.SOURCE_UNAVAILABLE,
                database_used="pubmed",
                query_time_ms=int((time.monotonic() - t0) * 1000),
            )

    async def _esearch(self, client: httpx.AsyncClient, query: str, max_results: int) -> list[str]:
        """Busca PMIDs via esearch."""
        params: dict = {
            "db": "pubmed",
            "term": query,
            "retmax": max_results,
            "retmode": "json",
            "sort": "relevance",
        }
        if self._api_key:
            params["api_key"] = self._api_key

        resp = await client.get(f"{BASE_URL}/esearch.fcgi", params=params)
        resp.raise_for_status()
        data = resp.json()
        return data.get("esearchresult", {}).get("idlist", [])

    async def _efetch(self, client: httpx.AsyncClient, pmids: list[str]) -> str:
        """Busca abstracts em XML via efetch."""
        params: dict = {
            "db": "pubmed",
            "id": ",".join(pmids),
            "rettype": "abstract",
            "retmode": "xml",
        }
        if self._api_key:
            params["api_key"] = self._api_key

        resp = await client.get(f"{BASE_URL}/efetch.fcgi", params=params)
        resp.raise_for_status()
        return resp.text

    def _parse_articles(self, xml_data: str) -> list[MedicalArticle]:
        """Parseia XML PubMed → list[MedicalArticle]."""
        articles = []
        try:
            root = ET.fromstring(xml_data)
        except ET.ParseError:
            logger.error("Falha ao parsear XML PubMed")
            return articles

        for article_elem in root.findall(".//PubmedArticle"):
            try:
                articles.append(self._parse_one_article(article_elem))
            except Exception as e:
                logger.warning("Falha ao parsear artigo: %s", e)
                continue
        return articles

    def _parse_one_article(self, elem: ET.Element) -> MedicalArticle:
        """Parseia um PubmedArticle XML element."""
        medline = elem.find(".//MedlineCitation")
        article = medline.find(".//Article") if medline is not None else None

        # PMID
        pmid_el = medline.find(".//PMID") if medline is not None else None
        pmid = pmid_el.text if pmid_el is not None else None

        # Title
        title_el = article.find(".//ArticleTitle") if article is not None else None
        title = title_el.text or "" if title_el is not None else ""

        # Authors
        authors = []
        if article is not None:
            for author in article.findall(".//Author"):
                last = author.findtext("LastName", "")
                first = author.findtext("Initials", "")
                if last:
                    authors.append(f"{last} {first}".strip())

        # Journal
        journal_el = article.find(".//Journal/Title") if article is not None else None
        journal = journal_el.text or "" if journal_el is not None else ""

        # Year
        year = 0
        year_el = article.find(".//Journal/JournalIssue/PubDate/Year") if article is not None else None
        if year_el is not None and year_el.text:
            try:
                year = int(year_el.text)
            except ValueError:
                pass

        # Abstract
        abstract_parts = []
        if article is not None:
            for abs_text in article.findall(".//Abstract/AbstractText"):
                label = abs_text.get("Label", "")
                text = abs_text.text or ""
                if label:
                    abstract_parts.append(f"{label}: {text}")
                else:
                    abstract_parts.append(text)
        abstract = " ".join(abstract_parts)

        # Conclusion (last section of structured abstract or last sentence)
        conclusion = None
        for abs_text in (article.findall(".//Abstract/AbstractText") if article is not None else []):
            if abs_text.get("Label", "").upper() in ("CONCLUSION", "CONCLUSIONS"):
                conclusion = abs_text.text

        # DOI
        doi = None
        for id_elem in elem.findall(".//ArticleIdList/ArticleId"):
            if id_elem.get("IdType") == "doi":
                doi = id_elem.text

        # Study type classification
        pub_types = []
        if medline is not None:
            for pt in medline.findall(".//PublicationTypeList/PublicationType"):
                if pt.text:
                    pub_types.append(pt.text.lower())
        study_type = self._classify_study_type(pub_types, title)
        evidence_level = self._classify_evidence_level(study_type)

        return MedicalArticle(
            pmid=pmid,
            title=title,
            authors=authors[:5],  # Limitar a 5 autores
            journal=journal,
            year=year,
            abstract=abstract,
            conclusion=conclusion,
            study_type=study_type,
            url=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}" if pmid else "",
            evidence_level=evidence_level,
            doi=doi,
        )

    @staticmethod
    def _classify_study_type(pub_types: list[str], title: str) -> str:
        """Classifica tipo de estudo pelos publication types e titulo."""
        title_lower = title.lower()
        types_str = " ".join(pub_types)

        if "meta-analysis" in types_str or "meta-analysis" in title_lower:
            return "meta_analysis"
        if "systematic review" in types_str or "systematic review" in title_lower:
            return "systematic_review"
        if "randomized controlled trial" in types_str or "randomized" in title_lower:
            return "rct"
        if "guideline" in types_str or "practice guideline" in types_str:
            return "guideline"
        if "cohort" in title_lower:
            return "cohort"
        if "case report" in types_str:
            return "case_report"
        return "other"

    @staticmethod
    def _classify_evidence_level(study_type: str) -> str:
        """Classifica nivel de evidencia pelo tipo de estudo."""
        mapping = {
            "meta_analysis": "A",
            "systematic_review": "A",
            "guideline": "A",
            "rct": "B",
            "cohort": "C",
            "case_control": "C",
            "case_report": "D",
        }
        return mapping.get(study_type, "D")

    def _build_query(self, query: str, study_type: str, date_from: Optional[str], language: str) -> str:
        """Constroi query PubMed com filtros."""
        parts = [query]

        type_filters = {
            "rct": "Randomized Controlled Trial[pt]",
            "systematic_review": "Systematic Review[pt]",
            "meta_analysis": "Meta-Analysis[pt]",
            "guideline": "Practice Guideline[pt]",
        }
        if study_type in type_filters:
            parts.append(type_filters[study_type])

        lang_filters = {
            "pt": "Portuguese[la]",
            "en": "English[la]",
            "es": "Spanish[la]",
        }
        if language in lang_filters:
            parts.append(lang_filters[language])

        if date_from:
            parts.append(f"{date_from}/01/01:3000[dp]")

        return " AND ".join(parts)

    async def is_available(self) -> bool:
        """Verifica se PubMed esta acessivel."""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    f"{BASE_URL}/esearch.fcgi",
                    params={"db": "pubmed", "term": "test", "retmax": 1, "retmode": "json"},
                )
                return resp.status_code == 200
        except Exception:
            return False
