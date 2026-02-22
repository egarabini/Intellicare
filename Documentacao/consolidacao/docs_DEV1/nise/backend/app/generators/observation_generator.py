"""
============================================================================
NISE TRAINING MODULE - OBSERVATION GENERATOR
============================================================================
Projeto: NISE - Treinamento Assistido
Módulo: Synthetic Observation Data Generator (FHIR R4)
Versão: 1.0
Data: 06/03/2026
Responsável: DEV2
============================================================================
"""

from faker import Faker
import random
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import json

fake = Faker('pt_BR')

# ============================================================================
# LOINC CODES (Brazilian Lab Tests)
# ============================================================================

LOINC_CODES = [
    # Hemograma
    {"code": "718-7", "display": "Hemoglobina", "unit": "g/dL", "range": (12.0, 16.0)},
    {"code": "789-8", "display": "Eritrócitos", "unit": "milhões/mm³", "range": (4.0, 5.5)},
    {"code": "6690-2", "display": "Leucócitos", "unit": "mil/mm³", "range": (4.0, 11.0)},
    {"code": "777-3", "display": "Plaquetas", "unit": "mil/mm³", "range": (150.0, 400.0)},
    
    # Glicemia
    {"code": "2339-0", "display": "Glicose", "unit": "mg/dL", "range": (70.0, 100.0)},
    {"code": "4548-4", "display": "Hemoglobina Glicada (HbA1c)", "unit": "%", "range": (4.0, 5.6)},
    
    # Função Renal
    {"code": "2160-0", "display": "Creatinina", "unit": "mg/dL", "range": (0.6, 1.2)},
    {"code": "3094-0", "display": "Ureia", "unit": "mg/dL", "range": (15.0, 45.0)},
    {"code": "33914-3", "display": "TFG (Taxa de Filtração Glomerular)", "unit": "mL/min/1.73m²", "range": (90.0, 120.0)},
    
    # Função Hepática
    {"code": "1742-6", "display": "ALT (TGP)", "unit": "U/L", "range": (7.0, 56.0)},
    {"code": "1920-8", "display": "AST (TGO)", "unit": "U/L", "range": (5.0, 40.0)},
    {"code": "1975-2", "display": "Bilirrubina Total", "unit": "mg/dL", "range": (0.3, 1.2)},
    
    # Lipidograma
    {"code": "2093-3", "display": "Colesterol Total", "unit": "mg/dL", "range": (150.0, 200.0)},
    {"code": "2085-9", "display": "HDL Colesterol", "unit": "mg/dL", "range": (40.0, 60.0)},
    {"code": "2089-1", "display": "LDL Colesterol", "unit": "mg/dL", "range": (100.0, 130.0)},
    {"code": "2571-8", "display": "Triglicerídeos", "unit": "mg/dL", "range": (50.0, 150.0)},
    
    # Eletrólitos
    {"code": "2951-2", "display": "Sódio", "unit": "mEq/L", "range": (135.0, 145.0)},
    {"code": "2823-3", "display": "Potássio", "unit": "mEq/L", "range": (3.5, 5.0)},
    {"code": "2075-0", "display": "Cloreto", "unit": "mEq/L", "range": (98.0, 107.0)},
    
    # Sinais Vitais
    {"code": "8480-6", "display": "Pressão Arterial Sistólica", "unit": "mmHg", "range": (110.0, 130.0)},
    {"code": "8462-4", "display": "Pressão Arterial Diastólica", "unit": "mmHg", "range": (70.0, 85.0)},
    {"code": "8867-4", "display": "Frequência Cardíaca", "unit": "bpm", "range": (60.0, 100.0)},
    {"code": "8310-5", "display": "Temperatura Corporal", "unit": "°C", "range": (36.0, 37.5)},
    {"code": "29463-7", "display": "Peso Corporal", "unit": "kg", "range": (50.0, 100.0)},
    {"code": "8302-2", "display": "Altura", "unit": "cm", "range": (150.0, 190.0)},
]

# ============================================================================
# OBSERVATION GENERATOR
# ============================================================================

