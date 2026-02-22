"""
============================================================================
NISE TRAINING MODULE - PATIENT GENERATOR
============================================================================
Projeto: NISE - Treinamento Assistido
Módulo: Synthetic Patient Data Generator (FHIR R4)
Versão: 1.0
Data: 05/03/2026
Responsável: DEV2
============================================================================
"""

from faker import Faker
from faker.providers import BaseProvider
import random
from datetime import datetime, timedelta
from typing import Dict, List
import json

# Faker brasileiro
fake_br = Faker('pt_BR')
fake_en = Faker('en_US')

# ============================================================================
# BRAZILIAN DOCUMENT PROVIDERS
# ============================================================================

class BrazilianDocumentProvider(BaseProvider):
    """Provider para documentos brasileiros válidos"""
    
    def cpf(self) -> str:
        """Gerar CPF válido (algoritmo módulo 11)"""
        def calculate_digit(digits: List[int], weights: List[int]) -> int:
            total = sum(d * w for d, w in zip(digits, weights))
            remainder = total % 11
            return 0 if remainder < 2 else 11 - remainder
        
        # Gerar 9 primeiros dígitos
        digits = [random.randint(0, 9) for _ in range(9)]
        
        # Calcular primeiro dígito verificador
        weights_1 = list(range(10, 1, -1))
        digit_1 = calculate_digit(digits, weights_1)
        digits.append(digit_1)
        
        # Calcular segundo dígito verificador
        weights_2 = list(range(11, 1, -1))
        digit_2 = calculate_digit(digits, weights_2)
        digits.append(digit_2)
        
        return ''.join(map(str, digits))
    
    def cns(self) -> str:
        """Gerar CNS (Cartão Nacional de Saúde) válido"""
        # Simplificado: CNS começa com 1, 2, 7, 8 ou 9
        prefix = random.choice(['1', '2', '7', '8', '9'])
        # Gerar 14 dígitos restantes
        digits = prefix + ''.join([str(random.randint(0, 9)) for _ in range(14)])
        return digits

# Registrar provider
fake_br.add_provider(BrazilianDocumentProvider)

# ============================================================================
# IBGE MUNICIPALITIES (amostra)
# ============================================================================

IBGE_MUNICIPALITIES = [
    {"code": "3550308", "name": "São Paulo", "state": "SP"},
    {"code": "3304557", "name": "Rio de Janeiro", "state": "RJ"},
    {"code": "3106200", "name": "Belo Horizonte", "state": "MG"},
    {"code": "4106902", "name": "Curitiba", "state": "PR"},
    {"code": "4314902", "name": "Porto Alegre", "state": "RS"},
    {"code": "2927408", "name": "Salvador", "state": "BA"},
    {"code": "2304400", "name": "Fortaleza", "state": "CE"},
    {"code": "5300108", "name": "Brasília", "state": "DF"},
    {"code": "1302603", "name": "Manaus", "state": "AM"},
    {"code": "2611606", "name": "Recife", "state": "PE"},
]

# ============================================================================
# PATIENT GENERATOR
# ============================================================================

class PatientGenerator:
    """Gerador de pacientes sintéticos FHIR R4"""
    
    def __init__(self):
        self.fake_br = fake_br
        self.fake_en = fake_en
        self.generated_cpfs = set()
        self.generated_cns = set()
    
    def generate_fhir_id(self) -> str:
        """Gerar ID FHIR único"""
        return f"patient-{self.fake_en.uuid4()}"
    
    def generate_unique_cpf(self) -> str:
        """Gerar CPF único"""
        while True:
            cpf = self.fake_br.cpf()
            if cpf not in self.generated_cpfs:
                self.generated_cpfs.add(cpf)
                return cpf
    
    def generate_unique_cns(self) -> str:
        """Gerar CNS único"""
        while True:
            cns = self.fake_br.cns()
            if cns not in self.generated_cns:
                self.generated_cns.add(cns)
                return cns
    
    def generate_birth_date(self, min_age: int = 18, max_age: int = 90) -> str:
        """Gerar data de nascimento"""
        today = datetime.now()
        min_date = today - timedelta(days=max_age * 365)
        max_date = today - timedelta(days=min_age * 365)
        birth_date = self.fake_br.date_between(start_date=min_date, end_date=max_date)
        return birth_date.strftime("%Y-%m-%d")
    
    def generate_patient(self) -> Dict:
        """
        Gerar paciente sintético completo (FHIR R4).
        
        Returns:
            dict: Recurso FHIR Patient completo
        """
        # Dados básicos
        fhir_id = self.generate_fhir_id()
        cpf = self.generate_unique_cpf()
        cns = self.generate_unique_cns()
        gender = random.choice(['male', 'female'])
        
        # Nome
        if gender == 'male':
            given_name = self.fake_br.first_name_male()
            family_name = self.fake_br.last_name()
        else:
            given_name = self.fake_br.first_name_female()
            family_name = self.fake_br.last_name()
        
        # Data de nascimento
        birth_date = self.generate_birth_date()
        
        # Município (IBGE)
        municipality = random.choice(IBGE_MUNICIPALITIES)
        
        # Endereço
        address_line = self.fake_br.street_address()
        city = municipality["name"]
        state = municipality["state"]
        postal_code = self.fake_br.postcode()
        
        # Recurso FHIR R4 Patient
        fhir_patient = {
            "resourceType": "Patient",
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
                "family": family_name,
                "given": [given_name]
            }],
            "gender": gender,
            "birthDate": birth_date,
            "address": [{
                "use": "home",
                "type": "physical",
                "line": [address_line],
                "city": city,
                "state": state,
                "postalCode": postal_code,
                "country": "BR",
                "extension": [{
                    "url": "http://hl7.org/fhir/StructureDefinition/iso21090-SC-coding",
                    "valueCoding": {
                        "system": "http://www.saude.gov.br/fhir/r4/CodeSystem/CBHPM",
                        "code": municipality["code"],
                        "display": municipality["name"]
                    }
                }]
            }]
        }
        
        return {
            "fhir_id": fhir_id,
            "cpf": cpf,
            "cns": cns,
            "name_given": given_name,
            "name_family": family_name,
            "birth_date": birth_date,
            "gender": gender,
            "municipality_code": municipality["code"],
            "municipality_name": municipality["name"],
            "data": fhir_patient
        }
    
    def generate_batch(self, count: int = 5000) -> List[Dict]:
        """
        Gerar lote de pacientes.
        
        Args:
            count: Número de pacientes a gerar
        
        Returns:
            list: Lista de pacientes
        """
        patients = []
        for i in range(count):
            patient = self.generate_patient()
            patients.append(patient)
            
            if (i + 1) % 500 == 0:
                print(f"✅ Generated {i + 1}/{count} patients...")
        
        return patients

