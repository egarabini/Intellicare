# EF-Z005 — Cobertura de Equipes de Saude da Familia (ESF)

> Integrar dados do e-SUS APS / SISAB para informar cobertura de Saude da Familia por municipio, identificar metas do Previne Brasil e calcular populacao sem cobertura.

## 1. Objetivo

Implementar cliente e-SUS APS (SISAB) para dados de cobertura ESF, permitindo que a Zilda responda:

- "Qual a cobertura de Saude da Familia em Campinas?"
- "Quantas equipes ESF faltam para atingir a meta do Previne Brasil?"
- "Qual o numero de familias sem cobertura de APS em Ribeirao Preto?"
- "Qual o credenciamento de ACS (Agentes Comunitarios) no municipio?"
- "Qual municipio da regiao tem menor cobertura ESF?"

## 2. Justificativa

- **Gap critico**: Cobertura ESF 0% implementada na v1.0.0
- **Previne Brasil**: Programa federal vincula repasse financeiro a indicadores ESF — municipios precisam acompanhar
- **Internacoes evitaveis**: Baixa cobertura ESF correlaciona com alta taxa ICSAP (EF-Z003)
- **Geralda/Oswaldo**: Precisam saber se paciente tem equipe ESF vinculada para acoes de acompanhamento
- **e-SUS APS**: SISAB disponibiliza dados de equipes e credenciamento via portal aberto

## 3. Escopo

### 3.1 Modelos de Dados

```python
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class ESFTeamType(str, Enum):
    ESF = "ESF"               # Equipe de Saude da Familia
    EAP = "EAP"               # Equipe de Atencao Primaria
    NASF = "NASF"             # Nucleo Ampliado de Saude da Familia
    eSB = "eSB"               # Equipe de Saude Bucal
    eMulti = "eMulti"         # Equipe Multiprofissional


@dataclass
class ESFTeam:
    """
    Equipe de Saude da Familia registrada no CNES/SISAB.
    """
    team_id: str                     # Identificador da equipe no SISAB
    team_type: ESFTeamType
    ine_code: str                    # Identificador Nacional de Equipe
    team_name: str

    municipality_code: str
    state_code: str
    cnes_code: str                   # Unidade de saude vinculada

    # Composicao
    has_doctor: bool
    has_nurse: bool
    has_tech_nurse: bool
    has_acs: bool                    # Agente Comunitario de Saude
    num_acs: int                     # Quantidade de ACS
    has_dentist: bool                # eSB vinculada

    # Cobertura
    reference_population: int        # Populacao cadastrada (meta: 3.450 pessoas/ESF)
    registered_families: int
    registered_individuals: int

    # Status
    is_active: bool
    implantation_date: Optional[str]

    data_source: str = "CNES/SISAB"
    reference_month: str = ""


@dataclass
class ESFCoverageData:
    """
    Dados de cobertura ESF de um municipio.
    """
    municipality_code: str
    municipality_name: Optional[str]
    state_code: str
    population: int                  # Populacao IBGE
    reference_month: str

    # Equipes
    total_esf_teams: int             # ESF ativas
    total_eap_teams: int             # EAP (sem ESF completa)
    total_nasf_teams: int
    total_esb_teams: int             # Saude Bucal

    # Populacao coberta
    covered_population: int          # Cadastrados em ESF/EAP
    coverage_rate: float             # covered / total_population (0.0 - 1.0)
    uncovered_population: int        # Sem cobertura APS

    # Agentes Comunitarios
    total_acs: int
    acs_per_1000_pop: float

    # Saude Bucal
    dental_coverage_rate: float

    # Metas Previne Brasil
    previne_brasil_target: float     # Meta federal de cobertura (tipicamente 0.60)
    previne_brasil_gap: float        # Diferenca para meta (negativo = abaixo)
    teams_needed_for_target: int     # Equipes adicionais necessarias

    # Tendencia (se dados historicos disponiveis)
    coverage_trend: Optional[str]    # "increasing"/"stable"/"decreasing"
    coverage_prev_year: Optional[float]


@dataclass
class RegionalESFComparison:
    """
    Comparativo de cobertura ESF entre municipios de uma regiao.
    """
    region_name: str
    state_code: str
    reference_month: str

    municipalities: list[ESFCoverageData]

    # Resumo
    avg_coverage_rate: float
    min_coverage: ESFCoverageData
    max_coverage: ESFCoverageData
    below_target_count: int          # Municipios abaixo da meta Previne Brasil
    above_target_count: int

    total_uncovered_population: int
    total_teams_needed: int          # Para toda a regiao atingir meta
```

