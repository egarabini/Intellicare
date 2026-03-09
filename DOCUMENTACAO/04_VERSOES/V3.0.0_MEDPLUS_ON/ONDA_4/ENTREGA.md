# 📦 ONDA_4 — Relatório de Entrega

**Data:** 2026-02-22
**Status:** ✅ CONCLUÍDA — W4-A (React Clinical Components) + W4-B (SMART-on-FHIR App Launch)

---

## W4-A: React Clinical Components

### Objetivo
Implementar uma biblioteca de 15 componentes React clínicos reutilizáveis para o Portal IntelliCare, com tipagem FHIR R4 completa, dark theme consistente (`bg-slate-900`) e cobertura de testes Vitest + jsdom.

### Arquivos Criados

#### `intellicare-portal/frontend/src/components/fhir/`

| Arquivo | Componente | Descrição |
|---------|------------|-----------|
| `types.ts` | — | Interfaces FHIR R4 + utility functions |
| `StatusBadge.tsx` | `<StatusBadge>` | Chip colorido por status (active/final/finished/etc.) |
| `PatientSummary.tsx` | `<PatientSummary>` | Card demográfico: nome, gênero, nascimento, CPF/CNS, contatos |
| `PatientTimeline.tsx` | `<PatientTimeline>` | Linha do tempo clínica de recursos heterogêneos |
| `ResourceTable.tsx` | `<ResourceTable>` | Tabela genérica paginada com busca client-side |
| `SearchControl.tsx` | `<SearchControl>` | Barra de busca FHIR com filtros e chips ativos |
| `DiagnosticReportDisplay.tsx` | `<DiagnosticReportDisplay>` | Card de relatório de exame com resultados e faixas de referência |
| `CodeableConceptInput.tsx` | `<CodeableConceptInput>` | Autocomplete para CID-10/LOINC/SNOMED com debounce |
| `ObservationChart.tsx` | `<ObservationChart>` | Recharts LineChart para séries temporais de observações |
| `MedicationCard.tsx` | `<MedicationCard>` | Card de MedicationRequest com posologia e frequência |
| `ProblemList.tsx` | `<ProblemList>` | Lista de condições ativas com severidade e status |
| `AllergyList.tsx` | `<AllergyList>` | Lista de alergias com criticalidade e reações |
| `VitalSignsGrid.tsx` | `<VitalSignsGrid>` | Grid de sinais vitais com detecção de fora-de-faixa (LOINC) |
| `EncounterCard.tsx` | `<EncounterCard>` | Card de encontro com tipo, classe, período, profissional |
| `ResourceDiff.tsx` | `<ResourceDiff>` | Comparador de versões FHIR (diff recursivo colorido) |
| `QuestionnaireForm.tsx` | `<QuestionnaireForm>` | Renderer de FHIR Questionnaire com coleta de respostas |
| `index.ts` | — | Barrel exports de todos os 15 componentes + tipos |

#### `intellicare-portal/frontend/vite.config.ts` (modificado)

Adicionado ambiente jsdom para testes de componentes React:

```typescript
/// <reference types="vitest" />
test: {
  environment: 'jsdom',
  globals: true,
  setupFiles: ['./src/test/setup.ts'],
},
```

#### `intellicare-portal/frontend/src/__tests__/fhir/components.test.tsx`

29 novos testes cobrindo:
- Utility functions: `codingDisplay`, `patientName`, `ageFromBirthDate` (8 testes)
- Componentes renderizados: StatusBadge, PatientSummary, PatientTimeline, ProblemList, AllergyList, EncounterCard, MedicationCard, DiagnosticReportDisplay, ResourceDiff (21 testes)

### Tipos FHIR R4 — `types.ts`

| Tipo | Recursos |
|------|----------|
| **Primitivos** | `Coding`, `CodeableConcept`, `Reference`, `Period`, `Quantity`, `HumanName`, `Address`, `ContactPoint`, `Meta` |
| **Resources** | `FHIRPatient`, `FHIRObservation`, `FHIRCondition`, `FHIREncounter`, `FHIRMedicationRequest`, `FHIRDiagnosticReport`, `FHIRAllergyIntolerance`, `FHIRQuestionnaire` |
| **Utils** | `codingDisplay()`, `fhirDate()`, `fhirDateTime()`, `patientName()`, `ageFromBirthDate()` |

