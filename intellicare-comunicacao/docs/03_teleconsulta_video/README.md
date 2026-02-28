# D3 - Teleconsulta/Vídeo (Jitsi Meet)

## 📋 Visão Geral

O **D3 - Teleconsulta/Vídeo** implementa integração com **Jitsi Meet** para teleconsultas, salas multidisciplinares, treinamentos e reuniões de emergência.

---

## 🎯 Objetivos

✅ **Teleconsultas**: Consultas médicas por vídeo  
✅ **Salas Multidisciplinares**: Discussão de casos clínicos  
✅ **Grupos**: Sessões de grupo (terapia, educação)  
✅ **Treinamentos**: Capacitação de equipes  
✅ **Emergência**: Salas de emergência com acesso rápido  

---

## 🏗️ Arquitetura

```
┌─────────────────────────────────────────────────────────────┐
│                    D3 - Teleconsulta/Vídeo                  │
│                                                             │
│  ┌──────────────┐      ┌──────────────┐                    │
│  │ JitsiClient  │◄─────│ JitsiConfig  │                    │
│  └──────┬───────┘      └──────────────┘                    │
│         │                                                   │
│         ▼                                                   │
│  ┌──────────────┐      ┌──────────────┐                    │
│  │ RoomService  │◄─────│ JitsiModels  │                    │
│  └──────┬───────┘      └──────────────┘                    │
│         │                                                   │
│         ▼                                                   │
│  ┌──────────────────┐                                      │
│  │ JitsiDispatcher  │◄──────────────────────────────────┐  │
│  └──────────────────┘                                    │  │
│         │                                                │  │
└─────────┼────────────────────────────────────────────────┼──┘
          │                                                │
          ▼                                                │
┌─────────────────────────────────────────────────────────┼──┐
│              D1 - Engine de Roteamento                  │  │
│                                                          │  │
│  ┌──────────────┐      ┌──────────────────┐            │  │
│  │RoutingEngine │─────►│DispatcherManager │────────────┘  │
│  └──────────────┘      └──────────────────┘               │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

---

## 📦 Componentes

### 1. **JitsiConfig** (`comunicacao/jitsi/config.py`)

Configuração do Jitsi Meet.

**Variáveis de Ambiente**:
- `JITSI_BASE_URL`: URL base do Jitsi (ex: `https://meet.gsi.srv.br`)
- `JITSI_APP_ID`: App ID para JWT
- `JITSI_APP_SECRET`: Secret para JWT
- `JITSI_DEFAULT_ROOM_DURATION`: Duração padrão (minutos)
- `JITSI_MAX_PARTICIPANTS`: Máximo de participantes
- `JITSI_ENABLE_RECORDING`: Habilitar gravação
- `JITSI_ENABLE_LOBBY`: Habilitar lobby
- `JITSI_ENABLE_CHAT`: Habilitar chat
- `JITSI_ENABLE_SCREEN_SHARING`: Habilitar compartilhamento de tela

### 2. **JitsiClient** (`comunicacao/jitsi/client.py`)

Cliente para geração de tokens JWT e URLs.

**Métodos**:
- `generate_room_name()`: Gera nome único de sala
- `generate_jwt_token()`: Gera token JWT para participante
- `get_room_url()`: Gera URL completa da sala
- `validate_room_config()`: Valida configuração de sala

### 3. **RoomService** (`comunicacao/jitsi/room_service.py`)

Serviço para CRUD de salas e participantes.

**Métodos**:
- `create_room()`: Cria nova sala
- `get_room()`: Busca sala por ID
- `list_rooms()`: Lista salas
- `add_participant()`: Adiciona participante
- `remove_participant()`: Remove participante
- `start_room()`: Inicia sala (SCHEDULED → ACTIVE)
- `end_room()`: Finaliza sala (ACTIVE → COMPLETED)
- `cancel_room()`: Cancela sala (SCHEDULED → CANCELLED)

### 4. **JitsiDispatcher** (`comunicacao/jitsi/dispatcher.py`)

