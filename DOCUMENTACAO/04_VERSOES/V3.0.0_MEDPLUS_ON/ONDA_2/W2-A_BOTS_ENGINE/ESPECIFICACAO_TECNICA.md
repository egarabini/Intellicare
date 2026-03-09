# 🔧 W2-A — Especificação Técnica: Bots Engine

## 1. Arquitetura

```
intellicare-core/
├── intellicare_core/
│   ├── bots/                       # [NOVO] Package de Bots
│   │   ├── __init__.py
│   │   ├── models.py               # SQLAlchemy models (Bot, BotExecution)
│   │   ├── executor.py             # Orquestrador de execução
│   │   ├── sandbox.py              # Sandbox Python (RestrictedPython)
│   │   ├── context.py              # BotExecutionContext
│   │   ├── client.py               # IntelliCareClient (FHIR client scoped)
│   │   ├── secrets_manager.py      # Gestão de secrets por tenant/bot
│   │   └── audit.py                # AuditEvent para execuções
│   └── subscriptions/
│       └── channels/
│           └── bot_channel.py      # Atualização do stub da Onda 1
```

## 2. Modelos de Dados

```sql
CREATE TABLE bots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    code TEXT NOT NULL,                    -- Código Python do bot
    code_version INT DEFAULT 1,
    runtime TEXT DEFAULT 'sandbox',       -- sandbox | subprocess
    status TEXT DEFAULT 'active',         -- active | inactive
    run_as_user BOOLEAN DEFAULT false,    -- Usar permissões do trigger ou do bot
    timeout_seconds INT DEFAULT 30,
    created_by TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE bot_secrets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL,
    bot_id UUID REFERENCES bots(id),     -- NULL = secret global do tenant
    name TEXT NOT NULL,
    value_encrypted TEXT NOT NULL,        -- Encrypted via Fernet
    UNIQUE(tenant_id, bot_id, name)
);

CREATE TABLE bot_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bot_id UUID NOT NULL REFERENCES bots(id),
    tenant_id TEXT NOT NULL,
    subscription_id UUID,
    input_resource_type TEXT,
    input_resource_id TEXT,
    interaction TEXT,                     -- create, update, delete
    success BOOLEAN NOT NULL,
    log_output TEXT,
    duration_ms INT,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_exec_bot ON bot_executions(bot_id, created_at DESC);
```

## 3. Sandbox Python (`sandbox.py`)

```python
from RestrictedPython import compile_restricted, safe_globals, safe_builtins

ALLOWED_IMPORTS = {
    "json", "datetime", "math", "re", "hashlib",
    "collections", "itertools", "functools", "typing",
}

class BotSandbox:
    """Executa código Python em ambiente restrito."""
    
    def execute(
        self,
        code: str,
        context: BotExecutionContext,
        timeout: int = 30,
    ) -> BotExecutionResult:
        compiled = compile_restricted(code, '<bot>', 'exec')
        
        restricted_globals = {
            **safe_globals,
            '__builtins__': {**safe_builtins, '__import__': self._restricted_import},
            'input': context.input_resource,
            'client': context.fhir_client,
            'secrets': context.secrets,
            'event': context.event_metadata,
            'print': context.logger.info,
        }
        
        result = run_with_timeout(
            lambda: exec(compiled, restricted_globals),
            timeout=timeout,
        )
        return result
```

## 4. Bot Execution Context (`context.py`)

```python
@dataclass
class BotExecutionContext:
    input_resource: dict           # Recurso FHIR que trigou o bot
    fhir_client: IntelliCareClient # Client autenticado scoped ao tenant
    secrets: dict                  # Secrets do bot/tenant
    event_metadata: EventMetadata  # subscription_id, interaction, etc.
    logger: BotLogger              # Logger que captura output
```

## 5. IntelliCare Client (`client.py`)

```python
class IntelliCareClient:
    """Client FHIR simplificado para uso em bots."""
    
    async def create(self, resource: dict) -> dict: ...
    async def read(self, resource_type: str, id: str) -> dict: ...
    async def update(self, resource: dict) -> dict: ...
    async def search(self, resource_type: str, params: dict) -> list: ...
    async def send_notification(self, channel: str, to: str, message: str) -> dict: ...
```

## 6. Integração com Subscriptions

```python
# intellicare_core/subscriptions/channels/bot_channel.py
class BotChannel:
    async def execute(self, subscription, resource, interaction):
        bot_id = extract_bot_id(subscription.channel_endpoint)
        bot = await load_bot(bot_id)
        
        context = BotExecutionContext(
            input_resource=resource,
            fhir_client=IntelliCareClient(tenant_id=subscription.tenant_id),
            secrets=await load_secrets(subscription.tenant_id, bot_id),
            event_metadata=EventMetadata(
                subscription_id=subscription.id,
                interaction=interaction,
            ),
            logger=BotLogger(),
        )
        
        sandbox = BotSandbox()
        result = sandbox.execute(bot.code, context, bot.timeout_seconds)
        
        await save_execution_log(bot, result)
        await create_audit_event(bot, resource, result)
        return result
```

## 7. Plano de Implementação

### Sprint 1 (7 dias)
- **Dia 1-2:** Models + migrations + CRUD API de bots
- **Dia 3-4:** Sandbox Python (RestrictedPython) + testes de segurança
- **Dia 5-6:** IntelliCareClient + BotExecutionContext + integração com Subscriptions
- **Dia 7:** Secrets manager (Fernet encryption) + testes e2e

### Sprint 2 (7 dias)
- **Dia 8-9:** AuditEvent + logs + métricas Prometheus
- **Dia 10-11:** UI no Gestor (editor de bot, logs, enable/disable)
- **Dia 12-13:** 5 bots exemplo (glicose alta, welcome, lab result, etc.)
- **Dia 14:** Documentação + code review + merge
