# INTELLICARE — Módulo de Comunicação Integrada
## Especificações Funcionais para Desenvolvimento Paralelo

**Versão**: 1.0  
**Data**: 15 de Fevereiro de 2026  
**Autor**: Agente Arquiteto de Comunicação  
**Classificação**: Documento Estratégico — Especificações Funcionais  
**Destinatários**: Agentes de Desenvolvimento (DEV), Arquiteto-Chefe, Stakeholders

---

## PARTE I — VISÃO ESTRATÉGICA

### 1. Contexto e Relevância

A comunicação na saúde não é um recurso acessório — é **infraestrutura clínica**. Cada minuto de atraso na transmissão de um alerta crítico, cada mensagem que não chega ao profissional certo, cada consulta que poderia ter sido remota mas exigiu deslocamento de um paciente crônico — tudo isso se traduz em **desfechos clínicos piores**.

O IntelliCare é uma plataforma modular de inteligência clínica que monitora doenças crônicas (Oswaldo), interpreta exames laboratoriais (Florence), avalia qualidade assistencial (Donabedian), gere planos de cuidado (Geralda), consulta dados do SUS (Zilda) e orquestra tudo isso via IA (Wanda/Nise). **Porém, nenhum desses módulos entrega valor ao paciente se a informação não fluir.**

O módulo `intellicare-comunicacao` é o **sistema nervoso** do IntelliCare — responsável por garantir que a informação certa chegue à pessoa certa, no canal certo, no momento certo, com rastreabilidade completa e conformidade com a LGPD.

### 2. Posicionamento Arquitetural

```
┌─────────────────────────────────────────────────────────┐
│                    CAMADA 7 — APLICAÇÕES                │
│         Portal Web (React)  │  App Mobile  │  Element   │
├─────────────────────────────────────────────────────────┤
│              CAMADA 6 — SEGURANÇA / LGPD                │
│          Keycloak SSO  │  RBAC  │  Auditoria            │
├─════════════════════════════════════════════════════════─┤
│     ██  CAMADA 5 — COMUNICACAO INTEGRADA (CPaaS)  ██    │
│                                                         │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌───────────┐  │
│  │  Rocket   │ │  Jitsi   │ │  Flowise │ │  Kestra   │  │
│  │  Chat     │ │  Meet    │ │  (Nise)  │ │  Workflows│  │
│  └──────────┘ └──────────┘ └──────────┘ └───────────┘  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌───────────┐  │
│  │  Email   │ │  Push    │ │ WhatsApp │ │  SMS      │  │
│  │  SMTP    │ │  Notif.  │ │ Business │ │  Gateway  │  │
│  └──────────┘ └──────────┘ └──────────┘ └───────────┘  │
│                                                         │
│  ┌──────────────────────────────────────────────────┐   │
│  │   ENGINE DE ROTEAMENTO — Regras + Prioridades    │   │
│  │   Redis Streams → Parser → Router → Dispatcher   │   │
│  └──────────────────────────────────────────────────┘   │
├─════════════════════════════════════════════════════════─┤
│              CAMADA 4 — SERVIÇOS DE IA                  │
│    Wanda (Orquestrador) │ Nise (Chatbot) │ Ollama      │
├─────────────────────────────────────────────────────────┤
│         CAMADA 3 — BASE DE CONHECIMENTO CLÍNICO         │
│    Oswaldo │ Florence │ Donabedian │ Geralda │ Zilda    │
├─────────────────────────────────────────────────────────┤
│              CAMADA 2 — MCP CORE (SDK)                  │
│    BaseDAO │ EventPublisher │ FHIR Client │ Auth        │
├─────────────────────────────────────────────────────────┤
│           CAMADA 1 — INFRAESTRUTURA                     │
│    PostgreSQL │ Redis │ Docker │ Traefik │ Prometheus   │
└─────────────────────────────────────────────────────────┘
```

### 3. Princípio Fundamental: CPaaS na Saúde

Seguindo o modelo **Gartner CPaaS** adaptado para saúde (referência HosmartAI):

> **O módulo de comunicação é um TRANSPORTADOR INTELIGENTE.**  
> Ele **não decide** o conteúdo clínico, a urgência nem o destinatário — isso é papel dos módulos clínicos (Oswaldo, Florence, Geralda) e do orquestrador (Wanda).  
> Ele **garante** que a mensagem chegue pelo canal adequado, no tempo adequado, com confirmação de entrega, auditoria e conformidade.

**Separação de responsabilidades:**
| Quem Decide | O Quê | Quem Transporta |
|---|---|---|
| Oswaldo | Alerta: "eGFR caiu 25% em 3 meses" | Comunicação → Rocket.Chat → Equipe |
| Florence | Insight: "Padrão nefrotóxico detectado" | Comunicação → Push → Médico responsável |
| Geralda | Lembrete: "Tome medicação às 14h" | Comunicação → WhatsApp/SMS → Paciente |
| Nise (Dr. Nise) | Educação: "Sobre diabetes tipo 2..." | Comunicação → Chatbot → Paciente |
| Donabedian | Relatório: "Indicador abaixo da meta" | Comunicação → Email → Gestor |
| Wanda | Agregação: "Paciente X - visão completa" | Comunicação → Portal/Notificação → Coordenador |

---

## PARTE II — ESTADO ATUAL E GAP ANALYSIS

### 4. O Que Já Existe (Baseline)

| Componente | Status | Descrição |
|---|---|---|
| **Matrix/Synapse** | ✅ Operacional | Homeserver em `matrix.gsi.srv.br`, client Element em `element.gsi.srv.br` |
| **Rocket.Chat** | ✅ Operacional | v7.13.2 em `rocket.gsi.srv.br`, Keycloak SSO ativo |
| **Jitsi Meet** | ✅ Operacional | Em `meet.gsi.srv.br`, JWT/Keycloak SSO ativo |
| **Keycloak SSO** | ✅ Operacional | Realm `bemcuidar`, clients para todos os serviços, 7 roles RBAC |
| **API FastAPI** | ✅ Funcional | 18 endpoints, Matrix client, patient-room links |
| **Redis Consumer** | ✅ Funcional | Consome `alert.created`, roteia para Matrix |
| **Bot Geralda** | ✅ Básico | Auto-join, comandos `!ajuda` e `!status` |
| **Testes** | ✅ Parcial | ~20 unit tests, 1 E2E pipeline test |
| **PostgreSQL Schema** | ✅ Parcial | Tabela `patient_room_links` |

### 5. O Que Falta (Gaps Identificados)

| Gap | Impacto | Prioridade |
|---|---|---|
| Rocket.Chat não integrado via API (só Matrix) | Equipe médica sem canal corporativo inteligente | **CRÍTICO** |
| Sem notificações push (mobile/web) | Alertas críticos dependem de browser aberto | **CRÍTICO** |
| Sem integração WhatsApp/SMS | Pacientes não recebem lembretes diretos | **ALTO** |
| Sem templates de mensagens | Cada módulo formata diferente, sem padronização | **ALTO** |
| Sem engine de roteamento multi-canal | Mensagem vai só pra Matrix, sem fallback | **ALTO** |
| Sem histórico de conversações | Sem auditoria, sem continuidade do cuidado | **ALTO** |
| Sem agendamento de teleconsultas | Jitsi funciona mas sem integração com agenda | **MÉDIO** |
| Sem dashboard de comunicações | Gestor não sabe o volume/eficácia das comunicações | **MÉDIO** |
| Sem consolidação operacional→analítico | Dados não disponíveis para Donabedian/Grafana | **MÉDIO** |
| Schema `src/comunicacao/` vazio (skeleton) | Estrutura de código não segue padrão dos outros módulos | **MÉDIO** |
| Sem proteção de endpoints (auth middleware) | API exposta sem autenticação | **MÉDIO** |
| Sem integração Kestra (workflows de notificação) | Fluxos não automatizados | **BAIXO** |

