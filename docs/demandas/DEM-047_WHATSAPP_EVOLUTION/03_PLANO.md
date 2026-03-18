---
tipo: plano-execucao
demanda: DEM-047
titulo: WhatsApp via Evolution API — Canal CarePlanner
status: pendente
dev: DEV-1
criado: 2026-03-18
---

# DEM-047 — Plano de Execução

## Estimativa

Tempo estimado: 3–4h | Complexidade: média-alta

O núcleo da entrega é o `WhatsAppAdapter` (Bloco 3 de `02_TECNICA.md`) e o
roteamento por canal no dispatcher. O restante (config, webhook, Kestra, UI)
segue padrões já estabelecidos no projeto.

---

## STEPs

### STEP-001 — Verificar pré-requisitos

```bash
# 1. Confirmar que o serviço evolution-api está declarado no docker-compose
grep -n "evolution" infra/docker-compose.yml 2>/dev/null || echo "ainda não existe"

# 2. Confirmar campo phone_e164 na tabela care_conversations
grep -n "phone_e164" modules/careplanner/models.py

# 3. Confirmar Channel enum atual
grep -n "ROCKETCHAT\|WHATSAPP\|Channel" modules/careplanner/contracts.py
```

Critério: entender o estado atual antes de qualquer modificação.

---

### STEP-002 — Atualizar `contracts.py` (Channel enum)

Localizar `Channel(StrEnum)` em `modules/careplanner/contracts.py`.
Adicionar `WHATSAPP = "whatsapp"` conforme **Bloco 1** de `02_TECNICA.md`.

Critério: `python -c "from modules.careplanner.contracts import Channel; print(Channel.WHATSAPP)"` imprime `whatsapp`.

---

### STEP-003 — Atualizar `config.py` (Evolution settings)

Adicionar os 5 campos Evolution em `CareplannerSettings` conforme **Bloco 2** de `02_TECNICA.md`:
- `evolution_api_url`
- `evolution_api_key`
- `evolution_instance_name`
- `evolution_webhook_secret`
- `evolution_max_retries`

Critério: `python -c "from modules.careplanner.config import get_careplanner_settings"` sem ImportError.

---

### STEP-004 — Criar `WhatsAppAdapter`

Criar `modules/careplanner/adapters/whatsapp.py` com o conteúdo completo
do **Bloco 3** de `02_TECNICA.md`.

Métodos a implementar:
- `__init__` (inicializa httpx.AsyncClient com base_url e headers)
- `send_message(phone_e164, text)` → POST `/message/sendText/{instance}`
- `extract_phone_from_jid(remote_jid)` → strip `@s.whatsapp.net`
- `verify_webhook_secret(token)` → comparação segreta com `hmac.compare_digest`
- `close()` → await client.aclose()

Critério: `python -c "from modules.careplanner.adapters.whatsapp import WhatsAppAdapter"` sem erros.

---

### STEP-005 — Atualizar `services.py` (roteamento por canal)

Em `modules/careplanner/services.py`, adicionar o método `_send_to_channel`
conforme **Bloco 4** de `02_TECNICA.md`:

```python
async def _send_to_channel(self, task: CareTask, conversation: CareConversation, text: str):
    if task.channel == Channel.WHATSAPP:
        # usa WhatsAppAdapter
    else:
        # usa RocketChatAdapter (comportamento atual)
```

⚠️ Substituir as chamadas diretas ao `RocketChatAdapter` pelo método `_send_to_channel`
nos fluxos de dispatch e reply. Não quebrar o fluxo RC existente.

Critério: `pytest packages/intellicare-core/tests/test_careplanner_phase_a.py -v` passa (não-regressão RC).

---

### STEP-006 — Adicionar repositório helpers

Em `modules/careplanner/repository.py`, adicionar as duas funções do **Bloco 5a**
de `02_TECNICA.md`:

- `find_active_task_by_phone(db, phone_e164)` — busca cross-tenant
- `get_tenant_by_correlation(db, correlation_id)` — retorna tenant_id da task

Critério: funções importáveis sem erro.

---

### STEP-007 — Adicionar endpoint webhook WhatsApp

Em `modules/careplanner/api/routes.py`, adicionar o endpoint
`POST /webhook/whatsapp/{token}` conforme **Bloco 5b** de `02_TECNICA.md`.

Estrutura do handler:
1. `verify_webhook_secret(token)` → 403 se inválido
2. Filtrar eventos `messages.upsert` (ignorar outros)
3. `extract_phone_from_jid(remoteJid)`
4. `find_active_task_by_phone(db, phone)`
5. `handle_whatsapp_inbound(db, task, message_body)`

Critério: endpoint registrado — `grep -n "webhook/whatsapp" modules/careplanner/api/routes.py`.

---

### STEP-008 — Adicionar `handle_whatsapp_inbound` em `services.py`

