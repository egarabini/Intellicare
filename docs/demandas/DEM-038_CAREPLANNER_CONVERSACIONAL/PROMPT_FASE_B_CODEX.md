# DEM-038 Fase B — Prompt para Codex

> **PLANEJADOR** | 2026-03-17
> Infra de staging 100% validada. Entregar Fase B completa.

---

## Contexto

O módulo `modules/careplanner/` já tem a **Fase A** concluída e commitada (`b6a3966`).
Não reescrever nada que já existe — apenas acrescentar.

### O que já existe (Fase A — NÃO ALTERAR)

| Arquivo | Conteúdo |
|---------|----------|
| `modules/careplanner/contracts.py` | `TaskStatus`, `EventType`, `Channel`, `ParticipantRole`, todos os Pydantic models (`CareTaskCreate`, `CareConversationUpsert`, etc.), `cast_channel_conversation_id()` |
| `modules/careplanner/config.py` | `CareplannerSettings` (pydantic-settings), `get_careplanner_settings()` |
| `modules/careplanner/repository.py` | `CareplannerRepository` com todos os métodos: `create_task`, `get_task`, `transition_task_status`, `record_event_if_new`, `list_events`, `upsert_conversation`, `get_conversation`, `create_template`, `list_templates`, `create_video_session` |
| `modules/careplanner/migrations.py` | 5 tabelas: `care_tasks`, `care_conversations`, `care_events`, `care_templates`, `care_video_sessions` |
| `packages/intellicare-core/tests/test_careplanner_phase_a.py` | 3 testes passando (máquina de estados, idempotência, BIGINT) |

---

## O que entregar na Fase B

### Arquivos a criar

```
modules/careplanner/
├── __init__.py                  ← criar/atualizar (pode já existir vazio)
├── main.py                      ← CRIAR
├── adapters/
│   ├── __init__.py              ← CRIAR
│   ├── rocketchat.py            ← CRIAR (portar de V2)
│   └── jitsi.py                 ← CRIAR (portar de V2)
├── adapters/kestra.py           ← CRIAR (portar de V2)
├── workers/
│   ├── __init__.py              ← CRIAR
│   └── dispatcher.py           ← CRIAR (stub OK para Fase B)
├── api/
│   ├── __init__.py              ← CRIAR
│   └── routes.py               ← CRIAR (todos os endpoints)
└── services.py                  ← CRIAR
```

### Arquivos a modificar

```
packages/intellicare-core/intellicare_core/module_loader/loader.py
    → adicionar "careplanner": "modules.careplanner.main" em AVAILABLE_MODULES

packages/intellicare-core/intellicare_core/main.py
    → adicionar loader.load("careplanner") junto dos outros módulos

infra/docker-compose.yml
    → adicionar serviços: kestra, mongo, mongo-init-replica, rocketchat, jitsi-web,
      jitsi-prosody, jitsi-jicofo, jitsi-jvb
    → adicionar volumes: kestra_data, mongo_data, rocketchat_uploads, jitsi_web,
      jitsi_prosody, jitsi_jicofo, jitsi_jvb

packages/intellicare-core/tests/test_careplanner_phase_b.py
    → CRIAR com 10 testes de integração (ver seção Testes abaixo)
```

---

## 1. `modules/careplanner/adapters/rocketchat.py`

**Portar de**: `C:\DOCSHARE\INTELLICARE_V2\intellicare-comunicacao\comunicacao\rocketchat\client.py`
(491 linhas — contém lógica completa de auth, rate limiting, retry com httpx async)

Classe a criar: `RocketChatAdapter`