---

## PARTE III — ESPECIFICAÇÕES FUNCIONAIS

### Convenções

Cada especificação funcional (EF) segue o formato:
- **Identificador**: EF-COM-XXX
- **Título**: Nome descritivo
- **Prioridade**: CRÍTICA / ALTA / MÉDIA / BAIXA
- **Dependências**: Outros EFs ou módulos necessários
- **Critérios de Aceite**: Condições mensuráveis de conclusão
- **Módulos Consumidores**: Quem consome esta funcionalidade

As EFs estão agrupadas em **Domínios Funcionais** que podem ser desenvolvidos em paralelo por diferentes agentes.

---

### DOMÍNIO 1: ENGINE DE ROTEAMENTO MULTI-CANAL
**Responsável**: Agente DEV-1  
**Escopo**: O coração do módulo — decide COMO e POR ONDE entregar cada mensagem

---

#### EF-COM-001: Motor de Roteamento de Mensagens

**Prioridade**: CRÍTICA  
**Dependências**: Nenhuma (base para tudo)  

**Descrição Funcional**:  
O sistema deve possuir um motor de roteamento capaz de receber uma intenção de comunicação (origem, destinatário, conteúdo, urgência, tipo) e determinar automaticamente:
1. Qual(is) canal(is) utilizar
2. Em que ordem tentar (cascata de fallback)
3. Com que prioridade na fila
4. Se deve aguardar confirmação de leitura

**Regras de Roteamento**:

| Severidade | Canal Primário | Fallback 1 | Fallback 2 | Timeout |
|---|---|---|---|---|
| CRÍTICA | Push + Rocket.Chat | SMS | Ligação telefônica* | 5 min |
| ALTA | Rocket.Chat + Push | Email | SMS | 15 min |
| MÉDIA | Rocket.Chat | Email | — | 1 hora |
| BAIXA | Email | — | — | 24 horas |
| EDUCACIONAL | WhatsApp/Chatbot | Email | — | Sem timeout |
| LEMBRETE | WhatsApp/SMS | Push | — | Configura horário |

*Ligação telefônica = integração futura; por enquanto, escalar para coordenador via Rocket.Chat

**Modelo de Dados — Intenção de Comunicação**:
```
CommunicationIntent {
    id: UUID
    source_module: string          // "intellicare-oswaldo"
    source_event_id: string        // ID do evento original
    recipient_type: enum           // PROFESSIONAL | PATIENT | TEAM | COORDINATOR
    recipient_id: string           // ID do profissional/paciente/equipe
    severity: enum                 // CRITICAL | HIGH | MEDIUM | LOW
    category: enum                 // CLINICAL_ALERT | REMINDER | EDUCATION | REPORT | TELECONSULT
    content_template_id: string    // Referência ao template
    content_params: JSON           // Parâmetros para preencher o template
    preferred_channel: string?     // Canal preferido (opcional, pode ser nulo)
    require_ack: boolean           // Exige confirmação de leitura?
    scheduled_at: datetime?        // Agendamento (nulo = imediato)
    expires_at: datetime?          // Expiração da mensagem
    correlation_id: string         // Para rastrear todo o fluxo
    created_at: datetime
}
```

**Modelo de Dados — Resultado de Entrega**:
```
DeliveryResult {
    id: UUID
    intent_id: UUID                // FK → CommunicationIntent
    channel: string                // "rocketchat" | "matrix" | "whatsapp" | "email" | "push" | "sms"
    attempt_number: int            // 1, 2, 3...
    status: enum                   // QUEUED | SENT | DELIVERED | READ | FAILED | EXPIRED
    channel_message_id: string?    // ID da mensagem no canal externo
    error_message: string?
    sent_at: datetime?
    delivered_at: datetime?
    read_at: datetime?
    created_at: datetime
}
```

**Critérios de Aceite**:
1. Uma intenção de comunicação CRÍTICA é roteada em menos de 2 segundos
2. Se o canal primário falha, o fallback é acionado dentro do timeout configurado
3. Cada tentativa gera um `DeliveryResult` persistido
4. O motor aceita regras customizáveis por instituição (configuração, não código)
5. Métricas de roteamento expostas em `/api/v1/routing/metrics`

**Módulos Consumidores**: Todos (Oswaldo, Florence, Geralda, Nise, Donabedian, Wanda)

---

#### EF-COM-002: Dispatcher Multi-Canal

**Prioridade**: CRÍTICA  
**Dependências**: EF-COM-001  

**Descrição Funcional**:  
Cada canal de comunicação deve ter um Dispatcher que implementa uma interface comum, permitindo ao Motor de Roteamento enviar mensagens de forma uniforme sem conhecer os detalhes de cada canal.

**Interface Comum do Dispatcher**:
```
IChannelDispatcher {
    channel_name: string
    is_available(): bool
    send(recipient_id, rendered_content, metadata): DeliveryResult
    check_delivery_status(channel_message_id): DeliveryStatus
    get_health(): HealthStatus
}
```

**Dispatchers Necessários** (em ordem de prioridade):

| Dispatcher | Canal | Status Atual | Prioridade |
|---|---|---|---|
| `RocketChatDispatcher` | Rocket.Chat API | Novo | CRÍTICA |
| `MatrixDispatcher` | Matrix/Synapse | Refatorar existente | ALTA |
| `PushDispatcher` | Web Push / FCM | Novo | ALTA |
| `EmailDispatcher` | SMTP | Novo | ALTA |
| `WhatsAppDispatcher` | WhatsApp Business API | Novo | MÉDIA |
| `SMSDispatcher` | Gateway SMS | Novo | MÉDIA |
| `JitsiDispatcher` | Jitsi (criar sala + notificar) | Novo | MÉDIA |

**Critérios de Aceite**:
1. Cada dispatcher implementa a interface `IChannelDispatcher`
2. O motor de roteamento pode usar qualquer dispatcher sem acoplamento direto
3. Novos dispatchers podem ser adicionados sem alterar o motor
4. Cada dispatcher reporta saúde via `/api/v1/channels/{channel}/health`
5. Dispatchers são configuráveis via variáveis de ambiente

---

#### EF-COM-003: Sistema de Templates de Mensagens

**Prioridade**: ALTA  
**Dependências**: Nenhuma (pode ser desenvolvido em paralelo)  

**Descrição Funcional**:  
As mensagens enviadas pelo sistema devem ser padronizadas via templates, garantindo consistência visual, acessibilidade e adaptação ao canal de destino. Um mesmo conteúdo clínico deve ser renderizado diferentemente para cada canal.

**Categorias de Templates**:

| Categoria | Exemplos | Canais |
|---|---|---|
| `CLINICAL_ALERT` | Alerta de queda de eGFR, hiperglicemia, PA elevada | Todos |
| `MEDICATION_REMINDER` | Lembrete de medicação com nome, dose e horário | WhatsApp, SMS, Push |
| `APPOINTMENT_REMINDER` | Lembrete de consulta com data, local, preparo | WhatsApp, Email, SMS |
| `TELECONSULT_INVITE` | Convite para teleconsulta com link Jitsi | Rocket.Chat, Email, WhatsApp |
| `LAB_RESULT` | Resultado de exame com interpretação (Florence) | Email, Portal, Push |
| `CARE_PLAN_UPDATE` | Atualização do plano de cuidado (Geralda) | Rocket.Chat, Email |
| `QUALITY_REPORT` | Relatório de indicadores (Donabedian) | Email, Portal |
| `EDUCATION_CONTENT` | Material educativo sobre condição crônica | WhatsApp, Chatbot |
| `TEAM_NOTIFICATION` | Notificação para equipe de saúde | Rocket.Chat, Matrix |
| `ESCALATION` | Escalonamento por não-leitura de alerta crítico | SMS, Push, Rocket.Chat |

