# 🔧 ESPECIFICAÇÃO TÉCNICA: COMUNICAÇÃO E WORKFLOW

---

## 📌 INFORMAÇÕES DO PROJETO

**ID**: PROJ-05-COMUNICACAO-WORKFLOW-TECH  
**Nome**: Sistema de Comunicação e Workflow Integrado - Especificação Técnica  
**Responsável**: DEV1  
**Data**: 26/03/2026  
**Versão**: 1.0  
**Status**: 📝 Em Especificação

---

## 🎯 OBJETIVO TÉCNICO

Definir a arquitetura técnica detalhada para implementação do sistema de comunicação e workflow usando:
- **Rocket.Chat** (Messaging Platform)
- **Jitsi** (Video Conferencing)
- **Flowise** (AI/RAG/Chatbots)
- **Kestra** (Workflow Orchestration)

---

## 🏗️ ARQUITETURA TÉCNICA

### **Visão Geral**

```
┌─────────────────────────────────────────────────────────────────┐
│                    INTELLICARE ECOSYSTEM                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ Rocket.Chat  │  │    Jitsi     │  │   Flowise    │         │
│  │   :3000      │  │    :8443     │  │    :3001     │         │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘         │
│         │                  │                  │                 │
│         └──────────────────┼──────────────────┘                 │
│                            │                                    │
│                    ┌───────┴────────┐                          │
│                    │     Kestra     │                          │
│                    │     :8080      │                          │
│                    └───────┬────────┘                          │
│                            │                                    │
│  ┌─────────────────────────┴─────────────────────────────┐    │
│  │         IntelliCare Communication Module              │    │
│  │              (FastAPI Backend :8010)                  │    │
│  └─────────────────────────┬─────────────────────────────┘    │
│                            │                                    │
│  ┌─────────────────────────┴─────────────────────────────┐    │
│  │              PostgreSQL 15+ (Database)                │    │
│  │  Schemas: comunicacao, flowise, kestra                │    │
│  └───────────────────────────────────────────────────────┘    │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │              Redis 7 (Cache + Events)                   │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │              Keycloak (SSO/Authentication)              │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 💻 STACK TECNOLÓGICO

### **1. Rocket.Chat**

| Componente | Versão | Descrição |
|------------|--------|-----------|
| Rocket.Chat | 6.5+ | Plataforma de comunicação open-source |
| MongoDB | 6.0+ | Database do Rocket.Chat |
| Node.js | 14+ | Runtime do Rocket.Chat |

**Configuração**:
```yaml
# docker-compose.yml
rocketchat:
  image: rocket.chat:6.5
  environment:
    - MONGO_URL=mongodb://mongo:27017/rocketchat
    - ROOT_URL=https://chat.gsi.srv.br
    - PORT=3000
    - ADMIN_USERNAME=admin
    - ADMIN_PASS=${ROCKETCHAT_ADMIN_PASSWORD}
    - OVERWRITE_SETTING_Show_Setup_Wizard=completed
  ports:
    - "3000:3000"
  depends_on:
    - mongo
```

**Integrações**:
- **Keycloak SSO**: OAuth2/OIDC
- **Jitsi**: Video call integration
- **Webhooks**: Outgoing webhooks para Kestra
- **Bots**: Hubot/Botpress integration

---

### **2. Jitsi Meet**

| Componente | Versão | Descrição |
|------------|--------|-----------|
| Jitsi Meet | stable | Frontend web |
| Jicofo | stable | Focus component |
| JVB | stable | Video bridge |
| Prosody | 0.12+ | XMPP server |

**Configuração**:
```yaml
# docker-compose.yml
jitsi-web:
  image: jitsi/web:stable
  environment:
    - ENABLE_AUTH=1
    - ENABLE_GUESTS=1
    - AUTH_TYPE=jwt
    - JWT_APP_ID=intellicare
    - JWT_APP_SECRET=${JITSI_JWT_SECRET}
    - PUBLIC_URL=https://meet.gsi.srv.br
  ports:
    - "8443:443"
    - "8000:80"
