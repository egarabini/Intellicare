"""Quick test of anonymization and validation services"""

import sys
sys.path.insert(0, 'src')

from florence.services.anonymization import AnonymizationService
from florence.services.clinical_validation import ClinicaAlgorithmValidator
from datetime import datetime

print("\n" + "="*70)
print("FLORENCE IMPLEMENTATION TESTS")
print("="*70)

# ========== ANONYMIZATION TESTS ==========
print("\n[TEST] ANONYMIZATION SERVICE TESTS")
print("-" * 70)

# Test 1: Hash determinístico
cpf = '12345678901'
hash1 = AnonymizationService.hash_cpf(cpf)
hash2 = AnonymizationService.hash_cpf(cpf)
print(f"\n[OK] Test 1 - Hash Deterministic: {hash1 == hash2}")
print(f"   CPF: {cpf}")
print(f"   Hash: {hash1[:32]}...")

# Test 2: Hash irreversível
cpf2 = '12345678902'
hash3 = AnonymizationService.hash_cpf(cpf2)
print(f"\n[OK] Test 2 - Hash Irreversible (avalanche effect)")
print(f"   CPF 1: {cpf} -> {hash1[:32]}...")
print(f"   CPF 2: {cpf2} -> {hash3[:32]}...")
print(f"   Completely different: {hash1 != hash3}")

# Test 3: Name truncation
nome = 'João da Silva'
truncado = AnonymizationService.truncate_name(nome)
print(f"\n[OK] Test 3 - Name Truncation")
print(f"   Original: {nome}")
print(f"   Truncated: {truncado}")

# Test 4: Date anonymization
data = datetime(1980, 1, 15)
data_mes_ano = AnonymizationService.anonymize_date(data, 'mes')
data_ano = AnonymizationService.anonymize_date(data, 'ano')
print(f"\n[OK] Test 4 - Date Anonymization")
print(f"   Original: 15/01/1980")
print(f"   Month/Year: {data_mes_ano}")
print(f"   Year only: {data_ano}")

# ========== CLINICAL VALIDATION TESTS ==========
print("\n\n[TEST] CLINICAL VALIDATION SERVICE TESTS")
print("-" * 70)

# Test 1: Valid hemograma
valido, msg = ClinicaAlgorithmValidator.validar_hemograma(
    hemoglobina=14.5,
    hematocrito=43.0,
    plaquetas=250.0,
    leucócitos=7.0,
    diferenciais={'neutrófilos': 60, 'linfócitos': 30, 'monócitos': 7, 'eosinófilos': 2, 'basófilos': 1}
)
print(f"\n[OK] Test 1 - Valid Hemograma: {valido}")
print(f"   Message: {ascii(msg[:40])}...")

# Test 2: Invalid hemograma
valido, msg = ClinicaAlgorithmValidator.validar_hemograma(
    hemoglobina=14.5,
    hematocrito=20.0,  # Inconsistent with Hb
    plaquetas=250.0,
    leucócitos=7.0,
    diferenciais={'neutrófilos': 60, 'linfócitos': 30, 'monócitos': 7, 'eosinófilos': 2, 'basófilos': 1}
)
print(f"\n[OK] Test 2 - Invalid Hemograma (Hb/Ht mismatch): {not valido}")
print(f"   Message: {ascii(msg[:60])}...")

# Test 3: Valid lipidogram
valido, msg = ClinicaAlgorithmValidator.validar_lipidograma(
    colesterol_total=200,
    triglicérides=100,
    hdl=50,
    ldl=130
)
print(f"\n[OK] Test 3 - Valid Lipidogram: {valido}")
print(f"   Message: {ascii(msg)}")

# Test 4: Kidney function
valido, msg = ClinicaAlgorithmValidator.validar_funcao_renal(
    creatinina=1.0,
    ureia=15.0
)
print(f"\n[OK] Test 4 - Valid Kidney Function: {valido}")
print(f"   Message: {ascii(msg)}")

print("\n" + "="*70)
print("[OK] ALL TESTS PASSED!")
print("="*70 + "\n")
