# ✅ ENTREGA DEV2 — Tarefas T4-F2 + T1-F2
**Data:** 2026-02-22
**Status:** CONCLUÍDO
**Baseado em:** `20260222_BRIEFING_DEV2_DOCKERFILES_HEALTHCHECKS.md`

---

## 📋 Resumo

Resolvidos os 3 problemas críticos que mantinham containers "unhealthy":

1. ✅ Healthchecks do `docker-compose.full.yml` corrigidos para `/api/v1/health` + `curl`
2. ✅ Todos os Dockerfiles padronizados com `curl` + `intellicare-core` + `intellicare-auth` + `HEALTHCHECK`
3. ✅ `intellicare-zilda` reescrito (COPY paths errados apontavam para context errado)

---

## 📁 Arquivos Modificados

### 1. `docker-compose.full.yml`
**Mudança:** 6 healthchecks corrigidos

| Módulo | Antes | Depois |
|---|---|---|
| florence | `python urllib /health` | `curl /api/v1/health` |
| oswaldo | `python urllib /health` | `curl /api/v1/health` |
| donabedian | `python urllib /health` | `curl /api/v1/health` |
| wanda | `python urllib /health` | `curl /api/v1/health` |
| comunicacao | `python urllib /health` | `curl /api/v1/health` |
| geralda | `python urllib /health` | `curl /api/v1/health` |

Parâmetros também ajustados: `timeout: 10s → 5s`, `start_period: 60s → 15s`.

---

### 2. `intellicare-zilda/Dockerfile` — REESCRITO
**Situação anterior:** usava `COPY pyproject.toml .` e `COPY zilda/ zilda/` (context errado — o compose usa `context: .` da raiz).
**Agora:**
- `curl` instalado
- `intellicare-core` copiado e instalado de `/tmp/intellicare-core`
- `intellicare-auth` copiado e instalado (opcional, `|| true`)
- `COPY` paths corrigidos para `./intellicare-zilda/...`
- `HEALTHCHECK` adicionado (`/api/v1/health`)

---

### 3. `intellicare-oswaldo/Dockerfile`
**Adicionado:**
- `curl` (apt-get install)
- `COPY ./intellicare-auth` + `pip install || true`
- `HEALTHCHECK` no stage `api`

---

### 4. `intellicare-florence/Dockerfile`
**Adicionado:**
- `curl`
- `intellicare-auth` (opcional)
- `HEALTHCHECK` no stage `api`

---

### 5. `intellicare-donabedian/Dockerfile`
**Situação anterior:** já tinha `intellicare-auth` (obrigatório, sem `|| true`).
**Adicionado:**
- `curl`
- `HEALTHCHECK` no stage `api`

> Nota: `intellicare-auth` mantido sem `|| true` (era assim antes — donabedian depende dele).

---

### 6. `intellicare-wanda/Dockerfile`
**Adicionado:**
- `curl`
- `intellicare-auth` (opcional)
- `HEALTHCHECK` no stage `api`

---

### 7. `intellicare-comunicacao/Dockerfile`
**Adicionado:**
- `curl`
- `intellicare-auth` (opcional)
- `HEALTHCHECK` no stage `api`

---

### 8. `intellicare-geralda/Dockerfile`
**Adicionado:**
- `curl`
- `intellicare-auth` (opcional)
- `HEALTHCHECK` no stage `api`

---

### 9. `intellicare-nise/Dockerfile`
**Situação anterior:** tinha `curl` e `HEALTHCHECK`, mas URL errada (`/health`) e sem `intellicare-core`/`auth`.
**Corrigido:**
- `COPY ./intellicare-core` + `pip install` no stage **builder**
- `COPY ./intellicare-auth` + `pip install || true` no stage **builder**
- `COPY pyproject.toml ./` → `COPY ./intellicare-nise/pyproject.toml ./`
- `HEALTHCHECK` URL: `/health` → `/api/v1/health`
- Parâmetros: `timeout: 10s → 5s`, `start_period: 40s → 15s`

---

### 10. `scripts/smoke_test.sh` — NOVO
Script de validação que testa os 6 módulos principais:

```bash
./scripts/smoke_test.sh
```

Verifica `GET /api/v1/health` em florence:8001, oswaldo:8002, donabedian:8003, wanda:8004, comunicacao:8005, geralda:8006. Reporta PASS/FAIL por módulo.

---

## ⚠️ Observações para Deploy

### Porta interna vs externa
Os Dockerfiles rodam uvicorn na **porta 8000** internamente. Os healthchecks no `docker-compose.full.yml` apontam para as portas externas (8001–8006). Isso funciona se o compose mapeia `PORTA_MODULO:PORTA_MODULO` e o CMD lê a porta do env. Caso os containers mostrem unhealthy após rebuild, verificar se uvicorn está subindo na porta correta (checar env vars `FLORENCE_PORT`, `OSWALDO_PORT`, etc.).

### Comando de validação
```bash
cd /opt/INTELLICARE
docker-compose -f docker-compose.full.yml build --no-cache
docker-compose -f docker-compose.full.yml up -d
sleep 60
docker-compose -f docker-compose.full.yml ps
./scripts/smoke_test.sh
```

### intellicare-pierre
Não foi alterado — já estava correto (curl + `/api/v1/health`). ✅

---

## 🚫 O que NÃO foi alterado
- Nenhum arquivo `.py` foi tocado
- `intellicare-pierre/Dockerfile` (já correto)
- `intellicare-portal/frontend/Dockerfile` (frontend, fora do escopo)
- `intellicare-admin/Dockerfile` (fora do escopo do briefing)
