---
tipo: especificacao-tecnica
demanda: DEM-038
titulo: CarePlanner Conversacional Multi-tenant
fase: 4
sprint: "4.1"
status: aprovada
planejador: PLANEJADOR
criado: 2026-03-17
revisado: 2026-03-17
---

# DEM-038 — Especificação Técnica

> Base path: `C:\Users\egara\INTELLICARE\`
> Todos os serviços de integração rodam como containers Docker **no mesmo stack**
> do IntelliCare — comunicação via rede interna Docker, sem chamadas externas entre eles.

| Serviço | Imagem base | Papel |
|---------|-------------|-------|
| **Kestra** | `kestra/kestra:latest-full` | Orquestrador de workflows de jornada |
| **Rocket.Chat** | `rocket.chat:latest` | Canal de mensagens texto com pacientes |
| **MongoDB** | `mongo:6` | Banco do Rocket.Chat |
| **Jitsi Web** | `jitsi/web:stable` | Frontend da videoconsulta |
| **Jitsi Prosody** | `jitsi/prosody:stable` | XMPP server do Jitsi |
| **Jitsi Jicofo** | `jitsi/jicofo:stable` | Conference focus |
| **Jitsi JVB** | `jitsi/jvb:stable` | Video bridge |

## Pré-condições

- `intellicare-core` funcional (DEM-003): auth, session e module_loader.
- Observabilidade ativa (DEM-025): metrics e logs.
- Notificações realtime disponíveis (DEM-026), para integração opcional.
- Infra disponível: PostgreSQL e Redis (já existem no stack).
- **Novos serviços Docker** a adicionar em `infra/docker-compose.yml`: Kestra,
  Rocket.Chat + MongoDB, Jitsi (4 containers).

## Decisões Técnicas Principais

1. **Kestra interno**: container `kestra` na rede Docker `intellicare_net`;
   IntelliCare chama `http://kestra:8080` e Kestra chama `http://intellicare-service:8000`.
2. **Rocket.Chat interno**: container `rocketchat` na mesma rede;
   IntelliCare chama `http://rocketchat:3000` para publicar mensagens;
   Rocket.Chat chama `http://intellicare-service:8000/careplanner/webhooks/rocketchat/inbound`
   para inbound.
3. **Jitsi interno**: stack de 4 containers na mesma rede; IntelliCare gera JWT
   de sala usando `JITSI_APP_SECRET` compartilhado; o link entregue ao paciente
   aponta para o subdomínio público `meet.intellicare.ia.br` (roteado pelo Traefik).
4. **Arquitetura modular**: `BaseModule`, `main.py`, `router.py`, `services.py`,
   `repository.py` — padrão dos outros módulos IntelliCare.
5. **Isolamento por tenant**: todas as operações via `TenantAwareSessionFactory`;
   `tenant_slug` extraído do JWT Keycloak, nunca de parâmetro de corpo.
6. **Assincronia correta**: `2xx` do Rocket.Chat no dispatch não conclui envio;
   jornada só avança para `SENT` com evento assíncrono `MESSAGE_SENT`.
7. **Event sourcing leve**: trilha de `care_events` para auditoria e idempotência
   por `event_id` único.

## Alterações em `infra/docker-compose.yml`

Adicionar os serviços abaixo ao arquivo existente.

### Kestra

```yaml
  kestra:
    image: kestra/kestra:latest-full
    container_name: kestra
    restart: unless-stopped
    command: server standalone --worker-thread=128
    environment:
      KESTRA_CONFIGURATION: |
        datasources:
          postgres:
            url: jdbc:postgresql://db:5432/kestra
            username: ${POSTGRES_USER}
            password: ${POSTGRES_PASSWORD}
        kestra:
          server:
            basic-auth:
              enabled: false
          repository:
            type: postgres
          storage:
            type: local
            local:
              base-path: /app/storage
          queue:
            type: postgres
          tasks:
            defaults: []
          url: http://kestra:8080
    volumes:
      - kestra_data:/app/storage
    networks:
      - intellicare_net
    depends_on:
      - db
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.kestra.rule=Host(`kestra.intellicare.ia.br`)"
      - "traefik.http.routers.kestra.tls.certresolver=le"
      - "traefik.http.services.kestra.loadbalancer.server.port=8080"
```

