# EF-W013 — Dr. Nise / FLOWISE (Chatbot do Paciente)

> **[NOVO V5]** Chatbot educacional para pacientes, delegado ao FLOWISE, com persona "Dr. Nise" — homenagem à Dra. Nise da Silveira, psiquiatra brasileira pioneira na humanização do cuidado.

## 1. Objetivo

Implementar o **chatbot para pacientes** do IntelliCare usando o FLOWISE como motor de IA:

- WANDA recebe mensagens do paciente via Portal ou Rocket.Chat
- Delega ao FLOWISE (endpoint configurado) com contexto do paciente (IPS)
- FLOWISE processa com sua chain/flow de educação em saúde
- WANDA retorna resposta ao cliente original
- Sessões de conversa persistidas para continuidade

A Dra. Nise é a persona do chatbot — empática, humanizada, não-diagnóstica, focada em educação e orientação de saúde.

## 2. Justificativa

- **Separação de responsabilidades**: WANDA orquestra agentes clínicos — educação de pacientes é domínio diferente, melhor em FLOWISE com flows visuais configuráveis pela equipe de saúde
- **FLOWISE já implantado**: Infraestrutura disponível — não requer nova stack
- **Persona configurável**: Equipe pode ajustar o flow Dr. Nise no FLOWISE sem deploy
- **Escalabilidade**: Múltiplos pacientes simultaneamente sem sobrecarregar WANDA
- **Contexto clínico seguro**: WANDA injeta IPS simplificado (sem dados sensíveis em excesso) e FLOWISE o usa para personalizar a resposta

## 3. Escopo

### 3.1 Arquitetura

```
Portal (paciente) ou RC (bot)
    │
    ▼ POST /api/v1/chat/patient
WANDA — DrNiseGateway
    │
    ├─► SessionManager      → obtém/cria sessão do paciente (Redis)
    ├─► IPSSimplifier       → extrai contexto seguro do IPS (EF-W002)
    ├─► FlowiseClient       → POST ao FLOWISE com mensagem + contexto
    │       │
    │       ▼ FLOWISE (servidor)
    │       Flow "Dr. Nise Education"
    │       (configurado pela equipe no FLOWISE UI)
    │       ├─ System prompt: persona Dr. Nise
    │       ├─ Contexto: IPS simplificado injetado como variável
    │       └─ LLM: Claude/Ollama/OpenAI (configurado no FLOWISE)
    │
    ├─► ResponseFilter      → filtra respostas inadequadas (safety)
    ├─► SessionUpdater      → atualiza histórico da sessão
    └─► AuditLogger         → registra interação (EF-W009)
    │
    ▼ Resposta para Portal/RC
```

### 3.2 DrNiseGateway

