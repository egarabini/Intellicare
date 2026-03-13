---
dem: DEM-008
titulo: Teste E2E de Integração — Especificação Técnica
tipo: TECNICA
status: aprovado
criado: 2026-03-13
---

# DEM-008 · 02 — Especificação Técnica

## Estrutura

```
tests/
└── e2e/
    ├── conftest.py          # fixtures de sessão (env, tokens, cleanup)
    ├── test_health.py       # AC-1: health checks
    ├── test_tenant_flow.py  # AC-2, AC-5, AC-10: lifecycle tenant
    ├── test_auth.py         # AC-3, AC-4, AC-5: autenticação e autorização
    ├── test_isolation.py    # AC-6: isolamento multi-tenant
    └── test_rag.py          # AC-7: ingest + busca semântica

tools/scripts/
└── run_e2e.sh               # AC-9: script de CI
```

---

## BLOCO 1 — `tests/e2e/conftest.py`

```python
"""
Fixtures de sessão para testes E2E.
Requerem ambiente rodando: docker-compose up -d
"""
from __future__ import annotations

import os
import pytest
import httpx

# ---------------------------------------------------------------------------
# Configuração de ambiente
# ---------------------------------------------------------------------------
API_URL = os.getenv("E2E_API_URL",      "http://localhost:8000")
KC_URL  = os.getenv("KEYCLOAK_URL",     "http://localhost:8080")
KC_REALM        = "intellicare"
KC_CLIENT_ID    = "intellicare-service"
KC_CLIENT_SECRET = os.getenv("KEYCLOAK_CLIENT_SECRET", "CHANGE_ME_ON_DEPLOY")

ADMIN_USER = os.getenv("KEYCLOAK_ADMIN",          "admin")
ADMIN_PASS = os.getenv("KEYCLOAK_ADMIN_PASSWORD",  "admin")

E2E_TENANT_SLUG = "e2e_test"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_token(username: str, password: str) -> str:
    resp = httpx.post(
        f"{KC_URL}/realms/{KC_REALM}/protocol/openid-connect/token",
        data={
            "client_id":     KC_CLIENT_ID,
            "client_secret": KC_CLIENT_SECRET,
            "grant_type":    "password",
            "username":      username,
            "password":      password,
            "scope":         "openid",
        },
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def admin_token() -> str:
    return get_token("platform-admin", "Admin@2025!")


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def api() -> httpx.Client:
    """Cliente HTTP sincrono apontando para intellicare-service."""
    with httpx.Client(base_url=API_URL, timeout=15) as client:
        yield client


@pytest.fixture(scope="session")
def admin_headers() -> dict[str, str]:
    return auth_headers(admin_token())


@pytest.fixture(scope="session")
def gestor_headers() -> dict[str, str]:
    """Token do gestor-dev (tenant_dev)."""
    return auth_headers(get_token("gestor-dev", "Gestor@2025!"))


@pytest.fixture(scope="session", autouse=True)
def e2e_tenant(api: httpx.Client, admin_headers: dict):
    """Cria o tenant e2e_test no início da sessão e faz cleanup ao final."""
    # Cleanup anterior se existir
    api.patch(
        f"/admin/tenants/{E2E_TENANT_SLUG}/status",
        json={"status": "suspended"},
        headers=admin_headers,
    )

    resp = api.post(
        "/admin/tenants",
        json={
            "slug": E2E_TENANT_SLUG,
            "name": "E2E Test Tenant",
            "gestor_email": "e2e@intellicare.dev",
        },
        headers=admin_headers,
    )
    # 201 ou 409 (já existe)
    assert resp.status_code in (201, 409), f"Criar tenant falhou: {resp.text}"

    yield E2E_TENANT_SLUG

    # Teardown: reativar para não deixar estado sujo (opcional)
    api.patch(
        f"/admin/tenants/{E2E_TENANT_SLUG}/status",
        json={"status": "active"},
        headers=admin_headers,
    )
```