Nota: Kestra usa o mesmo banco PostgreSQL (`db`) com um database separado
`kestra`. Criar o database antes do deploy:
```sql
CREATE DATABASE kestra OWNER postgres;
```

### Rocket.Chat + MongoDB

```yaml
  mongo:
    image: mongo:6
    container_name: mongo
    restart: unless-stopped
    command: mongod --oplogSize 128 --replSet rs0
    volumes:
      - mongo_data:/data/db
    networks:
      - intellicare_net

  mongo-init-replica:
    image: mongo:6
    networks:
      - intellicare_net
    depends_on:
      - mongo
    command: >
      bash -c "sleep 5 && mongosh --host mongo --eval \"rs.initiate({_id: 'rs0', members: [{_id: 0, host: 'mongo:27017'}]})\""
    restart: on-failure

  rocketchat:
    image: rocket.chat:latest
    container_name: rocketchat
    restart: unless-stopped
    environment:
      MONGO_URL: "mongodb://mongo:27017/rocketchat?replicaSet=rs0"
      MONGO_OPLOG_URL: "mongodb://mongo:27017/local?replicaSet=rs0"
      ROOT_URL: "https://chat.intellicare.ia.br"
      PORT: "3001"           # 3000 já é o Grafana no host; usar 3001 evita confusão
      DEPLOY_PLATFORM: docker
      # Conta bot do IntelliCare (criada via script de seed)
      # ROCKETCHAT_BOT_USER e ROCKETCHAT_BOT_PASSWORD definidos no .env
    volumes:
      - rocketchat_uploads:/app/uploads
    networks:
      - intellicare_net
    depends_on:
      - mongo
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.rocketchat.rule=Host(`chat.intellicare.ia.br`)"
      - "traefik.http.routers.rocketchat.tls.certresolver=le"
      - "traefik.http.services.rocketchat.loadbalancer.server.port=3001"
```

### Jitsi (4 containers)

