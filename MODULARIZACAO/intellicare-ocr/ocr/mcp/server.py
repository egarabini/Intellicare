"""Facade MCP para tools do intellicare-ocr."""

from __future__ import annotations

from typing import Any

from ocr.config import OcrConfig
from ocr.mcp.errors import ToolError
from ocr.mcp.schemas import TOOLS
from ocr.mcp.tools.extract_document import run as extract_document_run
from ocr.mcp.tools.index_document import run as index_document_run
from ocr.mcp.tools.ocr_image import run as ocr_image_run
from ocr.mcp.tools.parse_discharge_summary import run as parse_discharge_summary_run
from ocr.mcp.tools.parse_lab_result import run as parse_lab_result_run
from ocr.mcp.tools.search_documents import run as search_documents_run


class OcrMcpServer:
    def __init__(self, config: OcrConfig):
        self._config = config

    def list_tools(self) -> list[dict]:
        return TOOLS

    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if tool_name not in {tool["name"] for tool in TOOLS}:
            return {"status": "failed", "error_type": "unknown_tool", "error": f"Tool desconhecida: {tool_name}"}
        try:
            if tool_name == "extract_document":
                payload = await extract_document_run(arguments, self._config)
            elif tool_name == "ocr_image":
                payload = await ocr_image_run(arguments)
            elif tool_name == "parse_lab_result":
                payload = await parse_lab_result_run(arguments, self._config)
            elif tool_name == "parse_discharge_summary":
                payload = await parse_discharge_summary_run(arguments, self._config)
            elif tool_name == "search_documents":
                payload = await search_documents_run(arguments, self._config)
            elif tool_name == "index_document":
                payload = await index_document_run(arguments, self._config)
            else:  # pragma: no cover
                return {"status": "failed", "error_type": "unknown_tool", "error": f"Tool desconhecida: {tool_name}"}
            return {"status": "success", "tool": tool_name, "payload": payload}
        except ToolError as exc:
            return {"status": "failed", "error_type": exc.error_type, "error": str(exc), "tool": tool_name}
        except Exception as exc:
            return {"status": "failed", "error_type": "processing_error", "error": str(exc), "tool": tool_name}