```python
import hashlib
import hmac
import logging
from typing import Any

import httpx

from ..config import CareplannerSettings

logger = logging.getLogger(__name__)


class RocketChatAdapter:
    """
    Adapter async para Rocket.Chat.
    Porta do V2 intellicare-comunicacao/comunicacao/rocketchat/client.py.

    ATENÇÃO ao portar:
    - Preservar a lógica de login/token cache (userId + authToken em memória)
    - Preservar rate limiting (ROCKETCHAT_MAX_REQUESTS_PER_SECOND)
    - Preservar retry (ROCKETCHAT_MAX_RETRIES) com backoff exponencial
    - Remover herança de IChannelDispatcher (não existe no V3)
    - URL base: settings.rocketchat_url (= http://rocketchat:3001 no Docker)
    """

    def __init__(self, settings: CareplannerSettings) -> None:
        self._settings = settings
        self._user_id: str | None = None
        self._auth_token: str | None = None
        self._client: httpx.AsyncClient | None = None

    async def login_bot(self) -> None:
        """
        POST /api/v1/login com rocketchat_bot_username / rocketchat_bot_password.
        Armazena userId + authToken em memória.
        Renovar automaticamente se receber 401 em qualquer chamada.
        """
        ...

    async def ensure_room(self, tenant_slug: str, patient_ref: str) -> str:
        """
        Cria ou recupera canal no Rocket.Chat.
        Nome do canal: ic_{tenant_slug}_{patient_ref}
        Lógica:
          POST /api/v1/channels.create
          Se erro "already exists" → GET /api/v1/channels.info?roomName=ic_{tenant_slug}_{patient_ref}
        Retorna rc_room_id (string interna do Rocket.Chat).
        """
        ...

    async def post_message(self, rc_room_id: str, text: str) -> dict[str, Any]:
        """
        POST /api/v1/chat.postMessage
        Body: {"roomId": rc_room_id, "text": text}
        Retorna dict com _id da mensagem.
        HTTP 202 do RC = dispatched; não confundir com falha.
        """
        ...

    async def archive_room(self, rc_room_id: str) -> None:
        """
        POST /api/v1/channels.archive
        Body: {"roomId": rc_room_id}
        Chamado ao fechar a jornada (CLOSED).
        """
        ...

    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """
        Valida HMAC-SHA256 do webhook inbound do Rocket.Chat.
        Header: X-Rocketchat-Signature: sha256=<hex>
        Secret: settings.rocketchat_webhook_token
        """
        expected = hmac.new(
            self._settings.rocketchat_webhook_token.encode(),
            payload,
            hashlib.sha256,
        ).hexdigest()
        # comparar de forma segura; remover prefixo "sha256=" se presente
        received = signature.removeprefix("sha256=")
        return hmac.compare_digest(expected, received)

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
```

---

## 2. `modules/careplanner/adapters/jitsi.py`

**Portar de**: `C:\DOCSHARE\INTELLICARE_V2\intellicare-comunicacao\comunicacao\jitsi\client.py`

Classe a criar: `JitsiAdapter`

```python
from datetime import datetime, timedelta, timezone
import jwt  # PyJWT

from ..config import CareplannerSettings


class JitsiAdapter:
    """
    Adapter para geração de URLs e JWTs Jitsi.
    Porta do V2 intellicare-comunicacao/comunicacao/jitsi/client.py.

    ATENÇÃO ao portar:
    - sub = JITSI_BASE_URL (domínio do servidor, ex.: https://meet.intellicare.ia.br)
      NÃO é o app_id — conforme spec oficial lib-jitsi-meet e validado no V2
    - iss = JITSI_APP_ID (= "intellicare")
    - Algoritmo: HS256
    - Flag moderator como campo top-level do payload (não dentro de context)
    """

    def __init__(self, settings: CareplannerSettings) -> None:
        self._settings = settings

    def generate_room_jwt(
        self,
        room_name: str,
        user_id: str,
        user_name: str,
        is_moderator: bool = False,
        expires_in_minutes: int | None = None,
    ) -> str:
        """
        Gera JWT para acesso a sala Jitsi.

        Payload:
        {
          "iss": settings.jitsi_app_id,          # "intellicare"
          "sub": settings.jitsi_base_url,         # "https://meet.intellicare.ia.br"
          "aud": "jitsi",
          "iat": now,
          "nbf": now,
          "exp": now + expires_in_minutes * 60,
          "room": room_name,
          "moderator": is_moderator,              # top-level, não dentro de context
          "context": {
            "user": { "id": user_id, "name": user_name }
          }
        }
        """
        duration = expires_in_minutes or self._settings.jitsi_default_room_duration
        now = datetime.now(tz=timezone.utc)
        payload = {
            "iss": self._settings.jitsi_app_id,
            "sub": self._settings.jitsi_base_url,
            "aud": "jitsi",
            "iat": now,
            "nbf": now,
            "exp": now + timedelta(minutes=duration),
            "room": room_name,
            "moderator": is_moderator,
            "context": {
                "user": {"id": user_id, "name": user_name}
            },
        }
        return jwt.encode(payload, self._settings.jitsi_app_secret, algorithm="HS256")

    def get_room_url(self, room_name: str, jwt_token: str) -> str:
        """
        Constrói URL pública da sala.
        Formato: {JITSI_BASE_URL}/{room_name}?jwt={token}
        """
        base = self._settings.jitsi_base_url.rstrip("/")
        return f"{base}/{room_name}?jwt={jwt_token}"

    @staticmethod
    def build_room_name(tenant_slug: str, correlation_id_str: str) -> str:
        """
        Convenção de nome de sala: ic_{tenant_slug}_{primeiros 8 chars do correlation_id}
        Exemplo: ic_alfa_550e8400
        """
        short_id = correlation_id_str.replace("-", "")[:8]
        return f"ic_{tenant_slug}_{short_id}"
```