class ObservationGenerator:
    """Gerador de observações sintéticas FHIR R4"""
    
    def __init__(self):
        self.fake = fake
    
    def generate_fhir_id(self) -> str:
        """Gerar ID FHIR único"""
        return f"observation-{self.fake.uuid4()}"
    
    def generate_value(self, loinc_code: Dict, is_abnormal: bool = False) -> float:
        """
        Gerar valor para observação.
        
        Args:
            loinc_code: Dicionário com código LOINC
            is_abnormal: Se True, gera valor fora do range normal
        
        Returns:
            float: Valor gerado
        """
        min_val, max_val = loinc_code["range"]
        
        if is_abnormal:
            # 50% chance de estar acima ou abaixo do normal
            if random.random() < 0.5:
                # Abaixo do normal (70-90% do mínimo)
                value = min_val * random.uniform(0.7, 0.9)
            else:
                # Acima do normal (110-150% do máximo)
                value = max_val * random.uniform(1.1, 1.5)
        else:
            # Valor normal (dentro do range)
            value = random.uniform(min_val, max_val)
        
        return round(value, 2)
    
    def generate_effective_datetime(self, days_ago: int = 365) -> str:
        """Gerar data/hora da observação"""
        now = datetime.now()
        random_days = random.randint(0, days_ago)
        random_hours = random.randint(0, 23)
        random_minutes = random.randint(0, 59)
        
        effective_dt = now - timedelta(days=random_days, hours=random_hours, minutes=random_minutes)
        return effective_dt.strftime("%Y-%m-%dT%H:%M:%S")
    
    def generate_observation(self, patient_fhir_id: str) -> Dict:
        """
        Gerar observação sintética completa (FHIR R4).
        
        Args:
            patient_fhir_id: ID FHIR do paciente
        
        Returns:
            dict: Recurso FHIR Observation completo
        """
        # Selecionar código LOINC aleatório
        loinc_code = random.choice(LOINC_CODES)
        
        # 20% de chance de valor anormal
        is_abnormal = random.random() < 0.2
        
        # Gerar valor
        value = self.generate_value(loinc_code, is_abnormal)
        
        # Gerar data/hora
        effective_datetime = self.generate_effective_datetime()
        
        # ID FHIR
        fhir_id = self.generate_fhir_id()
        
        # Recurso FHIR R4 Observation
        fhir_observation = {
            "resourceType": "Observation",
            "id": fhir_id,
            "status": "final",
            "category": [{
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                    "code": "laboratory",
                    "display": "Laboratory"
                }]
            }],
            "code": {
                "coding": [{
                    "system": "http://loinc.org",
                    "code": loinc_code["code"],
                    "display": loinc_code["display"]
                }],
                "text": loinc_code["display"]
            },
            "subject": {
                "reference": f"Patient/{patient_fhir_id}"
            },
            "effectiveDateTime": effective_datetime,
            "valueQuantity": {
                "value": value,
                "unit": loinc_code["unit"],
                "system": "http://unitsofmeasure.org",
                "code": loinc_code["unit"]
            },
            "interpretation": [{
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation",
                    "code": "A" if is_abnormal else "N",
                    "display": "Abnormal" if is_abnormal else "Normal"
                }]
            }]
        }
        
        return {
            "fhir_id": fhir_id,
            "patient_fhir_id": patient_fhir_id,
            "code_loinc": loinc_code["code"],
            "code_display": loinc_code["display"],
            "value_quantity": value,
            "value_unit": loinc_code["unit"],
            "effective_datetime": effective_datetime,
            "data": fhir_observation
        }
    
    def generate_batch_for_patients(
        self, 
        patient_fhir_ids: List[str], 
        observations_per_patient: int = 4
    ) -> List[Dict]:
        """
        Gerar lote de observações para múltiplos pacientes.
        
        Args:
            patient_fhir_ids: Lista de IDs FHIR dos pacientes
            observations_per_patient: Número médio de observações por paciente
        
        Returns:
            list: Lista de observações
        """
        observations = []
        
        for patient_id in patient_fhir_ids:
            # Variar número de observações (±2)
            num_obs = observations_per_patient + random.randint(-2, 2)
            num_obs = max(1, num_obs)  # Mínimo 1 observação
            
            for _ in range(num_obs):
                observation = self.generate_observation(patient_id)
                observations.append(observation)
        
        return observations

