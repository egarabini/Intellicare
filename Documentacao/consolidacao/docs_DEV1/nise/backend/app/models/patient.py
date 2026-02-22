"""
============================================================================
NISE TRAINING MODULE - PATIENT MODEL
============================================================================
Projeto: NISE - Treinamento Assistido
Módulo: Patient SQLAlchemy Model
Versão: 1.0
Data: 17/03/2026
Responsável: DEV2
============================================================================
"""

from sqlalchemy import Column, String, DateTime, Integer
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from app.database import Base

# ============================================================================
# PATIENT MODEL
# ============================================================================

class Patient(Base):
    """
    Patient model for FHIR R4 resources.
    
    Stores FHIR Patient resources in JSONB format for flexibility
    while maintaining indexable fields for performance.
    """
    
    __tablename__ = "patients"
    __table_args__ = {"schema": "nise_training"}
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # FHIR ID (business key)
    fhir_id = Column(String(255), unique=True, nullable=False, index=True)
    
    # FHIR Resource (complete FHIR R4 Patient resource)
    fhir_resource = Column(JSONB, nullable=False)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<Patient(fhir_id='{self.fhir_id}')>"
    
    @property
    def name(self):
        """Get patient name from FHIR resource."""
        if self.fhir_resource and 'name' in self.fhir_resource:
            names = self.fhir_resource['name']
            if names:
                name = names[0]
                family = name.get('family', '')
                given = ' '.join(name.get('given', []))
                return f"{given} {family}".strip()
        return None
    
    @property
    def cpf(self):
        """Get CPF from FHIR resource."""
        if self.fhir_resource and 'identifier' in self.fhir_resource:
            for identifier in self.fhir_resource['identifier']:
                if identifier.get('system') == 'http://rnds.saude.gov.br/fhir/r4/NamingSystem/cpf':
                    return identifier.get('value')
        return None
    
    @property
    def cns(self):
        """Get CNS from FHIR resource."""
        if self.fhir_resource and 'identifier' in self.fhir_resource:
            for identifier in self.fhir_resource['identifier']:
                if identifier.get('system') == 'http://rnds.saude.gov.br/fhir/r4/NamingSystem/cns':
                    return identifier.get('value')
        return None
    
    @property
    def gender(self):
        """Get gender from FHIR resource."""
        return self.fhir_resource.get('gender') if self.fhir_resource else None
    
    @property
    def birthdate(self):
        """Get birthdate from FHIR resource."""
        return self.fhir_resource.get('birthDate') if self.fhir_resource else None