---

## 3. `modules/careplanner/adapters/kestra.py`

**Portar de**: `C:\DOCSHARE\INTELLICARE_V2\intellicare-nise\nise\services\kestra_client.py`

Classe a criar: `KestraAdapter`

```python
import httpx
from ..config import CareplannerSettings


class KestraAdapter:
    """
    Adapter HTTP para Kestra.
    Porta do V2 intellicare-nise/nise/services/kestra_client.py.

    URL interna: http://kestra:8080
    Auth: opcional (KESTRA_API_KEY; vazio em dev/staging)
    """

    def __init__(self, settings: CareplannerSettings) -> None:
        self._settings = settings

    async def resume_execution(self, execution_id: str, payload: dict | None = None) -> dict:
        """
        Retoma execução pausada no Kestra.
        POST http://kestra:8080/api/v1/executions/{execution_id}/resume
        Body: payload (pode ser None ou dict com dados de resposta do paciente)
        Usado pelo IntelliCare ao receber REPLIED para notificar o Kestra.
        """
        ...

    async def get_execution(self, execution_id: str) -> dict:
        """
        GET http://kestra:8080/api/v1/executions/{execution_id}
        Retorna estado atual da execução.
        """
        ...

    async def health_check(self) -> bool:
        """
        GET http://kestra:8080/health
        Retorna True se Kestra responder 200.
        """
        ...
```

---

## 4. `modules/careplanner/services.py`

Este é o núcleo da Fase B. Orquestra adapters + repository + máquina de estados.

