# Roteiro de Homologacao - DEM-017

## Estado atual

Os scripts tecnicos de seed/reset, documentos RAG e usuarios demo de Keycloak foram implementados e validados em terminal.

## Ciclos que dependem do Portal (DEM-016)

Os ciclos abaixo ficam aguardando o DEM-016 no `main`, porque exigem navegacao via browser e integracao visual com o Portal:

1. Ciclo 1 - Onboarding de Tenant pelo Portal/AdminUI
2. Ciclo 2 - Uso clinico completo via GestorUI + ClinicoUI
3. Ciclo 3 - Programas de Saude via GestorUI/ClinicoUI
4. Ciclo 4 - Billing e inadimplencia com navegacao completa
5. Ciclo 5 - Isolamento multi-tenant em interfaces autenticadas
6. Ciclo 6 - Tenant suspenso com bloqueio observado no Portal

## Preparacao tecnica concluida

- `tools/scripts/reset_demo.py`
- `tools/scripts/seed_demo.py`
- documentos seed em `tools/data/docs/seed/`
- extensao de `tools/scripts/setup_keycloak.py` para usuarios demo

## Quando o DEM-016 estiver no main

1. Executar `python tools/scripts/reset_demo.py`
2. Executar `python tools/scripts/seed_demo.py`
3. Abrir o Portal e percorrer os Ciclos 1-6
4. Registrar evidencias finais em `03_IMPLEMENTACAO.md`
