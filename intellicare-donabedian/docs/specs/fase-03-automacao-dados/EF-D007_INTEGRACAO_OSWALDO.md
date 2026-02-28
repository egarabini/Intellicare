# EF-D007 — Integracao Oswaldo (Indicadores Clinicos Auto-Alimentados)

> Consumir dados do Oswaldo para alimentar automaticamente indicadores de qualidade baseados em estadiamento de doencas cronicas, controle glicemico, pressao arterial e progressao de IRC.

## 1. Objetivo

Implementar `OswaldoIndicatorBridge` que traduz os estadiamentos e alertas do Oswaldo em medicoes automaticas de indicadores de qualidade do Donabedian:

- "% de pacientes DM2 com HbA1c controlada" (pilar Efetividade)
- "% de pacientes IRC G3+ com IECA/BRA prescrito" (pilar Legitimidade)
- "Taxa de progressao de IRC G3→G4 no periodo" (pilar Resultado)
- "% de alertas clinicos criticos respondidos em < 24h" (pilar Aceitabilidade/Processo)

## 2. Justificativa

- Indicadores de qualidade clinica hoje sao inseridos manualmente — impreciso e trabalhoso
- Oswaldo ja calcula estadiamentos e gera alertas — dados prontos para indicadores
- Sem integracao, o Donabedian mede qualidade de estrutura/processo mas nao de resultado clinico
- Resultado clinico e o pilar mais importante de Donabedian (desfecho real do paciente)

## 3. Escopo

### 3.1 Mapeamento Oswaldo → Indicadores Donabedian

```python
# Os indicadores abaixo devem existir no seed do Donabedian (ou ser criados automaticamente)
# e ser alimentados via Oswaldo periodicamente (cron diario)

OSWALDO_TO_INDICATOR_MAP = [
    OswaldoIndicatorMapping(
        indicator_name="Controle Glicemico DM2 (HbA1c < 8%)",
        indicator_description="% de pacientes DM2 com HbA1c <= 8% no ultimo trimestre",
        triad_dimension="outcome",
        pillar="efetividade",
        oswaldo_query={
            "disease": "dm2",
            "metric": "staging_distribution",
            "stages": ["CONTROLLED", "SUBOPTIMAL"],  # HbA1c < 8% = CONTROLLED + SUBOPTIMAL
            "period_days": 90,
        },
        calculation="(CONTROLLED_count + SUBOPTIMAL_count) / total_dm2_patients * 100",
        target_value=70.0,                # Meta: 70% dos pacientes controlados
        target_operator=">=",
        unit="%",
        period_type="quarterly",
    ),
    OswaldoIndicatorMapping(
        indicator_name="Controle de IRC — Progressao para G4",
        indicator_description="% de pacientes CKD G3 que progrediram para G4 no periodo",
        triad_dimension="outcome",
        pillar="efetividade",
        oswaldo_query={
            "disease": "ckd",
            "metric": "stage_transitions",
            "from_stages": ["G3a", "G3b"],
            "to_stages": ["G4", "G5"],
            "period_days": 365,
        },
        calculation="transitions_count / total_g3_patients * 100",
        target_value=5.0,                 # Meta: < 5% de progressao anual
        target_operator="<=",
        unit="%",
        period_type="yearly",
    ),
    OswaldoIndicatorMapping(
        indicator_name="Controle de Pressao Arterial HAS",
        indicator_description="% de pacientes HAS com PA controlada (OPTIMAL ou NORMAL)",
        triad_dimension="outcome",
        pillar="efetividade",
        oswaldo_query={
            "disease": "has",
            "metric": "staging_distribution",
            "stages": ["OPTIMAL", "NORMAL", "HIGH_NORMAL"],
            "period_days": 90,
        },
        target_value=60.0,
        target_operator=">=",
        unit="%",
        period_type="quarterly",
    ),
    OswaldoIndicatorMapping(
        indicator_name="Alertas Criticos com Resposta Documentada",
        indicator_description="% de alertas CRITICAL do Oswaldo com acao registrada em 24h",
        triad_dimension="process",
        pillar="aceitabilidade",
        oswaldo_query={
            "metric": "critical_alerts_response_rate",
            "severity": "critical",
            "response_window_hours": 24,
            "period_days": 30,
        },
        target_value=80.0,
        target_operator=">=",
        unit="%",
        period_type="monthly",
    ),
    OswaldoIndicatorMapping(
        indicator_name="Prescricao IECA/BRA em CKD com Proteinuria",
        indicator_description="% pacientes CKD G3+ com ACR > 30 que tem IECA/BRA prescrito",
        triad_dimension="process",
        pillar="legitimidade",
        oswaldo_query={
            "disease": "ckd",
            "metric": "guideline_adherence",
            "guideline": "KDIGO-2024-IECA-proteinuria",
            "period_days": 90,
        },
        target_value=85.0,
        target_operator=">=",
        unit="%",
        period_type="quarterly",
    ),
]
```

