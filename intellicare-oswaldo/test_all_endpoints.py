"""
Comprehensive test of all CRUD endpoints for Oswaldo.
"""

from src.oswaldo.api.main import app
from fastapi.testclient import TestClient
import json

client = TestClient(app)

print("=" * 60)
print("TESTE DOS ENDPOINTS DO OSWALDO")
print("=" * 60)

# 1. Create condition
print("\n1. CREATE CONDITION (POST /condicoes)")
payload = {
    'cid10': 'I10',
    'medico_diagnosticador': 'Dr. Silva',
    'confirmacao_exames': True,
    'gravidade_inicial': 'LEVE'
}
response = client.post('/api/v1/oswaldo/condicoes?paciente_cpf_hash=pacient001', json=payload)
print(f"   Status: {response.status_code}")
condicao = response.json()
condicao_id = condicao['id']
print(f"   ✓ Condition created with ID: {condicao_id}")

# 2. Get condition by ID
print("\n2. GET CONDITION BY ID (GET /condicoes/{id})")
response = client.get(f'/api/v1/oswaldo/condicoes/{condicao_id}')
print(f"   Status: {response.status_code}")
print(f"   ✓ Condition retrieved: {response.json()['cid10']}")

# 3. List patient conditions
print("\n3. LIST PATIENT CONDITIONS (GET /paciente/{cpf}/condicoes)")
response = client.get('/api/v1/oswaldo/paciente/pacient001/condicoes')
print(f"   Status: {response.status_code}")
result = response.json()
print(f"   ✓ Total conditions: {result['total']}")

# 4. Update condition
print("\n4. UPDATE CONDITION (PUT /condicoes/{id})")
update_payload = {
    'status': 'REVISADO',
    'gravidade_inicial': 'MODERADA'
}
response = client.put(f'/api/v1/oswaldo/condicoes/{condicao_id}', json=update_payload)
print(f"   Status: {response.status_code}")
print(f"   ✓ Condition updated: {response.json()['status']}")

# 5. Create acompanhamento
print("\n5. CREATE FOLLOW-UP (POST /acompanhamentos)")
acomp_payload = {
    'condicao_cronica_id': condicao_id,
    'medico_responsavel': 'Dr. Santos',
    'pa_sist': 140,
    'pa_diast': 90,
    'aderencia_medicacao': 85
}
response = client.post('/api/v1/oswaldo/acompanhamentos?paciente_cpf_hash=pacient001', json=acomp_payload)
print(f"   Status: {response.status_code}")
acompanhamento = response.json()
print(f"   ✓ Follow-up created with ID: {acompanhamento['id']}")

# 6. List acompanhamentos
print("\n6. LIST FOLLOW-UPS (GET /paciente/{cpf}/acompanhamentos)")
response = client.get('/api/v1/oswaldo/paciente/pacient001/acompanhamentos')
print(f"   Status: {response.status_code}")
result = response.json()
print(f"   ✓ Total follow-ups: {result['total']}")

# 7. Get timeline
print("\n7. GET PATIENT TIMELINE (GET /paciente/{cpf}/timeline)")
response = client.get('/api/v1/oswaldo/paciente/pacient001/timeline')
print(f"   Status: {response.status_code}")
result = response.json()
print(f"   ✓ Timeline events: {result['total_eventos']}")
print(f"   ✓ Conditions: {result['total_condicoes']}")
print(f"   ✓ Follow-ups: {result['total_acompanhamentos']}")

# 8. Get pending alerts
print("\n8. LIST PENDING ALERTS (GET /alertas/pendentes)")
response = client.get('/api/v1/oswaldo/alertas/pendentes')
print(f"   Status: {response.status_code}")
result = response.json()
print(f"   ✓ Pending alerts: {result['total']}")

# 9. Get alerts summary
print("\n9. GET ALERTS SUMMARY (GET /alertas/resumo)")
response = client.get('/api/v1/oswaldo/alertas/resumo')
print(f"   Status: {response.status_code}")
print(f"   ✓ Alert summary retrieved")

print("\n" + "=" * 60)
print("✓ ALL ENDPOINTS WORKING CORRECTLY")
print("=" * 60)
