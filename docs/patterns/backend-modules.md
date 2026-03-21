# Backend Modules

Padroes observados principalmente em DEM-003, DEM-037, DEM-038, DEM-041, DEM-047, DEM-048 e DEM-049.

## Modulo FastAPI carregado dinamicamente

### Estrutura que ja esta institucionalizada
- O core carrega modulos pelo `ModuleLoader` em [`packages/intellicare-core/intellicare_core/module_loader/loader.py`](/c:/Users/egara/INTELLICARE/packages/intellicare-core/intellicare_core/module_loader/loader.py), usando `AVAILABLE_MODULES` e `app.include_router(instance.get_router(), prefix=f"/{module_name}")`.
- O ponto de entrada do servico em [`packages/intellicare-core/intellicare_core/main.py`](/c:/Users/egara/INTELLICARE/packages/intellicare-core/intellicare_core/main.py) chama `loader.load(...)` e executa `startup()` de cada modulo no `lifespan`.
- No CarePlanner, o modulo expoe `Module(BaseModule)` em [`modules/careplanner/main.py`](/c:/Users/egara/INTELLICARE/modules/careplanner/main.py) e o router fica isolado em [`modules/careplanner/api/routes.py`](/c:/Users/egara/INTELLICARE/modules/careplanner/api/routes.py).

### Implicacao pratica
- Quando um modulo novo entrar no projeto, ele precisa expor `Module`, implementar `get_router()` e ser adicionado ao `AVAILABLE_MODULES`; so criar `router.py` nao o torna acessivel.
- O prefixo de rota nasce no loader, nao dentro do proprio modulo. Por isso os routers internos usam caminhos relativos como `/tasks` e `/consultations/video`, e a URL final vira `/<modulo>/...`.

## Settings via pydantic-settings, nunca hardcoded

### Evidencia concreta
- [`modules/careplanner/config.py`](/c:/Users/egara/INTELLICARE/modules/careplanner/config.py) usa `BaseSettings` e `SettingsConfigDict`, lendo `infra/.env` pela `REPO_ROOT`.
- O core faz o mesmo em [`packages/intellicare-core/intellicare_core/config/settings.py`](/c:/Users/egara/INTELLICARE/packages/intellicare-core/intellicare_core/config/settings.py).
- DEM-047/048/049 cresceram `CareplannerSettings` com `evolution_*`, `listmonk_*` e `jasmin_*` em vez de esconder URL e segredo dentro de adapter.

### Regra
- Toda dependencia externa nova entra primeiro em `config.py`.
- Service e adapter recebem settings injetados; se um valor esta direto no corpo de um metodo, o padrao foi quebrado.

## Migration por SQL idempotente no startup

### Como o projeto faz hoje
- O CarePlanner executa migracoes por tenant no `startup()` em [`modules/careplanner/main.py`](/c:/Users/egara/INTELLICARE/modules/careplanner/main.py).
- O SQL fica centralizado em [`modules/careplanner/migrations.py`](/c:/Users/egara/INTELLICARE/modules/careplanner/migrations.py) com `CREATE TABLE IF NOT EXISTS` e `CREATE INDEX IF NOT EXISTS`.
- DEM-037 seguiu a mesma linha para plataforma com `ADD COLUMN IF NOT EXISTS gestor_email` em [`docs/demandas/DEM-037_ADMINUI_FIXES/02_TECNICA.md`](/c:/Users/egara/INTELLICARE/docs/demandas/DEM-037_ADMINUI_FIXES/02_TECNICA.md).

### Regra
- Migration de modulo precisa ser idempotente. O staging e os testes reexecutam startup varias vezes.
- Se a mudanca for multi-tenant, ela precisa rodar dentro do schema do tenant, nao so em `public`.

## Seed no startup sem travar o boot

### Caso real
- DEM-041 adicionou `seed_default_templates` e o `startup()` do CarePlanner passou a semear templates padrao por tenant depois das migracoes.
- Em [`modules/careplanner/services.py`](/c:/Users/egara/INTELLICARE/modules/careplanner/services.py), a estrategia equivalente a `ON CONFLICT DO NOTHING` aparece com `try/except` para duplicidade, evitando falha no boot.

### Regra
- Seed padrao precisa ser reexecutavel.
- Erro de seed deve ser logado com contexto; nao pode derrubar o modulo inteiro por dado ja existente.

## Repositorio fino, service com orquestracao

### Evidencia concreta
- [`modules/careplanner/repository.py`](/c:/Users/egara/INTELLICARE/modules/careplanner/repository.py) concentra SQL, transicoes e consultas cross-tenant.
- [`modules/careplanner/services.py`](/c:/Users/egara/INTELLICARE/modules/careplanner/services.py) concentra decisao de canal, eventos, integracao com Kestra, Jitsi, Rocket.Chat e metricas.

### Regra
- Query complexa, `tenant_session`, `text()` e mapping ficam no repositorio.
- Orquestracao entre adapters, regras de status e side effects ficam em service.
- Nao importar service dentro de contract ou schema.

## Teste async de integracao precisa acompanhar o construtor

### Caso real que se repetiu
- DEM-047, DEM-048 e DEM-049 aumentaram o `__init__` de `CareplannerService` com `whatsapp`, `email` e `sms`.
- O impacto bateu em `packages/intellicare-core/tests`, porque fixtures antigas instanciavam `CareplannerService` sem os novos adapters e quebravam com `TypeError`.

### Regra
- Toda mudanca de assinatura em service compartilhado exige busca global nas fixtures.
- O atalho operacional valido continua sendo:

```bash
rg -n "CareplannerService\\(" packages/intellicare-core/tests
```

- Quando o service cresce, as fixtures precisam receber `MagicMock()` ou adapter fake para todos os parametros novos.
