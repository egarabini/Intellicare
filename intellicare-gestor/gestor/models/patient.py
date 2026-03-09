import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, Date, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from gestor.models.base import Base

class Patient(Base):
    """
    Modelo operacional Híbrido de Paciente no Gestor (PostgreSQL).
    Guarda dados essenciais para dashboards, filas e workflows iterativos.
    O prontuário clínico detalhado reside no FHIR Server (intellicare-grahame).
    """
    __tablename__ = "patients"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    fhir_patient_id = Column(String(255), nullable=True, index=True) # Preenchido via Kestra Async Workflow
    
    nome = Column(String(255), nullable=False)
    cpf = Column(String(14), unique=True, nullable=True) # 000.000.000-00
    cns = Column(String(15), unique=True, nullable=True) # Cartão Nacional de Saúde
    data_nascimento = Column(Date, nullable=True)
    telefone = Column(String(50), nullable=True)
    sexo = Column(String(20), nullable=True) # masculino, feminino, outro, ignorado
    
    active = Column(Boolean, default=True)
    
    # Vinculos Operacionais do SaaS
    default_sector_id = Column(UUID(as_uuid=True), ForeignKey("sectors.id"), nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

