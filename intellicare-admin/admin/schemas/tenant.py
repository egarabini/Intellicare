from pydantic import BaseModel, Field, field_validator, ConfigDict
from datetime import datetime
from uuid import UUID
from typing import Optional, List
import re

from admin.utils.cnpj import validate_cnpj_digits

class EstabelecimentoCreate(BaseModel):
    nome: str = Field(..., min_length=3, max_length=255)
    cnes: Optional[str] = Field(None, min_length=7, max_length=15)
    cnpj: str = Field(..., pattern=r"^\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}$")
    tipo: str = Field(..., min_length=3, max_length=50)  # HOSPITAL, CLINICA, LABORATORIO, SECRETARIA
    gestor: Optional[dict] = None  # {"nome": "...", "email": "...", "telefone": "..."}
    plano_id: str = Field(..., min_length=3, max_length=50)
    modulos: List[str] = Field(default_factory=list)

    @field_validator("cnpj")
    @classmethod
    def validate_cnpj(cls, v: str) -> str:
        # Remove formatação e valida dígitos
        numbers = re.sub(r"[^\d]", "", v)
        if not validate_cnpj_digits(numbers):
            raise ValueError("CNPJ inválido")
        return numbers

class EstabelecimentoResponse(BaseModel):
    id: UUID
    nome: str
    cnes: Optional[str]
    cnpj: Optional[str]
    tipo: str
    logo_url: Optional[str]
    status: str
    plano_id: Optional[str]
    gestor_nome: Optional[str]
    gestor_email: Optional[str]
    gestor_telefone: Optional[str]
    criado_em: datetime
    provisionado_em: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)

class EstabelecimentoUpdate(BaseModel):
    nome: Optional[str] = Field(None, min_length=3, max_length=255)
    logo_url: Optional[str] = None
    gestor_email: Optional[str] = None
    gestor_telefone: Optional[str] = None
    configuracoes: Optional[dict] = None

class EstabelecimentoListResponse(BaseModel):
    items: List[EstabelecimentoResponse]
    total: int
    page: int
    per_page: int

# Gestor schemas
class GestorCreate(BaseModel):
    nome: str = Field(..., min_length=3, max_length=255)
    email: str = Field(...)
    permissoes: Optional[dict] = None

class GestorResponse(BaseModel):
    id: UUID
    estabelecimento_id: UUID
    nome: str
    email: str
    permissoes: dict
    ativo: bool
    criado_em: datetime

    model_config = ConfigDict(from_attributes=True)
