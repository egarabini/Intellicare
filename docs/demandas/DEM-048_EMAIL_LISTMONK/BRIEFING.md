---
tipo: briefing-completo
demanda: DEM-048
titulo: E-mail Transacional via Listmonk — Canal 3 do CarePlanner
dev: DEV-1
estimativa: 2.5h
prerequisito: DEM-047 commitada (da98ce2)
---

# DEM-048 — E-mail via Listmonk (Canal 3 CarePlanner)

## Contexto

DEM-047 estabeleceu o padrão de multi-canal com `WhatsAppAdapter`. Esta demanda
replica o mesmo padrão para e-mail transacional via **Listmonk** (MIT License,
Docker-native, REST API simples). O Listmonk já está previsto no
`FerramentasOpenSourceComunicacao.md`.

Listmonk expõe `/api/tx` (transactional messages) — endpoint ideal para
mensagens one-to-one do CarePlanner. Não é necessário gerenciar listas; basta
enviar ao e-mail do paciente diretamente.

**Inbound e-mail: fora de escopo para V3** — e-mail é canal de saída apenas.
Quando o paciente responde por e-mail, o clínico verá a conversa fora do sistema.
A tarefa expira normalmente via `expiry_worker` se não houver resposta via outro canal.

---

## Arquivos a modificar/criar

| Arquivo | Tipo |
|---------|------|
| `modules/careplanner/contracts.py` | Modificar — `Channel.EMAIL = "email"` |
| `modules/careplanner/config.py` | Modificar — 4 vars Listmonk |
| `modules/careplanner/adapters/email.py` | **Novo** — `EmailAdapter` |
| `modules/careplanner/services.py` | Modificar — `_send_to_channel` + `open_task` |
| `infra/docker-compose.yml` | Modificar — serviço `listmonk` |
| `infra/init-db/03_listmonk.sql` | **Novo** — CREATE DATABASE listmonk |
| `infra/.env.staging.example` | Modificar — vars Listmonk |
| `infra/kestra/flows/careplanner_jornada_email.yml` | **Novo** |
| `modules/careplanner/main.py` | Modificar — seed templates email |
| `frontend/GestorUI/src/components/TriggerJourneyModal.tsx` | Modificar — option EMAIL |
| `packages/intellicare-core/tests/test_careplanner_phase_i.py` | **Novo** — 4 testes |

**Sem nova migration** — `channel` já existe em `care_tasks`; `email` é novo valor
do enum Python, não do banco (coluna é `VARCHAR`, aceita qualquer string).

---

## STEP-001 — `contracts.py`

```python
class Channel(StrEnum):
    ROCKETCHAT = "rocketchat"
    WHATSAPP   = "whatsapp"
    EMAIL      = "email"        # <- novo
```

---

## STEP-002 — `config.py`

```python
# Listmonk (E-mail)
listmonk_url: str = "http://listmonk:9000"
listmonk_username: str = "intellicare"
listmonk_password: str = ""
listmonk_sender_email: str = "noreply@intellicare.ia.br"
```

---

## STEP-003 — `adapters/email.py` (novo arquivo completo)

```python
"""Adapter async para e-mail transacional via Listmonk."""
from __future__ import annotations

import logging
from typing import Any

import httpx

from ..config import CareplannerSettings

logger = logging.getLogger(__name__)


class EmailAdapter:
    """Cliente async para Listmonk — envia e-mail transacional."""

    def __init__(self, settings: CareplannerSettings) -> None:
        self._settings = settings
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self._settings.listmonk_url.rstrip("/"),
                auth=(self._settings.listmonk_username, self._settings.listmonk_password),
                timeout=15.0,
            )
        return self._client

    async def send_message(self, email: str, subject: str, body: str) -> dict[str, Any]:
        """Envia e-mail transacional via Listmonk /api/tx."""
        client = await self._get_client()
        for attempt in range(1, 4):
            try:
                response = await client.post(
                    "/api/tx",
                    json={
                        "subscriber_email": email,
                        "template_id": 1,          # template padrão do Listmonk
                        "data": {
                            "subject": subject,
                            "body": body,
                            "from_email": self._settings.listmonk_sender_email,
                        },
                    },
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code >= 500 and attempt < 3:
                    import asyncio
                    await asyncio.sleep(0.5 * (2 ** (attempt - 1)))
                    continue
                raise
        raise httpx.HTTPError("Listmonk falhou após 3 tentativas")

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
```

---

## STEP-004 — `services.py`

### 4a — Adicionar `EmailAdapter` ao `__init__`

```python
from .adapters.email import EmailAdapter

class CareplannerService:
    def __init__(self, ..., email: EmailAdapter) -> None:
        ...
        self._email = email
```

### 4b — Estender `_send_to_channel`

```python
async def _send_to_channel(self, channel, rc_room_id, phone_e164, email, text):
    if channel == Channel.WHATSAPP:
        return await self._whatsapp.send_message(phone_e164, text)
    elif channel == Channel.EMAIL:
        if not email:
            raise ValueError("email obrigatorio para canal EMAIL")
        subject = "IntelliCare — Mensagem da sua equipe de saúde"
        return await self._email.send_message(email, subject, text)
    else:
        return await self._rc.post_message(rc_room_id, text)
```

### 4c — `open_task` para EMAIL — sem criar RC room

```python
if channel in (Channel.WHATSAPP, Channel.EMAIL):
    rc_room_id = None
else:
    rc_room_id = await self._rc.ensure_room(ctx.tenant_id, patient_ref)
```

---

## STEP-005 — `infra/init-db/03_listmonk.sql` (novo)

