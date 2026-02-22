# EF-002 — Integracao FHIR CarePlan

> Integrar a Geralda com o servidor FHIR R4 para ler e escrever recursos CarePlan, alinhando os planos de cuidado ao padrao internacional.

## 1. Objetivo

Os planos de cuidado da Geralda devem ser representados como recursos FHIR CarePlan, permitindo interoperabilidade com outros sistemas de saude (RNDS, hospitais, UBS) e alinhamento com o padrao HL7 FHIR R4.

## 2. Justificativa

- **Interoperabilidade**: FHIR e o padrao nacional (RNDS) e internacional
- **Compartilhamento**: Outros modulos (Florence, Oswaldo) podem consumir CarePlan
- **Rastreabilidade**: Historico clinico completo no servidor FHIR
- **Conformidade**: Requisito do ecossistema IntelliCare (FHIR R4 como lingua franca)

## 3. Escopo

### 3.1 Recursos FHIR Utilizados

#### CarePlan (Principal)
```json
{
  "resourceType": "CarePlan",
  "id": "cp-geralda-001",
  "status": "active",
  "intent": "plan",
  "title": "Plano de Cuidado - DRC + DM2",
  "subject": {
    "reference": "Patient/patient-123"
  },
  "period": {
    "start": "2026-02-15"
  },
  "category": [
    {
      "coding": [
        {
          "system": "http://hl7.org/fhir/us/core/CodeSystem/careplan-category",
          "code": "assess-plan"
        }
      ]
    }
  ],
  "addresses": [
    {
      "reference": "Condition/cond-n18-3",
      "display": "Doenca Renal Cronica G3a"
    },
    {
      "reference": "Condition/cond-e11",
      "display": "Diabetes Mellitus Tipo 2"
    }
  ],
  "goal": [
    {
      "reference": "Goal/goal-001",
      "display": "Manter eGFR acima de 45 mL/min"
    }
  ],
  "activity": [
    {
      "detail": {
        "kind": "MedicationRequest",
        "code": {
          "text": "Tomar Losartana 50mg 1x/dia"
        },
        "status": "in-progress",
        "scheduledTiming": {
          "repeat": {
            "frequency": 1,
            "period": 1,
            "periodUnit": "d"
          }
        },
        "description": "Medicamento para controle da pressao e protecao renal"
      }
    }
  ],
  "note": [
    {
      "text": "Plano criado pela Geralda em 15/02/2026"
    }
  ]
}
```

#### Task (Atividades do Plano)
```json
{
  "resourceType": "Task",
  "status": "requested",
  "intent": "plan",
  "basedOn": [
    { "reference": "CarePlan/cp-geralda-001" }
  ],
  "for": {
    "reference": "Patient/patient-123"
  },
  "code": {
    "text": "Medir pressao arterial"
  },
  "description": "Aferir PA em repouso, anotar valores",
  "executionPeriod": {
    "start": "2026-02-15T08:00:00-03:00"
  }
}
```

#### CommunicationRequest (Lembretes)
```json
{
  "resourceType": "CommunicationRequest",
  "status": "active",
  "category": [
    {
      "coding": [
        {
          "system": "http://intellicare.health/fhir/CodeSystem/reminder-category",
          "code": "medication-reminder"
        }
      ]
    }
  ],
  "subject": {
    "reference": "Patient/patient-123"
  },
  "payload": [
    {
      "contentString": "Hora de tomar seu medicamento: Losartana 50mg"
    }
  ],
  "occurrenceTiming": {
    "repeat": {
      "frequency": 1,
      "period": 1,
      "periodUnit": "d",
      "timeOfDay": ["08:00"]
    }
  }
}
```

### 3.2 Operacoes FHIR

#### Leitura (Consumo)
| Operacao | Endpoint FHIR | Quando |
|----------|--------------|--------|
| Buscar CarePlans do paciente | `GET /CarePlan?subject=Patient/{id}&status=active` | Ao abrir painel do paciente |
| Buscar Conditions do paciente | `GET /Condition?subject=Patient/{id}&clinical-status=active` | Ao criar plano (auto-preencher) |
| Buscar Medications | `GET /MedicationRequest?subject=Patient/{id}&status=active` | Ao gerar lembretes de medicacao |
| Buscar Patient | `GET /Patient/{id}` | Ao registrar paciente |
| IPS Summary | `GET /Patient/{id}/$summary` | Antes de qualquer analise (IPS-First) |

#### Escrita (Producao)
| Operacao | Endpoint FHIR | Quando |
|----------|--------------|--------|
| Criar CarePlan | `POST /CarePlan` | Ao criar plano na Geralda |
| Atualizar CarePlan | `PUT /CarePlan/{id}` | Ao modificar plano |
| Criar Task | `POST /Task` | Ao adicionar tarefa ao plano |
| Atualizar Task status | `PUT /Task/{id}` | Ao completar/pular tarefa |
| Criar CommunicationRequest | `POST /CommunicationRequest` | Ao criar lembrete |
| Registrar Communication | `POST /Communication` | Ao enviar lembrete (registro) |

