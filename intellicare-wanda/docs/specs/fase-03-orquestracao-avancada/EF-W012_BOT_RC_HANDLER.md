# EF-W012 — Bot Rocket.Chat Handler

> **[NOVO V5]** Processa comandos do @intellicare via Rocket.Chat — /paciente, /guideline, /resumo, /alerta, /teleconsulta, /ajuda.

## 1. Objetivo

Implementar o handler do bot **@intellicare** no Rocket.Chat para que a equipe clínica possa interagir com o ecossistema IntelliCare diretamente no chat:

- Receber comandos via webhook do Rocket.Chat
- Autenticar e autorizar por usuário/sala/role RBAC (Keycloak)
- Rotear comandos para os agentes corretos via WANDA
- Formatar respostas em mensagens RC (texto, attachments, botões)
- Manter contexto de conversa por usuário/sala (Redis)

## 2. Justificativa

- **Fluxo natural**: Médicos já usam RC como hub de comunicação — não devem sair do app
- **Acesso contextual**: `/paciente 12345` mostra resumo imediato no canal do time
- **Alertas ativos**: Bot pode iniciar conversa, não só responder
- **Teleconsulta**: `/teleconsulta 12345 dr_joao` cria sala Jitsi direto do RC
- **Auditoria**: Todo comando bot é rastreado com correlation_id (EF-W009)

## 3. Escopo

### 3.1 Comandos Suportados

| Comando | Sintaxe | Descrição | Permissão |
|---------|---------|-----------|-----------|
| `/paciente` | `/paciente {patient_id}` | Resumo clínico do paciente (IPS + alertas + plano) | médico, enfermeiro |
| `/guideline` | `/guideline {query}` | Busca guideline clínico (Florence RAG + PIERRE PubMed) | todos |
| `/resumo` | `/resumo {patient_id} [período]` | Relatório de acompanhamento (Geralda) | médico, enfermeiro |
| `/alerta` | `/alerta {patient_id} {msg}` | Cria alerta manual urgente (AlertHub EF-W007) | médico |
| `/teleconsulta` | `/teleconsulta {patient_id} [@user]` | Cria sala Jitsi (Comunicacao) | médico, admin |
| `/ajuda` | `/ajuda [comando]` | Ajuda contextual | todos |
| `/status` | `/status` | Status dos agentes do ecossistema | admin |

### 3.2 Arquitetura do Handler

```
Rocket.Chat (evento de mensagem/comando)
    │
    ▼ POST /api/v1/bot/command  (webhook incoming)
WandaBotHandler
    │
    ├─► CommandParser          → extrai comando, args, autor, sala
    ├─► AuthMiddleware         → valida token RC → verifica role Keycloak
    ├─► CommandRouter          → roteia para handler específico
    │
    ├─► PatientCommandHandler  (/paciente → WANDA orchestrate → formatar)
    ├─► GuidelineCommandHandler (/guideline → Florence + PIERRE → formatar)
    ├─► ResumoCommandHandler   (/resumo → Geralda → formatar)
    ├─► AlertaCommandHandler   (/alerta → AlertHub → RC mensagem)
    ├─► TeleconsultaHandler    (/teleconsulta → Comunicacao → Jitsi link)
    ├─► AjudaCommandHandler    (/ajuda → texto estático/dinâmico)
    └─► StatusCommandHandler   (/status → ModuleRegistry → tabela)
    │
    ▼
RocketChatResponseFormatter  → monta attachments, botões, markdown RC
    │
    ▼ POST (RC Incoming Webhook / REST API)
Rocket.Chat (responde na sala)
```

### 3.3 WandaBotHandler