```sql
-- Cria banco 'listmonk' se não existir (idempotente)
SELECT 'CREATE DATABASE listmonk'
WHERE NOT EXISTS (
    SELECT FROM pg_database WHERE datname = 'listmonk'
)\gexec
```

---

## STEP-006 — `docker-compose.yml`

Adicionar após o serviço `evolution-api`:

```yaml
listmonk:
  image: listmonk/listmonk:v3.0.0
  container_name: intellicare_listmonk
  restart: unless-stopped
  ports:
    - "9100:9000"
  environment:
    LISTMONK_app__address: "0.0.0.0:9000"
    LISTMONK_db__host: postgres
    LISTMONK_db__port: "5432"
    LISTMONK_db__user: postgres
    LISTMONK_db__password: ${POSTGRES_PASSWORD}
    LISTMONK_db__database: listmonk
  depends_on:
    - postgres
  networks:
    - intellicare_net
  command: ["./listmonk", "--install", "--idempotent", "--yes"]
```

⚠️ O flag `--install --idempotent --yes` roda as migrations do Listmonk
automaticamente na primeira subida — sem intervenção manual.

---

## STEP-007 — `.env.staging.example`

```
# Listmonk (E-mail)
LISTMONK_URL=http://listmonk:9000
LISTMONK_USERNAME=intellicare
LISTMONK_PASSWORD=change-me
LISTMONK_SENDER_EMAIL=noreply@intellicare.ia.br
```

---

## STEP-008 — Kestra flow

Criar `infra/kestra/flows/careplanner_jornada_email.yml`:

Igual ao `careplanner_jornada_basica.yml` com:
1. `id: careplanner_jornada_email`
2. Input adicional `contact_email: STRING`
3. No body do `open_task`: `"channel": "email"` e `"contact_email": "{{ inputs.contact_email }}"`
4. `template_code` default: `check_in_email`

---

## STEP-009 — Seed templates email em `main.py`

```python
EMAIL_TEMPLATES = [
    ("boas_vindas_email",    "email", "Olá {{nome_paciente}}, bem-vindo ao IntelliCare!\n\n{{mensagem}}"),
    ("check_in_email",       "email", "Olá {{nome_paciente}},\n\nComo você está se sentindo hoje?\n\nEquipe IntelliCare"),
    ("lembrete_email",       "email", "Lembrete: {{medicamento}} — {{instrucoes}}\n\nEquipe IntelliCare"),
    ("teleconsulta_email",   "email", "Sua teleconsulta está confirmada para {{data_hora}}.\nLink: {{link_video}}"),
]
```

---

## STEP-010 — `TriggerJourneyModal.tsx`

Adicionar `EMAIL` ao `NativeSelect` de canal (introduzido em DEM-047):

```tsx
data={[
  { label: 'Rocket.Chat', value: 'rocketchat' },
  { label: 'WhatsApp',    value: 'whatsapp' },
  { label: 'E-mail',      value: 'email' },
]}
```

Exibir campo `TextInput` de e-mail quando `channel === 'email'`:

```tsx
{channel === 'email' && (
  <TextInput
    label="E-mail do paciente"
    placeholder="paciente@email.com"
    required
    {...form.getInputProps('contact_email')}
  />
)}
```

---

## STEP-011 — Testes (`test_careplanner_phase_i.py`)

```python
"""Testes DEM-048 — canal E-mail."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from modules.careplanner.adapters.email import EmailAdapter
from modules.careplanner.contracts import Channel

def make_settings(**kwargs):
    base = dict(
        listmonk_url="http://localhost:9000",
        listmonk_username="test",
        listmonk_password="test",
        listmonk_sender_email="noreply@test.com",
    )
    base.update(kwargs)
    return MagicMock(**base)

@pytest.mark.asyncio
async def test_email_send_message():
    adapter = EmailAdapter(make_settings())
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = MagicMock(status_code=200, json=lambda: {"data": {}})
        mock_post.return_value.raise_for_status = lambda: None
        await adapter.send_message("p@test.com", "Teste", "corpo")
        called_path = mock_post.call_args[0][0]
        assert called_path == "/api/tx"

def test_channel_email_exists():
    assert Channel.EMAIL == "email"

@pytest.mark.asyncio
async def test_email_retry_on_500():
    """Deve tentar 3x em caso de erro 500."""
    adapter = EmailAdapter(make_settings())
    import httpx
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        err_resp = MagicMock(status_code=500)
        mock_post.return_value.raise_for_status = lambda: (_ for _ in ()).throw(
            httpx.HTTPStatusError("err", request=MagicMock(), response=err_resp)
        )
        with pytest.raises(httpx.HTTPError):
            await adapter.send_message("p@test.com", "s", "b")

@pytest.mark.asyncio
async def test_email_adapter_close():
    adapter = EmailAdapter(make_settings())
    client_mock = AsyncMock()
    adapter._client = client_mock
    await adapter.close()
    client_mock.aclose.assert_called_once()
```

Critério: `pytest test_careplanner_phase_i.py -v` → **4 passed**.

---

## STEP-012 — Commit

```
feat(careplanner): DEM-048 canal e-mail via Listmonk
```

Arquivos:
```
modules\careplanner\contracts.py
modules\careplanner\config.py
modules\careplanner\adapters\email.py
modules\careplanner\services.py
infra\docker-compose.yml
infra\init-db\03_listmonk.sql
infra\.env.staging.example
infra\kestra\flows\careplanner_jornada_email.yml
modules\careplanner\main.py
frontend\GestorUI\src\components\TriggerJourneyModal.tsx
packages\intellicare-core\tests\test_careplanner_phase_i.py
```
