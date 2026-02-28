from __future__ import annotations

import asyncio

from ocr.engine.ocr_engine import SuryaOcrEngine
import ocr.engine.ocr_engine as engine_mod


def test_ocr_engine_fallback_when_backend_unavailable(monkeypatch) -> None:
    monkeypatch.setattr(engine_mod, "pytesseract", None)
    monkeypatch.setattr(engine_mod, "Image", None)

    engine = SuryaOcrEngine()
    result = asyncio.run(engine.extract_text(b"fake-bytes"))
    assert result.engine_used == "surya-fallback"
    assert "fallback" in result.raw_text


def test_ocr_engine_uses_tesseract_when_available(monkeypatch) -> None:
    class _FakePytesseract:
        @staticmethod
        def image_to_string(image, lang: str = "por") -> str:  # noqa: ANN001
            _ = image, lang
            return "texto reconhecido"

    class _FakeImageModule:
        @staticmethod
        def open(stream):  # noqa: ANN001
            _ = stream
            return object()

    monkeypatch.setattr(engine_mod, "pytesseract", _FakePytesseract())
    monkeypatch.setattr(engine_mod, "Image", _FakeImageModule())

    engine = SuryaOcrEngine()
    available = asyncio.run(engine.is_available())
    result = asyncio.run(engine.extract_text(b"fake-image"))

    assert available is True
    assert result.engine_used == "tesseract"
    assert result.raw_text == "texto reconhecido"
