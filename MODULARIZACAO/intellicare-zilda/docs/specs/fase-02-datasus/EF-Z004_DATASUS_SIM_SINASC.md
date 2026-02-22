# EF-Z004 — DATASUS Mortalidade e Nascimentos (SIM / SINASC)

> Integrar dados do Sistema de Informacao sobre Mortalidade (SIM) e do Sistema de Informacoes sobre Nascidos Vivos (SINASC) para indicadores epidemiologicos vitais por municipio.

## 1. Objetivo

Implementar clientes DATASUS para os sistemas SIM e SINASC, permitindo que a Zilda responda:

- "Qual a taxa de mortalidade infantil em Campinas?"
- "Qual a principal causa de morte em Ribeirao Preto?"
- "Qual a cobertura de pre-natal no municipio?"
- "Qual a taxa de mortalidade prematura por doencas cardiovasculares?"
- "Quantos nascidos vivos com baixo peso em municipios de SP?"

## 2. Justificativa

- **Gap critico**: SIM e SINASC 0% implementados na v1.0.0
- **Indicadores-chave**: Mortalidade infantil e materna sao indicadores pactuados no PMAQ/Previne Brasil
- **Ciclo assistencial**: Nascimentos iniciam jornada na Geralda; obitos completam ciclo de auditoria
- **Wanda/Donabedian**: Precisam de indicadores de mortalidade para avaliar qualidade assistencial
- **APIs publicas**: MS disponibiliza SIM e SINASC via mesma API REST do DATASUS

## 3. Escopo

### 3.1 Modelos de Dados

```python
from dataclasses import dataclass, field
from typing import Optional


# ── SIM — Sistema de Informacao sobre Mortalidade ──

@dataclass
class MortalityRecord:
    """
    Registro de obito do SIM.
    """
    municipality_code: str           # Municipio de residencia (nao ocorrencia)
    state_code: str
    year: int
    month: Optional[int]

    cid_code: str                    # Causa basica de obito
    cid_description: Optional[str]
    cid_chapter: str                 # Ex: "IX - Aparelho Circulatorio"

    total_deaths: int
    sex: Optional[str]               # M/F/I (ignorado)
    age_group: Optional[str]         # "< 1", "1-4", "5-14", ... "80+"
    place_of_death: Optional[str]    # Hospital, Domicilio, Via publica, etc.

    # Classificacao
    is_avoidable: Optional[bool]     # Malta et al. (2010) — obitos evitaveis
    avoidable_category: Optional[str]  # "reducivel por APS", "reducivel em geral"
    is_maternal: bool = False
    is_infant: bool = False          # < 1 ano
    is_perinatal: bool = False       # < 7 dias pos-parto

    data_source: str = "SIM/DATASUS"
    reference_period: str = ""


@dataclass
class MortalityIndicators:
    """
    Indicadores de mortalidade calculados para um municipio/periodo.
    """
    municipality_code: str
    municipality_name: Optional[str]
    state_code: str
    year: int
    population: Optional[int]         # Da projecao IBGE

    # Taxas por 100.000 hab.
    general_mortality_rate: float
    infant_mortality_rate: Optional[float]     # Por 1.000 NV
    neonatal_mortality_rate: Optional[float]   # Por 1.000 NV
    maternal_mortality_ratio: Optional[float]  # Por 100.000 NV
    premature_mortality_rate: Optional[float]  # 30-69 anos, por 100.000

    # Composicao por grupos de causas
    cardiovascular_deaths: int
    neoplasm_deaths: int
    respiratory_deaths: int
    external_deaths: int             # Acidentes + violencia
    other_deaths: int

    # Top causas
    top_causes: list[dict]           # [{cid, desc, count, rate_per_100k}]
    avoidable_deaths: int
    avoidable_rate: float            # % do total


# ── SINASC — Sistema de Informacoes sobre Nascidos Vivos ──

@dataclass
class BirthRecord:
    """
    Registro de nascido vivo do SINASC.
    """
    municipality_code: str           # Municipio de residencia da mae
    state_code: str
    year: int
    month: Optional[int]

    total_births: int
    live_births: int                 # Nascidos vivos

    # Condicao ao nascer
    low_birth_weight: int            # < 2.500g
    very_low_birth_weight: int       # < 1.500g
    preterm: int                     # < 37 semanas
    apgar1_low: int                  # Apgar 1min < 7
    congenital_anomaly: int

    # Mae
    cesarian_births: int
    maternal_age_teen: int           # Mae < 20 anos
    maternal_age_advanced: int       # Mae >= 35 anos

    # Pre-natal
    no_prenatal: int                 # 0 consultas
    inadequate_prenatal: int         # 1-3 consultas
    adequate_prenatal: int           # 7+ consultas

    data_source: str = "SINASC/DATASUS"
    reference_period: str = ""


@dataclass
class BirthIndicators:
    """
    Indicadores de nascimentos calculados para um municipio/periodo.
    """
    municipality_code: str
    municipality_name: Optional[str]
    state_code: str
    year: int

    total_births: int
    birth_rate: Optional[float]       # Por 1.000 hab.

    # Qualidade pre-natal
    adequate_prenatal_rate: float     # % com 7+ consultas
    no_prenatal_rate: float           # % sem pre-natal

    # Condicao ao nascer
    low_birth_weight_rate: float      # % < 2.500g
    preterm_rate: float               # % prematuros
    cesarian_rate: float              # % cesareas

    # Riscos populacionais
    teen_mother_rate: float           # % maes adolescentes
    advanced_age_mother_rate: float   # % maes >= 35 anos

    # Benchmark
    benchmark_state_prenatal: Optional[float]
    benchmark_national_prenatal: Optional[float]
```