Dispatcher que implementa protocolo `ChannelDispatcher` do D1.

**Métodos** (protocolo):
- `send()`: Envia convite de teleconsulta
- `get_status()`: Consulta status de participante
- `cancel()`: Remove participante
- `health_check()`: Verifica saúde do canal
- `test_send()`: Envia mensagem de teste
- `get_capabilities()`: Retorna capacidades
- `validate_recipient()`: Valida destinatário

---

## 🗄️ Modelos de Dados

### **JitsiRoom** (Tabela: `jitsi_rooms`)

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | UUID | ID único |
| `room_name` | String | Nome da sala (único) |
| `room_type` | Enum | TELECONSULTA, MULTIDISCIPLINAR, GRUPO, TREINAMENTO, EMERGENCIA |
| `status` | Enum | SCHEDULED, ACTIVE, COMPLETED, CANCELLED |
| `scheduled_start` | DateTime | Início agendado |
| `scheduled_end` | DateTime | Fim agendado |
| `actual_start` | DateTime | Início real |
| `actual_end` | DateTime | Fim real |
| `max_participants` | Integer | Máximo de participantes |
| `patient_id` | String | ID do paciente (opcional) |
| `intent_id` | String | ID do intent (D1) |
| `title` | String | Título da sala |
| `description` | Text | Descrição |

### **JitsiParticipant** (Tabela: `jitsi_participants`)

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | UUID | ID único |
| `room_id` | UUID | ID da sala (FK) |
| `user_id` | String | ID do usuário |
| `user_name` | String | Nome do usuário |
| `user_email` | String | Email (opcional) |
| `role` | Enum | MODERATOR, PRESENTER, PARTICIPANT |
| `invited_at` | DateTime | Data do convite |
| `joined_at` | DateTime | Data de entrada |
| `left_at` | DateTime | Data de saída |
| `jwt_token` | Text | Token JWT |
| `token_expires_at` | DateTime | Expiração do token |

---

## 🔌 API Endpoints

### **Salas**

- `POST /api/v1/jitsi/rooms` - Criar sala
- `GET /api/v1/jitsi/rooms/{room_id}` - Buscar sala
- `GET /api/v1/jitsi/rooms` - Listar salas
- `POST /api/v1/jitsi/rooms/{room_id}/start` - Iniciar sala
- `POST /api/v1/jitsi/rooms/{room_id}/end` - Finalizar sala
- `POST /api/v1/jitsi/rooms/{room_id}/cancel` - Cancelar sala

### **Participantes**

- `POST /api/v1/jitsi/rooms/{room_id}/participants` - Adicionar participante
- `DELETE /api/v1/jitsi/participants/{participant_id}` - Remover participante

### **Webhooks**

- `POST /api/v1/jitsi/webhook` - Receber eventos do Jitsi

---

## 📊 Estatísticas

| Métrica | Valor |
|---------|-------|
| **Linhas de Código** | ~2,000 |
| **Arquivos Criados** | 13 |
| **Modelos SQLAlchemy** | 2 |
| **Modelos Pydantic** | 3 |
| **Enums** | 3 |
| **API Endpoints** | 11 |
| **Tabelas** | 2 |
| **Índices** | 8 |
| **Testes** | 50+ |
| **Cobertura de Testes** | ≥90% (target) |

---

## 🔗 Integrações

- **D1 - Engine de Roteamento**: Via `JitsiDispatcher`
- **Jitsi Meet**: Via JWT tokens e REST API
- **Keycloak**: SSO para autenticação (futuro)

---

## 📚 Documentação Adicional

- [Integração D1 ↔ D3](./INTEGRACAO_D1.md)
- [Guia Operacional](./GUIA_OPERACIONAL.md)

---

## 🚀 Próximos Passos

1. ✅ Implementar testes (≥90% coverage)
2. ✅ Documentação técnica
3. ⏳ Integração com Keycloak SSO
4. ⏳ Webhooks do Jitsi para atualizar status
5. ⏳ Gravação de teleconsultas
6. ⏳ Transcrição automática (Whisper)

