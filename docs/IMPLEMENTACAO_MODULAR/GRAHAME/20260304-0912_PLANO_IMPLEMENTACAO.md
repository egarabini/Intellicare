# GRAHAME — Plano de Implementacao
**Data:** 2026-03-04
**Versao:** 1.0.0
**Estimativa Total:** 3-5 dias
**Prioridade:** ONDA 2 — Core Clinico

---

## Estado Atual

GRAHAME tem endpoints FHIR funcionais para Patient, Observation e Condition.
O foco desta versao e hardening e expansao para recursos adicionais,
alem de implementar CDS Hooks 2.0.

---

## Fase 1 — Auditoria e Hardening (Dia 1) — ~4h

### Tarefa 1.1 — Verificar estado atual
```bash
cd intellicare-grahame
pip install -e ".[dev]"
pytest tests/ -v --tb=short
uvicorn grahame.api.app:app --port 8012
curl http://localhost:8012/api/v1/health
curl -X POST http://localhost:8012/api/v1/Patient \
  -H "Content-Type: application/json" \
  -d '{"resourceType":"Patient","name":[{"text":"Teste"}]}'
```
- [ ] Identificar endpoints funcionais
- [ ] Listar testes passando vs falhando
- [ ] Corrigir falhas criticas

### Tarefa 1.2 — Adicionar MedicationRequest
- [ ] Rota GET/POST /MedicationRequest seguindo padrao existente
- [ ] Testes para MedicationRequest

### Tarefa 1.3 — Endpoint $everything
```python
# GET /Patient/{id}/$everything → Bundle com todos os recursos
async def patient_everything(patient_id: str, db, tenant):
    # Buscar: Patient, Observations, Conditions, MedicationRequests, Encounters
    # Agregar em Bundle
```
- [ ] Implementar $everything
- [ ] Testar com paciente que tem multiplos recursos

---

## Fase 2 — CDS Hooks (Dia 2-3) — ~5h

### Tarefa 2.1 — Discovery endpoint
```python
# GET /cds-services
{
  "services": [
    {
      "hook": "patient-view",
      "title": "IntelliCare Patient Summary",
      "description": "Alertas clinicos ao abrir o prontuario",
      "id": "patient-view"
    }
  ]
}
```

### Tarefa 2.2 — patient-view hook
```python
# POST /cds-services/patient-view
# Input: fhirAuthorization, context.patientId
# Logica:
#   1. Buscar Conditions ativas do paciente
#   2. Buscar Observations recentes
#   3. Gerar cards de alerta se: creatinina > 1.5, HbA1c > 9, etc.
# Output: {"cards": [...]}
```
- [ ] Implementar patient-view com pelo menos 3 regras de alerta
- [ ] Testar com paciente simulado

### Tarefa 2.3 — order-sign hook (opcional para v2.0)
- [ ] Implementar verificacao de contraindicacoes baseada em Conditions ativas
- [ ] Testar com prescricao de IECA em paciente com creatinina alta

---

## Fase 3 — Testes e Release (Dia 4-5) — ~4h

### Tarefa 3.1 — Suite completa
```bash
pytest tests/ -v --cov=grahame --cov-report=term-missing
```
- [ ] Meta: >= 80% cobertura, 0 falhas
- [ ] Testes de CDS Hooks incluidos

### Tarefa 3.2 — Docker smoke test
```bash
docker compose up --build -d
curl http://localhost:8012/api/v1/health
curl http://localhost:8012/cds-services
```
- [ ] Container sobe com PostgreSQL
- [ ] Migrations aplicadas automaticamente no startup

### Tarefa 3.3 — Validar integracao com GERALDA
- [ ] GERALDA cria CarePlan e envia para GRAHAME
- [ ] GRAHAME armazena e retorna no $everything do paciente

---

## Checklist de Entrega

| Item | Status |
|------|--------|
| CRUD Patient/Observation/Condition | [ ] |
| MedicationRequest implementado | [ ] |
| $everything retorna Bundle completo | [ ] |
| patient-view CDS Hook com 3 regras | [ ] |
| pytest >= 80% cobertura | [ ] |
| docker compose up → healthy | [ ] |
| smoke_tests.py inclui GRAHAME | [ ] |

---

*GRAHAME v2.0 — Plano de Implementacao — 2026-03-04*
