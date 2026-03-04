# COMUNICACAO — Plano de Implementacao
**Data:** 2026-03-04
**Versao:** 2.0.0
**Estimativa Total:** 3-4 dias
**Prioridade:** ONDA 1 — Quick Win (fix deps critico)

---

## Estado Atual

133 testes implementados, 1 skipped. Suite falha na COLETA por falta de `email-validator`.
Esta e uma correcao simples que desbloqueia toda a suite de testes.

---

## Fase 1 — Correcao Critica (2-3 horas) — BLOQUEADOR IDENTIFICADO (solucao conhecida, execucao pendente)

### Tarefa 1.1 — Adicionar email-validator
```toml
# intellicare-comunicacao/pyproject.toml
[project]
dependencies = [
    ...
    "email-validator>=2.1.0",  # ADICIONAR
    ...
]
```
```bash
pip install -e ".[dev]"
pytest --co -q  # deve mostrar 0 errors
```
- [ ] Editar pyproject.toml
- [ ] Reinstalar dependencias
- [ ] Verificar: 0 erros de coleta

### Tarefa 1.2 — Corrigir 4 testes falhando

**test_sms/test_dispatcher.py::test_get_status:**
```python
# Verificar: fixture de sessao esta async?
# Corrigir conftest.py se necessario (ver padrao em spec tecnica)
```

**test_sms/test_providers.py — test_twilio_send e test_zenvia_send:**
```python
# Adicionar @pytest.mark.asyncio + async def + await
@pytest.mark.asyncio
async def test_twilio_send(mock_twilio):
    result = await provider.send(...)
```

**test_whatsapp/test_webhook.py::test_handle_status_update:**
```python
# Mesma correcao de fixture async
```

- [ ] Corrigir os 4 testes
- [ ] `pytest -q` → 0 falhas
- [ ] Meta: suite completa passa

---

## Fase 2 — Smoke Test de Integracao (Dia 2) — ~4h

### Tarefa 2.1 — Subir com Docker
```bash
docker compose up --build -d
curl http://localhost:8005/api/v1/health
```
- [ ] Container sobe sem erros
- [ ] Health check retorna 200

### Tarefa 2.2 — Validar Rocket.Chat
```bash
curl http://localhost:8005/api/v1/channels
# Deve retornar canais do RC
```
- [ ] Conexao com RC estabelecida
- [ ] Enviar mensagem de teste via API

### Tarefa 2.3 — Validar WhatsApp WAHA
```bash
curl http://localhost:8005/api/v1/whatsapp/status
```
- [ ] Status da sessao WAHA retornado
- [ ] Sessao ativa

---

## Fase 3 — Historico de Mensagens (Dia 3) — ~4h

### Tarefa 3.1 — Modelo de log
```python
# comunicacao/models/message_log.py
class MessageLog(Base):
    __tablename__ = "message_logs"
    id: UUID (PK)
    channel: str       # "rocketchat", "whatsapp", "sms", "email"
    recipient: str     # numero ou email ou RC username
    content: str
    status: str        # "sent", "delivered", "read", "failed"
    provider_id: str   # ID da mensagem no provedor
    error_msg: Optional[str]
    created_at: datetime
    tenant_id: str
```
- [ ] Criar modelo + migracao Alembic
- [ ] Injetar log em todos os dispatchers

### Tarefa 3.2 — Endpoint de historico
```
GET /api/v1/messages/history?recipient={id}&channel={canal}&limit=50
```
- [ ] Implementar endpoint
- [ ] Testar via curl

---

## Checklist de Entrega

| Item | Status |
|------|--------|
| email-validator adicionado | [ ] |
| pytest -q → 0 falhas | [ ] |
| docker compose up → healthy | [ ] |
| Rocket.Chat conectado | [ ] |
| WAHA sessao ativa | [ ] |
| Log de mensagens persistido | [ ] |
| smoke_tests.py inclui COMUNICACAO | [ ] |

---

*COMUNICACAO v2.0 — Plano de Implementacao — 2026-03-04*