```yaml
  jitsi-web:
    image: jitsi/web:stable
    container_name: jitsi-web
    restart: unless-stopped
    environment:
      PUBLIC_URL: "https://meet.intellicare.ia.br"
      ENABLE_AUTH: 1
      AUTH_TYPE: jwt
      JWT_APP_ID: "${JITSI_APP_ID}"
      JWT_APP_SECRET: "${JITSI_APP_SECRET}"
      JWT_ACCEPTED_ISSUERS: "${JITSI_APP_ID}"
      JWT_ACCEPTED_AUDIENCES: "jitsi"
      XMPP_DOMAIN: "meet.jitsi"
      XMPP_AUTH_DOMAIN: "auth.meet.jitsi"
      XMPP_MUC_DOMAIN: "muc.meet.jitsi"
      XMPP_INTERNAL_MUC_DOMAIN: "internal-muc.meet.jitsi"
      JICOFO_AUTH_USER: focus
      TZ: America/Sao_Paulo
    volumes:
      - jitsi_web:/config
    networks:
      - intellicare_net
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.jitsi.rule=Host(`meet.intellicare.ia.br`)"
      - "traefik.http.routers.jitsi.tls.certresolver=le"
      - "traefik.http.services.jitsi.loadbalancer.server.port=80"

  jitsi-prosody:
    image: jitsi/prosody:stable
    container_name: jitsi-prosody
    restart: unless-stopped
    environment:
      XMPP_DOMAIN: "meet.jitsi"
      XMPP_AUTH_DOMAIN: "auth.meet.jitsi"
      XMPP_MUC_DOMAIN: "muc.meet.jitsi"
      XMPP_INTERNAL_MUC_DOMAIN: "internal-muc.meet.jitsi"
      JICOFO_AUTH_USER: focus
      JICOFO_AUTH_PASSWORD: "${JICOFO_AUTH_PASSWORD}"
      JVB_AUTH_USER: jvb
      JVB_AUTH_PASSWORD: "${JVB_AUTH_PASSWORD}"
      JWT_APP_ID: "${JITSI_APP_ID}"
      JWT_APP_SECRET: "${JITSI_APP_SECRET}"
      ENABLE_AUTH: 1
      AUTH_TYPE: jwt
      TZ: America/Sao_Paulo
    volumes:
      - jitsi_prosody:/config
    networks:
      - intellicare_net

  jitsi-jicofo:
    image: jitsi/jicofo:stable
    container_name: jitsi-jicofo
    restart: unless-stopped
    environment:
      XMPP_SERVER: jitsi-prosody
      XMPP_DOMAIN: "meet.jitsi"
      XMPP_AUTH_DOMAIN: "auth.meet.jitsi"
      XMPP_INTERNAL_MUC_DOMAIN: "internal-muc.meet.jitsi"
      JICOFO_AUTH_USER: focus
      JICOFO_AUTH_PASSWORD: "${JICOFO_AUTH_PASSWORD}"
      JVB_BREWERY_MUC: jvbbrewery
      TZ: America/Sao_Paulo
    volumes:
      - jitsi_jicofo:/config
    networks:
      - intellicare_net
    depends_on:
      - jitsi-prosody

  jitsi-jvb:
    image: jitsi/jvb:stable
    container_name: jitsi-jvb
    restart: unless-stopped
    environment:
      XMPP_SERVER: jitsi-prosody
      XMPP_DOMAIN: "meet.jitsi"
      XMPP_AUTH_DOMAIN: "auth.meet.jitsi"
      XMPP_INTERNAL_MUC_DOMAIN: "internal-muc.meet.jitsi"
      JVB_AUTH_USER: jvb
      JVB_AUTH_PASSWORD: "${JVB_AUTH_PASSWORD}"
      JVB_BREWERY_MUC: jvbbrewery
      JVB_PORT: 10000
      JVB_TCP_HARVESTER_DISABLED: "true"
      PUBLIC_URL: "https://meet.intellicare.ia.br"
      TZ: America/Sao_Paulo
    ports:
      - "10000:10000/udp"    # UDP para media stream (não vai pelo Traefik)
    volumes:
      - jitsi_jvb:/config
    networks:
      - intellicare_net
    depends_on:
      - jitsi-prosody
```

### Volumes e DNS record adicionais

**Volumes** (adicionar na seção `volumes:` do docker-compose.yml):
```yaml
volumes:
  # ... existentes ...
  kestra_data:
  mongo_data:
  rocketchat_uploads:
  jitsi_web:
  jitsi_prosody:
  jitsi_jicofo:
  jitsi_jvb:
```

**DNS** (Eduardo — adicionar junto dos registros de produção):
```
A  chat.intellicare.ia.br   → IP do VPS
A  meet.intellicare.ia.br   → IP do VPS
A  kestra.intellicare.ia.br → IP do VPS (acesso interno de operação)
```

**Porta UDP 10000** — abrir no firewall do VPS para o Jitsi JVB (media stream).

## Variáveis de Ambiente (`infra/.env.staging` e `infra/.env.production`)

Adicionar às variáveis já existentes. Os nomes seguem a convenção estabelecida
em `intellicare-comunicacao` (V2) para facilitar a migração:

