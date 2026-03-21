# Workers e Webhooks

Padroes tirados principalmente de DEM-047, DEM-048, DEM-049, DEM-051 e da implementacao atual do CarePlanner.

## Adapter HTTP assíncrono com cliente lazy

### Evidencia concreta
- DEM-047, DEM-048 e DEM-049 documentam `WhatsAppAdapter`, `EmailAdapter` e `SMSAdapter` com `self._client: httpx.AsyncClient | None = None`.
- Os tres usam `_get_client()` para criar o cliente sob demanda, e `close()` para `aclose()`.

### Regra
- Nao inicializar `httpx.AsyncClient` no `__init__`.
- Adapter recebe apenas settings e cria o cliente quando realmente vai falar com o provedor.
- Todo adapter de canal precisa expor `send_message(...)` e `close()`.

## Retry exponencial curto e previsivel

### Caso real
- Nas tecnicas de DEM-047/048/049, o retry padrao usa `await asyncio.sleep(0.5 * (2 ** (attempt - 1)))` e para em 3 tentativas.
- O worker de dispatch em [`modules/careplanner/workers/dispatcher.py`](/c:/Users/egara/INTELLICARE/modules/careplanner/workers/dispatcher.py) reaplica exatamente a mesma curva com `BACKOFF_BASE = 0.5` e `MAX_RETRIES = 3`.

### Regra
- Retry deve ser curto o bastante para nao prender o worker e previsivel o bastante para debugging.
- Depois da ultima tentativa, a mensagem precisa ir para dead-letter e a task precisa ser marcada como `FAILED`.

## Worker Redis: fila principal e dead-letter

### Evidencia concreta
- [`modules/careplanner/workers/dispatcher.py`](/c:/Users/egara/INTELLICARE/modules/careplanner/workers/dispatcher.py) usa `BLPOP` em `QUEUE_KEY = "careplanner:dispatch:queue"` e move falhas para `DEAD_KEY = "careplanner:dispatch:dead"`.
- O payload que entra na fila ja leva `correlation_id`, `tenant_slug`, `attempts` e `enqueued_at`.

### Regra
- Job de worker precisa ser serializavel em JSON.
- `correlation_id` e `tenant_slug` tem de viajar juntos; sem isso o worker multi-tenant perde contexto.
- Dead-letter nao e opcional em fluxo de mensagem externa.

## Webhook seguro por token e retorno "ignored"

### Evidencia concreta
- [`modules/careplanner/api/routes.py`](/c:/Users/egara/INTELLICARE/modules/careplanner/api/routes.py) expone `/webhook/whatsapp/{token}` e `/webhook/sms/{token}`.
- O webhook do Rocket.Chat valida assinatura por `_ensure_signature(...)`.
- O webhook do WhatsApp retorna `{"status": "ignored"}` para evento nao relevante, `fromMe` e payload sem telefone/texto.

### Regra
- Evento irrelevante nao deve gerar 4xx desnecessario.
- Segredo vazio em adapter de canal costuma significar ambiente dev/staging permissivo; por isso `verify_webhook_secret(token)` precisa suportar esse fluxo conscientemente.

## Inbound órfão precisa virar métrica

### Caso real
- [`modules/careplanner/services.py`](/c:/Users/egara/INTELLICARE/modules/careplanner/services.py) incrementa `careplanner_orphan_inbound_total` quando nao encontra conversa por room, conversation id ou telefone.
- O log tambem registra `Inbound Rocket.Chat sem correlacao` e `WhatsApp inbound órfão`.

### Regra
- Evento órfão precisa ser observavel em log e métrica.
- Resposta de webhook continua `ok/ignored`; quem reage ao problema e a observabilidade, nao o provedor externo.

## Cross-tenant inbound é a exceção aceita

### Evidencia concreta
- `find_active_task_by_phone()` em [`modules/careplanner/repository.py`](/c:/Users/egara/INTELLICARE/modules/careplanner/repository.py) varre tenants ativos para resolver inbound WhatsApp.
- `process_inbound_from_webhook()` em [`modules/careplanner/services.py`](/c:/Users/egara/INTELLICARE/modules/careplanner/services.py) tambem percorre tenants para achar a conversa correta do Rocket.Chat.

### Regra
- Busca cross-tenant so e aceitavel quando o provedor externo nao devolve tenant de origem.
- Quando esse caminho existir, ele precisa estar documentado como tradeoff operacional, porque escala pior que consulta dentro de um tenant conhecido.
