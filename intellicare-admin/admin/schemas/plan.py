from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, List
from decimal import Decimal

class PlanCreate(BaseModel):
    id: str = Field(..., min_length=3, max_length=50)
    nome: str = Field(..., min_length=3, max_length=255)
    descricao: Optional[str] = None
    preco_mensal: Decimal
    moeda: str = "BRL"
    max_gestores: Optional[int] = None
    max_usuarios_saude: Optional[int] = None
    max_storage_gb: Optional[int] = None
    max_chamadas_api_mensal: Optional[int] = None
    modulos: List[str] = Field(default_factory=list)
    status: str = "active"

class PlanResponse(PlanCreate):
    criado_em: datetime

    model_config = ConfigDict(from_attributes=True)

class PlanUpdate(BaseModel):
    nome: Optional[str] = Field(None, min_length=3, max_length=255)
    descricao: Optional[str] = None
    preco_mensal: Optional[Decimal] = None
    max_gestores: Optional[int] = None
    max_usuarios_saude: Optional[int] = None
    max_storage_gb: Optional[int] = None
    max_chamadas_api_mensal: Optional[int] = None
    modulos: Optional[List[str]] = None
    status: Optional[str] = None
