# 2.1.B - Subir e Validar (Smoke)

**Data de início:** 2026-02-24
**Responsável:** DEV2
**Status:** ✅ CONCLUÍDO (16/16 saudáveis no smoke)

## Objetivo

Executar smoke test no stack completo e consolidar serviços saudáveis vs pendentes.

## Execuções relevantes

- `docker compose --env-file .env.full -f docker-compose.full.yml up -d`
- `python scripts/smoke_tests.py --json .../20260224-1225_SMOKE_REPORT.json`
- `python scripts/smoke_tests.py --json .../20260224-1313_SMOKE_REPORT.json`
- `python scripts/smoke_tests.py --json .../20260224-1331_SMOKE_REPORT.json`

## Resultado atual

- **16/16 serviços saudáveis (100%)** no smoke de `2026-02-24 13:31`.
- Backends saudáveis: `florence`, `oswaldo`, `donabedian`, `wanda`, `comunicacao`, `geralda`, `zilda`, `ocr`, `pierre`, `admin`, `gestor`, `grahame`, `nise`.
- Frontend saudável: `portal`.
- Infra saudável: `postgres`, `redis`.

## Pendências

- Não há pendência de subida/smoke para 2.1.B.
- Próxima etapa da fase: `2.1.C_COMUNICACAO_ENTRE_MODULOS`.

## Artefatos

- `20260224-1225_EXECUCAO_SMOKE.md`
- `20260224-1225_SMOKE_REPORT.json`
- `20260224-1313_SMOKE_REPORT.json`
- `20260224-1331_SMOKE_REPORT.json`
- `20260224-1331_FECHAMENTO_16_DE_16.md`
- `RESUMO_2.1.B.md`
