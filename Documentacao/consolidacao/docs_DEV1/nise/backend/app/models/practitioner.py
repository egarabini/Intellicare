"""
============================================================================
NISE TRAINING MODULE - PRACTITIONER MODEL
============================================================================
Projeto: NISE - Treinamento Assistido
Módulo: Practitioner SQLAlchemy Model
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
# PRACTITIONER MODEL
# ============================================================================

class Practitioner(Base):
    """
    Practitioner model for FHIR R4 resources.
    
    Stores FHIR Practitioner resources (healthcare professionals)
    """
    
    __tablename__ = "practitioners"
    __table_args__ = {"schema": "nise_training"}
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # FHIR ID (business key)
    fhir_id = Column(String(255), unique=True, nullable=False, index=True)
    
    # FHIR Resource (complete FHIR R4 Practitioner resource)
    fhir_resource = Column(JSONB, nullable=False)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<Practitioner(fhir_id='{self.fhir_id}')>"
    
    @property
    def name(self):
        """Get practitioner name from FHIR resource."""
        if self.fhir_resource and 'name' in self.fhir_resource:
            names = self.fhir_resource['name']
            if names:
                name = names[0]
                family = name.get('family', '')
                given = ' '.join(name.get('given', []))
                prefix = ' '.join(name.get('prefix', []))
                full_name = f"{prefix} {given} {family}".strip()
                return full_name
        return None
    
    @property
    def crm(self):
        """Get CRM from FHIR resource."""
        if self.fhir_resource and 'identifier' in self.fhir_resource:
            for identifier in self.fhir_resource['identifier']:
                if 'CRM' in identifier.get('system', ''):
                    return identifier.get('value')
        return None
    
    @property
    def specialty(self):
        """Get specialty from FHIR resource."""
        if self.fhir_resource and 'qualification' in self.fhir_resource:
            qualifications = self.fhir_resource['qualification']
            if qualifications:
                code = qualifications[0].get('code', {})
                coding = code.get('coding', [])
                if coding:
                    return coding[0].get('display')
        return None

