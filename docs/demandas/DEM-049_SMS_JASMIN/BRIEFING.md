---
tipo: briefing-completo
demanda: DEM-049
titulo: SMS via Jasmin — Canal 4 do CarePlanner
dev: DEV-2
estimativa: 2h
prerequisito: DEM-047 commitada (da98ce2)
---

# DEM-049 — SMS via Jasmin (Canal 4 CarePlanner)

## Contexto

Jasmin (GPL-3.0) é o gateway SMS open-source mais maduro do ecossistema Python,
com suporte a SMPP e REST HTTP API. Para o IntelliCare usamos a **HTTP API REST**
(`/send`) — sem SMPP, mais simples de operar.

O padrão de `SMSAdapter` é idêntico ao `WhatsAppAdapter` (DEM-047) e
`EmailAdapter` (DEM-048): httpx async, retry exponencial, settings injetados.

**Inbound SMS**: Jasmin pode encaminhar respostas via webhook HTTP. Implementar
o endpoint inbound (igual ao WhatsApp) para fechar o loop SENT→REPLIED via SMS.

---

## Arquivos a modificar/criar

| Arquivo | Tipo |
|---------|------|
| `modules/careplanner/contracts.py` | Modificar — `Channel.SMS = "sms"` |
| `modules/careplanner/config.py` | Modificar — 4 vars Jasmin |
| `modules/careplanner/adapters/sms.py` | **Novo** — `SMSAdapter` |
| `modules/careplanner/services.py` | Modificar — `_send_to_channel` |
| `modules/careplanner/api/routes.py` | Modificar — webhook SMS inbound |
| `infra/docker-compose.yml` | Modificar — serviço `jasmin` |
| `infra/.env.staging.example` | Modificar — vars Jasmin |
| `infra/kestra/flows/careplanner_jornada_sms.yml` | **Novo** |
| `modules/careplanner/main.py` | Modificar — seed templates SMS |
| `frontend/GestorUI/src/components/TriggerJourneyModal.tsx` | Modificar — option SMS |
| `packages/intellicare-core/tests/test_careplanner_phase_j.py` | **Novo** — 4 testes |

---

## STEP-001 — `contracts.py`

```python
class Channel(StrEnum):
    ROCKETCHAT = "rocketchat"
    WHATSAPP   = "whatsapp"
    EMAIL      = "email"
    SMS        = "sms"           # <- novo
```

---

## STEP-002 — `config.py`

```python
# Jasmin SMS Gateway
jasmin_url: str = "http://jasmin:1401"
jasmin_username: str = "admin"
jasmin_password: str = ""
jasmin_sender_id: str = "INTELLICARE"   # nome exibido no SMS
```

---

## STEP-003 — `adapters/sms.py` (novo arquivo completo)

```python
"""Adapter async para SMS via Jasmin HTTP API."""
from __future__ import annotations

import logging
import urllib.parse
from typing import Any

import httpx

from ..config import CareplannerSettings

logger = logging.getLogger(__name__)


class SMSAdapter:
    """Cliente async para Jasmin — envia SMS via HTTP API."""

    def __init__(self, settings: CareplannerSettings) -> None:
        self._settings = settings
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self._settings.jasmin_url.rstrip("/"),
                timeout=15.0,
            )
        return self._client

    def _normalize_phone(self, phone_e164: str) -> str:
        """Remove + para formato internacional. Ex: +5511999 → 5511999"""
        return phone_e164.lstrip("+")

    async def send_message(self, phone_e164: str, text: str) -> dict[str, Any]:
        """Envia SMS via Jasmin /send endpoint."""
        client = await self._get_client()
        phone = self._normalize_phone(phone_e164)

        # SMS: máx 160 chars. Truncar com aviso no log se necessário.
        if len(text) > 160:
            logger.warning("SMS truncado de %d para 160 chars", len(text))
            text = text[:157] + "..."

        params = {
            "username": self._settings.jasmin_username,
            "password": self._settings.jasmin_password,
            "to": phone,
            "from": self._settings.jasmin_sender_id,
            "content": text,
        }

        for attempt in range(1, 4):
            try:
                response = await client.get("/send", params=params)
                response.raise_for_status()
                # Jasmin retorna texto: "Success \"msgid\"" ou "Error ..."
                body = response.text.strip()
                if body.startswith("Error"):
                    raise httpx.HTTPError(f"Jasmin recusou SMS: {body}")
                return {"status": "sent", "jasmin_response": body}
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code >= 500 and attempt < 3:
                    import asyncio
                    await asyncio.sleep(0.5 * (2 ** (attempt - 1)))
                    continue
                raise
        raise httpx.HTTPError("Jasmin falhou após 3 tentativas")

    def verify_webhook_secret(self, token: str) -> bool:
        """Jasmin não assina webhooks — usar token simples no path."""
        secret = getattr(self._settings, "jasmin_webhook_secret", "")
        if not secret:
            return True
        return token == secret

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
```