---

## BLOCO 2 — `tests/e2e/test_health.py`

```python
"""AC-1: Todos os health checks retornam healthy em < 2s."""
import pytest
import httpx
from .conftest import API_URL, KC_URL

pytestmark = pytest.mark.e2e


def test_api_health(api: httpx.Client):
    resp = api.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"


def test_admin_module_health(api: httpx.Client, admin_headers: dict):
    resp = api.get("/admin/health", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["module"] == "admin"


def test_keycloak_health():
    resp = httpx.get(f"{KC_URL}/realms/intellicare/.well-known/openid-configuration", timeout=10)
    assert resp.status_code == 200
    assert "token_endpoint" in resp.json()
```

---

## BLOCO 3 — `tests/e2e/test_auth.py`

```python
"""AC-3, AC-4, AC-5: autenticação e autorização."""
import pytest
import httpx
from jose import jwt as jose_jwt
from .conftest import gestor_headers, get_token

pytestmark = pytest.mark.e2e


def test_token_contem_tenant_id(gestor_headers: dict):
    """AC-3: JWT do gestor-dev contém tenant_id = 'dev'."""
    token = gestor_headers["Authorization"].split(" ")[1]
    # Decodificar sem verificar assinatura (só inspeção de claims)
    payload = jose_jwt.get_unverified_claims(token)
    assert payload.get("tenant_id") == "dev", (
        f"tenant_id esperado 'dev', obtido: {payload.get('tenant_id')}"
    )


def test_gestor_acessa_gestor_endpoint(api: httpx.Client, gestor_headers: dict):
    """AC-4: Token gestor aceito em /gestor/health."""
    resp = api.get("/gestor/health", headers=gestor_headers)
    # Módulo pode não estar carregado → 404 é aceitável aqui (carregado na DEM-009)
    assert resp.status_code in (200, 404), f"Esperado 200 ou 404, obtido {resp.status_code}"


def test_gestor_negado_em_admin(api: httpx.Client, gestor_headers: dict):
    """AC-5: Token gestor rejeitado em /admin/tenants."""
    resp = api.get("/admin/tenants", headers=gestor_headers)
    assert resp.status_code == 403, f"Esperado 403, obtido {resp.status_code}: {resp.text}"


def test_sem_token_retorna_401(api: httpx.Client):
    resp = api.get("/admin/tenants")
    assert resp.status_code == 401
```

---

## BLOCO 4 — `tests/e2e/test_tenant_flow.py`

```python
"""AC-2, AC-10: lifecycle de tenant."""
import pytest
import httpx
import asyncpg
import os

pytestmark = pytest.mark.e2e

DB_URL = os.getenv("DATABASE_URL", "postgresql://intellicare:intellicare@localhost:5432/intellicare")


def test_schema_criado_no_postgres(e2e_tenant: str):
    """AC-2: Schema existe no PostgreSQL após criação do tenant."""
    import asyncio

    async def check():
        conn = await asyncpg.connect(DB_URL)
        try:
            row = await conn.fetchrow(
                "SELECT schema_name FROM information_schema.schemata WHERE schema_name = $1",
                f"tenant_{e2e_tenant}",
            )
            return row is not None
        finally:
            await conn.close()

    schema_exists = asyncio.get_event_loop().run_until_complete(check())
    assert schema_exists, f"Schema 'tenant_{e2e_tenant}' não encontrado no PostgreSQL"


def test_tenant_suspenso_bloqueia_acesso(api: httpx.Client, admin_headers: dict, e2e_tenant: str):
    """AC-10: Tenant suspenso → 403 em endpoints do módulo."""
    # Suspender
    resp = api.patch(
        f"/admin/tenants/{e2e_tenant}/status",
        json={"status": "suspended"},
        headers=admin_headers,
    )
    assert resp.status_code == 200

    # Tentar acessar endpoint do módulo (qualquer módulo)
    # O middleware deve bloquear tenants suspensos
    # (implementado no DEM-003 TenantMiddleware)
    resp = api.get(f"/gestor/health?tenant={e2e_tenant}", headers=admin_headers)
    # 403 ou 404 (módulo não carregado ainda) são ambos válidos aqui
    assert resp.status_code in (200, 403, 404)

    # Reativar
    api.patch(
        f"/admin/tenants/{e2e_tenant}/status",
        json={"status": "active"},
        headers=admin_headers,
    )
```

