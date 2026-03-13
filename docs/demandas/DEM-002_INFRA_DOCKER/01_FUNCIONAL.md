---
tipo: especificacao-funcional
demanda: DEM-002
titulo: Infra Docker + Pipeline de Ingestão RAG
fase: 1
sprint: "1.0"
status: aprovado
planejador: Claude
criado: 2026-03-13
depende_de:
  - DEM-001_VAULT_OBSIDIAN
habilita:
  - DEM-003_INTELLICARE_CORE
  - DEM-004_KEYCLOAK_CONFIG
tags:
  - fase-1
  - infra
  - docker
  - pgvector
  - rag
  - p0
---

# DEM-002 — Infra Docker + Pipeline de Ingestão RAG

## Objetivo

Colocar no ar o ambiente de desenvolvimento local completo do IntelliCare V3 e
o pipeline de ingestão de documentos para o RAG.

Ao final desta DEM, o desenvolvedor consegue:

1. Subir toda a infraestrutura com **`docker compose up -d`**
2. Conectar no PostgreSQL com pgvector ativo
3. Indexar documentos Markdown no pgvector com **`python tools/scripts/ingest_docs.py`**
4. Verificar que o OLLAMA responde (embedding + geração)
5. Acessar o Keycloak (interface admin disponível)
6. Verificar Traefik (dashboard de roteamento ativo)

Sem isso, nenhuma DEM de código (DEM-003 em diante) tem onde rodar.

---

## Contexto

A tríade RAG+SLM+pgvector (ADR-003) exige infraestrutura local específica.
O `docker-compose.yml` é o único arquivo que precisa existir para um dev novo
clonar o repo e ter tudo rodando. Não há dependências de cloud.

A DEM-001 criou `tools/scripts/` como diretório placeholder. Esta DEM o popula
com o script de ingestão — que é o "alimentador" do pgvector. Faz sentido
colocar aqui (sprint 1.0) porque pgvector é habilitado nesta mesma DEM e o
pipeline não depende de nenhum módulo de negócio.

---

## Escopo

### O que está incluído

| Bloco | O que entrega | Por quê |
|-------|--------------|---------|
| 1 | `infra/docker-compose.yml` | Stack completa: PG+pgvector, Redis, Keycloak, OLLAMA, Traefik |
| 2 | `infra/postgres/init.sql` | `CREATE EXTENSION vector` + role + encoding |
| 3 | `infra/.env.example` | Todas as variáveis necessárias documentadas |
| 4 | `infra/keycloak/` | Realm export inicial (intellicare) |
| 5 | `deploy/Dockerfile` | Imagem base do `intellicare-service` |
| 6 | `tools/scripts/ingest_docs.py` | Markdown → chunks → embedding → pgvector |
| 7 | `tools/scripts/smoke_test.sh` | Verifica que todos os serviços respondem |
| 8 | Atualização de `AGENTS.md` | Adicionar seção "Como subir o ambiente" |

### O que NÃO está incluído

- Nenhum módulo de negócio (admin, gestor, cuidado...)
- Keycloak realm completo com roles — isso é DEM-004
- Configuração de CI/CD — roadmap
- Deploy em produção — roadmap
- OLLAMA com GPU — o compose sobe CPU; documentar como ativar GPU opcionalmente

---

## Serviços no docker-compose.yml

| Serviço | Imagem | Porta | Papel |
|---------|--------|-------|-------|
| `postgres` | `pgvector/pgvector:pg16` | 5432 | BD principal + extensão vector |
| `redis` | `redis:7-alpine` | 6379 | Cache + filas |
| `keycloak` | `quay.io/keycloak/keycloak:24` | 8080 | IdP (OAuth2/OIDC) |
| `ollama` | `ollama/ollama:latest` | 11434 | SLM local (embeddings + geração) |
| `traefik` | `traefik:v3` | 80, 443, 8090 | Proxy reverso + roteamento |

**Rede:** `intellicare-net` (bridge). Todos os serviços na mesma rede interna.

**Volumes nomeados:**
- `postgres_data` — persistência do PostgreSQL
- `redis_data` — persistência do Redis
- `keycloak_data` — persistência do Keycloak
- `ollama_models` — modelos OLLAMA baixados

---

## Pipeline de ingestão RAG (ingest_docs.py)

O script varre `docs/` recursivamente, chunkifica cada `.md`, gera embedding
via OLLAMA e insere no pgvector do tenant de destino.

```
docs/**/*.md
    ↓
chunking (512 tokens, 50 tokens overlap)
    ↓
embedding via OLLAMA (nomic-embed-text, 384 dims)
    ↓
INSERT INTO {schema}.knowledge_base (title, content, source, embedding)
```

Tabela `knowledge_base` é distinta de `protocols` (que vem na DEM-013).
`knowledge_base` armazena docs do vault (ADRs, notas de módulo, design-docs).
`protocols` armazenará protocolos clínicos. Mesma infraestrutura, propósitos diferentes.

O script aceita parâmetros:
- `--tenant` — schema de destino (default: `tenant_dev` para desenvolvimento)
- `--path` — diretório a ingerir (default: `docs/`)
- `--model` — modelo de embedding (default: `nomic-embed-text`)
- `--dry-run` — mostra o que seria ingerido sem fazer INSERT

---

## Critérios de Aceite

1. `docker compose up -d` sobe todos os 5 serviços sem erro
2. `docker compose ps` mostra todos com status `healthy`
3. `psql -U intellicare -c "SELECT extname FROM pg_extension WHERE extname='vector'"` retorna `vector`
4. `curl http://localhost:11434/api/tags` retorna JSON com modelos disponíveis
5. `curl http://localhost:8080` redireciona para Keycloak login
6. `python tools/scripts/smoke_test.sh` passa todos os checks
7. `python tools/scripts/ingest_docs.py --tenant tenant_dev --dry-run` lista arquivos sem erro
8. `python tools/scripts/ingest_docs.py --tenant tenant_dev` conclui sem erro
9. `SELECT COUNT(*) FROM tenant_dev.knowledge_base` retorna > 0
10. `deploy/Dockerfile` faz build sem erro (`docker build -f deploy/Dockerfile .`)

---

## Resultado Esperado

Após DEM-002, o ambiente de desenvolvimento é reproduzível com um único comando.
Qualquer agente desenvolvedor clona o repo, copia `.env.example` para `.env`,
roda `docker compose up -d` e está pronto para trabalhar na DEM-003.

O vault Obsidian já está indexado no pgvector — os ADRs, notas de módulos e
design-docs são consultáveis via busca semântica desde o início do desenvolvimento.

---

## Notas para o Agente Desenvolvedor

- Use `pgvector/pgvector:pg16` — não `postgres:16`. A imagem oficial da pgvector já
  inclui a extensão compilada.
- OLLAMA precisa baixar o modelo `nomic-embed-text` na primeira execução (~270MB).
  Documentar isso no README e no smoke_test.
- O `ingest_docs.py` deve ser idempotente: re-executar não duplica registros.
  Use `INSERT ... ON CONFLICT (source_path, chunk_index) DO UPDATE`.
- Keycloak em dev roda com `--optimized` desabilitado e `start-dev` para simplicidade.
- Traefik em dev expõe o dashboard em porta 8090 sem autenticação (aceitável localmente).
