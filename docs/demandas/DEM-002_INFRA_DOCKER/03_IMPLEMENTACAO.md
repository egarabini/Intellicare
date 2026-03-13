# DEM-002 - Implementacao

## Arquivos criados

- `infra/.env.example`
- `infra/docker-compose.yml`
- `infra/postgres/init.sql`
- `infra/keycloak/realm-export.json`
- `deploy/Dockerfile`
- `tools/scripts/requirements.txt`
- `tools/scripts/ingest_docs.py`
- `tools/scripts/smoke_test.sh`

## Arquivos alterados

- `AGENTS.md`

## Decisoes tomadas

- Mantido `infra/.env.example` como template versionado e criado `infra/.env` localmente apenas para execucao da stack.
- O `smoke_test.sh` foi implementado via Bash, mas usando `docker exec` para PostgreSQL e Redis. Isso remove dependencia de `psql`, `pg_isready` e `redis-cli` instalados no host.
- O `Dockerfile` foi deixado tolerante ao estado atual do esqueleto V3: ele instala `packages/intellicare-core` e modulos somente se existir `pyproject.toml`.
- O script `ingest_docs.py` preserva idempotencia via `ON CONFLICT (source_path, chunk_index) DO UPDATE`.

## Desvios da especificacao

- Traefik foi exposto em `8088:80` em vez de `80:80`. No host atual, o Docker falhou ao bindar a porta `80` com erro de permissao. O dashboard permaneceu em `8090`.
- O `init.sql` nao definiu `LC_COLLATE` e `LC_CTYPE` no `CREATE DATABASE keycloak`. O bootstrap do `pgvector/pgvector:pg16` inicializou corretamente com o locale da imagem, e a versao simplificada evita falhas de locale em ambientes diferentes.
- O chunking do `ingest_docs.py` foi reduzido de `512` para `200` tokens aproximados com overlap `50`. Com `512`, o `nomic-embed-text` no OLLAMA retornou `500` por estouro de contexto durante a ingestao real.
- O smoke test foi executado com `C:\Program Files\Git\bin\bash.exe`, porque `bash` puro nao estava disponivel no PATH do ambiente Windows.

## Validacao executada

- `docker compose --env-file infra/.env -f infra/docker-compose.yml config`
- `docker compose --env-file infra/.env -f infra/docker-compose.yml up -d`
- `curl http://localhost:11434/api/tags`
- `curl -I http://localhost:8080`
- `curl http://localhost:8090/api/version`
- `C:\Program Files\Git\bin\bash.exe tools/scripts/smoke_test.sh`
- `python tools/scripts/ingest_docs.py --tenant tenant_dev --dry-run`
- `python tools/scripts/ingest_docs.py --tenant tenant_dev`
- `docker exec -e PGPASSWORD=intellicare_dev_password intellicare-postgres psql -U intellicare -d intellicare -tAc "SELECT COUNT(*) FROM tenant_dev.knowledge_base"`
- `docker build -f deploy/Dockerfile .`

## Resultado

- Stack da DEM-002 operacional com `postgres`, `redis`, `keycloak`, `ollama` e `traefik` saudaveis.
- OLLAMA com `nomic-embed-text:latest` baixado.
- Ingestao concluida para `docs/`.
- Contagem final em `tenant_dev.knowledge_base`: `296`.

## Observacoes

- `docker compose ps` no host ainda lista containers orfaos antigos do projeto `intellicare`. Eles nao foram removidos nesta DEM para evitar impacto em artefatos locais preexistentes.
