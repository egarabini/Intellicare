# DEMANDAS — Índice de Andamento

Cada arquivo neste diretório representa uma demanda de desenvolvimento,
do momento da especificação até o deploy em staging.

## Fluxo resumido

```
Eduardo + Claude definem escopo
    → Claude cria branch + ANDAMENTO_DEMANDA
    → Dev trabalha e preenche log
    → Dev avisa Eduardo ao concluir
    → Claude + Eduardo revisam
    → Claude cria PR → Eduardo aprova
    → GitHub Actions deploya em staging
```

## Nomenclatura dos arquivos

```
YYYYMMDD-HHMM_DEM-NNN_MODULO_DESCRICAO.md
```

## Status possíveis

| Status | Significado |
|---|---|
| `BACKLOG` | Aguardando início |
| `EM_DEV` | Dev trabalhando |
| `EM_REVISAO` | Dev concluiu, aguardando Claude+Eduardo |
| `APROVADO` | Revisado, aguardando PR/deploy |
| `DEPLOYED` | Em staging |
| `BLOQUEADO` | Impedimento — ver log |
| `CANCELADO` | Cancelado — ver motivo |

## Template

`docs/NORMAS_E_PADROES/20260307-1703_TEMPLATE_ANDAMENTO_DEMANDA.md`

---

## Índice de demandas

| ID | Módulo | Descrição | Status | Dev | Data |
|---|---|---|---|---|---|
| [DEM-001](./20260307-1703_DEM-001_INFRA_FIX_SUBDOMINIOS.md) | portal · traefik | Fix subdomínios de produção | `EM_REVISAO` | @infra | 2026-03-07 |
