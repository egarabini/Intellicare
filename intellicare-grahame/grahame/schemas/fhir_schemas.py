"""Schemas FHIR R4 para entrada/saída da API."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class FHIRResourceIn(BaseModel):
    """Recurso FHIR para criação/atualização.

    O campo `resource` deve conter um recurso FHIR R4 válido (dict)
    com pelo menos `resourceType` e `id`.
    """

    resource: dict[str, Any] = Field(..., description="Recurso FHIR R4 completo (JSON)")


class FHIRResourceOut(BaseModel):
    """Recurso FHIR recuperado do banco."""

    id: str
    resource_type: str
    fhir_id: str
    resource: dict[str, Any]
    active: bool
    tenant_id: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class FHIRBundleEntry(BaseModel):
    """Entry de um Bundle FHIR."""

    fullUrl: str | None = None
    resource: dict[str, Any]


class FHIRBundle(BaseModel):
    """Bundle FHIR R4 para responses de busca (searchset)."""

    resourceType: str = "Bundle"
    type: str = "searchset"
    total: int
    entry: list[FHIRBundleEntry] = []