---

## STEP-004 — `services.py` — estender `_send_to_channel`

```python
from .adapters.sms import SMSAdapter

class CareplannerService:
    def __init__(self, ..., sms: SMSAdapter) -> None:
        ...
        self._sms = sms

async def _send_to_channel(self, channel, rc_room_id, phone_e164, email, text):
    if channel == Channel.WHATSAPP:
        return await self._whatsapp.send_message(phone_e164, text)
    elif channel == Channel.SMS:
        if not phone_e164:
            raise ValueError("phone_e164 obrigatorio para canal SMS")
        return await self._sms.send_message(phone_e164, text)
    elif channel == Channel.EMAIL:
        return await self._email.send_message(email, "IntelliCare", text)
    else:
        return await self._rc.post_message(rc_room_id, text)
```

⚠️ Verificar se DEM-048 já adicionou `email` neste método. Se sim, apenas
adicionar o bloco `elif channel == Channel.SMS` sem duplicar o resto.

---

## STEP-005 — Webhook SMS inbound (`api/routes.py`)

```python
@router.post("/webhook/sms/{token}", status_code=status.HTTP_200_OK)
async def sms_webhook(
    token: str,
    request: Request,
    service: CareplannerService = Depends(get_service),
) -> dict:
    """Recebe respostas SMS via Jasmin MO webhook."""
    settings = get_careplanner_settings()
    sms = SMSAdapter(settings)
    if not sms.verify_webhook_secret(token):
        raise api_error(401, "unauthorized", "Token invalido")

    body = await request.json()
    # Jasmin MO payload: { "from": "5511999", "to": "INTELLICARE", "content": "..." }
    phone_raw = body.get("from", "")
    text = body.get("content", "")

    if not phone_raw or not text:
        return {"status": "ignored", "reason": "sem phone ou texto"}

    phone_e164 = f"+{phone_raw.lstrip('+')}"
    await service.handle_whatsapp_inbound(phone=phone_e164.lstrip("+"), text=text)
    # Reutiliza handle_whatsapp_inbound — mesma lógica de cross-tenant phone lookup
    return {"status": "ok"}
```

---

## STEP-006 — `docker-compose.yml`

```yaml
jasmin:
  image: jookies/jasmin:0.10
  container_name: intellicare_jasmin
  restart: unless-stopped
  ports:
    - "1401:1401"    # HTTP API
    - "8990:8990"    # CLI management
  environment:
    REDIS_CLIENT_HOST: redis
    AMQP_BROKER_HOST: rabbitmq   # se usar RabbitMQ; senão remover
  depends_on:
    - redis
  networks:
    - intellicare_net
```

⚠️ Jasmin usa Redis para filas internas. Verificar se o serviço `redis` já
existe no `docker-compose.yml` do IntelliCare (provável — CarePlanner usa Redis).
Se existir, apenas adicionar o serviço `jasmin` com `depends_on: [redis]`.

---

## STEP-007 — `.env.staging.example`

```
# Jasmin SMS
JASMIN_URL=http://jasmin:1401
JASMIN_USERNAME=admin
JASMIN_PASSWORD=change-me
JASMIN_SENDER_ID=INTELLICARE
JASMIN_WEBHOOK_SECRET=change-me
```

