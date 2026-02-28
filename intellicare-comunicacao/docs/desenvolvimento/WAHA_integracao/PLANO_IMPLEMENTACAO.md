# EF-COM-034 — Plano de Implementação: Integração WAHA

> **DEV Atribuído:** A definir  
> **Depende de:** D1 (Engine Roteamento), D4.3 (WhatsApp Meta)  
> **Estimativa total:** 5–7 dias  
> **Prioridade:** MÉDIA

---

## Visão Geral

Este plano detalha o passo a passo para integrar o WAHA como backend auxiliar do canal WhatsApp no módulo intellicare-comunicacao.

---

## Ordem de Execução

| # | Task | Estimativa | Depende de | Entregável |
|---|------|------------|------------|------------|
| 1 | Configuração e WAHAConfig | 0.5 dia | — | waha_config.py, variáveis env |
| 2 | WAHAClient | 1 dia | Task 1 | waha_client.py |
| 3 | Refatorar WhatsAppDispatcher (backend pluggável) | 1.5 dias | Task 2 | dispatcher.py modificado |
| 4 | Registro no app.py e variáveis de ambiente | 0.5 dia | Task 3 | app.py, config |
| 5 | Testes unitários | 1 dia | Tasks 2, 3 | test_waha_client.py, test_dispatcher |
| 6 | Documentação e Docker Compose | 0.5 dia | Task 4 | README, docker-compose |
| 7 | Validação E2E (opcional) | 0.5 dia | Task 6 | Script de teste manual |

**Total: 5,5–7 dias**

---

## Passo a Passo Detalhado

### Passo 1: Configuração e WAHAConfig (0.5 dia)

**Objetivo:** Criar estrutura de configuração para WAHA.

**Ações:**

1. Criar arquivo `comunicacao/channels/whatsapp/waha_config.py`:

```python
"""Configuração WAHA (WhatsApp HTTP API)."""
from dataclasses import dataclass
import os
from typing import Optional

@dataclass
class WAHAConfig:
    base_url: str
    session: str = "default"
    api_key: Optional[str] = None
    timeout: int = 30

    @classmethod
    def from_env(cls) -> "WAHAConfig":
        return cls(
            base_url=os.getenv("WAHA_BASE_URL", "http://localhost:3000"),
            session=os.getenv("WAHA_SESSION", "default"),
            api_key=os.getenv("WAHA_API_KEY") or None,
            timeout=int(os.getenv("WAHA_TIMEOUT_SECONDS", "30")),
        )

    def is_configured(self) -> bool:
        """Retorna True se WAHA está configurado (base_url definido)."""
        return bool(self.base_url and self.base_url.strip())
```

2. Em `comunicacao/channels/whatsapp/config.py` (ou `comunicacao/config.py`), adicionar leitura de `WHATSAPP_BACKEND`.

3. Atualizar `comunicacao/channels/whatsapp/__init__.py` para exportar `WAHAConfig` e `WAHAClient` (após criar).

**Checklist:**
- [ ] WAHAConfig criado
- [ ] WHATSAPP_BACKEND lido
- [ ] Export em __init__.py

---

### Passo 2: WAHAClient (1 dia)

**Objetivo:** Implementar cliente HTTP para API WAHA.

**Ações:**

1. Criar `comunicacao/channels/whatsapp/waha_client.py` conforme especificação técnica (seção 3.1).

2. Implementar:
   - `_to_chat_id(phone)` — converte +5511999999999 → 5511999999999@c.us
   - `send_text(to, text)` — POST /api/sendText
   - `health_check()` — GET /api/sessions/{session}
   - Tratamento de erros (httpx.HTTPStatusError, timeout)