```dotenv
# ─── Kestra ───────────────────────────────────────────────────────────────────
KESTRA_URL=http://kestra:8080
KESTRA_API_KEY=           # deixar vazio se auth desabilitado (dev); preencher em prod
KESTRA_TIMEOUT=30.0

# ─── Rocket.Chat ──────────────────────────────────────────────────────────────
# Nomes alinhados com intellicare-comunicacao V2
ROCKETCHAT_URL=http://rocketchat:3001
ROCKETCHAT_BOT_USERNAME=intellicare_bot
ROCKETCHAT_BOT_PASSWORD=<definir_no_seed>
ROCKETCHAT_WEBHOOK_TOKEN=<hmac_secret_gerado>   # token para validar webhooks inbound
ROCKETCHAT_MAX_REQUESTS_PER_SECOND=10
ROCKETCHAT_MAX_RETRIES=3

# ─── Jitsi ────────────────────────────────────────────────────────────────────
# Nomes alinhados com intellicare-comunicacao V2
JITSI_BASE_URL=https://meet.intellicare.ia.br
JITSI_APP_ID=intellicare
JITSI_APP_SECRET=<secret_gerado>
JITSI_DEFAULT_ROOM_DURATION=120          # minutos (2h para jornadas de paciente)
JITSI_MAX_PARTICIPANTS=10
JICOFO_AUTH_PASSWORD=<gerado>
JVB_AUTH_PASSWORD=<gerado>
```

Notas:
- `ROCKETCHAT_URL=http://rocketchat:3001` usa o nome do container Docker —
  funciona pois `intellicare-service` e `rocketchat` estão na mesma rede
  `intellicare_net`.
- Os nomes de env vars seguem o padrão do V2 (`intellicare-comunicacao`)
  para que o código possa ser portado sem renomear variáveis.

## Estrutura de Arquivos do Módulo

```text
modules/careplanner/
├── __init__.py
├── main.py                    # BaseModule, lifespan, registro de rotas
├── contracts.py               # Enums: TaskStatus, EventType, Channel
├── config.py                  # CareplannerSettings (lê env vars)
├── repository.py              # CRUD: care_tasks, care_conversations, care_events, care_templates, care_video_sessions
├── services.py                # Lógica: open_task, process_callback, process_inbound, open_video_session
├── adapters/
│   ├── __init__.py
│   ├── rocketchat.py          # ensure_room, post_message, archive_room, verify_signature
│   └── jitsi.py              # generate_room_jwt, build_room_url
├── workers/
│   ├── __init__.py
│   └── dispatcher.py         # Enfileira envios e retries via Redis (Fase B)
├── api/
│   ├── __init__.py
│   └── routes.py              # Routers FastAPI
└── migrations.py              # SQL migrations por tenant_schema
```

## Integração no Core

### Registrar módulo no loader

```python
# packages/intellicare-core/intellicare_core/module_loader/loader.py
AVAILABLE_MODULES["careplanner"] = "modules.careplanner.main"
```

### Carregar no app principal

```python
# packages/intellicare-core/intellicare_core/main.py
loader.load("careplanner")
```

## Modelo de Dados (por schema `tenant_{slug}`)

### 1) `care_tasks`

```sql
CREATE TABLE IF NOT EXISTS care_tasks (
    id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    correlation_id       UUID NOT NULL UNIQUE,
    kestra_execution_id  TEXT,
    patient_ref          TEXT NOT NULL,
    task_type            TEXT NOT NULL,
    status               TEXT NOT NULL DEFAULT 'CREATED',
    channel              TEXT NOT NULL DEFAULT 'rocketchat',
    tenant_slug          TEXT NOT NULL,
    metadata             JSONB DEFAULT '{}',
    created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at           TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_care_tasks_status  ON care_tasks(status, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_care_tasks_patient ON care_tasks(patient_ref, created_at DESC);
```

### 2) `care_conversations`

Mapeia `correlation_id` ↔ sala Rocket.Chat.

```sql
CREATE TABLE IF NOT EXISTS care_conversations (
    id                       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    correlation_id           UUID NOT NULL UNIQUE REFERENCES care_tasks(correlation_id),
    channel                  TEXT NOT NULL DEFAULT 'rocketchat',
    channel_conversation_id  BIGINT NOT NULL,
    rc_room_id               TEXT,
    phone_e164               TEXT,
    participant_role         TEXT,
    tenant_slug              TEXT NOT NULL,
    last_interaction_at      TIMESTAMPTZ,
    created_at               TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at               TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_care_conv_channel_id
    ON care_conversations(channel, channel_conversation_id);
```

