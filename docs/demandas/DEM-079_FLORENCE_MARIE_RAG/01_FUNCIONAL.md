---
tipo: especificacao-funcional
demanda: DEM-079
titulo: Florence via Marie RAG
sprint: 2026-05-09
status: em-execucao
dev: CODEX
criado: 2026-03-22
depende_de: [DEM-075, DEM-071]
tags: [marie, florence, rag, ia, soap]
adr: docs/adr/ADR-002-marie-dify-orchestrator.md
---

# DEM-079 — Florence via Marie RAG

## Objetivo

Migrar a geração de nota SOAP do Florence para o pipeline Marie RAG, enriquecendo as sugestões com o histórico longitudinal do paciente (DEM-071). Com `MARIE_ENABLED=true`, Florence passa a gerar SOAP contextualizado — levando em conta diagnósticos anteriores, medicamentos em uso e padrão de consultas do paciente.

Esta DEM também ativa `MARIE_ENABLED=true` no staging pela primeira vez, validando o stack Dify com carga real.

---

## Personas

**Clínico (Florence):** ao clicar "Sugerir SOAP via IA", se `MARIE_ENABLED=true`, recebe uma sugestão que considera:
- Últimas 5 consultas do paciente
- Diagnósticos CID anteriores
- Medicamentos prescritos ativos
- Notas SOAP anteriores (campos S e O)

A experiência de UI é idêntica ao SOAP atual — o clínico não percebe a diferença no fluxo, mas a qualidade da sugestão é superior.

**Gestor de Plataforma:** ativa `MARIE_ENABLED=true` no `.env` para habilitar o RAG em Florence e Oswaldo simultaneamente.

---

## Critérios de aceite

1. `MARIE_ENABLED=false` — comportamento idêntico ao sprint anterior (zero regressão)
2. `MARIE_ENABLED=true` — `POST /florence/notes/suggest` chama workflow `florence_soap_rag` no Dify
3. Payload enviado ao Marie inclui: `chief_complaint`, `patient_history` (resumo da timeline últimos 180 dias)
4. Se Marie indisponível (timeout/5xx), fallback para LLM local transparente
5. 4+ testes com mock Dify — passando
6. Staging com `MARIE_ENABLED=true` — smoke do `/florence/notes/suggest` retorna SOAP com contexto histórico

---

## Fora de escopo

- Base de conhecimento externa no Dify (protocolos clínicos, CBHPM) — próximo sprint
- Florence FREE TEXT via Marie (apenas SOAP nesta DEM)
- Multi-tenant isolation no Dify (todos os tenants compartilham instância)
