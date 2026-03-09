"""HISContext — modelo de contexto de sessão originado por HIS externo."""

from __future__ import annotations

import base64
import json
from enum import Enum
from pydantic import BaseModel, Field


class HISSystem(str, Enum):
    """Sistemas HIS planejados para integração."""

    TASY = "philips_tasy"
    SOUL_MV = "soul_mv"
    TOTVS = "totvs_rm"
    FEEGOW = "feegow"
    PIXEON = "pixeon"
    SISHOSP = "sishosp"
    OPENEMR = "openemr"
    UNKNOWN = "unknown"


class HISContext(BaseModel):
    """Contexto de sessão originado por um HIS externo.

    Propagado como header X-HIS-Context (JSON base64) entre serviços internos.
    Criado pelo intellicare-bridge ao processar o EHR Launch token do HIS.
    """

    his_system: HISSystem = HISSystem.UNKNOWN
    his_patient_id: str = Field(..., description="ID do paciente no HIS de origem")
    fhir_patient_id: str = Field(default="", description="ID FHIR mapeado pelo bridge")
    encounter_id: str = Field(default="", description="ID do encontro/atendimento")
    practitioner_id: str = Field(default="", description="ID do profissional no HIS")
    tenant_id: str = Field(..., description="Tenant IntelliCare")
    launch_token: str = Field(default="", description="Opaque token do EHR Launch")
    iss: str = Field(default="", description="FHIR Base URL do HIS")
    scopes: list[str] = Field(default_factory=list)

    def to_header(self) -> str:
        """Serializa para uso como header X-HIS-Context."""
        return base64.b64encode(self.model_dump_json().encode()).decode()

    @classmethod
    def from_header(cls, header_value: str) -> HISContext:
        """Desserializa do header X-HIS-Context."""
        data = json.loads(base64.b64decode(header_value).decode())
        if isinstance(data.get("his_system"), str):
            data["his_system"] = HISSystem(data["his_system"])
        return cls(**data)
