# D2 - Rocket.Chat Integration - Guia de Operação

**Versão**: 1.0  
**Data**: 2026-02-17  
**Status**: ✅ Completo

---

## 📋 Índice

1. [Visão Geral](#visão-geral)
2. [Arquitetura](#arquitetura)
3. [Configuração](#configuração)
4. [Operação](#operação)
5. [Monitoramento](#monitoramento)
6. [Troubleshooting](#troubleshooting)
7. [Manutenção](#manutenção)

---

## 🎯 Visão Geral

A integração Rocket.Chat (D2) fornece comunicação em tempo real entre profissionais de saúde através de:

- **Mensagens em Canais**: Comunicação assíncrona em canais públicos/privados
- **Bot @intellicare**: Comandos clínicos via chat
- **Sincronização de Usuários**: Keycloak → Rocket.Chat automática
- **Webhooks**: Eventos bidirecionais (KC → RC, RC → Bot)

### Componentes Principais

| Componente | Descrição | Arquivo |
|------------|-----------|---------|
| **RocketChatClient** | Cliente HTTP para RC API v7.13.2 | `rocketchat/client.py` |
| **RocketChatDispatcher** | Implementação IChannelDispatcher | `rocketchat/dispatcher.py` |
| **ChannelService** | Gerenciamento de canais | `rocketchat/channel_service.py` |
| **UserSyncService** | Sincronização KC → RC | `sync/user_sync_service.py` |
| **WebhookHandler** | Processamento de webhooks RC | `rocketchat/webhook_handler.py` |
| **IntelliCareBot** | Processador de comandos | `bot/intellicare_bot.py` |

---

## 🏗️ Arquitetura

### Fluxo de Sincronização de Usuários

```
Keycloak (Novo Usuário)
    │
    ▼
Keycloak Webhook Event
    │
    ▼
POST /api/v1/sync/keycloak-event
    │
    ▼
UserSyncService.handle_keycloak_event()
    │
    ├── 1. Buscar dados do usuário (KeycloakAdminClient)
    ├── 2. Buscar roles do usuário
    ├── 3. Mapear roles (KC → RC)
    ├── 4. Verificar se existe no RC
    ├── 5. Criar usuário no RC (se não existe)
    └── 6. Salvar UserSyncRecord
    │
    ▼
Usuário criado no Rocket.Chat ✅
```

### Fluxo de Comando do Bot

```
Usuário envia "/paciente patient-123" no RC
    │
    ▼
Rocket.Chat Outgoing Webhook
    │
    ▼
POST /api/v1/webhooks/rocketchat
    │
    ▼
RocketChatWebhookHandler
    │
    ├── 1. Validar token
    ├── 2. Filtrar mensagens de bot
    ├── 3. Detectar comando (/)
    └── 4. Parsear comando e args
    │
    ▼
IntelliCareBot.handle_paciente(["patient-123"])
    │
    ├── 1. Validar argumentos
    ├── 2. Buscar dados do paciente
    └── 3. Formatar resposta (Markdown)
    │
    ▼
RocketChatClient.send_message()
    │
    ▼
Resposta enviada ao canal ✅
```

---

## ⚙️ Configuração

### Variáveis de Ambiente

```bash
# Rocket.Chat
ROCKETCHAT_URL=https://rocket.gsi.srv.br
ROCKETCHAT_BOT_USERNAME=intellicare-bot
ROCKETCHAT_BOT_PASSWORD=<secret>
ROCKETCHAT_ADMIN_USER_ID=<admin_user_id>
ROCKETCHAT_ADMIN_AUTH_TOKEN=<admin_auth_token>
ROCKETCHAT_WEBHOOK_TOKEN=<webhook_secret>

# Keycloak Admin
KEYCLOAK_ADMIN_URL=https://keycloak.gsi.srv.br
KEYCLOAK_ADMIN_REALM=master
KEYCLOAK_ADMIN_USERNAME=admin
KEYCLOAK_ADMIN_PASSWORD=<secret>
KEYCLOAK_TARGET_REALM=bemcuidar

# Comunicação
COMUNICACAO_PORT=8005
```

### Configuração do Rocket.Chat

#### 1. Criar Usuário Bot

```bash
# Via RC Admin UI
1. Acesse: https://rocket.gsi.srv.br/admin/users
2. Clique em "New User"
3. Preencha:
   - Name: IntelliCare Bot
   - Username: intellicare-bot
   - Email: bot@intellicare.local
   - Password: <gerar senha forte>
   - Roles: bot, user
4. Salvar
```

#### 2. Configurar Outgoing Webhook

```bash
# Via RC Admin UI
1. Acesse: https://rocket.gsi.srv.br/admin/integrations
2. Clique em "New Integration" → "Outgoing WebHook"
3. Preencha:
   - Event Trigger: Message Sent
   - Enabled: Yes
   - Channel: #all_public_channels (ou específico)
   - Trigger Words: / (para comandos)
   - URLs: http://localhost:8005/api/v1/webhooks/rocketchat
   - Token: <gerar token seguro>
4. Salvar
```

### Configuração do Keycloak

#### 1. Configurar Event Listener

```bash
# Via Keycloak Admin UI
1. Acesse: https://keycloak.gsi.srv.br/admin
2. Selecione realm "bemcuidar"
3. Events → Config
4. Event Listeners: Adicionar "webhook"
5. Salvar
```

#### 2. Configurar Webhook URL

```bash
# Via Keycloak Admin UI (ou REST API)
1. Configurar webhook URL: http://localhost:8005/api/v1/sync/keycloak-event
2. Eventos: REGISTER, UPDATE, DELETE
```

---

## 🚀 Operação

### Iniciar Serviço

```bash
cd ./intellicare-comunicacao

# Ativar ambiente virtual
source venv/bin/activate  # Linux/Mac
# ou
.\venv\Scripts\activate  # Windows

# Iniciar servidor
uvicorn comunicacao.api.app:create_app --factory --host 0.0.0.0 --port 8005
```

### Comandos do Bot

| Comando | Descrição | Exemplo |
|---------|-----------|---------|
| `/paciente {id}` | Mostra informações do paciente | `/paciente patient-123` |
| `/lab {id}` | Mostra resultados de laboratório | `/lab patient-123` |
| `/alerta {id}` | Mostra detalhes do alerta | `/alerta alert-456` |
| `/escalar {id}` | Escala alerta para nível superior | `/escalar alert-456` |
| `/teleconsulta {id}` | Cria sala Jitsi | `/teleconsulta patient-123` |
| `/ajuda` | Mostra comandos disponíveis | `/ajuda` |

### Sincronização Manual de Usuários

```python
from comunicacao.sync import UserSyncService

service = UserSyncService()

# Sincronizar usuário específico
sync_record = await service.sync_user("keycloak-user-id")
print(f"Status: {sync_record.sync_status}")

# Reconciliação completa (todos os usuários)
stats = await service.reconcile_all_users()
print(f"Sincronizados: {stats['synced']}/{stats['total']}")
```

### Criar Canal via API

```bash
curl -X POST "http://localhost:8005/api/v1/rocketchat/channel" \
  -H "Authorization: Bearer <keycloak_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "channel_type": "case",
    "identifier": "patient-123",
    "members": ["dr.joao", "enf.ana"],
    "read_only": false
  }'
```

### Enviar Mensagem via API

```bash
curl -X POST "http://localhost:8005/api/v1/rocketchat/message" \
  -H "Authorization: Bearer <keycloak_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "room_id": "xyz789",
    "text": "**Alerta**: Glicemia elevada detectada",
    "alias": "IntelliCare",
    "emoji": ":hospital:"
  }'
```

---

## 📊 Monitoramento

### Health Check

```bash
# Verificar saúde do serviço
curl http://localhost:8005/api/v1/health

# Verificar conexão com RC
curl http://localhost:8005/api/v1/rocketchat/health
```

### Logs

```bash
# Logs do serviço
tail -f logs/comunicacao.log

# Filtrar logs de RC
tail -f logs/comunicacao.log | grep "rocketchat"

# Filtrar logs de sync
tail -f logs/comunicacao.log | grep "sync"
```

### Métricas (Prometheus)

```bash
# Endpoint de métricas
curl http://localhost:8005/metrics

# Métricas relevantes:
# - rocketchat_messages_sent_total
# - rocketchat_channels_created_total
# - user_sync_total{status="synced"}
# - user_sync_total{status="error"}
# - bot_commands_total{command="paciente"}
```

---

## 🔧 Troubleshooting

### Problema: Bot não responde a comandos

**Sintomas**:
- Usuário envia `/paciente patient-123` no RC
- Bot não responde

**Diagnóstico**:
```bash
# 1. Verificar logs
tail -f logs/comunicacao.log | grep "webhook"

# 2. Verificar se webhook está configurado no RC
# Acesse: https://rocket.gsi.srv.br/admin/integrations

# 3. Testar webhook manualmente
curl -X POST "http://localhost:8005/api/v1/webhooks/rocketchat" \
  -H "Content-Type: application/json" \
  -d '{
    "_id": "test",
    "channel_id": "ch123",
    "channel_name": "test",
    "user_id": "user123",
    "user_name": "test.user",
    "text": "/ajuda",
    "ts": "2026-02-17T10:30:00Z"
  }'
```

**Soluções**:
1. Verificar se `ROCKETCHAT_WEBHOOK_TOKEN` está configurado
2. Verificar se outgoing webhook está habilitado no RC
3. Verificar se URL do webhook está correta
4. Verificar logs para erros de autenticação

---

### Problema: Usuários não sincronizam do Keycloak

**Sintomas**:
- Novo usuário criado no Keycloak
- Usuário não aparece no Rocket.Chat

**Diagnóstico**:
```bash
# 1. Verificar logs de sync
tail -f logs/comunicacao.log | grep "sync"

# 2. Verificar status de sync
python -c "
from comunicacao.sync import UserSyncService
import asyncio

async def check():
    service = UserSyncService()
    records = await service.get_all_sync_records()
    for r in records:
        print(f'{r.username}: {r.sync_status}')

asyncio.run(check())
"
```

**Soluções**:
1. Verificar se webhook do Keycloak está configurado
2. Verificar credenciais do Keycloak Admin (`KEYCLOAK_ADMIN_*`)
3. Executar reconciliação manual
4. Verificar se usuário está habilitado no Keycloak

---

### Problema: Erro ao criar canal

**Sintomas**:
- API retorna erro ao criar canal
- `{"success": false, "error": "..."}`

**Diagnóstico**:
```bash
# Verificar logs
tail -f logs/comunicacao.log | grep "channel"
```

**Soluções**:
1. Verificar se bot tem permissões no RC
2. Verificar se nome do canal já existe
3. Verificar se membros existem no RC
4. Verificar credenciais do bot (`ROCKETCHAT_BOT_*`)

---

## 🔄 Manutenção

### Reconciliação Periódica de Usuários

Recomenda-se executar reconciliação completa a cada 6 horas:

```bash
# Cron job (Linux)
0 */6 * * * cd /path/to/intellicare-comunicacao && python -c "
from comunicacao.sync import UserSyncService
import asyncio

async def reconcile():
    service = UserSyncService()
    stats = await service.reconcile_all_users()
    print(f'Reconciliação: {stats}')

asyncio.run(reconcile())
"
```

### Limpeza de Logs

```bash
# Rotacionar logs (logrotate)
/var/log/intellicare/comunicacao.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
}
```

### Backup de Configurações

```bash
# Backup de variáveis de ambiente
cp .env .env.backup.$(date +%Y%m%d)

# Backup de configurações do RC (via API)
# TODO: Implementar script de backup
```

---

## 📚 Referências

- [Rocket.Chat API Documentation](https://developer.rocket.chat/reference/api)
- [Keycloak Admin REST API](https://www.keycloak.org/docs-api/latest/rest-api/)
- [ESPECIFICACAO_FUNCIONAL.md](./ESPECIFICACAO_FUNCIONAL.md)
- [ESPECIFICACAO_TECNICA.md](./ESPECIFICACAO_TECNICA.md)

---

**Última Atualização**: 2026-02-17  
**Responsável**: Equipe IntelliCare

