# 📋 W4-A — Especificação: React Components Clínicos

## 1. Objetivo
Adaptar e integrar componentes React do Medplum (118 disponíveis) ao portal IntelliCare, priorizando os 15 mais impactantes para produtividade clínica.

## 2. Componentes Prioritários (v1)

| # | Componente | Uso no IntelliCare | Origem Medplum |
|---|---|---|---|
| 1 | **PatientSummary** | Visão consolidada do paciente | `PatientSummary/` |
| 2 | **PatientTimeline** | Timeline de eventos clínicos | `PatientTimeline/` |
| 3 | **ResourceForm** | Formulários FHIR genéricos | `ResourceForm/` |
| 4 | **ResourceTable** | Listagem de recursos com busca | `ResourceTable/` |
| 5 | **QuestionnaireForm** | Formulários dinâmicos (SDC) | `QuestionnaireForm/` |
| 6 | **QuestionnaireBuilder** | Editor visual de formulários | `QuestionnaireBuilder/` |
| 7 | **DiagnosticReportDisplay** | Exibição de laudos | `DiagnosticReportDisplay/` |
| 8 | **Scheduler** | Agendamento de consultas | `Scheduler/` |
| 9 | **SearchControl** | Busca FHIR com filtros | `SearchControl/` |
| 10 | **CodeableConceptInput** | Input de códigos (CID, LOINC) | `CodeableConceptInput/` |
| 11 | **MedicationRequest** | Prescrição médica | Via ResourceForm |
| 12 | **EncounterTimeline** | Timeline do encontro | `EncounterTimeline/` |
| 13 | **Chat** | Comunicação intra-equipe | `chat/` |
| 14 | **ResourceDiff** | Comparação de versões | `ResourceDiff/` |
| 15 | **StatusBadge** | Status visual de recursos | `StatusBadge/` |

## 3. Estratégia de Adaptação
- **Não copiar código TypeScript** — reimplementar em React + nossa design system
- **Usar como referência de UX/funcionalidade** — copiar o comportamento, não o código
- **Conectar ao IntelliCare API** (não ao MedplumClient)
- **Respeitar design system existente** do portal

## 4. Plano: 14 dias (Dev 1 + Dev 2 + Dev 3)
- Dia 1-3: PatientSummary + PatientTimeline
- Dia 4-6: ResourceForm + ResourceTable + SearchControl
- Dia 7-9: QuestionnaireForm + QuestionnaireBuilder
- Dia 10-12: DiagnosticReportDisplay + Scheduler + CodeableConceptInput
- Dia 13-14: Chat + StatusBadge + integração final

---

# 📋 W4-B — Especificação: SMART-on-FHIR Launch

## 1. Objetivo
Implementar o protocolo SMART-on-FHIR App Launch Framework, permitindo que aplicações de terceiros se autentiquem e acessem dados FHIR do IntelliCare de forma padronizada.

## 2. Funcionalidades
- **EHR Launch:** App é lançado de dentro do IntelliCare (contexto do paciente/encontro)
- **Standalone Launch:** App acessa IntelliCare externamente (seleção de paciente)
- **Scopes FHIR:** `patient/*.read`, `user/Observation.write`, etc.
- **Token exchange:** OAuth2 com extensões SMART
- **Well-known endpoint:** `/.well-known/smart-configuration`
- **FHIR Capability Statement:** Referência a SMART security extensions

## 3. Integração com Keycloak
- Keycloak como Authorization Server
- Custom mapper para SMART scopes
- Launch context (patient, encounter) no token

## 4. Plano: 10 dias (Dev 4)
- Dia 1-3: Well-known + Capability Statement
- Dia 4-6: EHR Launch flow (com Keycloak)
- Dia 7-8: Standalone Launch
- Dia 9-10: Testes com SMART Health IT test suite
