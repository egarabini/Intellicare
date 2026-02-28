# EF-010 — Integracao com Florence e Oswaldo

> Consumo de dados clinicos (Florence) e de doencas cronicas (Oswaldo) para enriquecer o cuidado do paciente.

## 1. Objetivo

Integrar a Geralda com Florence (inteligencia clinica) e Oswaldo (motor de doencas cronicas) para:
- Consumir analises clinicas da Florence para personalizar cuidados
- Receber alertas de piora/melhora do Oswaldo para ajustar planos
- Usar dados laboratoriais da Florence para educacao contextualizada
- Usar estagiamento de doencas do Oswaldo para trilhas adequadas
- Enriquecer resumos de paciente com dados multi-agente

## 2. Justificativa

- **Contexto clinico**: Geralda precisa de dados clinicos para gerar orientacoes corretas
- **Alertas proativos**: Mudancas clinicas devem ajustar planos automaticamente
- **Educacao contextual**: Material educativo deve refletir o estado real do paciente
- **Adesao informada**: Monitorar adesao com contexto de gravidade clinica
- **Resumos completos**: Paciente recebe visao integrada do seu estado

## 3. Escopo

### 3.1 Dados Consumidos da Florence

Florence e o agente de **inteligencia clinica profunda** com RAG e analise laboratorial.

| Endpoint Florence | Dados | Uso na Geralda |
|-------------------|-------|----------------|
| `GET /api/v1/analyze` | Analise clinica | Contexto para plano de cuidado |
| `GET /api/v1/labs/patient/{id}` | Resultados laboratoriais | Educacao sobre exames, alertas |
| `GET /api/v1/ips/{patient_id}` | IPS (resumo do paciente) | Contexto completo para LLM |
| `GET /api/v1/protocols/search` | Protocolos clinicos (RAG) | Base para protocolos institucionais |

#### Cenarios de Uso

**1. Resultado de exame disponivel**
```
Florence emite: clinical.exam_result
    │
    ▼
Geralda recebe evento (EF-006)
    │
    ├─ Enriquece com dados do paciente
    ├─ Identifica contexto (EF-007)
    │     └─ C82 (Assistencia IA ao Paciente)
    ├─ Executa protocolo (EF-008)
    │     ├─ Gera material educativo sobre o exame (EF-005)
    │     ├─ Simplifica resultado em linguagem acessivel (EF-004)
    │     └─ Envia ao paciente via canal preferido
    └─ Registra evidencia
```

**2. Resumo clinico para pre-consulta**
```
Geralda precisa de resumo clinico para pre-consulta (EF-013)
    │
    ▼
Via Wanda, solicita a Florence:
    POST wanda/api/v1/query
    {
        "queries": [
            {"agent": "florence", "capability": "clinical_analysis",
             "query": "resumo clinico do paciente nos ultimos 90 dias"}
        ]
    }
    │
    ▼
Florence retorna:
    - Diagnosticos ativos
    - Medicamentos atuais
    - Ultimos exames relevantes
    - Alertas clinicos pendentes
    │
    ▼
Geralda gera resumo simplificado para o paciente levar a consulta
```

### 3.2 Dados Consumidos do Oswaldo

Oswaldo e o motor de **doencas cronicas** (DRC, DM2, HAS).

| Endpoint Oswaldo | Dados | Uso na Geralda |
|-------------------|-------|----------------|
| `GET /api/v1/analyze` | Analise de doenca cronica | Estagiamento, risco |
| `GET /api/v1/staging/{patient_id}` | Estagiamento DRC/DM2/HAS | Trilha educativa, alertas |
| `GET /api/v1/risk/{patient_id}` | Score de risco | Prioridade de acompanhamento |
| `GET /api/v1/progression/{patient_id}` | Progressao da doenca | Ajuste de plano de cuidado |

#### Cenarios de Uso

**1. Piora de condicao cronica**
```
Oswaldo emite: clinical.condition_worsened
    payload: {
        "condition": "N18",
        "previous_stage": "3a",
        "current_stage": "3b",
        "risk_delta": +0.15
    }
    │
    ▼
Geralda recebe evento (EF-006)
    │
    ├─ Contexto C51 ativado (Triagem de Risco)
    ├─ Protocolo P-C51-TRIAGEM-V1:
    │     ├─ step-1: Notificar equipe via Rocket.Chat (URGENTE)
    │     ├─ step-2: Ajustar plano de cuidado (aumentar frequencia monitoramento)
    │     ├─ step-3: Gerar material educativo sobre novo estagio
    │     ├─ step-4: Agendar teleconsulta com nefrologista
    │     └─ step-5: Atualizar trilha educativa
    └─ Registra evidencia FHIR
```

