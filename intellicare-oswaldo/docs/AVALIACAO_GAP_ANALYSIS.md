# Oswaldo — Gap Analysis (2026-02-16)

> Avaliacao do que esta implementado vs. especificado na v1.0.0 — base para a evolucao v2.0.

## Resumo Executivo

A Oswaldo v1.0.0 (98 testes, ~79% cobertura) entregou um **core engine de alta qualidade**: estadiamento clinico correto para CKD/DM2/HAS com algoritmos KDIGO, ADA e ESC/ESH, sistema de alertas (threshold + trend), persistencia FHIR via PostgreSQL, e 6 dos 7 endpoints REST especificados.

**Maturidade geral: 7.5/10** — motor robusto, mas ~60% das funcionalidades de negocio nao implementadas.

---

## Componentes Implementados (Core Solido)

| Componente | Maturidade | Notas |
|-----------|-----------|-------|
| ChronicDiseaseEngine | 9/10 | Orquestrador completo e bem testado |
| Estadiamento CKD (KDIGO) | 9/10 | G1-G5 + A1-A3, combinacao de eixos |
| Estadiamento DM2 (ADA) | 9/10 | HbA1c: CONTROLLED/SUBOPTIMAL/POOR/VERY_POOR |
| Estadiamento HAS (ESC/ESH) | 9/10 | 7 categorias de pressao arterial |
| ThresholdAlertRule | 9/10 | Alertas por valor absoluto |
| TrendAlertRule | 9/10 | Alertas por velocidade de progressao |
| Perfis YAML (ckd, dm2, has) | 9/10 | 3 doencas, 24+ observacoes, 38+ alertas |
| DiseaseProfileRegistry | 9/10 | Carregamento dinamico, factory extensivel |
| FHIRDataStore (PostgreSQL) | 8/10 | UPSERT, busca por tipo/paciente/codigo |
| API REST (6 endpoints) | 8/10 | health, info, diseases, staging, alerts, analyze |

---

## Gaps Criticos (0% implementados)

| Gap | Impacto | Justificativa |
|-----|---------|---------------|
| Subagente + `/api/v1/analyze` (contrato Wanda) | **BLOQUEADOR** | Wanda nao consegue usar o Oswaldo sem este endpoint no padrao correto |
| MedicationAdvisor | Alto | Flag `enable_medication_advisor` existe, sem implementacao |
| CV Risk Calculator | Alto | Flag `enable_cv_risk_calculator` existe, sem implementacao |
| Publicacao de alertas (Redis Stream) | Alto | Alertas sao gerados mas nao propagados ao ecossistema |
| Integracao Florence | Medio | Sem acesso a RAG clinico ou resultados de exames |
| Integracao Zilda | Medio | Sem verificacao de disponibilidade de servicos (dialise, etc.) |
| Dashboard Streamlit | Baixo | Especificado, nao implementado |

---

## Gaps Parciais (implementados de forma incompleta)

| Gap | Status | Detalhe |
|-----|--------|---------|
| Confidence score | Campo existe, nunca preenchido | `StagingResult.confidence_score` sempre None |
| Historico de estadiamento | Calculado, nao persistido | Cada chamada recalcula — sem timeline |
| Endpoint `/api/v1/trends/{patient_id}/{biomarker}` | Ausente | Tendencias disponiveis so via `/analyze` |
| Recomendacoes clinicas | Parcial | Alertas tem `message` mas sem estrutura formal |
| Logs auditaveis | Logging basico | Sem audit trail estruturado |

---

## Inventario de Testes

| Arquivo | Testes | Componente | Status |
|---------|--------|-----------|--------|
| test_staging_ckd.py | ~15 | KDIGO staging | ✅ Completo |
| test_staging_dm2.py | ~15 | ADA staging | ✅ Completo |
| test_staging_has.py | ~15 | ESC/ESH staging | ✅ Completo |
| test_alerts.py | ~20 | Threshold + Trend alerts | ✅ Completo |
| test_core_logic.py | 23 | ChronicDiseaseEngine | ✅ Completo |
| test_profiles.py | 17 | Loader, Registry, Schema | ✅ Completo |
| test_datastore.py | 11 | FHIRDataStore | ✅ Bom |
| test_api.py | 8 | Endpoints FastAPI | ✅ Basico |
| test_models.py | 8 | Dataclasses | ✅ Completo |
| test_day4-7_*.py | ~420 | Legacy v0.6 (src/) | ⚠️ Legacy |

**Total v1.0 core:** ~132 testes funcionais no codigo principal
**Total incluindo legacy:** ~521 testes

---

## Mapa de Gaps para Especificacoes v2.0

### Fase 1 — Completar Base (pre-requisito para integracao)
| EF | Titulo |
|----|--------|
| EF-O001 | Historico de Estadiamento e Endpoint de Tendencias |
| EF-O002 | Confidence Score e Recomendacoes Clinicas Estruturadas |
| EF-O003 | Subagente Oswaldo + Contrato Wanda (`/api/v1/analyze`) |

### Fase 2 — Algoritmos Clinicos Avancados
| EF | Titulo |
|----|--------|
| EF-O004 | Conselheiro de Medicamentos (MedicationAdvisor) |
| EF-O005 | Calculadora de Risco Cardiovascular (Framingham + CKD-EPI) |
| EF-O006 | Extensao de Doencas (DPOC, ICC, Dislipidemia) |

### Fase 3 — Integracao e Orquestracao
| EF | Titulo |
|----|--------|
| EF-O007 | Integracao Florence (exames, RAG clinico) |
| EF-O008 | Integracao Zilda (disponibilidade de servicos por territorio) |
| EF-O009 | Publicacao de Eventos (Redis Stream — alertas ao ecossistema) |

---

## Compatibilidade

Os **98 testes v1.0** (core `oswaldo/`) devem continuar passando em todas as fases.
Os **9 endpoints existentes** nao devem quebrar.
O diretorio `src/` (legacy) e mantido como referencia mas nao e alvo desta evolucao.
