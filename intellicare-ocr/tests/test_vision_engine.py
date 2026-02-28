from __future__ import annotations

import asyncio
from urllib.error import URLError

from ocr.config import OcrConfig
from ocr.engine.vision_engine import Llama4VisionEngine


def test_vision_engine_is_available_when_model_exists(monkeypatch) -> None:
    engine = Llama4VisionEngine(OcrConfig(vision_model="llama4:scout"))
    monkeypatch.setattr(
        engine,
        "_http_json",
        lambda path, payload: {"models": [{"name": "llama4:scout"}]},
    )
    assert asyncio.run(engine.is_available()) is True


def test_vision_engine_extract_structured_returns_parsed_payload(monkeypatch) -> None:
    engine = Llama4VisionEngine(OcrConfig())
    monkeypatch.setattr(
        engine,
        "_http_json",
        lambda path, payload: {"response": '{"raw_text":"Texto OCR","confidence_score":0.91,"section":"A"}'},
    )
    result = asyncio.run(engine.extract_structured(b"image-bytes", document_type="lab_report"))
    assert result["engine_used"] == "llama4-vision"
    assert result["raw_text"] == "Texto OCR"
    assert result["structured_data"]["section"] == "A"
    assert result["confidence_score"] == 0.91


def test_vision_engine_extract_structured_handles_unavailable(monkeypatch) -> None:
    engine = Llama4VisionEngine(OcrConfig())

    def _raise(path, payload):
        raise URLError("down")

    monkeypatch.setattr(engine, "_http_json", _raise)
    try:
        asyncio.run(engine.extract_structured(b"image-bytes", document_type="generic"))
    except RuntimeError as exc:
        assert "llama4_unavailable" in str(exc)
    else:  # pragma: no cover
        assert False, "Esperava RuntimeError"
