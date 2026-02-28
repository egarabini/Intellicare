from __future__ import annotations

import base64
import asyncio

from ocr.config import OcrConfig
from ocr.mcp.server import OcrMcpServer


def test_mcp_server_unknown_tool_returns_failed() -> None:
    server = OcrMcpServer(config=OcrConfig())
    result = asyncio.run(server.call_tool("x_tool", {}))
    assert result["status"] == "failed"
    assert result["error_type"] == "unknown_tool"


def test_mcp_server_extract_document_returns_payload() -> None:
    server = OcrMcpServer(config=OcrConfig())
    text_b64 = base64.b64encode("texto clinico".encode("utf-8")).decode("utf-8")
    result = asyncio.run(
        server.call_tool(
            "extract_document",
            {"file_content_base64": text_b64, "file_type": "txt", "document_type": "generic"},
        )
    )
    assert result["status"] == "success"
    assert "payload" in result
    assert result["payload"]["confidence_score"] >= 0.0


def test_mcp_server_returns_validation_error_for_bad_arguments() -> None:
    server = OcrMcpServer(config=OcrConfig())
    result = asyncio.run(server.call_tool("search_documents", {"query": "creatinina", "patient_id": "p1", "top_k": 100}))
    assert result["status"] == "failed"
    assert result["error_type"] == "validation_error"
