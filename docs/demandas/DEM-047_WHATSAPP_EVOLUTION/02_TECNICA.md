---
tipo: especificacao-tecnica
demanda: DEM-047
titulo: WhatsApp como Canal CarePlanner via Evolution API
---

# DEM-047 — Especificação Técnica

## Mapa de mudanças

| Arquivo | Tipo | O que muda |
|---------|------|-----------|
| `modules/careplanner/contracts.py` | Modificar | `Channel.WHATSAPP = "whatsapp"` |
| `modules/careplanner/config.py` | Modificar | Settings Evolution API |
| `modules/careplanner/adapters/whatsapp.py` | **Novo** | `WhatsAppAdapter` |
| `modules/careplanner/services.py` | Modificar | Roteamento por canal no dispatch |
| `modules/careplanner/api/routes.py` | Modificar | Webhook WA + channel no TriggerRequest |
| `modules/careplanner/main.py` | Modificar | Seed templates WA no startup |
| `modules/careplanner/workers/dispatcher.py` | Modificar | Roteamento por canal |
| `infra/docker-compose.yml` | Modificar | Serviço `evolution-api` |
| `infra/kestra/flows/careplanner_jornada_whatsapp.yml` | **Novo** | Flow Kestra WA |
| `infra/.env.staging.example` | Modificar | Vars Evolution API |
| `frontend/GestorUI/src/components/TriggerJourneyModal.tsx` | Modificar | Seletor de canal |
| `packages/intellicare-core/tests/test_careplanner_phase_h.py` | **Novo** | 4 testes |

**Sem nova migration** — `channel` já é coluna existente em `care_tasks` e
`care_conversations`; `rc_room_id` já é nullable em `care_conversations`.

---

## Bloco 1 — `contracts.py`: adicionar WHATSAPP ao Channel

```python
class Channel(StrEnum):
    ROCKETCHAT = "rocketchat"
    WHATSAPP = "whatsapp"        # <- novo
```

---

## Bloco 2 — `config.py`: settings Evolution API

```python
class CareplannerSettings(BaseSettings):
    # ... settings existentes ...

    # Evolution API (WhatsApp)
    evolution_api_url: str = "http://evolution-api:8080"
    evolution_api_key: str = ""
    evolution_instance_name: str = "intellicare"
    evolution_webhook_secret: str = ""   # para verificação HMAC (opcional)
    evolution_max_retries: int = 3
```

---

## Bloco 3 — `adapters/whatsapp.py` (novo arquivo completo)

```python
"""Adapter async para integracao com WhatsApp via Evolution API."""
from __future__ import annotations

import logging
from typing import Any

import httpx

from ..config import CareplannerSettings

logger = logging.getLogger(__name__)


class WhatsAppAdapter:
    """Cliente async para Evolution API — envia/recebe via WhatsApp."""

    def __init__(self, settings: CareplannerSettings) -> None:
        self._settings = settings
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self._settings.evolution_api_url.rstrip("/"),
                headers={"apikey": self._settings.evolution_api_key},
                timeout=30.0,
            )
        return self._client

    def _normalize_phone(self, phone_e164: str) -> str:
        """Remove + e retorna apenas dígitos. Ex: +5511999999999 → 5511999999999"""
        return phone_e164.lstrip("+")

    async def send_message(self, phone_e164: str, text: str) -> dict[str, Any]:
        """Envia mensagem de texto para o número E.164 via Evolution API."""
        client = await self._get_client()
        instance = self._settings.evolution_instance_name
        phone = self._normalize_phone(phone_e164)

        for attempt in range(1, self._settings.evolution_max_retries + 1):
            try:
                response = await client.post(
                    f"/message/sendText/{instance}",
                    json={
                        "number": phone,
                        "textMessage": {"text": text},
                    },
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code >= 500 and attempt < self._settings.evolution_max_retries:
                    import asyncio
                    await asyncio.sleep(0.5 * (2 ** (attempt - 1)))
                    continue
                raise
        raise httpx.HTTPError(f"Evolution API falhou após {self._settings.evolution_max_retries} tentativas")

    def extract_phone_from_jid(self, remote_jid: str) -> str:
        """Extrai número de telefone do JID do WhatsApp.
        Ex: '5511999999999@s.whatsapp.net' → '5511999999999'
        """
        return remote_jid.split("@")[0]

    def verify_webhook_secret(self, token: str) -> bool:
        """Verifica token simples no path do webhook."""
        secret = self._settings.evolution_webhook_secret
        if not secret:
            return True   # sem configuração, aceita (dev/staging sem segredo)
        return token == secret

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
```

