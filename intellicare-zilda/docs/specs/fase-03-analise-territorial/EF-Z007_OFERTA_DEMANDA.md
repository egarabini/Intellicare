# EF-Z007 — Analise de Oferta vs Demanda

> Calcular capacidade instalada vs necessidade populacional por territorio e servico, identificando desequilibrios e projetando necessidades futuras.

## 1. Objetivo

Implementar o motor de analise oferta-demanda, permitindo que a Zilda responda:

- "A capacidade de dialise SUS em Campinas e suficiente para a populacao com IRC?"
- "Quantos leitos de UTI tem a regiao de saude vs o recomendado pela OMS?"
- "Com o crescimento da populacao idosa, quantas equipes ESF adicionais serao necessarias?"
- "A rede de UBS de Ribeirao Preto consegue absorver a demanda atual?"
- "Qual o indice de ocupacao de leitos hospitalares SUS no municipio?"

## 2. Justificativa

- **Gap critico**: Oferta-demanda 0% implementado na v1.0.0
- **Donabedian precisa**: Para avaliar estrutura (Structure domain) — capacidade instalada adequada
- **Gestao**: Subsidia decisoes de investimento e planejamento da rede
- **Wanda**: "Tem capacidade de atender mais pacientes IRC nessa regiao?"
- **Prevencao de colapso**: Identificar antes de atingir limite de capacidade

## 3. Escopo

### 3.1 Modelos de Dados

```python
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class BalanceStatus(str, Enum):
    SURPLUS = "surplus"           # Oferta > demanda (>= 120%)
    BALANCED = "balanced"         # Oferta balanceada (90-120%)
    DEFICIT_MILD = "deficit_mild"     # Leve deficit (70-90%)
    DEFICIT_MODERATE = "deficit_moderate"  # Deficit moderado (50-70%)
    DEFICIT_CRITICAL = "deficit_critical"  # Deficit critico (< 50%)


@dataclass
class ServiceCapacity:
    """
    Capacidade instalada de um servico em um territorio.
    """
    municipality_code: str
    municipality_name: Optional[str]
    state_code: str

    service_code: str
    service_name: str

    # Oferta (CNES)
    total_establishments: int
    sus_establishments: int         # Contratados pelo SUS
    total_beds: Optional[int]       # Leitos para servicos com leitos
    sus_beds: Optional[int]
    monthly_capacity: Optional[int] # Procedimentos/mes (SIA/DATASUS)

    # Populacao
    target_population: int          # Populacao com necessidade estimada

    # Razoes
    capacity_per_100k: float        # Capacidade / populacao * 100.000
    standard_per_100k: float        # Padrao MS / OMS recomendado
    sus_capacity_rate: float        # % da capacidade no SUS


@dataclass
class SupplyDemandAnalysis:
    """
    Analise de oferta vs demanda para um servico em um territorio.
    """
    municipality_code: str
    municipality_name: Optional[str]
    state_code: str
    year: int

    service_code: str
    service_name: str

    # Capacidade instalada
    capacity: ServiceCapacity

    # Demanda estimada
    estimated_demand: int           # Pacientes/procedimentos necessarios
    demand_estimation_method: str   # Ex: "prevalencia_ibge", "datasus_sih"
    prevalence_rate: Optional[float] # Taxa de prevalencia usada

    # Balanco
    balance_status: BalanceStatus
    supply_demand_ratio: float      # supply / demand (1.0 = equilibrio)
    unmet_demand: int               # Demanda nao atendida (negativo = superavit)
    unmet_demand_pct: float

    # Projecao
    projected_demand_5y: Optional[int]    # Projecao 5 anos (populacao + envelhecimento)
    projected_balance_5y: Optional[BalanceStatus]

    # Recomendacoes
    recommendations: list[str]

    # Benchmarks
    benchmark_state: Optional[float]
    benchmark_national: Optional[float]


@dataclass
class TerritorialCapacityReport:
    """
    Relatorio completo de capacidade de um territorio.
    """
    municipality_code: str
    municipality_name: Optional[str]
    state_code: str
    population: int
    year: int

    services_analyzed: list[SupplyDemandAnalysis]

    # Resumo
    critical_deficits: list[str]        # Servicos com deficit critico
    moderate_deficits: list[str]
    surplus_services: list[str]

    overall_capacity_score: float       # 0-1 (1 = plena capacidade)

    # Comparativo regional
    state_avg_score: Optional[float]
    national_avg_score: Optional[float]

    key_findings: list[str]
    priority_investments: list[str]     # Top 3 investimentos sugeridos
```

### 3.2 Parametros de Referencia (Padroes MS / OMS)

