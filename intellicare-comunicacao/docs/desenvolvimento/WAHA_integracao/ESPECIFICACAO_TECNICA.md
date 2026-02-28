# EF-COM-034 — Especificação Técnica: Integração WAHA

> **Módulo:** `intellicare-comunicacao`  
> **Canal:** WhatsApp (backend auxiliar)  
> **Stack:** Python 3.11+, httpx, FastAPI, Pydantic 2.x

---

## 1. Arquitetura

### 1.1 Diagrama de Componentes

```
┌─────────────────────────────────────────────────────────────────┐
│                    RoutingEngine (D1)                          │
│                         │                                       │
│                         ▼                                       │
│              DispatcherManager.dispatch("whatsapp", msg)        │
└─────────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                 WhatsAppDispatcher                               │
│                                                                  │
│  backend: Literal["meta", "waha", "auto"]                       │
│                                                                  │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────┐    │
│  │ meta        │    │ waha        │    │ auto            │    │
│  │             │    │             │    │                  │    │
│  │ WhatsAppClient│  │ WAHAClient  │    │ Meta → WAHA     │    │
│  │ (Meta API)  │    │ (WAHA API)  │    │ (fallback)       │    │
│  └──────┬──────┘    └──────┬──────┘    └────────┬────────┘    │
└─────────┼──────────────────┼────────────────────┼─────────────┘
          │                  │                    │
          ▼                  ▼                    ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│ Meta Graph API  │  │ WAHA API        │  │ Meta ou WAHA    │
│ (produção)      │  │ (homologação)   │  │ (fallback)      │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

### 1.2 Fluxo de Envio

```
ChannelMessage (whatsapp)
    │
    ├─ backend=meta  → WhatsAppClient.send_template_message() ou send_text_message()
    │
    ├─ backend=waha  → WAHAClient.send_text()
    │                     │
    │                     └─ POST {WAHA_BASE_URL}/api/sendText
    │                        Body: { session, chatId, text }
    │
    └─ backend=auto  → try WhatsAppClient
                       except → WAHAClient.send_text()
```

---

## 2. Estrutura de Arquivos

```
comunicacao/channels/whatsapp/
├── __init__.py              # Exporta WAHAClient, WAHAConfig
├── client.py                # WhatsAppClient (Meta) — existente
├── waha_client.py           # NOVO — WAHAClient
├── waha_config.py           # NOVO — WAHAConfig (ou estender config.py)
├── config.py                # WhatsAppConfig — existente (estender)
├── dispatcher.py            # WhatsAppDispatcher — MODIFICAR
├── models.py
├── templates.py
└── webhook_handler.py       # Existente (Meta)
```

---

## 3. Contratos API

### 3.1 WAHAClient

```python
# comunicacao/channels/whatsapp/waha_client.py

from typing import Optional
import httpx

class WAHAClient:
    """Cliente HTTP para WAHA (WhatsApp HTTP API)."""

    def __init__(
        self,
        base_url: str,
        session: str = "default",
        api_key: Optional[str] = None,
        timeout: int = 30,
    ):
        self._base_url = base_url.rstrip("/")
        self._session = session
        self._api_key = api_key
        self._timeout = timeout
        self._client = httpx.AsyncClient(
            timeout=timeout,
            headers={
                "Content-Type": "application/json",
                **({"X-Api-Key": api_key} if api_key else {}),
            },
        )

    def _to_chat_id(self, phone: str) -> str:
        """Converte +5511999999999 para 5511999999999@c.us"""
        normalized = phone.replace("+", "").replace(" ", "").replace("-", "")
        return f"{normalized}@c.us"

    async def send_text(self, to: str, text: str) -> dict:
        """
        Envia mensagem de texto.

        Args:
            to: Número no formato +5511999999999
            text: Conteúdo da mensagem

        Returns:
            {"messageId": "..."} ou {"success": True, "message": {...}}

        Raises:
            httpx.HTTPError: Em falha HTTP
        """
        chat_id = self._to_chat_id(to)
        payload = {
            "session": self._session,
            "chatId": chat_id,
            "text": text,
        }
        url = f"{self._base_url}/api/sendText"
        response = await self._client.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
        # WAHA retorna messageId ou message.id
        message_id = data.get("messageId") or (data.get("message", {}).get("id"))
        return {"messageId": message_id, "raw": data}

    async def health_check(self) -> bool:
        """Verifica se WAHA está disponível e sessão ativa."""
        try:
            url = f"{self._base_url}/api/sessions/{self._session}"
            response = await self._client.get(url)
            if response.status_code != 200:
                return False
            data = response.json()
            status = data.get("status") or data.get("state")
            return status in ("STARTED", "started", "CONNECTED")
        except Exception:
            return False

    async def close(self) -> None:
        await self._client.aclose()
```

### 3.2 WAHAConfig

```python
# comunicacao/channels/whatsapp/waha_config.py

from .config import WhatsAppConfig  # ou dataclass

from dataclasses import dataclass
from typing import Optional

