# EF-017 — Canal Equipe-Paciente com IA

> Chat bidirecional entre equipe de saude e paciente mediado por IA, com escalacao inteligente.

## 1. Objetivo

Implementar o canal de comunicacao bidirecional equipe-paciente, responsavel por:
- Manter sala Matrix/Element dedicada por paciente
- Processar mensagens do paciente via LLM (Geralda como intermediaria)
- Responder autonomamente perguntas dentro do escopo da Geralda
- Escalar para profissional quando necessario (fora do escopo, urgente)
- Registrar toda comunicacao para auditoria (LGPD)
- Permitir profissional enviar mensagens diretamente ao paciente

## 2. Justificativa

- **Acesso facilitado**: Paciente tem canal direto com sua equipe de saude
- **Autonomia da IA**: Perguntas simples respondidas sem onerar profissional
- **Seguranca**: IA detecta urgencia e escala imediatamente
- **Vinculo**: Canal fortalece relacionamento equipe-paciente
- **Registro**: Toda comunicacao auditavel para continuidade do cuidado

## 3. Escopo

### 3.1 Arquitetura do Canal

```
Paciente (Element/WhatsApp)
        │
        ▼ mensagem
┌───────────────────┐
│   Bot Geralda     │  ← processa primeiro
│   (Matrix)        │
└────────┬──────────┘
         │
         ├─ Escopo Geralda? ────────► Responde autonomamente
         │   (lembrete, educacao,       via LLM (EF-003)
         │    duvida sobre plano)
         │
         ├─ Escopo clinico           ► Encaminha para Florence/Oswaldo
         │   (resultado exame,          via Wanda, responde com
         │    pergunta sobre doenca)    referencia ao profissional
         │
         ├─ Urgencia detectada       ► Escala imediato para equipe
         │   (dor forte, sintoma         Notifica Rocket.Chat
         │    de alerta)                  Instrui paciente (pronto-socorro?)
         │
         └─ Fora do escopo          ► Informa limitacao e
             (questao juridica,          redireciona para humano
              diagnostico novo)
```

### 3.2 Sala Dedicada por Paciente

```python
class PatientRoomManager:
    """Gerencia salas Matrix dedicadas por paciente."""

    async def create_patient_room(
        self,
        patient_id: str,
        patient_name: str,
        unit_id: str,
        professional_ids: list[str],
    ) -> PatientRoom:
        """
        Cria ou recupera sala Matrix dedicada.

        Configuracoes:
        - Nome: f"BemCuidar | {patient_name}"
        - Visibilidade: privada
        - Convites: bot Geralda + profissionais da equipe
        - Opcoes: desabilitar convites externos, habilitar leitura de historico

        Retorna room_id para armazenamento.
        """

    async def get_patient_room(
        self,
        patient_id: str,
    ) -> Optional[PatientRoom]:
        """
        Busca sala existente do paciente.

        Consulta tabela patient_rooms (intellicare-comunicacao).
        """

    async def invite_professional(
        self,
        patient_id: str,
        professional_id: str,
    ) -> None:
        """
        Convida profissional para a sala do paciente.

        Ex: medico solicitou ver historico de mensagens.
        """

    async def archive_room(
        self,
        patient_id: str,
        reason: str,
    ) -> None:
        """
        Arquiva sala ao encerrar jornada (E7).

        Historico mantido para auditoria (5 anos).
        Sala torna-se somente leitura.
        """
```

### 3.3 Processador de Mensagens

```python
class PatientMessageProcessor:
    """Processa mensagens do paciente com IA."""

    def __init__(
        self,
        llm_agent,              # GeraldaAgent (EF-003)
        urgency_detector,       # Deteccao de urgencia
        scope_classifier,       # Classificacao de escopo
        escalation_handler,     # Escalacao para equipe
        context_manager,        # ContextManager (EF-007)
        notification_engine,    # NotificationEngine (EF-015)
    ):
        ...

    async def process(
        self,
        patient_id: str,
        message: str,
        room_id: str,
        channel: str = "matrix",
    ) -> ProcessingResult:
        """
        Processa mensagem do paciente.

        Fluxo:
        1. Detectar urgencia (EF-011 detector)
        2. Se urgente → escalar imediatamente
        3. Classificar escopo da mensagem
        4. Carregar contexto da jornada (EF-007)
        5. Processar com LLM (EF-003) + ferramentas
        6. Gerar resposta
        7. Enviar resposta ao paciente
        8. Registrar no audit log
        9. Emitir evento digital.message_processed
        """

    async def classify_scope(
        self,
        message: str,
        patient_context: dict,
    ) -> MessageScope:
        """
        Classifica o escopo da mensagem.

        Escopos:
        - GERALDA: Pode responder autonomamente
          Ex: "Que horas tomo Losartana?"
              "Nao entendi meu plano"
              "Fiz o exercicio"
              "Quando e minha consulta?"

        - CLINICAL: Precisa de dado clinico (consulta Florence/Oswaldo)
          Ex: "O que significa creatinina 1.8?"
              "Minha pressao esta controlada?"
              "Estou no estagio certo da DRC?"

        - OUT_OF_SCOPE: Fora do dominio de saude
          Ex: "Voce pode me ajudar com impostos?"
              "O que voce acha do governo?"

        - EMERGENCY: Possivel emergencia
          Ex: "Estou com dor no peito"
              "Sinto falta de ar"
              "Minhas pernas inchou muito"
        """
```