### 3.2 ESUSAPSClient

```python
class ESUSAPSClient:
    """
    Cliente para e-SUS APS / SISAB — dados de Saude da Familia.

    Fontes:
    1. CNES API: equipes registradas (preferencial)
    2. SISAB: producao e cobertura (complementar)
    3. IBGE: populacao para calculo de cobertura

    Meta Previne Brasil: 60% de cobertura ESF para boa pontuacao.
    Parametro tecnico ESF: 1 equipe / 3.450 pessoas (max 4.000).

    Cache:
    - Equipes ativas: TTL 6h (mudam com credenciamento)
    - Cobertura agregada: TTL 2h
    - Comparativo regional: TTL 4h
    """

    # Meta federal de cobertura (Previne Brasil 2023-2026)
    PREVINE_BRASIL_TARGET = 0.60

    # Parametro tecnico: populacao por equipe ESF
    POPULATION_PER_ESF_TEAM = 3450
    POPULATION_PER_ESF_TEAM_MAX = 4000

    def __init__(
        self,
        cnes_client: "CnesClient",
        ibge_client: "IBGEClient",
        cache_manager,
    ):
        self._cnes = cnes_client
        self._ibge = ibge_client
        self._cache = cache_manager

    async def get_esf_teams(
        self,
        municipality_code: str,
        active_only: bool = True,
    ) -> list[ESFTeam]:
        """
        Equipes ESF de um municipio.

        Busca no CNES por estabelecimentos do tipo 01 (UBS/ESF)
        com equipamentos de ESF (INE).

        Cache: 6h.
        """

    async def get_esf_coverage(
        self,
        municipality_code: str,
    ) -> ESFCoverageData:
        """
        Cobertura ESF calculada para o municipio.

        Algoritmo:
        1. Busca equipes ativas (get_esf_teams)
        2. Soma populacao cadastrada
        3. Busca populacao IBGE do municipio
        4. Calcula coverage_rate = cadastrados / populacao
        5. Calcula gap para meta Previne Brasil
        6. Calcula equipes necessarias para atingir meta

        Cache: 2h.
        """

    async def get_regional_esf_comparison(
        self,
        municipality_codes: list[str],
        region_name: str,
    ) -> RegionalESFComparison:
        """
        Comparativo de cobertura ESF para uma lista de municipios (regiao).

        Util para:
        "Qual municipio da regiao de Campinas tem menor cobertura ESF?"

        Processa cada municipio em paralelo via asyncio.gather().
        Cache: 4h.
        """

    async def calculate_teams_needed(
        self,
        municipality_code: str,
        target_coverage: float = PREVINE_BRASIL_TARGET,
    ) -> dict:
        """
        Calcula quantas equipes ESF precisam ser criadas para atingir meta.

        Retorna:
        {
            "current_coverage": 0.48,
            "target_coverage": 0.60,
            "current_teams": 12,
            "needed_teams": 3,
            "needed_acs": 9,           # ~3 ACS por equipe
            "uncovered_population": 35000,
            "cost_estimate_brl": None,  # Nao calculado — sensivel politicamente
        }
        Cache: 2h.
        """

    async def get_acs_credentialing(
        self,
        municipality_code: str,
    ) -> dict:
        """
        Credenciamento de Agentes Comunitarios de Saude.

        Retorna:
        {
            "total_acs": 48,
            "acs_per_team": 4.0,           # Meta: 1 ACS / 750 famílias
            "families_per_acs": 720,
            "is_adequate": True,
            "standard": "1 ACS para ate 750 familias"
        }
        Cache: 6h.
        """
```

