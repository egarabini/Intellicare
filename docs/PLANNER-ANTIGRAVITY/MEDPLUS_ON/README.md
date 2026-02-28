# MEDPLUS_ON — Roadmap de Absorção Medplum

**Objetivo:** Absorver funcionalidades do Medplum no IntelliCare conforme análise de gap.

**Documento base:** [ANALISE_GAP_MEDPLUM.md](ANALISE_GAP_MEDPLUM.md)

---

## Visão Geral das Ondas

| Onda | Foco | Status |
|------|------|--------|
| ONDA_1 | FHIR Operations + Subscriptions | Concluída |
| ONDA_2 | Bots Engine + Access Policies | Concluída |
| ONDA_3 | FHIR Storage + Search | Concluída |
| ONDA_4 | React Components + SMART | Concluída |
| ONDA_5 | CDS Hooks + Terminology | Concluída |
| ONDA_6 | WAHA Webhook + Deploy | Concluída |
| ONDA_7 | Bulk Data + CDS Feedback | Concluída |
| **ONDA_8** | Interoperabilidade Brasileira + Performance | Em andamento |
| **ONDA_9** | UX e Flexibilidade | Implementada |
| **ONDA_10** | Framework de Extensibilidade | Implementada |
| **ONDA_11** | Refinamentos | Implementada |

---

## ONDA_8 — Interoperabilidade Brasileira + Performance

- **W8-A:** CCDA Parser/Import
- **W8-B:** HL7v2 Agent
- **W8-C:** Subscription Performance
- **W8-D:** Production Hardening

→ [ONDA_8/README.md](ONDA_8/README.md)

---

## ONDA_9 — UX e Flexibilidade

- **W9-A:** AI Operation + SSE (streaming)
- **W9-B:** $find + $book (agendamento)
- **W9-C:** On-behalf-of Header

→ [ONDA_9/README.md](ONDA_9/README.md)

---

## ONDA_10 — Framework de Extensibilidade

- **W10-A:** Custom Operations Framework
- **W10-B:** ConceptMap Import + $translate

→ [ONDA_10/README.md](ONDA_10/README.md)

---

## ONDA_11 — Refinamentos

- **W11-A:** WS Token Refresh
- **W11-B:** Terminology ($lookup, $validate-code)
- **W11-C:** Display language overrides (i18n)

→ [ONDA_11/README.md](ONDA_11/README.md)

---

## Ordem de Execução Recomendada

1. **ONDA_8** — Crítico para Brasil (CCDA, HL7v2) e produção
2. **ONDA_9** — UX (AI streaming, agendamento, delegação)
3. **ONDA_10** — Extensibilidade (custom ops, terminologia)
4. **ONDA_11** — Refinamentos (token refresh, i18n)

---

**Última atualização:** 2026-02-25