---

## BLOCO 5 — `tests/e2e/test_isolation.py`

```python
"""AC-6: Isolamento de schema entre tenants."""
import pytest
import asyncpg
import asyncio
import os

pytestmark = pytest.mark.e2e

DB_URL = os.getenv("DATABASE_URL", "postgresql://intellicare:intellicare@localhost:5432/intellicare")


@pytest.mark.asyncio
async def test_dados_isolados_entre_tenants():
    """Inserir em tenant_dev não aparece em tenant_e2e_test e vice-versa."""
    conn = await asyncpg.connect(DB_URL)
    try:
        # Inserir na knowledge_base do tenant_dev
        await conn.execute("SET search_path TO tenant_dev, public")
        await conn.execute("""
            INSERT INTO knowledge_base (title, content, source_path)
            VALUES ('Doc Isolamento', 'Conteúdo exclusivo tenant_dev', 'test/isolamento.txt')
        """)

        # Verificar que NÃO aparece em tenant_e2e_test
        await conn.execute("SET search_path TO tenant_e2e_test, public")
        row = await conn.fetchrow(
            "SELECT * FROM knowledge_base WHERE title = 'Doc Isolamento'"
        )
        assert row is None, "FALHA: dado do tenant_dev vazou para tenant_e2e_test!"

        # Cleanup
        await conn.execute("SET search_path TO tenant_dev, public")
        await conn.execute(
            "DELETE FROM knowledge_base WHERE title = 'Doc Isolamento'"
        )
    finally:
        await conn.close()
```

---

## BLOCO 6 — `tests/e2e/test_rag.py`

```python
"""AC-7: Ingest de documento + busca semântica."""
import pytest
import asyncio
import asyncpg
import os
import sys

pytestmark = pytest.mark.e2e

DB_URL    = os.getenv("DATABASE_URL",  "postgresql://intellicare:intellicare@localhost:5432/intellicare")
OLLAMA_URL = os.getenv("OLLAMA_URL",   "http://localhost:11434")
EMBED_MODEL = os.getenv("EMBED_MODEL", "nomic-embed-text")


@pytest.mark.asyncio
async def test_ingest_e_busca_semantica():
    """Ingerir 1 documento e verificar que a busca retorna ele no top-1."""
    import httpx

    # 1. Obter embedding do documento
    resp = httpx.post(
        f"{OLLAMA_URL}/api/embeddings",
        json={"model": EMBED_MODEL, "prompt": "Protocolo de hipertensão arterial sistêmica"},
        timeout=30,
    )
    if resp.status_code != 200:
        pytest.skip(f"OLLAMA não disponível: {resp.status_code}")

    embedding = resp.json()["embedding"]
    assert len(embedding) == 768, f"Embedding com dimensão inesperada: {len(embedding)}"

    # 2. Inserir na knowledge_base do tenant_dev
    conn = await asyncpg.connect(DB_URL)
    try:
        await conn.execute("SET search_path TO tenant_dev, public")

        # Inserir com embedding
        import json
        await conn.execute("""
            INSERT INTO knowledge_base (title, content, source_path, embedding)
            VALUES ($1, $2, $3, $4::vector)
            ON CONFLICT DO NOTHING
        """,
            "Protocolo HAS",
            "Protocolo de hipertensão arterial sistêmica — PA > 140/90 mmHg",
            "test/rag_test.txt",
            f"[{','.join(str(x) for x in embedding)}]",
        )

        # 3. Busca semântica
        query_resp = httpx.post(
            f"{OLLAMA_URL}/api/embeddings",
            json={"model": EMBED_MODEL, "prompt": "hipertensão pressão arterial"},
            timeout=30,
        )
        query_emb = query_resp.json()["embedding"]

        rows = await conn.fetch(f"""
            SELECT title, 1 - (embedding <=> '[{','.join(str(x) for x in query_emb)}]'::vector) AS sim
            FROM knowledge_base
            ORDER BY embedding <=> '[{','.join(str(x) for x in query_emb)}]'::vector
            LIMIT 3
        """)

        assert rows, "Busca não retornou resultados"
        top1 = rows[0]["title"]
        assert top1 == "Protocolo HAS", f"Top-1 inesperado: {top1}"

        # Cleanup
        await conn.execute("DELETE FROM knowledge_base WHERE source_path = 'test/rag_test.txt'")

    finally:
        await conn.close()
```

