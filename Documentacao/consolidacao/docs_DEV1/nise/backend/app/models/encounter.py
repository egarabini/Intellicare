"""
============================================================================
NISE TRAINING MODULE - ENCOUNTER MODEL
============================================================================
Projeto: NISE - Treinamento Assistido
Módulo: Encounter SQLAlchemy Model
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
# ENCOUNTER MODEL
# ============================================================================

class Encounter(Base):
    """
    Encounter model for FHIR R4 resources.
    
    Stores FHIR Encounter resources (patient consultations/visits)
    """
    
    __tablename__ = "encounters"
    __table_args__ = {"schema": "nise_training"}
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # FHIR ID (business key)
    fhir_id = Column(String(255), unique=True, nullable=False, index=True)
    
    # Patient reference (for quick queries)
    patient_id = Column(String(255), index=True)
    
    # FHIR Resource (complete FHIR R4 Encounter resource)
    fhir_resource = Column(JSONB, nullable=False)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<Encounter(fhir_id='{self.fhir_id}', patient_id='{self.patient_id}')>"
    
    @property
    def class_code(self):
        """Get encounter class (AMB, EMER, etc.)."""
        if self.fhir_resource and 'class' in self.fhir_resource:
            return self.fhir_resource['class'].get('code')
        return None
    
    @property
    def status(self):
        """Get encounter status."""
        return self.fhir_resource.get('status') if self.fhir_resource else None
    
    @property
    def period(self):
        """Get encounter period."""
        if self.fhir_resource and 'period' in self.fhir_resource:
            return self.fhir_resource['period']
        return None

