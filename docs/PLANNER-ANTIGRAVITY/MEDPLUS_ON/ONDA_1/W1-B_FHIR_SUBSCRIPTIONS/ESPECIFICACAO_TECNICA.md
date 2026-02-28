# 🔧 W1-B — Especificação Técnica: FHIR Subscriptions Engine

## 1. Arquitetura

```
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│  Qualquer Módulo │────▶│  Subscription    │────▶│  Redis Queue     │
│  (cria recurso)  │     │  Evaluator       │     │  (Celery)        │
└──────────────────┘     └──────────────────┘     └────────┬─────────┘
                                                           │
                         ┌─────────────────────────────────┼─────────┐
                         │                                 │         │
                    ┌────▼─────┐  ┌──────────────┐  ┌─────▼────┐
                    │ REST-Hook│  │  WebSocket   │  │   Bot    │
                    │ Worker   │  │  Publisher   │  │  Worker  │
                    └────┬─────┘  └──────┬───────┘  └─────┬────┘
                         │               │                 │
                    ┌────▼─────┐  ┌──────▼───────┐  ┌─────▼────┐
                    │ External │  │  Connected   │  │  Bot     │
                    │ Webhook  │  │  Clients     │  │  Engine  │
                    └──────────┘  └──────────────┘  └──────────┘
```

### 1.1 Localização no Código

```
intellicare-core/
├── intellicare_core/
│   ├── subscriptions/              # [NOVO] Package de subscriptions
│   │   ├── __init__.py
│   │   ├── evaluator.py            # Avalia se recurso bate com critério
│   │   ├── matcher.py              # Match de FHIR Search criteria
│   │   ├── dispatcher.py           # Despacha para canal correto
│   │   ├── channels/
│   │   │   ├── __init__.py
│   │   │   ├── rest_hook.py        # REST-hook (webhook) channel
│   │   │   ├── websocket_channel.py # WebSocket channel
│   │   │   └── bot_channel.py      # Bot channel (stub para Onda 2)
│   │   ├── workers.py              # Celery workers
│   │   ├── models.py               # SQLAlchemy models
│   │   └── audit.py                # AuditEvent helper

intellicare-comunicacao/
├── comunicacao/
│   ├── subscriptions/              # [NOVO] WebSocket endpoint
│   │   └── ws_handler.py           # WebSocket connection manager
```

### 1.2 Dependências Novas

```toml
# intellicare-core/pyproject.toml
[project.optional-dependencies]
subscriptions = [
    "celery[redis]>=5.3",
    "httpx>=0.25",              # Para REST-hook calls (async)
]
```

---

## 2. Modelos de Dados

### 2.1 Tabela `fhir_subscriptions`

```sql
CREATE TABLE fhir_subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL,
    resource_json JSONB NOT NULL,          -- Subscription FHIR completo
    status TEXT NOT NULL DEFAULT 'requested',  -- requested, active, off, error
    channel_type TEXT NOT NULL,            -- rest-hook, websocket, bot
    channel_endpoint TEXT,                 -- URL do webhook ou Bot/{id}
    criteria TEXT NOT NULL,                -- "Observation?code=glucose"
    criteria_resource_type TEXT NOT NULL,  -- "Observation" (extraído do criteria)
    hmac_secret TEXT,                      -- Secret para assinatura HMAC
    max_attempts INT DEFAULT 4,
    error_count INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT chk_status CHECK (status IN ('requested', 'active', 'off', 'error'))
);

CREATE INDEX idx_sub_tenant_status ON fhir_subscriptions(tenant_id, status);
CREATE INDEX idx_sub_criteria_type ON fhir_subscriptions(criteria_resource_type, status);
```

### 2.2 Tabela `fhir_subscription_audit`

```sql
CREATE TABLE fhir_subscription_audit (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subscription_id UUID NOT NULL REFERENCES fhir_subscriptions(id),
    tenant_id TEXT NOT NULL,
    resource_type TEXT NOT NULL,
    resource_id TEXT NOT NULL,
    interaction TEXT NOT NULL,             -- create, update, delete
    attempt INT NOT NULL,
    outcome TEXT NOT NULL,                 -- success, minor-failure, serious-failure
    status_code INT,                       -- HTTP status code (para rest-hook)
    diagnostics TEXT,
    duration_ms INT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_audit_sub ON fhir_subscription_audit(subscription_id, created_at);
```