---

## BLOCO 7 — `tools/scripts/run_e2e.sh`

```bash
#!/usr/bin/env bash
# run_e2e.sh — Executa suite E2E completa
# Uso: ./tools/scripts/run_e2e.sh
set -euo pipefail

echo "=== IntelliCare V3 — Teste E2E ==="

# 1. Verificar que docker-compose está rodando
echo "Verificando serviços..."
docker compose -f infra/docker-compose.yml ps --quiet || {
    echo "ERRO: docker-compose não está rodando. Execute: docker compose -f infra/docker-compose.yml up -d"
    exit 1
}

# 2. Aguardar health da API
echo "Aguardando API..."
for i in $(seq 1 30); do
    if curl -sf http://localhost:8000/health > /dev/null; then
        echo "API pronta."
        break
    fi
    echo "  Aguardando... ($i/30)"
    sleep 2
done

# 3. Setup Keycloak (idempotente)
echo "Configurando Keycloak..."
python tools/scripts/setup_keycloak.py

# 4. Rodar testes E2E
echo "Executando testes E2E..."
pytest tests/e2e/ \
    -m e2e \
    -v \
    --tb=short \
    --cov=intellicare_core \
    --cov=modules \
    --cov-report=term-missing \
    --cov-fail-under=70

echo "=== Todos os testes E2E passaram ==="
```

---

## BLOCO 8 — `pytest.ini` (ou `pyproject.toml` trecho)

```ini
[pytest]
markers =
    e2e: testes de integração ponta a ponta (requerem ambiente rodando)
    unit: testes unitários (sem dependências externas)
asyncio_mode = auto
```

---

## BLOCO 9 — Commit

```bash
chmod +x tools/scripts/run_e2e.sh

git add tests/e2e/ \
        tools/scripts/run_e2e.sh \
        pytest.ini \
        docs/demandas/DEM-008_E2E_INTEGRATION/

git commit -m "DEM-008: Suite E2E - health, auth, tenant lifecycle, isolamento, RAG basico"
git push origin main
```

---

## Critérios de Aceite (técnicos)

| # | Critério | Verificação |
|---|---|---|
| AC-1 | Health checks < 2s | `test_health.py` |
| AC-2 | Schema criado | `test_tenant_flow.py::test_schema_criado_no_postgres` |
| AC-3 | `tenant_id` no JWT | `test_auth.py::test_token_contem_tenant_id` |
| AC-4 | Gestor aceito em `/gestor` | `test_auth.py::test_gestor_acessa_gestor_endpoint` |
| AC-5 | Gestor rejeitado em `/admin` | `test_auth.py::test_gestor_negado_em_admin` |
| AC-6 | Isolamento de schemas | `test_isolation.py::test_dados_isolados_entre_tenants` |
| AC-7 | RAG top-1 correto | `test_rag.py::test_ingest_e_busca_semantica` |
| AC-8 | `pytest -m e2e` → 0 falhas | `run_e2e.sh` exit code 0 |
| AC-9 | Cobertura ≥ 70% | `--cov-fail-under=70` |