```

**Integrações**:
- **Rocket.Chat**: Embedded video calls
- **JWT Authentication**: Keycloak tokens
- **Recording**: Jibri (opcional)

---

### **3. Flowise**

| Componente | Versão | Descrição |
|------------|--------|-----------|
| Flowise | 1.8+ | RAG/Chatbot platform |
| Ollama | latest | Local LLM engine |
| PostgreSQL | 15+ | Flowise database |
| pgvector | 0.5+ | Vector embeddings |

**Configuração**:
```yaml
# docker-compose.yml
flowise:
  image: flowiseai/flowise:latest
  environment:
    - DATABASE_TYPE=postgres
    - DATABASE_HOST=postgres
    - DATABASE_PORT=5432
    - DATABASE_USER=admin_flowise
    - DATABASE_PASSWORD=${FLOWISE_DB_PASSWORD}
    - DATABASE_NAME=intellicare
    - DATABASE_SCHEMA=flowise
    - PORT=3001
    - FLOWISE_USERNAME=admin
    - FLOWISE_PASSWORD=${FLOWISE_PASSWORD}
    - OLLAMA_BASE_URL=http://ollama:11434
  ports:
    - "3001:3001"
  depends_on:
    - postgres
    - ollama
```

**Chatflows**:
1. **Geralda Bot**: Suporte a pacientes
2. **Wanda Bot**: Suporte a profissionais
3. **Dr. Nise Bot**: Treinamento médico
4. **Florence Bot**: Análise laboratorial
5. **Oswaldo Bot**: Doenças crônicas

---

### **4. Kestra**

| Componente | Versão | Descrição |
|------------|--------|-----------|
| Kestra | latest | Workflow orchestration |
| PostgreSQL | 15+ | Kestra database |

**Configuração**:
```yaml
# docker-compose.yml
kestra:
  image: kestra/kestra:latest
  command: server standalone
  environment:
    KESTRA_CONFIGURATION: |
      datasources:
        postgres:
          url: jdbc:postgresql://postgres:5432/intellicare
          driverClassName: org.postgresql.Driver
          username: admin_kestra
          password: ${KESTRA_DB_PASSWORD}
      kestra:
        server:
          basic-auth:
            enabled: true
            username: admin@kestra.io
            password: ${KESTRA_ADMIN_PASSWORD}
        repository:
          type: postgres
        queue:
          type: postgres
        url: https://kestra.gsi.srv.br/
  ports:
    - "8080:8080"
  depends_on:
    - postgres
```

**Workflows**:
- Comunicação automatizada
- Integração entre módulos
- Agendamentos recorrentes
- ETL/ELT de dados

---

## 🗄️ BANCO DE DADOS

### **Schema: `comunicacao`**

```sql
-- Tabela de usuários (sincronizada com Keycloak)
CREATE TABLE comunicacao.users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    keycloak_id UUID NOT NULL UNIQUE,
    rocketchat_id VARCHAR(50) UNIQUE,
    username VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    roles JSONB DEFAULT '[]',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Tabela de canais/salas
