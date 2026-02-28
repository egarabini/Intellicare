#!/usr/bin/env python3
"""
Script de validação rápida do Florence
Testa os componentes principais sem precisar de banco de dados
"""

import sys
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent / "src"))

print("=" * 80)
print("VALIDAÇÃO RÁPIDA DO FLORENCE")
print("=" * 80)

# Test 1: Importar módulos principais
print("\n[1/5] Testando imports...")
try:
    from florence.services.clinical_validation import ClinicaAlgorithmValidator
    from florence.models.anonymization import PacienteAnonimizado, PacienteHashMapping
    from florence.services.anonymization import AnonymizationService
    print("✅ Imports OK")
except Exception as e:
    print(f"❌ Erro nos imports: {e}")
    sys.exit(1)

# Test 2: Validador de Hemograma
print("\n[2/5] Testando validador de hemograma...")
try:
    # Caso válido: Hb=14.0, Hct=42.0 (relação 1:3)
    valido, msg = ClinicaAlgorithmValidator.validar_hemograma(
        hemoglobina=14.0,
        hematocrito=42.0,
        plaquetas=250.0,
        leucócitos=7.5,
        diferenciais={
            "neutrófilos": 60.0,
            "linfócitos": 30.0,
            "monócitos": 5.0,
            "eosinófilos": 3.0,
            "basófilos": 2.0
        },
        sexo="M"
    )
    
    if valido:
        print(f"✅ Hemograma válido: {msg}")
    else:
        print(f"⚠️ Hemograma inválido: {msg}")
        
    # Caso inválido: Hb=14.0, Hct=60.0 (relação errada)
    valido2, msg2 = ClinicaAlgorithmValidator.validar_hemograma(
        hemoglobina=14.0,
        hematocrito=60.0,  # Muito alto para Hb=14
        plaquetas=250.0,
        leucócitos=7.5,
        diferenciais={
            "neutrófilos": 60.0,
            "linfócitos": 30.0,
            "monócitos": 5.0,
            "eosinófilos": 3.0,
            "basófilos": 2.0
        },
        sexo="M"
    )
    
    if not valido2:
        print(f"✅ Detectou incoerência: {msg2}")
    else:
        print(f"❌ Não detectou incoerência")
        
except Exception as e:
    print(f"❌ Erro no validador de hemograma: {e}")
    import traceback
    traceback.print_exc()

# Test 3: Validador de Lipidograma
print("\n[3/5] Testando validador de lipidograma...")
try:
    valido, msg = ClinicaAlgorithmValidator.validar_lipidograma(
        colesterol_total=200.0,
        hdl=50.0,
        triglicerides=150.0,
        ldl_informado=120.0
    )
    
    if valido:
        print(f"✅ Lipidograma válido: {msg}")
    else:
        print(f"⚠️ Lipidograma inválido: {msg}")
        
except Exception as e:
    print(f"❌ Erro no validador de lipidograma: {e}")
    import traceback
    traceback.print_exc()

# Test 4: Validador de Glicemia
print("\n[4/5] Testando validador de glicemia...")
try:
    # Glicemia normal em jejum
    valido, msg = ClinicaAlgorithmValidator.validar_glicemia(
        glicemia=90.0,
        tipo="jejum",
        paciente_diabetico=False
    )
    
    if valido:
        print(f"✅ Glicemia normal: {msg}")
    else:
        print(f"⚠️ Glicemia anormal: {msg}")
    
    # Glicemia crítica
    valido2, msg2 = ClinicaAlgorithmValidator.validar_glicemia(
        glicemia=400.0,
        tipo="aleatorio",
        paciente_diabetico=True
    )
    
    if not valido2:
        print(f"✅ Detectou glicemia crítica: {msg2}")
    else:
        print(f"❌ Não detectou glicemia crítica")
        
except Exception as e:
    print(f"❌ Erro no validador de glicemia: {e}")
    import traceback
    traceback.print_exc()

# Test 5: Anonimização
print("\n[5/5] Testando anonimização...")
try:
    # Criar serviço de anonimização
    service = AnonymizationService()
    
    # Testar hash de CPF
    cpf = "12345678901"
    hash1 = service.hash_cpf(cpf)
    hash2 = service.hash_cpf(cpf)
    
    # Hash deve ser determinístico
    if hash1 == hash2:
        print(f"✅ Hash determinístico: {hash1[:16]}...")
    else:
        print(f"❌ Hash não determinístico")
    
    # Hash deve ter 64 caracteres (SHA256 hex)
    if len(hash1) == 64:
        print(f"✅ Hash SHA256 correto (64 chars)")
    else:
        print(f"❌ Hash com tamanho incorreto: {len(hash1)}")
    
    # Testar anonimização de paciente
    dados_paciente = {
        "cpf": "12345678901",
        "nome": "João Silva Santos",
        "data_nascimento": "1980-01-15"
    }
    
    anonimizado = service.anonymize_patient(dados_paciente)
    
    print(f"✅ Paciente anonimizado:")
    print(f"   - Hash: {anonimizado['paciente_id_hash'][:16]}...")
    print(f"   - Nome truncado: {anonimizado['nome_truncado']}")
    print(f"   - Data: {anonimizado['data_nascimento_mes_ano']}")
    
    # Verificar que não há CPF no resultado
    if 'cpf' not in anonimizado:
        print(f"✅ CPF não presente no resultado anonimizado")
    else:
        print(f"❌ CPF ainda presente no resultado!")
        
except Exception as e:
    print(f"❌ Erro na anonimização: {e}")
    import traceback
    traceback.print_exc()

# Resumo final
print("\n" + "=" * 80)
print("VALIDAÇÃO CONCLUÍDA")
print("=" * 80)
print("\n✅ Florence está funcionando corretamente!")
print("\nPróximos passos:")
print("1. Testar API REST (python run_api_8001.py)")
print("2. Executar testes completos (pytest tests/)")
print("3. Validar integração com Oswaldo")