```python
# standards.py — Padroes de capacidade instalada por servico
# Fontes: Ministerio da Saude, OMS, Resolucoes CFM/CFO

SERVICE_STANDARDS = {
    # Leitos hospitalares
    "leitos_gerais": Standard(
        name="Leitos Hospitalares Gerais",
        indicator="leitos_por_1000_hab",
        recommended=3.0,               # OMS: 3 leitos / 1.000 hab
        minimum=2.0,
        source="OMS / MS Portaria 1.101/2002"
    ),
    "leitos_uti": Standard(
        name="Leitos UTI",
        indicator="leitos_por_100k_hab",
        recommended=25.0,              # ~2.5 / 10.000 hab
        minimum=10.0,
        source="CFM Resolucao 2.156/2016"
    ),

    # Dialise
    "hemodialise": Standard(
        name="Sessoes de Hemodialise",
        indicator="prevalencia_irc_por_100k",
        recommended=None,              # Segue prevalencia IRC
        prevalence_rate=0.001,         # ~0.1% em dialise (SBN)
        source="Sociedade Brasileira de Nefrologia"
    ),

    # APS
    "esf": Standard(
        name="Equipes ESF",
        indicator="equipes_por_pop",
        recommended=1 / 3450,          # 1 equipe / 3.450 hab
        minimum=1 / 4000,
        source="Portaria MS 2.436/2017 — PNAB"
    ),
    "ubs": Standard(
        name="Unidades Basicas de Saude",
        indicator="ubs_por_100k_hab",
        recommended=6.0,               # ~1 UBS / 15.000 hab
        minimum=3.0,
        source="Ministerio da Saude"
    ),

    # Especialidades
    "cardiologia": Standard(
        name="Cardiologistas SUS",
        indicator="especialistas_por_100k",
        recommended=5.0,
        minimum=2.0,
        source="CFM / Ministerio da Saude"
    ),
    "nefrologia": Standard(
        name="Nefrologistas SUS",
        indicator="especialistas_por_100k",
        recommended=2.0,
        minimum=0.5,
        source="Sociedade Brasileira de Nefrologia"
    ),
    "oncologia": Standard(
        name="Atendimento Oncologico",
        indicator="centros_por_milhao",
        recommended=1.0,               # 1 centro / 1 milhao hab
        minimum=0.5,
        source="INCA / Ministerio da Saude"
    ),
}
```

### 3.3 SupplyDemandEngine

```python
class SupplyDemandEngine:
    """
    Motor de analise de oferta vs demanda.

    Metodologia:
    1. OFERTA: dados CNES (estabelecimentos, leitos, servicos)
    2. DEMANDA: estimada por prevalencia (IBGE populacao * taxa epidemiologica)
       ou por producao historica (DATASUS SIH/SIA)
    3. BALANCO: ratio = oferta / demanda
    4. STATUS: classificado em 5 niveis (surplus → deficit_critical)
    5. PROJECAO: usa crescimento populacional IBGE + envelhecimento

    Cache: 6h.
    """

    def __init__(
        self,
        cnes_client: "CnesClient",
        ibge_client: "IBGEClient",
        datasus_hospitalar: "DataSUSHospitalarClient",
        esf_client: "ESUSAPSClient",
        cache_manager,
    ):
        ...

    async def analyze_service(
        self,
        municipality_code: str,
        service_code: str,
        year: int,
    ) -> SupplyDemandAnalysis:
        """
        Analise oferta-demanda para um servico especifico.

        Exemplo para dialise:
        - Oferta: sessoes/mes disponiveis (CNES servico 117)
        - Demanda: populacao * 0.1% (prevalencia IRC em dialise)
        - Ratio: se oferta cobre demanda com margem 20%, BALANCED

        Cache: 6h.
        """

    async def get_territorial_report(
        self,
        municipality_code: str,
        services: Optional[list[str]] = None,  # None = todos
        year: Optional[int] = None,
    ) -> TerritorialCapacityReport:
        """
        Relatorio completo de capacidade territorial.

        Analisa os 8 principais servicos em paralelo.
        Gera key_findings e priority_investments.

        Cache: 6h.
        """

    async def project_future_demand(
        self,
        municipality_code: str,
        service_code: str,
        years_ahead: int = 5,
    ) -> dict:
        """
        Projeta demanda futura considerando:
        - Crescimento populacional (IBGE)
        - Envelhecimento da populacao (piramide etaria)
        - Para IRC/DM/HAS: fator de piora epidemiologica +2%/ano

        Retorna:
        {
            "year_target": 2031,
            "current_demand": 1200,
            "projected_demand": 1680,
            "growth_rate": 0.07,
            "drivers": ["crescimento pop. +1.2%/ano", "envelhecimento +5.8% pop. >65"],
            "additional_capacity_needed": 480,
            "action_urgency": "high"  # Necessidade de investimento em 2-3 anos
        }
        Cache: 24h.
        """

    def _estimate_demand_by_prevalence(
        self,
        population: int,
        service_code: str,
    ) -> int:
        """
        Estima demanda com base em taxa de prevalencia epidemiologica.

        Para dialise: populacao * 0.1% (SBN)
        Para UTI: 2.5 leitos / 10.000 hab (demanda baseline)
        Para ESF: populacao / 3.450 pessoas por equipe
        """

    def _classify_balance(
        self,
        supply: int,
        demand: int,
    ) -> tuple[BalanceStatus, float]:
        """
        Classifica o balanco oferta-demanda.

        Retorna: (BalanceStatus, ratio)
        - ratio > 1.2:  SURPLUS (oferta >= 120% da demanda)
        - 0.9-1.2:      BALANCED
        - 0.7-0.9:      DEFICIT_MILD
        - 0.5-0.7:      DEFICIT_MODERATE
        - < 0.5:        DEFICIT_CRITICAL
        """
```