---

## Bloco 4 — `services.py`: roteamento por canal no dispatch

### 4a — Adicionar WhatsAppAdapter ao `__init__` do `CareplannerService`

```python
from .adapters.whatsapp import WhatsAppAdapter

class CareplannerService:
    def __init__(
        self,
        repo: CareplannerRepository,
        rc: RocketChatAdapter,
        jitsi: JitsiAdapter,
        kestra: KestraAdapter,
        whatsapp: WhatsAppAdapter,           # <- novo
        settings: CareplannerSettings | None = None,
    ) -> None:
        self._repo = repo
        self._rc = rc
        self._jitsi = jitsi
        self._kestra = kestra
        self._whatsapp = whatsapp             # <- novo
        self._settings = settings or get_careplanner_settings()
```

### 4b — Modificar `dispatch_task` para rotear por canal

Localizar o método que efetivamente envia a mensagem ao paciente (chamado
pelo `dispatcher.py`). Atualmente chama `rc.post_message`. Alterar para:

```python
async def _send_to_channel(
    self,
    channel: Channel,
    rc_room_id: str | None,
    phone_e164: str | None,
    text: str,
) -> dict[str, Any]:
    if channel == Channel.WHATSAPP:
        if not phone_e164:
            raise ValueError("phone_e164 obrigatorio para canal WHATSAPP")
        return await self._whatsapp.send_message(phone_e164, text)
    else:
        if not rc_room_id:
            raise ValueError("rc_room_id obrigatorio para canal ROCKETCHAT")
        return await self._rc.post_message(rc_room_id, text)
```

Substituir a chamada direta a `rc.post_message` por `_send_to_channel(...)`.

### 4c — `open_task` para WhatsApp — sem criar room no RC

Localizar em `open_task` o trecho que chama `rc.ensure_room`. Adicionar
condicional:

```python
if channel == Channel.WHATSAPP:
    rc_room_id = None   # WhatsApp não usa RC room
else:
    rc_room_id = await self._rc.ensure_room(ctx.tenant_id, patient_ref)
```

---

## Bloco 5 — `api/routes.py`: webhook WhatsApp + channel no TriggerRequest

### 5a — Adicionar `channel` ao `TriggerJourneyRequest`

```python
class TriggerJourneyRequest(BaseModel):
    patient_ref: str
    task_type: str
    template_code: str | None = None
    clinico_ref: str | None = None
    include_video: bool = False
    contact_phone_e164: str | None = None
    channel: Channel = Channel.ROCKETCHAT    # <- novo (default mantém compatibilidade)
```

### 5b — Novo endpoint webhook WhatsApp

```python
@router.post("/webhook/whatsapp/{token}", status_code=status.HTTP_200_OK)
async def whatsapp_webhook(
    token: str,
    request: Request,
    service: CareplannerService = Depends(get_service),
) -> dict:
    """Recebe eventos inbound do WhatsApp via Evolution API."""
    body = await request.json()

    # Verificar token de segurança
    settings = get_careplanner_settings()
    wa = WhatsAppAdapter(settings)
    if not wa.verify_webhook_secret(token):
        raise api_error(401, "unauthorized", "Token invalido")

    # Processar apenas eventos de mensagem recebida
    event = body.get("event", "")
    if event != "messages.upsert":
        return {"status": "ignored", "event": event}

    data = body.get("data", {})
    key = data.get("key", {})

    # Ignorar mensagens enviadas pelo bot (fromMe=True)
    if key.get("fromMe", False):
        return {"status": "ignored", "reason": "fromMe"}

    remote_jid = key.get("remoteJid", "")
    phone = wa.extract_phone_from_jid(remote_jid)
    message_obj = data.get("message", {})
    text = (
        message_obj.get("conversation")
        or message_obj.get("extendedTextMessage", {}).get("text")
        or ""
    )

    if not phone or not text:
        return {"status": "ignored", "reason": "sem phone ou texto"}

    # Processar como inbound — mesmo handler do RC
    # Criar TenantContext mínimo para buscar a tarefa pelo phone
    # O service.handle_whatsapp_inbound busca care_conversation pelo phone_e164
    await service.handle_whatsapp_inbound(phone=phone, text=text)
    return {"status": "ok"}
```