### 3.4 Respostas Autonomas da Geralda

```python
# Exemplos de interacoes autonomas

# Consulta sobre plano de cuidado
PACIENTE: "Nao lembro o que tenho que fazer hoje"
GERALDA:  "Oi Joao! Hoje voce tem 3 atividades:
           ✅ Losartana 50mg — 08:00 (ja passou a hora)
           ⏰ Metformina 850mg — 12:00 (em 2 horas)
           🚶 Caminhada 20min — qualquer horario

           Voce tomou a Losartana de manha?"

# Confirmacao de medicamento
PACIENTE: "Tomei todos os remedios"
GERALDA:  "Otimo Joao! Ja marquei como feito 👍
           Sua adesao hoje esta em 100%.
           Lembre-se: proximo remedio e a Metformina
           no almoco, as 12:00."

# Pergunta sobre doenca (CLINICAL — busca Oswaldo)
PACIENTE: "Doutor falou que minha TFG e 45. E bom ou ruim?"
GERALDA:  "Essa e uma pergunta importante! Deixa eu
           verificar seus dados e te explicar...
           [consulta Oswaldo via Wanda]
           TFG de 45 indica DRC no estagio 3a, que e
           um estagio moderado. Nao e uma emergencia,
           mas precisa de cuidado continuo — exatamente
           o que voce esta fazendo!
           Quer que eu te envie um material explicando
           melhor o que e TFG?"

# Urgencia detectada
PACIENTE: "Estou com muita falta de ar e meu pe inchou muito"
GERALDA:  "Joao, esses sintomas precisam de atencao imediata!
           ⚠️ VAI AO PRONTO-SOCORRO AGORA.
           Diga que tem DRC e HAS.
           Leve sua lista de medicamentos.

           Ja avisei sua equipe de saude.
           Consegue ir ao pronto-socorro?"
           [Notifica equipe no Rocket.Chat: URGENTE]
```

### 3.5 Interface para Profissional

```python
class ProfessionalMessageInterface:
    """Interface para profissional se comunicar com paciente."""

    async def send_to_patient(
        self,
        professional_id: str,
        patient_id: str,
        message: str,
        message_type: str = "direct",     # direct, instruction, follow_up
    ) -> None:
        """
        Profissional envia mensagem diretamente ao paciente.

        Envia para a sala Matrix do paciente.
        Registra como comunicacao do profissional (nao da IA).
        """

    async def broadcast_to_cohort(
        self,
        professional_id: str,
        unit_id: str,
        patient_ids: list[str],
        message_template: str,
        condition_filter: Optional[str] = None,
    ) -> BroadcastResult:
        """
        Envia mensagem para grupo de pacientes.

        Ex: "Informamos que a unidade estara fechada no feriado..."
        Personaliza com nome de cada paciente.
        Respeita LGPD e limites diarios.
        """

    async def get_patient_conversation(
        self,
        professional_id: str,
        patient_id: str,
        last_n_messages: int = 50,
    ) -> list[Message]:
        """
        Profissional visualiza historico de mensagens.

        Inclui mensagens da IA e do paciente.
        Marca mensagens de IA vs mensagens diretas.
        """

    async def take_over(
        self,
        professional_id: str,
        patient_id: str,
        duration_minutes: int = 30,
    ) -> None:
        """
        Profissional assume conversa temporariamente.

        Durante o take_over:
        - Bot Geralda recebe mensagens mas NAO responde automaticamente
        - Mensagens do paciente aparecem no Rocket.Chat do profissional
        - Profissional responde diretamente

        Apos duration_minutes, bot retoma automaticamente.
        """
```

### 3.6 Auditoria de Comunicacoes

```python
class CommunicationAuditLogger:
    """Registra todas as comunicacoes para auditoria LGPD."""

    async def log_patient_message(
        self,
        patient_id: str,
        room_id: str,
        message: str,
        processed: bool,
        scope: str,
        escalated: bool,
    ) -> None:
        """Registra mensagem recebida do paciente."""

    async def log_geralda_response(
        self,
        patient_id: str,
        room_id: str,
        response: str,
        response_type: str,     # autonomous, escalated, professional
        llm_used: bool,
    ) -> None:
        """Registra resposta enviada ao paciente."""

    async def export_audit_fhir(
        self,
        patient_id: str,
        start_date: date,
        end_date: date,
    ) -> list[dict]:
        """
        Exporta historico em formato FHIR Communication.

        Usado para exportacao LGPD (direito de acesso)
        e para integracao com prontuario.
        """
```

### 3.7 Tabelas

