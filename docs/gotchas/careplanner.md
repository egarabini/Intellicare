# Gotchas CarePlanner

Problemas reais observados principalmente em DEM-047, DEM-048, DEM-049, DEM-050 e no codigo atual do modulo.

## `CareplannerService.__init__` cresce e quebra fixtures antigas

### Situacao real
- DEM-047 adicionou `whatsapp`, DEM-048 adicionou `email` e DEM-049 adicionou `sms` ao construtor de [`modules/careplanner/services.py`](/c:/Users/egara/INTELLICARE/modules/careplanner/services.py).

### Sintoma
- Testes em `packages/intellicare-core/tests` falham com `TypeError` por argumentos obrigatorios ausentes quando a fixture continua instanciando a versao antiga do service.

### Fix
- Fazer busca global nas fixtures:

```bash
rg -n "CareplannerService\\(" packages/intellicare-core/tests
```

- Atualizar todas as instancias com `MagicMock()` ou fake adapter para cada dependencia nova.

## Adicionar canal no enum nao basta

### Situacao real
- O dispatcher e `_send_to_channel()` precisam conhecer explicitamente `WHATSAPP`, `EMAIL` e `SMS`.
- O roteamento real esta em [`modules/careplanner/services.py`](/c:/Users/egara/INTELLICARE/modules/careplanner/services.py) e o worker em [`modules/careplanner/workers/dispatcher.py`](/c:/Users/egara/INTELLICARE/modules/careplanner/workers/dispatcher.py).

### Sintoma
- O canal entra no banco, mas a mensagem sai pelo fluxo default de Rocket.Chat ou explode em validacao de `rc_room_id`.

### Fix
- Ao incluir novo valor em `Channel`, revisar juntos:
- `_send_to_channel()`
- `dispatcher_worker/_do_dispatch()`
- payloads de trigger no frontend
- templates por canal

## `rc_room_id` so existe para Rocket.Chat

### Situacao real
- Em [`modules/careplanner/services.py`](/c:/Users/egara/INTELLICARE/modules/careplanner/services.py), Rocket.Chat exige `rc_room_id`; WhatsApp, Email e SMS nao.
- O dispatcher ja trata isso com `rc_room_id = None` para `Channel.WHATSAPP`.

### Sintoma
- Fluxos multicanal falham com `ValueError("rc_room_id obrigatorio para canal ROCKETCHAT")` quando codigo compartilhado tenta reaproveitar o mesmo caminho sem condicional.

### Fix
- Toda chamada de envio precisa decidir o canal antes de validar `rc_room_id`.
- Em `open_task` e `dispatcher`, nao criar room do Rocket.Chat para canais externos.

## Lookup cross-tenant por telefone escala mal

### Situacao real
- `find_active_task_by_phone()` em [`modules/careplanner/repository.py`](/c:/Users/egara/INTELLICARE/modules/careplanner/repository.py) percorre todos os tenants ativos ate achar uma conversa WhatsApp.

### Sintoma
- Em ambiente pequeno funciona bem e mascara o custo.
- Com mais tenants, inbound por telefone vira varredura sequencial e aumenta latencia de webhook.

### Fix
- Aceitavel na V3 com poucos tenants.
- Quando o numero de tenants crescer, criar estrategia de lookup global ou indice publico para telefone/correlation.

## Inbound órfão precisa ser tratado como dado operacional, nao como erro 500

### Situacao real
- `process_inbound()` e `handle_whatsapp_inbound()` registram `careplanner_orphan_inbound_total` e retornam fluxo seguro quando nao encontram correlacao.

### Sintoma
- Sem esse tratamento, webhook de provedor externo passa a gerar erro ruidoso para mensagem atrasada, room arquivada ou telefone sem task ativa.

### Fix
- Manter log + metrica para órfãos.
- Retornar `ok` ou `ignored` ao provedor e investigar pelo observability depois.

## `TenantContext` nao tem `.db` na V3 — usar `tenant_session(ctx)`

### Situacao real
- O briefing da DEM-058 (Oswaldo) usou `ctx.db.fetch()` baseado no padrao da V2.
- Na V3, `TenantContext` e um `@dataclass(frozen=True)` que nao expoe handler `db`.
- O acesso ao banco e feito via `tenant_session(ctx)` conforme padrao de
  `modules/careplanner/repository.py`.

### Sintoma
- Testes retornam `500 Internal Server Error`.
- Log: `AttributeError: 'TenantContext' object has no attribute 'db'`.

### Fix
- Consultar `modules/careplanner/repository.py` ou `modules/florence/repository.py`
  como fonte de verdade para o padrao de acesso ao banco.
- Substituir `ctx.db.fetch(...)` / `ctx.db.fetchrow(...)` pelo equivalente com
  `tenant_session(ctx)`.
- Nunca copiar padroes de repositorios da V2 sem verificar se `TenantContext` expoe `.db`.