### 3.3 Endpoints REST

```python
# GET /esf/municipality/{code}/teams
# Query params: active_only (default true)
# Retorna: list[ESFTeam]

# GET /esf/municipality/{code}/coverage
# Retorna: ESFCoverageData com gap Previne Brasil

# GET /esf/municipality/{code}/teams-needed
# Query params: target_coverage (default 0.60)
# Retorna: dict com calculo de equipes necessarias

# GET /esf/municipality/{code}/acs
# Retorna: dict com credenciamento de ACS

# GET /esf/region/comparison
# Body: {municipality_codes: [...], region_name: "..."}
# Retorna: RegionalESFComparison com ranking
```

### 3.4 LangChain Tools no ZildaAgent

```python
# Adicionar ao ZildaAgent._build_tools():
Tool(
    name="get_esf_coverage",
    description="Cobertura de Saude da Familia (ESF) em um municipio. "
                "Inclui numero de equipes, populacao coberta, meta Previne Brasil "
                "e quantas equipes faltam para atingir a meta. "
                "Use para perguntas sobre APS, Saude da Familia, NASF, ACS.",
    func=self._tool_get_esf_coverage,
),
Tool(
    name="compare_regional_esf",
    description="Compara cobertura ESF entre municipios de uma regiao. "
                "Use para 'qual municipio da regiao tem menor cobertura APS' "
                "ou rankings de cobertura de Saude da Familia.",
    func=self._tool_compare_regional_esf,
),
```

### 3.5 Configuracao

```env
# ESF / e-SUS APS
INTELLICARE_ESF_PREVINE_BRASIL_TARGET=0.60
INTELLICARE_ESF_CACHE_TEAMS_TTL=21600       # 6h
INTELLICARE_ESF_CACHE_COVERAGE_TTL=7200     # 2h
INTELLICARE_ESF_CACHE_REGIONAL_TTL=14400    # 4h
```

### 3.6 Arquitetura de Arquivos

```
zilda/
  clients/
    esf/
      __init__.py
      esus_aps.py            # ESUSAPSClient
      models.py              # ESFTeam, ESFCoverageData, RegionalESFComparison
      calculators.py         # Calculos de cobertura e gap
  api/
    routes/
      esf.py                 # Endpoints /esf/...
```

## 4. Testes

- ESUSAPSClient: get_teams, get_coverage, regional_comparison, teams_needed (6 testes)
- Calculo de cobertura: taxa, gap, equipes necessarias (4 testes)
- RegionalComparison: ranking, min/max, abaixo da meta (3 testes)
- Endpoints REST (4 testes)
- LangChain Tools (2 testes)
- Fallback sem dados CNES (2 testes)
- **Total**: 21+ testes novos

## 5. Criterios de Aceitacao

- [ ] `ESUSAPSClient` com 5 metodos funcionais
- [ ] Calculo de gap para meta Previne Brasil (60%)
- [ ] Calculo de equipes ESF necessarias com parametro 3.450 hab/equipe
- [ ] Comparativo regional com ranking de cobertura
- [ ] 5 endpoints REST documentados
- [ ] 2 novas LangChain Tools no ZildaAgent
- [ ] Cobertura expressa como porcentagem e populacao absoluta
- [ ] 68 testes v1.0 continuam passando
- [ ] 21+ testes novos
- [ ] Cobertura >= 88%

## 6. Estimativa de Complexidade

- **Arquivos novos**: `clients/esf/esus_aps.py`, `clients/esf/models.py`, `clients/esf/calculators.py`, `api/routes/esf.py`
- **Arquivos modificados**: `subagent/tools.py` (2 tools novas), `api/app.py`
- **Linhas estimadas**: ~380
- **Testes novos**: ~21
