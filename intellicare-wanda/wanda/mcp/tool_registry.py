"""Unified Tool Registry — HTTP + MCP tools (EF-W011).

Provides a single registry that joins HTTP module endpoints
and MCP tool invocations for use by the orchestrator and
future LangGraph integration.
"""

import logging
from typing import Any, Callable, Optional

from wanda.mcp.client import WandaMCPClient
from wanda.mcp.models import MCPToolInfo

logger = logging.getLogger(__name__)


class ToolDefinition:
    """A unified tool definition (HTTP or MCP)."""

    def __init__(
        self,
        name: str,
        description: str,
        source_type: str,  # "http" | "mcp"
        module_name: str,
        invoke: Callable,
    ):
        self.name = name
        self.description = description
        self.source_type = source_type
        self.module_name = module_name
        self.invoke = invoke

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "source_type": self.source_type,
            "module_name": self.module_name,
        }


# MCP tool descriptions (optimized for LLM routing)
MCP_TOOL_DESCRIPTIONS: dict[str, str] = {
    # MINERVA tools
    "parse_lab_result": (
        "Extrai resultados de exames laboratoriais de PDFs ou imagens. "
        "Use quando o usuario enviar um laudo em PDF ou quando precisar "
        "interpretar exames de outro sistema. "
        "Retorna dict compativel com Florence para interpretacao."
    ),
    "extract_document": (
        "Extrai texto e metadados de documentos medicos (PDF, DOCX, imagem). "
        "Use para documentos genericos que nao sao laudos laboratoriais."
    ),
    "ocr_image": (
        "OCR de imagem medica. Converte imagem em texto estruturado. "
        "Use para fotos de receitas, exames escritos a mao."
    ),
    "parse_discharge_summary": (
        "Extrai dados estruturados de um sumario de alta hospitalar. "
        "Retorna diagnosticos, procedimentos, medicamentos na alta."
    ),
    "search_documents": (
        "Busca semantica no historico de documentos do paciente. "
        "Use para encontrar laudos, prescricoes e sumarios anteriores. "
        "Requer patient_id."
    ),
    "index_document": (
        "Indexa um documento no repositorio do paciente. "
        "Usado internamente apos OCR/extracao."
    ),
    # PIERRE tools
    "web_search": (
        "Busca web em tempo real via Tavily. "
        "Use para: guidelines atualizados, aprovacoes ANVISA recentes, "
        "noticias medicas, documentos regulatorios. "
        "NAO use para conhecimento clinico geral."
    ),
    "search_medical_literature": (
        "Busca na literatura medica indexada (PubMed, BVS/BIREME, SciELO). "
        "Use para: ensaios clinicos, revisoes sistematicas, evidencias. "
        "Prefira sobre web_search para perguntas sobre evidencias cientificas."
    ),
    "check_regulatory": (
        "Verifica status regulatorio de medicamentos, dispositivos e procedimentos. "
        "Use para: aprovacoes ANVISA, cobertura ANS, resolucoes CFM."
    ),
    "analyze_text": (
        "Analise profunda de texto longo via Qwen2.5-72B. "
        "Use para: extrair pontos de um guideline, comparar protocolos, "
        "sintetizar resultados. Custo: alto (LLM local)."
    ),
    "summarize_document": (
        "Resume documentos longos em pontos principais. "
        "Use para: resumir artigos, guidelines, prontuarios extensos."
    ),
    "translate_to_portuguese": (
        "Traduz texto para portugues brasileiro. "
        "Use para: artigos em ingles, guidelines internacionais."
    ),
}


class WandaToolRegistry:
    """Unified registry of all WANDA tools (HTTP + MCP).

    Provides a single list of available tools for the orchestrator
    and future LangGraph integration (EF-W005).
    """

    def __init__(self, mcp_client: Optional[WandaMCPClient] = None):
        self._mcp_client = mcp_client
        self._tools: dict[str, ToolDefinition] = {}

    async def build(self) -> None:
        """Build the tool registry from all available sources."""
        self._tools.clear()

        if self._mcp_client:
            await self._register_mcp_tools()

        logger.info("Tool registry built: %d tools", len(self._tools))

    async def _register_mcp_tools(self) -> None:
        """Register tools from connected MCP Servers."""
        all_tools = await self._mcp_client.list_tools()

        for module_name, tools in all_tools.items():
            for tool_dict in tools:
                tool_name = tool_dict["name"]
                description = MCP_TOOL_DESCRIPTIONS.get(
                    tool_name, tool_dict.get("description", "")
                )

                async def make_invoker(mn: str, tn: str):
                    async def invoke(params: dict, correlation_id: str = "") -> dict:
                        return await self._mcp_client.call_tool(
                            module_name=mn,
                            tool_name=tn,
                            params=params,
                            correlation_id=correlation_id,
                        )
                    return invoke

                invoker = await make_invoker(module_name, tool_name)

                self._tools[tool_name] = ToolDefinition(
                    name=tool_name,
                    description=description,
                    source_type="mcp",
                    module_name=module_name,
                    invoke=invoker,
                )

    def get_all_tools(self) -> list[ToolDefinition]:
        """Return all registered tools."""
        return list(self._tools.values())

    def get_tool(self, name: str) -> Optional[ToolDefinition]:
        """Get a tool by name."""
        return self._tools.get(name)

    def get_tools_by_module(self, module_name: str) -> list[ToolDefinition]:
        """Get all tools from a specific module."""
        return [t for t in self._tools.values() if t.module_name == module_name]

    def get_tool_descriptions(self) -> list[dict[str, str]]:
        """Get tool name+description pairs (for LLM prompts)."""
        return [
            {"name": t.name, "description": t.description}
            for t in self._tools.values()
        ]

    @property
    def total_tools(self) -> int:
        return len(self._tools)