```python
# wanda/bot/rc_handler.py

from pydantic import BaseModel
from enum import Enum
from typing import Optional

class BotCommand(str, Enum):
    PACIENTE = "paciente"
    GUIDELINE = "guideline"
    RESUMO = "resumo"
    ALERTA = "alerta"
    TELECONSULTA = "teleconsulta"
    AJUDA = "ajuda"
    STATUS = "status"

class RCIncomingMessage(BaseModel):
    """Payload do webhook incoming do Rocket.Chat."""
    token: str                      # Token de autenticação do webhook
    channel_id: str
    channel_name: str
    user_id: str
    user_name: str
    text: str                       # Texto completo da mensagem
    timestamp: str
    bot: Optional[bool] = False

class ParsedCommand(BaseModel):
    command: BotCommand
    args: list[str]
    patient_id: Optional[str]       # Extraído dos args quando aplicável
    raw_args: str
    user_id: str
    user_name: str
    channel_id: str
    channel_name: str
    correlation_id: str             # UUID gerado por requisição

class WandaBotHandler:
    """
    Handler central para comandos do bot @intellicare no Rocket.Chat.

    Recebe webhooks do RC, valida, roteia e responde.
    """

    def __init__(
        self,
        command_parser: "CommandParser",
        auth_middleware: "BotAuthMiddleware",
        command_router: "CommandRouter",
        rc_client: "RocketChatBotClient",
        context_store: "BotContextStore",    # Redis
        audit_logger: "BotAuditLogger",
    ):
        ...

    async def handle_webhook(
        self,
        payload: RCIncomingMessage,
    ) -> dict:
        """
        Entry point para POST /api/v1/bot/command.

        Fluxo:
        1. Validar token webhook (ROCKETCHAT_WEBHOOK_TOKEN)
        2. Ignorar mensagens do próprio bot (payload.bot=True)
        3. Parsear comando (CommandParser)
        4. Autenticar usuário (BotAuthMiddleware)
        5. Rotear para handler específico (CommandRouter)
        6. Responder no RC (RocketChatBotClient)
        7. Logar no audit (BotAuditLogger)

        Returns: {"status": "ok", "correlation_id": "..."}
        """
        ...

    async def send_error(
        self,
        channel_id: str,
        error_msg: str,
        correlation_id: str,
    ) -> None:
        """Responde com mensagem de erro formatada no RC."""
        ...
```

### 3.4 CommandParser

```python
class CommandParser:
    """
    Extrai comando e argumentos de uma mensagem RC.

    Exemplos:
    "@intellicare /paciente 12345"    → BotCommand.PACIENTE, args=["12345"]
    "/guideline DRC KDIGO 2024"       → BotCommand.GUIDELINE, args=["DRC KDIGO 2024"]
    "/teleconsulta 12345 @dr_joao"    → BotCommand.TELECONSULTA, args=["12345", "dr_joao"]
    """

    # Prefixos aceitos (menção + comando direto)
    TRIGGERS = ["@intellicare", "/"]

    def parse(self, text: str, user_id: str, channel_id: str) -> Optional[ParsedCommand]:
        """
        Retorna ParsedCommand ou None se texto não é um comando.

        Lógica:
        - Procura por /<comando> no texto
        - Valida se comando está em BotCommand
        - Extrai patient_id se primeiro arg é numérico/UUID
        - Gera correlation_id
        """
        ...

    def extract_patient_id(self, args: list[str]) -> Optional[str]:
        """Primeiro arg numérico ou UUID é tratado como patient_id."""
        ...
```

### 3.5 BotAuthMiddleware

```python
class BotAuthMiddleware:
    """
    Valida identidade do usuário RC via Keycloak.

    Flow:
    1. RC user_id → lookup no Keycloak (realm bemcuidar)
    2. Verificar roles RBAC para o comando solicitado
    3. Se patient_id presente → verificar acesso ao paciente (LGPD)
    """

    COMMAND_ROLES = {
        BotCommand.PACIENTE:       ["medico", "enfermeiro", "admin"],
        BotCommand.GUIDELINE:      ["medico", "enfermeiro", "tecnico", "admin"],
        BotCommand.RESUMO:         ["medico", "enfermeiro", "admin"],
        BotCommand.ALERTA:         ["medico", "admin"],
        BotCommand.TELECONSULTA:   ["medico", "admin"],
        BotCommand.AJUDA:          ["medico", "enfermeiro", "tecnico", "admin", "paciente"],
        BotCommand.STATUS:         ["admin"],
    }

    async def authorize(
        self,
        command: ParsedCommand,
    ) -> AuthResult:
        """
        Verifica se user_id tem permissão para o comando.

        Se não autorizado → retorna AuthResult(authorized=False, reason=...)
        Handler deve responder com mensagem de erro no RC.
        """
        ...
```

### 3.6 Handlers por Comando

