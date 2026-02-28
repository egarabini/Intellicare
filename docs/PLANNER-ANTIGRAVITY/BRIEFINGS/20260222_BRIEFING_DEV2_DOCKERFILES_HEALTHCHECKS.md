# 📋 BRIEFING DEV2 — Tarefas T4-F2 + T1-F2
**Data:** 2026-02-22  
**Prazo estimado:** 2-3 dias  
**Prioridade:** 🔴 Alta — resolve containers "unhealthy" em produção  
**Conflito com outras trilhas:** ZERO — trabalho isolado em Dockerfiles e endpoints

---

## 🎯 Objetivo

Resolver dois problemas críticos que mantêm os containers como **"unhealthy"** no servidor:

1. **Healthchecks apontam para URL errada** (`/health` vs `/api/v1/health`)
2. **Dockerfiles inconsistentes** — alguns não instalam `intellicare-core` nem `intellicare-auth`

Ao final, **TODOS os containers** devem subir com status **"healthy"**.

---

## 📊 Diagnóstico Atual (Auditoria Completa)

### Problema 1: Healthchecks Incorretos no `docker-compose.full.yml`

O `docker-compose.full.yml` configura healthchecks assim:
```yaml
healthcheck:
  test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8001/health')"]
```

Mas os módulos expõem o endpoint em **`/api/v1/health`** (não `/health`).

| Módulo | URL no docker-compose | URL real no código | Status |
|---|---|---|---|
| florence | `/health` | `/api/v1/health` + `/health` (legado) | ⚠️ Funciona por acaso |
| oswaldo | `/health` | `/api/v1/health` + `/health` (legado) | ⚠️ Funciona por acaso |
| donabedian | `/health` | `/api/v1/health` (somente) | ❌ **FALHA** |
| wanda | `/health` | `/api/v1/health` (somente) | ❌ **FALHA** |
| comunicacao | `/health` | `/api/v1/health` (somente) | ❌ **FALHA** |
| geralda | `/health` | `/api/v1/health` (somente) | ❌ **FALHA** |

### Problema 2: Dockerfiles Inconsistentes

| Módulo | Tem intellicare-core? | Tem intellicare-auth? | Tem curl? | Tem HEALTHCHECK? |
|---|---|---|---|---|
| **oswaldo** | ✅ COPY /tmp | ❌ | ❌ | ❌ |
| **florence** | ✅ COPY /tmp | ❌ | ❌ | ❌ |
| **donabedian** | ✅ COPY /tmp | ✅ COPY /tmp | ❌ | ❌ |
| **wanda** | ✅ COPY /tmp | ❌ | ❌ | ❌ |
| **comunicacao** | ✅ COPY /tmp | ❌ | ❌ | ❌ |
| **geralda** | ✅ COPY /tmp | ❌ | ❌ | ❌ |
| **zilda** | ❌ **FALTANDO** | ❌ | ❌ | ❌ |
| **nise** | ❌ **FALTANDO** | ❌ | ✅ | ✅ (mas URL errada) |
| **superz** | ❌ (não usa) | ❌ | ✅ | ✅ `/api/v1/health` ✅ |

### Problema 3: psycopg Inconsistente

| Módulo | Tem psycopg? | Formato |
|---|---|---|
| oswaldo | ✅ | `psycopg[binary] ^3.1.0` |
| comunicacao | ✅ | `psycopg[binary] ^3.1.0` |
| admin | ✅ | `psycopg[binary] ^3.1.0` |
| **florence** | ❌ | — |
| **donabedian** | ❌ | — |
| **wanda** | ❌ | — |
| **geralda** | ❌ | — |
| **zilda** | ❌ | — |

---

## ✅ TAREFA 1: Corrigir Healthchecks no `docker-compose.full.yml`

**Arquivo:** `./docker-compose.full.yml`

### O que mudar:

Para **CADA módulo backend** (florence, oswaldo, donabedian, wanda, comunicacao, geralda), trocar o healthcheck de:

```yaml
# ❌ ANTES (errado)
healthcheck:
  test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:PORTA/health')"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 60s
```

Para:

```yaml
# ✅ DEPOIS (correto — usa curl + URL correta)
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:PORTA/api/v1/health"]
  interval: 30s
  timeout: 5s
  retries: 3
  start_period: 15s
```

### Mapeamento de portas por módulo:

| Módulo | Container | Porta | URL do healthcheck |
|---|---|---|---|
| florence | intellicare-florence | 8001 | `http://localhost:8001/api/v1/health` |
| oswaldo | intellicare-oswaldo | 8002 | `http://localhost:8002/api/v1/health` |
| donabedian | intellicare-donabedian | 8003 | `http://localhost:8003/api/v1/health` |
| wanda | intellicare-wanda | 8004 | `http://localhost:8004/api/v1/health` |
| comunicacao | intellicare-comunicacao | 8005 | `http://localhost:8005/api/v1/health` |
| geralda | intellicare-geralda | 8006 | `http://localhost:8006/api/v1/health` |

> [!IMPORTANT]
> Para usar `curl` no healthcheck, o Dockerfile precisa ter `curl` instalado (ver Tarefa 2).