`channel_conversation_id` é sempre `BIGINT` — converter string recebida antes
de persistir (lição crítica do estudo CarePlanner `So.md`).

### 3) `care_events`

```sql
CREATE TABLE IF NOT EXISTS care_events (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id       TEXT NOT NULL UNIQUE,
    correlation_id UUID REFERENCES care_tasks(correlation_id),
    event_type     TEXT NOT NULL,
    status         TEXT,
    payload        JSONB NOT NULL,
    tenant_slug    TEXT NOT NULL,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_care_events_corr  ON care_events(correlation_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_care_events_type  ON care_events(event_type, created_at DESC);
```

### 4) `care_templates`

```sql
CREATE TABLE IF NOT EXISTS care_templates (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_code TEXT NOT NULL,
    channel       TEXT NOT NULL DEFAULT 'rocketchat',
    content       TEXT NOT NULL,
    variables     JSONB DEFAULT '[]',
    active        BOOLEAN NOT NULL DEFAULT TRUE,
    tenant_slug   TEXT NOT NULL,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (template_code, channel, tenant_slug)
);
```

### 5) `care_video_sessions`

```sql
CREATE TABLE IF NOT EXISTS care_video_sessions (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    correlation_id UUID REFERENCES care_tasks(correlation_id),
    room_name      TEXT NOT NULL,
    clinico_jwt    TEXT NOT NULL,
    patient_jwt    TEXT NOT NULL,
    expires_at     TIMESTAMPTZ NOT NULL,
    clinico_ref    TEXT NOT NULL,
    patient_ref    TEXT NOT NULL,
    tenant_slug    TEXT NOT NULL,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

## Máquina de Estados

```
CREATED
  │ dispatch (Rocket.Chat 2xx)
  ▼
DISPATCHED
  │ EVENT: MESSAGE_SENT (assíncrono)
  ▼
SENT
  │ EVENT: INBOUND_RECEIVED (correlacionado)
  ▼
REPLIED
  │ ação clínica / Kestra decide próximo step
  ▼
CLOSED

Qualquer estado ──falha técnica real──► FAILED
Inbound sem correlação ──────────────► ORPHAN_INBOUND (evento, não muda estado da tarefa)
DISPATCHED sem MESSAGE_SENT > SLA ───► EXPIRED
```

**Regra crítica**: `HTTP 202` do Rocket.Chat → `DISPATCHED`. Nunca `FAILED`.

## Reaproveitamento de Código V2

O `intellicare-comunicacao` (V2) já entregou implementações completas e testadas
dos três adaptadores. O dev **NÃO deve reescrever** — deve **portar**:

| Origem (V2) | Destino (V3 DEM-038) | O que é |
|-------------|----------------------|---------|
| `comunicacao/rocketchat/client.py` (491 linhas) | `adapters/rocketchat.py` | Cliente async httpx com login, send_message, create_channel, invite, health_check, rate limiting, retry |
| `comunicacao/rocketchat/config.py` | parte de `config.py` | RocketChatConfig com `from_env()` |
| `comunicacao/rocketchat/webhook_handler.py` | `adapters/rocketchat.py` | HMAC validation, command parsing |
| `comunicacao/jitsi/client.py` | `adapters/jitsi.py` | JWT HS256, URL builder |
| `comunicacao/jitsi/config.py` | parte de `config.py` | JitsiConfig com `from_env()` |
| `intellicare-nise/nise/services/kestra_client.py` | `adapters/kestra.py` (novo) | Kestra HTTP client: trigger, get_execution, health_check |

Ajustes ao portar:
1. Remover herança de classes V2 (`IChannelDispatcher`, etc.) — não existe no V3
2. Adicionar `tenant_slug` como parâmetro onde o V2 não tinha
3. As env vars são idênticas ao V2 (seção acima) — `from_env()` funciona sem mudança
4. Preservar a lógica de login/token cache do `RocketChatClient` V2

---

## Adaptador Rocket.Chat (`adapters/rocketchat.py`)

**Portar de**: `C:\DOCSHARE\INTELLICARE_V2\intellicare-comunicacao\comunicacao\rocketchat\client.py`

```python
class RocketChatAdapter:
    # URL interna: http://rocketchat:3000

    async def login_bot(self) -> None:
        """POST /api/v1/login com ROCKETCHAT_BOT_USER/PASSWORD.
        Armazena userId + authToken em memória (renovar se 401)."""
        ...

    async def ensure_room(self, tenant_slug: str, patient_ref: str) -> str:
        """Cria ou recupera canal.
        Nome: ic_{tenant_slug}_{patient_ref}
        POST /api/v1/channels.create (ignora erro 'already exists')
        Retorna rc_room_id."""
        ...

    async def post_message(self, rc_room_id: str, text: str) -> dict:
        """POST /api/v1/chat.postMessage. Retorna dict com _id da mensagem."""
        ...

    async def archive_room(self, rc_room_id: str) -> None:
        """POST /api/v1/channels.archive ao fechar jornada."""
        ...

    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """HMAC-SHA256 com ROCKETCHAT_WEBHOOK_TOKEN.
        Header: X-Rocketchat-Signature"""
        ...