```python
class PatientCommandHandler:
    """
    /paciente {patient_id}

    Retorna resumo clínico completo do paciente.
    """

    async def execute(self, cmd: ParsedCommand) -> RCMessage:
        """
        Fluxo:
        1. Chama WANDA /api/v1/orchestrate com patient_id
        2. WANDA executa: IPS-First → Oswaldo + Florence + Geralda
        3. Formata resposta como RC attachment com seções:
           - Cabeçalho: nome, idade, CPF mascarado
           - Condições Crônicas (Oswaldo — staging)
           - Alertas Ativos (Florence/Oswaldo)
           - Plano de Cuidado (Geralda — próximas ações)
           - Exames Recentes (Florence — labs)
        4. Adiciona botão "Ver Prontuário" com link para Portal
        """
        ...

class GuidelineCommandHandler:
    """
    /guideline {query}

    Busca guideline clínico via Florence (RAG) e PIERRE (PubMed).
    """

    async def execute(self, cmd: ParsedCommand) -> RCMessage:
        """
        Fluxo:
        1. POST Florence /api/v1/analyze com query
        2. Se PIERRE disponível (EF-W011): call tool search_pubmed
        3. Agrega: guideline local (Florence) + evidências (PIERRE)
        4. Formata: citação + trecho relevante + link
        Timeout: 15s (PIERRE pode ser lento)
        """
        ...

class ResumoCommandHandler:
    """
    /resumo {patient_id} [30d|90d|6m]

    Relatório de acompanhamento do período.
    """

    async def execute(self, cmd: ParsedCommand) -> RCMessage:
        """
        Chama Geralda /api/v1/analyze → resumo de acompanhamento.
        Período padrão: 30 dias.
        Formato: attachment com tabela de consultas + aderência + evolução.
        """
        ...

class AlertaCommandHandler:
    """
    /alerta {patient_id} {mensagem}

    Cria alerta manual urgente no AlertHub.
    """

    async def execute(self, cmd: ParsedCommand) -> RCMessage:
        """
        POST /api/v1/alerts/manual com:
        - patient_id, severity=CRITICAL, source=bot, message=cmd.raw_args
        AlertHub (EF-W007) processa e roteia para equipe.
        Responde com confirmação + correlation_id.
        """
        ...

class TeleconsultaCommandHandler:
    """
    /teleconsulta {patient_id} [@profissional]

    Cria sala Jitsi e notifica profissional.
    """

    async def execute(self, cmd: ParsedCommand) -> RCMessage:
        """
        POST Comunicacao /api/v1/teleconsult/create com:
        - patient_id, host_user_id, invited_user (opcional)
        Comunicacao gera JWT Jitsi e cria sala.
        Responde com link direto: https://meet.gsi.srv.br/{room}
        """
        ...

class StatusCommandHandler:
    """
    /status

    Mostra status de todos os agentes do ecossistema.
    """

    async def execute(self, cmd: ParsedCommand) -> RCMessage:
        """
        Consulta ModuleRegistry (EF-W001).
        Formata tabela: módulo | status | latência | último check.
        Usa emoji 🟢🟡🔴 para indicar saúde.
        """
        ...
```

### 3.7 RocketChatResponseFormatter

```python
class RocketChatResponseFormatter:
    """
    Formata respostas para o formato de attachment do Rocket.Chat.

    RC suporta: texto markdown, attachments com campos, botões (actions).
    """

    def format_patient_summary(
        self,
        patient_name: str,
        conditions: list[dict],
        alerts: list[dict],
        care_plan: dict,
        correlation_id: str,
    ) -> dict:
        """
        Retorna payload RC com:
        {
          "text": "Resumo: João Silva",
          "attachments": [{
            "color": "#2196F3",
            "title": "Condições Crônicas",
            "fields": [
              {"title": "DRC G3aA2", "value": "Creatinina 2.1 (estável)", "short": True},
              ...
            ],
            "actions": [
              {"type": "button", "text": "Ver Prontuário", "url": "..."}
            ]
          }]
        }
        """
        ...

    def format_error(self, error: str, correlation_id: str) -> dict:
        """Attachment vermelho com mensagem de erro e correlation_id."""
        ...

    def format_guideline(
        self,
        query: str,
        local_result: str,
        pubmed_result: Optional[str],
    ) -> dict:
        """Attachment azul com resultado RAG + citação PubMed."""
        ...
```

### 3.8 BotContextStore (Redis)

Mantém contexto de conversa por usuário para comandos multi-turno futuros:

```
wanda:bot:context:{user_id}:{channel_id}    TTL=1800s (30min)
{
  "last_patient_id": "12345",
  "last_command": "paciente",
  "timestamp": "2026-02-17T10:00:00Z"
}
```

Permite que próximo `/resumo` sem patient_id use o último paciente consultado.

### 3.9 BotAuditLogger

```python
# Cada comando bot é auditado (integra com EF-W009)
INSERT INTO wanda_operacional.bot_command_log (
    correlation_id,
    user_id, user_name,
    channel_id, channel_name,
    command, args,
    patient_id,
    authorized,
    response_status,   -- "success" | "error" | "timeout"
    latency_ms,
    created_at
);
```

---

## 4. API

### 4.1 Endpoint Principal

```
POST /api/v1/bot/command
Content-Type: application/json

{
  "token": "ROCKETCHAT_WEBHOOK_TOKEN",
  "channel_id": "GENERAL",
  "channel_name": "equipe-cardiologia",
  "user_id": "dr_joao_rc_id",
  "user_name": "dr_joao",
  "text": "@intellicare /paciente 12345",
  "timestamp": "2026-02-17T10:00:00Z"
}

Response 200:
{
  "status": "ok",
  "correlation_id": "abc-123"
}
```

A resposta ao usuário é enviada de forma assíncrona via RC API (não no response do webhook).

### 4.2 Endpoints Adicionais

