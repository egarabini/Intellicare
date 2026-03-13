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

## Propósito

Módulo de inteligência clínica: analisa prontuários, detecta inconsistências, gera score de qualidade e exporta dados em formato FHIR R4 interoperável. Na V3, substitui chamadas a LLMs externas por SLM local (OLLAMA) e integra pgvector para busca semântica do histórico clínico.

---

## O que entrega (V2 — a preservar)

- Análise de prontuários estruturados via LLM (V3: SLM local)
- Exportação FHIR R4: Patient, Observation, Condition, MedicationStatement
- Score de qualidade de dados clínicos por prontuário
- Detecção de inconsistências e dados faltantes

---

## Recursos FHIR R4 em uso

| Recurso | Uso |
|---------|-----|
| `Patient` | Dados demográficos do paciente |
| `Encounter` | Consultas e internações |
| `Observation` | Sinais vitais, resultados laboratoriais |
| `Condition` | Diagnósticos e problemas ativos |
| `MedicationStatement` | Medicamentos em uso |
| `Procedure` | Procedimentos realizados |
| `DiagnosticReport` | Laudos e relatórios |

Ver [[references/fhir-r4-recursos-usados]] para lista completa.

---

## Estratégia de incorporação em V3

1. Preservar lógica de análise e exports FHIR do V2
2. Adaptar para `TenantAwareSessionFactory` do intellicare-core
3. Substituir chamadas LLM externas por SLM local (OLLAMA)
4. Integrar com pgvector para busca semântica de histórico clínico do paciente

---

## Roles Autorizados (planejado)

- **`CLINICO`** — análise de prontuários e exportação FHIR
- **`TENANT_GESTOR`** — relatórios de qualidade e exports em lote

---

## Stack e Dependências

- FastAPI (APIRouter com prefix `/oswaldo`)
- FHIR R4 serialization (intellicare-core/fhir/)
- SLM local OLLAMA (DEM-010)
- pgvector para busca semântica de histórico
- [[decisoes/ADR-003-rag-slm-pgvector]]
- intellicare-core (DEM-003)

---

## DEMs relacionadas

- **DEM-013**: Cuidado backend (dados clínicos que Oswaldo analisa)
- **DEM-009**: Pipeline RAG (busca semântica de histórico)
- **DEM-010**: SLM OLLAMA (análise via modelo local)
