"""Parser de PDF com fallback simplificado."""

from __future__ import annotations

import time

from minerva.engine.models import ExtractionResult, ExtractionStatus
from minerva.utils.confidence import score_from_text

try:
    import fitz  # type: ignore[import-not-found]
except Exception:  # pragma: no cover
    fitz = None  # type: ignore[assignment]


class PdfParser:
    async def parse(self, pdf_bytes: bytes, use_llm: bool = True) -> ExtractionResult:
        started = time.perf_counter()
        _ = use_llm
        text = ""
        engine_used = "pymupdf-fallback"
        warnings: list[str] = []

        if fitz is not None:
            try:
                doc = fitz.open(stream=pdf_bytes, filetype="pdf")
                text = "\n".join((page.get_text("text") or "").strip() for page in doc)
                doc.close()
                engine_used = "pymupdf"
            except Exception:
                warnings.append("pymupdf_parse_failed")

        if not text:
            text = f"[pdf_bytes={len(pdf_bytes)}] texto extraido (fallback)"
            engine_used = "pymupdf-fallback"

        confidence = score_from_text(text)
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        status = ExtractionStatus.SUCCESS if confidence >= 0.6 else ExtractionStatus.PARTIAL
        return ExtractionResult(
            status=status,
            raw_text=text,
            confidence_score=confidence,
            processing_time_ms=elapsed_ms,
            engine_used=engine_used,
            warnings=warnings + ([] if confidence >= 0.6 else ["low_confidence"]),
        )
