from __future__ import annotations

import asyncio
import base64

from minerva.config import OcrConfig
from minerva.engine.models import ExtractionResult, ExtractionStatus
from minerva.mcp.tools.extract_document import run as extract_document_run
from minerva.mcp.tools.index_document import run as index_document_run
from minerva.mcp.tools.ocr_image import run as ocr_image_run
from minerva.mcp.tools.parse_discharge_summary import run as parse_discharge_summary_run
from minerva.mcp.tools.parse_lab_result import run as parse_lab_result_run
from minerva.mcp.tools.search_documents import run as search_documents_run


def test_extract_document_tool_for_txt() -> None:
    content_b64 = base64.b64encode("alta hospitalar 2026-02-10".encode("utf-8")).decode("utf-8")
    result = asyncio.run(
        extract_document_run(
            {
                "file_content_base64": content_b64,
                "file_type": "txt",
                "document_type": "discharge_summary",
                "patient_id": "p-123",
            },
            config=OcrConfig(lgpd_salt="tests"),
        )
    )
    assert result["raw_text"]
    assert result["structured_data"]["document_type"] == "discharge_summary"
    assert result["structured_data"]["patient_name_hash"].startswith("sha256:")


def test_extract_document_tool_for_image_uses_vision(monkeypatch) -> None:
    async def _fake_extract(self, image: bytes, document_type: str) -> dict:
        _ = image
        return {
            "raw_text": "texto visao",
            "structured_data": {"doc_type": document_type},
            "confidence_score": 0.92,
            "processing_time_ms": 5,
            "engine_used": "llama4-vision",
            "warnings": [],
        }

    monkeypatch.setattr(
        "minerva.mcp.tools.extract_document.Llama4VisionEngine.extract_structured",
        _fake_extract,
    )
    image_b64 = base64.b64encode(b"fake-image").decode("utf-8")
    result = asyncio.run(
        extract_document_run(
            {
                "file_content_base64": image_b64,
                "file_type": "png",
                "document_type": "generic",
            },
            config=OcrConfig(),
        )
    )
    assert result["raw_text"] == "texto visao"
    assert result["confidence_score"] == 0.92


def test_extract_document_tool_for_image_falls_back_to_surya(monkeypatch) -> None:
    async def _raise(self, image: bytes, document_type: str) -> dict:
        _ = image, document_type
        raise RuntimeError("llama4_unavailable")

    async def _fake_surya(self, image: bytes, language: str = "pt-BR") -> ExtractionResult:
        _ = image, language
        return ExtractionResult(
            status=ExtractionStatus.SUCCESS,
            raw_text="texto fallback",
            confidence_score=0.88,
            processing_time_ms=4,
            engine_used="surya-fallback",
            warnings=[],
        )

    monkeypatch.setattr("minerva.mcp.tools.extract_document.Llama4VisionEngine.extract_structured", _raise)
    monkeypatch.setattr("minerva.mcp.tools.extract_document.SuryaOcrEngine.extract_text", _fake_surya)
    image_b64 = base64.b64encode(b"fake-image").decode("utf-8")
    result = asyncio.run(
        extract_document_run(
            {
                "file_content_base64": image_b64,
                "file_type": "png",
                "document_type": "generic",
            },
            config=OcrConfig(),
        )
    )
    assert result["raw_text"] == "texto fallback"
    assert "llama4_vision_fallback_surya" in result.get("warnings", [])


def test_ocr_image_tool_returns_expected_contract() -> None:
    image_b64 = base64.b64encode(b"fake-image-data").decode("utf-8")
    result = asyncio.run(ocr_image_run({"image_base64": image_b64, "image_type": "png"}))
    assert "extracted_text" in result
    assert "confidence_score" in result
    assert "processing_time_ms" in result


def test_parse_lab_result_tool_with_document_text() -> None:
    result = asyncio.run(
        parse_lab_result_run(
            {"document_text": "Creatinina 2,4\nPotassio 5.1"},
            config=OcrConfig(),
        )
    )
    assert result["lab_results"]["creatinine"] == 2.4
    assert result["lab_results"]["potassium"] == 5.1
    assert result["confidence_score"] >= 0.6


def test_parse_discharge_summary_tool_from_txt_payload() -> None:
    text = (
        "Alta em 2026-02-10 CID N18.3 paciente estavel. "
        "Metformina 500mg 2x ao dia."
    )
    text_b64 = base64.b64encode(text.encode("utf-8")).decode("utf-8")
    result = asyncio.run(
        parse_discharge_summary_run(
            {
                "file_content_base64": text_b64,
                "file_type": "txt",
                "patient_id": "patient-a",
            },
            config=OcrConfig(),
        )
    )
    assert result["patient_id"] == "patient-a"
    assert result["discharge_date"] == "2026-02-10"
    assert result["primary_diagnosis"]["cid10"] == "N18.3"


def test_index_and_search_tools_flow() -> None:
    config = OcrConfig(lgpd_salt="tests")
    indexed = asyncio.run(
        index_document_run(
            {
                "document_text": "Creatinina 2.1 mg/dL e potassio 5.0",
                "document_type": "lab_report",
                "patient_id": "patient-z",
                "metadata": {"source": "Lab A", "date": "2026-02-10"},
            },
            config=config,
        )
    )
    searched = asyncio.run(
        search_documents_run(
            {
                "query": "creatinina potassio",
                "patient_id": "patient-z",
                "document_type": "lab_report",
                "top_k": 3,
            },
            config=config,
        )
    )
    assert indexed["status"] in {"indexed", "deduplicated"}
    assert searched["total_found"] >= 1
    assert searched["patient_document_count"] >= 1