---

## 3. Componentes Principais

### 3.1 Subscription Evaluator (`evaluator.py`)

```python
class SubscriptionEvaluator:
    """
    Ponto de entrada: chamado por qualquer módulo quando um recurso é criado/atualizado/deletado.
    """
    
    def __init__(self, db: AsyncSession, redis: Redis):
        self.db = db
        self.redis = redis
        self.matcher = FHIRCriteriaMatcher()
    
    async def evaluate(
        self,
        resource: dict,
        resource_type: str,
        interaction: Literal["create", "update", "delete"],
        tenant_id: str,
        previous_version: Optional[dict] = None,
    ) -> int:
        """
        1. Buscar subscriptions ativas para este resource_type e tenant
        2. Para cada, verificar se o critério bate
        3. Enfileirar job para cada match
        4. Retornar quantidade de jobs enfileirados
        """
        if resource_type == "AuditEvent":
            return 0  # Nunca disparar para AuditEvents
        
        subscriptions = await self._get_active_subscriptions(
            tenant_id, resource_type
        )
        
        jobs_queued = 0
        ws_events = []
        
        for sub in subscriptions:
            if self.matcher.matches(resource, sub.criteria):
                if sub.channel_type == "websocket":
                    ws_events.append(sub)
                else:
                    await self._enqueue_job(sub, resource, interaction)
                    jobs_queued += 1
        
        if ws_events:
            await self._publish_websocket(resource, ws_events)
        
        return jobs_queued
```

### 3.2 FHIR Criteria Matcher (`matcher.py`)

```python
class FHIRCriteriaMatcher:
    """
    Avalia se um recurso FHIR bate com um critério de Subscription.
    Critério é um FHIR Search string: "Observation?code=glucose&value-quantity=gt200"
    """
    
    def matches(self, resource: dict, criteria: str) -> bool:
        resource_type, params = self._parse_criteria(criteria)
        
        if resource.get("resourceType") != resource_type:
            return False
        
        for param_name, param_value in params.items():
            if not self._matches_param(resource, param_name, param_value):
                return False
        
        return True
    
    def _matches_param(self, resource: dict, name: str, value: str) -> bool:
        """Avalia um parâmetro de busca contra o recurso."""
        # Suporta: code, status, subject, value-quantity, etc.
        # Operadores: gt, lt, ge, le, eq, ne
        ...
    
    def _parse_criteria(self, criteria: str) -> Tuple[str, dict]:
        """Parse 'Observation?code=glucose&status=final' → ('Observation', {code: glucose, status: final})"""
        ...
```

### 3.3 REST-Hook Channel (`channels/rest_hook.py`)

```python
class RestHookChannel:
    """Envia recurso FHIR via HTTP POST para endpoint configurado."""
    
    async def send(
        self,
        subscription: SubscriptionModel,
        resource: dict,
        interaction: str,
        attempt: int,
    ) -> ChannelResult:
        headers = self._build_headers(subscription, resource, interaction)
        body = json.dumps(resource)
        
        if subscription.hmac_secret:
            headers["X-Signature"] = hmac.new(
                subscription.hmac_secret.encode(),
                body.encode(),
                hashlib.sha256
            ).hexdigest()
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                subscription.channel_endpoint,
                content=body,
                headers=headers,
            )
        
        return ChannelResult(
            success=200 <= response.status_code < 300,
            status_code=response.status_code,
        )
    
    def _build_headers(self, sub, resource, interaction) -> dict:
        return {
            "Content-Type": "application/fhir+json",
            "X-IntelliCare-Subscription": str(sub.id),
            "X-IntelliCare-Interaction": interaction,
            **self._parse_custom_headers(sub.resource_json),
        }
```

### 3.4 WebSocket Channel (`channels/websocket_channel.py`)