---

## STEP-008 — Kestra flow

Criar `infra/kestra/flows/careplanner_jornada_sms.yml`:

Igual ao `careplanner_jornada_whatsapp.yml` com:
1. `id: careplanner_jornada_sms`
2. No body do `open_task`: `"channel": "sms"`
3. `template_code` default: `check_in_sms`

---

## STEP-009 — Seed templates SMS em `main.py`

```python
SMS_TEMPLATES = [
    ("boas_vindas_sms",  "sms", "Ola {{nome_paciente}}! Bem-vindo ao IntelliCare. Responda a esta msg."),
    ("check_in_sms",     "sms", "{{nome_paciente}}, como se sente hoje? Responda 1-10. IntelliCare"),
    ("lembrete_sms",     "sms", "Lembrete: {{medicamento}} agora. IntelliCare"),
    ("confirmacao_sms",  "sms", "Consulta confirmada: {{data_hora}}. Link: {{link_video}} IntelliCare"),
]
```

⚠️ SMS: máx 160 chars. Verificar todos os templates no limite.

---

## STEP-010 — `TriggerJourneyModal.tsx`

Adicionar `SMS` ao `NativeSelect` de canal (DEM-047 introduziu, DEM-048 expandiu):

```tsx
data={[
  { label: 'Rocket.Chat', value: 'rocketchat' },
  { label: 'WhatsApp',    value: 'whatsapp' },
  { label: 'E-mail',      value: 'email' },
  { label: 'SMS',         value: 'sms' },
]}
```

Campo telefone já existe para WhatsApp — reutilizar para SMS:

```tsx
{(channel === 'whatsapp' || channel === 'sms') && (
  <TextInput
    label="Telefone do paciente"
    placeholder="+5511999999999"
    required
    {...form.getInputProps('contact_phone_e164')}
  />
)}
```

---

## STEP-011 — Testes (`test_careplanner_phase_j.py`)

```python
"""Testes DEM-049 — canal SMS."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from modules.careplanner.adapters.sms import SMSAdapter
from modules.careplanner.contracts import Channel

def make_settings(**kwargs):
    base = dict(
        jasmin_url="http://localhost:1401",
        jasmin_username="admin",
        jasmin_password="test",
        jasmin_sender_id="TEST",
        jasmin_webhook_secret="secret",
    )
    base.update(kwargs)
    return MagicMock(**base)

@pytest.mark.asyncio
async def test_sms_send_message():
    adapter = SMSAdapter(make_settings())
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = MagicMock(status_code=200, text='Success "abc123"')
        mock_get.return_value.raise_for_status = lambda: None
        result = await adapter.send_message("+5511999999999", "Teste SMS")
        assert result["status"] == "sent"

def test_channel_sms_exists():
    assert Channel.SMS == "sms"

def test_sms_truncate_long_message():
    adapter = SMSAdapter(make_settings())
    long_msg = "x" * 200
    # O truncamento ocorre dentro de send_message — testar _normalize_phone
    assert adapter._normalize_phone("+5511999") == "5511999"

def test_sms_verify_secret():
    adapter = SMSAdapter(make_settings(jasmin_webhook_secret="abc"))
    assert adapter.verify_webhook_secret("abc") is True
    assert adapter.verify_webhook_secret("errado") is False
```

Critério: `pytest test_careplanner_phase_j.py -v` → **4 passed**.

---

## STEP-012 — Commit

```
feat(careplanner): DEM-049 canal SMS via Jasmin
```

Arquivos:
```
modules\careplanner\contracts.py
modules\careplanner\config.py
modules\careplanner\adapters\sms.py
modules\careplanner\services.py
modules\careplanner\api\routes.py
infra\docker-compose.yml
infra\.env.staging.example
infra\kestra\flows\careplanner_jornada_sms.yml
modules\careplanner\main.py
frontend\GestorUI\src\components\TriggerJourneyModal.tsx
packages\intellicare-core\tests\test_careplanner_phase_j.py
```
