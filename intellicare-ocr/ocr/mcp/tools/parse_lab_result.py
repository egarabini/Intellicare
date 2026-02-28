"""Tool parse_lab_result (implementacao inicial)."""

from __future__ import annotations

from typing import Any

from ocr.config import OcrConfig
from ocr.engine.lab_extractor import LabResultExtractor
from ocr.mcp.errors import ToolValidationError
from ocr.mcp.tools.extract_document import run as extract_document_run


async def run(arguments: dict[str, Any], config: OcrConfig) -> dict[str, Any]:
    text = arguments.get("document_text")
    if text is not None and not str(text).strip():
        raise ToolValidationError("document_text vazio")
    if not text:
        if not arguments.get("file_content_base64"):
            raise ToolValidationError("informe document_text ou file_content_base64")
        extracted = await extract_document_run(
            {
                "file_content_base64": arguments.get("file_content_base64", ""),
                "file_type": arguments.get("file_type", "pdf"),
                "document_type": "lab_report",
            },
            config=config,
        )
        text = extracted["raw_text"]

    raw = str(text)
    lab_results, unrecognized_items, confidence = LabResultExtractor().extract(raw)
    return {
        "lab_results": lab_results,
        "metadata": {},
        "unrecognized_items": unrecognized_items,
        "confidence_score": confidence,
        "low_confidence": confidence < config.confidence_threshold_warn,
    }