**2. Melhora de condicao**
```
Oswaldo emite: clinical.condition_improved
    │
    ▼
Geralda:
    ├─ Envia mensagem positiva ao paciente
    ├─ Ajusta frequencia de lembretes (reduz)
    └─ Gera material motivacional
```

### 3.3 Clientes HTTP para Agentes

```python
class FlorenceClient:
    """Cliente HTTP para comunicacao com Florence."""

    def __init__(self, florence_url: str, timeout: int = 30):
        self._url = florence_url  # ex: "http://florence:8002"
        self._timeout = timeout

    async def get_patient_ips(self, patient_id: str) -> dict:
        """
        Busca IPS (International Patient Summary) do paciente.

        GET {florence_url}/api/v1/ips/{patient_id}

        Returns:
            IPS FHIR Bundle com condicoes, medicamentos, alergias, etc.
        """

    async def get_lab_results(
        self, patient_id: str, last_n: int = 5
    ) -> list[dict]:
        """
        Busca ultimos resultados laboratoriais.

        GET {florence_url}/api/v1/labs/patient/{patient_id}?limit={last_n}
        """

    async def analyze(
        self, patient_id: str, query: str
    ) -> dict:
        """
        Solicita analise clinica.

        POST {florence_url}/api/v1/analyze
        {"patient_id": "...", "query": "..."}
        """

    async def search_protocols(
        self, condition: str, topic: str
    ) -> list[dict]:
        """
        Busca protocolos clinicos via RAG.

        GET {florence_url}/api/v1/protocols/search?q={condition}+{topic}
        """


class OswaldoClient:
    """Cliente HTTP para comunicacao com Oswaldo."""

    def __init__(self, oswaldo_url: str, timeout: int = 30):
        self._url = oswaldo_url  # ex: "http://oswaldo:8001"
        self._timeout = timeout

    async def get_staging(self, patient_id: str) -> dict:
        """
        Busca estagiamento de doencas cronicas.

        GET {oswaldo_url}/api/v1/staging/{patient_id}

        Returns:
            {
                "conditions": [
                    {"code": "N18", "name": "DRC", "stage": "3a", "gfr": 45.2},
                    {"code": "E11", "name": "DM2", "hba1c": 7.1, "control": "regular"},
                    {"code": "I10", "name": "HAS", "bp_avg": "140/90", "control": "ruim"},
                ],
                "overall_risk": "medio-alto",
            }
        """

    async def get_risk_score(self, patient_id: str) -> dict:
        """
        Busca score de risco do paciente.

        GET {oswaldo_url}/api/v1/risk/{patient_id}
        """

    async def get_progression(self, patient_id: str) -> dict:
        """
        Busca historico de progressao da doenca.

        GET {oswaldo_url}/api/v1/progression/{patient_id}

        Returns:
            Timeline de mudancas de estagio nos ultimos 12 meses.
        """

    async def analyze(
        self, patient_id: str, query: str
    ) -> dict:
        """
        Solicita analise de doenca cronica.

        POST {oswaldo_url}/api/v1/analyze
        """
```

### 3.4 Servico de Dados Agregados

```python
class PatientDataAggregator:
    """Agrega dados de multiplos agentes para contexto completo."""

    def __init__(
        self,
        florence_client: FlorenceClient,
        oswaldo_client: OswaldoClient,
        wanda_notifier: WandaNotifier,
    ):
        ...

    async def get_full_context(
        self, patient_id: str
    ) -> PatientFullContext:
        """
        Agrega dados de Florence + Oswaldo + Geralda interna.

        Chamadas paralelas:
        - Florence: IPS + ultimos labs
        - Oswaldo: staging + risk

        Combina com dados internos:
        - Care plans ativos
        - Adesao atual
        - Estado da jornada

        Returns:
            PatientFullContext com visao 360 graus
        """

    async def generate_patient_summary(
        self,
        patient_id: str,
        purpose: str,  # "pre_consultation", "discharge", "follow_up"
        reading_level: str = "basico",
    ) -> str:
        """
        Gera resumo do paciente para um proposito especifico.

        Usa LLM (Ollama) para sintetizar dados de multiplos agentes
        em texto acessivel ao paciente ou profissional.
        """
```

