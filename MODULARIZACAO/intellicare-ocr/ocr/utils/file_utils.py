"""Funcoes utilitarias para arquivos/base64."""

from __future__ import annotations

import base64

from ocr.mcp.errors import ToolValidationError


SUPPORTED_FILE_TYPES = {"pdf", "jpeg", "jpg", "png", "tiff", "txt"}


def decode_base64_payload(payload: str) -> bytes:
    raw = payload.strip()
    if not raw:
        raise ToolValidationError("payload base64 vazio")
    if raw.startswith("data:") and "," in raw:
        raw = raw.split(",", 1)[1]
    try:
        decoded = base64.b64decode(raw.encode("utf-8"), validate=True)
    except Exception as exc:
        raise ToolValidationError("payload base64 invalido") from exc
    if not decoded:
        raise ToolValidationError("arquivo decodificado vazio")
    return decoded


def normalize_file_type(file_type: str) -> str:
    normalized = file_type.strip().lower()
    if normalized == "jpg":
        normalized = "jpeg"
    if normalized not in SUPPORTED_FILE_TYPES:
        raise ValueError(f"file_type nao suportado: {file_type}")
    return normalized