```

## Adaptador Jitsi (`adapters/jitsi.py`)

**Portar de**: `C:\DOCSHARE\INTELLICARE_V2\intellicare-comunicacao\comunicacao\jitsi\client.py`

```python
class JitsiAdapter:
    # URL pública para o usuário: JITSI_BASE_URL (= https://meet.intellicare.ia.br)
    # JWT assinado com JITSI_APP_SECRET — compartilhado com jitsi-web (ENABLE_AUTH=1)

    def generate_room_jwt(
        self,
        room_name: str,
        user_id: str,
        user_name: str,
        is_moderator: bool = False,
        expires_in_minutes: int = 120,
    ) -> str:
        """
        Assina JWT com JITSI_APP_SECRET (HS256).
        Payload conforme padrão oficial lib-jitsi-meet:
        {
          "iss": JITSI_APP_ID,        # quem emitiu
          "sub": JITSI_BASE_URL,      # domínio do servidor Jitsi (NÃO o app_id)
          "aud": "jitsi",
          "iat": now,  "nbf": now,  "exp": now + expires_in_minutes*60,
          "room": room_name,
          "moderator": true/false,    # flag top-level
          "context": {
            "user": { "id": user_id, "name": user_name }
          }
        }
        ATENÇÃO: sub = base_url (domínio), não app_id.
        Padrão validado em intellicare-comunicacao V2 e pela spec oficial Jitsi.
        """
        ...

    def get_room_url(self, room_name: str, jwt_token: str) -> str:
        """JITSI_BASE_URL/{room_name}?jwt={token}"""
        ...
