# DEMANDAS — Índice de Andamento

Cada **pasta** neste diretório representa uma demanda de desenvolvimento,
do momento da especificação até o deploy em staging.

Cada pasta contém:
- `README.md` — ANDAMENTO_DEMANDA (metadados, log, status)
- `01_ESPECIFICACAO_FUNCIONAL.md` — o que é e por quê (demandas com dev ativo)
- `02_ESPECIFICACAO_TECNICA.md` — como construir, com código de referência
- `03_PLANO_IMPLEMENTACAO.md` — passo a passo de execução

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

## Nomenclatura das pastas

```
YYYYMMDD-HHMM_DEM-NNN_MODULO_DESCRICAO/
└── README.md
└── 01_ESPECIFICACAO_FUNCIONAL.md   (quando houver dev ativo)
└── 02_ESPECIFICACAO_TECNICA.md
└── 03_PLANO_IMPLEMENTACAO.md
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
| [DEM-001](./20260307-1703_DEM-001_INFRA_FIX_SUBDOMINIOS/README.md) | portal · traefik | Fix subdomínios de produção | `EM_REVISAO` | @infra | 2026-03-07 |
| [DEM-002](./20260308-1200_DEM-002_ADMIN_GESTOR_AUTH_FIX/README.md) | intellicare-admin · intellicare-gestor | Keycloak auth + React SPAs admin e gestor | `APROVADO` | dev1 | 2026-03-08 |
| [DEM-003](./20260308-1400_DEM-003_FRONTENDS_DISEASE_DASHBOARDS/README.md) | admin-frontend · gestor-frontend · donabedian | Disease dashboards React + endpoints Donabedian | `DEPLOYED` | dev2 | 2026-03-08 |
| [DEM-004](./20260308-1600_DEM-004_ADMIN_MODULE_TEST_CONSOLE/README.md) | intellicare-admin | Module Test Console — probe + teste funcional + integração | `APROVADO` | dev2 | 2026-03-08 |
| [DEM-005](./20260308-1700_DEM-005_INTEGRACAO_BRIDGE_PREP/README.md) | core · grahame · wanda · auth · bridge-stub | Preparar portas de integração HIS (intellicare-bridge) | `APROVADO` | dev3 | 2026-03-09 |
| [DEM-006](./20260308-1900_DEM-006_DOCKER_LOCAL_SETUP/README.md) | docker-compose · todos os Dockerfiles | Atualizar e validar todos os containers Docker do ambiente local | `APROVADO` | dev | 2026-03-09 |