```python
# wanda/nise/dr_nise_gateway.py

from pydantic import BaseModel
from typing import Optional

class PatientMessage(BaseModel):
    """Mensagem enviada pelo paciente."""
    patient_id: str
    message: str
    channel: str            # "portal" | "rocketchat" | "whatsapp"
    session_id: Optional[str] = None    # Continua sessão existente se fornecido
    correlation_id: str

class DrNiseResponse(BaseModel):
    """Resposta da Dra. Nise."""
    response: str
    session_id: str
    disclaimer: str         # "Sou a Dr. Nise, assistente educacional. Não substituo atendimento médico."
    source: str             # "flowise" | "fallback"
    latency_ms: int
    correlation_id: str
    flagged: bool = False   # True se ResponseFilter detectou conteúdo inadequado

class DrNiseGateway:
    """
    Gateway da WANDA para o FLOWISE (Dr. Nise).

    Responsável por:
    - Gerenciar sessões de conversa (Redis)
    - Enriquecer mensagens com contexto IPS simplificado
    - Delegar ao FLOWISE
    - Filtrar respostas
    - Auditar interações
    """

    def __init__(
        self,
        flowise_client: "FlowiseClient",
        session_manager: "NiseSessionManager",
        ips_simplifier: "IPSSimplifier",
        response_filter: "NiseResponseFilter",
        audit_logger: "NiseAuditLogger",
        ips_manager,        # De EF-W002
    ):
        ...

    async def chat(
        self,
        msg: PatientMessage,
    ) -> DrNiseResponse:
        """
        Processa mensagem do paciente e retorna resposta da Dr. Nise.

        Fluxo:
        1. Obter/criar sessão (NiseSessionManager)
        2. Buscar IPS do paciente (IPSManager.get — EF-W002)
        3. Simplificar IPS para contexto seguro (IPSSimplifier)
        4. Enviar ao FLOWISE (FlowiseClient.chat)
        5. Filtrar resposta (NiseResponseFilter)
        6. Atualizar sessão com histórico
        7. Auditar interação
        8. Retornar DrNiseResponse

        Em caso de falha FLOWISE:
        - Usar fallback (mensagem orientando a contatar equipe)
        - NÃO tentar responder clinicamente com outro LLM
        """
        ...

    async def get_session_history(
        self,
        patient_id: str,
        session_id: str,
    ) -> list[dict]:
        """Retorna histórico de conversa da sessão para exibição no Portal."""
        ...

    async def end_session(
        self,
        patient_id: str,
        session_id: str,
    ) -> None:
        """Encerra sessão e persiste histórico no PostgreSQL."""
        ...
```

### 3.3 FlowiseClient

```python
class FlowiseClient:
    """
    Cliente HTTP para o FLOWISE.

    O FLOWISE expõe uma API REST simples:
    POST /api/v1/prediction/{chatflowid}

    O chatflowid é o flow "Dr. Nise Education" configurado no FLOWISE UI.
    """

    def __init__(
        self,
        flowise_url: str,           # FLOWISE_URL (ex: http://flowise:3001)
        chatflow_id: str,           # FLOWISE_DR_NISE_FLOW_ID
        api_key: Optional[str],     # FLOWISE_API_KEY (se configurado)
        timeout_seconds: int = 30,
    ):
        ...

    async def chat(
        self,
        message: str,
        session_id: str,
        overrideConfig: Optional[dict] = None,  # Injetar contexto IPS
    ) -> FlowiseResponse:
        """
        Envia mensagem ao FLOWISE e retorna resposta.

        Payload:
        {
          "question": message,
          "overrideConfig": {
            "sessionId": session_id,
            "vars": {
              "patient_context": ips_simplified_json,
              "persona": "dr_nise"
            }
          }
        }

        Response:
        {
          "text": "Olá! Sou a Dr. Nise. Entendo que você...",
          "question": "...",
          "chatId": "...",
          "sessionId": "..."
        }
        """
        ...

    async def health_check(self) -> bool:
        """GET /api/v1/ping — verifica se FLOWISE está acessível."""
        ...
```

### 3.4 IPSSimplifier

```python
class IPSSimplifier:
    """
    Extrai contexto seguro do IPS para enviar ao FLOWISE.

    PRINCÍPIO DE MÍNIMO PRIVILÉGIO:
    O FLOWISE não deve receber o IPS completo (FHIR Bundle bruto).
    Recebe apenas o contexto necessário para personalizar a resposta educacional,
    sem dados que não são necessários para educação em saúde.
    """

    def simplify(self, ips: dict, patient_id: str) -> dict:
        """
        Extrai e simplifica dados do IPS para contexto educacional.

        Retorna:
        {
          "patient_id": "hash_do_id",      # Hasheado — não o ID real
          "conditions": ["DRC G3a", "DM2", "HAS"],   # Apenas nomes
          "medications_count": 5,           # Contagem, não nomes
          "allergies": ["Penicilina"],      # Sim — relevante para educação
          "language": "pt-BR",
          "education_level": "médio",       # Se disponível
          "last_visit_days_ago": 15         # Contexto temporal
        }

        NÃO inclui:
        - CPF, nome completo, data de nascimento
        - Valores laboratoriais específicos
        - Nomes de medicamentos (apenas contagem)
        - Dados de outros profissionais
        """
        ...
```

