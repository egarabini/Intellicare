from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class TerminologySystem(str, Enum):
    CID10 = "cid10"
    LOINC = "loinc"
    SNOMED = "snomed"
    TUSS = "tuss"
    CUSTOM = "custom"


class Terminology(BaseModel):
    code: str = Field(..., description="Código da terminologia")
    system: TerminologySystem = Field(..., description="Sistema de terminologia")
    display: str = Field(..., description="Nome/descrição")
    definition: Optional[str] = Field(None, description="Definição detalhada")
    synonyms: List[str] = Field(default_factory=list, description="Sinônimos")
    parent_code: Optional[str] = Field(None, description="Código pai (hierarquia)")
    children_codes: List[str] = Field(default_factory=list, description="Códigos filhos")
    metadata: Dict[str, str] = Field(default_factory=dict)
    
    class Config:
        json_schema_extra = {
            "example": {
                "code": "N18.3",
                "system": "cid10",
                "display": "Doença renal crônica, estágio 3",
                "definition": "DRC com TFG entre 30-59 mL/min/1.73m²",
                "synonyms": ["DRC G3", "Insuficiência renal moderada"],
                "parent_code": "N18"
            }
        }


class TerminologyMapping(BaseModel):
    source_code: str
    source_system: TerminologySystem
    target_code: str
    target_system: TerminologySystem
    equivalence: str = Field(..., description="Tipo de equivalência: exact, equivalent, wider, narrower")
    comments: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "source_code": "2160-0",
                "source_system": "loinc",
                "target_code": "Creatinina sérica",
                "target_system": "custom",
                "equivalence": "exact"
            }
        }


class TerminologySearchRequest(BaseModel):
    query: str = Field(..., description="Texto de busca")
    system: Optional[TerminologySystem] = None
    limit: int = Field(default=20, ge=1, le=100)


class TerminologySearchResult(BaseModel):
    terminology: Terminology
    score: float = Field(..., description="Relevância da busca (0-1)")
