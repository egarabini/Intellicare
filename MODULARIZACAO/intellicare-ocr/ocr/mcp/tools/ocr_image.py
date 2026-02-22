"""Tool ocr_image."""

from __future__ import annotations

from typing import Any

from ocr.engine.ocr_engine import SuryaOcrEngine
from ocr.mcp.errors import ToolValidationError
from ocr.utils.file_utils import decode_base64_payload


async def run(arguments: dict[str, Any]) -> dict[str, Any]:
    image_base64 = str(arguments.get("image_base64", ""))
    image_type = str(arguments.get("image_type", "")).strip().lower()
    if image_type not in {"jpeg", "png", "tiff", "dicom_text"}:
        raise ToolValidationError("image_type invalido")
    content = decode_base64_payload(image_base64)
    result = await SuryaOcrEngine().extract_text(content)
    low_regions = []
    if result.confidence_score < 0.6:
        low_regions.append({"region": "full", "text": "...", "confidence": result.confidence_score})
    return {
        "extracted_text": result.raw_text,
        "confidence_score": result.confidence_score,
        "low_confidence_regions": low_regions,
        "processing_time_ms": result.processing_time_ms,
    }