| Método | Path | Descrição |
|--------|------|-----------|
| `GET` | `/api/v1/bot/status` | Status do bot (conectado ao RC?) |
| `GET` | `/api/v1/bot/commands` | Lista comandos disponíveis (para ajuda dinâmica) |
| `GET` | `/api/v1/bot/metrics` | Comandos por tipo, latência média |
| `GET` | `/api/v1/bot/log` | Últimos 50 comandos executados (admin) |

---

## 5. Configuração

```bash
# Rocket.Chat
ROCKETCHAT_URL=https://rocket.gsi.srv.br
ROCKETCHAT_BOT_TOKEN=<bot_auth_token>         # Token do usuário bot
ROCKETCHAT_WEBHOOK_TOKEN=<webhook_secret>      # Token de validação incoming
ROCKETCHAT_BOT_USER_ID=<bot_user_id>

# Keycloak (para autorização)
KEYCLOAK_URL=https://keycloak.gsi.srv.br
KEYCLOAK_REALM=bemcuidar
KEYCLOAK_CLIENT_ID=intellicare-wanda

# Comportamento
BOT_CONTEXT_TTL=1800                           # Segundos de contexto por usuário
BOT_MAX_RESPONSE_TIME=30                       # Timeout total do handler
BOT_DEFAULT_PERIOD=30d                         # Período padrão para /resumo
```

---

## 6. Testes

| # | Teste | Tipo |
|---|-------|------|
| T01 | Webhook com token inválido retorna 403 | API |
| T02 | Mensagem do próprio bot é ignorada silenciosamente | Unit |
| T03 | `/paciente 12345` parsa patient_id=12345 corretamente | Unit |
| T04 | `/guideline DRC KDIGO` parsa sem patient_id | Unit |
| T05 | Usuário sem role "medico" recebe "Acesso negado" para `/paciente` | Integration |
| T06 | `/ajuda` responde para qualquer role | Unit |
| T07 | PatientCommandHandler chama WANDA orchestrate com IPS | Integration |
| T08 | GuidelineCommandHandler agrega Florence + PIERRE (se disponível) | Integration |
| T09 | GuidelineCommandHandler funciona se PIERRE offline (graceful) | Integration |
| T10 | TeleconsultaCommandHandler retorna link Jitsi válido | Integration |
| T11 | AlertaCommandHandler cria alerta CRITICAL no AlertHub | Integration |
| T12 | StatusCommandHandler formata tabela com todos os módulos | Integration |
| T13 | BotContextStore salva último patient_id no Redis | Unit |
| T14 | `/resumo` sem patient_id usa contexto anterior do Redis | Integration |
| T15 | Timeout de WANDA resulta em mensagem de erro no RC | Integration |
| T16 | BotAuditLogger persiste cada comando com correlation_id | Integration |
| T17 | format_patient_summary gera attachment RC válido | Unit |
| T18 | format_error inclui correlation_id para rastreamento | Unit |
| T19 | Handler responde 200 imediatamente (resposta RC é async) | API |
| T20 | Métricas Prometheus incrementadas por comando | Unit |

**Cobertura mínima:** ≥ 85%

---

## 7. Critérios de Aceitação

- [ ] 7 comandos implementados e funcionais (/paciente, /guideline, /resumo, /alerta, /teleconsulta, /ajuda, /status)
- [ ] Autenticação via token webhook + autorização RBAC por role Keycloak
- [ ] Resposta formatada como RC attachment com campos e botões
- [ ] Contexto de conversa por usuário/sala (Redis, TTL 30min)
- [ ] Audit log de todos os comandos (EF-W009 integration)
- [ ] Graceful degradation: PIERRE offline não quebra `/guideline`
- [ ] Webhook retorna 200 imediatamente (resposta RC é assíncrona)
- [ ] 20+ testes passando
- [ ] Cobertura ≥ 85%

---

## 8. Estimativa de Complexidade

- **Arquivos novos**: ~10 (handler, parser, auth, 7 command handlers, formatter, audit)
- **Arquivos modificados**: ~3 (api/app.py, config.py, docker-compose.yml)
- **Linhas estimadas**: ~1.500
- **Testes novos**: ~20

---

## 9. Dependências

| Dependência | Uso |
|-------------|-----|
| `intellicare-comunicacao` | Teleconsulta (Jitsi) + envio de mensagens RC |
| EF-W001 | ModuleRegistry para /status |
| EF-W005 | LangGraph orchestration para /paciente (complexo) |
| EF-W007 | AlertHub para /alerta |
| EF-W009 | correlation_id propagado em todos os comandos |
| Keycloak | RBAC por role (bemcuidar realm) |
| Redis | BotContextStore (contexto de conversa) |
| ROCKETCHAT_WEBHOOK_TOKEN | Validação do webhook incoming |