**Modelo de Dados — Template**:
```
MessageTemplate {
    id: string                    // "clinical_alert_egfr_drop"
    category: string              // "CLINICAL_ALERT"
    version: int                  // Versionamento semântico
    channel_variants: {
        "rocketchat": {
            format: "markdown",
            body: "🚨 **ALERTA CLÍNICO — {{severity}}**\n\n**Paciente**: {{patient_name}}\n**Tipo**: {{alert_type}}\n**Mensagem**: {{message}}\n**Módulo**: {{source_module}}\n**Ref**: {{correlation_id}}"
        },
        "whatsapp": {
            format: "whatsapp_template",
            template_name: "clinical_alert_v1",
            body: "⚠️ ALERTA {{severity}}\nPaciente: {{patient_name}}\n{{message}}\nAcesse: {{portal_url}}"
        },
        "email": {
            format: "html",
            subject: "[IntelliCare] Alerta Clínico — {{patient_name}}",
            body: "<html>...</html>"
        },
        "sms": {
            format: "plain",
            body: "INTELLICARE ALERTA {{severity}}: {{patient_name}} - {{message}}. Acesse {{short_url}}"
        },
        "push": {
            format: "push",
            title: "Alerta Clínico — {{severity}}",
            body: "{{patient_name}}: {{message}}",
            action_url: "{{portal_url}}/patient/{{patient_id}}/alerts"
        }
    }
    params_schema: JSON            // Schema dos parâmetros esperados
    created_at: datetime
    updated_at: datetime
}
```

**Critérios de Aceite**:
1. Templates armazenados em PostgreSQL com versionamento
2. API CRUD para templates: `POST/GET/PUT/DELETE /api/v1/templates`
3. Endpoint de preview: `POST /api/v1/templates/{id}/preview` (renderiza com dados fake)
4. Cada template tem variantes para pelo menos 3 canais
5. Templates suportam i18n (pt-BR como padrão, expansível)
6. Parâmetros são validados contra o schema antes de renderizar

---

### DOMÍNIO 2: INTEGRAÇÃO ROCKET.CHAT
**Responsável**: Agente DEV-2  
**Escopo**: Rocket.Chat como plataforma de comunicação corporativa da equipe de saúde

---

#### EF-COM-010: Integração API Rocket.Chat

**Prioridade**: CRÍTICA  
**Dependências**: EF-COM-002 (interface do dispatcher)  

**Descrição Funcional**:  
O módulo deve integrar-se completamente à API REST do Rocket.Chat para:
1. Enviar mensagens para canais e usuários
2. Criar canais/grupos automaticamente
3. Gerenciar usuários (sincronizar com Keycloak)
4. Enviar mensagens com formatação rica (attachments, botões)
5. Receber webhooks de eventos do Rocket.Chat

**Funcionalidades Específicas**:

| Função | Endpoint RC | Uso no IntelliCare |
|---|---|---|
| Enviar mensagem | `POST /api/v1/chat.postMessage` | Alertas clínicos, notificações de equipe |
| Criar canal | `POST /api/v1/channels.create` | Canal por equipe/unidade/paciente |
| Criar grupo privado | `POST /api/v1/groups.create` | Discussão de caso clínico |
| Convidar usuário | `POST /api/v1/channels.invite` | Adicionar profissional ao canal da equipe |
| Listar canais | `GET /api/v1/channels.list` | Descoberta de canais existentes |
| Webhook incoming | Configurar webhook | Receber comandos/respostas |
| Enviar attachment | `POST /api/v1/chat.postMessage` (attachments) | Resultados de exame, relatórios |
| Reagir a mensagem | `POST /api/v1/chat.react` | Confirmar leitura de alerta |

**Organização de Canais no Rocket.Chat**:

```
#geral                          — Canal geral do IntelliCare
#alertas-clinicos               — Todos os alertas (filtráveis por severidade)
#equipe-{unidade_id}            — Canal por unidade de saúde
#caso-{patient_id}              — Discussão de caso (grupo privado)
#teleconsultas                  — Agendamento e links de teleconsulta
#qualidade-{indicador}          — Discussões sobre indicadores Donabedian
#educacao-saude                 — Compartilhamento de materiais educativos
```

**Critérios de Aceite**:
1. `RocketChatDispatcher` implementa `IChannelDispatcher`
2. Mensagens enviadas via API com authToken do bot (`intellicare-bot`)
3. Canais criados automaticamente quando equipe/paciente é registrado
4. Webhook configurado para receber respostas/reações
5. Health check verifica conectividade com RC a cada 30s
6. Rate limiting respeitado (RC impõe limites por default)

---

#### EF-COM-011: Sincronização de Usuários Keycloak → Rocket.Chat

**Prioridade**: ALTA  
**Dependências**: EF-COM-010  

**Descrição Funcional**:  
Quando um profissional de saúde é cadastrado/atualizado no Keycloak (realm `bemcuidar`), suas informações devem ser sincronizadas automaticamente com o Rocket.Chat, incluindo:
- Criação de conta (se não existir)
- Atualização de nome, email, avatar
- Atribuição a canais com base nas roles do Keycloak
- Desativação quando removido do Keycloak

**Mapeamento de Roles → Canais**:

| Role Keycloak | Canais RC Auto-Adicionados |
|---|---|
| `admin` | `#geral`, `#alertas-clinicos`, todos os `#equipe-*` |
| `doctor` | `#geral`, `#alertas-clinicos`, `#equipe-{sua_unidade}`, `#teleconsultas` |
| `nurse` | `#geral`, `#alertas-clinicos`, `#equipe-{sua_unidade}` |
| `care_coordinator` | `#geral`, `#alertas-clinicos`, todos os `#equipe-*`, `#qualidade-*` |
| `nutritionist` | `#geral`, `#equipe-{sua_unidade}`, `#educacao-saude` |
| `hospital_admin` | `#geral`, `#qualidade-*` |
| `patient` | Apenas `#caso-{seu_id}` (grupo privado) |

**Critérios de Aceite**:
1. Evento de login no Keycloak dispara sync via webhook ou polling
2. Novo usuário Keycloak gera conta RC em menos de 30 segundos
3. Roles mapeadas corretamente para canais
4. Desativação no Keycloak desativa no RC
5. Log de sincronização persistido para auditoria

---

#### EF-COM-012: Bot IntelliCare no Rocket.Chat

**Prioridade**: ALTA  
**Dependências**: EF-COM-010  

**Descrição Funcional**:  
Um bot (`@intellicare`) deve estar presente no Rocket.Chat como assistente da equipe de saúde, respondendo a comandos e provendo informações clínicas sob demanda.

**Comandos do Bot**:

| Comando | Ação | Módulo Backend |
|---|---|---|
| `/paciente {id}` | Resumo clínico do paciente | Wanda (agregação) |
| `/alertas {hoje\|semana}` | Lista alertas recentes | Oswaldo |
| `/exames {patient_id}` | Últimos resultados laboratoeriais | Florence |
| `/plano {patient_id}` | Plano de cuidado ativo | Geralda |
| `/indicadores {pilar}` | Indicadores de qualidade | Donabedian |
| `/teleconsulta {patient_id}` | Criar sala Jitsi e enviar convite | Jitsi + Comunicação |
| `/escalar {alerta_id}` | Escalar alerta para coordenador | Comunicação |
| `/ajuda` | Lista de comandos disponíveis | Local |
| `/drnise {pergunta}` | Perguntar ao chatbot Dr. Nise | Nise/Flowise |

