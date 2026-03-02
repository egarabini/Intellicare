"""Tool parse_discharge_summary (implementacao inicial)."""

from __future__ import annotations

from typing import Any

from minerva.config import OcrConfig
from minerva.engine.discharge_extractor import DischargeExtractor
from minerva.mcp.errors import ToolValidationError
from minerva.mcp.tools.extract_document import run as extract_document_run


async def run(arguments: dict[str, Any], config: OcrConfig) -> dict[str, Any]:
    if not str(arguments.get("file_content_base64", "")).strip():
        raise ToolValidationError("file_content_base64 obrigatorio")
    extracted = await extract_document_run(
        {
            "file_content_base64": arguments.get("file_content_base64", ""),
            "file_type": arguments.get("file_type", "pdf"),
            "document_type": "discharge_summary",
            "patient_id": arguments.get("patient_id"),
        },
        config=config,
    )
    text = extracted["raw_text"]
    parsed = DischargeExtractor().extract(text)
    response = {
        "patient_id": arguments.get("patient_id"),
        "discharge_date": parsed["discharge_date"],
        "primary_diagnosis": parsed["primary_diagnosis"],
        "secondary_diagnoses": parsed["secondary_diagnoses"],
        "medications": parsed["medications"],
        "follow_up": parsed["follow_up"],
        "instructions": parsed["instructions"],
        "confidence_score": parsed["confidence_score"],
        "low_confidence": parsed["confidence_score"] < config.confidence_threshold_warn,
    }
    return response
