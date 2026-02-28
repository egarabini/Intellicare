"""Engine de visao com Llama4 via Ollama."""

from __future__ import annotations

import asyncio
import base64
import json
import time
from typing import Any
from urllib import request
from urllib.error import URLError

from ocr.config import OcrConfig
from ocr.utils.confidence import score_from_text


VISION_PROMPT = (
    "Voce e um especialista em extracao de documentos medicos brasileiros. "
    "Analise o documento e retorne apenas JSON valido com campos relevantes "
    "para o tipo de documento informado."
)


class Llama4VisionEngine:
    def __init__(self, config: OcrConfig) -> None:
        self._config = config

    async def is_available(self) -> bool:
        try:
            data = await asyncio.to_thread(self._http_json, "/api/tags", None)
        except Exception:
            return False
        model_names = [str(model.get("name", "")) for model in data.get("models", [])]
        desired = self._config.vision_model
        return any(name == desired or name.startswith(f"{desired}:") or desired in name for name in model_names)

    async def extract_structured(self, image: bytes, document_type: str) -> dict[str, Any]:
        started = time.perf_counter()
        payload = {
            "model": self._config.vision_model,
            "prompt": f"{VISION_PROMPT}\nTipo do documento: {document_type}",
            "images": [base64.b64encode(image).decode("utf-8")],
            "stream": False,
            "format": "json",
        }
        try:
            data = await asyncio.wait_for(
                asyncio.to_thread(self._http_json, "/api/generate", payload),
                timeout=max(1, self._config.vision_timeout_seconds),
            )
        except TimeoutError as exc:
            raise RuntimeError("llama4_timeout") from exc
        except URLError as exc:
            raise RuntimeError("llama4_unavailable") from exc

        response_text = str(data.get("response", "")).strip()
        parsed = self._parse_json_response(response_text)
        raw_text = str(parsed.get("raw_text") or parsed.get("text") or json.dumps(parsed, ensure_ascii=False))
        confidence = parsed.get("confidence_score")
        if not isinstance(confidence, (int, float)):
            confidence = score_from_text(raw_text)
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        return {
            "raw_text": raw_text,
            "structured_data": parsed,
            "confidence_score": max(0.0, min(1.0, float(confidence))),
            "processing_time_ms": elapsed_ms,
            "engine_used": "llama4-vision",
            "warnings": [],
        }

    def _http_json(self, path: str, payload: dict[str, Any] | None) -> dict[str, Any]:
        url = f"{self._config.ollama_url.rstrip('/')}{path}"
        body = None
        method = "GET"
        headers = {}
        if payload is not None:
            method = "POST"
            body = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"
        req = request.Request(url=url, data=body, method=method, headers=headers)
        timeout = max(1, self._config.vision_timeout_seconds)
        with request.urlopen(req, timeout=timeout) as response:
            content = response.read().decode("utf-8")
        return json.loads(content or "{}")

    def _parse_json_response(self, response_text: str) -> dict[str, Any]:
        text = response_text.strip()
        if not text:
            raise RuntimeError("llama4_empty_response")
        if text.startswith("```"):
            first = text.find("{")
            last = text.rfind("}")
            if first >= 0 and last > first:
                text = text[first : last + 1]
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            first = text.find("{")
            last = text.rfind("}")
            if first >= 0 and last > first:
                parsed = json.loads(text[first : last + 1])
            else:
                raise RuntimeError("llama4_invalid_json_response")
        if not isinstance(parsed, dict):
            raise RuntimeError("llama4_invalid_json_response")
        return parsed
