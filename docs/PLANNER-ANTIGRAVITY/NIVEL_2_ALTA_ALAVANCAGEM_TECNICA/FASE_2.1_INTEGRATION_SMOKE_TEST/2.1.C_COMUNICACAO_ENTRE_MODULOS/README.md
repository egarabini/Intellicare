# 2.1.C - Comunicação Entre Módulos

**Data de início:** 2026-02-24
**Responsável:** DEV2
**Status:** ✅ EXECUTADO E REGISTRADO

## Objetivo

Executar testes de integração entre módulos após stack ficar 100% saudável.

## Evidências

- `20260224-1431_EXECUCAO_COMUNICACAO.json`
- `20260224-1434_CHECKS_COMPLEMENTARES.json`
- `20260224-1435_EXECUCAO_2.1.C.md`
- `RESUMO_2.1.C.md`

## Resultado

- Critério de aceite "3 fluxos cross-módulo" atendido via WANDA:
  - WANDA -> Oswaldo (`modules_used=["intellicare-oswaldo"]`)
  - WANDA -> Florence (`modules_used=["intellicare-florence"]`)
  - WANDA -> Zilda (`modules_used=["intellicare-zilda"]`)
- Portal respondeu HTTP 200 em `http://localhost:3001`.
- Stack permaneceu estável sem crashloop (containers com uptime > 40 min).

## Pendências técnicas identificadas

- WANDA não possui endpoint `/api/v1/fhir-proxy` (retorno 404).
- Fluxo Geralda -> Grahame (sincronização CarePlan) ainda não implementado.
- Donabedian responde `/api/v1/health` com 200, porém `/api/v1/info` com 500, ficando `offline` no discovery da WANDA.