**Critérios de Aceite**:
1. Bot responde em menos de 3 segundos para comandos locais
2. Bot responde em menos de 10 segundos para comandos que consultam outros módulos
3. Respostas formatadas em Markdown com dados relevantes
4. Bot respeita RBAC — médico vê dados clínicos, paciente vê apenas seus dados
5. Comandos desconhecidos retornam mensagem amigável com sugestões
6. Bot registra todas as interações para auditoria (LGPD)

---

### DOMÍNIO 3: TELECONSULTA E VÍDEO
**Responsável**: Agente DEV-3  
**Escopo**: Jitsi Meet integrado ao fluxo clínico

---

#### EF-COM-020: Agendamento de Teleconsultas

**Prioridade**: ALTA  
**Dependências**: EF-COM-010 (RC), EF-COM-003 (Templates)  

**Descrição Funcional**:  
O sistema deve permitir agendar teleconsultas que automaticamente:
1. Criam uma sala Jitsi dedicada (com JWT/Keycloak)
2. Enviam convite ao paciente (WhatsApp/SMS/Email)
3. Enviam convite ao profissional (Rocket.Chat/Push)
4. Criam lembrete automático (30min antes, 5min antes)
5. Registram a sessão como recurso FHIR (`Encounter`)

**Modelo de Dados — Teleconsulta**:
```
Teleconsultation {
    id: UUID
    patient_id: string
    professional_id: string
    professional_role: string     // "doctor" | "nurse" | "nutritionist"
    scheduled_at: datetime
    duration_minutes: int         // default: 30
    jitsi_room_name: string       // gerado: "intellicare-{uuid_short}"
    jitsi_url: string             // "https://meet.gsi.srv.br/intellicare-{uuid_short}"
    jwt_token: string?            // Token JWT para acesso
    status: enum                  // SCHEDULED | REMINDED | IN_PROGRESS | COMPLETED | NO_SHOW | CANCELLED
    notes: text?                  // Notas pós-consulta
    recording_url: string?        // Se gravação habilitada
    fhir_encounter_id: string?    // Referência FHIR
    created_at: datetime
    updated_at: datetime
}
```

**Fluxo de Agendamento**:
```
1. Profissional: POST /api/v1/teleconsult/schedule
   └─→ Cria Teleconsultation (status: SCHEDULED)
   └─→ Gera sala Jitsi + JWT
   └─→ Envia convite ao paciente (template: TELECONSULT_INVITE → WhatsApp)
   └─→ Envia convite ao profissional (template: TELECONSULT_INVITE → Rocket.Chat)

2. T-30min: Cron/Kestra
   └─→ Envia lembrete ao paciente (template: APPOINTMENT_REMINDER → WhatsApp/SMS)
   └─→ Envia lembrete ao profissional (Push)
   └─→ Status → REMINDED

3. Profissional entra na sala:
   └─→ Webhook Jitsi → Status → IN_PROGRESS

4. Sessão encerrada:
   └─→ Status → COMPLETED
   └─→ Profissional pode adicionar notas
   └─→ Registrar como FHIR Encounter

5. Se ninguém entra em T+15min:
   └─→ Status → NO_SHOW
   └─→ Notificar coordenador
```

**Critérios de Aceite**:
1. API: `POST /api/v1/teleconsult/schedule`, `GET /api/v1/teleconsult/{id}`, `PUT /api/v1/teleconsult/{id}/cancel`, `GET /api/v1/teleconsult/patient/{pid}`, `GET /api/v1/teleconsult/professional/{pid}`
2. Convite enviado em até 30 segundos após agendamento
3. Lembretes disparados nos tempos corretos (±1 min de tolerância)
4. Link Jitsi com JWT válido para ambas partes
5. No-show detectado e notificado automaticamente
6. Registro FHIR gerado após conclusão

---

#### EF-COM-021: Sala de Discussão de Caso (Multidisciplinar)

**Prioridade**: MÉDIA  
**Dependências**: EF-COM-010, EF-COM-020  

**Descrição Funcional**:  
Para pacientes complexos (múltiplas comorbidades, reclassificações frequentes), o sistema deve permitir criar uma "Sala de Caso" que combina:
1. Canal privado no Rocket.Chat (`#caso-{patient_id}`)
2. Histórico de alertas clínicos relevantes
3. Resumo clínico atualizado (via Wanda)
4. Capacidade de iniciar teleconsulta multidisciplinar (Jitsi)
5. Compartilhamento de resultados de exames (Florence)

**Critérios de Aceite**:
1. Criação via `POST /api/v1/case-room/{patient_id}`
2. Profissionais adicionados com base no plano de cuidado (Geralda)
3. Resumo clínico fixado (pinned) no canal
4. Alertas do paciente roteados automaticamente para o canal
5. Botão "Iniciar Teleconsulta" cria sala Jitsi e notifica todos no canal

---

### DOMÍNIO 4: NOTIFICAÇÕES E CANAIS EXTERNOS
**Responsável**: Agente DEV-4  
**Escopo**: Push notifications, WhatsApp, SMS, Email

---

#### EF-COM-030: Notificações Push (Web + Mobile)

**Prioridade**: CRÍTICA  
**Dependências**: EF-COM-001 (Router)  

**Descrição Funcional**:  
O sistema deve enviar notificações push via:
- **Web Push** (Service Workers + VAPID) para o Portal React
- **Firebase Cloud Messaging (FCM)** para app mobile futuro

Notificações push são o canal de menor latência e devem ser usadas para **alertas críticos** e **lembretes urgentes**.

**Funcionalidades**:
1. Registro de dispositivo: `POST /api/v1/push/subscribe` (recebe push subscription do navegador)
2. Envio de notificação: interno via `PushDispatcher`
3. Gerenciar assinaturas: `GET/DELETE /api/v1/push/subscriptions/{user_id}`
4. Suporte a ações na notificação ("Ver Alerta", "Confirmar Leitura", "Abrir Teleconsulta")

**Modelo de Dados — Push Subscription**:
```
PushSubscription {
    id: UUID
    user_id: string               // Keycloak user ID
    device_type: enum             // WEB | ANDROID | IOS
    subscription_data: JSON       // Push subscription object (endpoint, keys)
    user_agent: string
    active: boolean
    created_at: datetime
    last_used_at: datetime
}
```

**Critérios de Aceite**:
1. Notificação push entregue em menos de 3 segundos após dispatch
2. Suporte a Web Push API (VAPID)
3. Notificações clicáveis redirecionam para a URL correta no portal
4. Assinaturas expiradas removidas automaticamente
5. Métricas: taxa de entrega, taxa de clique

---

#### EF-COM-031: Integração WhatsApp Business API

**Prioridade**: MÉDIA  
**Dependências**: EF-COM-001, EF-COM-003 (Templates)  

**Descrição Funcional**:  
Para comunicação direta com pacientes, o WhatsApp é o canal com maior penetração no Brasil (99% dos smartphones). O sistema deve integrar-se via WhatsApp Business API (Cloud API da Meta) para:
1. Enviar mensagens de template (aprovadas pela Meta)
2. Enviar mensagens de sessão (resposta a mensagens recebidas)
3. Receber mensagens de pacientes (webhooks)
4. Enviar lembretes de medicação, consulta e exames