```sql
-- Conversas (vinculo paciente-sala)
CREATE TABLE patient_channels (
    id BIGSERIAL PRIMARY KEY,
    patient_id VARCHAR(64) UNIQUE NOT NULL,
    matrix_room_id VARCHAR(200),
    rocketchat_room_id VARCHAR(200),
    channel_status VARCHAR(20) DEFAULT 'active',  -- active, archived
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    archived_at TIMESTAMPTZ
);

CREATE INDEX idx_channels_patient ON patient_channels(patient_id);

-- Mensagens (log auditavel)
CREATE TABLE channel_messages (
    id BIGSERIAL PRIMARY KEY,
    message_id UUID UNIQUE NOT NULL,
    patient_id VARCHAR(64) NOT NULL,
    sender_type VARCHAR(20) NOT NULL,    -- patient, geralda_ai, professional
    sender_id VARCHAR(100),
    message_text TEXT NOT NULL,
    message_hash VARCHAR(64),            -- SHA256 para integridade
    channel VARCHAR(50),
    scope_classified VARCHAR(20),        -- geralda, clinical, out_of_scope, emergency
    escalated BOOLEAN DEFAULT FALSE,
    escalated_to VARCHAR(100),
    llm_used BOOLEAN DEFAULT FALSE,
    tools_called JSONB DEFAULT '[]',
    response_time_ms INTEGER,
    sent_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_messages_patient ON channel_messages(patient_id);
CREATE INDEX idx_messages_date ON channel_messages(sent_at);
CREATE INDEX idx_messages_scope ON channel_messages(scope_classified);
CREATE INDEX idx_messages_emergency ON channel_messages(patient_id, scope_classified)
    WHERE scope_classified = 'emergency';

-- Take-over de profissional
CREATE TABLE professional_takeovers (
    id BIGSERIAL PRIMARY KEY,
    patient_id VARCHAR(64) NOT NULL,
    professional_id VARCHAR(100) NOT NULL,
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL,
    ended_at TIMESTAMPTZ,
    reason TEXT
);

CREATE INDEX idx_takeovers_patient ON professional_takeovers(patient_id);
CREATE INDEX idx_takeovers_active ON professional_takeovers(patient_id, expires_at)
    WHERE ended_at IS NULL;
```

### 3.8 Endpoints

| Metodo | Path | Descricao |
|--------|------|-----------|
| POST | `/api/v1/channel/patient` | Criar canal do paciente |
| GET | `/api/v1/channel/{patient_id}` | Info do canal |
| POST | `/api/v1/channel/{patient_id}/send` | Profissional envia mensagem |
| POST | `/api/v1/channel/broadcast` | Broadcast para grupo |
| GET | `/api/v1/channel/{patient_id}/messages` | Historico |
| POST | `/api/v1/channel/{patient_id}/takeover` | Profissional assume conversa |
| DELETE | `/api/v1/channel/{patient_id}/takeover` | Encerra take-over |
| GET | `/api/v1/channel/{patient_id}/audit` | Auditoria LGPD |
| GET | `/api/v1/channel/stats` | Metricas do canal |

### 3.9 Regras de Privacidade (LGPD)

1. **Consentimento explicito** para monitoramento de mensagens pela IA
2. **Hash de integridade** de cada mensagem (SHA256)
3. **Retencao**: Mensagens mantidas por 5 anos
4. **Direito de acesso**: Exportacao FHIR Communication disponivel
5. **Portabilidade**: Historico exportavel em formato padrao
6. **Anonimizacao**: Ao encerrar jornada, dados anonimizados para analytics
7. **Professional take-over**: Paciente notificado quando profissional assume

## 4. Testes

- PatientRoomManager: create, get, invite, archive (5 testes)
- PatientMessageProcessor: escopo, urgencia, resposta, escalacao (10 testes)
- ScopeClassifier: geralda, clinical, out_of_scope, emergency (6 testes)
- ProfessionalMessageInterface: send, broadcast, takeover (6 testes)
- CommunicationAuditLogger: log, export FHIR (4 testes)
- Privacidade: hash, retencao, anonimizacao (3 testes)
- Endpoints: todos 9 (6 testes)
- Integracao: mensagem urgente → resposta → escalacao → equipe (3 testes)
- **Total**: 43+ testes

## 5. Criterios de Aceitacao

- [ ] Sala Matrix criada automaticamente para cada paciente
- [ ] Bot Geralda responde mensagens em linguagem acessivel
- [ ] 4 escopos de classificacao (geralda, clinical, out_of_scope, emergency)
- [ ] Escalacao imediata para urgencias com instrucao ao paciente
- [ ] Profissional pode enviar mensagens diretamente
- [ ] Broadcast para grupo de pacientes
- [ ] Take-over de profissional (30min padrao)
- [ ] Log auditavel com hash de integridade
- [ ] Exportacao FHIR Communication para LGPD
- [ ] Anonimizacao ao encerrar jornada
- [ ] 9 endpoints funcionais
- [ ] 43+ testes
- [ ] Cobertura >= 85%

## 6. Estimativa de Complexidade

- **Arquivos novos**: ~9
- **Arquivos modificados**: ~5 (api, llm_agent, context_manager, notification_engine, docker)
- **Linhas estimadas**: ~2.000
- **Testes novos**: ~43
