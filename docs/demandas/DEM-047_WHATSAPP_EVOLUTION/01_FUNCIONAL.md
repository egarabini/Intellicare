---
tipo: especificacao-funcional
demanda: DEM-047
titulo: WhatsApp como Canal CarePlanner via Evolution API
sprint: "5.1"
status: pronto-para-dev
planejador: Claude (PLANEJADOR)
criado: 2026-03-18
depende_de: [DEM-038, DEM-041]
habilita: [DEM-048]
tags: [careplanner, whatsapp, evolution-api, canal, backend, frontend, p1]
---

# DEM-047 — WhatsApp como Canal CarePlanner (Evolution API)

## Objetivo

O CarePlanner hoje opera exclusivamente via Rocket.Chat. No Brasil, WhatsApp
é o canal de comunicação primário de 98% dos pacientes — instalar o app RC
no celular do paciente cria fricção desnecessária. Esta DEM adiciona WhatsApp
como segundo canal do CarePlanner via **Evolution API** (open-source,
self-hosted, Docker-native, cliente Python disponível), sem remover o RC.

O gestor escolhe o canal ao criar a jornada. O restante do fluxo
(máquina de estados, Kestra, notificações, templates) permanece idêntico.

---

## Estado Atual vs. Estado Desejado

| Item | Hoje | DEM-047 |
|------|------|---------|
| `Channel` enum | `ROCKETCHAT` | ✅ + `WHATSAPP` |
| Envio de mensagem ao paciente | RC room | ✅ RC room **ou** WhatsApp número E.164 |
| Recebimento de resposta do paciente | webhook RC | ✅ webhook RC **ou** webhook Evolution API |
| TriggerJourneyModal — canal | sem seletor | ✅ `NativeSelect` RC / WhatsApp |
| Evolution API no docker-compose | ❌ | ✅ serviço `evolution-api` |
| Kestra flow WhatsApp | ❌ | ✅ `careplanner_jornada_whatsapp.yml` |
| Templates com canal WHATSAPP | ❌ | ✅ seed de 4 templates `channel=whatsapp` |

---

## Critérios de Aceite

1. `POST /careplanner/journeys/trigger` aceita `channel: "whatsapp"`. A jornada
   é criada com `Channel.WHATSAPP` e o dispatcher envia via Evolution API.

2. Quando o paciente responde no WhatsApp, o webhook `POST /careplanner/webhook/whatsapp`
   recebe a mensagem, identifica a `care_task` pelo telefone (`phone_e164`), e
   transita o status para `REPLIED` — idêntico ao fluxo RC.

3. O TriggerJourneyModal exibe `NativeSelect` com opções "Rocket.Chat" e
   "WhatsApp". Quando "WhatsApp" selecionado, campo `contact_phone` torna-se
   obrigatório (telefone E.164 do paciente, ex: `+5511999999999`).

4. Templates listados no Select do TriggerModal filtram por canal selecionado
   (`active=true AND channel=whatsapp` ou `channel=rocketchat`).

5. Seed de 4 templates `channel=whatsapp` no startup: `boas_vindas_wa`,
   `check_in_wa`, `lembrete_medicacao_wa`, `teleconsulta_confirmacao_wa`
   (conteúdo idêntico aos RC, só o canal difere).

6. Evolution API acessível em `http://evolution-api:8080` no docker-compose
   interno. Variáveis de ambiente documentadas no `.env.staging.example`.

7. `pytest packages/intellicare-core/tests/test_careplanner_phase_h.py -v`
   → 4 passed.

8. `npm run build` no GestorUI sem erros.

---

## O que NÃO está incluído

- WhatsApp Business API oficial da Meta (custo por mensagem — Evolution API
  via Baileys é gratuito para volume moderado)
- Envio de mídia (imagens, áudio, documentos) via WhatsApp
- Templates com variáveis dinâmicas renderizadas (ex: `{{nome_paciente}}`)
- WhatsApp no ClinicoUI ou PacienteUI
- SMS (DEM-048 futura)
- Listmonk email (DEM-049 futura)

---

## Notas para o Agente Desenvolvedor

**Evolution API — Como funciona:**
- Self-hosted, Docker-native, REST API com autenticação por `apikey` no header
- Uma **instância** = um número WhatsApp conectado (QR Code no primeiro uso)
- Enviar mensagem: `POST /message/sendText/{instanceName}`
  body: `{"number": "5511999999999", "textMessage": {"text": "Olá!"}}`
- Webhook inbound: Evolution faz POST no nosso endpoint com estrutura:
  ```json
  {
    "event": "messages.upsert",
    "instance": "intellicare",
    "data": {
      "key": { "remoteJid": "5511999999999@s.whatsapp.net", "fromMe": false },
      "message": { "conversation": "texto do paciente" }
    }
  }
  ```
- Auth header: `apikey: <EVOLUTION_API_KEY>`

**Identificação do paciente no WhatsApp:**
O `phone_e164` já está na tabela `care_conversations`. Para WhatsApp, ele
é o identificador primário da conversa (não há room_id). O webhook chega com
`remoteJid = "5511999999999@s.whatsapp.net"` — extrair número com
`remoteJid.split("@")[0]` e comparar com `phone_e164` (sem o `+`).

**`rc_room_id` em conversas WhatsApp:**
Para jornadas WhatsApp, `rc_room_id` fica `None`. O campo já é nullable
na tabela — sem migration necessária.

**Segurança do webhook WhatsApp:**
A Evolution API suporta `webhookByEvents` e pode assinar com HMAC.
Configurar `EVOLUTION_WEBHOOK_SECRET` e verificar header
`X-Evolution-Signature` (similar ao `verify_webhook_signature` do RC).
Se a versão instalada não suportar HMAC, usar token fixo no path:
`POST /careplanner/webhook/whatsapp/{token}` e comparar com env var.
