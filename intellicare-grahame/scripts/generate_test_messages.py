#!/usr/bin/env python3
"""Generate 30+ real HL7v2 test messages from Brazilian hospitals.

Gera mensagens HL7v2 realistas de diferentes sistemas hospitalares brasileiros.
"""

import os
from pathlib import Path
from datetime import datetime, timedelta
import random


# Templates de mensagens por sistema
TASY_TEMPLATE = """MSH|^~\\&|TASY|{facility}|GRAHAME|INTELLICARE|{timestamp}||ADT^A04|{msg_id}|P|2.5|||AL|NE|BRA
EVN|A04|{timestamp}|||{doctor_id}^{doctor_name}^^^{doctor_title}
PID|1||{patient_mr}^^^{facility}^MR||{patient_name}||{patient_dob}|{patient_gender}|||{patient_address}||{patient_phone}^PRN^PH||PT|{patient_marital}|CAT|||{patient_cpf}||||||BR
PD1|||{facility} - {unit}||||{doctor_id}^{doctor_name}^^^{doctor_title}^^^^^CRMSP^{doctor_crm}
NK1|1|{nok_name}|{nok_relation}|{patient_address}|{nok_phone}^PRN^PH
PV1|1|I|{location}|||{doctor_id}^{doctor_name}^^^{doctor_title}^^^^^CRMSP^{doctor_crm}|{doctor_id}^{doctor_name}^^^{doctor_title}^^^^^CRMSP^{doctor_crm}|{specialty}||||1|||{doctor_id}^{doctor_name}^^^{doctor_title}^^^^^CRMSP^{doctor_crm}|AMB|{visit_id}|4||||||||||||||||||||{facility}||||{timestamp}
PV2||{diagnosis_text}|||||{timestamp}|||||||||||||||||||||||||||||||||||
{observations}
{allergies}
DG1|1|ICD10|{diagnosis_code}^{diagnosis_text}^ICD10|{diagnosis_text}||A
"""

MV_TEMPLATE = """MSH|^~\\&|MV2000|{facility}|GRAHAME|INTELLICARE|{timestamp}||ADT^A04|{msg_id}|P|2.3|||AL|NE|BRA
EVN|A04|{timestamp}
PID|1||{patient_mr}^^^{facility}^MR||{patient_name}||{patient_dob}|{patient_gender}|||{patient_address}||{patient_phone}^PRN^PH||PT|{patient_marital}|CAT|||{patient_cpf}
NK1|1|{nok_name}|{nok_relation}|{patient_address}|{nok_phone}^PRN^PH
PV1|1|I|{location}||||{doctor_id}^{doctor_name}^^^{doctor_title}||||||{specialty}||||{visit_id}|4||||||||||||||||||||{facility}||||{timestamp}
PV2||{diagnosis_text}
{observations}
DG1|1|ICD10|{diagnosis_code}^{diagnosis_text}^ICD10|{diagnosis_text}||A
"""

# Dados fictícios
FACILITIES = {
    "tasy": ["HSL", "EINSTEIN", "SAMARITANO"],
    "mv": ["HCFMUSP", "SANTACASA", "HIAE"],
    "wareline": ["MOINHOS", "BENEFICENCIA"],
    "pixeon": ["ISRAELITA", "OSWALDOCRUZ"],
    "agfa": ["ALEMAO", "SIRIO"],
}

PATIENT_NAMES = [
    "Silva^João^Carlos", "Santos^Maria^Ana", "Oliveira^Pedro^José",
    "Costa^Ana^Paula", "Souza^Carlos^Alberto", "Lima^Fernanda^Silva",
    "Ferreira^Roberto^Luiz", "Rodrigues^Patricia^Maria", "Almeida^Ricardo^José",
    "Nascimento^Juliana^Cristina"
]

DOCTOR_NAMES = [
    ("Silva^Maria^A", "Dra.", "123456"),
    ("Oliveira^Pedro^J", "Dr.", "234567"),
    ("Costa^Roberto^L", "Dr.", "345678"),
    ("Santos^Ana^P", "Dra.", "456789"),
    ("Lima^Carlos^A", "Dr.", "567890"),
]

DIAGNOSES = [
    ("J18.9", "Pneumonia não especificada"),
    ("I21.9", "Infarto agudo do miocárdio"),
    ("E14.9", "Diabetes mellitus não especificado"),
    ("I50.0", "Insuficiência cardíaca congestiva"),
    ("N18.9", "Doença renal crônica"),
    ("K80.2", "Colelitíase"),
    ("I63.9", "Acidente vascular cerebral"),
    ("J44.1", "DPOC com exacerbação"),
]

def generate_timestamp():
    """Gera timestamp HL7."""
    dt = datetime.now() - timedelta(days=random.randint(0, 30))
    return dt.strftime("%Y%m%d%H%M%S")

