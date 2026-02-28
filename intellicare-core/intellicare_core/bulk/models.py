"""Modelos para FHIR Bulk Data $export (HL7 FHIR Bulk Data Access spec).

Referência: https://hl7.org/fhir/uv/bulkdata/

Estrutura do manifest retornado quando o job é concluído:

    {
      "transactionTime": "2026-02-22T10:00:00Z",
      "request": "https://server/fhir/$export",
      "requiresAccessToken": false,
      "output": [
        {"type": "Patient", "url": "https://server/bulk-data/{job_id}/Patient", "count": 100},
        {"type": "Observation", "url": "...", "count": 500}
      ],
      "error": []
    }
"""

from __future__ import annotations

import uuid
from datetime import datetime, UTC
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class BulkExportStatus(str, Enum):
    ACCEPTED = "accepted"
    IN_PROGRESS = "in-progress"
    COMPLETED = "completed"
    ERROR = "error"
    CANCELLED = "cancelled"


class BulkOutputFile(BaseModel):
    """Uma entrada no array ``output`` do manifest."""

    type: str
    """FHIR resource type (ex: 'Patient', 'Observation')."""

    url: str
    """URL para download do arquivo NDJSON."""

    count: int = 0
    """Número de recursos nesse arquivo."""


class BulkExportManifest(BaseModel):
    """Manifest FHIR Bulk Data — retornado quando status = completed."""

    transactionTime: str
    """ISO 8601 timestamp do início da transação de exportação."""

    request: str
    """URL original da requisição de kick-off."""

    requiresAccessToken: bool = False
    output: list[BulkOutputFile] = Field(default_factory=list)
    error: list[dict[str, Any]] = Field(default_factory=list)
    deleted: list[dict[str, Any]] = Field(default_factory=list)


class BulkExportJob(BaseModel):
    """Estado de um job de exportação bulk (armazenado em memória)."""

    job_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    status: BulkExportStatus = BulkExportStatus.ACCEPTED

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    completed_at: Optional[datetime] = None

    request_url: str = ""
    resource_types: list[str] = Field(default_factory=list)
    tenant_id: str = "default"

    resources_exported: int = 0
    error: Optional[str] = None
