from datetime import date, datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field

# Base properties
class PatientBase(BaseModel):
    nome: str = Field(..., description="Nome completo do paciente")
    cpf: Optional[str] = Field(None, description="CPF do paciente")
    cns: Optional[str] = Field(None, description="Cartão Nacional de Saúde")
    data_nascimento: Optional[date] = Field(None, description="Data de nascimento")
    telefone: Optional[str] = Field(None, description="Telefone de contato principal")
    sexo: Optional[str] = Field(None, description="Sexo (masculino, feminino, outro, ignorado)")
    active: bool = Field(True, description="Status de atividade do paciente no portal SaaS")
    default_sector_id: Optional[UUID] = Field(None, description="Unidade ou polo atrelado a este paciente")

# Properties to receive on Patient creation
class PatientCreate(PatientBase):
    pass

# Properties to receive on Patient update
class PatientUpdate(PatientBase):
    nome: Optional[str] = None
    pass

# Properties returning from API
class PatientResponse(PatientBase):
    id: UUID
    fhir_patient_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Properties to associate an existing Patient with a FHIR Patient ID
class PatientFhirLink(BaseModel):
    fhir_patient_id: str = Field(..., description="ID oficial gerado no Servidor FHIR Grahame")