### 3.5 NiseSessionManager

```python
class NiseSessionManager:
    """
    Gerencia sessões de conversa do paciente com a Dr. Nise.

    Sessão ativa: Redis (TTL = 2 horas de inatividade)
    Sessão encerrada: PostgreSQL (persistência longa)
    """

    SESSION_TTL_SECONDS = 7200      # 2h de inatividade → encerra
    MAX_HISTORY_IN_REDIS = 20       # Últimas 20 trocas em memória

    async def get_or_create(
        self,
        patient_id: str,
        session_id: Optional[str] = None,
    ) -> NiseSession:
        """
        Retorna sessão existente (se session_id válido e não expirado)
        ou cria nova sessão.
        """
        ...

    async def update(
        self,
        session: NiseSession,
        user_message: str,
        nise_response: str,
    ) -> None:
        """Adiciona troca ao histórico da sessão (Redis)."""
        ...

    async def persist_to_db(self, session: NiseSession) -> None:
        """Persiste sessão encerrada no PostgreSQL (auditoria LGPD)."""
        ...
```

### 3.6 NiseResponseFilter

```python
class NiseResponseFilter:
    """
    Filtra respostas do FLOWISE antes de enviar ao paciente.

    REGRAS DE SEGURANÇA:
    - Nunca confirmar/negar diagnóstico específico
    - Nunca recomendar medicamento específico
    - Sempre incluir disclaimer quando resposta envolve sintomas graves
    - Detectar e bloquear conteúdo inapropriado
    """

    DANGER_PATTERNS = [
        r"tome\s+\d+\s*mg",            # Dosagem específica
        r"você tem\s+\w+",              # Diagnóstico assertivo
        r"cancela?r?\s+medicamento",    # Instrução de parar medicamento
    ]

    ESCALATION_KEYWORDS = [
        "dor no peito", "falta de ar grave", "desmaio",
        "sangramento intenso", "pensamento suicida"
    ]

    async def filter(
        self,
        response: str,
        patient_message: str,
    ) -> FilterResult:
        """
        Retorna FilterResult com:
        - filtered_response: texto (pode ser modificado)
        - flagged: bool (se houve conteúdo problemático)
        - escalation_needed: bool (se precisa acionar equipe)
        - escalation_reason: str (se escalation_needed=True)

        Se escalation_needed → WANDA dispara alerta via AlertHub (EF-W007)
        com prioridade ALTA para equipe de enfermagem.
        """
        ...
```

---

## 4. Persona "Dr. Nise"

A persona é configurada no FLOWISE como System Prompt do flow, mas os princípios são:

```
Você é a Dr. Nise, assistente educacional de saúde do IntelliCare.

Inspirada na Dra. Nise da Silveira (1905-1999), pioneira brasileira
na humanização do cuidado em saúde mental, sua missão é:

- Educar pacientes sobre suas condições de saúde em linguagem acessível
- Orientar sobre hábitos saudáveis, adesão ao tratamento e autocuidado
- Escutar com empatia e validar os sentimentos do paciente
- Nunca diagnosticar, prescrever ou substituir o médico
- Sempre encorajar a conversa com a equipe de saúde

Tom: empático, acolhedor, respeitoso, claro.
Idioma: sempre português brasileiro.
Nível: linguagem simples, evitar jargão médico.

LIMITES ABSOLUTOS:
- "Não sou médica e não posso diagnosticar ou prescrever."
- Se sintoma grave → "Procure atendimento imediato ou ligue 192 (SAMU)."
- Se dúvida de medicamento → "Confirme com seu médico ou farmacêutico."
```

---

## 5. Banco de Dados

