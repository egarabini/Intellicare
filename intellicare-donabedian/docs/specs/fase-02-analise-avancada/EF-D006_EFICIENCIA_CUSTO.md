# EF-D006 — Eficiencia: Custo-Beneficio e QALY

> Implementar analise de eficiencia real do pilar Eficiencia — calculando custo por resultado obtido, QALY (Quality-Adjusted Life Year) simplificado e ROI de intervencoes de qualidade.

## 1. Objetivo

Elevar o pilar Eficiencia de 5/10 para funcionalidade real, respondendo:

- "Qual o custo por internacao evitada pelo programa de telefarmacia?"
- "O investimento em treinamento de checklist cirurgico reduziu reinternacoes?"
- "Qual o custo por QALY das intervencoes de qualidade implementadas?"
- "A melhoria nos indicadores de processo gerou reducao de custo?"

## 2. Justificativa

- Eficiencia (Donabedian) = relacao custo/beneficio — sem custo nao ha eficiencia real
- Gestores hospitalares precisam justificar investimentos em qualidade para diretoria
- Bancos de fomento (BNDES, BID) exigem analise de custo-efetividade para financiamento
- Sem ROI de qualidade, o Donabedian e visto como "custo administrativo" nao como investimento

## 3. Escopo

### 3.1 Modelos de Dados

```python
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class CostEntry:
    """
    Registro de custo associado a um indicador ou intervencao.
    """
    cost_id: str
    indicator_id: Optional[str]          # Indicador relacionado (se aplicavel)
    intervention_name: Optional[str]     # Nome da intervencao (ex: "Programa Telefarmacia")

    cost_category: str                   # "pessoal", "material", "treinamento", "infraestrutura"
    cost_brl: float                      # Custo em BRL
    period_start: str
    period_end: str
    unit_description: str                # O que este custo compra (ex: "salarios enfermeiros/mes")


@dataclass
class EfficiencyAnalysis:
    """
    Analise de eficiencia para uma intervencao ou indicador.
    """
    indicator_id: Optional[str]
    intervention_name: str
    period_start: str
    period_end: str

    # Custos
    total_cost_brl: float
    cost_breakdown: list[CostEntry]

    # Resultados obtidos
    baseline_value: float                # Valor antes da intervencao
    current_value: float                 # Valor apos
    improvement_absolute: float          # Diferenca absoluta
    improvement_relative_pct: float      # Diferenca percentual

    # Indicadores derivados de resultado (quando aplicavel)
    events_avoided: Optional[int]        # Ex: reinternacoes evitadas
    cost_per_event_avoided: Optional[float]  # BRL por evento evitado

    # QALY simplificado
    qaly_gained: Optional[float]         # Anos de vida ajustados por qualidade ganhos (estimado)
    cost_per_qaly: Optional[float]       # BRL por QALY

    # ROI
    estimated_savings_brl: Optional[float]  # Economia estimada pelo resultado
    roi_ratio: Optional[float]           # (savings - cost) / cost
    roi_interpretation: Optional[str]    # "alto_valor", "valor_aceitavel", "baixo_valor"

    # Benchmark de custo
    cost_per_qaly_threshold_brl: float = 40_000  # PIB per capita BR = limiar OMS
    is_cost_effective: Optional[bool]


@dataclass
class EfficiencyScore:
    """
    Score de Eficiencia para o periodo (contribui para pilar Eficiencia).
    """
    period_start: str
    period_end: str

    # Analises disponíveis
    analyses: list[EfficiencyAnalysis]
    analyzed_indicators_count: int
    total_investment_brl: float

    # Score derivado
    cost_effective_count: int            # Intervencoes custo-efetivas
    efficiency_score: float              # 0-100 para o pilar Eficiencia
    score_methodology: str               # Como o score foi calculado
```

### 3.2 EfficiencyEngine

