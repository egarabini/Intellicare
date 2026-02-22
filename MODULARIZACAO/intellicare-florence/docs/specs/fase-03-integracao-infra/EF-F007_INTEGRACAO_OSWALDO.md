# EF-F007 — Integracao Oswaldo (Florence Consome Estadiamento)

> Implementar OswaldoClient na Florence para contextualizar interpretacoes laboratoriais com o estadiamento de doencas cronicas do Oswaldo — ajustando limiares, priorizando exames e gerando narrativas mais precisas para pacientes CKD, DM2 e HAS.

## 1. Objetivo

Florence hoje interpreta cada exame de forma generica, sem saber se o paciente tem CKD G4 ou DM2 descontrolada. Com o estadiamento do Oswaldo:

- **Creatinina 2.1 mg/dL SEM contexto**: "Creatinina elevada"
- **Creatinina 2.1 mg/dL COM CKD G3b do Oswaldo**: "Creatinina 2.1 em paciente CKD G3b — TFG estimada compativel com estadio. Avaliar progressao comparando com historico. ACR prioritario para avaliacao de proteinuria."

A Florence tambem enriquece o Oswaldo (EF-O007, ja especificado) com dados laboratoriais mais detalhados. Esta spec cobre o sentido inverso: Florence consome Oswaldo.

## 2. Justificativa

- Interpretacao de exames sem contexto clinico gera recomendacoes genericas — de baixo valor
- DRC G4 tem limiares diferentes: potassio > 5.0 e mais preocupante do que em paciente sem CKD
- HbA1c em DM2 POOR (> 10%) tem urgencia maior do que em paciente sem DM2
- Oswaldo ja tem `/api/v1/analyze` funcional — Florence pode consumir facilmente

## 3. Escopo

### 3.1 OswaldoClient (na Florence)

```python
class OswaldoClient:
    """
    Cliente HTTP para consultar estadiamento do Oswaldo.
    Porta 8001 — POST /api/v1/analyze.

    Cache: 30min por patient_id (estadiamento nao muda em minutos).
    Graceful degradation: se Oswaldo indisponivel, Florence interpreta sem contexto.
    Timeout: 10s.
    """

    async def get_patient_staging(
        self,
        patient_id: str,
    ) -> Optional[OswaldoContext]:
        """
        Consulta estadiamento atual de todas as doencas do paciente.

        Request para Oswaldo:
        {
            "query": "Qual o estadiamento atual do paciente?",
            "patient_id": patient_id,
            "capability": "chronic_disease_staging",
            "context": {"requesting_agent": "florence"},
        }

        Retorna: OswaldoContext ou None se Oswaldo indisponivel.
        """

    async def get_ckd_stage(
        self,
        patient_id: str,
    ) -> Optional[str]:
        """
        Retorna apenas o estadio CKD do paciente.
        Ex: "G3b" | "G4" | None
        """

    async def get_dm2_control(
        self,
        patient_id: str,
    ) -> Optional[str]:
        """
        Retorna controle glicemico DM2.
        Ex: "CONTROLLED" | "SUBOPTIMAL" | "POOR" | "VERY_POOR" | None
        """

    async def is_available(self) -> bool:
        """Verifica disponibilidade do Oswaldo."""


@dataclass
class OswaldoContext:
    """
    Contexto clinico fornecido pelo Oswaldo para contextualizar analise da Florence.
    """
    patient_id: str
    retrieved_at: str

    # Estadiamentos por doenca
    ckd_stage: Optional[str]         # "G1" | "G2" | "G3a" | "G3b" | "G4" | "G5"
    dm2_control: Optional[str]       # "CONTROLLED" | "SUBOPTIMAL" | "POOR" | "VERY_POOR"
    has_stage: Optional[str]         # "OPTIMAL" | "NORMAL" | "HIGH_NORMAL" | "GRADE1" ...
    active_alerts: list[str]         # Alertas ativos do Oswaldo

    # Flags calculadas para uso interno da Florence
    is_high_risk_ckd: bool = False   # G3b+ (limiares ajustados)
    is_dm2_uncontrolled: bool = False  # POOR ou VERY_POOR
    has_cardiovascular_risk: bool = False  # Score Framingham alto
```

### 3.2 ContextualLabInterpreter

