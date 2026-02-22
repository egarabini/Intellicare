"""
============================================================================
NISE TRAINING MODULE - OBSERVATION MODEL
============================================================================
Projeto: NISE - Treinamento Assistido
Módulo: Observation SQLAlchemy Model
Versão: 1.0
Data: 17/03/2026
Responsável: DEV2
============================================================================
"""

from sqlalchemy import Column, String, DateTime, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from app.database import Base

# ============================================================================
# OBSERVATION MODEL
# ============================================================================

class Observation(Base):
    """
    Observation model for FHIR R4 resources.
    
    Stores FHIR Observation resources (lab results, vital signs, etc.)
    """
    
    __tablename__ = "observations"
    __table_args__ = {"schema": "nise_training"}
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # FHIR ID (business key)
    fhir_id = Column(String(255), unique=True, nullable=False, index=True)
    
    # Patient reference (for quick queries)
    patient_id = Column(String(255), index=True)
    
    # FHIR Resource (complete FHIR R4 Observation resource)
    fhir_resource = Column(JSONB, nullable=False)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<Observation(fhir_id='{self.fhir_id}', patient_id='{self.patient_id}')>"
    
    @property
    def code(self):
        """Get observation code (LOINC)."""
        if self.fhir_resource and 'code' in self.fhir_resource:
            coding = self.fhir_resource['code'].get('coding', [])
            if coding:
                return coding[0].get('code')
        return None
    
    @property
    def value(self):
        """Get observation value."""
        if self.fhir_resource:
            if 'valueQuantity' in self.fhir_resource:
                return self.fhir_resource['valueQuantity'].get('value')
            elif 'valueString' in self.fhir_resource:
                return self.fhir_resource['valueString']
        return None
    
    @property
    def status(self):
        """Get observation status."""
        return self.fhir_resource.get('status') if self.fhir_resource else None