@dataclass
class WAHAConfig:
    base_url: str
    session: str = "default"
    api_key: Optional[str] = None
    timeout: int = 30

    @classmethod
    def from_env(cls) -> "WAHAConfig":
        import os
        return cls(
            base_url=os.getenv("WAHA_BASE_URL", "http://localhost:3000"),
            session=os.getenv("WAHA_SESSION", "default"),
            api_key=os.getenv("WAHA_API_KEY"),
            timeout=int(os.getenv("WAHA_TIMEOUT_SECONDS", "30")),
        )
```

### 3.3 Extensão WhatsAppConfig

```python
# Em config.py — adicionar

WHATSAPP_BACKEND = os.getenv("WHATSAPP_BACKEND", "meta")  # meta | waha | auto
```

---

## 4. Modificações no WhatsAppDispatcher

### 4.1 Assinatura do __init__

```python
def __init__(
    self,
    db: AsyncSession,
    config: WhatsAppConfig,
    backend: Literal["meta", "waha", "auto"] = "meta",
    waha_config: Optional[WAHAConfig] = None,
):
    self._db = db
    self._config = config
    self._backend = backend
    self._client_meta = WhatsAppClient(config) if backend in ("meta", "auto") else None
    self._client_waha = WAHAClient(**waha_config) if waha_config and backend in ("waha", "auto") else None
```

### 4.2 Lógica do send()

```python
async def send(self, message: ChannelMessage) -> DispatchResult:
    phone = message.recipient.recipient_id
    text = message.content.body

    if self._backend == "meta":
        return await self._send_with_meta(message)
    elif self._backend == "waha":
        return await self._send_with_waha(message)
    else:  # auto
        result = await self._send_with_meta(message)
        if not result.success:
            result = await self._send_with_waha(message)
        return result
```

### 4.3 _send_with_waha()

```python
async def _send_with_waha(self, message: ChannelMessage) -> DispatchResult:
    try:
        phone = message.recipient.recipient_id
        text = message.content.body
        result = await self._client_waha.send_text(to=phone, text=text)
        message_id = result.get("messageId", "unknown")

        log = ExternalMessageLog(
            channel=self.channel,
            direction="outbound",
            intent_id=message.intent_id,
            correlation_id=message.correlation_id,
            recipient_id=phone,
            provider_message_id=message_id,
            status=ExternalMessageStatus.SENT,
            message_content={"provider": "waha", "text_preview": text[:80]},
            sent_at=datetime.now(UTC),
        )
        self._db.add(log)
        await self._db.commit()

        return DispatchResult(
            success=True,
            channel_message_id=message_id,
            metadata={"provider": "waha"},
        )
    except Exception as exc:
        logger.error("WAHA send failed: %s", exc)
        return DispatchResult(
            success=False,
            error_code="waha_send_failed",
            error_message=str(exc),
        )
```

---

## 5. Variáveis de Ambiente

| Variável | Obrigatório | Default | Descrição |
|----------|-------------|---------|-----------|
| `WHATSAPP_BACKEND` | Não | `meta` | `meta` \| `waha` \| `auto` |
| `WAHA_BASE_URL` | Sim (se waha/auto) | — | Ex: `http://waha:3000` |
| `WAHA_SESSION` | Não | `default` | Nome da sessão WAHA |
| `WAHA_API_KEY` | Não | — | Header X-Api-Key |
| `WAHA_TIMEOUT_SECONDS` | Não | `30` | Timeout HTTP |

---

## 6. Modelos de Dados

Nenhum modelo novo. Reutilizar:

- `ExternalMessageLog` — adicionar `provider` no `message_content` ou metadata
- `ChannelMessage`, `DispatchResult`, `ChannelHealth` — existentes

---

## 7. Testes

### 7.1 Unitários

| Arquivo | Testes |
|---------|--------|
| `tests/test_waha_client.py` | send_text, health_check, _to_chat_id, timeout, erro 4xx/5xx |
| `tests/test_whatsapp_dispatcher.py` | send com backend=waha, send com backend=auto (fallback) |

### 7.2 Integração

| Cenário | Mock |
|---------|------|
| WAHA retorna 200 | httpx mock |
| WAHA retorna 500 | DispatchResult success=False |
| Meta falha, WAHA sucesso | Mock Meta raise, WAHA 200 |

### 7.3 Cobertura

- WAHAClient: ≥ 90%
- Dispatcher (branch waha/auto): ≥ 85%

---

## 8. Métricas Prometheus

```
communication_messages_sent_total{channel="whatsapp", provider="meta|waha"}
communication_messages_failed_total{channel="whatsapp", provider="meta|waha"}
```

---

## 9. Docker Compose (WAHA para dev)

```yaml
# docker-compose.override.yml ou similar

services:
  waha:
    image: devlikeapro/waha:latest
    ports:
      - "3000:3000"
    environment:
      - WAHA_ENGINE=WEBJS
    volumes:
      - waha_sessions:/root/.waha
```

---

## 10. Referências

- [WAHA API](https://waha.devlike.pro/docs/)
- [Send Text](https://waha.devlike.pro/docs/how-to/send-messages/#send-text)
- [Sessions](https://waha.devlike.pro/docs/how-to/sessions/)
