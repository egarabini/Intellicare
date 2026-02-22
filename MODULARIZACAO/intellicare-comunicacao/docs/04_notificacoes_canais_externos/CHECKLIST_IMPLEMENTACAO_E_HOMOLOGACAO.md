# Checklist - Implementacao e Homologacao (EF-COM-030..033)

## 1. Base de seguranca (IAM)
- [ ] Middleware de auth Keycloak ativo no app FastAPI.
- [ ] `POST /api/v1/send` protegido com `get_current_user`.
- [ ] `GET /api/v1/status/{message_id}` protegido com `get_current_user`.
- [ ] `GET /api/v1/intents` protegido com `require_role("admin")`.
- [ ] Evidencia: chamadas sem token retornam `401/403`.

## 2. Endpoint omnicanal
- [ ] `MessageRequest` valida campos obrigatorios (`channel`, `recipient`, `content`).
- [ ] `send_message` integra `RoutingEngine` + `DispatcherManager`.
- [ ] Resposta retorna `message_id`, `status`, `channel`, `recipient`.
- [ ] Erro de canal invalido retorna HTTP coerente (recomendado `400`).

## 3. DispatcherManager
- [ ] Instancia dispatchers por ambiente (`Rocket.Chat`, `Email`, `SMS`, `WhatsApp`).
- [ ] `dispatch(channel, payload)` roteia para o dispatcher correto.
- [ ] Canal nao suportado tratado com erro controlado.
- [ ] Cobrir subject default de email quando `metadata.subject` ausente.

## 4. Rocket.Chat
- [ ] `RocketChatDispatcher.send_message` com headers/token corretos.
- [ ] Modo DEV local simula envio com `status=queued`.
- [ ] Em modo real, falhas HTTP retornam `status=error` e detalhe.

## 5. Email
- [ ] `EmailDispatcher.send_email` envia via SMTP_SSL com login.
- [ ] Retorno de sucesso contem `status=sent`.
- [ ] Excecoes SMTP retornam `status=error`.
- [ ] Validar compatibilidade de porta TLS/SSL com ambiente (465/587).

## 6. SMS
- [ ] `SMSDispatcher` envia payload basico com `to` e `text`.
- [ ] Falhas de provider retornam erro padronizado.
- [ ] Chave/API URL configuradas via env (`SMS_API_URL`, `SMS_API_KEY`).

## 7. WhatsApp
- [ ] `WhatsAppDispatcher` envia payload basico com `to` e `text`.
- [ ] Token/API URL configuradas via env (`WA_API_URL`, `WA_API_TOKEN`).
- [ ] Validar tratamento de timeout/falha de provider.

## 8. Testes automatizados
- [ ] Rodar sempre via venv:
- [ ] `.\.venv\Scripts\python.exe -m pytest -q`
- [ ] Cobrir pelo menos:
- [ ] API (`/send`, `/status`, `/intents`)
- [ ] Manager (`dispatch` por canal, canal invalido)
- [ ] Dispatchers individuais (sucesso e erro)

## 9. Smoke test manual (minimo)
- [ ] `POST /api/v1/send` para `channel=rocketchat`.
- [ ] `POST /api/v1/send` para `channel=email`.
- [ ] `POST /api/v1/send` para `channel=sms`.
- [ ] `POST /api/v1/send` para `channel=whatsapp`.
- [ ] `GET /api/v1/status/{message_id}`.
- [ ] `GET /api/v1/intents` com usuario admin.

## 10. Observabilidade minima recomendada
- [ ] Logar canal, destinatario mascarado, status e `message_id`.
- [ ] Nao logar conteudo sensivel completo em producao.
- [ ] Identificar claramente falhas de provider para troubleshooting.

## 11. Criterio de aceite final
- [ ] Endpoints protegidos e funcionais.
- [ ] 4 canais despachando no fluxo `send`.
- [ ] Erros de canal/provider tratados sem quebrar API.
- [ ] Testes passando na `.venv`.
- [ ] Evidencias de homologacao anexadas (requests/responses e logs).