```python
"""Servicos de orqustracao do CarePlanner."""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from uuid import UUID

from intellicare_core.contracts.base import TenantContext

from .adapters.jitsi import JitsiAdapter
from .adapters.kestra import KestraAdapter
from .adapters.rocketchat import RocketChatAdapter
from .config import get_careplanner_settings
from .contracts import (
    CareConversationUpsert,
    CareEventCreate,
    CareTaskCreate,
    CareVideoSessionCreate,
    Channel,
    EventType,
    ParticipantRole,
    TaskStatus,
    cast_channel_conversation_id,
)
from .repository import CareplannerRepository

logger = logging.getLogger(__name__)


class CareplannerService:
    def __init__(
        self,
        repo: CareplannerRepository,
        rc: RocketChatAdapter,
        jitsi: JitsiAdapter,
        kestra: KestraAdapter,
    ) -> None:
        self._repo = repo
        self._rc = rc
        self._jitsi = jitsi
        self._kestra = kestra

    # ──────────────────────────────────────────────────────────
    # 1. Abrir jornada (chamado pelo Kestra via HTTP Task)
    # ──────────────────────────────────────────────────────────
    async def open_task(
        self,
        ctx: TenantContext,
        kestra_execution_id: str,
        patient_ref: str,
        task_type: str,
        template_code: str,
        template_variables: dict,
        contact_phone: str | None = None,
        contact_role: str = "PACIENTE",
    ) -> dict:
        """
        Cria CareTask (CREATED) + dispara mensagem no Rocket.Chat.

        Fluxo:
        1. Criar CareTask (CREATED)
        2. ensure_room(tenant_slug, patient_ref) → rc_room_id
        3. Resolver template (buscar care_templates ou usar fallback)
        4. post_message(rc_room_id, texto_renderizado)
        5. Transição CREATED → DISPATCHED (HTTP 2xx do RC)
        6. upsert_conversation com rc_room_id e channel_conversation_id=0 (placeholder)
        7. Retornar {"ok": True, "correlation_id": str, "status": "CREATED"}

        REGRA CRÍTICA: HTTP 202 do RC = DISPATCHED. Nunca FAILED por causa de 202.
        FAILED apenas se httpx levantar exceção ou RC retornar >= 500.
        """
        ...

    # ──────────────────────────────────────────────────────────
    # 2. Callback de entrega confirmada (MESSAGE_SENT)
    # ──────────────────────────────────────────────────────────
    async def process_message_sent(
        self,
        ctx: TenantContext,
        event_id: str,
        correlation_id: UUID,
        rc_room_id: str,
        channel_conversation_id: str | int,
    ) -> dict:
        """
        Avança DISPATCHED → SENT.

        Fluxo:
        1. record_event_if_new(event_id, MESSAGE_SENT) — idempotente
        2. Se evento já existia: retornar {"ok": True, "duplicate": True}
        3. upsert_conversation com rc_room_id e channel_conversation_id (BIGINT cast)
        4. transition_task_status(correlation_id, SENT)
        5. Retornar {"ok": True, "status": "SENT"}
        """
        ...

    # ──────────────────────────────────────────────────────────
    # 3. Inbound do paciente (Rocket.Chat → IntelliCare)
    # ──────────────────────────────────────────────────────────
    async def process_inbound(
        self,
        ctx: TenantContext,
        event_id: str,
        rc_room_id: str,
        channel_conversation_id: str | int,
        content: str,
        occurred_at: str | None = None,
    ) -> dict:
        """
        Processa mensagem inbound do paciente.

        Fluxo:
        1. record_event_if_new(event_id, INBOUND_RECEIVED)
        2. Buscar conversation por rc_room_id OU channel_conversation_id
           (SELECT * FROM care_conversations WHERE rc_room_id = :rc_room_id)
        3. Se não encontrada → gravar ORPHAN_INBOUND + retornar {"ok": True, "orphan": True}
        4. Se encontrada → transition SENT → REPLIED (ou DISPATCHED → REPLIED se veio antes do MESSAGE_SENT)
        5. upsert_conversation com last_interaction_at = agora
        6. Se task tem kestra_execution_id → kestra.resume_execution(execution_id, {"content": content})
        7. Retornar {"ok": True, "status": "REPLIED", "correlation_id": str}

        Inbound órfão NUNCA retorna 4xx — sempre 202.
        """
        ...

    # ──────────────────────────────────────────────────────────
    # 4. Videoconsulta Jitsi
    # ──────────────────────────────────────────────────────────
    async def open_video_session(
        self,
        ctx: TenantContext,
        correlation_id: UUID,
        clinico_ref: str,
    ) -> dict:
        """
        Gera JWTs Jitsi e persiste em care_video_sessions.

        Fluxo:
        1. Buscar task por correlation_id (404 se não existir)
        2. room_name = JitsiAdapter.build_room_name(tenant_slug, str(correlation_id))
        3. clinico_jwt = jitsi.generate_room_jwt(room_name, clinico_ref, clinico_ref, moderator=True)
        4. patient_jwt = jitsi.generate_room_jwt(room_name, task.patient_ref, task.patient_ref, moderator=False)
        5. expires_at = now + JITSI_DEFAULT_ROOM_DURATION minutos
        6. create_video_session(CareVideoSessionCreate(...))
        7. clinico_url = jitsi.get_room_url(room_name, clinico_jwt)
        8. patient_url = jitsi.get_room_url(room_name, patient_jwt)
        9. Enviar patient_url ao paciente via rc.post_message(rc_room_id, "Sua videoconsulta: {patient_url}")
           (buscar rc_room_id da conversation; se não houver, pular silenciosamente)
        10. record_event VIDEO_SESSION_OPENED
        11. Retornar {"room_name", "clinico_url", "patient_url", "expires_at"}
        """
        ...

    # ──────────────────────────────────────────────────────────
    # 5. Fechar jornada
    # ──────────────────────────────────────────────────────────
    async def close_task(
        self,
        ctx: TenantContext,
        correlation_id: UUID,
    ) -> dict:
        """
        Fecha jornada → CLOSED e arquiva sala no Rocket.Chat.

        Fluxo:
        1. Buscar task (404 se não existir)
        2. transition_task_status(correlation_id, CLOSED)
        3. Buscar conversation → se tiver rc_room_id: rc.archive_room(rc_room_id)
        4. record_event TASK_CLOSED
        5. Retornar {"ok": True, "status": "CLOSED"}
        """
        ...
```

---

## 5. `modules/careplanner/api/routes.py`

