"""Tool search_documents (implementacao inicial sem DB vetorial)."""

from __future__ import annotations

from typing import Any
from datetime import datetime

from minerva.config import OcrConfig
from minerva.mcp.errors import ToolValidationError
from minerva.storage.chroma_store import get_chroma_store
from minerva.utils.anonymizer import hash_patient_id


async def run(arguments: dict[str, Any], config: OcrConfig) -> dict[str, Any]:
    query = str(arguments.get("query", ""))
    if not query.strip():
        raise ToolValidationError("query obrigatoria")
    patient_id = str(arguments.get("patient_id", ""))
    if not patient_id.strip():
        raise ToolValidationError("patient_id obrigatorio")
    top_k = int(arguments.get("top_k", 5))
    if top_k < 1 or top_k > 20:
        raise ToolValidationError("top_k deve estar entre 1 e 20")
    date_from = arguments.get("date_from")
    date_to = arguments.get("date_to")
    try:
        if date_from:
            _ = datetime.fromisoformat(str(date_from))
        if date_to:
            _ = datetime.fromisoformat(str(date_to))
    except ValueError as exc:
        raise ToolValidationError("date_from/date_to devem estar em formato ISO") from exc
    patient_hash = hash_patient_id(patient_id, config.lgpd_salt or "unsafe-dev-salt")
    return get_chroma_store().search(
        query=query,
        patient_id_hash=patient_hash,
        document_type=str(arguments.get("document_type", "all")),
        top_k=top_k,
        date_from=date_from,
        date_to=date_to,
    )
