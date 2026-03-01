"""Tool extract_document."""

from __future__ import annotations

from typing import Any

from minerva.config import OcrConfig
from minerva.engine.ocr_engine import SuryaOcrEngine
from minerva.engine.pdf_parser import PdfParser
from minerva.engine.vision_engine import Llama4VisionEngine
from minerva.mcp.errors import ToolValidationError
from minerva.utils.anonymizer import hash_patient_id
from minerva.utils.file_utils import decode_base64_payload, normalize_file_type


async def run(arguments: dict[str, Any], config: OcrConfig) -> dict[str, Any]:
    file_content_base64 = str(arguments.get("file_content_base64", ""))
    file_type = normalize_file_type(str(arguments.get("file_type", "")))
    document_type = str(arguments.get("document_type", "generic"))
    patient_id = arguments.get("patient_id")
    if document_type not in {"lab_report", "discharge_summary", "prescription", "regulatory", "generic"}:
        raise ToolValidationError("document_type invalido")

    content = decode_base64_payload(file_content_base64)
    if file_type == "pdf":
        result = await PdfParser().parse(content)
        pages = 1
    elif file_type == "txt":
        raw = content.decode("utf-8", errors="ignore")
        result = {
            "raw_text": raw,
            "confidence_score": 0.98 if raw else 0.0,
            "processing_time_ms": 1,
            "engine_used": "txt-direct",
            "warnings": [],
        }
        pages = 1
    else:
        warnings: list[str] = []
        try:
            vision_result = await Llama4VisionEngine(config).extract_structured(content, document_type=document_type)
            result = vision_result
        except Exception:
            ocr_result = await SuryaOcrEngine().extract_text(content)
            result = ocr_result.model_dump(mode="json")
            warnings.append("llama4_vision_fallback_surya")
            result["warnings"] = list(result.get("warnings", [])) + warnings
        pages = 1

    raw_text = result["raw_text"] if isinstance(result, dict) else result.raw_text
    confidence = result["confidence_score"] if isinstance(result, dict) else result.confidence_score
    processing_time_ms = result["processing_time_ms"] if isinstance(result, dict) else result.processing_time_ms
    warnings = result["warnings"] if isinstance(result, dict) else result.warnings
    engine_used = result["engine_used"] if isinstance(result, dict) else result.engine_used

    structured: dict[str, Any] = {
        "document_type": document_type,
        "sections": {"full_text": raw_text},
    }
    if patient_id:
        structured["patient_name_hash"] = hash_patient_id(str(patient_id), config.lgpd_salt or "unsafe-dev-salt")

    response = {
        "raw_text": raw_text,
        "structured_data": structured,
        "confidence_score": confidence,
        "pages_processed": pages,
        "processing_time_ms": processing_time_ms,
        "engine_used": engine_used,
        "warnings": warnings,
    }
    if confidence < config.confidence_threshold_warn:
        response["low_confidence"] = True
    return response