```python
class EfficiencyEngine:
    """
    Motor de analise de eficiencia e custo-beneficio.

    Abordagem:
    - Requer que gestores registrem CUSTOS via endpoint dedicado
    - Sem custo registrado: eficiencia calculada apenas por indicadores
      (sem componente de custo-beneficio — score parcial)
    - Com custo: calcula ROI, custo por evento evitado e QALY estimado
    """

    # Limiar OMS de custo-efetividade = 3x PIB per capita
    # PIB per capita Brasil 2025 ≈ R$ 46.000 → limiar ≈ R$ 138.000 por QALY
    # Usamos limiar mais conservador (1x PIB = R$ 46.000) para saude publica
    COST_EFFECTIVENESS_THRESHOLD_BRL = 46_000

    async def analyze_efficiency(
        self,
        indicator_id: str,
        period_start: str,
        period_end: str,
        baseline_period_start: str,
        baseline_period_end: str,
    ) -> EfficiencyAnalysis:
        """
        Analise de eficiencia para um indicador com custo registrado.

        Passos:
        1. Busca custos registrados para o indicador
        2. Calcula melhoria vs periodo baseline
        3. Estima eventos evitados (quando aplicavel)
        4. Calcula custo por evento evitado
        5. Estima QALY simplificado (tabela de conversao por tipo de indicador)
        6. Calcula ROI (economia SUS/plano vs investimento)
        """

    async def calculate_efficiency_score(
        self,
        period_start: str,
        period_end: str,
    ) -> EfficiencyScore:
        """
        Score de Eficiencia para o periodo.

        Se ha custos registrados: score baseado em custo-efetividade
        Se nao ha custos: score baseado apenas em melhoria relativa de indicadores
        """

    def estimate_qaly(
        self,
        indicator_name: str,
        improvement_absolute: float,
        population_affected: Optional[int] = None,
    ) -> Optional[float]:
        """
        Estimativa simplificada de QALY por tipo de indicador.

        Tabela de conversao (baseada em literatura):
        - Taxa de infeccao hospitalar (-1%): ~0.3 QALY por 100 pacientes
        - Mortalidade hospitalar (-0.1%): ~1.0 QALY por 1.000 internacoes
        - Reinternacao evitada (1 caso): ~0.2 QALY
        - Tempo porta-balao IAM (-10min): ~0.5 QALY por 100 pacientes
        """

    def estimate_savings(
        self,
        indicator_name: str,
        events_avoided: int,
    ) -> Optional[float]:
        """
        Estimativa de economia por eventos evitados.

        Tabela de custos SUS (SIGTAP):
        - Internacao geral: R$ 1.200/dia (media SUS)
        - Reinternacao: R$ 3.500 por episodio (media)
        - Infeccao hospitalar: R$ 8.000 por caso (ANVISA)
        - IAM com angioplastia: R$ 15.000 (SIGTAP)
        """
```

### 3.3 Registro de Custos

```python
# Novo endpoint para registrar custos de intervencoes:
# POST /api/v1/costs
# Body: CostEntry
# Retorna: CostEntry criado

# GET /api/v1/costs
# Query params: indicator_id, period_start, period_end
# Retorna: list[CostEntry]

# GET /api/v1/efficiency/indicator/{indicator_id}
# Query params: period_start, period_end, baseline_start, baseline_end
# Retorna: EfficiencyAnalysis

# GET /api/v1/efficiency/summary
# Query params: period_start, period_end
# Retorna: EfficiencyScore com todas as analises

# GET /api/v1/efficiency/pillar-score
# Query params: period_start, period_end
# Retorna: Score 0-100 do pilar Eficiencia com metodologia
```

### 3.4 Tabela SQL

```sql
CREATE TABLE donabedian_costs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    indicator_id UUID REFERENCES donabedian_indicators(id),
    intervention_name VARCHAR(200),
    cost_category VARCHAR(50) NOT NULL,
    cost_brl NUMERIC(12,2) NOT NULL,
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    unit_description TEXT,
    created_by UUID,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 3.5 Dashboard — Secao Eficiencia

Adicionar a pagina `1_🏠_Home.py` e nova aba na pagina de indicadores:
- ROI por intervencao (tabela com custo, resultado, ROI)
- Custo por QALY vs limiar (gauge chart)
- "X intervencoes custo-efetivas no periodo"
- Timeline de investimento vs melhoria de indicadores

## 4. Testes

- EfficiencyEngine.analyze_efficiency: com custo, sem custo (3 testes)
- estimate_qaly: por tipo de indicador (3 testes)
- estimate_savings: infeccao, reinternacao, IAM (3 testes)
- calculate_efficiency_score: com e sem dados de custo (2 testes)
- Endpoints: costs CRUD, efficiency analysis, summary (4 testes)
- **Total**: 15+ testes novos

## 5. Criterios de Aceitacao

- [ ] `EfficiencyEngine` com 4 metodos principais
- [ ] Tabela `donabedian_costs` com migration
- [ ] QALY estimado com tabela de conversao por tipo de indicador
- [ ] ROI calculado quando ha custos e baseline registrados
- [ ] Score de Eficiencia (0-100) integrado ao pilar existente
- [ ] Funciona sem custo registrado (score parcial sem penalizar)
- [ ] Limiar OMS/PIB per capita documentado na metodologia
- [ ] 363 testes v1.0 continuam passando
- [ ] 15+ testes novos

## 6. Estimativa de Complexidade

- **Arquivos novos**: `efficiency/engine.py`, `efficiency/models.py`, `api/routes/efficiency.py`, migration `donabedian_costs`
- **Arquivos modificados**: `api/routes/assessment.py` (integrar Eficiencia score), `dashboard/pages/1_🏠_Home.py`
- **Linhas estimadas**: ~500
- **Testes novos**: ~15