Conforme **Bloco 6** de `02_TECNICA.md`. Lógica:
- Verificar se task está em status `SENT`
- Gravar evento `INBOUND_WHATSAPP`
- Transicionar para `REPLIED`
- Chamar `notify_clinico_replied`

Critério: função importável; pytest de não-regressão ainda passa.

---

### STEP-009 — Atualizar `docker-compose.yml` + criar init SQL

Três sub-tarefas conforme **Bloco 9** de `02_TECNICA.md`:

**9a — Init automático do banco `evolution`**

1. Verificar se `postgres` no `docker-compose.yml` já monta `./infra/init-db:/docker-entrypoint-initdb.d`
2. Se não existir, adicionar o volume (não remover volumes existentes)
3. Criar `infra/init-db/02_evolution.sql`:

```sql
SELECT 'CREATE DATABASE evolution'
WHERE NOT EXISTS (
    SELECT FROM pg_database WHERE datname = 'evolution'
)\gexec
```

Isso cria o banco automaticamente na primeira inicialização — **sem precisar
rodar nenhum comando manual**.

**9b — Serviço `evolution-api`**

Adicionar bloco `evolution-api` ao `docker-compose.yml` conforme Bloco 9b do `02_TECNICA.md`.

**9c — `.env.staging.example`**

Adicionar as 4 vars Evolution ao final do arquivo.

Critério: `docker compose config` valida o YAML sem erros.

---

### STEP-010 — Criar Kestra flow WhatsApp

Criar `infra/kestra/flows/careplanner_jornada_whatsapp.yml` conforme
**Bloco 10** de `02_TECNICA.md`.

É idêntico ao `careplanner_jornada_basica.yml` mas com `"channel": "whatsapp"`
no body do trigger.

Adicionar ao `seed_flows.py` (ou script equivalente):
```python
"careplanner_jornada_whatsapp.yml"
```

Critério: arquivo criado; `python seed_flows.py --dry-run` lista o novo flow.

---

### STEP-011 — Atualizar `TriggerJourneyModal.tsx` (GestorUI)

Localizar `frontend/GestorUI/src/components/TriggerJourneyModal.tsx`
(ou nome equivalente — buscar com `grep -rn "TriggerJourney\|trigger.*modal" frontend/GestorUI/src`).

Adicionar seletor de canal conforme **Bloco 11** de `02_TECNICA.md`:

```tsx
<NativeSelect
  label="Canal"
  data={[
    { value: 'rocketchat', label: 'RocketChat' },
    { value: 'whatsapp',   label: 'WhatsApp' },
  ]}
  value={channel}
  onChange={e => setChannel(e.currentTarget.value)}
/>
```

⚠️ Usar `NativeSelect` (não `Select`) por compatibilidade com Mantine 7.

Incluir `channel` no payload do POST `/careplanner/journeys/trigger`.

Critério: `cd frontend/GestorUI && npm run build` sem erros de tipo.

---

### STEP-012 — Rodar testes

```bash
# Backend
pytest packages/intellicare-core/tests/ -q --tb=short -k "careplanner"

# Build frontend
cd frontend/GestorUI && npm run build
```

Os 4 testes do **Bloco 12** de `02_TECNICA.md` podem ser adicionados em
`packages/intellicare-core/tests/test_careplanner_whatsapp.py`.

Critério: pytest passa; build GestorUI OK.

---

### STEP-013 — Commit

```
feat(careplanner): DEM-047 canal WhatsApp via Evolution API
```

Arquivos:
```
modules\careplanner\contracts.py
modules\careplanner\config.py
modules\careplanner\adapters\whatsapp.py
modules\careplanner\services.py
modules\careplanner\repository.py
modules\careplanner\api\routes.py
infra\docker-compose.yml
infra\.env.staging.example
infra\kestra\flows\careplanner_jornada_whatsapp.yml
frontend\GestorUI\src\components\TriggerJourneyModal.tsx
packages\intellicare-core\tests\test_careplanner_whatsapp.py
docs\demandas\DEM-047_WHATSAPP_EVOLUTION\
```

---

## Riscos

| Risco | Mitigação |
|-------|-----------|
| Evolution API ainda não está rodando em staging | STEP-009 só prepara docker-compose; subir o serviço é passo de infra separado |
| `phone_e164` ausente na `care_conversation` ao disparar via WhatsApp | STEP-007 extrai do `remoteJid` e persiste antes do inbound |
| Quebrar fluxo RC existente no `services.py` | STEP-005 exige não-regressão explícita com pytest |
| `TriggerJourneyModal.tsx` usa nome ou path diferente | STEP-011 instrui a buscar com grep antes de editar |
| Versão Evolution API muda schema do webhook | Usar `v2.2.0` fixo conforme Bloco 9; testar com webhook.site antes de apontar para prod |
| `NativeSelect` vs `Select` no Mantine 7 | Bloco 11 especifica `NativeSelect` explicitamente |
