"""Engine MINERVA simplificado com fallback local."""

from __future__ import annotations

import io
import time

from minerva.engine.models import ExtractionResult, ExtractionStatus
from minerva.utils.confidence import score_from_text

try:
    import pytesseract
except Exception:  # pragma: no cover
    pytesseract = None  # type: ignore[assignment]

try:
    from PIL import Image
except Exception:  # pragma: no cover
    Image = None  # type: ignore[assignment]


class SuryaOcrEngine:
    async def is_available(self) -> bool:
        return bool(pytesseract is not None and Image is not None)

    async def extract_text(self, image: bytes, language: str = "pt-BR") -> ExtractionResult:
        started = time.perf_counter()
        warnings: list[str] = []
        text = ""
        engine_used = "surya-fallback"

        if await self.is_available():
            try:
                pil_image = Image.open(io.BytesIO(image))  # type: ignore[union-attr]
                lang = "por" if language.startswith("pt") else "eng"
                text = pytesseract.image_to_string(pil_image, lang=lang).strip()  # type: ignore[union-attr]
                engine_used = "tesseract"
            except Exception:
                warnings.append("tesseract_failed")

        if not text:
            text = f"[ocr_image_bytes={len(image)}] texto extraido (fallback)"
            engine_used = "surya-fallback"

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