```python
"""Rotas FastAPI do módulo CarePlanner."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from pydantic import BaseModel

from intellicare_core.auth.dependencies import get_tenant_context
from intellicare_core.contracts.base import TenantContext

router = APIRouter()

# ── Schemas de request/response ────────────────────────────────────────────

class OpenTaskRequest(BaseModel):
    kestra_execution_id: str
    patient_ref: str
    task_type: str
    contact: dict          # {"phone_e164": str, "role": str}
    message: dict          # {"template_code": str, "variables": dict}


class MessageSentRequest(BaseModel):
    event_id: str
    correlation_id: UUID
    event_type: str        # deve ser "MESSAGE_SENT"
    refs: dict             # {"rc_room_id": str, "channel_conversation_id": str|int}


class InboundRequest(BaseModel):
    event_id: str
    event_type: str        # deve ser "INBOUND_RECEIVED"
    rc_room_id: str
    channel_conversation_id: str | int
    content: str
    occurred_at: str | None = None


class VideoRequest(BaseModel):
    correlation_id: UUID
    clinico_ref: str


# ── Endpoints ───────────────────────────────────────────────────────────────

@router.post("/tasks/open", status_code=status.HTTP_202_ACCEPTED)
async def open_task(
    body: OpenTaskRequest,
    ctx: TenantContext = Depends(get_tenant_context),
) -> dict:
    """Kestra chama este endpoint para iniciar jornada do paciente."""
    ...


@router.post("/events/message-sent", status_code=status.HTTP_200_OK)
async def message_sent_callback(
    request: Request,
    body: MessageSentRequest,
    x_rocketchat_signature: str | None = Header(default=None),
    ctx: TenantContext = Depends(get_tenant_context),
) -> dict:
    """
    Callback de entrega: Rocket.Chat confirma que a mensagem foi enviada.
    Validar HMAC. Avançar DISPATCHED → SENT.
    """
    ...


@router.post("/webhooks/rocketchat/inbound", status_code=status.HTTP_202_ACCEPTED)
async def rocketchat_inbound(
    request: Request,
    body: InboundRequest,
    x_rocketchat_signature: str | None = Header(default=None),
) -> dict:
    """
    Webhook: paciente respondeu no Rocket.Chat.
    Validar HMAC. NÃO requer JWT Keycloak (vem do RC).
    Inbound órfão → 202 (nunca 4xx).
    """
    ...


@router.post("/consultations/video", status_code=status.HTTP_201_CREATED)
async def open_video_session(
    body: VideoRequest,
    ctx: TenantContext = Depends(get_tenant_context),
) -> dict:
    """Clínico solicita videoconsulta para a jornada ativa."""
    ...


@router.get("/tasks/{correlation_id}")
async def get_task(
    correlation_id: UUID,
    ctx: TenantContext = Depends(get_tenant_context),
) -> dict:
    """Detalhe da jornada + últimos 10 eventos."""
    ...


@router.get("/tasks")
async def list_tasks(
    status_filter: str | None = None,
    page: int = 1,
    ctx: TenantContext = Depends(get_tenant_context),
) -> dict:
    """Lista jornadas do tenant filtradas por status."""
    ...


@router.post("/tasks/{correlation_id}/close", status_code=status.HTTP_200_OK)
async def close_task(
    correlation_id: UUID,
    ctx: TenantContext = Depends(get_tenant_context),
) -> dict:
    """Fecha jornada + arquiva sala no Rocket.Chat."""
    ...
```

---

## 6. `modules/careplanner/main.py`

Seguir **exatamente** o padrão de `modules/notifications/main.py`:

```python
"""Módulo CarePlanner — ponto de entrada compatível com BaseModule."""
from __future__ import annotations

import logging

from fastapi import APIRouter
from sqlalchemy import text

from intellicare_core.contracts.base import BaseModule, HealthResponse
from intellicare_core.db.session import get_engine

from .migrations import CAREPLANNER_MIGRATIONS   # lista de SQL strings — ver migrations.py
from .api.routes import router as careplanner_router

logger = logging.getLogger(__name__)


class Module(BaseModule):
    """Módulo CarePlanner Conversacional (DEM-038)."""

    @property
    def name(self) -> str:
        return "careplanner"

    @property
    def version(self) -> str:
        return "1.0.0"

    def get_router(self) -> APIRouter:
        return careplanner_router

    async def startup(self) -> None:
        """Aplica migrations em todos os tenants."""
        async with get_engine().begin() as conn:
            tenants = (
                await conn.execute(text("SELECT slug FROM public.tenants"))
            ).scalars().all()
            for slug in tenants:
                schema = f"tenant_{slug}"
                try:
                    await conn.execute(text(f'SET search_path TO "{schema}"'))
                    for sql in CAREPLANNER_MIGRATIONS:
                        await conn.execute(text(sql))
                    logger.info("Migrations careplanner aplicadas: %s", schema)
                except Exception:
                    logger.exception("Erro ao migrar careplanner para %s", schema)
            await conn.execute(text("SET search_path TO public"))

    async def shutdown(self) -> None:
        pass

    async def health(self) -> HealthResponse:
        return HealthResponse(
            status="healthy",
            module=self.name,
            version=self.version,
            details={},
        )
```

