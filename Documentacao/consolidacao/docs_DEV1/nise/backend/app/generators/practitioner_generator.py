"""
============================================================================
NISE TRAINING MODULE - PRACTITIONER GENERATOR
============================================================================
Projeto: NISE - Treinamento Assistido
Módulo: Synthetic Practitioner Data Generator (FHIR R4)
Versão: 1.0
Data: 10/03/2026
Responsável: DEV2
============================================================================
"""

from faker import Faker
import random
from typing import Dict, List

fake_br = Faker('pt_BR')
fake_en = Faker('en_US')

# ============================================================================
# MEDICAL SPECIALTIES (Brazilian)
# ============================================================================

MEDICAL_SPECIALTIES = [
    {"code": "394814009", "display": "Cardiologia", "system": "SNOMED-CT"},
    {"code": "394583002", "display": "Nefrologia", "system": "SNOMED-CT"},
    {"code": "394582007", "display": "Endocrinologia", "system": "SNOMED-CT"},
    {"code": "394579002", "display": "Geriatria", "system": "SNOMED-CT"},
    {"code": "394802001", "display": "Medicina de Família e Comunidade", "system": "SNOMED-CT"},
    {"code": "394585009", "display": "Obstetrícia e Ginecologia", "system": "SNOMED-CT"},
    {"code": "394537008", "display": "Pediatria", "system": "SNOMED-CT"},
    {"code": "394611003", "display": "Cirurgia Geral", "system": "SNOMED-CT"},
    {"code": "394587001", "display": "Psiquiatria", "system": "SNOMED-CT"},
    {"code": "394821009", "display": "Medicina Interna", "system": "SNOMED-CT"},
]

# ============================================================================
# PRACTITIONER GENERATOR
# ============================================================================

class PractitionerGenerator:
    """Gerador de profissionais de saúde sintéticos FHIR R4"""
    
    def __init__(self):
        self.fake_br = fake_br
        self.fake_en = fake_en
        self.generated_cpfs = set()
        self.generated_crms = set()
    
    def generate_fhir_id(self) -> str:
        """Gerar ID FHIR único"""
        return f"practitioner-{self.fake_en.uuid4()}"
    
    def generate_unique_cpf(self) -> str:
        """Gerar CPF único (simplificado)"""
        while True:
            cpf = ''.join([str(random.randint(0, 9)) for _ in range(11)])
            if cpf not in self.generated_cpfs:
                self.generated_cpfs.add(cpf)
                return cpf
    
    def generate_unique_crm(self, state: str = "SP") -> str:
        """Gerar CRM único"""
        while True:
            number = random.randint(10000, 999999)
            crm = f"{number}/{state}"
            if crm not in self.generated_crms:
                self.generated_crms.add(crm)
                return crm
    
    def generate_practitioner(self) -> Dict:
        """
        Gerar profissional de saúde sintético completo (FHIR R4).
        
        Returns:
            dict: Recurso FHIR Practitioner completo
        """
        # Dados básicos
        fhir_id = self.generate_fhir_id()
        cpf = self.generate_unique_cpf()
        gender = random.choice(['male', 'female'])
        
        # Nome
        if gender == 'male':
            given_name = self.fake_br.first_name_male()
            prefix = "Dr."
        else:
            given_name = self.fake_br.first_name_female()
            prefix = "Dra."
        
        family_name = self.fake_br.last_name()
        
        # Especialidade
        specialty = random.choice(MEDICAL_SPECIALTIES)
        
        # CRM
        state = random.choice(["SP", "RJ", "MG", "PR", "RS", "BA", "CE", "DF"])
        crm = self.generate_unique_crm(state)
        
        # CNS (simplificado)
        cns = ''.join([str(random.randint(0, 9)) for _ in range(15)])
        
        # Recurso FHIR R4 Practitioner
        fhir_practitioner = {
            "resourceType": "Practitioner",
            "id": fhir_id,
            "identifier": [
                {
                    "use": "official",
                    "type": {
                        "coding": [{
                            "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                            "code": "TAX",
                            "display": "Tax ID number"
                        }],
                        "text": "CPF"
                    },
                    "system": "http://rnds.saude.gov.br/fhir/r4/NamingSystem/cpf",
                    "value": cpf
                },
                {
                    "use": "official",
                    "type": {
                        "coding": [{
                            "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                            "code": "MD",
                            "display": "Medical License number"
                        }],
                        "text": "CRM"
                    },
                    "system": "http://www.cremesp.org.br",
                    "value": crm
                },
                {
                    "use": "official",
                    "type": {
                        "coding": [{
                            "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                            "code": "HC",
                            "display": "Health Card Number"
                        }],
                        "text": "CNS"
                    },
                    "system": "http://rnds.saude.gov.br/fhir/r4/NamingSystem/cns",
                    "value": cns
                }
            ],
            "name": [{
                "use": "official",
                "prefix": [prefix],
                "family": family_name,
                "given": [given_name]
            }],
            "gender": gender,
            "qualification": [{
                "code": {
                    "coding": [{
                        "system": f"http://snomed.info/sct",
                        "code": specialty["code"],
                        "display": specialty["display"]
                    }],
                    "text": specialty["display"]
                }
            }]
        }
        
        return {
            "fhir_id": fhir_id,
            "cpf": cpf,
            "cns": cns,
            "name_given": given_name,
            "name_family": family_name,
            "specialty": specialty["display"],
            "crm": crm,
            "data": fhir_practitioner
        }
    
    def generate_batch(self, count: int = 1000) -> List[Dict]:
        """
        Gerar lote de profissionais.
        
        Args:
            count: Número de profissionais a gerar
        
        Returns:
            list: Lista de profissionais
        """
        practitioners = []
        for i in range(count):
            practitioner = self.generate_practitioner()
            practitioners.append(practitioner)
            
            if (i + 1) % 100 == 0:
                print(f"✅ Generated {i + 1}/{count} practitioners...")
        
        return practitioners

