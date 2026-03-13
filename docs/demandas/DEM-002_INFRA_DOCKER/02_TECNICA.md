---
tipo: especificacao-tecnica
demanda: DEM-002
titulo: Infra Docker + Pipeline de Ingestão RAG
fase: 1
sprint: "1.0"
status: aprovado
planejador: Claude
criado: 2026-03-13
---

# DEM-002 — Especificação Técnica

> Todos os arquivos em `C:\Users\egara\INTELLICARE\`.
> Shell de referência: PowerShell (Windows) ou bash (WSL/Linux equivalente).

---

## PRÉ-CONDIÇÕES

- DEM-001 concluída (vault em `docs/`, repo limpo no main)
- Docker Desktop instalado e rodando
- Python 3.11+ disponível (`python --version`)
- Git na branch `main` sem pendências

Verificação:
```powershell
docker --version
docker compose version
python --version
git -C C:\Users\egara\INTELLICARE status
```

---

## BLOCO 1 — `infra/.env.example`

Criar `infra/.env.example` (nunca `.env` direto — vai no git como template):

```dotenv
# ============================================================
# IntelliCare V3 — Variáveis de ambiente
# Copie para infra/.env e preencha os valores
# ============================================================

# PostgreSQL
POSTGRES_USER=intellicare
POSTGRES_PASSWORD=intellicare_dev_password
POSTGRES_DB=intellicare

# Redis
REDIS_PASSWORD=redis_dev_password

# Keycloak
KEYCLOAK_ADMIN=admin
KEYCLOAK_ADMIN_PASSWORD=admin_dev_password
KC_DB=postgres
KC_DB_URL=jdbc:postgresql://postgres:5432/keycloak
KC_DB_USERNAME=intellicare
KC_DB_PASSWORD=intellicare_dev_password

# OLLAMA
OLLAMA_HOST=0.0.0.0
OLLAMA_ORIGINS=*

# Traefik
TRAEFIK_DASHBOARD_PORT=8090

# Aplicação
SECRET_KEY=dev-secret-key-change-in-production
ENVIRONMENT=development
LOG_LEVEL=DEBUG

# Tenant de desenvolvimento
DEV_TENANT_SLUG=tenant_dev
```

Copiar para uso imediato:
```powershell
Copy-Item infra\.env.example infra\.env
```

---

## BLOCO 2 — `infra/postgres/init.sql`

Criar diretório `infra/postgres/` e o arquivo `init.sql`:

```sql
-- IntelliCare V3 — Inicialização do PostgreSQL
-- Executado automaticamente pelo container na primeira inicialização

-- Extensões
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Banco do Keycloak
CREATE DATABASE keycloak
    WITH OWNER = intellicare
    ENCODING = 'UTF8'
    LC_COLLATE = 'en_US.utf8'
    LC_CTYPE = 'en_US.utf8';

-- Schema de desenvolvimento (tenant fictício para testes locais)
CREATE SCHEMA IF NOT EXISTS tenant_dev;

-- Tabela knowledge_base no tenant_dev (para ingestão imediata dos docs)
CREATE TABLE IF NOT EXISTS tenant_dev.knowledge_base (
    id              SERIAL PRIMARY KEY,
    title           TEXT NOT NULL,
    content         TEXT NOT NULL,
    source_path     TEXT NOT NULL,
    chunk_index     INTEGER NOT NULL DEFAULT 0,
    embedding       vector(768),
    metadata        JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now(),
    UNIQUE (source_path, chunk_index)
);

-- Índice HNSW para busca semântica
CREATE INDEX IF NOT EXISTS knowledge_base_embedding_idx
    ON tenant_dev.knowledge_base
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

-- Trigger para updated_at
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER knowledge_base_updated_at
    BEFORE UPDATE ON tenant_dev.knowledge_base
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
```

---

## BLOCO 3 — `infra/docker-compose.yml`

```yaml
# IntelliCare V3 — Docker Compose (desenvolvimento local)
# Uso: docker compose --env-file infra/.env up -d

name: intellicare

