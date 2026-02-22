"""
============================================================================
NISE TRAINING MODULE - ENCOUNTER GENERATOR
============================================================================
Projeto: NISE - Treinamento Assistido
Módulo: Synthetic Encounter Data Generator (FHIR R4)
Versão: 1.0
Data: 10/03/2026
Responsável: DEV2
============================================================================
"""

from faker import Faker
import random
from datetime import datetime, timedelta
from typing import Dict, List

fake = Faker('pt_BR')

# ============================================================================
# ENCOUNTER TYPES
# ============================================================================

ENCOUNTER_TYPES = [
    {"code": "AMB", "display": "Ambulatorial", "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode"},
    {"code": "EMER", "display": "Emergência", "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode"},
    {"code": "HH", "display": "Home Health", "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode"},
    {"code": "IMP", "display": "Internação", "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode"},
    {"code": "ACUTE", "display": "Agudo", "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode"},
]

# ============================================================================
# ENCOUNTER GENERATOR
# ============================================================================

class EncounterGenerator:
    """Gerador de consultas/atendimentos sintéticos FHIR R4"""
    
    def __init__(self):
        self.fake = fake
    
    def generate_fhir_id(self) -> str:
        """Gerar ID FHIR único"""
        return f"encounter-{self.fake.uuid4()}"
    
    def generate_datetime(self, days_ago: int = 365) -> tuple:
        """
        Gerar data/hora de início e fim do atendimento.
        
        Returns:
            tuple: (start_datetime, end_datetime)
        """
        now = datetime.now()
        random_days = random.randint(0, days_ago)
        random_hours = random.randint(8, 18)  # Horário comercial
        
        start_dt = now - timedelta(days=random_days, hours=random_hours)
        
        # Duração do atendimento (15 min a 2 horas)
        duration_minutes = random.randint(15, 120)
        end_dt = start_dt + timedelta(minutes=duration_minutes)
        
        return (
            start_dt.strftime("%Y-%m-%dT%H:%M:%S"),
            end_dt.strftime("%Y-%m-%dT%H:%M:%S")
        )
    
    def generate_encounter(
        self, 
        patient_fhir_id: str, 
        practitioner_fhir_id: str
    ) -> Dict:
        """
        Gerar consulta/atendimento sintético completo (FHIR R4).
        
        Args:
            patient_fhir_id: ID FHIR do paciente
            practitioner_fhir_id: ID FHIR do profissional
        
        Returns:
            dict: Recurso FHIR Encounter completo
        """
        # ID FHIR
        fhir_id = self.generate_fhir_id()
        
        # Tipo de atendimento
        encounter_type = random.choice(ENCOUNTER_TYPES)
        
        # Data/hora
        start_datetime, end_datetime = self.generate_datetime()
        
        # Status
        status = "finished"  # Todos os atendimentos já finalizados
        
        # Recurso FHIR R4 Encounter
        fhir_encounter = {
            "resourceType": "Encounter",
            "id": fhir_id,
            "status": status,
            "class": {
                "system": encounter_type["system"],
                "code": encounter_type["code"],
                "display": encounter_type["display"]
            },
            "type": [{
                "coding": [{
                    "system": encounter_type["system"],
                    "code": encounter_type["code"],
                    "display": encounter_type["display"]
                }],
                "text": encounter_type["display"]
            }],
            "subject": {
                "reference": f"Patient/{patient_fhir_id}"
            },
            "participant": [{
                "individual": {
                    "reference": f"Practitioner/{practitioner_fhir_id}"
                }
            }],
            "period": {
                "start": start_datetime,
                "end": end_datetime
            }
        }
        
        return {
            "fhir_id": fhir_id,
            "patient_fhir_id": patient_fhir_id,
            "practitioner_fhir_id": practitioner_fhir_id,
            "encounter_type": encounter_type["code"],
            "start_datetime": start_datetime,
            "end_datetime": end_datetime,
            "data": fhir_encounter
        }
    
    def generate_batch_for_patients(
        self,
        patient_fhir_ids: List[str],
        practitioner_fhir_ids: List[str],
        encounters_per_patient: int = 1
    ) -> List[Dict]:
        """
        Gerar lote de consultas para múltiplos pacientes.
        
        Args:
            patient_fhir_ids: Lista de IDs FHIR dos pacientes
            practitioner_fhir_ids: Lista de IDs FHIR dos profissionais
            encounters_per_patient: Número médio de consultas por paciente
        
        Returns:
            list: Lista de consultas
        """
        encounters = []
        
        for patient_id in patient_fhir_ids:
            # Variar número de consultas
            num_encounters = random.randint(
                max(1, encounters_per_patient - 1),
                encounters_per_patient + 1
            )
            
            for _ in range(num_encounters):
                # Selecionar profissional aleatório
                practitioner_id = random.choice(practitioner_fhir_ids)
                
                encounter = self.generate_encounter(patient_id, practitioner_id)
                encounters.append(encounter)
        
        return encounters

