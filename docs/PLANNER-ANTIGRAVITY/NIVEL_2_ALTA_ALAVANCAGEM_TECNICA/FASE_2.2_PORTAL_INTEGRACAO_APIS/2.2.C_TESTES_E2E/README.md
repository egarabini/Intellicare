# 2.2.C - Testes E2E Minimos

**Data de inicio:** 2026-02-24  
**Responsavel:** DEV2  
**Status:** ✅ EXECUTADO E REGISTRADO

## Objetivo

Executar e registrar uma suite E2E minima para validar fluxos criticos do portal com APIs mockadas.

## Suite executada

Arquivo de testes:

- `intellicare-portal/frontend/tests/e2e/portal-workflows.e2e.test.tsx`

Cenarios cobertos (5):

1. Login white-label dispara autenticacao.
2. Dashboard carrega dados reais mockados.
3. Busca de paciente no Grahame abre recurso no visualizador.
4. Plano de cuidado da Geralda atualiza status visual da tarefa.
5. Busca CNES na Zilda retorna estabelecimento e contexto territorial.

## Evidencias

- `20260224-1549_E2E_REPORT.json`
- `20260224-1550_EXECUCAO_2.2.C.md`
- `RESUMO_2.2.C.md`

## Observacao tecnica

- A execucao foi feita com Vitest em `jsdom` e mock de `fetch`.
- Tentativa de instalar `msw` falhou no ambiente atual por indisponibilidade de cache npm (`ENOTCACHED`).
- A migracao para Playwright+Cypress/MSW permanece como melhoria para hardening.
