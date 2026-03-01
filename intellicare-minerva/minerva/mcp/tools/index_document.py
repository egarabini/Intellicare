"""Tool index_document (implementacao inicial sem ChromaDB)."""

from __future__ import annotations

from typing import Any

from minerva.config import OcrConfig
from minerva.mcp.errors import ToolValidationError
from minerva.storage.chroma_store import get_chroma_store
from minerva.utils.anonymizer import hash_patient_id


async def run(arguments: dict[str, Any], config: OcrConfig) -> dict[str, Any]:
    text = str(arguments.get("document_text", ""))
    if not text.strip():
        raise ToolValidationError("document_text obrigatorio")
    patient_id = str(arguments.get("patient_id", "anonymous"))
    patient_hash = hash_patient_id(patient_id, config.lgpd_salt or "unsafe-dev-salt")
    document_type = str(arguments.get("document_type", "generic"))
    if not document_type.strip():
        raise ToolValidationError("document_type obrigatorio")
    metadata = arguments.get("metadata") or {}
    if not isinstance(metadata, dict):
        raise ToolValidationError("metadata deve ser objeto")
    return get_chroma_store().index_document(
        text=text,
        patient_id_hash=patient_hash,
        document_type=document_type,
        metadata=metadata,
    )