### 3.2 DataSUSMortalidadeClient

```python
class DataSUSMortalidadeClient:
    """
    Cliente para SIM — Sistema de Informacao sobre Mortalidade do DATASUS.

    API base: https://apidadosabertos.saude.gov.br/sim/
    Cache: TTL 48h (dados publicados mensalmente com defasagem)

    Nota: SIM tem defasagem de ate 18 meses para dados finais.
    Dados preliminares disponíveis em 6-12 meses.
    """

    # Obitos evitaveis — Malta et al. (2010) com atualizacao 2017
    AVOIDABLE_DEATHS = {
        "reducivel_aps": [
            "I10", "I11", "I12",  # HAS
            "E10", "E11", "E13",  # DM
            "J45", "J46",         # Asma
            "J44",                # DPOC
        ],
        "reducivel_intervencao_hospitalar": [
            "I20", "I21", "I22",  # Infarto
            "I60", "I61", "I63",  # AVC
            "N00", "N01",         # Glomerulonefrite
        ],
        "reducivel_acoes_prevencao": [
            "A33", "A34", "A35",  # Tetano
            "A36",                # Difteria
            "B05",                # Sarampo
        ],
    }

    async def get_mortality_by_municipality(
        self,
        municipality_code: str,
        year: int,
        cid_chapter: Optional[str] = None,
    ) -> list[MortalityRecord]:
        """
        Obitos por municipio de residencia.
        Cache: 48h.
        """

    async def get_mortality_indicators(
        self,
        municipality_code: str,
        year: int,
        population: Optional[int] = None,  # Usa IBGE se None
    ) -> MortalityIndicators:
        """
        Indicadores de mortalidade com taxas calculadas.

        Calcula automaticamente:
        - Taxa de mortalidade geral por 100.000 hab
        - Taxa de mortalidade infantil por 1.000 NV
        - Razao de mortalidade materna por 100.000 NV
        - Distribuicao por capitulos CID
        - % obitos evitaveis

        Cache: 48h.
        """

    async def get_infant_mortality(
        self,
        municipality_code: str,
        year: int,
    ) -> dict:
        """
        Mortalidade infantil detalhada.

        Retorna:
        {
            "infant_deaths": 12,
            "live_births": 4850,
            "infant_mortality_rate": 2.47,    # por 1.000 NV
            "neonatal_deaths": 8,
            "neonatal_rate": 1.65,
            "perinatal_deaths": 6,
            "perinatal_rate": 1.24,
            "benchmark_state": 9.1,           # Media estadual
            "benchmark_national": 12.4,       # Media nacional
            "below_sdg_target": True,         # ODS < 12 por 1.000 NV
        }
        Cache: 48h.
        """

    async def get_mortality_trend(
        self,
        municipality_code: str,
        cid_code: str,
        years: int = 5,
    ) -> dict:
        """
        Tendencia de mortalidade por causa especifica.

        Retorna serie temporal com regressao linear simples
        para identificar aumento/queda.

        Cache: 72h.
        """
```

### 3.3 DataSUSNascimentosClient