> Verificar se `migrations.py` já expõe `CAREPLANNER_MIGRATIONS` como lista de strings SQL.
> Se não expõe, adicionar a constante sem quebrar os testes existentes da Fase A.

---

## 7. `modules/careplanner/workers/dispatcher.py`

**Stub para Fase B** (retry/dead-letter é Fase D):

```python
"""Dispatcher de tarefas CarePlanner (stub Fase B — retry implementado na Fase D)."""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


async def enqueue_dispatch(correlation_id: str, tenant_slug: str) -> None:
    """
    Fase B: stub síncrono — dispatch já é feito em services.open_task().
    Fase D: implementar fila Redis com retry/dead-letter.
    """
    logger.debug("dispatcher.enqueue_dispatch: %s / %s (stub)", correlation_id, tenant_slug)
```

---

## 8. Registrar no Module Loader

### `packages/intellicare-core/intellicare_core/module_loader/loader.py`

Adicionar na dict `AVAILABLE_MODULES`:
```python
"careplanner": "modules.careplanner.main",
```

### `packages/intellicare-core/intellicare_core/main.py`

Adicionar junto dos outros `loader.load(...)`:
```python
loader.load("careplanner")
```

---

## 9. `infra/docker-compose.yml` — Novos serviços

Adicionar na seção `services:` (conteúdo completo está em `docs/demandas/DEM-038_CAREPLANNER_CONVERSACIONAL/02_TECNICA.md`, seção "Alterações em `infra/docker-compose.yml`"):

- `kestra` (porta 8080 interna, Traefik → `kestra.intellicare.ia.br`)
- `mongo` (MongoDB 6, replica set rs0)
- `mongo-init-replica` (inicialização do replica set)
- `rocketchat` (porta interna 3001, Traefik → `chat.intellicare.ia.br`)
- `jitsi-web` (Traefik → `meet.intellicare.ia.br`)
- `jitsi-prosody`
- `jitsi-jicofo`
- `jitsi-jvb` (porta UDP `10000:10000/udp` já aberta no firewall)

Adicionar na seção `volumes:`:
```yaml
  kestra_data:
  mongo_data:
  rocketchat_uploads:
  jitsi_web:
  jitsi_prosody:
  jitsi_jicofo:
  jitsi_jvb:
```

---

## 10. Testes — `packages/intellicare-core/tests/test_careplanner_phase_b.py`

Implementar **todos os 10 testes** com adaptadores mockados (nunca chamadas reais de rede).

| # | Tipo | Descrição |
|---|------|-----------|
| 1 | Unit | Transições de estado válidas e inválidas via `TaskStatus.ensure_transition` |
| 2 | Unit | Idempotência: `record_event_if_new` com `event_id` duplicado retorna `(record, False)` |
| 3 | Unit | `cast_channel_conversation_id("85")` → `85` (int); string inválida levanta `ValueError` |
| 4 | Unit | `verify_webhook_signature` aceita HMAC correto e rejeita incorreto |
| 5 | Unit | JWT Jitsi: `generate_room_jwt` → decode confirma `iss=app_id`, `sub=base_url`, `moderator=True/False`, `exp` dentro de prazo |
| 6 | Integração | Fluxo completo com mock: `open_task` → `DISPATCHED`, `message_sent` → `SENT`, `inbound` → `REPLIED` |
| 7 | Integração | Isolamento multi-tenant: correlation_id do tenant A não visível no tenant B |
| 8 | Integração | Webhook sem assinatura (ou assinatura errada) → `HTTPException 403` |
| 9 | Integração | Inbound órfão (rc_room_id desconhecido) → grava `ORPHAN_INBOUND` + retorna `{"orphan": True}` |
| 10 | Integração | `close_task` → status `CLOSED` + `archive_room` chamado no mock RC adapter |