---

## ✅ TAREFA 2: Padronizar TODOS os Dockerfiles

### Template padrão a seguir:

Use este template como referência. O modelo de **oswaldo/florence/wanda/geralda/comunicacao** já segue a estrutura com multi-stage build. O importante é garantir que TODOS tenham:

1. `curl` instalado (para healthchecks)
2. `intellicare-core` copiado e instalado
3. `intellicare-auth` copiado e instalado (como opcional)
4. `HEALTHCHECK` no Dockerfile

```dockerfile
FROM python:3.11-slim AS base

WORKDIR /app

# Instalar curl para healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

# ── intellicare-core (obrigatório) ──────────────────────────
COPY ./intellicare-core /tmp/intellicare-core
RUN pip install --no-cache-dir -e /tmp/intellicare-core

# ── intellicare-auth (opcional — módulo funciona sem) ───────
COPY ./intellicare-auth /tmp/intellicare-auth
RUN pip install --no-cache-dir -e /tmp/intellicare-auth || true

# ── Instalar o módulo ──────────────────────────────────────
COPY ./intellicare-MODULO/pyproject.toml ./intellicare-MODULO/README.md* ./

RUN pip install --no-cache-dir . || true

COPY ./intellicare-MODULO .

RUN pip install --no-cache-dir -e .

EXPOSE PORTA

# ── API ────────────────────────────────────────────────────
FROM base AS api

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:PORTA/api/v1/health || exit 1

CMD ["uvicorn", "MODULO.api.app:ENTRY", "--host", "0.0.0.0", "--port", "PORTA"]
```

### Mudanças por Dockerfile (checklist detalhado):

#### 1. `intellicare-zilda/Dockerfile` ⚠️ PRECISA MAIS MUDANÇAS
**Situação atual:** NÃO copia intellicare-core, NÃO tem curl, NÃO tem HEALTHCHECK.

```diff
 FROM python:3.11-slim AS base
 
 WORKDIR /app

+# Instalar curl para healthcheck
+RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*
+
+# Instalar intellicare-core
+COPY ./intellicare-core /tmp/intellicare-core
+RUN pip install --no-cache-dir -e /tmp/intellicare-core
+
+# Instalar intellicare-auth (opcional)
+COPY ./intellicare-auth /tmp/intellicare-auth
+RUN pip install --no-cache-dir -e /tmp/intellicare-auth || true
+
-COPY pyproject.toml .
-COPY zilda/ zilda/
+COPY ./intellicare-zilda/pyproject.toml ./intellicare-zilda/README.md* ./
+RUN pip install --no-cache-dir . || true
+COPY ./intellicare-zilda .
+RUN pip install --no-cache-dir -e .
 
-RUN pip install --no-cache-dir -e .
+EXPOSE 8000
 
 # --- API ---
 FROM base AS api
-EXPOSE 8000
+HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
+    CMD curl -f http://localhost:8000/api/v1/health || exit 1
 CMD ["uvicorn", "zilda.api.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
```

> [!CAUTION]
> O Zilda usa `context: .` (raiz do .) no `docker-compose.full.yml`, mas o Dockerfile atual usa `COPY pyproject.toml .` como se o context fosse o diretório do módulo. **Precisa mudar para `COPY ./intellicare-zilda/...`** para ser consistente.

---

#### 2. `intellicare-oswaldo/Dockerfile`
**Adicionar:** curl + intellicare-auth + HEALTHCHECK

```diff
+# Instalar curl para healthcheck
+RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*
+
 # Instalar intellicare-core primeiro
 COPY ./intellicare-core /tmp/intellicare-core
 RUN pip install --no-cache-dir -e /tmp/intellicare-core

+# Instalar intellicare-auth (opcional)
+COPY ./intellicare-auth /tmp/intellicare-auth
+RUN pip install --no-cache-dir -e /tmp/intellicare-auth || true
+
 # ... resto mantém igual ...

 # API (porta 8000)
 FROM base AS api
+HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
+    CMD curl -f http://localhost:8000/api/v1/health || exit 1
 CMD ["uvicorn", "oswaldo.api.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
```

---

#### 3. `intellicare-florence/Dockerfile`
**Adicionar:** curl + intellicare-auth + HEALTHCHECK (mesmo padrão do oswaldo)

---

#### 4. `intellicare-wanda/Dockerfile`
**Adicionar:** curl + intellicare-auth + HEALTHCHECK (mesmo padrão)

---

#### 5. `intellicare-comunicacao/Dockerfile`
**Adicionar:** curl + intellicare-auth + HEALTHCHECK

> [!NOTE]  
> O comunicacao já tem auth opcional no código Python (padrão try/except). O COPY do intellicare-auth no Dockerfile permite que funcione COM auth quando disponível.

---

#### 6. `intellicare-geralda/Dockerfile`
**Adicionar:** curl + intellicare-auth + HEALTHCHECK

---

#### 7. `intellicare-donabedian/Dockerfile`
**Já tem intellicare-auth.** Adicionar: curl + HEALTHCHECK

