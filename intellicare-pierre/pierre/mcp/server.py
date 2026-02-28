"""PierreMCPServer — MCP Server com 6 tools de inteligencia externa."""

from __future__ import annotations

import json
import logging
from typing import Any

from mcp.server import Server
from mcp.types import TextContent, Tool

from pierre.cache.search_cache import SearchCache
from pierre.config import PierreConfig
from pierre.integrations.knowledge_client import KnowledgeClient
from pierre.llm.qwen_client import QwenClient
from pierre.llm.url_fetcher import URLFetcher
from pierre.mcp.schemas import (
    ANALYZE_TEXT_SCHEMA,
    CHECK_REGULATORY_SCHEMA,
    SEARCH_MEDICAL_LITERATURE_SCHEMA,
    SUMMARIZE_DOCUMENT_SCHEMA,
    TRANSLATE_TO_PORTUGUESE_SCHEMA,
    WEB_SEARCH_SCHEMA,
)
from pierre.mcp.tools.analyze_text import handle_analyze_text
from pierre.mcp.tools.check_regulatory import handle_check_regulatory
from pierre.mcp.tools.search_medical_literature import handle_search_medical_literature
from pierre.mcp.tools.summarize_document import handle_summarize_document
from pierre.mcp.tools.translate_to_portuguese import handle_translate_to_portuguese
from pierre.mcp.tools.web_search import handle_web_search
from pierre.rate_limiter.limiter import TavilyRateLimiter
from pierre.search.bireme_client import BIREMEClient
from pierre.search.pubmed_client import PubMedClient
from pierre.search.regulatory_client import RegulatoryClient
from pierre.search.scielo_client import SciELOClient
from pierre.search.tavily_client import TavilySearchClient

logger = logging.getLogger(__name__)