### 3.3 Camada de Adaptacao FHIR

Criar `geralda/fhir/` com:

```
geralda/fhir/
  __init__.py
  careplan_adapter.py     # Converte CarePlan FHIR <-> CarePlan Geralda
  task_adapter.py         # Converte Task FHIR <-> CareTask Geralda
  reminder_adapter.py     # Converte CommunicationRequest <-> Reminder Geralda
  patient_adapter.py      # Busca e enriquece dados do paciente
  fhir_sync.py            # Sincronizacao bidirecional
```

### 3.4 Mapeamento Bidirecional

#### CarePlan Geralda -> FHIR
```python
class CarePlanFHIRAdapter:
    def to_fhir(self, plan: CarePlan) -> dict:
        """Converte CarePlan interno para recurso FHIR R4"""

    def from_fhir(self, fhir_resource: dict) -> CarePlan:
        """Converte recurso FHIR R4 para CarePlan interno"""

    async def sync_to_fhir(self, plan: CarePlan) -> str:
        """Salva/atualiza no servidor FHIR, retorna ID FHIR"""

    async def sync_from_fhir(self, patient_id: str) -> list[CarePlan]:
        """Busca CarePlans do paciente no FHIR e importa"""
```

### 3.5 Estrategia de Sincronizacao

**Geralda e a fonte primaria** para planos de cuidado:
1. Profissional cria plano na Geralda (via API ou Wanda)
2. Geralda persiste no PostgreSQL (EF-001)
3. Geralda sincroniza para o servidor FHIR (assíncrono)
4. Outros sistemas podem consultar o FHIR

**Importacao de CarePlans externos**:
1. Se ja existe CarePlan no FHIR criado por outro sistema
2. Geralda pode importar e assumir o acompanhamento
3. Manter referencia ao ID FHIR original

### 3.6 Coluna de Mapeamento FHIR

Adicionar a `care_plans`:
```sql
ALTER TABLE care_plans ADD COLUMN fhir_id VARCHAR(128);
ALTER TABLE care_plans ADD COLUMN fhir_last_sync TIMESTAMPTZ;
ALTER TABLE care_tasks ADD COLUMN fhir_id VARCHAR(128);
ALTER TABLE reminders ADD COLUMN fhir_id VARCHAR(128);
```

## 4. Configuracao

```env
# FHIR Server
INTELLICARE_FHIR_SERVER_URL=http://localhost:8080/fhir
INTELLICARE_FHIR_TIMEOUT=30
INTELLICARE_FHIR_SYNC_ENABLED=true
INTELLICARE_FHIR_SYNC_MODE=async  # async ou sync
```

## 5. Endpoints Novos

| Metodo | Path | Descricao |
|--------|------|-----------|
| POST | `/api/v1/plans/{plan_id}/sync-fhir` | Forca sincronizacao de um plano para FHIR |
| POST | `/api/v1/patients/{patient_id}/import-fhir` | Importa CarePlans do FHIR para um paciente |
| GET | `/api/v1/patients/{patient_id}/summary` | Retorna IPS simplificado do paciente |

## 6. Testes

### 6.1 Testes Unitarios
- Conversao CarePlan Geralda -> FHIR (5+ testes)
- Conversao FHIR -> CarePlan Geralda (5+ testes)
- Conversao Task/Reminder (5+ testes)
- Edge cases: campos opcionais, ICD-10 invalido

### 6.2 Testes de Integracao (com FHIR mock)
- Criar CarePlan no FHIR via adapter
- Buscar CarePlans do paciente
- Sincronizar plano modificado
- Importar plano externo
- Minimo 10 testes

### 6.3 Mock do Servidor FHIR
- Usar `respx` para mockar HTTP ao FHIR server
- Fixtures com recursos FHIR R4 validos

## 7. Criterios de Aceitacao

- [ ] Adapter bidirecional CarePlan (interno <-> FHIR R4)
- [ ] Adapter bidirecional Task (interno <-> FHIR Task)
- [ ] Adapter CommunicationRequest para Reminders
- [ ] Sincronizacao assincrona ao criar/atualizar planos
- [ ] Importacao de CarePlans FHIR existentes
- [ ] IPS Summary endpoint funcional
- [ ] 20+ testes novos (unitarios + integracao)
- [ ] Documentacao dos mapeamentos FHIR
- [ ] Cobertura >= 90%

## 8. Riscos e Mitigacoes

| Risco | Mitigacao |
|-------|-----------|
| FHIR server indisponivel | Sync assincrono com retry; funciona offline |
| Mapeamento incompleto | Testes de roundtrip (Geralda -> FHIR -> Geralda) |
| CarePlan externo com formato inesperado | Validacao robusta + log de warnings |
| Conflito de atualizacao | Geralda como fonte primaria; FHIR e espelho |

## 9. Estimativa de Complexidade

- **Arquivos novos**: ~8
- **Arquivos modificados**: ~4 (config, models, docker)
- **Linhas estimadas**: ~1.200
- **Testes novos**: ~20
