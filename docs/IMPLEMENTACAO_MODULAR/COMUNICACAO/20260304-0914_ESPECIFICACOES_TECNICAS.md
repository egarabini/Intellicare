# COMUNICACAO — Especificacoes Tecnicas
**Data:** 2026-03-04
**Versao:** 1.0.0
**Modulo:** intellicare-comunicacao (porta 8005)

---

## 1. Stack Tecnologica

| Componente | Tecnologia |
|-----------|-----------|
| Runtime | Python 3.11 |
| Framework | FastAPI |
| Mensageria | Rocket.Chat API, WAHA (WhatsApp) |
| SMS | Twilio SDK, Zenvia API |
| Email | aiosmtplib + email-validator |
| Video | Jitsi JWT (python-jose) |
| Fila | Redis Streams (intellicare-core) |
| BD | PostgreSQL (log de mensagens) |
| Testes | pytest + pytest-asyncio + respx |

---

## 2. Problema Atual a Corrigir

Os 11 arquivos de teste falham com:
```
ModuleNotFoundError: No module named 'email_validator'
```

**Correcao imediata:**
```toml
# pyproject.toml — adicionar em [project.dependencies]
"email-validator>=2.1.0",
```

Depois de corrigir, 4 testes adicionais precisam ser corrigidos:
- `test_sms/test_dispatcher.py::test_get_status` — SQLAlchemy fixture
- `test_sms/test_providers.py::test_twilio_send` — async/await
- `test_sms/test_providers.py::test_zenvia_send` — async/await
- `test_whatsapp/test_webhook.py::test_handle_status_update` — SQLAlchemy fixture

---

## 3. Arquitetura — 7 Dominios

```
[Modulos Clinicos] → [DispatcherManager] → [Provedores]
       │                     │
       │              ┌──────┴──────────────────────────┐
       │              │      │          │         │      │
       │          RocketChat  WhatsApp  SMS      Email  Jitsi
       │              │
       └──── Redis Streams (eventos assincronos)
```

---

## 4. Configuracao

```env
# Rocket.Chat
ROCKETCHAT_URL=https://rocket.gsi.srv.br
ROCKETCHAT_ADMIN_USER=admin
ROCKETCHAT_ADMIN_PASS=senha

# WhatsApp WAHA
WAHA_BASE_URL=http://waha:3000
WAHA_SESSION=default
WAHA_API_KEY=chave

# SMS
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_FROM_NUMBER=
ZENVIA_TOKEN=

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=

# Jitsi
JITSI_BASE_URL=https://meet.gsi.srv.br
JITSI_SECRET=segredo_jwt

# Infra
REDIS_URL=redis://redis:6379/0
DATABASE_URL=postgresql+asyncpg://...
PORT=8000
```

---

## 5. Correcoes de Testes

### 5.1 Fixtures SQLAlchemy
```python
# tests/conftest.py — padrao correto para async
@pytest_asyncio.fixture
async def session() -> AsyncGenerator[AsyncSession, None]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncSession(engine) as s:
        yield s
```

### 5.2 Testes async SMS
```python
# tests/test_sms/test_providers.py — corrigir para async
@pytest.mark.asyncio
async def test_twilio_send(session):  # era sync
    ...
    result = await provider.send(message)  # era sem await
    assert result.status == "sent"
```

---

*COMUNICACAO v2.0 — Especificacoes Tecnicas — 2026-03-04*