```python
class DataSUSNascimentosClient:
    """
    Cliente para SINASC — Sistema de Informacoes sobre Nascidos Vivos.

    API base: https://apidadosabertos.saude.gov.br/sinasc/
    Cache: TTL 48h

    Nota: SINASC tem defasagem menor que SIM (~3-6 meses).
    """

    # Faixas de avaliacao pre-natal (OMS / Min. Saude)
    PRENATAL_ADEQUACY = {
        "inadequate": range(0, 4),        # 0-3 consultas
        "regular": range(4, 7),           # 4-6 consultas
        "adequate": range(7, 100),        # 7+ consultas
    }

    async def get_births_by_municipality(
        self,
        municipality_code: str,
        year: int,
    ) -> BirthRecord:
        """
        Dados de nascimentos de um municipio.
        Cache: 48h.
        """

    async def get_birth_indicators(
        self,
        municipality_code: str,
        year: int,
    ) -> BirthIndicators:
        """
        Indicadores de nascimentos com taxas calculadas.

        Inclui benchmarks estadual e nacional para
        pre-natal adequado, baixo peso e prematuridade.

        Cache: 48h.
        """

    async def get_prenatal_coverage(
        self,
        municipality_code: str,
        year: int,
    ) -> dict:
        """
        Cobertura de pre-natal detalhada.

        Retorna:
        {
            "total_births": 4850,
            "no_prenatal": 48,           # 0 consultas
            "no_prenatal_rate": 0.0099,
            "inadequate": 291,           # 1-3 consultas
            "regular": 970,              # 4-6 consultas
            "adequate": 3541,            # 7+ consultas
            "adequate_rate": 0.73,
            "benchmark_state": 0.79,
            "benchmark_national": 0.72,
            "above_national": True,
        }
        Cache: 48h.
        """
```

### 3.4 VitalIndicatorsAggregator

```python
class VitalIndicatorsAggregator:
    """
    Combina SIM + SINASC + SIH para perfil epidemiologico completo.

    Usado pela LangChain Tool "get_epidemiological_profile"
    para perguntas como "qual a situacao de saude de Campinas?".
    """

    async def get_epidemiological_profile(
        self,
        municipality_code: str,
        year: int,
    ) -> dict:
        """
        Perfil epidemiologico completo.

        Agrega em paralelo:
        - MortalityIndicators (SIM)
        - BirthIndicators (SINASC)
        - HospitalizationSummary (SIH)
        - TerritorialContext (CNES)

        Resultado:
        {
            "municipality": {"code": "350950", "name": "Campinas", "state": "SP"},
            "year": 2025,
            "mortality": { ... MortalityIndicators ... },
            "births": { ... BirthIndicators ... },
            "hospitalizations": { ... HospitalizationSummary ... },
            "key_findings": [
                "Taxa de mortalidade infantil abaixo da media nacional (2.5 vs 12.4)",
                "Pre-natal adequado em 73% dos nascimentos (meta 80%)",
                "Internacoes ICSAP representam 28% do total — acima da media SP"
            ],
        }

        Cache: 4h (agrega dados de 3 fontes).
        """
```

### 3.5 Endpoints REST

```python
# SIM
# GET /datasus/sim/municipality/{code}
# Query params: year (required), cid_chapter (optional)
# Retorna: list[MortalityRecord]

# GET /datasus/sim/municipality/{code}/indicators
# Query params: year (required)
# Retorna: MortalityIndicators

# GET /datasus/sim/municipality/{code}/infant
# Query params: year (required)
# Retorna: dict com mortalidade infantil detalhada

# GET /datasus/sim/municipality/{code}/trend/{cid_code}
# Query params: years (default 5)
# Retorna: dict com serie temporal + tendencia

# SINASC
# GET /datasus/sinasc/municipality/{code}
# Query params: year (required)
# Retorna: BirthRecord

# GET /datasus/sinasc/municipality/{code}/indicators
# Query params: year (required)
# Retorna: BirthIndicators

# GET /datasus/sinasc/municipality/{code}/prenatal
# Query params: year (required)
# Retorna: dict com cobertura pre-natal

# Combinado
# GET /datasus/epidemiological-profile/municipality/{code}
# Query params: year (required)
# Retorna: perfil completo com SIM + SINASC + SIH + CNES
```

### 3.6 LangChain Tools adicionais no ZildaAgent

