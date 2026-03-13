# DEM-003 - Implementacao

## Arquivos criados

- `packages/intellicare-core/pyproject.toml`
- `packages/intellicare-core/README.md`
- `packages/intellicare-core/intellicare_core/__init__.py`
- `packages/intellicare-core/intellicare_core/contracts/__init__.py`
- `packages/intellicare-core/intellicare_core/contracts/base.py`
- `packages/intellicare-core/intellicare_core/contracts/errors.py`
- `packages/intellicare-core/intellicare_core/config/__init__.py`
- `packages/intellicare-core/intellicare_core/config/settings.py`
- `packages/intellicare-core/intellicare_core/db/__init__.py`
- `packages/intellicare-core/intellicare_core/db/session.py`
- `packages/intellicare-core/intellicare_core/db/migrations.py`
- `packages/intellicare-core/intellicare_core/auth/__init__.py`
- `packages/intellicare-core/intellicare_core/auth/jwt.py`
- `packages/intellicare-core/intellicare_core/vector/__init__.py`
- `packages/intellicare-core/intellicare_core/vector/embeddings.py`
- `packages/intellicare-core/intellicare_core/module_loader/__init__.py`
- `packages/intellicare-core/intellicare_core/module_loader/loader.py`
- `packages/intellicare-core/tests/conftest.py`
- `packages/intellicare-core/tests/test_contracts.py`
- `packages/intellicare-core/tests/test_config.py`
- `packages/intellicare-core/tests/test_db.py`
- `packages/intellicare-core/tests/test_auth.py`
- `packages/intellicare-core/tests/test_vector.py`
- `packages/intellicare-core/tests/test_architecture.py`

## Arquivos removidos

- `packages/intellicare-core/_PLACEHOLDER.md`

## Decisoes tomadas

- O pacote foi estruturado exatamente nas seis areas previstas: `contracts`, `config`, `db`, `auth`, `vector` e `module_loader`.
- `TenantAwareSessionFactory` foi exposta explicitamente em `intellicare_core.db`, alem do helper `tenant_session`, para atender o criterio funcional da DEM.
- A validacao JWT usa JWKS real do Keycloak com selecao por `kid`, em vez de passar o documento JWKS inteiro diretamente para `python-jose`.
- A busca vetorial protege `table` com validacao de identificador SQL antes de interpolar o nome na query.

## Desvios da especificacao

- `pyproject.toml` usa `setuptools.build_meta` no lugar de `setuptools.backends.legacy:build`. Isso permite `pip install -e` com suporte moderno a editable installs no ambiente atual.
- `Settings` passou a resolver `infra/.env` por caminho absoluto a partir da raiz do repo. O caminho relativo da spec quebrava quando `pytest` definia `rootdir` como `packages/intellicare-core/`.
- O client HTTP do OLLAMA usa `ollama_api_url` em vez de `ollama_host`. No ambiente da DEM-002, `OLLAMA_HOST=0.0.0.0` serve para o container, mas nao e uma URL valida para o cliente Python.
- A engine SQLAlchemy foi configurada com `NullPool`. No Windows + `pytest-asyncio`, o pool compartilhado entre event loops causou falhas de conexao com `Event loop is closed`.

## Validacao executada

- `pytest packages/intellicare-core/tests -v --tb=short`
- `python -m pip install -e packages\\intellicare-core[dev]`
- `python -c "from intellicare_core.contracts import BaseModule, TenantContext; print('OK contracts')"`
- `python -c "from intellicare_core.config import get_settings; s = get_settings(); print('OK config', s.environment)"`
- `python -c "from intellicare_core.db import TenantAwareSessionFactory; print('OK db')"`
- `python -c "from intellicare_core.auth import verify_token; print('OK auth')"`
- `python -c "from intellicare_core.vector import get_embedding; print('OK vector')"`
- `python -c "from intellicare_core.module_loader import ModuleLoader; print('OK loader')"`

## Resultado

- Suite de testes da DEM-003 verde: `16 passed`.
- Importacoes principais do SDK funcionando no Python do host.
- `TenantAwareSessionFactory` validada contra `tenant_dev` do PostgreSQL local.
- `get_embedding("teste")` e `semantic_search(...)` validados contra o OLLAMA + pgvector da DEM-002.

## Observacoes

- O `pip install -e` concluiu, mas o `pip` emitiu aviso de compatibilidade porque alguns pacotes legados instalados no host ainda declaram dependencia em `intellicare-core>=1.0.0`.
- O workspace ainda pode exibir warnings de permissao ao listar alguns diretorios temporarios criados por `pip/pytest`. Eles nao foram incluidos no commit da DEM.
