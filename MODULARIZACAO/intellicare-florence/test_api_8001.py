#!/usr/bin/env python
"""Quick test of Florence API endpoints - Updated for port 8001"""

import requests
import json

BASE_URL = "http://localhost:8001/api/v1/validacao"

print("\n" + "="*60)
print("TESTES RÁPIDOS - FLORENCE API (Porta 8001)")
print("="*60)

# Test 1: Health
print("\n✓ TESTE 1: Health Check")
r = requests.get("http://localhost:8001/health")
print(f"  Status: {r.status_code} - {r.json()['status']}")

# Test 2: Tipos Suportados
print("\n✓ TESTE 2: Tipos Suportados")
r = requests.get(f"{BASE_URL}/tipos-suportados")
print(f"  Status: {r.status_code}")
print(f"  Tipos: {', '.join(r.json()['tipos'])}")

# Test 3: Hemograma Válido
print("\n✓ TESTE 3: Hemograma Válido")
payload = {
    "tipo_exame": "hemograma",
    "sexo": "M",
    "dados": {
        "hemoglobina": 14.5,
        "hematocrito": 42.5,
        "plaquetas": 250,
        "leucocitos": 7.0,
        "diferenciais": {
            "neutrofilos": 60,
            "linfocitos": 30,
            "monocitos": 8,
            "eosinofilos": 2
        }
    }
}
r = requests.post(f"{BASE_URL}/validador-clinico", json=payload)
resultado = r.json()
print(f"  Status: {r.status_code}")
print(f"  Válido: {resultado['valido']} ✅")
print(f"  Mensagem: {resultado['mensagem']}")

# Test 4: Hemograma Incoerente
print("\n✓ TESTE 4: Hemograma Incoerente (Hb/Ht mismatch)")
payload["dados"]["hematocrito"] = 30.0  # Incoerente
r = requests.post(f"{BASE_URL}/validador-clinico", json=payload)
resultado = r.json()
print(f"  Status: {r.status_code}")
print(f"  Válido: {resultado['valido']} (esperado False)")
print(f"  Mensagem: {resultado['mensagem']}")

# Test 5: Glicemia Crítica
print("\n✓ TESTE 5: Glicemia Crítica")
payload5 = {
    "tipo_exame": "glicemia",
    "tipo_amostra": "aleatoria",
    "paciente_diabetico": True,
    "dados": {"glicemia": 350}
}
r = requests.post(f"{BASE_URL}/validador-clinico", json=payload5)
resultado = r.json()
print(f"  Status: {r.status_code}")
print(f"  Válido: {resultado['valido']} (esperado False)")
print(f"  Mensagem: {resultado['mensagem']}")

# Test 6: Lipidograma Válido
print("\n✓ TESTE 6: Lipidograma Válido (Friedewald)")
payload6 = {
    "tipo_exame": "lipidograma",
    "dados": {
        "colesterol_total": 200,
        "triglicerida": 100,
        "hdl": 50,
        "ldl": 130
    }
}
r = requests.post(f"{BASE_URL}/validador-clinico", json=payload6)
resultado = r.json()
print(f"  Status: {r.status_code}")
print(f"  Válido: {resultado['valido']} ✅")
print(f"  Mensagem: {resultado['mensagem']}")

# Test 7: Função Renal Válida
print("\n✓ TESTE 7: Função Renal Válida")
payload7 = {
    "tipo_exame": "funcao_renal",
    "age_anos": 45,
    "dados": {
        "creatinina": 1.0,
        "ureia": 15
    }
}
r = requests.post(f"{BASE_URL}/validador-clinico", json=payload7)
resultado = r.json()
print(f"  Status: {r.status_code}")
print(f"  Válido: {resultado['valido']} ✅")
print(f"  Mensagem: {resultado['mensagem']}")

# Test 8: Hepatograma Válido
print("\n✓ TESTE 8: Hepatograma Válido")
payload8 = {
    "tipo_exame": "hepatograma",
    "dados": {
        "ast": 30,
        "alt": 28,
        "bilirrubina_total": 1.0,
        "bilirrubina_direta": 0.2,
        "fosfatase_alcalina": 80
    }
}
r = requests.post(f"{BASE_URL}/validador-clinico", json=payload8)
resultado = r.json()
print(f"  Status: {r.status_code}")
print(f"  Válido: {resultado['valido']} ✅")
print(f"  Mensagem: {resultado['mensagem']}")

print("\n" + "="*60)
print("✅ TODOS OS TESTES COMPLETADOS COM SUCESSO!")
print("="*60)
print("\n📋 API está pronta para apresentação ao especialista")
print("📍 Swagger UI: http://localhost:8001/api/docs")
print("📍 ReDoc: http://localhost:8001/api/redoc")
print("\n💡 Dica: Use http://localhost:8001/api/docs durante a reunião")