### 5c — Adicionar `handle_whatsapp_inbound` no `services.py`

```python
async def handle_whatsapp_inbound(self, phone: str, text: str) -> None:
    """Processa mensagem inbound WhatsApp — identifica tarefa pelo phone_e164."""
    phone_e164 = f"+{phone}"
    # Buscar conversa ativa pelo phone em todos os tenants
    # (WhatsApp não tem tenant no webhook — buscar pelo phone globalmente)
    correlation_id = await self._repo.find_active_task_by_phone(phone_e164)
    if not correlation_id:
        logger.warning("WhatsApp inbound órfão: phone=%s", phone)
        careplanner_orphan_inbound_total.labels(tenant_slug="unknown").inc()
        return

    tenant_slug = await self._repo.get_tenant_by_correlation(correlation_id)
    ctx = TenantContext.from_slug(slug=tenant_slug, user_id="system", roles=[])
    # Reutilizar handle_inbound existente
    await self.handle_inbound(ctx=ctx, correlation_id=correlation_id, content=text)
```

---

## Bloco 6 — `repository.py`: 2 métodos novos

```python
async def find_active_task_by_phone(self, phone_e164: str) -> UUID | None:
    """Busca correlation_id de tarefa ativa pelo phone_e164 (cross-tenant)."""
    # Busca na tabela global (sem schema de tenant) — usar information_schema
    # para listar schemas e varrer. OU: adicionar tabela global de index.
    # Solução simples: varrer todos os tenants ativos.
    tenants = await self._get_active_tenant_slugs()
    for slug in tenants:
        async with engine_session(slug) as db:
            row = (await db.execute(text("""
                SELECT ct.correlation_id
                FROM care_conversations cc
                JOIN care_tasks ct ON ct.correlation_id = cc.correlation_id
                WHERE cc.phone_e164 = :phone
                  AND ct.status NOT IN ('CLOSED', 'FAILED', 'EXPIRED')
                  AND ct.channel = 'whatsapp'
                ORDER BY ct.created_at DESC
                LIMIT 1
            """), {"phone": phone_e164})).mappings().first()
            if row:
                return row["correlation_id"]
    return None

async def get_tenant_by_correlation(self, correlation_id: UUID) -> str:
    """Retorna tenant_slug de uma care_task pelo correlation_id."""
    tenants = await self._get_active_tenant_slugs()
    for slug in tenants:
        async with engine_session(slug) as db:
            row = (await db.execute(text("""
                SELECT tenant_slug FROM care_tasks
                WHERE correlation_id = :cid LIMIT 1
            """), {"cid": str(correlation_id)})).mappings().first()
            if row:
                return row["tenant_slug"]
    raise ValueError(f"Tenant nao encontrado para correlation_id={correlation_id}")
```

⚠️ `_get_active_tenant_slugs()` provavelmente já existe no repositório para
o `expiry_worker`. Verificar e reutilizar.

---

## Bloco 7 — `main.py`: seed templates WhatsApp no startup

Adicionar ao método `seed_default_templates` (ou criar `seed_whatsapp_templates`
chamado logo após):

```python
WHATSAPP_TEMPLATES = [
    ("boas_vindas_wa",           "whatsapp", "Olá {{nome_paciente}}! Bem-vindo ao IntelliCare. Como posso ajudá-lo hoje?"),
    ("check_in_wa",              "whatsapp", "Olá {{nome_paciente}}! Como você está se sentindo hoje? Responda com um número de 1 a 10."),
    ("lembrete_medicacao_wa",    "whatsapp", "Lembrete: não esqueça de tomar sua medicação {{medicamento}} agora. ✅"),
    ("teleconsulta_confirmacao_wa", "whatsapp", "Sua teleconsulta está confirmada para {{data_hora}}. Link: {{link_video}}"),
]
for code, channel, content in WHATSAPP_TEMPLATES:
    try:
        await repo.create_template(ctx, CareTemplateCreate(
            template_code=code, channel=Channel(channel),
            content=content, variables=[], active=True,
        ))
    except Exception:
        pass  # ON CONFLICT DO NOTHING equivalente
```