class PierreMCPServer:
    """
    MCP Server para intellicare-pierre.
    Expoe 6 tools via protocolo MCP sobre HTTP SSE.
    """

    def __init__(self, config: PierreConfig):
        self._config = config
        self._server = Server("intellicare-pierre")

        # Inicializar componentes compartilhados
        self._cache = SearchCache(config.redis_url, config.cache_enabled)
        self._rate_limiter = TavilyRateLimiter(config.tavily_rate_limit_per_hour)

        # Clientes de busca
        self._tavily = TavilySearchClient(
            api_key=config.tavily_api_key,
            cache=self._cache,
            rate_limiter=self._rate_limiter,
        )
        self._pubmed = PubMedClient(api_key=config.pubmed_api_key)
        self._bireme = BIREMEClient()
        self._scielo = SciELOClient()
        self._regulatory = RegulatoryClient(self._tavily, self._cache)
        self._knowledge_client = None
        if config.enable_knowledge_integration:
            self._knowledge_client = KnowledgeClient(
                base_url=config.knowledge_base_url,
                timeout_seconds=config.knowledge_timeout_seconds,
            )

        # LLM
        self._qwen = QwenClient(
            ollama_url=config.ollama_url,
            model=config.llm_model,
            model_fallback=config.llm_model_fallback,
            timeout=config.llm_timeout_seconds,
            max_tokens=config.llm_max_tokens,
        )
        self._url_fetcher = URLFetcher()

        # Registrar handlers MCP
        self._register_handlers()

    @property
    def server(self) -> Server:
        """Acesso ao MCP Server subjacente."""
        return self._server

    def _register_handlers(self) -> None:
        """Registra list_tools e call_tool no MCP Server."""

        @self._server.list_tools()
        async def handle_list_tools() -> list[Tool]:
            return [
                Tool(
                    name="web_search",
                    description=(
                        "Busca web em tempo real via Tavily. Use para encontrar guidelines "
                        "atualizados, informacoes recentes de medicamentos, noticias regulatorias "
                        "ou qualquer informacao medica nao coberta pelos outros agentes."
                    ),
                    inputSchema=WEB_SEARCH_SCHEMA,
                ),
                Tool(
                    name="search_medical_literature",
                    description=(
                        "Busca em PubMed e BVS/BIREME (literatura medica indexada). "
                        "Use para encontrar evidencias cientificas, ensaios clinicos, "
                        "revisoes sistematicas e meta-analises."
                    ),
                    inputSchema=SEARCH_MEDICAL_LITERATURE_SCHEMA,
                ),
                Tool(
                    name="check_regulatory",
                    description=(
                        "Verifica status regulatorio de medicamentos e dispositivos no Brasil. "
                        "Use para confirmar aprovacao ANVISA, cobertura ANS ou regulamentacao CFM."
                    ),
                    inputSchema=CHECK_REGULATORY_SCHEMA,
                ),
                Tool(
                    name="analyze_text",
                    description=(
                        "Analise profunda de texto medico via LLM local (Qwen2.5). "
                        "Use para extrair informacoes especificas, responder perguntas sobre "
                        "um texto, comparar documentos ou sintetizar conteudo complexo."
                    ),
                    inputSchema=ANALYZE_TEXT_SCHEMA,
                ),
                Tool(
                    name="summarize_document",
                    description=(
                        "Resume documento longo (guideline, artigo, relatorio) em formato "
                        "clinicamente acionavel. Aceita texto direto ou URL publica."
                    ),
                    inputSchema=SUMMARIZE_DOCUMENT_SCHEMA,
                ),
                Tool(
                    name="translate_to_portuguese",
                    description=(
                        "Traduz textos medicos para PT-BR com terminologia medica correta. "
                        "Preserva termos tecnicos sem traducao consolidada."
                    ),
                    inputSchema=TRANSLATE_TO_PORTUGUESE_SCHEMA,
                ),
            ]

        @self._server.call_tool()
        async def handle_call_tool(name: str, arguments: dict) -> list[TextContent]:
            logger.info("MCP call_tool: %s", name)
            try:
                result = await self._route_tool(name, arguments)
                return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]
            except Exception as e:
                logger.error("MCP tool %s falhou: %s", name, e)
                error_result = {
                    "error": str(e),
                    "tool": name,
                    "status": "error",
                }
                return [TextContent(type="text", text=json.dumps(error_result, ensure_ascii=False))]

    async def _route_tool(self, name: str, arguments: dict) -> dict:
        """Roteia chamada para handler apropriado."""
        if name == "web_search":
            return await handle_web_search(self._tavily, arguments)
        elif name == "search_medical_literature":
            return await handle_search_medical_literature(
                self._pubmed,
                self._bireme,
                self._scielo,
                arguments,
                self._knowledge_client,
            )
        elif name == "check_regulatory":
            return await handle_check_regulatory(self._regulatory, arguments)
        elif name == "analyze_text":
            return await handle_analyze_text(self._qwen, arguments)
        elif name == "summarize_document":
            return await handle_summarize_document(self._qwen, self._url_fetcher, arguments)
        elif name == "translate_to_portuguese":
            return await handle_translate_to_portuguese(self._qwen, arguments)
        else:
            raise ValueError(f"Tool desconhecida: {name}")

    async def get_health(self) -> dict[str, Any]:
        """Retorna status de saude de cada componente."""
        tavily_ok = await self._tavily.is_available()
        cache_ok = await self._cache.is_available()
        pubmed_ok = await self._pubmed.is_available()
        qwen_ok = await self._qwen.is_available()
        rate_status = await self._rate_limiter.get_status()

        components = {
            "tavily": {"available": tavily_ok, "configured": self._config.tavily_configured},
            "pubmed": {"available": pubmed_ok, "has_api_key": self._config.pubmed_has_key},
            "redis_cache": {"available": cache_ok, "enabled": self._config.cache_enabled},
            "ollama_llm": {"available": qwen_ok, "model": self._config.llm_model},
            "rate_limiter": rate_status,
        }

        all_critical_ok = tavily_ok or pubmed_ok  # Pelo menos uma fonte de busca

        return {
            "status": "healthy" if all_critical_ok else "degraded",
            "components": components,
        }

    async def shutdown(self) -> None:
        """Cleanup de recursos."""
        await self._cache.close()
