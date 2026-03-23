---
tipo: especificacao-funcional
demanda: DEM-075
titulo: Marie Bootstrap
sprint: 2026-05-02
status: em-execucao
dev: CODEX
criado: 2026-03-22
depende_de: [DEM-073]
habilita: [DEM-069]
tags: [marie, dify, ia, orchestration, rag]
adr: docs/adr/ADR-002-marie-dify-orchestrator.md
---

# DEM-075 — Marie Bootstrap

## Objetivo

Realizar o bootstrap do **Módulo Marie** como microsserviço parceiro baseado em Dify. Esta DEM não substitui o comportamento atual de Florence ou Oswaldo — ela **adiciona uma camada opcional** que pode ser ativada por feature flag (`MARIE_ENABLED`), permitindo zero downtime e rollback imediato.

O escopo desta DEM é restrito ao bootstrap: infraestrutura Dify UP, cliente Python integrado, e migração de **um único flow** como prova de conceito (`oswaldo_cid10`).

> Marie Curie: cria os instrumentos para medir o invisível. Processa históricos complexos e RAG antes de entregar resposta validada. Não substitui — **amplifica**.

---

## Personas

**Gestor de Plataforma:** ativa/desativa Marie via variável de ambiente `MARIE_ENABLED=true|false` no `.env`. Sem interface UI nesta DEM.

**Clínico (Oswaldo):** ao solicitar sugestão de CID-10, se `MARIE_ENABLED=true`, a sugestão passa pelo pipeline RAG do Marie antes de retornar. A experiência de UI é idêntica — o clínico não percebe a diferença, mas recebe contexto longitudinal do histórico do paciente.

**Dev/ARQUITETO:** valida que com `MARIE_ENABLED=false` (default), o comportamento é 100% idêntico ao estado anterior — nenhum impacto em testes existentes.

---

## O que Marie faz no `oswaldo_cid10` (prova de conceito)

Antes (sem Marie):
```
Clínico digita sintomas → Oswaldo LLM → sugestão CID-10
```

Depois (com `MARIE_ENABLED=true`):
```
Clínico digita sintomas → Oswaldo → marie_client.call_marie("cid10_rag", {sintomas, historico_timeline}) → Dify RAG pipeline → sugestão CID-10 contextualizada
```

O histórico da linha do tempo (DEM-071) é passado como contexto ao Marie — permitindo sugestões de CID levando em conta diagnósticos anteriores do paciente.

---

## Critérios de aceite

1. `docker compose up` sobe os containers Marie (Dify) sem erro
2. `MARIE_ENABLED=false` — todos os testes existentes passam sem alteração (zero regressão)
3. `MARIE_ENABLED=true` — `POST /oswaldo/suggest` com `cid10` chama Marie antes do LLM local
4. Se Marie retornar erro (timeout, 5xx), fallback automático para LLM local sem erro para o usuário
5. `marie_client.py` tem timeout configurável via `MARIE_TIMEOUT_SECONDS` (default: 10s)
6. Testes: `test_marie_client.py` com mock do Dify — 4+ testes passando

---

## Fora de escopo desta DEM

- Migração de `florence_soap` para Marie (próxima DEM)
- UI de configuração de workflows Marie no AdminUI
- RAG com documentos externos (DICOM, PDFs MinIO)
- Autenticação multi-tenant no Dify (todos os tenants compartilham a instância Marie neste sprint)