```

Nome da sala: `ic_{tenant_slug}_{correlation_id[:8]}`.
- CLINICO recebe JWT com `moderator: true`
- Paciente recebe JWT com `moderator: false`

## Integração Kestra ↔ IntelliCare

Todos os serviços comunicam via rede Docker interna `intellicare_net`:

```
Kestra (http://kestra:8080)
  └─ HTTP Task → POST http://intellicare-service:8000/careplanner/tasks/open
  └─ Webhook Trigger → aguarda POST http://kestra:8080/api/v1/executions/{id}/resume
  └─ HTTP Task → POST http://intellicare-service:8000/careplanner/tasks/{id}/close

IntelliCare (http://intellicare-service:8000)
  └─ Ao receber REPLIED: POST http://kestra:8080/api/v1/executions/{id}/resume

Rocket.Chat (http://rocketchat:3000)
  └─ Webhook Outgoing → POST http://intellicare-service:8000/careplanner/webhooks/rocketchat/inbound
  └─ IntelliCare → POST http://rocketchat:3000/api/v1/chat.postMessage
```

## Contratos de API (MVP)

### 1) Abrir jornada (acionado pelo Kestra)

`POST /careplanner/tasks/open`
`Authorization: Bearer <JWT Keycloak service account>`

```json
{
  "kestra_execution_id": "exec-abc123",
  "patient_ref": "PAC-456",
  "task_type": "CONTATO_INICIAL",
  "contact": { "phone_e164": "+5531999999999", "role": "PACIENTE" },
  "message": { "template_code": "BOAS_VINDAS", "variables": { "nome": "Maria" } }
}
```

Response `202`:
```json
{ "ok": true, "correlation_id": "550e8400-...", "status": "CREATED" }
```

### 2) Callback de entrega confirmada

`POST /careplanner/events/message-sent`
`X-Rocketchat-Signature: <hmac>`

```json
{
  "event_id": "evt-rc-001",
  "correlation_id": "550e8400-...",
  "event_type": "MESSAGE_SENT",
  "refs": { "rc_room_id": "GENERAL_xyz", "channel_conversation_id": "85" }
}
```

### 3) Webhook inbound (Rocket.Chat → IntelliCare)

`POST /careplanner/webhooks/rocketchat/inbound`
`X-Rocketchat-Signature: <hmac>`

```json
{
  "event_id": "evt-in-001",
  "event_type": "INBOUND_RECEIVED",
  "rc_room_id": "GENERAL_xyz",
  "channel_conversation_id": "85",
  "content": "SIM",
  "occurred_at": "2026-03-17T10:00:00Z"
}
```

Correlação não encontrada → `ORPHAN_INBOUND` + retorna `202`.

### 4) Videoconsulta Jitsi

`POST /careplanner/consultations/video`
`Authorization: Bearer <JWT CLINICO>`

```json
{ "correlation_id": "550e8400-...", "clinico_ref": "dr.silva" }
```

Response `201`:
```json
{
  "room_name": "ic_alfa_550e8400",
  "clinico_url": "https://meet.intellicare.ia.br/ic_alfa_550e8400?jwt=<moderator_jwt>",
  "patient_url": "https://meet.intellicare.ia.br/ic_alfa_550e8400?jwt=<participant_jwt>",
  "expires_at": "2026-03-20T16:00:00Z"
}
```

`patient_url` enviado automaticamente ao paciente via Rocket.Chat na sala da jornada.

### 5) Outros

```
GET  /careplanner/tasks/{correlation_id}         # detalhe + últimos 10 eventos
GET  /careplanner/tasks?status=SENT&page=1       # listagem por tenant
POST /careplanner/tasks/{correlation_id}/close   # fecha jornada + arquiva sala RC
```

## Segurança

1. JWT Keycloak obrigatório em todas as APIs internas.
2. HMAC-SHA256 obrigatório nos webhooks do Rocket.Chat (`ROCKETCHAT_WEBHOOK_SECRET`).
3. Anti-replay por `event_id` único + `UNIQUE` constraint em `care_events`.
4. Log sem PII em claro (mascarar `phone_e164`, `content` de mensagens).
5. Jitsi `ENABLE_AUTH=1` + `AUTH_TYPE=jwt` — sala inacessível sem JWT assinado.
6. Kestra UI exposto em `kestra.intellicare.ia.br` com autenticação básica ou
   IP whitelist (acesso restrito à equipe de operação).

## Observabilidade

```
careplanner_dispatch_total{tenant_slug, status}
careplanner_event_total{tenant_slug, event_type}
careplanner_orphan_inbound_total{tenant_slug}
careplanner_video_session_total{tenant_slug}
careplanner_dispatch_to_sent_seconds{tenant_slug}   # histogram
careplanner_inbound_to_close_seconds{tenant_slug}   # histogram
```

## Testes Mínimos

| # | Tipo | Descrição |
|---|------|-----------|
| 1 | Unit | Transições válidas/inválidas da máquina de estados |
| 2 | Unit | Idempotência por `event_id` duplicado |
| 3 | Unit | `channel_conversation_id` string → BIGINT |
| 4 | Unit | HMAC verification do webhook Rocket.Chat |
| 5 | Unit | JWT Jitsi: validade, room name, flag moderador |
| 6 | Integração | Fluxo: `open → dispatch(202) → message-sent → inbound` (mock RC adapter) |
| 7 | Integração | Isolamento multi-tenant: correlação tenant A não vaza tenant B |
| 8 | Integração | Webhook sem assinatura → `403` |
| 9 | Integração | Inbound órfão → `ORPHAN_INBOUND` + `202` |
| 10 | Integração | Fechar jornada → archive_room chamado no adapter (mock) |

## Plano de Entrega

### Fase A — Fundação técnica

- Migrations (5 tabelas)
- `contracts.py`: enums de status e event_type
- `repository.py`: CRUD + idempotência
- `config.py`: leitura de env vars
- Testes unitários (máquina de estados, idempotência, BIGINT cast)

### Fase B — Adaptadores e fluxo assíncrono

- `adapters/rocketchat.py` com mock para testes
- `adapters/jitsi.py`
- `services.py`: open_task, process_message_sent, process_inbound, open_video_session
- `api/routes.py`: todos os endpoints
- Testes de integração (mock adapters)
- **Adicionar serviços ao `docker-compose.yml`** (Kestra, Rocket.Chat, Jitsi)

### Fase C — Integração interna

- Notificações realtime ao CLINICO quando paciente responde
- Gatilho para módulo `cuidado` em `REPLIED`
- Alertas Grafana
- Dashboard operacional básico em GestorUI

### Fase D — Hardening

- Retry/dead-letter para falhas de dispatch
- SLOs e runbooks
- Revisão de segurança (LGPD, HMAC, JWT Jitsi)
- Testes Playwright (GestorUI)

## Riscos e Mitigações

| Risco | Impacto | Mitigação |
|-------|---------|-----------|
| Perda de ponte conversa↔correlação | Inbound órfão | `care_conversations` com upsert transacional |
| Tenant mismatch | Violação LGPD | `tenant_slug` validado via JWT em todos os boundaries |
| Falso `FAILED` por `202` | Estado inconsistente | Separar ACK técnico de confirmação real (RN-02) |
| Duplicidade de callback | Estado duplicado | `event_id` + UNIQUE em `care_events` |
| `channel_conversation_id` string | Erros de join | Cast BIGINT no boundary de entrada |
| Expiração do JWT Jitsi | Link inválido | `expires_at` persistido; alertar se próximo de expirar |
| Sala Rocket.Chat duplicada | Confusão operacional | `ensure_room` faz lookup por nome antes de criar |
| JVB Jitsi precisa porta UDP 10000 | Vídeo não flui | Abrir porta 10000/udp no firewall do VPS |
| Kestra sem autenticação em dev | Exposição UI | Habilitar basic-auth em staging/prod |

## Definição de Pronto

Para virar ticket de implementação (Fase A):

- [x] Stack confirmado: Rocket.Chat + Kestra + Jitsi — todos containers Docker internos
- [x] Modelo de dados aprovado (BIGINT, UNIQUE, índices)
- [x] Contratos JSON validados pelo PLANEJADOR
- [x] `docker-compose.yml` extensions documentadas nesta spec
- [x] Env vars documentadas
- [ ] Eduardo aprova escopo da Fase A antes de iniciar Fase B
- [ ] Gerar segredos: `ROCKETCHAT_WEBHOOK_SECRET`, `JITSI_APP_SECRET`, `JICOFO_AUTH_PASSWORD`, `JVB_AUTH_PASSWORD`
- [ ] DNS: `chat.intellicare.ia.br`, `meet.intellicare.ia.br`, `kestra.intellicare.ia.br`
- [ ] Firewall VPS: abrir porta UDP 10000 (Jitsi JVB)
- [ ] Database `kestra` criado no PostgreSQL antes do primeiro deploy
