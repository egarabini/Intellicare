---
tipo: especificacao-funcional
demanda: DEM-003
titulo: intellicare-core — SDK Compartilhado
fase: 1
sprint: "1.1"
status: aprovado
planejador: Claude
criado: 2026-03-13
depende_de:
  - DEM-002_INFRA_DOCKER
habilita:
  - DEM-004_KEYCLOAK_CONFIG
  - DEM-005_ADMIN_BACKEND
  - DEM-008_GESTOR_BACKEND
  - DEM-013_CUIDADO_BACKEND
tags:
  - fase-1
  - core
  - sdk
  - p0
---

# DEM-003 — intellicare-core: SDK Compartilhado

## Objetivo

Construir o pacote Python `intellicare-core` — o SDK que todos os módulos
importam. Ele fornece as abstrações fundamentais que garantem consistência,
segurança e isolamento multi-tenant em todo o sistema.

Sem este pacote, cada módulo precisaria reimplementar por conta própria:
autenticação JWT, conexão com PostgreSQL scoped por schema, embeddings via OLLAMA,
e o protocolo de carregamento dinâmico. O resultado seria inconsistência,
duplicação de código e vulnerabilidades de multi-tenancy.

---

## Contexto

A DEM-002 colocou a infraestrutura no ar (PostgreSQL+pgvector, Redis, Keycloak, OLLAMA).
Agora precisamos do "vocabulário comum" que todos os módulos falarão.

O `intellicare-core` é um pacote Python instalável via `pip install -e packages/intellicare-core`.
Ele não é um serviço — não tem porta, não tem Dockerfile próprio. É uma biblioteca.

---

## Os 6 sub-pacotes

### 1. `contracts` — Os contratos que todo módulo assina

Define as interfaces obrigatórias. Se um módulo não implementa `BaseModule`,
o `ModuleLoader` recusa carregá-lo. É a garantia mecânica de consistência.

```
BaseModule          — interface de todo módulo (health, info, routes)
HealthResponse      — schema do GET /health
ModuleInfo          — schema do GET /info (nome, versão, módulos habilitados)
TenantContext       — o objeto que viaja em todo request (tenant_id, schema, user)
APIError            — schema padronizado de erros {"error": "code", "message": "..."}
```

### 2. `config` — Configuração centralizada e validada

`pydantic-settings` lê do `.env` e valida todos os valores na inicialização.
Se uma variável obrigatória estiver faltando, o processo morre com mensagem clara.
Nenhum módulo acessa `os.environ` diretamente — todos importam de `core.config`.

### 3. `db` — Acesso a dados multi-tenant

`TenantAwareSessionFactory` é o coração do isolamento. Ela abre uma sessão
SQLAlchemy que automaticamente define `search_path = tenant_{slug}`, garantindo
que toda query vai para o schema correto sem que o código de negócio precise
saber disso.

Inclui também os helpers Alembic para criação e migração de schemas por tenant.

### 4. `auth` — Autenticação via Keycloak

`verify_token(token)` valida o JWT do Keycloak e retorna um `TenantContext`
populado com `tenant_id`, `user_id` e `roles`. É o único lugar no código
onde tokens são processados. Módulos só chamam `Depends(get_current_tenant)`.

### 5. `vector` — Embeddings e busca semântica

Wrapper assíncrono sobre a API do OLLAMA para geração de embeddings.
Helper `semantic_search(query, schema, table, limit)` encapsula a query pgvector
completa — os módulos não escrevem SQL vetorial diretamente.

### 6. `module_loader` — Carregamento dinâmico por tenant

`ModuleLoader` importa módulos Python sob demanda, verifica que implementam
`BaseModule`, registra suas rotas no app FastAPI principal e aplica o filtro
de módulos habilitados por plano do tenant.

---

## Regra de dependência entre sub-pacotes

```
contracts   ←── nenhuma dependência interna
config      ←── contracts
db          ←── contracts, config
auth        ←── contracts, config
vector      ←── contracts, config
module_loader ←── contracts, config, db, auth
```

`contracts` nunca importa de `db`, `auth` ou qualquer camada acima.
Violações são detectadas pelo linter de arquitetura em `tests/architecture/`.

---

## Critérios de Aceite

1. `pip install -e packages/intellicare-core` conclui sem erro
2. `from intellicare_core.contracts import BaseModule, TenantContext` funciona
3. `from intellicare_core.db import TenantAwareSessionFactory` funciona
4. `from intellicare_core.auth import verify_token` funciona
5. `from intellicare_core.vector import get_embedding, semantic_search` funciona
6. `from intellicare_core.module_loader import ModuleLoader` funciona
7. Testes unitários passam: `pytest packages/intellicare-core/tests/ -v`
8. Teste de arquitetura passa: módulos em camadas superiores não importam `contracts`
9. `TenantAwareSessionFactory` direciona queries para `tenant_{slug}` correto
   (testado com `tenant_dev` do PostgreSQL da DEM-002)
10. `get_embedding("teste")` retorna lista de floats via OLLAMA

---

## O que NÃO está incluído

- Nenhum endpoint de negócio (admin, gestor, cuidado...)
- FHIR helpers — são do módulo `oswaldo` (Fase 3)
- Lógica de billing ou provisionamento — é do módulo `admin`
- Frontend — este pacote é backend puro

---

## Resultado Esperado

Após DEM-003, qualquer agente que começar a DEM-005 (admin backend) tem
um vocabulário claro: `TenantContext` para isolar dados, `BaseModule` para
estruturar o módulo, `TenantAwareSessionFactory` para queries seguras,
`verify_token` para autenticar requests. Zero ambiguidade sobre como fazer.