CREATE TABLE comunicacao.channels (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rocketchat_room_id VARCHAR(50) UNIQUE,
    name VARCHAR(100) NOT NULL,
    type VARCHAR(20) NOT NULL, -- 'direct', 'group', 'channel'
    description TEXT,
    members JSONB DEFAULT '[]', -- [user_id, ...]
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Tabela de mensagens (auditoria)
CREATE TABLE comunicacao.messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    channel_id UUID REFERENCES comunicacao.channels(id),
    user_id UUID REFERENCES comunicacao.users(id),
    rocketchat_message_id VARCHAR(50),
    content TEXT NOT NULL,
    message_type VARCHAR(20) DEFAULT 'text', -- 'text', 'file', 'video_call'
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Índices
CREATE INDEX idx_messages_channel ON comunicacao.messages(channel_id, created_at DESC);
CREATE INDEX idx_messages_user ON comunicacao.messages(user_id, created_at DESC);
CREATE INDEX idx_channels_type ON comunicacao.channels(type);
```

---

## 🔌 API DO MÓDULO COMUNICAÇÃO

### **Estrutura FastAPI**

```python
# comunicacao/api/main.py
from fastapi import FastAPI, Depends
from intellicare_auth import get_current_user, requires_role

app = FastAPI(
    title="IntelliCare Comunicação",
    version="1.0.0",
    description="Módulo de Comunicação e Workflow"
)

# Endpoints
@app.get("/api/v1/health")
async def health():
    """Health check"""
    return {"status": "healthy"}

@app.get("/api/v1/channels")
async def list_channels(user: dict = Depends(get_current_user)):
    """Listar canais do usuário"""
    pass

@app.post("/api/v1/channels")
@requires_role("intellicare_admin")
async def create_channel(user: dict = Depends(get_current_user)):
    """Criar novo canal"""
    pass

@app.post("/api/v1/messages/send")
async def send_message(user: dict = Depends(get_current_user)):
    """Enviar mensagem"""
    pass

@app.post("/api/v1/video/create")
async def create_video_room(user: dict = Depends(get_current_user)):
    """Criar sala de vídeo Jitsi"""
    pass

@app.get("/api/v1/bots")
async def list_bots():
    """Listar bots disponíveis"""
    pass
```

---

## 🔐 AUTENTICAÇÃO E SEGURANÇA

### **1. Keycloak SSO**

**Rocket.Chat**:
```javascript
// Configuração OAuth2
{
  "OAuth": {
    "enabled": true,
    "provider": "keycloak",
    "serverURL": "https://keycloak.gsi.srv.br/auth",
    "realm": "saudeplanner.com.br",
    "clientId": "intellicare-rocketchat",
    "clientSecret": "${ROCKETCHAT_CLIENT_SECRET}",
    "buttonLabelText": "Login com IntelliCare",
    "usernameField": "preferred_username",
    "emailField": "email",
    "nameField": "name"
  }
}
```

**Jitsi JWT**:
```python
# Gerar JWT para Jitsi
import jwt
from datetime import datetime, timedelta

def generate_jitsi_token(user_id: str, room_name: str) -> str:
    payload = {
        "context": {
            "user": {
                "id": user_id,
                "name": user_name,
                "email": user_email
            }
        },
        "aud": "intellicare",
        "iss": "intellicare",
        "sub": "meet.gsi.srv.br",
        "room": room_name,
        "exp": datetime.utcnow() + timedelta(hours=2)
    }
    return jwt.encode(payload, JITSI_JWT_SECRET, algorithm="HS256")
```

### **2. LGPD Compliance**

- **Auditoria**: Todas as mensagens registradas
- **Retenção**: Política de 90 dias (configurável)
- **Anonimização**: Dados sensíveis mascarados
- **Consentimento**: Termo de uso obrigatório
- **Direito ao Esquecimento**: Endpoint de exclusão

---

## 🤖 INTEGRAÇÃO COM BOTS (FLOWISE)

### **Arquitetura de Chatbots**

```
┌─────────────────────────────────────────────────────────┐
│                    Rocket.Chat                          │
│  (Usuário envia mensagem para @geralda)                │
└─────────────────┬───────────────────────────────────────┘
                  │
                  │ Webhook
                  ▼
┌─────────────────────────────────────────────────────────┐
│           IntelliCare Communication API                 │
│  POST /api/v1/webhooks/rocketchat                       │
└─────────────────┬───────────────────────────────────────┘
                  │
                  │ HTTP Request
                  ▼
┌─────────────────────────────────────────────────────────┐
│                    Flowise API                          │
│  POST /api/v1/prediction/{chatflow_id}                  │
└─────────────────┬───────────────────────────────────────┘
                  │
                  │ RAG + LLM
                  ▼
┌─────────────────────────────────────────────────────────┐
│                    Ollama (LLM)                         │
│  Model: llama2:7b (ou outro)                            │
└─────────────────┬───────────────────────────────────────┘
                  │
                  │ Response
                  ▼
┌─────────────────────────────────────────────────────────┐
│           Rocket.Chat (Resposta do bot)                 │
└─────────────────────────────────────────────────────────┘
```

### **Implementação**

```python
# comunicacao/integrations/flowise_bot.py
from flowise_client import FlowiseClient

class BotHandler:
    def __init__(self):
        self.flowise = FlowiseClient(
            base_url="http://flowise:3001",
            api_key=settings.FLOWISE_API_KEY
        )
    
    async def handle_message(
        self,
        bot_name: str,
        message: str,
        user_id: str,
        channel_id: str
    ) -> str:
        """Processar mensagem para bot"""
        
        # Mapear bot para chatflow
        chatflow_map = {
            "geralda": settings.GERALDA_CHATFLOW_ID,
            "wanda": settings.WANDA_CHATFLOW_ID,
            "dr_nise": settings.DR_NISE_CHATFLOW_ID,
            "florence": settings.FLORENCE_CHATFLOW_ID,
            "oswaldo": settings.OSWALDO_CHATFLOW_ID
        }
        
        chatflow_id = chatflow_map.get(bot_name)
        if not chatflow_id:
            return "Bot não encontrado"
        
        # Enviar para Flowise
        response = await self.flowise.predict(
            chatflow_id=chatflow_id,
            question=message,
            session_id=f"{user_id}_{channel_id}",
            overrideConfig={
                "user_id": user_id,
                "channel_id": channel_id
            }
        )
        
        return response.get("text", "Desculpe, não entendi")
```

---

## 🔄 WORKFLOWS KESTRA

### **Exemplo 1: Lembrete de Consulta**

```yaml
# kestra/flows/reminder-teleconsulta.yml
id: reminder-teleconsulta
namespace: intellicare.comunicacao

inputs:
  - id: appointment_id
    type: STRING
  - id: patient_id
    type: STRING
  - id: professional_id
    type: STRING
  - id: scheduled_time
    type: DATETIME

tasks:
  # D-1: Enviar lembrete
  - id: send-reminder-d1
    type: io.kestra.plugin.scripts.python.Script
    script: |
      import requests
      
      # Enviar mensagem no Rocket.Chat
      response = requests.post(
          "http://comunicacao:8010/api/v1/messages/send",
          json={
              "user_id": "{{ inputs.patient_id }}",
              "message": "Lembrete: Você tem uma teleconsulta amanhã às {{ inputs.scheduled_time }}"
          }
      )
      print(response.json())

triggers:
  - id: schedule
    type: io.kestra.core.models.triggers.types.Schedule
    cron: "0 9 * * *"  # Diariamente às 09:00
```

### **Exemplo 2: Alerta de Exame Crítico**

```yaml
# kestra/flows/alert-exame-critico.yml
id: alert-exame-critico
namespace: intellicare.comunicacao

triggers:
  - id: webhook
    type: io.kestra.core.models.triggers.types.Webhook
    key: florence-critical-exam

tasks:
  - id: notify-oswaldo
    type: io.kestra.plugin.fs.http.Request
    uri: "http://oswaldo:8000/api/v1/alerts"
    method: POST
    body: |
      {
        "patient_id": "{{ trigger.body.patient_id }}",
        "exam_type": "{{ trigger.body.exam_type }}",
        "result": "{{ trigger.body.result }}"
      }
  
  - id: notify-rocketchat
    type: io.kestra.plugin.fs.http.Request
    uri: "http://comunicacao:8010/api/v1/messages/send"
    method: POST
    body: |
      {
        "channel": "#alertas",
        "message": "🚨 ALERTA: Exame crítico detectado para paciente {{ trigger.body.patient_id }}"
      }
```

---

## 📊 MONITORAMENTO E MÉTRICAS

### **Prometheus Metrics**

```python
# comunicacao/monitoring/metrics.py
from prometheus_client import Counter, Histogram, Gauge

# Métricas de mensagens
messages_sent = Counter(
    'comunicacao_messages_sent_total',
    'Total de mensagens enviadas',
    ['channel_type', 'user_role']
)

# Métricas de vídeo
video_calls_created = Counter(
    'comunicacao_video_calls_created_total',
    'Total de chamadas de vídeo criadas'
)

video_call_duration = Histogram(
    'comunicacao_video_call_duration_seconds',
    'Duração das chamadas de vídeo'
)

# Métricas de bots
bot_requests = Counter(
    'comunicacao_bot_requests_total',
    'Total de requisições para bots',
    ['bot_name']
)

bot_response_time = Histogram(
    'comunicacao_bot_response_time_seconds',
    'Tempo de resposta dos bots',
    ['bot_name']
)
```

---

## 🧪 TESTES

### **Estrutura de Testes**

```
tests/
├── unit/
│   ├── test_rocketchat_client.py
│   ├── test_jitsi_jwt.py
│   ├── test_flowise_bot.py
│   └── test_kestra_workflows.py
├── integration/
│   ├── test_sso_keycloak.py
│   ├── test_video_call_flow.py
│   └── test_bot_integration.py
└── e2e/
    ├── test_teleconsulta_completa.py
    └── test_alerta_critico.py
```

---

**Responsável**: DEV1  
**Data**: 26/03/2026  
**Versão**: 1.0  
**Status**: ✅ Especificação Técnica Completa