### VitalSignsGrid — Códigos LOINC Cobertos

| LOINC | Sinal Vital | Faixa Normal |
|-------|-------------|--------------|
| 8867-4 | Frequência Cardíaca | 60–100 bpm |
| 9279-1 | Frequência Respiratória | 12–20 rpm |
| 8310-5 | Temperatura | 36.0–37.5 °C |
| 2708-6 | SpO₂ | ≥95% |
| 29463-7 | Peso | — |
| 8302-2 | Altura | — |
| 55284-4 | Pressão Arterial (componente) | < 130/80 |

### Testes

```
35 passed (29 novos + 6 pré-existentes)
0 failed
```

---

## W4-B: SMART-on-FHIR App Launch Framework

### Objetivo
Implementar o protocolo HL7 SMART App Launch 2.0 (STU2) no IntelliCare: discovery endpoint `/.well-known/smart-configuration`, EHR Launch, Standalone Launch, tradução de SMART scopes para regras de autorização, e CapabilityStatement com extensões de segurança SMART.

### Arquivos Criados

#### `intellicare-auth/intellicare_auth/smart/`

| Arquivo | Descrição |
|---------|-----------|
| `__init__.py` | Exports públicos do pacote smart |
| `models.py` | `SmartConfiguration`, `LaunchContext`, `SmartTokenClaims` |
| `scope_translator.py` | `parse_smart_scopes()` + `smart_scopes_to_rules()` |
| `launch_handler.py` | `EHRLaunchHandler`, `StandaloneLaunchHandler`, `_encode/_decode_launch_context()` |
| `router.py` | FastAPI router com 4 endpoints SMART |

#### `intellicare-grahame/grahame/api/routes/smart_routes.py`

Router Grahame com:
- `GET /api/v1/.well-known/smart-configuration`
- `GET /api/v1/metadata` → CapabilityStatement com extensões SMART de segurança

#### `intellicare-grahame/grahame/api/app.py` (modificado)

Registrado `smart_router` com prefix `/api/v1`.

#### `intellicare-auth/tests/smart/`

| Arquivo | Testes |
|---------|--------|
| `test_scope_translator.py` | 19 — parse_smart_scopes (9) + smart_scopes_to_rules (10) |
| `test_models_and_launch.py` | 19 — SmartConfiguration (3) + LaunchContext (4) + encode/decode (3) + EHRLaunchHandler (4) + StandaloneLaunchHandler (3) + SmartTokenClaims (2) |

### Modelos — `models.py`

**`SmartConfiguration`** — Discovery document SMART 2.0:
```python
SmartConfiguration(
    issuer: str,
    jwks_uri: str,
    authorization_endpoint: str,
    token_endpoint: str,
    scopes_supported: list[str],   # patient/*.read, openid, offline_access, fhirUser, ...
    capabilities: list[str],       # launch-ehr, launch-standalone, client-public, ...
    code_challenge_methods_supported: list[str],  # ["S256"]
)
```

**`LaunchContext`** — contexto de lançamento EHR:
```python
LaunchContext(
    launch_type: Literal["ehr", "standalone"],
    patient: Optional[str],       # "Patient/<id>"
    encounter: Optional[str],     # "Encounter/<id>"
    practitioner: Optional[str],
    intent: Optional[str],
    need_patient_banner: bool,
)
# Properties:
ctx.patient_id   # extrai "<id>" de "Patient/<id>"
ctx.encounter_id # extrai "<id>" de "Encounter/<id>"
```

**`SmartTokenClaims`** — claims do access token pós-autorização:
```python
SmartTokenClaims(sub, iss, exp, iat, scope, patient, encounter)
# Properties:
claims.scopes         # list[str] — split de scope
claims.launch_context # LaunchContext reconstruído dos claims
```

### Launch Handlers — `launch_handler.py`

**`EHRLaunchHandler`** (lançamento iniciado pelo EHR):