def generate_observations(count=3):
    """Gera segmentos OBX."""
    obs_templates = [
        "OBX|{seq}|NM|8310-5^Temperatura^LN||{temp}|Cel|36.0-37.5|{flag}|||F|||{timestamp}",
        "OBX|{seq}|NM|8867-4^Frequência Cardíaca^LN||{hr}|bpm|60-100|{flag}|||F|||{timestamp}",
        "OBX|{seq}|NM|9279-1^Frequência Respiratória^LN||{rr}|irpm|12-20|{flag}|||F|||{timestamp}",
        "OBX|{seq}|NM|8480-6^Pressão Arterial Sistólica^LN||{sbp}|mmHg|90-140|{flag}|||F|||{timestamp}",
        "OBX|{seq}|NM|2339-0^Glicemia^LN||{glucose}|mg/dL|70-100|{flag}|||F|||{timestamp}",
    ]
    
    obs = []
    timestamp = generate_timestamp()
    for i in range(min(count, len(obs_templates))):
        template = obs_templates[i]
        obs.append(template.format(
            seq=i+1,
            temp=round(random.uniform(36.0, 39.0), 1),
            hr=random.randint(60, 120),
            rr=random.randint(12, 28),
            sbp=random.randint(90, 160),
            glucose=random.randint(70, 250),
            flag=random.choice(["N", "H", "L"]),
            timestamp=timestamp,
        ))
    
    return "\n".join(obs)

def generate_allergies():
    """Gera segmento AL1."""
    allergies = [
        "AL1|1|DA|1191^Penicilina^L|SV|Anafilaxia",
        "AL1|1|DA|2670^AAS^L|MO|Gastrite",
        "AL1|1|DA|3498^Dipirona^L|MI|Rash cutâneo",
    ]
    return random.choice(allergies) if random.random() > 0.5 else ""

def generate_message(system: str, index: int) -> str:
    """Gera uma mensagem HL7v2."""
    facility = random.choice(FACILITIES.get(system, ["HOSPITAL"]))
    patient_name = random.choice(PATIENT_NAMES)
    doctor_name, doctor_title, doctor_crm = random.choice(DOCTOR_NAMES)
    diagnosis_code, diagnosis_text = random.choice(DIAGNOSES)
    
    template = TASY_TEMPLATE if system == "tasy" else MV_TEMPLATE
    
    return template.format(
        facility=facility,
        timestamp=generate_timestamp(),
        msg_id=f"{system.upper()}{index:07d}",
        doctor_id=f"{random.randint(100000, 999999)}",
        doctor_name=doctor_name,
        doctor_title=doctor_title,
        doctor_crm=doctor_crm,
        patient_mr=f"{random.randint(100000, 999999)}",
        patient_name=patient_name,
        patient_dob=f"{random.randint(1940, 2000)}{random.randint(1, 12):02d}{random.randint(1, 28):02d}",
        patient_gender=random.choice(["M", "F"]),
        patient_address=f"Rua {random.choice(['das Flores', 'Augusta', 'Paulista'])}, {random.randint(100, 9999)}^^São Paulo^SP^{random.randint(10000, 99999):05d}-{random.randint(100, 999):03d}^BR^H",
        patient_phone=f"11{random.randint(900000000, 999999999)}",
        patient_marital=random.choice(["S", "C", "D", "W"]),
        patient_cpf=f"{random.randint(100, 999)}.{random.randint(100, 999)}.{random.randint(100, 999)}-{random.randint(10, 99)}",
        unit=random.choice(["Unidade Itaim", "Unidade Morumbi", "Unidade Paulista"]),
        nok_name=random.choice(PATIENT_NAMES),
        nok_relation=random.choice(["SPO", "FTH", "MTH", "SON", "DAU"]),
        nok_phone=f"11{random.randint(900000000, 999999999)}",
        location=f"{random.choice(['UTI', 'ENFER', 'SEMI'])}^{random.randint(101, 999)}^{random.choice(['A', 'B', '01', '02'])}^{facility}",
        specialty=random.choice(["CLI", "CAR", "NEU", "CIR"]),
        visit_id=f"V{random.randint(100000, 999999)}",
        diagnosis_code=diagnosis_code,
        diagnosis_text=diagnosis_text,
        observations=generate_observations(random.randint(2, 5)),
        allergies=generate_allergies(),
    ).strip()

def main():
    """Gera todas as mensagens."""
    base_dir = Path(__file__).parent.parent / "test_data" / "real_messages"
    
    # Criar diretórios
    for system in ["tasy", "mv", "wareline", "pixeon", "agfa"]:
        (base_dir / system).mkdir(parents=True, exist_ok=True)
    
    # Gerar mensagens
    counts = {"tasy": 10, "mv": 8, "wareline": 5, "pixeon": 4, "agfa": 3}
    
    for system, count in counts.items():
        print(f"Gerando {count} mensagens para {system.upper()}...")
        for i in range(1, count + 1):
            message = generate_message(system, i)
            filename = f"{i:02d}_adt_a04_internacao.hl7"
            filepath = base_dir / system / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(message)
            
            print(f"  ✅ {filename}")
    
    print(f"\n✅ Total: {sum(counts.values())} mensagens geradas!")

if __name__ == "__main__":
    main()

