---
tipo: nota-modulo
modulo: oswaldo
porto: 8002
fase: 3
sprint: "3.x"
status: existente-v2
score_v2: "8/10"
dem_principal: TBD
tags: [fase-3, oswaldo, fhir, analise-clinica]
---

# Módulo: oswaldo

**Responsabilidade:** Análise clínica + exportação FHIR R4.
Único módulo com score alto no V2 (8/10). Será incorporado na Fase 3.

---

## O que entrega (V2 — a preservar)

- Análise de prontuários estruturados via LLM
- Exportação FHIR R4: Patient, Observation, Condition, MedicationStatement
- Score de qualidade de dados clínicos por prontuário
- Detecção de inconsistências e dados faltantes

## Estratégia de incorporação em V3

1. Preservar lógica de análise e exports FHIR do V2
2. Adaptar para `TenantAwareSessionFactory` do intellicare-core
3. Substituir chamadas LLM externas por SLM local (OLLAMA)
4. Integrar com pgvector para busca semântica de histórico clínico do paciente

## Recursos FHIR R4 em uso

Ver [[references/fhir-r4-recursos-usados]] para lista completa.

Principais: `Patient`, `Encounter`, `Observation`, `Condition`,
`MedicationStatement`, `Procedure`, `DiagnosticReport`.

## Dependências

- [[decisoes/ADR-003-rag-slm-pgvector]] — para busca de histórico clínico
- intellicare-core/fhir/ (DEM-003)
- SLM local OLLAMA (DEM-002)