```python
# Adicionar ao ZildaAgent._build_tools():
Tool(
    name="get_mortality_indicators",
    description="Indicadores de mortalidade do SIM/DATASUS. Use para responder sobre "
                "taxa de mortalidade infantil, materna, por doencas especificas, "
                "obitos evitaveis ou tendencia de mortalidade em um municipio.",
    func=self._tool_get_mortality_indicators,
),
Tool(
    name="get_birth_indicators",
    description="Indicadores de nascimentos do SINASC/DATASUS. Use para informar sobre "
                "cobertura de pre-natal, taxa de baixo peso ao nascer, prematuridade, "
                "ou cesarianas em um municipio.",
    func=self._tool_get_birth_indicators,
),
Tool(
    name="get_epidemiological_profile",
    description="Perfil epidemiologico completo de um municipio: mortalidade + nascimentos "
                "+ internacoes + rede assistencial. Use para perguntas amplas como "
                "'qual e a situacao de saude do municipio X'.",
    func=self._tool_get_epidemiological_profile,
),
```

### 3.7 Configuracao

```env
# DATASUS SIM/SINASC (herdado do EF-Z003)
INTELLICARE_DATASUS_BASE_URL=https://apidadosabertos.saude.gov.br
INTELLICARE_DATASUS_CACHE_VITAL_TTL=172800   # 48h em segundos
INTELLICARE_DATASUS_ENABLED=true
```

### 3.8 Arquitetura de Arquivos

```
zilda/
  clients/
    datasus/
      __init__.py
      hospitalar.py          # EF-Z003 — SIH
      mortalidade.py         # DataSUSMortalidadeClient (SIM)
      nascimentos.py         # DataSUSNascimentosClient (SINASC)
      aggregator.py          # VitalIndicatorsAggregator
      models.py              # Todos os modelos (unificado com EF-Z003)
      fallback.py            # DataSUSFallbackStrategy (compartilhado)
      icsap.py               # Constantes ICSAP + obitos evitaveis (compartilhado)
  api/
    routes/
      datasus.py             # Todos os endpoints /datasus/...
```

## 4. Testes

- DataSUSMortalidadeClient: get_mortality, get_indicators, get_infant, get_trend (6 testes)
- DataSUSNascimentosClient: get_births, get_indicators, get_prenatal (4 testes)
- VitalIndicatorsAggregator: perfil completo, dados parciais (2 testes)
- Calculo de taxas: infantil, materna, evitaveis (4 testes)
- Endpoints: SIM, SINASC, perfil epidemiologico (5 testes)
- LangChain Tools: 3 novas tools (3 testes)
- Mock SIM/SINASC indisponivel: degradacao graceful (2 testes)
- **Total**: 26+ testes novos

## 5. Criterios de Aceitacao

- [ ] `DataSUSMortalidadeClient` com 4 metodos funcionais
- [ ] `DataSUSNascimentosClient` com 3 metodos funcionais
- [ ] `VitalIndicatorsAggregator` com perfil epidemiologico completo
- [ ] Calculo automatico de taxas (infantil, materna, pre-natal)
- [ ] 8 endpoints REST documentados e funcionais
- [ ] 3 novas LangChain Tools no ZildaAgent (total: 11 tools)
- [ ] Benchmarks estadual e nacional incluidos nas respostas
- [ ] Fallback gracioso quando SIM/SINASC indisponíveis
- [ ] 68 testes v1.0 continuam passando
- [ ] 26+ testes novos
- [ ] Cobertura >= 88%

## 6. Estimativa de Complexidade

- **Arquivos novos**: `clients/datasus/mortalidade.py`, `clients/datasus/nascimentos.py`, `clients/datasus/aggregator.py`, atualizacoes em `models.py` e `icsap.py`
- **Arquivos modificados**: `subagent/tools.py` (3 tools novas), `api/routes/datasus.py` (5 rotas novas)
- **Linhas estimadas**: ~500
- **Testes novos**: ~26

## 7. Notas de Implementacao

### Defasagem de dados

SIM e SINASC tem publicacao com defasagem significativa:
- **SIM**: dados preliminares ~6 meses, definitivos ~18 meses apos ocorrencia
- **SINASC**: dados mais rapidos, ~3-6 meses

O cliente deve sempre informar qual ano de dados esta sendo usado:
```python
# Em ZildaAnalysis.metadata:
{
    "data_source": "SIM/DATASUS",
    "year_requested": 2026,
    "year_available": 2024,   # Ultimo ano com dados
    "data_lag_warning": "Dados do SIM com defasagem tipica de 12-18 meses"
}
```

### Privacidade

Dados do SIM contem informacoes sensíveis. A Zilda NUNCA expoe:
- Dados individuais (cada obito tem identificacao)
- O cliente recebe apenas dados agregados por municipio/CID
- Nao armazenar payload bruto da API — apenas modelos calculados
