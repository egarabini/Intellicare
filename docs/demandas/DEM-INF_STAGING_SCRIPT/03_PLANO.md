---
tipo: plano-execucao
demanda: DEM-INF
titulo: Staging Update Script
status: pendente
dev: DEV-3 / DEV-4
criado: 2026-03-18
---

# DEM-INF Staging — Plano de Execução

## Estimativa

Tempo estimado: 45min | Complexidade: baixa

Apenas criação de arquivos. Nenhuma lógica de negócio.

---

## STEPs

### STEP-001 — Criar `deploy/` se não existir

```bash
mkdir -p deploy
```

### STEP-002 — Criar `deploy/staging_update.sh`

Conforme **Bloco 1** de `02_TECNICA.md`.

```bash
chmod +x deploy/staging_update.sh
```

Critério: `bash -n deploy/staging_update.sh` (syntax check) sem erros.

### STEP-003 — Criar `infra/.env.staging.example`

Conforme **Bloco 2** de `02_TECNICA.md`.

Verificar se `.env.staging` já existe no `.gitignore` — se não, adicionar:
```
infra/.env.staging
infra/.env.production
```

### STEP-004 — Criar `deploy/README.md`

Conforme **Bloco 3** de `02_TECNICA.md`.

### STEP-005 — Atualizar `_dashboard.md`

Na seção "Ações pendentes", substituir o bloco de staging desatualizado
pelo novo comando:
```
STAGING_ENV_FILE=infra/.env.staging bash deploy/staging_update.sh
```

### STEP-006 — Commit

```
infra(staging): DEM-INF script deploy + .env.example + README
```

Arquivos:
```
deploy\staging_update.sh
deploy\README.md
infra\.env.staging.example
docs\demandas\DEM-INF_STAGING_SCRIPT\
.gitignore  (se precisar adicionar .env.staging)
```