### 3.4 Endpoints REST

```python
# GET /supply-demand/municipality/{code}/service/{service_code}
# Query params: year (default atual)
# Retorna: SupplyDemandAnalysis

# GET /supply-demand/municipality/{code}/report
# Query params: year (default atual), services (lista opcional)
# Retorna: TerritorialCapacityReport

# GET /supply-demand/municipality/{code}/service/{service_code}/projection
# Query params: years_ahead (default 5)
# Retorna: dict com projecao de demanda

# GET /supply-demand/region
# Body: {municipality_codes: [...], service_code: "117"}
# Retorna: list[SupplyDemandAnalysis] para comparativo regional
```

### 3.5 LangChain Tools no ZildaAgent

```python
# Adicionar ao ZildaAgent._build_tools():
Tool(
    name="analyze_supply_demand",
    description="Analisa capacidade instalada vs demanda para um servico especifico. "
                "Use para perguntas sobre 'suficiencia' ou 'capacidade': "
                "'a capacidade de dialise e suficiente?', 'tem leitos UTI suficientes?', "
                "'quantos especialistas tem vs o recomendado?'.",
    func=self._tool_analyze_supply_demand,
),
Tool(
    name="get_territorial_capacity_report",
    description="Relatorio completo de capacidade assistencial de um municipio. "
                "Analisa multiplos servicos e gera ranking de deficits. "
                "Use para perguntas amplas sobre situacao da saude ou planejamento.",
    func=self._tool_get_territorial_capacity_report,
),
```

### 3.6 Configuracao

```env
INTELLICARE_SUPPLY_DEMAND_CACHE_TTL=21600  # 6h
INTELLICARE_SUPPLY_DEMAND_PROJECTION_YEARS=5
INTELLICARE_SUPPLY_DEMAND_EPIDEMIOLOGICAL_GROWTH=0.02  # +2%/ano para doencas cronicas
```

### 3.7 Arquitetura de Arquivos

```
zilda/
  analysis/
    __init__.py
    voids.py               # EF-Z006
    supply_demand.py       # SupplyDemandEngine
    standards.py           # SERVICE_STANDARDS
    projections.py         # Logica de projecao demografica
  api/
    routes/
      supply_demand.py     # Endpoints /supply-demand/...
```

## 4. Testes

- SupplyDemandEngine: analise por servico, relatorio completo (5 testes)
- Classificacao de balanco: surplus, balanced, cada nivel deficit (5 testes)
- Estimativa por prevalencia: dialise, UTI, ESF (3 testes)
- Projecao demografica: crescimento, envelhecimento, urgencia (3 testes)
- Standards: validar padroes por servico (2 testes)
- Endpoints (4 testes)
- LangChain Tools (2 testes)
- **Total**: 24+ testes novos

## 5. Criterios de Aceitacao

- [ ] `SupplyDemandEngine` com 3 metodos principais
- [ ] 10+ servicos com padroes de referencia (MS/OMS/CFM)
- [ ] Classificacao em 5 niveis (surplus → deficit_critical)
- [ ] Projecao de demanda com fator de envelhecimento
- [ ] `TerritorialCapacityReport` com key_findings e priority_investments
- [ ] 4 endpoints REST funcionais
- [ ] 2 novas LangChain Tools no ZildaAgent
- [ ] Fontes citadas em todos os padroes (MS, OMS, CFM)
- [ ] 68 testes v1.0 continuam passando
- [ ] 24+ testes novos
- [ ] Cobertura >= 87%

## 6. Estimativa de Complexidade

- **Arquivos novos**: `analysis/supply_demand.py`, `analysis/standards.py`, `analysis/projections.py`, `api/routes/supply_demand.py`
- **Arquivos modificados**: `subagent/tools.py` (2 tools), `api/app.py`
- **Linhas estimadas**: ~600
- **Testes novos**: ~24

## 7. Notas de Implementacao

### Metodologia de estimativa de demanda

A Zilda usa 2 abordagens para estimar demanda:

1. **Por prevalencia** (preferencial): `populacao * taxa_epidemiologica`
   - Confiavel para doencas com prevalencia bem estudada (IRC, DM, HAS)
   - Fontes: SBN, SBD, SBC, IBGE

2. **Por historico** (complementar): dados reais do DATASUS SIH/SIA
   - Mais preciso para servicos com producao registrada
   - Limitado pelo gap temporal do DATASUS

### Limitacoes a comunicar

A Zilda sempre informa nas respostas de oferta-demanda:
> "Estimativa de demanda baseada em taxas epidemiologicas nacionais — pode variar pelo perfil especifico da populacao local."

### Integracao com Donabedian

O `TerritorialCapacityReport` pode ser consumido diretamente pelo Donabedian
como entrada para a dimensao **Estrutura** (Structure) da avaliacao de qualidade.
Formato de exportacao FHIR: `Measure` + `MeasureReport`.
