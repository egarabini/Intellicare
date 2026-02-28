"""
Comprehensive test of all CRUD endpoints for Oswaldo - Improved.
"""

from src.oswaldo.api.main import app
from fastapi.testclient import TestClient
import json
import uuid

client = TestClient(app)

print("=" * 70)
print("TESTE COMPLETO DOS ENDPOINTS DO OSWALDO")
print("=" * 70)

# Generate unique patient hash to avoid conflicts
patient_hash = f"patient_{uuid.uuid4().hex[:8]}"
print(f"\nPaciente teste: {patient_hash}\n")

try:
    # 1. Create condition
    print("1. CREATE CONDITION (POST /condicoes)")
    payload = {
        'cid10': 'I10',
        'medico_diagnosticador': 'Dr. Silva',
        'confirmacao_exames': True,
        'gravidade_inicial': 'LEVE'
    }
    response = client.post(f'/api/v1/oswaldo/condicoes?paciente_cpf_hash={patient_hash}', json=payload)
    assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
    condicao = response.json()
    condicao_id = condicao['id']
    print(f"   ✓ Status: {response.status_code} - Condition created with ID: {condicao_id}\n")

    # 2. Get condition by ID
    print("2. GET CONDITION BY ID (GET /condicoes/{id})")
    response = client.get(f'/api/v1/oswaldo/condicoes/{condicao_id}')
    assert response.status_code == 200
    print(f"   ✓ Status: {response.status_code} - Retrieved: {response.json()['cid10']}\n")

    # 3. List patient conditions
    print("3. LIST PATIENT CONDITIONS (GET /paciente/{cpf}/condicoes)")
    response = client.get(f'/api/v1/oswaldo/paciente/{patient_hash}/condicoes')
    assert response.status_code == 200
    result = response.json()
    print(f"   ✓ Status: {response.status_code} - Total conditions: {result['total']}\n")

    # 4. Update condition
    print("4. UPDATE CONDITION (PUT /condicoes/{id})")
    update_payload = {
        'status': 'REVISADO',
        'gravidade_inicial': 'MODERADA'
    }
    response = client.put(f'/api/v1/oswaldo/condicoes/{condicao_id}', json=update_payload)
    assert response.status_code == 200
    print(f"   ✓ Status: {response.status_code} - Updated status: {response.json()['status']}\n")

    # 5. Create acompanhamento
    print("5. CREATE FOLLOW-UP (POST /acompanhamentos)")
    acomp_payload = {
        'condicao_cronica_id': condicao_id,
        'medico_responsavel': 'Dr. Santos',
        'pa_sist': 140,
        'pa_diast': 90,
        'glicemia_jejum': 150.5,
        'aderencia_medicacao': 85
    }
    response = client.post(f'/api/v1/oswaldo/acompanhamentos?paciente_cpf_hash={patient_hash}', json=acomp_payload)
    assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
    acompanhamento = response.json()
    acomp_id = acompanhamento['id']
    print(f"   ✓ Status: {response.status_code} - Follow-up created with ID: {acomp_id}\n")

    # 6. List acompanhamentos
    print("6. LIST FOLLOW-UPS (GET /paciente/{cpf}/acompanhamentos)")
    response = client.get(f'/api/v1/oswaldo/paciente/{patient_hash}/acompanhamentos')
    assert response.status_code == 200
    result = response.json()
    print(f"   ✓ Status: {response.status_code} - Total follow-ups: {result['total']}\n")

    # 7. Get specific acompanhamento
    print("7. GET SPECIFIC FOLLOW-UP (GET /acompanhamentos/{id})")
    response = client.get(f'/api/v1/oswaldo/acompanhamentos/{acomp_id}')
    assert response.status_code == 200
    print(f"   ✓ Status: {response.status_code} - Follow-up retrieved\n")

    # 8. Get timeline
    print("8. GET PATIENT TIMELINE (GET /paciente/{cpf}/timeline)")
    response = client.get(f'/api/v1/oswaldo/paciente/{patient_hash}/timeline')
    assert response.status_code == 200
    result = response.json()
    print(f"   ✓ Status: {response.status_code}")
    print(f"      - Timeline events: {result['total_eventos']}")
    print(f"      - Conditions: {result['total_condicoes']}")
    print(f"      - Follow-ups: {result['total_acompanhamentos']}\n")

    # 9. Get pending alerts
    print("9. LIST PENDING ALERTS (GET /alertas/pendentes)")
    response = client.get('/api/v1/oswaldo/alertas/pendentes')
    assert response.status_code == 200
    result = response.json()
    print(f"   ✓ Status: {response.status_code} - Pending alerts: {result['total']}\n")

    # 10. Get alerts summary
    print("10. GET ALERTS SUMMARY (GET /alertas/resumo)")
    response = client.get('/api/v1/oswaldo/alertas/resumo')
    assert response.status_code == 200
    print(f"   ✓ Status: {response.status_code} - Alert summary retrieved\n")

    # 11. Test duplicate condition prevention
    print("11. TEST DUPLICATE PREVENTION (POST duplicate)")
    response = client.post(f'/api/v1/oswaldo/condicoes?paciente_cpf_hash={patient_hash}', json=payload)
    assert response.status_code == 400, f"Expected 400, got {response.status_code}"
    print(f"   ✓ Status: {response.status_code} - Duplicate correctly rejected\n")

    # 12. Test invalid status transition
    print("12. TEST INVALID STATUS TRANSITION (PUT with bad status)")
    invalid_update = {'status': 'INVALID_STATUS'}
    response = client.put(f'/api/v1/oswaldo/condicoes/{condicao_id}', json=invalid_update)
    assert response.status_code == 400
    print(f"   ✓ Status: {response.status_code} - Invalid transition correctly rejected\n")

    # 13. Test delete (soft-delete)
    print("13. SOFT-DELETE CONDITION (DELETE /condicoes/{id})")
    response = client.delete(f'/api/v1/oswaldo/condicoes/{condicao_id}')
    assert response.status_code == 200
    print(f"   ✓ Status: {response.status_code} - Condition soft-deleted\n")

    # 14. Verify deleted condition is now ENCERRADO
    print("14. VERIFY SOFT-DELETE (GET deleted condition)")
    response = client.get(f'/api/v1/oswaldo/condicoes/{condicao_id}')
    assert response.status_code == 200
    status = response.json()['status']
    assert status == 'ENCERRADO'
    print(f"   ✓ Status: {response.status_code} - Condition status is now: {status}\n")

    print("=" * 70)
    print("✓ ALL 14 ENDPOINT TESTS PASSED SUCCESSFULLY!")
    print("=" * 70)
    print("\nEndpoints Tested:")
    print("  ✓ POST   /api/v1/oswaldo/condicoes")
    print("  ✓ GET    /api/v1/oswaldo/condicoes/{id}")
    print("  ✓ GET    /api/v1/oswaldo/paciente/{cpf}/condicoes")
    print("  ✓ PUT    /api/v1/oswaldo/condicoes/{id}")
    print("  ✓ DELETE /api/v1/oswaldo/condicoes/{id}")
    print("  ✓ POST   /api/v1/oswaldo/acompanhamentos")
    print("  ✓ GET    /api/v1/oswaldo/acompanhamentos/{id}")
    print("  ✓ GET    /api/v1/oswaldo/paciente/{cpf}/acompanhamentos")
    print("  ✓ GET    /api/v1/oswaldo/paciente/{cpf}/timeline")
    print("  ✓ GET    /api/v1/oswaldo/alertas/pendentes")
    print("  ✓ GET    /api/v1/oswaldo/alertas/resumo")
    print("=" * 70)

except AssertionError as e:
    print(f"\n✗ TEST FAILED: {e}")
    exit(1)
except Exception as e:
    print(f"\n✗ UNEXPECTED ERROR: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
