# NORMAS_E_PADROES

Regras e padrões que todo desenvolvedor do IntelliCare deve conhecer e seguir.

## Documentos

| Arquivo | Conteúdo |
|---|---|
| [20260221-0714_PADRAO_NOMENCLATURA_DOCUMENTOS.md](./20260221-0714_PADRAO_NOMENCLATURA_DOCUMENTOS.md) | Padrão de nomenclatura `YYYYMMDD-HHMM_TITULO.md` |
| [20260307-1703_FLUXO_GIT_E_DEPLOY.md](./20260307-1703_FLUXO_GIT_E_DEPLOY.md) | Fluxo completo: feature branch → PR → staging → deploy |
| [20260307-1703_TEMPLATE_ANDAMENTO_DEMANDA.md](./20260307-1703_TEMPLATE_ANDAMENTO_DEMANDA.md) | Template oficial do registro de andamento por demanda |
| [20260308-1800_NORMA_ESPECIFICACAO_DEMANDAS.md](./20260308-1800_NORMA_ESPECIFICACAO_DEMANDAS.md) | 🔴 **OBRIGATÓRIO** — 3 docs de spec por demanda antes do dev começar |
| [20260308-1900_NORMA_AMBIENTE_DESENVOLVIMENTO_LOCAL.md](./20260308-1900_NORMA_AMBIENTE_DESENVOLVIMENTO_LOCAL.md) | 🔴 **OBRIGATÓRIO** — todo dev trabalha localmente; staging só recebe código via PR |

## Resumo das regras principais

**Git:** todo trabalho em feature branch — nunca em `staging` ou `main` direto. Branch criada por Claude antes de repassar ao dev. Nomenclatura: `feat/modulo-descricao`, `fix/modulo-descricao`, `infra/descricao`. Commit: `tipo(modulo): descrição em imperativo, minúsculas`.

**Deploy:** nenhum dev altera arquivo diretamente no servidor. Deploy via GitHub Actions após merge em `staging`. Smoke test obrigatório.

**Documentação:** todo arquivo segue `YYYYMMDD-HHMM_TITULO.md`. Toda demanda gera um `ANDAMENTO_DEMANDA` em `06_ANDAMENTO/DEMANDAS/`. Dev preenche o log step a step.

**Especificação de demandas (🔴 obrigatório):** toda demanda deve ter 3 documentos criados por Claude + Eduardo **antes** de ir para o dev: `01_ESPECIFICACAO_FUNCIONAL.md`, `02_ESPECIFICACAO_TECNICA.md` e `03_PLANO_IMPLEMENTACAO.md` — salvos na pasta da própria demanda em `06_ANDAMENTO/DEMANDAS/`. Dev não começa sem os três.

**Ambiente de desenvolvimento (🔴 obrigatório):** todo desenvolvedor trabalha localmente via Docker. Staging não é ambiente de dev — recebe código apenas via PR mergeado. Setup: `cp .env.example .env` → `docker compose -f docker-compose.full.yml up -d` → `bash scripts/smoke_test.sh`.

## Links relacionados

- [Governança geral](../GOVERNANCA/20260307-1703_GOVERNANCA_DESENVOLVIMENTO.md)
- [Índice de demandas](../RELATORIOS_E_ANDAMENTO/DEMANDAS/README.md)
- [CODEOWNERS](../../.github/CODEOWNERS)