**Templates WhatsApp Necessários** (submeter para aprovação da Meta):

| Template Name | Categoria | Conteúdo |
|---|---|---|
| `medication_reminder` | UTILITY | "Olá {{1}}, lembrete: tome {{2}} ({{3}}) às {{4}}. IntelliCare" |
| `appointment_reminder` | UTILITY | "Olá {{1}}, sua consulta com {{2}} é {{3}} às {{4}}. Local: {{5}}. IntelliCare" |
| `teleconsult_invite` | UTILITY | "Olá {{1}}, sua teleconsulta com {{2}} é {{3}} às {{4}}. Acesse: {{5}}" |
| `lab_result_ready` | UTILITY | "Olá {{1}}, seus resultados de exame estão disponíveis. Acesse: {{2}}" |
| `care_plan_update` | UTILITY | "Olá {{1}}, seu plano de cuidado foi atualizado. Veja em: {{2}}" |

**Fluxo de Recebimento (Inbound)**:
```
Paciente envia WhatsApp → Meta Webhook → IntelliCare API → 
  ├─ Se comando reconhecido → Responder automaticamente
  ├─ Se dúvida clínica → Encaminhar para Dr. Nise (chatbot)
  └─ Se urgência → Criar alerta e notificar equipe
```

**Critérios de Aceite**:
1. `WhatsAppDispatcher` implementa `IChannelDispatcher`
2. Templates aprovados pela Meta e funcionais
3. Webhook recebe mensagens e roteia corretamente
4. Número de WhatsApp Business verificado e ativo
5. Opt-in/Opt-out de pacientes gerenciado (LGPD)
6. Histórico de conversas armazenado com criptografia

---

#### EF-COM-032: Gateway SMS

**Prioridade**: MÉDIA  
**Dependências**: EF-COM-001  

**Descrição Funcional**:  
SMS é o canal de último recurso para pacientes sem smartphone ou sem internet. Deve ser usado para:
1. Alertas críticos quando push e WhatsApp falharam (fallback)
2. Lembretes de consulta para pacientes sem WhatsApp
3. Código de verificação / OTP (se necessário)

**Critérios de Aceite**:
1. `SMSDispatcher` implementa `IChannelDispatcher`
2. Integração com gateway SMS brasileiro (ex: Zenvia, Twilio, Infobip)
3. Mensagens limitadas a 160 caracteres com informação essencial
4. Logs de envio para auditoria
5. Rate limiting para evitar custos excessivos

---

#### EF-COM-033: Serviço de Email Transacional

**Prioridade**: ALTA  
**Dependências**: EF-COM-003 (Templates)  

**Descrição Funcional**:  
Email é o canal padrão para comunicações não-urgentes: relatórios, resumos semanais, convites e notificações de atualização.

**Funcionalidades**:
1. Envio via SMTP configurável (ou serviço como SendGrid/SES)
2. Templates HTML responsivos para cada categoria
3. Fila de envio com retry automático
4. Tracking de abertura e clique (pixel + UTM)
5. Unsubscribe gerenciado por categoria (LGPD)

**Emails Automáticos**:

| Trigger | Template | Destinatário |
|---|---|---|
| Alerta clínico ALTO | `clinical_alert` | Profissional responsável |
| Resultado de exame disponível | `lab_result_ready` | Paciente + Médico |
| Resumo semanal de indicadores | `weekly_quality_report` | Gestor/Coordenador |
| Teleconsulta agendada | `teleconsult_invite` | Paciente + Profissional |
| Plano de cuidado atualizado | `care_plan_update` | Paciente |
| Reclassificação de paciente | `patient_reclassification` | Equipe multiprofissional |

**Critérios de Aceite**:
1. `EmailDispatcher` implementa `IChannelDispatcher`
2. Templates HTML renderizam corretamente em Gmail, Outlook, Apple Mail
3. Retry automático: 3 tentativas com backoff exponencial
4. Unsubscribe link funcional em cada email
5. DKIM/SPF configurados para domínio `gsi.srv.br`

---

### DOMÍNIO 5: EVENTOS E CONSOLIDAÇÃO
**Responsável**: Agente DEV-5  
**Escopo**: Event bus, consumer groups, consolidação operacional→analítico

---

#### EF-COM-040: Consumer Multi-Evento (Redis Streams)

**Prioridade**: CRÍTICA  
**Dependências**: EF-COM-001  

**Descrição Funcional**:  
Expandir o consumer atual (que só ouve `alert.created`) para consumir todos os eventos relevantes do barramento Redis Streams:

**Eventos a Consumir**:

| Stream | Evento | Origem | Ação na Comunicação |
|---|---|---|---|
| `intellicare:alert.created` | Alerta clínico | Oswaldo | Rotear via Engine (EF-COM-001) |
| `intellicare:lab.interpreted` | Exame interpretado | Florence | Notificar médico + paciente |
| `intellicare:care_plan.updated` | Plano atualizado | Geralda | Notificar paciente + equipe |
| `intellicare:quality.threshold` | Indicador abaixo do limiar | Donabedian | Notificar gestor |
| `intellicare:patient.reclassified` | Paciente reclassificado | Oswaldo | Notificar equipe multidisciplinar |
| `intellicare:medication.reminder` | Lembrete de medicação | Geralda | Enviar ao paciente (WhatsApp/SMS) |
| `intellicare:teleconsult.scheduled` | Teleconsulta agendada | Comunicação | Enviar convites |
| `intellicare:teleconsult.reminder` | Lembrete de teleconsulta | Kestra/Cron | Enviar lembretes |

**Arquitetura do Consumer**:
```
Redis Streams
    │
    ├── intellicare:alert.created ──────┐
    ├── intellicare:lab.interpreted ────┤
    ├── intellicare:care_plan.updated ──┤
    ├── intellicare:quality.threshold ──┤    Consumer Group
    ├── intellicare:patient.reclassified┼───"comunicacao-consumers"
    ├── intellicare:medication.reminder ┤        │
    ├── intellicare:teleconsult.* ──────┘   ┌────┴────┐
                                           Worker 1  Worker 2  (escalável)
                                               │
                                        EventParser
                                               │
                                    CommunicationIntent
                                               │
                                       RoutingEngine
                                               │
                                   ┌─────┬─────┬──────┐
                                   RC   Push  Email  WhatsApp
```

**Critérios de Aceite**:
1. Consumer group `comunicacao-consumers` com XREADGROUP e ACK/NACK
2. Mensagens não processadas vão para Dead Letter Queue (DLQ)
3. Cada evento gera um `CommunicationIntent` processado pelo Router
4. Métricas por stream: received, processed, failed, avg_latency
5. Consumer escalável horizontalmente (múltiplos workers)
6. Reconexão automática em caso de falha Redis

---

#### EF-COM-041: Consolidação Operacional → Analítico

**Prioridade**: MÉDIA  
**Dependências**: EF-COM-040  

**Descrição Funcional**:  
Seguindo o padrão dual-schema do IntelliCare (replicado do Donabedian), os dados de comunicação devem ser consolidados do schema operacional para o analítico:

