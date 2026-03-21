---
tipo: briefing-completo
demanda: DEM-INF (Memória Operacional)
titulo: Institucionalizar patterns, gotchas e handoffs do projeto
dev: CODEX
estimativa: 3h
base: Conclusões IA-FRAMEWORK — Camada 1
---

# DEM-INF — Memória Operacional IntelliCare

## Contexto

O projeto acumulou 52+ DEMs de conhecimento operacional que hoje vive apenas
na memória de sessão. Erros recorrentes (CareplannerService fixtures, git push
antes do deploy, init-db só roda no primeiro boot) continuam custando tempo
a cada sprint porque não existem como artefatos persistentes.

Esta DEM implementa a **Camada 1 do IA-FRAMEWORK**: transformar conhecimento
implícito em arquivos reutilizáveis por qualquer dev ou agente.

## Regra de ouro

**Conteúdo real, não templates vazios.** Cada arquivo deve ter no mínimo
3 entradas concretas retiradas de situações reais do projeto. Se o conteúdo
puder ser replicado por qualquer LLM sem conhecer o IntelliCare, está errado.

---

## STEP-001 — Criar estrutura de pastas

```bash
mkdir -p docs/patterns docs/gotchas docs/digests
mkdir -p docs/demandas/_templates
```

---

## STEP-002 — `docs/patterns/README.md`

Índice + regra operacional:

```markdown
# Patterns IntelliCare

Catálogo de padrões de implementação reutilizáveis.
Toda DEM que estabelecer um padrão novo registra aqui.

## Índice
- [Backend Modules](backend-modules.md)
- [Frontend Pages](frontend-pages.md)
- [Workers e Webhooks](workers-webhooks.md)
```

---

## STEP-003 — `docs/patterns/backend-modules.md`

Entradas obrigatórias (conteúdo real):

**Padrão de módulo FastAPI:**
- Estrutura: `models.py` → `repository.py` → `services.py` → `api/routes.py` → `main.py`
- O `main.py` do módulo é registrado em `modules/__init__.py` via `include_router`
- Settings via `BaseSettings` com `env_prefix` — nunca hardcoded

**Padrão de migration:**
- Arquivo em `modules/{modulo}/migrations/NNN_descricao.sql`
- Aplicado pelo `startup_event` do módulo, não pelo Alembic
- Sempre idempotente: `CREATE TABLE IF NOT EXISTS`, `ADD COLUMN IF NOT EXISTS`

**Padrão de seed:**
- Seed no `startup_event` com `ON CONFLICT DO NOTHING` ou equivalente
- Nunca falhar silenciosamente — logar o erro mas não travar o startup

**Padrão de teste de integração async:**
- Fixture `client: AsyncClient` + `db: AsyncSession` no conftest
- Quando `CareplannerService.__init__` ganhar novo parâmetro, atualizar
  TODAS as fixtures que o instanciam — buscar com:
  `grep -rn "CareplannerService(" packages/intellicare-core/tests/`

---

## STEP-004 — `docs/patterns/frontend-pages.md`

Entradas obrigatórias:

**Padrão de página List/Detail:**
- Hook `useNomeModulo.ts` em `src/hooks/` — separar lógica de dados da UI
- Página List: tabela paginada + filtro por status + badge de contagem
- Página Detail: layout 2 colunas — info principal esquerda, timeline/ações direita

**Mantine 7 — armadilhas conhecidas:**
- Usar `NativeSelect` para dropdowns simples, não `Select` — `Select` tem
  comportamento de portal que quebra em modais em Mantine 7
- `TextInput` com `form.getInputProps` não precisa de `onChange` explícito
- `Badge` não aceita prop `radius` no Mantine 7 — usar `variant` + `size`

**Padrão de hook com canal:**
```typescript
// Canal como parâmetro de filtro — não hardcoded
const { data: templates } = useCareplannerTemplates(active, channel)
```

---

## STEP-005 — `docs/patterns/workers-webhooks.md`

Entradas obrigatórias:

**Padrão de Adapter:**
- Classe com `__init__(settings)`, método async `send_message()`, método `close()`
- Cliente httpx lazy-initialized em `_get_client()` — não no `__init__`
- Retry exponencial: `0.5 * (2 ** (attempt - 1))` segundos, máx 3 tentativas
- Sempre implementar `verify_webhook_secret(token)` — retornar `True` se secret vazio

**Padrão de webhook seguro:**
- Token no path: `POST /webhook/{canal}/{token}`
- Verificar com `hmac.compare_digest` ou comparação direta
- Retornar `{"status": "ignored"}` para eventos não relevantes — nunca 4xx desnecessário
- Logar eventos órfãos com `logger.warning` + incrementar métrica `orphan_inbound_total`

**Padrão de worker Redis:**
- Loop com `BLPOP` ou `lpop` com sleep
- Dead-letter queue para mensagens que falharam N vezes
- Sempre logar o `correlation_id` em todas as mensagens de log do worker

---

## STEP-006 — `docs/gotchas/README.md`

```markdown
# Gotchas IntelliCare

Problemas recorrentes documentados. Antes de gastar tempo debugando,
verificar se o problema já está catalogado aqui.

## Índice
- [CarePlanner](careplanner.md)
- [Staging e Deploy](staging-deploy.md)
- [Keycloak e Auth](keycloak-auth.md)
```

---

## STEP-007 — `docs/gotchas/careplanner.md`

Entradas obrigatórias (todas situações reais):