services:

  postgres:
    image: pgvector/pgvector:pg16
    container_name: intellicare-postgres
    restart: unless-stopped
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./postgres/init.sql:/docker-entrypoint-initdb.d/init.sql:ro
    ports:
      - "5432:5432"
    networks:
      - intellicare-net
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 30s

  redis:
    image: redis:7-alpine
    container_name: intellicare-redis
    restart: unless-stopped
    command: redis-server --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    networks:
      - intellicare-net
    healthcheck:
      test: ["CMD", "redis-cli", "-a", "${REDIS_PASSWORD}", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  keycloak:
    image: quay.io/keycloak/keycloak:24.0
    container_name: intellicare-keycloak
    restart: unless-stopped
    command: start-dev --import-realm
    environment:
      KEYCLOAK_ADMIN: ${KEYCLOAK_ADMIN}
      KEYCLOAK_ADMIN_PASSWORD: ${KEYCLOAK_ADMIN_PASSWORD}
      KC_DB: ${KC_DB}
      KC_DB_URL: ${KC_DB_URL}
      KC_DB_USERNAME: ${KC_DB_USERNAME}
      KC_DB_PASSWORD: ${KC_DB_PASSWORD}
      KC_HEALTH_ENABLED: "true"
    volumes:
      - keycloak_data:/opt/keycloak/data
      - ./keycloak/realm-export.json:/opt/keycloak/data/import/realm-export.json:ro
    ports:
      - "8080:8080"
    networks:
      - intellicare-net
    depends_on:
      postgres:
        condition: service_healthy
    healthcheck:
      test: ["CMD-SHELL", "exec 3<>/dev/tcp/localhost/8080; echo -e 'GET /health/ready HTTP/1.1\r\nHost: localhost\r\n\r\n' >&3; grep -q 'UP' <&3"]
      interval: 30s
      timeout: 10s
      retries: 10
      start_period: 90s

  ollama:
    image: ollama/ollama:latest
    container_name: intellicare-ollama
    restart: unless-stopped
    environment:
      OLLAMA_HOST: ${OLLAMA_HOST}
      OLLAMA_ORIGINS: ${OLLAMA_ORIGINS}
    volumes:
      - ollama_models:/root/.ollama
    ports:
      - "11434:11434"
    networks:
      - intellicare-net
    # Para GPU NVIDIA: descomentar as linhas abaixo
    # deploy:
    #   resources:
    #     reservations:
    #       devices:
    #         - driver: nvidia
    #           count: 1
    #           capabilities: [gpu]
    healthcheck:
      test: ["CMD-SHELL", "curl -sf http://localhost:11434/api/tags || exit 1"]
      interval: 15s
      timeout: 10s
      retries: 5
      start_period: 30s

  traefik:
    image: traefik:v3.0
    container_name: intellicare-traefik
    restart: unless-stopped
    command:
      - "--api.insecure=true"
      - "--api.dashboard=true"
      - "--providers.docker=true"
      - "--providers.docker.exposedbydefault=false"
      - "--entrypoints.web.address=:80"
      - "--log.level=INFO"
    ports:
      - "80:80"
      - "${TRAEFIK_DASHBOARD_PORT}:8080"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
    networks:
      - intellicare-net
    healthcheck:
      test: ["CMD", "traefik", "healthcheck"]
      interval: 10s
      timeout: 5s
      retries: 3

volumes:
  postgres_data:
  redis_data:
  keycloak_data:
  ollama_models:

networks:
  intellicare-net:
    driver: bridge
```

---

## BLOCO 4 — `infra/keycloak/realm-export.json`

Criar `infra/keycloak/realm-export.json` com realm mínimo (roles e clients
serão configurados na DEM-004 — aqui só o suficiente para o Keycloak iniciar):

```json
{
  "realm": "intellicare",
  "displayName": "IntelliCare",
  "enabled": true,
  "registrationAllowed": false,
  "loginWithEmailAllowed": true,
  "duplicateEmailsAllowed": false,
  "resetPasswordAllowed": true,
  "bruteForceProtected": true,
  "accessTokenLifespan": 900,
  "ssoSessionMaxLifespan": 28800,
  "roles": {
    "realm": [
      { "name": "PLATFORM_ADMIN", "description": "Administrador da plataforma IntelliCare" },
      { "name": "TENANT_GESTOR",  "description": "Gestor de um tenant específico" },
      { "name": "CLINICO",        "description": "Profissional de saúde" },
      { "name": "PACIENTE",       "description": "Paciente" }
    ]
  },
  "clients": [
    {
      "clientId": "intellicare-service",
      "name": "IntelliCare Service",
      "enabled": true,
      "protocol": "openid-connect",
      "publicClient": false,
      "serviceAccountsEnabled": true,
      "authorizationServicesEnabled": false,
      "directAccessGrantsEnabled": true,
      "standardFlowEnabled": true,
      "redirectUris": ["http://localhost/*", "http://localhost:8010/*"],
      "webOrigins": ["http://localhost:8010"]
    }
  ],
  "users": [
    {
      "username": "platform-admin",
      "email": "admin@intellicare.local",
      "enabled": true,
      "emailVerified": true,
      "credentials": [{ "type": "password", "value": "admin123", "temporary": false }],
      "realmRoles": ["PLATFORM_ADMIN"]
    }
  ]
}
```

---

## BLOCO 5 — `deploy/Dockerfile`

```dockerfile
# IntelliCare V3 — Imagem base do intellicare-service
# Empacota todos os módulos em um único container

FROM python:3.11-slim AS base

# Sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Dependências base (cache layer)
COPY packages/intellicare-core/pyproject.toml packages/intellicare-core/
RUN pip install --no-cache-dir -e packages/intellicare-core/[all] 2>/dev/null || true

# Módulos (cada um tem seu pyproject.toml)
COPY modules/ modules/
RUN for module in modules/*/; do \
    if [ -f "$module/pyproject.toml" ]; then \
        pip install --no-cache-dir -e "$module" 2>/dev/null || true; \
    fi; \
done

# Código da aplicação
COPY packages/ packages/
COPY configs/ configs/

# Usuário não-root
RUN useradd -r -s /bin/false intellicare
USER intellicare

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "intellicare_service.app:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## BLOCO 6 — `tools/scripts/ingest_docs.py`

```python
#!/usr/bin/env python3
"""
IntelliCare V3 — Pipeline de ingestão de documentos para pgvector.

Uso:
    python tools/scripts/ingest_docs.py --tenant tenant_dev
    python tools/scripts/ingest_docs.py --tenant tenant_dev --path docs/decisoes/
    python tools/scripts/ingest_docs.py --tenant tenant_dev --dry-run
"""

import argparse
import asyncio
import hashlib
import os
import re
import sys
from pathlib import Path
from typing import Generator

import asyncpg
import httpx

# ── Configuração ──────────────────────────────────────────────────────────────

ROOT = Path(__file__).resolve().parents[2]  # raiz do repo

DEFAULT_DOCS_PATH = ROOT / "docs"
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")
CHUNK_SIZE = 512      # tokens aproximados
CHUNK_OVERLAP = 50    # tokens de sobreposição

DB_URL = (
    f"postgresql://{os.getenv('POSTGRES_USER', 'intellicare')}:"
    f"{os.getenv('POSTGRES_PASSWORD', 'intellicare_dev_password')}@"
    f"{os.getenv('POSTGRES_HOST', 'localhost')}:5432/"
    f"{os.getenv('POSTGRES_DB', 'intellicare')}"
)


# ── Chunking ──────────────────────────────────────────────────────────────────

def chunk_markdown(text: str, path: str) -> Generator[dict, None, None]:
    """Divide markdown em chunks com metadados."""
    # Remove frontmatter YAML
    text = re.sub(r"^---\n.*?\n---\n", "", text, flags=re.DOTALL)
    # Divide por parágrafos/seções
    paragraphs = [p.strip() for p in re.split(r"\n\n+", text) if p.strip()]

    current_chunk = []
    current_size = 0
    chunk_index = 0

    for para in paragraphs:
        words = para.split()
        para_size = len(words)

        if current_size + para_size > CHUNK_SIZE and current_chunk:
            yield {
                "content": "\n\n".join(current_chunk),
                "source_path": path,
                "chunk_index": chunk_index,
                "title": _extract_title(current_chunk[0]),
            }
            chunk_index += 1
            # Sobreposição: mantém último parágrafo
            overlap = current_chunk[-1:] if current_chunk else []
            current_chunk = overlap + [para]
            current_size = sum(len(p.split()) for p in current_chunk)
        else:
            current_chunk.append(para)
            current_size += para_size

    if current_chunk:
        yield {
            "content": "\n\n".join(current_chunk),
            "source_path": path,
            "chunk_index": chunk_index,
            "title": _extract_title(current_chunk[0]),
        }


def _extract_title(text: str) -> str:
    """Extrai título do primeiro heading ou usa primeiras palavras."""
    match = re.match(r"^#+\s+(.+)$", text, re.MULTILINE)
    if match:
        return match.group(1)[:100]
    return text[:80].replace("\n", " ")


# ── Embedding ─────────────────────────────────────────────────────────────────

async def get_embedding(text: str, client: httpx.AsyncClient) -> list[float]:
    """Gera embedding via OLLAMA."""
    resp = await client.post(
        f"{OLLAMA_HOST}/api/embeddings",
        json={"model": EMBED_MODEL, "prompt": text},
        timeout=30.0,
    )
    resp.raise_for_status()
    return resp.json()["embedding"]


# ── Database ──────────────────────────────────────────────────────────────────

async def ensure_table(conn: asyncpg.Connection, schema: str) -> None:
    """Cria tabela knowledge_base se não existir."""
    await conn.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
    await conn.execute(f"""
        CREATE TABLE IF NOT EXISTS {schema}.knowledge_base (
            id          SERIAL PRIMARY KEY,
            title       TEXT NOT NULL,
            content     TEXT NOT NULL,
            source_path TEXT NOT NULL,
            chunk_index INTEGER NOT NULL DEFAULT 0,
            embedding   vector(768),
            metadata    JSONB DEFAULT '{{}}',
            created_at  TIMESTAMPTZ DEFAULT now(),
            updated_at  TIMESTAMPTZ DEFAULT now(),
            UNIQUE (source_path, chunk_index)
        )
    """)
    await conn.execute(f"""
        CREATE INDEX IF NOT EXISTS knowledge_base_embedding_idx_{schema}
        ON {schema}.knowledge_base
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64)
    """)


async def upsert_chunk(
    conn: asyncpg.Connection,
    schema: str,
    chunk: dict,
    embedding: list[float],
) -> None:
    await conn.execute(f"""
        INSERT INTO {schema}.knowledge_base
            (title, content, source_path, chunk_index, embedding)
        VALUES ($1, $2, $3, $4, $5::vector)
        ON CONFLICT (source_path, chunk_index)
        DO UPDATE SET
            title = EXCLUDED.title,
            content = EXCLUDED.content,
            embedding = EXCLUDED.embedding,
            updated_at = now()
    """, chunk["title"], chunk["content"],
        chunk["source_path"], chunk["chunk_index"],
        str(embedding))


# ── Main ──────────────────────────────────────────────────────────────────────

async def ingest(args: argparse.Namespace) -> None:
    docs_path = Path(args.path)
    md_files = sorted(docs_path.rglob("*.md"))

    # Excluir templates
    md_files = [f for f in md_files if "_templates" not in str(f)]

    print(f"Encontrados {len(md_files)} arquivos .md em {docs_path}")

    if args.dry_run:
        for f in md_files:
            rel = str(f.relative_to(ROOT))
            chunks = list(chunk_markdown(f.read_text(encoding="utf-8"), rel))
            print(f"  {rel} → {len(chunks)} chunks")
        print("\nDry run concluído. Nenhuma inserção realizada.")
        return

    # Conexão PostgreSQL
    conn = await asyncpg.connect(DB_URL)
    await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
    await ensure_table(conn, args.tenant)

    total_chunks = 0
    async with httpx.AsyncClient() as http:
        for md_file in md_files:
            rel = str(md_file.relative_to(ROOT))
            text = md_file.read_text(encoding="utf-8")
            chunks = list(chunk_markdown(text, rel))

            for chunk in chunks:
                embedding = await get_embedding(chunk["content"], http)
                await upsert_chunk(conn, args.tenant, chunk, embedding)
                total_chunks += 1

            print(f"  ✓ {rel} ({len(chunks)} chunks)")

    await conn.close()
    print(f"\nIngestão concluída: {len(md_files)} arquivos, {total_chunks} chunks.")


def main() -> None:
    parser = argparse.ArgumentParser(description="IntelliCare — ingestão de docs para pgvector")
    parser.add_argument("--tenant", default="tenant_dev", help="Schema de destino")
    parser.add_argument("--path", default=str(DEFAULT_DOCS_PATH), help="Diretório a ingerir")
    parser.add_argument("--model", default=EMBED_MODEL, help="Modelo de embedding OLLAMA")
    parser.add_argument("--dry-run", action="store_true", help="Listar sem inserir")
    args = parser.parse_args()

    asyncio.run(ingest(args))


if __name__ == "__main__":
    main()
```

**Dependências do script** — criar `tools/scripts/requirements.txt`:

```
asyncpg>=0.29
httpx>=0.27
```

Instalação:
```powershell
pip install -r tools/scripts/requirements.txt
```

---

## BLOCO 7 — `tools/scripts/smoke_test.sh`

```bash
#!/usr/bin/env bash
# IntelliCare V3 — Smoke test do ambiente de desenvolvimento
# Uso: bash tools/scripts/smoke_test.sh

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

pass() { echo -e "${GREEN}✓${NC} $1"; }
fail() { echo -e "${RED}✗${NC} $1"; exit 1; }

echo "IntelliCare V3 — Smoke Test"
echo "================================"

# PostgreSQL
pg_isready -h localhost -p 5432 -U intellicare -d intellicare 2>/dev/null \
    && pass "PostgreSQL: respondendo" \
    || fail "PostgreSQL: não responde"

PGPASSWORD=intellicare_dev_password \
psql -h localhost -U intellicare -d intellicare -c \
    "SELECT extname FROM pg_extension WHERE extname='vector'" 2>/dev/null \
    | grep -q vector \
    && pass "pgvector: extensão ativa" \
    || fail "pgvector: extensão NÃO encontrada"

# Redis
redis-cli -h localhost -p 6379 -a redis_dev_password ping 2>/dev/null \
    | grep -q PONG \
    && pass "Redis: respondendo" \
    || fail "Redis: não responde"

# OLLAMA
curl -sf http://localhost:11434/api/tags > /dev/null \
    && pass "OLLAMA: API respondendo" \
    || fail "OLLAMA: não responde"

# Keycloak
curl -sf http://localhost:8080 > /dev/null \
    && pass "Keycloak: respondendo" \
    || fail "Keycloak: não responde"

# Traefik
curl -sf http://localhost:8090/api/version > /dev/null \
    && pass "Traefik: dashboard respondendo" \
    || fail "Traefik: não responde"

echo ""
echo "================================"
echo "Todos os serviços OK."
```

---

## BLOCO 8 — Atualização de `AGENTS.md`

Adicionar seção "Como subir o ambiente" ao `AGENTS.md` na raiz do repo,
após a seção de "Mapa de Módulos":

```markdown
## Como Subir o Ambiente (Desenvolvimento)

**Pré-requisitos:** Docker Desktop rodando, Python 3.11+

```bash
# 1. Copiar variáveis de ambiente
Copy-Item infra\.env.example infra\.env   # PowerShell
# ou: cp infra/.env.example infra/.env   # bash

# 2. Subir infraestrutura
docker compose --env-file infra/.env -f infra/docker-compose.yml up -d

# 3. Aguardar serviços ficarem healthy (~60s no primeiro boot)
docker compose -f infra/docker-compose.yml ps

# 4. Baixar modelo de embedding OLLAMA (primeira vez, ~270MB)
docker exec intellicare-ollama ollama pull nomic-embed-text

# 5. Indexar vault no pgvector
pip install -r tools/scripts/requirements.txt
python tools/scripts/ingest_docs.py --tenant tenant_dev

# 6. Verificar tudo
bash tools/scripts/smoke_test.sh
```

Serviços disponíveis após `docker compose up`:
- PostgreSQL: `localhost:5432`
- Redis: `localhost:6379`
- Keycloak: `http://localhost:8080` (admin/admin_dev_password)
- OLLAMA: `http://localhost:11434`
- Traefik dashboard: `http://localhost:8090`
```

---

## BLOCO 9 — Commit

```powershell
cd C:\Users\egara\INTELLICARE
git add infra/ deploy/Dockerfile tools/scripts/ AGENTS.md
git commit -m "feat: infra Docker + pipeline ingestão RAG (DEM-002)"
git push origin main
```

Verificação final:
```powershell
docker compose --env-file infra/.env -f infra/docker-compose.yml up -d
# aguardar ~60s
bash tools/scripts/smoke_test.sh
python tools/scripts/ingest_docs.py --tenant tenant_dev --dry-run
```

---

## Resultado esperado

```
infra/
├── .env.example
├── docker-compose.yml
├── postgres/
│   └── init.sql
└── keycloak/
    └── realm-export.json

deploy/
└── Dockerfile

tools/scripts/
├── requirements.txt
├── ingest_docs.py
└── smoke_test.sh
```

Estado final: `docker compose ps` mostra 5 serviços `healthy`.
`SELECT COUNT(*) FROM tenant_dev.knowledge_base` > 0.