```python
class ContextualLabInterpreter:
    """
    Versao contextualizada do LabInterpreter.
    Ajusta limiares e mensagens baseado no OswaldoContext.

    Herda de LabInterpreter — adiciona contextualizacao sem quebrar interface existente.
    """

    CONTEXT_ADJUSTMENTS = {
        # CKD G3b+ — potassio mais preocupante
        ("potassium", "ckd_g3b_plus"): ContextAdjustment(
            lower_threshold_by=0.5,    # alert em K > 5.0 em vez de 5.5
            message_prefix="Em paciente CKD G3b: ",
            add_recommendation="Risco aumentado de hipercalemia. Monitorar mais frequentemente.",
        ),
        # DM2 descontrolado — HbA1c context
        ("hba1c", "dm2_poor"): ContextAdjustment(
            message_prefix="DM2 com controle inadequado: ",
            add_recommendation="Meta HbA1c < 7% — intensificar terapia hipoglicemiante.",
        ),
        # CKD + eGFR — ajuste de estadiamento
        ("egfr", "ckd_g4"): ContextAdjustment(
            message_prefix="DRC G4 — TFG em nivel de preparo para TRS: ",
            add_recommendation="TFG < 30 — encaminhar para nefrologista para planejamento de TRS (dialise).",
        ),
        # ACR em DRC — proteinuria
        ("albumin_creatinine_ratio", "any_ckd"): ContextAdjustment(
            message_prefix="Proteinuria em paciente CKD: ",
            add_recommendation="ACR > 30 com CKD — KDIGO indica IECA/BRA para nefroproteçao.",
        ),
    }

    def interpret_with_context(
        self,
        lab_id: str,
        value: float,
        oswaldo_context: OswaldoContext,
    ) -> LabInterpretation:
        """
        Interpreta exame com ajuste baseado no contexto do Oswaldo.
        """
```

### 3.3 Integracao no ClinicalAnalyzer

```python
class ClinicalAnalyzer:
    """
    Versao com suporte a contexto do Oswaldo.
    """

    async def analyze_labs(
        self,
        patient_id: str,
        lab_results: dict,
        use_oswaldo_context: bool = True,    # NOVO
        ...
    ) -> ClinicalAnalysis:
        """
        1. Se use_oswaldo_context=True e patient_id valido:
           - Consulta OswaldoClient (com cache)
           - Usa ContextualLabInterpreter em vez de LabInterpreter padrao
        2. Se Oswaldo indisponivel: usa LabInterpreter padrao (graceful degradation)
        3. Analise normal + inclui oswaldo_context no resultado se disponivel
        """
```

### 3.4 Endpoints Atualizados

```python
# O response de /api/v1/analyze (Wanda) e /api/v1/analyze-labs agora inclui:
{
    "result": {
        ...,
        "oswaldo_context": {
            "ckd_stage": "G3b",
            "dm2_control": "POOR",
            "context_influenced": ["potassium", "hba1c", "egfr"],  # Quais exames tiveram limiares ajustados
        },
    }
}

# NOVO endpoint de contexto:
# GET /api/v1/patients/{patient_id}/clinical-context
# Consolida: Oswaldo (estadiamento) + Florence (historico de labs)
# Retorna: {oswaldo_context, latest_labs, lab_trends}
# Util para Wanda montar contexto completo do paciente
```

### 3.5 Configuracao

```env
FLORENCE_OSWALDO_URL=http://oswaldo:8001
FLORENCE_OSWALDO_ENABLED=true
FLORENCE_OSWALDO_TIMEOUT=10
FLORENCE_OSWALDO_CACHE_TTL=1800     # 30 min
```

## 4. Testes

- OswaldoClient.get_patient_staging: dados retornados, Oswaldo down (2 testes)
- OswaldoClient.is_available: up, down (2 testes)
- ContextualLabInterpreter: potassio CKD G3b+ ajustado, HbA1c DM2 POOR contextualizado (2 testes)
- ClinicalAnalyzer com context: usa ContextualLabInterpreter, fallback sem Oswaldo (2 testes)
- GET /patients/{id}/clinical-context: retorna consolidado Oswaldo + labs (2 testes)
- Cache: segunda consulta usa cache (1 teste)
- **Total**: 12+ testes novos

## 5. Criterios de Aceitacao

- [ ] `OswaldoClient` com graceful degradation (Florence funciona sem Oswaldo)
- [ ] `ContextualLabInterpreter` ajusta limiares para CKD G3b+ (potassio, eGFR, ACR)
- [ ] `ContextualLabInterpreter` contextualiza HbA1c para DM2 descontrolado
- [ ] Response da analise inclui `oswaldo_context` quando disponivel
- [ ] Cache de 30min por patient_id para consultas ao Oswaldo
- [ ] Endpoint `/patients/{id}/clinical-context` consolida ambos os agentes
- [ ] 198 testes existentes continuam passando
- [ ] 12+ testes novos

## 6. Estimativa de Complexidade

- **Arquivos novos**: `florence/integrations/oswaldo.py` (OswaldoClient + OswaldoContext), `florence/engine/contextual_interpreter.py`
- **Arquivos modificados**: `florence/engine/clinical_analyzer.py` (integrar contexto), `florence/api/app.py` (endpoint clinical-context + response update), `florence/config.py`
- **Linhas estimadas**: ~320
- **Testes novos**: ~12