| Método | Descrição |
|--------|-----------|
| `generate_launch_token(ctx)` | Encoda LaunchContext em token base64url com TTL 5 min |
| `validate_launch_token(token)` | Decodifica e valida; retorna `None` se inválido/expirado |
| `build_authorize_url(client_id, redirect_uri, context, scope?, state?)` | URL de autorização OAuth2 com `?launch=<token>&iss=<fhir_base>` |

**`StandaloneLaunchHandler`** (app inicia sem contexto de paciente):

| Método | Descrição |
|--------|-----------|
| `build_authorize_url(client_id, redirect_uri, scope?, state?)` | URL com scope `launch/patient` para picker de paciente no Keycloak |

### Scope Translator — `scope_translator.py`

**Formato SMART:** `{context}/{resource}.{permission}` onde:
- `context`: `patient` | `user` | `system`
- `resource`: tipo FHIR ou `*` (wildcard)
- `permission`: `read` | `write` | `*`

**Tradução para ResourceRule:**

| SMART Permission | FHIR Interactions |
|-----------------|-------------------|
| `read` | `search`, `read`, `vread`, `history` |
| `write` | `create`, `update`, `delete` |
| `*` | Todas as 7 interações |

Wildcard de recurso (`*`) expande para `allowed_resource_types` fornecidos, ou sentinela `"*"` se omitido.

### Endpoints SMART — `router.py`

| Método | Path | Função |
|--------|------|--------|
| `GET` | `/.well-known/smart-configuration` | Discovery document SMART 2.0 |
| `POST` | `/smart/launch/ehr` | Gera authorize_url + launch_token para EHR Launch |
| `GET` | `/smart/launch/validate/{token}` | Valida e decodifica launch token |
| `POST` | `/smart/launch/standalone` | Gera authorize_url para Standalone Launch |

### CapabilityStatement — Extensões SMART de Segurança

```json
{
  "rest": [{
    "security": {
      "cors": true,
      "extension": [{
        "url": "http://fhir-registry.smarthealthit.org/StructureDefinition/oauth-uris",
        "extension": [
          { "url": "authorize",  "valueUri": "<keycloak>/auth" },
          { "url": "token",      "valueUri": "<keycloak>/token" },
          { "url": "introspect", "valueUri": "<keycloak>/introspect" },
          { "url": "jwks",       "valueUri": "<keycloak>/certs" }
        ]
      }]
    }
  }]
}
```

Cobre 12 resource types, 3 operações customizadas (`$everything`, `$summary`, `$validate`).

### Testes

```
38 passed (19 + 19)
0 failed
```

---

## Resumo de Testes ONDA_4

| Workstream | Arquivo de Testes | Testes |
|------------|-------------------|--------|
| W4-A Portal | `src/__tests__/fhir/components.test.tsx` | 35 (29 novos) |
| W4-B SMART | `tests/smart/test_scope_translator.py` | 19 |
| W4-B SMART | `tests/smart/test_models_and_launch.py` | 19 |
| **Total ONDA_4** | | **73 testes** |

---

## Acúmulo MEDPLUS_ON

| ONDA | Workstreams | Testes adicionados |
|------|-------------|--------------------|
| ONDA_1 | W1-A (IPS Generator) + W1-B (Policy Engine) | 91 |
| ONDA_2 | W2-A (Audit Trail) + W2-B (FHIR Questionnaire Engine) | 105 |
| ONDA_3 | W3-A (FHIR-Native Storage) + W3-B (FHIR Search Engine) | 87 |
| ONDA_4 | W4-A (React Components) + W4-B (SMART-on-FHIR) | 73 |
| **Total** | **8 workstreams** | **~356 testes** |

---

## Próxima ONDA

**ONDA_5** — opções candidatas:
- **W5-A**: CDS Hooks (Clinical Decision Support) — implementar servidor CDS Hooks 2.0 em Grahame, consumido por WANDA
- **W5-B**: FHIR Bulk Data ($export) — exportação assíncrona NDJSON para analytics/ETL com Kestra
- **W5-C**: Terminology Service ($lookup, $validate-code, $expand, $translate) — coberto parcialmente pelo intellicare-conhecimento