```sql
-- Schema: wanda_operacional

CREATE TABLE nise_sessions (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id  VARCHAR(64) NOT NULL,
    session_id  VARCHAR(64) UNIQUE NOT NULL,
    channel     VARCHAR(20) NOT NULL,          -- "portal" | "rocketchat"
    started_at  TIMESTAMPTZ DEFAULT NOW(),
    ended_at    TIMESTAMPTZ,
    message_count INTEGER DEFAULT 0,
    flagged_count INTEGER DEFAULT 0,           -- Quantas filtragens ocorreram
    escalated   BOOLEAN DEFAULT FALSE,         -- Se escalou para equipe
    status      VARCHAR(16) DEFAULT 'ACTIVE'   -- "ACTIVE" | "ENDED" | "ESCALATED"
);

CREATE TABLE nise_messages (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id  UUID REFERENCES wanda_operacional.nise_sessions(id),
    role        VARCHAR(10) NOT NULL,           -- "patient" | "nise"
    content     TEXT NOT NULL,
    flagged     BOOLEAN DEFAULT FALSE,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Dados de mensagem são retidos por 2 anos (LGPD — prontuário eletrônico)
-- Acesso restrito: apenas o próprio paciente e gestor LGPD
CREATE INDEX idx_nise_sessions_patient ON wanda_operacional.nise_sessions(patient_id);
CREATE INDEX idx_nise_messages_session ON wanda_operacional.nise_messages(session_id, created_at);
```

---

## 6. API

| Método | Path | Descrição |
|--------|------|-----------|
| `POST` | `/api/v1/chat/patient` | Envia mensagem para Dr. Nise |
| `GET` | `/api/v1/chat/patient/session/{session_id}` | Histórico da sessão |
| `DELETE` | `/api/v1/chat/patient/session/{session_id}` | Encerra sessão |
| `GET` | `/api/v1/chat/nise/status` | Status do FLOWISE (disponível?) |
| `GET` | `/api/v1/chat/nise/metrics` | Sessões ativas, mensagens hoje |

### Exemplo de requisição

```json
POST /api/v1/chat/patient
{
  "patient_id": "12345",
  "message": "O que é doença renal crônica?",
  "channel": "portal",
  "session_id": null,
  "correlation_id": "uuid-abc-123"
}
```

### Exemplo de resposta

```json
{
  "response": "Olá! Sou a Dr. Nise. A doença renal crônica (DRC) acontece quando os rins perdem gradualmente a capacidade de filtrar o sangue. É importante manter as consultas regulares e seguir as orientações do seu médico. Posso explicar mais sobre como cuidar dos rins no dia a dia. O que você gostaria de saber?",
  "session_id": "sess-xyz-456",
  "disclaimer": "Sou a Dr. Nise, assistente educacional. Não substituo consulta médica.",
  "source": "flowise",
  "latency_ms": 1250,
  "correlation_id": "uuid-abc-123",
  "flagged": false
}
```

---

## 7. Configuração

```bash
# FLOWISE
FLOWISE_URL=http://flowise:3001
FLOWISE_DR_NISE_FLOW_ID=<uuid-do-flow-no-flowise>
FLOWISE_API_KEY=<api-key-se-habilitado>
FLOWISE_TIMEOUT_SECONDS=30

# Comportamento
NISE_SESSION_TTL=7200                   # 2h de inatividade
NISE_MAX_HISTORY=20                     # Mensagens em memória por sessão
NISE_ESCALATION_ENABLED=true           # Acionar equipe em sintomas graves
NISE_FALLBACK_MESSAGE="Olá! Estou temporariamente indisponível. Por favor, entre em contato com sua equipe de saúde pelo Rocket.Chat."
```

---

## 8. Testes