### 3.5 Mapeamento de Eventos Inter-Agentes

| Evento de Origem | Agente Emissor | Acao na Geralda |
|------------------|---------------|-----------------|
| `clinical.exam_result` | Florence | Gerar material educativo sobre exame |
| `clinical.condition_worsened` | Oswaldo | Ajustar plano + notificar equipe |
| `clinical.condition_improved` | Oswaldo | Mensagem positiva + ajustar frequencia |
| `clinical.medication_changed` | Florence/FHIR | Atualizar lembretes + educacao |
| `clinical.vital_sign_alert` | Florence | Triagem de risco + protocolo C51 |
| `clinical.admission` | FHIR/Hospital | Iniciar jornada (C1) |
| `clinical.discharge` | FHIR/Hospital | Alta clinica (C41) |

### 3.6 Modo Direto vs Via Wanda

```
Modo 1: Via Wanda (PADRAO — recomendado)
    Geralda → Wanda → Florence/Oswaldo → Wanda → Geralda
    Pros: Auditoria centralizada, IPS-First, seguranca
    Contras: Latencia extra (~50-100ms)

Modo 2: Direto (quando Wanda indisponivel ou para dados simples)
    Geralda → Florence/Oswaldo (HTTP direto)
    Pros: Menor latencia
    Contras: Sem auditoria centralizada, sem IPS-First da Wanda

Regra: Usar modo direto APENAS quando:
    1. Wanda esta indisponivel (graceful degradation)
    2. Dado e somente leitura e nao-sensivel (ex: staging generico)
    3. Operacao e interna e nao envolve decisao clinica
```

### 3.7 Configuracao

```env
# Florence
INTELLICARE_FLORENCE_URL=http://florence:8002
INTELLICARE_FLORENCE_TIMEOUT=30
INTELLICARE_FLORENCE_ENABLED=true

# Oswaldo
INTELLICARE_OSWALDO_URL=http://oswaldo:8001
INTELLICARE_OSWALDO_TIMEOUT=30
INTELLICARE_OSWALDO_ENABLED=true

# Modo de comunicacao
INTELLICARE_PREFER_WANDA_ROUTING=true   # true = via Wanda, false = direto
```

### 3.8 Arquitetura de Integracao

```
geralda/integrations/
  __init__.py
  florence_client.py        # Cliente HTTP Florence
  oswaldo_client.py         # Cliente HTTP Oswaldo
  patient_aggregator.py     # Agregador de dados multi-agente
  event_handlers/
    __init__.py
    clinical_events.py      # Handler de eventos clinicos
    chronic_events.py       # Handler de eventos de doencas cronicas
```

## 4. Testes

- FlorenceClient: IPS, labs, analyze, protocols, timeout (6 testes)
- OswaldoClient: staging, risk, progression, analyze, timeout (6 testes)
- PatientDataAggregator: full context, summary, falha parcial (6 testes)
- ClinicalEventHandler: exam_result, medication_changed, admission (5 testes)
- ChronicEventHandler: worsened, improved, staging_change (5 testes)
- Graceful degradation: Florence down, Oswaldo down, ambos down (3 testes)
- Via Wanda vs direto: routing decision (3 testes)
- **Total**: 34+ testes

## 5. Criterios de Aceitacao

- [ ] FlorenceClient funcional (IPS, labs, analyze, protocols)
- [ ] OswaldoClient funcional (staging, risk, progression, analyze)
- [ ] PatientDataAggregator com chamadas paralelas
- [ ] Handlers para eventos clinicos e de doencas cronicas
- [ ] Resumo multi-agente gerado via LLM
- [ ] Modo via Wanda (padrao) e direto (fallback)
- [ ] Graceful degradation quando agentes indisponiveis
- [ ] 34+ testes
- [ ] Cobertura >= 85%

## 6. Estimativa de Complexidade

- **Arquivos novos**: ~8
- **Arquivos modificados**: ~3 (config, event_pipeline, docker)
- **Linhas estimadas**: ~1.400
- **Testes novos**: ~34