```python
class WebSocketChannel:
    """Publica no Redis Pub/Sub para clients WebSocket conectados."""
    
    async def publish(
        self,
        redis: Redis,
        resource: dict,
        subscriptions: List[SubscriptionModel],
        tenant_id: str,
    ):
        message = {
            "resource": resource,
            "events": [
                {"subscription_id": s.id, "criteria": s.criteria}
                for s in subscriptions
            ],
        }
        channel = f"intellicare:subscriptions:{tenant_id}:websockets"
        await redis.publish(channel, json.dumps(message))
```

### 3.5 Celery Worker (`workers.py`)

```python
from celery import Celery

app = Celery("subscriptions", broker="redis://localhost:6379/0")

@app.task(
    bind=True,
    max_retries=19,
    default_retry_delay=1,
    retry_backoff=True,
    retry_backoff_max=262144,  # ~73 horas
)
def process_subscription_job(self, job_data: dict):
    """
    Processa um job de subscription:
    1. Carregar subscription (verificar se ainda ativa)
    2. Carregar recurso (verificar se é versão atual)
    3. Despachar para canal correto (rest-hook ou bot)
    4. Registrar AuditEvent
    5. Em caso de falha, retry com backoff
    """
    subscription = load_subscription(job_data["subscription_id"])
    if not subscription or subscription.status != "active":
        return  # Subscription desactivada, parar
    
    resource = load_resource(job_data["resource_type"], job_data["resource_id"])
    
    channel = get_channel(subscription.channel_type)
    result = channel.send(subscription, resource, job_data["interaction"])
    
    create_audit_event(subscription, resource, result)
    
    if not result.success:
        max_attempts = subscription.max_attempts or 4
        if self.request.retries < max_attempts:
            raise self.retry(countdown=2 ** self.request.retries)
```

---

## 4. Integração com Módulos Existentes

### 4.1 Hook Point nos Módulos

Cada módulo que cria/atualiza recursos FHIR deve chamar o evaluator:

```python
# Em qualquer módulo ao criar/atualizar recurso FHIR
from intellicare_core.subscriptions import evaluate_subscriptions

# Após salvar o recurso no banco:
await evaluate_subscriptions(
    resource=saved_resource,
    resource_type="Observation",
    interaction="create",
    tenant_id=current_tenant.id,
)
```

### 4.2 Integração com Grahame (CDR)

O hook principal fica no **Grahame** (FHIR server), que é o ponto central de CRUD:

```python
# grahame/fhir/crud.py
async def create_resource(resource_type, data, tenant_id):
    saved = await db.create(data)
    await evaluate_subscriptions(saved, resource_type, "create", tenant_id)
    return saved

async def update_resource(resource_type, id, data, tenant_id):
    previous = await db.read(id)
    saved = await db.update(id, data)
    await evaluate_subscriptions(saved, resource_type, "update", tenant_id, previous)
    return saved
```

---

## 5. WebSocket Endpoint

```python
# comunicacao/subscriptions/ws_handler.py
from fastapi import WebSocket

@router.websocket("/ws/subscriptions")
async def subscription_websocket(
    websocket: WebSocket,
    criteria: str,          # "Observation?code=glucose"
    token: str,             # JWT para autenticação
):
    tenant_id = validate_token(token)
    await websocket.accept()
    
    # Registrar subscription no Redis
    sub_id = register_ws_subscription(tenant_id, criteria)
    
    # Escutar Redis Pub/Sub
    channel = f"intellicare:subscriptions:{tenant_id}:websockets"
    async for message in redis_subscribe(channel):
        # Filtrar por subscription_id
        if matches_subscription(message, sub_id):
            await websocket.send_json(message["resource"])
```

---

## 6. Testes

- Testes unitários do `FHIRCriteriaMatcher` (15+ cenários de critériosinórios)
- Testes do `SubscriptionEvaluator` (enfileiramento correto)
- Testes do `RestHookChannel` com mock HTTP
- Testes de retry com backoff
- Testes de HMAC signature
- Testes de multi-tenancy (Subscriptions isoladas)
- Testes de WebSocket (conexão, recepção de mensagem, desconexão)
- Teste de AuditEvent (geração correta em sucesso e falha)