| # | Teste | Tipo |
|---|-------|------|
| T01 | `chat()` com FLOWISE disponível retorna resposta com session_id | Integration |
| T02 | `chat()` com session_id existente continua conversa (histórico) | Integration |
| T03 | `chat()` com FLOWISE offline retorna fallback (não crash) | Integration |
| T04 | `IPSSimplifier.simplify()` não inclui CPF ou nome completo | Unit |
| T05 | `IPSSimplifier.simplify()` inclui condições e alergias | Unit |
| T06 | `NiseResponseFilter` bloqueia dosagem específica ("tome 500mg") | Unit |
| T07 | `NiseResponseFilter` detecta keyword de emergência → escalation_needed=True | Unit |
| T08 | Escalation aciona AlertHub (EF-W007) com prioridade ALTA | Integration |
| T09 | `NiseSessionManager.get_or_create()` cria nova sessão no Redis | Unit |
| T10 | Sessão expira após TTL (2h) → nova sessão criada | Integration |
| T11 | `end_session()` persiste histórico no PostgreSQL | Integration |
| T12 | `GET /api/v1/chat/patient/session/{id}` retorna histórico formatado | API |
| T13 | `GET /api/v1/chat/nise/status` retorna healthy quando FLOWISE OK | API |
| T14 | `GET /api/v1/chat/nise/status` retorna degraded quando FLOWISE offline | API |
| T15 | Disclaimer sempre presente na resposta | Unit |
| T16 | `nise_sessions` e `nise_messages` persistidos corretamente | Integration |
| T17 | Audit log registra interação com correlation_id | Integration |
| T18 | FlowiseClient.health_check() retorna True/False sem exceção | Unit |
| T19 | POST /api/v1/chat/patient sem patient_id retorna 422 | API |
| T20 | Múltiplas sessões simultâneas (3 pacientes) funcionam independentemente | Integration |

**Cobertura mínima:** ≥ 85%

---

## 9. Critérios de Aceitação

- [ ] Chat funcional via `POST /api/v1/chat/patient` em < 3s (P95)
- [ ] Sessões persistidas no Redis (ativas) e PostgreSQL (encerradas)
- [ ] IPSSimplifier respeita mínimo privilégio (sem dados sensíveis desnecessários)
- [ ] Fallback elegante quando FLOWISE offline (mensagem clara, sem crash)
- [ ] ResponseFilter detecta conteúdo perigoso e aciona AlertHub
- [ ] Disclaimer sempre presente em todas as respostas
- [ ] Histórico de sessão recuperável via API
- [ ] 20+ testes passando
- [ ] Cobertura ≥ 85%

---

## 10. Estimativa de Complexidade

- **Arquivos novos**: ~9 (gateway, flowise_client, simplifier, session_manager, filter, audit, schemas, endpoints, tests)
- **Arquivos modificados**: ~3 (api/app.py, config.py, docker-compose.yml)
- **Linhas estimadas**: ~1.200
- **Testes novos**: ~20

---

## 11. Nota sobre Privacidade (LGPD)

As conversas com a Dr. Nise são registros de saúde (Art. 11 LGPD — dados sensíveis):

- Consentimento do paciente obtido no cadastro do Portal
- Acesso ao histórico restrito ao próprio paciente + responsável LGPD
- Retenção de 2 anos (resolução CFM 2.217/2018 — prontuário eletrônico)
- Direito de exclusão: implementar `DELETE /api/v1/chat/patient/{id}/all-data`
- Dados não compartilhados com FLOWISE além do contexto mínimo (IPSSimplifier)

---

## 12. Homenagem

> **Dra. Nise da Silveira (1905–1999)**
> Psiquiatra brasileira alagoana, pioneira na humanização do tratamento em saúde mental. Opôs-se à lobotomia e ao eletrochoque, substituindo a violência pelo amor, pela arte e pelo cuidado. Fundou a Casa das Palmeiras e o Museu de Imagens do Inconsciente. Sua filosofia: "A loucura não é algo a ser curado, mas acolhido."
>
> A Dr. Nise do IntelliCare carrega seu legado: acolher o paciente com empatia, educá-lo com clareza, respeitá-lo como sujeito do próprio cuidado.