---

## Bloco 8 — `workers/dispatcher.py`: roteamento por canal

Localizar onde o dispatcher chama `rc.post_message` (ou `service.dispatch_task`).
Adicionar leitura do campo `channel` da task antes de rotear:

```python
channel = Channel(task_row.get("channel", "rocketchat"))
# Usar service._send_to_channel(channel, rc_room_id, phone_e164, text)
```

---

## Bloco 9 — `infra/docker-compose.yml`: serviço Evolution API

### 9a — Script de init automático do banco `evolution`

O Evolution API v2.2.0 **cria as tabelas via migration interna**, mas **não cria
o database**. A solução é um script SQL que roda automaticamente na primeira
inicialização do container Postgres.

**Verificar** se `infra/docker-compose.yml` já monta o volume de init:
```yaml
postgres:
  volumes:
    - ./infra/init-db:/docker-entrypoint-initdb.d
```

Se o volume já existe, apenas criar o arquivo abaixo.
Se não existe, adicionar o volume ao serviço `postgres` (não remove os volumes
existentes, apenas acrescenta).

Criar `infra/init-db/02_evolution.sql`:
```sql
-- Cria banco 'evolution' se não existir (idempotente)
SELECT 'CREATE DATABASE evolution'
WHERE NOT EXISTS (
    SELECT FROM pg_database WHERE datname = 'evolution'
)\gexec
```

> O `\gexec` é específico do `psql` — o docker-entrypoint do postgres 16
> executa os scripts via psql, então funciona nativamente.

### 9b — Serviço `evolution-api`

Adicionar após o serviço `rocketchat`:

```yaml
evolution-api:
  image: atendai/evolution-api:v2.2.0
  container_name: intellicare_evolution
  restart: unless-stopped
  ports:
    - "8081:8080"
  environment:
    SERVER_URL: http://evolution-api:8080
    AUTHENTICATION_API_KEY: ${EVOLUTION_API_KEY}
    AUTHENTICATION_EXPOSE_IN_FETCH_INSTANCES: "true"
    DATABASE_PROVIDER: postgresql
    DATABASE_CONNECTION_URI: postgresql://postgres:${POSTGRES_PASSWORD}@postgres:5432/evolution
    DATABASE_CONNECTION_CLIENT_NAME: evolution_client
    WEBHOOK_GLOBAL_URL: http://intellicare-service:8000/api/v1/careplanner/webhook/whatsapp/${EVOLUTION_WEBHOOK_SECRET}
    WEBHOOK_GLOBAL_ENABLED: "true"
    WEBHOOK_EVENTS_MESSAGES_UPSERT: "true"
    WEBHOOK_EVENTS_CONNECTION_UPDATE: "false"
    WEBHOOK_EVENTS_QRCODE_UPDATED: "false"
  depends_on:
    - postgres
  networks:
    - intellicare_net
```

### 9c — `.env.staging.example`

Adicionar ao final do arquivo `infra/.env.staging.example`:
```
# Evolution API (WhatsApp)
EVOLUTION_API_KEY=change-me-strong-key
EVOLUTION_WEBHOOK_SECRET=change-me-strong-secret
EVOLUTION_INSTANCE_NAME=intellicare
EVOLUTION_API_URL=http://evolution-api:8080
```

### 9d — Mapa de arquivos deste bloco

```
infra/
├── init-db/
│   └── 02_evolution.sql     ← NOVO
├── docker-compose.yml        ← Modificar (volume init-db no postgres + serviço evolution-api)
└── .env.staging.example      ← Modificar (4 vars Evolution)
```

---

## Bloco 10 — Kestra flow WhatsApp

Criar `infra/kestra/flows/careplanner_jornada_whatsapp.yml`:

Idêntico ao `careplanner_jornada_basica.yml` com duas diferenças:
1. `id: careplanner_jornada_whatsapp`
2. No body do `open_task`, adicionar `"channel": "whatsapp"`