**`CareplannerService.__init__` — parâmetros crescem a cada DEM de canal**
> Situação: DEM-047/048/049 adicionaram `whatsapp`, `email`, `sms` ao `__init__`.
> Symptoma: `TypeError: __init__() missing N required positional arguments` nos testes.
> Fix: `grep -rn "CareplannerService(" packages/intellicare-core/tests/` e atualizar
> TODAS as fixtures para incluir os novos adapters como `MagicMock()`.

**`Channel` enum — sempre adicionar ao dispatcher também**
> Situação: adicionar novo valor ao `Channel(StrEnum)` não é suficiente.
> Symptoma: novo canal entra no banco mas o dispatcher ignora e usa RC.
> Fix: atualizar `_send_to_channel()` em `services.py` com `elif channel == Channel.NOVO`.

**Cross-tenant phone lookup — lento com muitos tenants**
> Situação: `find_active_task_by_phone` varre todos os schemas sequencialmente.
> Aceitável para V3 (poucos tenants). Se > 20 tenants, adicionar índice global.

**`rc_room_id` obrigatório no RC mas None no WhatsApp/Email/SMS**
> Situação: `open_task` tenta criar room no RC para qualquer canal.
> Fix: condicional em `open_task`:
> `if channel == Channel.ROCKETCHAT: rc_room_id = await rc.ensure_room(...)`

---

## STEP-008 — `docs/gotchas/staging-deploy.md`

Entradas obrigatórias:

**`git push` antes do deploy no VPS — sempre**
> Situação: commits existiam apenas nas máquinas dos devs. VPS fez `git pull`
> e continuou na versão antiga. `staging_update.sh` reportou "already up to date".
> Fix: dev que commitou a última DEM faz `git push origin main` ANTES de
> pedir ao DEV-3/4 para fazer o deploy.

**`docker-entrypoint-initdb.d` só roda no PRIMEIRO boot do Postgres**
> Situação: `infra/init-db/03_listmonk.sql` existe no repo mas o banco `listmonk`
> não foi criado no VPS porque o volume Postgres já existia.
> Fix: criar o banco manualmente com `docker compose exec postgres psql -U postgres -c "CREATE DATABASE listmonk;"`.
> Para reset completo: `docker compose down -v && docker compose up -d`.

**`infra/letsencrypt/` suja o working tree do VPS**
> Situação: Traefik gera `infra/letsencrypt/` em runtime. `git status` mostra `??`.
> Fix: `echo "infra/letsencrypt/" >> .gitignore` e commitar.

**Senha com caracteres especiais quebra URIs de conexão**
> Situação: `POSTGRES_PASSWORD` com `@`, `#`, `!` quebra Prisma/SQLAlchemy
> quando interpolado em `postgresql://user:PASS@host/db`.
> Fix: criar variável dedicada URL-encoded (`EVOLUTION_DB_PASS=SenhaSimples`)
> ou usar `urllib.parse.quote_plus(password)` no Python.

**Portas publicadas vs portas internas — não confundir**
> Listmonk: `9001:9000` (host:container). Smoke test usa `localhost:9001`, não `9000`.
> Evolution API: `8081:8080`. Smoke test usa `localhost:8081`.

---

## STEP-009 — `docs/gotchas/keycloak-auth.md`

Entradas obrigatórias:

**`VITE_KEYCLOAK_URL` ausente quebra login silenciosamente**
> Symptoma: OIDC authority `undefined`, login redireciona para URL errada.
> Fix: verificar `.env` de cada frontend antes do build.

**`redirect_uri` deve apontar para a raiz da SPA, não para `/callback`**
> Situação: SPAs React sem SSR não têm rota `/callback` — o OIDC callback
> deve ir para `/` e o handler de OIDC captura o código na query string.
> Fix: `redirect_uri = https://dominio.com/gestor-ui/` (com barra final).

**Roles no JWT — CLINICO ausente nos endpoints GET do CarePlanner**
> Situação: endpoints `GET /careplanner/*` só aceitavam role GESTOR.
> Symptoma: clínico autenticado recebe 403 em endpoints de leitura.
> Fix: adicionar `Role.CLINICO` à lista de roles permitidas nos decorators.

---

## STEP-010 — Template HANDOFF.yml

Criar `docs/demandas/_templates/HANDOFF.yml`:

```yaml
# HANDOFF — preenchido pelo dev ao finalizar a DEM
dem: DEM-NNN
titulo: ""
dev: ""          # DEV-1 / DEV-2 / CODEX / DEV-3/4
timestamp: ""    # ISO 8601
status: ""       # committed / partial / blocked

commit: ""       # hash curto
branch: main

files_changed:
  - ""

tests_passed: ""  # ex: "4/4" ou "53 passed"

pending_actions: []
  # - descrição da ação pendente

notes: ""
  # Decisões técnicas relevantes, gotchas encontrados,
  # o que o próximo dev precisa saber antes de continuar.

regressao_risco: []
  # Arquivos/módulos que podem ter sido afetados indiretamente
```

---

## STEP-011 — Commit

```
docs: DEM-INF memória operacional — patterns, gotchas, HANDOFF template
```

Arquivos:
```
docs/patterns/README.md
docs/patterns/backend-modules.md
docs/patterns/frontend-pages.md
docs/patterns/workers-webhooks.md
docs/gotchas/README.md
docs/gotchas/careplanner.md
docs/gotchas/staging-deploy.md
docs/gotchas/keycloak-auth.md
docs/demandas/_templates/HANDOFF.yml
```

## Critério de aceite

`docs/gotchas/careplanner.md` tem a entrada sobre `CareplannerService.__init__`.
`docs/gotchas/staging-deploy.md` tem a entrada sobre `git push antes do deploy`.
Nenhum arquivo tem conteúdo placeholder — todo texto é baseado em situação real do projeto.