**Schema Operacional** (`comunicacao_operacional`):
```sql
-- Intenções de comunicação
CREATE TABLE communication_intents (
    id UUID PRIMARY KEY,
    source_module VARCHAR(100),
    source_event_id VARCHAR(200),
    recipient_type VARCHAR(50),
    recipient_id VARCHAR(200),
    severity VARCHAR(20),
    category VARCHAR(50),
    content_template_id VARCHAR(100),
    content_params JSONB,
    scheduled_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ,
    correlation_id VARCHAR(200),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    valid_from TIMESTAMPTZ DEFAULT NOW(),
    valid_to TIMESTAMPTZ DEFAULT '9999-12-31',
    rowversion INT DEFAULT 1
);

-- Resultados de entregas
CREATE TABLE delivery_results (
    id UUID PRIMARY KEY,
    intent_id UUID REFERENCES communication_intents(id),
    channel VARCHAR(50),
    attempt_number INT,
    status VARCHAR(20),
    channel_message_id VARCHAR(300),
    error_message TEXT,
    sent_at TIMESTAMPTZ,
    delivered_at TIMESTAMPTZ,
    read_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Templates
CREATE TABLE message_templates (
    id VARCHAR(100) PRIMARY KEY,
    category VARCHAR(50),
    version INT DEFAULT 1,
    channel_variants JSONB,
    params_schema JSONB,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Teleconsultas
CREATE TABLE teleconsultations (
    id UUID PRIMARY KEY,
    patient_id VARCHAR(200),
    professional_id VARCHAR(200),
    professional_role VARCHAR(50),
    scheduled_at TIMESTAMPTZ,
    duration_minutes INT DEFAULT 30,
    jitsi_room_name VARCHAR(200),
    jitsi_url VARCHAR(500),
    status VARCHAR(20),
    notes TEXT,
    fhir_encounter_id VARCHAR(200),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Subscriptions push
CREATE TABLE push_subscriptions (
    id UUID PRIMARY KEY,
    user_id VARCHAR(200),
    device_type VARCHAR(20),
    subscription_data JSONB,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_used_at TIMESTAMPTZ
);

-- Preferências de comunicação do paciente (LGPD)
CREATE TABLE patient_comm_preferences (
    patient_id VARCHAR(200) PRIMARY KEY,
    whatsapp_optin BOOLEAN DEFAULT false,
    sms_optin BOOLEAN DEFAULT false,
    email_optin BOOLEAN DEFAULT true,
    push_optin BOOLEAN DEFAULT true,
    preferred_channel VARCHAR(50) DEFAULT 'whatsapp',
    quiet_hours_start TIME,         -- Ex: 22:00
    quiet_hours_end TIME,           -- Ex: 07:00
    phone_number VARCHAR(20),
    email VARCHAR(200),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Schema Analítico** (`comunicacao_analitico`):
```sql
-- Visão desnormalizada para dashboards e Donabedian
CREATE TABLE comm_analytics (
    id UUID PRIMARY KEY,
    intent_id UUID,
    source_module VARCHAR(100),
    recipient_type VARCHAR(50),
    severity VARCHAR(20),
    category VARCHAR(50),
    channel_used VARCHAR(50),
    final_status VARCHAR(20),       -- DELIVERED | READ | FAILED | EXPIRED
    time_to_send_ms INT,            -- Latência até envio
    time_to_deliver_ms INT,         -- Latência até entrega
    time_to_read_ms INT,            -- Latência até leitura
    attempts_count INT,             -- Quantas tentativas
    date_dim DATE,                  -- Para particionamento
    hour_dim INT,                   -- 0-23
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Métricas agregadas por dia
CREATE TABLE comm_daily_metrics (
    date DATE,
    channel VARCHAR(50),
    category VARCHAR(50),
    severity VARCHAR(20),
    total_sent INT,
    total_delivered INT,
    total_read INT,
    total_failed INT,
    avg_time_to_deliver_ms FLOAT,
    avg_time_to_read_ms FLOAT,
    PRIMARY KEY (date, channel, category, severity)
);
```

**Critérios de Aceite**:
1. Consolidação via Redis Streams (mesmo padrão Donabedian)
2. Dados analíticos atualizados com latência máxima de 5 minutos
3. Dashboards Grafana com: volume por canal, taxa de entrega, tempo médio de leitura
4. API `/api/v1/analytics/summary` retorna métricas consolidadas
5. Dados particionados por data para performance

---

### DOMÍNIO 6: CONFORMIDADE, AUDITORIA E PREFERÊNCIAS
**Responsável**: Agente DEV-6  
**Escopo**: LGPD, auditoria, preferências do paciente

---

#### EF-COM-050: Gestão de Preferências de Comunicação (LGPD)

**Prioridade**: ALTA  
**Dependências**: Nenhuma (domínio independente)  

**Descrição Funcional**:  
A LGPD (Lei 13.709/2018) exige consentimento explícito para comunicações. O sistema deve:
1. Registrar opt-in/opt-out por canal para cada paciente
2. Respeitar horários de silêncio (quiet hours)
3. Permitir o paciente consultar e alterar suas preferências
4. Bloquear envio para canais sem opt-in

**API de Preferências**:
- `GET /api/v1/preferences/{patient_id}` — Consultar preferências
- `PUT /api/v1/preferences/{patient_id}` — Atualizar preferências
- `POST /api/v1/preferences/{patient_id}/optin/{channel}` — Opt-in em canal
- `DELETE /api/v1/preferences/{patient_id}/optin/{channel}` — Opt-out de canal

**Regras de Negócio**:
1. Alertas CRÍTICOS sempre são enviados (base legal: proteção da vida — Art. 7, VII LGPD)
2. Demais comunicações respeitam opt-in e quiet hours
3. Opt-out deve ser processado em até 24 horas
4. Paciente pode solicitar exclusão de histórico de mensagens (direito ao esquecimento)

**Critérios de Aceite**:
1. Motor de roteamento consulta preferências antes de cada envio
2. Quiet hours bloqueiam mensagens não-críticas (exceto CRITICAL)
3. Logs de consent (opt-in/opt-out) com timestamp para auditoria
4. API acessível pelo paciente via portal (role `patient`)
5. Relatório de conformidade exportável para DPO

---

#### EF-COM-051: Trilha de Auditoria de Comunicações

**Prioridade**: ALTA  
**Dependências**: EF-COM-001, EF-COM-041  

**Descrição Funcional**:  
Toda comunicação clínica deve ser rastreável end-to-end. O sistema deve registrar:
1. Quem enviou (módulo + usuário)
2. Para quem (profissional/paciente)
3. O quê (template + parâmetros, nunca dados clínicos em texto plano no log)
4. Por qual canal
5. Quando (timestamps de cada etapa)
6. Resultado (entregue, lido, falhou)

**Formato FHIR**:  
Cada comunicação clínica deve poder ser exportada como recurso FHIR R4 `Communication`:
```json
{
  "resourceType": "Communication",
  "status": "completed",
  "category": [{"coding": [{"system": "intellicare", "code": "clinical-alert"}]}],
  "priority": "urgent",
  "subject": {"reference": "Patient/{patient_id}"},
  "sender": {"reference": "Device/intellicare-oswaldo"},
  "recipient": [{"reference": "Practitioner/{professional_id}"}],
  "sent": "2026-02-15T20:30:00Z",
  "received": "2026-02-15T20:30:02Z",
  "payload": [{"contentString": "Alerta: Queda de eGFR..."}]
}
```

**Critérios de Aceite**:
1. API `/api/v1/audit/communications` com filtros por data, canal, paciente, módulo
2. Exportação FHIR: `GET /api/v1/fhir/Communication/{id}`
3. Dados de auditoria imutáveis (append-only, sem update/delete)
4. Retenção configurável (padrão: 5 anos para dados clínicos)
5. Acesso à auditoria requer role `admin` ou `care_coordinator`

---

### DOMÍNIO 7: DASHBOARD E MONITORAMENTO
**Responsável**: Agente DEV-7  
**Escopo**: Dashboards Grafana, métricas Prometheus, visibilidade

---

#### EF-COM-060: Dashboard de Comunicações (Grafana)

**Prioridade**: MÉDIA  
**Dependências**: EF-COM-041 (Consolidação)  

**Descrição Funcional**:  
Dashboard Grafana com visão gerencial das comunicações do IntelliCare:

**Painéis**:

| Painel | Métrica | Visualização |
|---|---|---|
| Volume por Canal | Mensagens/hora por canal | Gráfico de barras empilhadas |
| Taxa de Entrega | % entregue por canal | Gauge por canal |
| Tempo Médio de Leitura | Segundos até leitura por severidade | Gráfico de linha |
| Alertas Críticos | Alertas não-lidos > 5min | Tabela com countdown |
| Teleconsultas | Agendadas vs Realizadas vs No-show | Pie chart |
| Canais de Fallback | % de mensagens que usaram fallback | Gauge |
| Top Módulos Emissores | Ranking de módulos por volume | Horizontal bar |
| Erros de Entrega | Erros por canal nas últimas 24h | Alert list |

**Critérios de Aceite**:
1. Dashboard provisionado automaticamente via Grafana API/JSON
2. Dados atualizados a cada 1 minuto
3. Filtros por período, canal, módulo, severidade
4. Alertas Grafana para: taxa de falha > 10%, alerta crítico não-lido > 10min
5. Dashboard acessível via Keycloak SSO (role `admin`, `hospital_admin`, `care_coordinator`)

---

#### EF-COM-061: Métricas Prometheus

**Prioridade**: MÉDIA  
**Dependências**: EF-COM-001  

**Descrição Funcional**:  
Expor métricas de comunicação no formato Prometheus para monitoramento:

```
# Contadores
intellicare_comm_messages_total{channel="rocketchat",severity="critical",status="delivered"} 42
intellicare_comm_messages_total{channel="whatsapp",severity="low",status="failed"} 3

# Histogramas
intellicare_comm_delivery_duration_seconds_bucket{channel="push",le="1"} 95
intellicare_comm_delivery_duration_seconds_bucket{channel="email",le="5"} 80

# Gauges
intellicare_comm_pending_intents 12
intellicare_comm_active_consumers 2
intellicare_comm_channel_health{channel="rocketchat"} 1
intellicare_comm_channel_health{channel="whatsapp"} 0
```

**Critérios de Aceite**:
1. Endpoint `/metrics` no formato Prometheus
2. Scrape interval: 15 segundos
3. Alertas Prometheus/Alertmanager para SLA de comunicação
4. Integração com Grafana existente (prometheus datasource já configurado)

---

## PARTE IV — MATRIZ DE DEPENDÊNCIAS E PARALELISMO

### Diagrama de Dependências entre EFs

```
                    EF-COM-003 (Templates)
                         │
EF-COM-001 (Router) ─────┤──── EF-COM-050 (LGPD/Preferências)
     │                   │              │
     ├── EF-COM-002 ─────┤              │
     │   (Dispatchers)   │              │
     │        │          │              │
     │   ┌────┼────┬─────┼──────┐       │
     │   │    │    │     │      │       │
     │  010  030  033   031    032      │
     │  (RC) (Push)(Email)(WA) (SMS)    │
     │   │                              │
     │  011 (Sync KC→RC)                │
     │  012 (Bot RC)                    │
     │                                  │
     ├── EF-COM-020 (Teleconsulta)      │
     │   021 (Sala de Caso)             │
     │                                  │
     ├── EF-COM-040 (Consumer Multi) ───┤
     │        │                         │
     │   EF-COM-041 (Consolidação) ─────┤
     │        │                         │
     │   EF-COM-060 (Dashboard) ────────┘
     │   EF-COM-061 (Prometheus)
     │
     └── EF-COM-051 (Auditoria)
```

### Plano de Desenvolvimento Paralelo

| Sprint | Agente DEV-1 | Agente DEV-2 | Agente DEV-3 | Agente DEV-4 | Agente DEV-5 | Agente DEV-6 |
|---|---|---|---|---|---|---|
| **S1** | EF-COM-001 (Router) | EF-COM-003 (Templates) | — | — | — | EF-COM-050 (LGPD) |
| **S2** | EF-COM-002 (Dispatchers) | EF-COM-010 (RC API) | EF-COM-020 (Teleconsulta) | EF-COM-030 (Push) | EF-COM-040 (Consumer) | EF-COM-051 (Auditoria) |
| **S3** | Integração | EF-COM-011+012 (Sync+Bot) | EF-COM-021 (Sala Caso) | EF-COM-033 (Email) | EF-COM-041 (Consolidação) | — |
| **S4** | — | — | — | EF-COM-031 (WhatsApp) | EF-COM-060+061 (Dashboard) | — |
| **S5** | — | — | — | EF-COM-032 (SMS) | — | — |
| **S6** | **Integração Final + Testes E2E** |

---

## PARTE V — CONTRATOS E INTERFACES

### 5.1 API Contract (OpenAPI Summary)

```
Base URL: /api/v1

# Roteamento
POST   /routing/send                    → Enviar CommunicationIntent
GET    /routing/metrics                 → Métricas do router
GET    /routing/rules                   → Regras de roteamento ativas

# Canais
GET    /channels                        → Lista canais disponíveis
GET    /channels/{channel}/health       → Health de canal específico

# Templates
POST   /templates                       → Criar template
GET    /templates                       → Listar templates
GET    /templates/{id}                  → Detalhe do template
PUT    /templates/{id}                  → Atualizar template
DELETE /templates/{id}                  → Remover template
POST   /templates/{id}/preview          → Preview com dados

# Rocket.Chat
POST   /rocketchat/message             → Enviar mensagem RC
POST   /rocketchat/channel             → Criar canal
POST   /rocketchat/channel/{id}/invite → Convidar pessoa
GET    /rocketchat/channels             → Listar canais

# Teleconsulta
POST   /teleconsult/schedule            → Agendar
GET    /teleconsult/{id}                → Detalhe
PUT    /teleconsult/{id}/cancel         → Cancelar
GET    /teleconsult/patient/{pid}       → Por paciente
GET    /teleconsult/professional/{pid}  → Por profissional

# Push
POST   /push/subscribe                 → Registrar dispositivo
GET    /push/subscriptions/{user_id}   → Listar subscriptions
DELETE /push/subscriptions/{id}        → Remover subscription

# Preferências LGPD
GET    /preferences/{patient_id}       → Consultar
PUT    /preferences/{patient_id}       → Atualizar
POST   /preferences/{patient_id}/optin/{channel}  → Opt-in
DELETE /preferences/{patient_id}/optin/{channel}   → Opt-out

# Eventos
GET    /events/consumer/status          → Status do consumer
POST   /events/consumer/start           → Iniciar consumer
POST   /events/consumer/stop            → Parar consumer
GET    /events/metrics                  → Métricas de eventos

# Auditoria
GET    /audit/communications            → Buscar (filtros)
GET    /fhir/Communication/{id}         → Exportar como FHIR

# Analytics
GET    /analytics/summary               → Resumo consolidado
GET    /analytics/by-channel             → Por canal
GET    /analytics/by-severity            → Por severidade

# Saúde
GET    /health                          → Health check geral
GET    /info                            → Informações do módulo
GET    /metrics                         → Prometheus metrics
```

### 5.2 Eventos Redis Streams (Produzidos pelo Módulo)

| Stream | Evento | Quando |
|---|---|---|
| `intellicare:comm.sent` | Mensagem enviada | Após dispatch bem-sucedido |
| `intellicare:comm.delivered` | Mensagem entregue | Confirmação do canal |
| `intellicare:comm.read` | Mensagem lida | Confirmação de leitura |
| `intellicare:comm.failed` | Falha de entrega | Após todas tentativas |
| `intellicare:teleconsult.scheduled` | Teleconsulta agendada | Após criação |
| `intellicare:teleconsult.completed` | Teleconsulta realizada | Após encerramento |

### 5.3 Variáveis de Ambiente

```bash
# Core
INTELLICARE_COMUNICACAO_PORT=8010
INTELLICARE_COMUNICACAO_DB_URL=postgresql://...
INTELLICARE_COMUNICACAO_REDIS_URL=redis://...

# Rocket.Chat
ROCKETCHAT_URL=https://rocket.gsi.srv.br
ROCKETCHAT_BOT_USERNAME=intellicare-bot
ROCKETCHAT_BOT_PASSWORD=<secret>
ROCKETCHAT_ADMIN_TOKEN=<token>

# Matrix
MATRIX_HOMESERVER=https://matrix.gsi.srv.br
MATRIX_BOT_USER=@intellicare_bot:matrix.gsi.srv.br
MATRIX_BOT_PASSWORD=<secret>

# Jitsi
JITSI_URL=https://meet.gsi.srv.br
JITSI_JWT_SECRET=<from_keycloak>
JITSI_JWT_APP_ID=jitsi-meet

# Push
VAPID_PUBLIC_KEY=<generated>
VAPID_PRIVATE_KEY=<generated>
FCM_SERVER_KEY=<optional>

# WhatsApp
WHATSAPP_API_URL=https://graph.facebook.com/v18.0
WHATSAPP_PHONE_NUMBER_ID=<meta_id>
WHATSAPP_ACCESS_TOKEN=<meta_token>

# SMS
SMS_GATEWAY_URL=<provider_url>
SMS_API_KEY=<provider_key>

# Email
SMTP_HOST=<smtp_host>
SMTP_PORT=587
SMTP_USERNAME=<user>
SMTP_PASSWORD=<password>
EMAIL_FROM=intellicare@gsi.srv.br

# Keycloak
KEYCLOAK_URL=https://keycloak.gsi.srv.br
KEYCLOAK_REALM=bemcuidar
KEYCLOAK_CLIENT_ID=intellicare-comunicacao
KEYCLOAK_CLIENT_SECRET=<secret>
```

---

## PARTE VI — VISÃO DE FUTURO

### O Que Isso Representa para a Saúde

Quando este módulo estiver completo, o IntelliCare terá uma capacidade **sem precedentes** no cenário brasileiro de saúde digital:

1. **Zero delay em alertas críticos**: Um paciente diabético cujo eGFR cai abaixo de 30 ml/min/1.73m² terá sua equipe notificada em **menos de 5 segundos** — via push, Rocket.Chat e SMS simultaneamente. Hoje, esse alerta pode levar **dias** para chegar ao médico via prontuário físico.

2. **Teleconsulta integrada ao fluxo clínico**: Não é apenas "uma chamada de vídeo". É uma teleconsulta onde o médico já entra sabendo o histórico completo (Wanda), os últimos exames (Florence), os alertas recentes (Oswaldo) e o plano de cuidado (Geralda) — tudo na tela, antes do paciente dizer "alô".

3. **Paciente como protagonista**: Via WhatsApp, o paciente recebe lembretes de medicação, pergunta dúvidas ao Dr. Nise, recebe resultados de exames e é lembrado de consultas — no canal que já usa todo dia, sem precisar instalar nada.

4. **Gestão baseada em evidências (Donabedian)**: O gestor vê em tempo real quantas comunicações críticas foram lidas em menos de 5 minutos, quantas teleconsultas tiveram no-show, qual canal tem a melhor taxa de entrega — dados que hoje simplesmente **não existem** em nenhum sistema público brasileiro.

5. **Conformidade LGPD nativa**: Não é um patch posterior. Cada mensagem respeita opt-in, quiet hours, direito ao esquecimento e rastreabilidade completa. O DPO tem relatórios automáticos.

6. **Interoperabilidade FHIR**: Cada comunicação clínica é um recurso FHIR `Communication`, pronto para integrar com qualquer sistema que siga o padrão (RNDS, S-Codes, outros).

### Benchmark Internacional

| Capacidade | IntelliCare (Planejado) | Epic MyChart | Cerner CareAware | SUS Atual |
|---|---|---|---|---|
| Alertas multi-canal | ✅ 6 canais + fallback | ✅ 3 canais | ✅ 2 canais | ❌ Manual |
| Teleconsulta integrada | ✅ Jitsi + contexto clínico | ✅ Proprietário | ✅ Proprietário | ❌ Não existe |
| WhatsApp nativo | ✅ Business API | ❌ | ❌ | ❌ |
| Chatbot clínico | ✅ Dr. Nise (Ollama/Flowise) | ✅ Parcial | ❌ | ❌ |
| FHIR Communication | ✅ R4 nativo | ✅ Parcial | ✅ Parcial | ❌ |
| LGPD/consent management | ✅ Nativo | N/A (HIPAA) | N/A (HIPAA) | ❌ |
| Open source | ✅ 100% | ❌ | ❌ | Variável |
| Custo | ✅ Livre | $$$$ | $$$$ | N/A |

---

## PARTE VII — INSTRUÇÕES PARA AGENTES DEV

### Para cada Domínio Funcional, o agente DEV deve:

1. **Receber** este documento e ler inteiramente o domínio atribuído
2. **Gerar** Especificações Técnicas incluindo:
   - Diagrama de classes/componentes
   - Schemas de banco de dados (migrations Alembic)
   - Contratos de API (OpenAPI/Pydantic models)
   - Testes unitários e de integração planejados
   - Dependências de pacotes Python
3. **Gerar** Plano de Implementação incluindo:
   - Estimativa de esforço (story points ou horas)
   - Ordem de implementação dentro do domínio
   - Pontos de integração com outros domínios
   - Riscos e mitigações
4. **Submeter** para revisão e aprovação antes de codificar
5. **Desenvolver** seguindo os padrões do IntelliCare:
   - Dual-schema (operacional/analítico)
   - BaseDAO[T] do intellicare-core
   - EventPublisher para Redis Streams
   - Keycloak auth middleware
   - Testes com cobertura ≥ 80%
   - Documentação inline (docstrings)

### Padrões de Código Obrigatórios

- **Python 3.11+**, FastAPI, SQLAlchemy 2.0, Pydantic 2.5
- **Imports**: do `intellicare-core` para BaseDAO, EventPublisher, BaseModuleConfig
- **Testes**: pytest, fixtures, mocks para serviços externos
- **Migrations**: Alembic com nomenclatura `YYYY_MM_DD_HHMM_description.py`
- **Logs**: structlog com correlation_id em cada entrada
- **Métricas**: prometheus_client para counters/histograms
- **Config**: Pydantic-settings com prefixo `INTELLICARE_COMUNICACAO_`

---

**Documento gerado em**: 15/02/2026  
**Próxima Revisão**: Após retorno das Especificações Técnicas dos Agentes DEV  
**Aprovação**: Pendente — Arquiteto-Chefe (Eduardo Garabini)

---

*"A comunicação na saúde não é sobre tecnologia. É sobre o segundo que separa um alerta do cuidado. É sobre a mensagem que lembra o paciente de tomar o remédio. É sobre a teleconsulta que evita uma internação. Cada milissegundo conta. Cada canal importa. Cada vida merece a melhor comunicação possível."*