```yaml
id: careplanner_jornada_whatsapp
namespace: intellicare.careplanner
description: "Jornada CarePlanner via WhatsApp"

inputs:
  - id: tenant_slug
    type: STRING
  - id: patient_ref
    type: STRING
  - id: contact_phone_e164
    type: STRING
  - id: task_type
    type: STRING
    defaults: CHECK_IN
  - id: template_code
    type: STRING
    defaults: check_in_wa

variables:
  tenant_jwt: "{{ kv('intellicare_jwt_' + inputs.tenant_slug) }}"

tasks:
  - id: open_task
    type: io.kestra.plugin.core.http.Request
    uri: "http://intellicare-service:8000/api/v1/careplanner/tasks/open"
    method: POST
    headers:
      Authorization: "Bearer {{ vars.tenant_jwt }}"
      Content-Type: application/json
    body: |
      {
        "patient_ref": "{{ inputs.patient_ref }}",
        "task_type": "{{ inputs.task_type }}",
        "template_code": "{{ inputs.template_code }}",
        "channel": "whatsapp",
        "contact_phone_e164": "{{ inputs.contact_phone_e164 }}",
        "kestra_execution_id": "{{ execution.id }}"
      }

  - id: wait_for_reply
    type: io.kestra.plugin.core.flow.Pause
    delay: PT72H
    onResume:
      - id: patient_reply
        type: STRING

  - id: close_task
    type: io.kestra.plugin.core.http.Request
    uri: "http://intellicare-service:8000/api/v1/careplanner/tasks/{{ outputs.open_task.body.correlation_id }}/close"
    method: POST
    headers:
      Authorization: "Bearer {{ vars.tenant_jwt }}"
```

---

## Bloco 11 — `TriggerJourneyModal.tsx`: seletor de canal

```typescript
// Adicionar estado de canal
const [channel, setChannel] = useState<'rocketchat' | 'whatsapp'>('rocketchat')

// NativeSelect para canal (antes do campo template_code)
<NativeSelect
  label="Canal de comunicação"
  data={[
    { label: 'Rocket.Chat', value: 'rocketchat' },
    { label: 'WhatsApp', value: 'whatsapp' },
  ]}
  value={channel}
  onChange={e => setChannel(e.currentTarget.value as 'rocketchat' | 'whatsapp')}
/>

// Campo phone — obrigatório quando WhatsApp
{channel === 'whatsapp' && (
  <TextInput
    label="Telefone do paciente (WhatsApp)"
    placeholder="+5511999999999"
    required
    {...form.getInputProps('contact_phone_e164')}
  />
)}

// Filtrar templates por canal no Select
const { data: templates } = useCareplannerTemplates(true, channel)
// Atualizar hook para aceitar channel como segundo param
```

---

## Bloco 12 — Testes Python (`test_careplanner_phase_h.py`)

```python
"""Testes DEM-047 — canal WhatsApp."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from modules.careplanner.adapters.whatsapp import WhatsAppAdapter
from modules.careplanner.contracts import Channel
from modules.careplanner.config import CareplannerSettings

def make_settings(**kwargs):
    base = dict(
        evolution_api_url="http://localhost:8080",
        evolution_api_key="test-key",
        evolution_instance_name="test",
        evolution_webhook_secret="secret123",
    )
    base.update(kwargs)
    return MagicMock(**base)

@pytest.mark.asyncio
async def test_whatsapp_send_message():
    """WhatsAppAdapter.send_message chama endpoint correto."""
    settings = make_settings()
    adapter = WhatsAppAdapter(settings)
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = MagicMock(status_code=200, json=lambda: {"key": {"id": "abc"}})
        mock_post.return_value.raise_for_status = lambda: None
        await adapter.send_message("+5511999999999", "Olá!")
        called_path = mock_post.call_args[0][0]
        assert "sendText/test" in called_path

def test_extract_phone_from_jid():
    """Extrai número de JID corretamente."""
    adapter = WhatsAppAdapter(make_settings())
    assert adapter.extract_phone_from_jid("5511999999999@s.whatsapp.net") == "5511999999999"

def test_verify_webhook_secret_correto():
    adapter = WhatsAppAdapter(make_settings(evolution_webhook_secret="abc123"))
    assert adapter.verify_webhook_secret("abc123") is True

def test_verify_webhook_secret_errado():
    adapter = WhatsAppAdapter(make_settings(evolution_webhook_secret="abc123"))
    assert adapter.verify_webhook_secret("errado") is False
```

Executar:
```bash
pytest packages/intellicare-core/tests/test_careplanner_phase_h.py -v
```
Critério: **4 passed**.