### 3.2 OswaldoClient (no Donabedian)

```python
class OswaldoClient:
    """
    Cliente HTTP para integracao com Oswaldo (8001).
    Usa o contrato padrao: POST /api/v1/analyze

    Cache: 1h por consulta (dados calculados pelo Oswaldo sao caros)
    Graceful degradation: se Oswaldo indisponivel, indicadores ficam
    sem medicao para o periodo (nao usam dados antigos — melhor ser
    honesto sobre a ausencia de dados).
    """

    async def get_staging_distribution(
        self,
        disease: str,
        period_days: int,
    ) -> dict:
        """
        Distribuicao de estadios no periodo.
        Ex: {"CONTROLLED": 42, "SUBOPTIMAL": 28, "POOR": 18, "VERY_POOR": 12}
        """

    async def get_stage_transitions(
        self,
        disease: str,
        from_stages: list[str],
        to_stages: list[str],
        period_days: int,
    ) -> dict:
        """
        Transicoes de estadio no periodo.
        Ex: {"transitions": 8, "total_at_risk": 120, "rate": 0.067}
        """

    async def get_critical_alerts(
        self,
        period_days: int,
    ) -> dict:
        """
        Alertas criticos e taxa de resposta.
        Ex: {"total_critical": 24, "responded_24h": 19, "response_rate": 0.79}
        """

    async def is_available(self) -> bool:
        """Verifica disponibilidade do Oswaldo."""
```

### 3.3 OswaldoIndicatorBridge

```python
class OswaldoIndicatorBridge:
    """
    Traduz dados do Oswaldo em medicoes para o Donabedian.

    Executado:
    1. Via job schedulado (cron diario as 02:00)
    2. Via endpoint manual: POST /api/v1/sync/oswaldo
    3. Via evento Redis quando Oswaldo publica "clinical.staging.calculated"
    """

    async def sync_all_indicators(self) -> SyncResult:
        """
        Sincroniza todos os indicadores mapeados.

        Para cada mapeamento:
        1. Consulta Oswaldo com a query definida
        2. Calcula valor do indicador
        3. Verifica se ja existe medicao para o periodo (skip se sim)
        4. Cria nova Measurement via DAO do Donabedian
        5. Log do resultado

        Retorna: SyncResult com contagem de criados, ignorados, erros.
        """

    async def sync_indicator(
        self,
        mapping: OswaldoIndicatorMapping,
    ) -> Optional[dict]:
        """
        Sincroniza um indicador especifico.
        """


@dataclass
class SyncResult:
    source: str = "oswaldo"
    synced_at: str = ""
    indicators_created: int = 0
    indicators_skipped: int = 0   # Ja existiam
    indicators_failed: int = 0
    errors: list[str] = field(default_factory=list)
    oswaldo_available: bool = True
```

### 3.4 Endpoints REST Novos

```python
# POST /api/v1/sync/oswaldo
# Dispara sincronizacao manual com Oswaldo
# Retorna: SyncResult

# GET /api/v1/sync/oswaldo/status
# Retorna: ultima sincronizacao (data, resultado, indicadores atualizados)

# GET /api/v1/sync/mappings/oswaldo
# Retorna: lista de mapeamentos Oswaldo → Indicadores Donabedian
```

### 3.5 Configuracao

```env
INTELLICARE_OSWALDO_URL=http://oswaldo:8001
INTELLICARE_OSWALDO_ENABLED=true
INTELLICARE_DONABEDIAN_SYNC_CRON="0 2 * * *"    # 02:00 diario
INTELLICARE_DONABEDIAN_SYNC_OSWALDO_ENABLED=true
```

## 4. Testes

- OswaldoClient: get_staging_distribution, get_stage_transitions, Oswaldo indisponivel (4 testes)
- OswaldoIndicatorBridge.sync_all_indicators: dados disponiveis, Oswaldo down (3 testes)
- Mapeamentos: calculo correto de cada indicador (5 testes)
- Endpoints: sync, status, mappings (3 testes)
- **Total**: 15+ testes novos

## 5. Criterios de Aceitacao

- [ ] 5+ indicadores clinicos mapeados para dados do Oswaldo
- [ ] `OswaldoIndicatorBridge` com sync automatico e manual
- [ ] Graceful degradation: Oswaldo down = indicadores sem medicao (nao erro)
- [ ] Deduplicacao: nao cria medicao duplicada para o mesmo periodo
- [ ] Job schedulado configurado no docker-compose
- [ ] 363 testes v1.0 continuam passando
- [ ] 15+ testes novos

## 6. Estimativa de Complexidade

- **Arquivos novos**: `integrations/oswaldo.py`, `sync/oswaldo_bridge.py`, `api/routes/sync.py`
- **Arquivos modificados**: `api/main.py`, `config.py`, `docker-compose.yml` (cron)
- **Linhas estimadas**: ~400
- **Testes novos**: ~15