---

#### 8. `intellicare-nise/Dockerfile`
**Atenção especial:** Este módulo usa multi-stage build diferente (builder → runtime).

```diff
 # Install runtime dependencies
 RUN apt-get update && apt-get install -y \
     libpq5 \
     curl \
     && rm -rf /var/lib/apt/lists/*

 # Health check
-HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
-    CMD curl -f http://localhost:8000/health || exit 1
+HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
+    CMD curl -f http://localhost:8000/api/v1/health || exit 1
```

**Também adicionar:** COPY de intellicare-core e intellicare-auth no stage builder.

---

#### 9. `intellicare-superz/Dockerfile`
**Já está OK.** Tem curl, HEALTHCHECK apontando para `/api/v1/health`. ✅ Nenhuma mudança necessária.

---

## ✅ TAREFA 3: Validação Final

Após todas as mudanças, executar no servidor:

```bash
# 1. Rebuild sem cache
cd /opt/INTELLICARE
docker-compose -f docker-compose.full.yml build --no-cache

# 2. Subir tudo
docker-compose -f docker-compose.full.yml up -d

# 3. Esperar 60 segundos para start_period
sleep 60

# 4. Verificar status
docker-compose -f docker-compose.full.yml ps

# 5. Todos devem estar "(healthy)"
# Se algum estiver "(unhealthy)", verificar logs:
docker-compose -f docker-compose.full.yml logs --tail=50 NOME_DO_MODULO
```

### Script de smoke test (criar como `scripts/smoke_test.sh`):
```bash
#!/bin/bash
echo "=== IntelliCare Smoke Test ==="

MODULES=(
    "florence:8001"
    "oswaldo:8002"
    "donabedian:8003"
    "wanda:8004"
    "comunicacao:8005"
    "geralda:8006"
)

PASS=0
FAIL=0

for entry in "${MODULES[@]}"; do
    MODULE="${entry%%:*}"
    PORT="${entry##*:}"
    
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:${PORT}/api/v1/health" --connect-timeout 5)
    
    if [ "$HTTP_CODE" == "200" ]; then
        echo "✅ ${MODULE} (porta ${PORT}) — HTTP ${HTTP_CODE}"
        PASS=$((PASS + 1))
    else
        echo "❌ ${MODULE} (porta ${PORT}) — HTTP ${HTTP_CODE}"
        FAIL=$((FAIL + 1))
    fi
done

echo ""
echo "Resultado: ${PASS} OK, ${FAIL} FALHAS de ${#MODULES[@]} módulos"
```

---

## ⚠️ Regras Importantes

> [!WARNING]
> **NÃO ALTERAR** nenhum código Python dos módulos (`*.py`). Estas tarefas envolvem APENAS:
> - `Dockerfile` (cada módulo)
> - `docker-compose.full.yml` (healthchecks)
> - Script de smoke test

> [!IMPORTANT]
> O build context no `docker-compose.full.yml` usa `context: .` (raiz do .). Então os COPYs nos Dockerfiles devem usar caminhos relativos a essa raiz:
> - ✅ `COPY ./intellicare-core /tmp/intellicare-core`
> - ✅ `COPY ./intellicare-oswaldo/pyproject.toml ...`
> - ❌ `COPY pyproject.toml .` (errado se context é a raiz)

---

## 📁 Arquivos que o Dev2 vai modificar

| # | Arquivo | Tipo de mudança |
|---|---|---|
| 1 | `docker-compose.full.yml` | Corrigir healthcheck URLs (6 módulos) |
| 2 | `intellicare-zilda/Dockerfile` | Reescrever (mais mudanças) |
| 3 | `intellicare-oswaldo/Dockerfile` | Adicionar curl + auth + HEALTHCHECK |
| 4 | `intellicare-florence/Dockerfile` | Adicionar curl + auth + HEALTHCHECK |
| 5 | `intellicare-donabedian/Dockerfile` | Adicionar curl + HEALTHCHECK |
| 6 | `intellicare-wanda/Dockerfile` | Adicionar curl + auth + HEALTHCHECK |
| 7 | `intellicare-comunicacao/Dockerfile` | Adicionar curl + auth + HEALTHCHECK |
| 8 | `intellicare-geralda/Dockerfile` | Adicionar curl + auth + HEALTHCHECK |
| 9 | `intellicare-nise/Dockerfile` | Corrigir URL + adicionar core/auth |
| 10 | `scripts/smoke_test.sh` | **NOVO** — script de validação |

**Total: 9 arquivos modificados + 1 novo**

---

## 🏁 Critério de Conclusão

A tarefa está **CONCLUÍDA** quando:

1. ✅ `docker-compose -f docker-compose.full.yml ps` mostra TODOS os containers como **(healthy)**
2. ✅ `./scripts/smoke_test.sh` retorna **0 FALHAS**
3. ✅ Nenhum código Python foi alterado
4. ✅ Todos os Dockerfiles instalam `intellicare-core` e `intellicare-auth`
5. ✅ Todos os Dockerfiles têm `curl` e `HEALTHCHECK`