3. Considerar números BR antigos: documentar que pode ser necessário `checkNumberStatus` para alguns números (issue conhecida WAHA #238).

**Exemplo de request:**
```json
POST /api/sendText
{
  "session": "default",
  "chatId": "5511999999999@c.us",
  "text": "Olá! Lembrete: sua consulta é amanhã às 10h."
}
```

**Checklist:**
- [ ] WAHAClient implementado
- [ ] send_text funcionando
- [ ] health_check funcionando
- [ ] Logs adequados

---

### Passo 3: Refatorar WhatsAppDispatcher (1.5 dias)

**Objetivo:** Dispatcher com backends pluggáveis (meta, waha, auto).

**Ações:**

1. **Modificar `__init__` do WhatsAppDispatcher:**
   - Adicionar parâmetros `backend` e `waha_config`
   - Instanciar `WhatsAppClient` apenas se backend in ("meta", "auto")
   - Instanciar `WAHAClient` apenas se backend in ("waha", "auto") e waha_config válido

2. **Extrair `_send_with_meta`:**
   - Mover lógica atual do `send()` para método privado `_send_with_meta(message)`.

3. **Implementar `_send_with_waha`:**
   - Extrair phone e text de `message.recipient.recipient_id` e `message.content.body`
   - Chamar `WAHAClient.send_text()`
   - Criar `ExternalMessageLog` com `provider: "waha"`
   - Retornar `DispatchResult`

4. **Implementar `send()` com branching:**
   - `backend=meta` → `_send_with_meta`
   - `backend=waha` → `_send_with_waha`
   - `backend=auto` → try `_send_with_meta`; se falhar, `_send_with_waha`

5. **Ajustar `health_check`:**
   - Se backend=waha: usar WAHAClient.health_check()
   - Se backend=auto: verificar ambos e incluir no details

6. **Ajustar `get_capabilities`:**
   - Incluir `metadata.backend` e `metadata.provider`

**Checklist:**
- [ ] Dispatcher refatorado
- [ ] backend=meta mantém comportamento atual
- [ ] backend=waha envia texto livre
- [ ] backend=auto faz fallback
- [ ] Logs com provider correto

---

### Passo 4: Registro no app.py (0.5 dia)

**Objetivo:** Registrar WhatsAppDispatcher com backend configurável.

**Ações:**

1. Em `comunicacao/api/app.py`, no bloco de registro do WhatsAppDispatcher:

```python
# Ler backend
whatsapp_backend = os.getenv("WHATSAPP_BACKEND", "meta").lower()
if whatsapp_backend not in ("meta", "waha", "auto"):
    logger.warning("WHATSAPP_BACKEND inválido (%s), usando meta", whatsapp_backend)
    whatsapp_backend = "meta"

waha_config = None
if whatsapp_backend in ("waha", "auto"):
    try:
        waha_config = WAHAConfig.from_env()
        if not waha_config.base_url:
            logger.warning("WAHA_BASE_URL não configurado, desabilitando WAHA")
            waha_config = None
    except Exception as e:
        logger.warning("WAHA config inválida: %s", e)
        waha_config = None

whatsapp_dispatcher = WhatsAppDispatcher(
    db=db,
    config=whatsapp_config,
    backend=whatsapp_backend,
    waha_config=waha_config,
)
dispatcher_manager.register(whatsapp_dispatcher)
```

2. Adicionar variáveis no `.env.example` ou documentação:

```
# WhatsApp Backend: meta (produção) | waha (homologação) | auto (fallback)
WHATSAPP_BACKEND=meta

# WAHA (apenas se backend=waha ou auto)
WAHA_BASE_URL=http://localhost:3000
WAHA_SESSION=default
WAHA_API_KEY=
WAHA_TIMEOUT_SECONDS=30
```

**Checklist:**
- [ ] app.py atualizado
- [ ] Variáveis documentadas
- [ ] Comportamento default=meta preservado

---

### Passo 5: Testes Unitários (1 dia)

**Objetivo:** Cobertura ≥ 85% no código novo.

**Ações:**

1. Criar `tests/test_waha/test_client.py`:
   - `test_to_chat_id` — conversão de número
   - `test_send_text_success` — mock 200, verificar messageId
   - `test_send_text_http_error` — mock 500, verificar exceção
   - `test_health_check_available` — mock 200, status STARTED
   - `test_health_check_unavailable` — mock 500 ou timeout

2. Estender `tests/test_integration/test_d4_integration.py` ou criar `tests/test_whatsapp/test_dispatcher_waha.py`:
   - `test_dispatcher_send_waha_backend` — backend=waha, mock WAHAClient
   - `test_dispatcher_fallback_auto` — Meta falha, WAHA sucesso
   - `test_dispatcher_meta_priority_auto` — Meta sucesso, WAHA não chamado

3. Executar: `pytest tests/test_waha tests/test_whatsapp -v --cov=comunicacao.channels.whatsapp`

**Checklist:**
- [ ] Testes passando
- [ ] Cobertura ≥ 85%
- [ ] Sem regressão nos testes existentes

---

### Passo 6: Documentação e Docker (0.5 dia)

**Objetivo:** Documentar uso e fornecer ambiente WAHA para dev.

**Ações:**

1. Atualizar `docs/04_notificacoes_canais_externos/GUIA_CONFIGURACAO.md`:
   - Seção "WhatsApp WAHA (Auxiliar)"
   - Variáveis WHATSAPP_BACKEND, WAHA_*
   - Exemplo de docker-compose para WAHA

2. Criar ou atualizar `docker-compose.waha.yml` (opcional):

```yaml
services:
  waha:
    image: devlikeapro/waha:latest
    ports:
      - "3000:3000"
    environment:
      - WAHA_ENGINE=WEBJS
    volumes:
      - waha_sessions:/root/.waha

volumes:
  waha_sessions:
```

3. Atualizar `docs/desenvolvimento/WAHA_integracao/README.md` com link para guia.

**Checklist:**
- [ ] GUIA_CONFIGURACAO atualizado
- [ ] docker-compose.waha.yml criado (se aplicável)
- [ ] README da pasta desenvolvimento atualizado

---

### Passo 7: Validação E2E (0.5 dia, opcional)

**Objetivo:** Validar fluxo completo com WAHA real.

**Ações:**

1. Subir WAHA: `docker-compose -f docker-compose.waha.yml up -d`
2. Autenticar sessão: acessar dashboard WAHA, escanear QR Code
3. Configurar: `WHATSAPP_BACKEND=waha`, `WAHA_BASE_URL=http://localhost:3000`
4. Enviar mensagem de teste via API do comunicacao
5. Verificar recebimento no WhatsApp do número de teste

**Checklist:**
- [ ] WAHA sobe e autentica
- [ ] Mensagem enviada pelo IntelliCare chega no WhatsApp
- [ ] Log em ExternalMessageLog com provider=waha

---

## Riscos e Mitigações

| Risco | Mitigação |
|-------|-----------|
| WAHA muda API | Documentar versão; testes com mock |
| Números BR antigos falham | Documentar checkNumberStatus; fallback para Meta se auto |
| Regressão no fluxo Meta | Manter testes existentes; backend=meta como default |

---

## Checklist Final de Entrega

- [ ] WAHAConfig e WAHAClient implementados
- [ ] WhatsAppDispatcher com backend pluggável
- [ ] app.py registra dispatcher com config
- [ ] Testes unitários passando (≥ 85% cobertura)
- [ ] Documentação atualizada (GUIA_CONFIGURACAO, README)
- [ ] Variáveis de ambiente documentadas
- [ ] docker-compose.waha.yml (opcional)
- [ ] Validação E2E com WAHA real (opcional)

---

## Referências

- [ESPECIFICACAO_FUNCIONAL.md](ESPECIFICACAO_FUNCIONAL.md)
- [ESPECIFICACAO_TECNICA.md](ESPECIFICACAO_TECNICA.md)
- [WAHA Quick Start](https://waha.devlike.pro/docs/overview/quick-start/)