**Estrutura dos mocks**:
```python
class MockRocketChatAdapter:
    def __init__(self):
        self.posted_messages = []
        self.archived_rooms = []
        self.rooms = {}

    async def login_bot(self): pass

    async def ensure_room(self, tenant_slug, patient_ref):
        name = f"ic_{tenant_slug}_{patient_ref}"
        self.rooms[name] = "ROOM_" + name
        return "ROOM_" + name

    async def post_message(self, rc_room_id, text):
        self.posted_messages.append({"room": rc_room_id, "text": text})
        return {"_id": "msg_001"}

    async def archive_room(self, rc_room_id):
        self.archived_rooms.append(rc_room_id)

    def verify_webhook_signature(self, payload, signature):
        return signature == "valid"


class MockKestraAdapter:
    def __init__(self):
        self.resumed = []

    async def resume_execution(self, execution_id, payload=None):
        self.resumed.append(execution_id)
        return {"status": "RUNNING"}
```

---

## Regras críticas de implementação

### BIGINT
Sempre usar `cast_channel_conversation_id()` ao receber `channel_conversation_id` de
qualquer payload externo (webhook, request body). Nunca persistir como string.

### Async ACK
`HTTP 202` do Rocket.Chat em `post_message` → status `DISPATCHED`.
Nunca `FAILED` por causa de 202. `FAILED` apenas em exceção httpx ou RC >= 500.

### Jitsi JWT
`sub` = `JITSI_BASE_URL` (domínio, ex.: `https://meet.intellicare.ia.br`) — **NÃO** o `app_id`.
Validado na spec oficial lib-jitsi-meet e no código V2.

### Isolamento de tenant
`tenant_slug` sempre extraído de `TenantContext` (que vem do JWT Keycloak).
Nunca aceitar `tenant_slug` de parâmetro de corpo de request.

### Webhook inbound
Não exige JWT Keycloak — vem do Rocket.Chat diretamente.
Exige `X-Rocketchat-Signature` válido (HMAC-SHA256).
HMAC inválido → `HTTP 403`.
Inbound sem correlação → `ORPHAN_INBOUND` + `HTTP 202` (nunca 4xx).

### Idempotência
Verificar `event_id` em `care_events` antes de qualquer `INSERT`.
Se duplicado, retornar o registro existente sem alterar estado da tarefa.

---

## Dependências Python

Verificar se já estão no `pyproject.toml` ou `requirements.txt` do serviço:

```
httpx>=0.27
PyJWT>=2.8
```

Se não estiverem, adicionar.

---

## Definição de Pronto (Fase B)

- [ ] Todos os arquivos listados na seção "Arquivos a criar" existem e importam sem erro
- [ ] `loader.py` e `main.py` registram o módulo `careplanner`
- [ ] `docker-compose.yml` contém os 7 novos serviços e 7 volumes
- [ ] `pytest packages/intellicare-core/tests/test_careplanner_phase_b.py` → 10/10 passando
- [ ] `pytest packages/intellicare-core/tests/test_careplanner_phase_a.py` → 3/3 ainda passando (não regressão)
- [ ] Sem imports de módulos V2 ou de classes que não existem no V3
- [ ] `git status` sem arquivos CRLF modificados (`.gitattributes` já garante isso)

---

## Commit esperado

```
feat(DEM-038-B): CarePlanner Fase B — adapters RC/Jitsi/Kestra, services, routes, docker-compose

- adapters/rocketchat.py: porta V2 intellicare-comunicacao (login, ensure_room, post_message, archive, HMAC)
- adapters/jitsi.py: JWT HS256 (sub=base_url), build_room_name
- adapters/kestra.py: resume_execution, get_execution, health_check
- services.py: open_task, process_message_sent, process_inbound, open_video_session, close_task
- api/routes.py: 7 endpoints (tasks/open, events/message-sent, webhooks/inbound, consultations/video, tasks/{id}, tasks, tasks/{id}/close)
- main.py: Module(BaseModule) com startup migrations
- workers/dispatcher.py: stub para Fase D
- module_loader + main.py: registra careplanner
- docker-compose.yml: kestra, mongo, rocketchat, jitsi (4 containers) + volumes
- test_careplanner_phase_b.py: 10 testes (4 unit + 6 integração), mock adapters
```
