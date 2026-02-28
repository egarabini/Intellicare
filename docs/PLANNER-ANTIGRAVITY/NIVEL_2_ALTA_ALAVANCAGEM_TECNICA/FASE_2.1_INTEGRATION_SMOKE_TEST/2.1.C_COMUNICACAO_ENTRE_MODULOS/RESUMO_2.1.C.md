# RESUMO - 2.1.C Comunicação Entre Módulos

**Data:** 2026-02-24  
**Status:** ✅ EXECUTADA

## Resultado objetivo

- Fluxos cross-módulo validados com sucesso (mínimo exigido >= 3):
  - WANDA -> Oswaldo
  - WANDA -> Florence
  - WANDA -> Zilda

## Evidências

- `20260224-1431_EXECUCAO_COMUNICACAO.json`
- `20260224-1434_CHECKS_COMPLEMENTARES.json`
- `20260224-1435_EXECUCAO_2.1.C.md`

## Ajustes aplicados para viabilizar a fase

- Correção de URLs internas da WANDA no `docker-compose.full.yml` para uso de portas internas Docker (`:8000`).
- Recriação do container `wanda` para aplicar variáveis atualizadas.

## Riscos/pontos pendentes

1. `donabedian` aparece offline no discovery da WANDA porque `/api/v1/info` retorna 500.
2. Endpoint `WANDA /api/v1/fhir-proxy` não existe (404), apesar de constar no roadmap.
3. Fluxo `Geralda -> Grahame` (sync de CarePlan) ainda não está implementado no módulo Geralda atual.

## Critério de aceite da fase

- [x] `smoke_tests.py` com stack saudável (16/16 já validado em 2.1.B)
- [x] Pelo menos 3 fluxos cross-módulo funcionando
- [x] Sem containers em crashloop após janela de observação
