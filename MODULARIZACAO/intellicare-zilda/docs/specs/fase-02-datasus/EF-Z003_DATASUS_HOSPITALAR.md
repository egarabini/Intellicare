# EF-Z003 — DATASUS Producao Hospitalar (SIH)

> Integrar dados do Sistema de Informacoes Hospitalares (SIH) do DATASUS para fornecer indicadores de internacoes por municipio, CID e procedimento.

## 1. Objetivo

Implementar cliente DATASUS para dados de producao hospitalar (SIH), permitindo que a Zilda responda perguntas como:

- "Quantas internacoes por insuficiencia cardiaca ocorreram em Campinas no ultimo ano?"
- "Qual a taxa de internacao por DM2 na regiao de saude de Ribeirao Preto?"
- "Quais os principais CIDs de internacao em municipios de SP com alta prevalencia de IRC?"

## 2. Justificativa

- **Gap critico**: DATASUS 0% implementado na v1.0.0 (identificado no gap analysis)
- **Contexto clinico**: Internacoes por CID revelam carga de doenca real do territorio
- **Oswaldo/Florence precisam**: dados de hospitalizacao para calcular risco e planejar encaminhamentos
- **Wanda necessita**: para queries como "quantas internacoes evitaveis por HAS houve aqui?"
- **SIH e publico**: Ministerio da Saude disponibiliza via API REST — sem scraping

## 3. Escopo

### 3.1 Modelos de Dados

```python
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class HospitalizationRecord:
    """
    Registro de internacao do SIH.
    """
    municipality_code: str
    state_code: str
    year: int
    month: Optional[int]             # None = dados anuais

    cid_code: str                    # CID-10 primario
    cid_description: Optional[str]

    # Totais
    total_admissions: int            # AIHs aprovadas
    total_days: int                  # Total de diarias
    total_deaths: int                # Obitos hospitalares
    total_value_brl: float           # Valor total pago pelo SUS

    # Medias calculadas
    avg_length_of_stay: float        # total_days / total_admissions
    in_hospital_mortality_rate: float  # total_deaths / total_admissions

    # Faixa etaria (se disponivel)
    age_group: Optional[str]         # "0-4", "5-14", "15-44", "45-64", "65+"

    # Metadados
    data_source: str = "SIH/DATASUS"
    reference_period: str = ""       # "2025-01" ou "2025"
    cache_key: str = ""


@dataclass
class HospitalizationSummary:
    """
    Sumario de internacoes por municipio/periodo — visao agregada.
    """
    municipality_code: str
    municipality_name: Optional[str]
    state_code: str
    year: int

    total_admissions: int
    total_days: int
    total_deaths: int
    total_value_brl: float

    mortality_rate: float            # Obitos / total
    avg_length_of_stay: float

    top_cids: list[dict]             # [{cid: "I50", desc: "...", count: 430}, ...]
    avoidable_admissions: int        # Internacoes sensíveis a APS
    avoidable_rate: float            # % do total


@dataclass
class RegionalHospitalizationData:
    """
    Dados de internacao para uma regiao de saude.
    """
    region_code: str
    region_name: str
    state_code: str
    year: int
    municipalities: list[str]        # Codigos IBGE dos municipios

    aggregated_admissions: int
    top_cids_region: list[dict]
    comparison_to_state_avg: dict    # {cid: ratio_vs_state}
    high_burden_municipalities: list[dict]  # Municipios acima da media
```

### 3.2 DataSUSHospitalarClient

```python
class DataSUSHospitalarClient:
    """
    Cliente para SIH — Sistema de Informacoes Hospitalares do DATASUS.

    API base: https://apidadosabertos.saude.gov.br/sih/
    Documentacao: https://datasus.saude.gov.br/acesso-informacao/producao-hospitalar-sih-sus/

    Cache:
    - Dados mensais: TTL 24h (nao mudam apos publicacao)
    - Dados anuais: TTL 72h
    - Dados de regiao: TTL 6h (agregacao local)
    """

    BASE_URL = "https://apidadosabertos.saude.gov.br/sih"

    # CIDs sensíveis a APS (internacoes evitaveis por doencas cronicas)
    # Fonte: Portaria MS 2.027/2011 — Lista Brasileira de Internacoes por
    #        Condicoes Sensiveis a Atencao Primaria (ICSAP)
    ICSAP_CIDS = {
        # Doencas preventíveis por vacinacao
        "A33": "Tetano neonatal",
        "A34": "Tetano obstétrico",
        "A35": "Outros tetanos",
        "A36": "Difteria",
        # HAS e complicacoes
        "I10": "Hipertensao essencial",
        "I11": "Doenca cardiaca hipertensiva",
        "I12": "Doenca renal hipertensiva",
        "I50": "Insuficiencia cardiaca",
        # Diabetes
        "E10": "DM tipo 1 — cetoacidose",
        "E11": "DM tipo 2 — cetoacidose",
        "E140": "DM com coma",
        # IRC/Dialise
        "N18": "Doenca renal cronica",
        "N19": "Insuficiencia renal nao especificada",
        # Asma e DPOC
        "J45": "Asma",
        "J46": "Estado de mal asmatico",
        "J44": "DPOC",
        # Pneumonia (bacteriana)
        "J13": "Pneumonia por Streptococcus",
        "J14": "Pneumonia por Haemophilus",
        "J15": "Pneumonia bacteriana",
        "J18": "Pneumonia por microrganismo nao especificado",
    }

    def __init__(self, http_client, cache_manager):
        self._http = http_client
        self._cache = cache_manager

    async def get_admissions_by_municipality(
        self,
        municipality_code: str,
        year: int,
        month: Optional[int] = None,
        cid_chapter: Optional[str] = None,  # Ex: "IX" = Aparelho Circulatorio
    ) -> list[HospitalizationRecord]:
        """
        Internacoes de um municipio por periodo.

        Params:
            municipality_code: Codigo IBGE (6 digitos)
            year: Ano de referencia (min 2010)
            month: Mes (1-12) ou None para dados anuais
            cid_chapter: Filtrar por capitulo do CID-10

        Cache: 24h para mensal, 72h para anual.
        """

    async def get_hospitalization_summary(
        self,
        municipality_code: str,
        year: int,
    ) -> HospitalizationSummary:
        """
        Sumario completo de internacoes com ranking de CIDs.

        Calcula automaticamente:
        - Top 10 CIDs por volume
        - Taxa de internacoes evitaveis (ICSAP)
        - Mortalidade hospitalar geral
        - Tempo medio de permanencia

        Cache: 24h.
        """

    async def get_admissions_by_cid(
        self,
        municipality_code: str,
        cid_code: str,
        years: list[int],
    ) -> list[HospitalizationRecord]:
        """
        Serie historica de internacoes por CID especifico.

        Util para responder:
        "Quantas internacoes por IRC em Campinas nos ultimos 5 anos?"

        Cache: 72h (dados historicos nao mudam).
        """

    async def get_regional_admissions(
        self,
        region_municipalities: list[str],
        year: int,
    ) -> RegionalHospitalizationData:
        """
        Agrega internacoes para uma lista de municipios (regiao de saude).

        Compara cada CID com media estadual para identificar
        burden especifico da regiao.

        Processamento local — agrega resultados de get_hospitalization_summary()
        de cada municipio.

        Cache: 6h.
        """

    async def get_avoidable_admissions(
        self,
        municipality_code: str,
        year: int,
    ) -> dict:
        """
        Internacoes sensiveis a APS (lista ICSAP).

        Retorna:
        {
            "total_icsap": 1243,
            "icsap_rate": 0.28,         # % do total de internacoes
            "top_icsap_cids": [
                {"cid": "I50", "desc": "Insuf. Cardiaca", "count": 432, "rate": 0.09}
            ],
            "benchmark_national_avg": 0.26,  # Media nacional
            "above_benchmark": True,
        }

        Cache: 24h.
        """

    async def _call_api(
        self,
        endpoint: str,
        params: dict,
    ) -> dict:
        """
        Chama API DATASUS com tratamento de erros e retry.

        Estrategia de fallback:
        1. Tenta API REST principal
        2. Se indisponivel: retorna dados em cache stale (ate 7 dias)
        3. Se sem cache: retorna None com flag data_unavailable=True

        NUNCA falha o request — degradacao graceful.
        """
```

### 3.3 Endpoints REST

```python
# GET /datasus/sih/municipality/{code}
# Query params: year (required), month (optional), cid_chapter (optional)
# Retorna: list[HospitalizationRecord]

# GET /datasus/sih/municipality/{code}/summary
# Query params: year (required)
# Retorna: HospitalizationSummary

# GET /datasus/sih/municipality/{code}/avoidable
# Query params: year (required)
# Retorna: dict com ICSAP breakdown

# GET /datasus/sih/municipality/{code}/cid/{cid_code}
# Query params: years (lista, default [ano_atual-1, ano_atual])
# Retorna: list[HospitalizationRecord] — serie historica

# GET /datasus/sih/region
# Body: {municipality_codes: [...], year: 2025}
# Retorna: RegionalHospitalizationData

# GET /datasus/sih/municipality/{code}/trend
# Calcula tendencia de internacoes (ultimos 3 anos)
# Retorna: {trend: "increasing"/"stable"/"decreasing", slope: 0.12}
```

### 3.4 Integracao com Ferramentas LangChain (Zilda Subagente)

```python
# Adicionar ao ZildaAgent._build_tools():
Tool(
    name="get_hospitalization_data",
    description="Dados de internacoes hospitalares do SIH/DATASUS por municipio e CID. "
                "Use para responder quantas internacoes por doenca especifica ou taxa "
                "de internacoes evitaveis em um municipio. Requer municipio e ano.",
    func=self._tool_get_hospitalization_data,
),
Tool(
    name="get_avoidable_admissions",
    description="Internacoes sensiveis a APS (ICSAP) — indica qualidade da atencao basica. "
                "Use quando perguntarem sobre internacoes evitaveis, qualidade APS, "
                "impacto ESF na reducao de hospitalizacoes.",
    func=self._tool_get_avoidable_admissions,
),
```

### 3.5 Tratamento de Limitacoes da API DATASUS

```python
class DataSUSFallbackStrategy:
    """
    Dados do DATASUS podem ter atraso de ate 6 meses (publicacao mensal atrasada).

    Estrategia:
    1. Tentar ano atual -> se sem dados, tentar ano-1 -> ano-2
    2. Informar ao usuario qual periodo esta disponivel
    3. Para dados de tendencia: usar serie 3-5 anos

    Exemplo de resposta quando dados nao disponíveis:
    "Dados de internacao para 2026 ainda nao publicados pelo DATASUS.
     Usando dados de 2025 (ultimo periodo disponivel)."
    """

    MAX_RETRY_YEARS = 3   # Tenta ate 3 anos atras

    async def get_most_recent_available(
        self,
        client: DataSUSHospitalarClient,
        municipality_code: str,
        target_year: int,
    ) -> tuple[HospitalizationSummary, int]:
        """
        Tenta ano alvo, regride se necessario.
        Retorna (dados, ano_efetivo).
        """
```

### 3.6 Configuracao

```env
# DATASUS
INTELLICARE_DATASUS_BASE_URL=https://apidadosabertos.saude.gov.br
INTELLICARE_DATASUS_TIMEOUT=30
INTELLICARE_DATASUS_RETRY_ATTEMPTS=3
INTELLICARE_DATASUS_CACHE_MONTHLY_TTL=86400    # 24h em segundos
INTELLICARE_DATASUS_CACHE_ANNUAL_TTL=259200    # 72h em segundos
INTELLICARE_DATASUS_ENABLED=true
```

### 3.7 Arquitetura de Arquivos

```
zilda/
  clients/
    datasus/
      __init__.py
      hospitalar.py          # DataSUSHospitalarClient
      models.py              # HospitalizationRecord, HospitalizationSummary, etc.
      fallback.py            # DataSUSFallbackStrategy
      icsap.py               # Constantes e logica ICSAP
  api/
    routes/
      datasus.py             # Endpoints /datasus/sih/...
```

## 4. Testes

- DataSUSHospitalarClient: init, get_admissions, get_summary, get_avoidable (6 testes)
- Calculo ICSAP: identificar CIDs, taxa correta (3 testes)
- DataSUSFallbackStrategy: ano disponivel, fallback ano-1, todos indisponiveis (3 testes)
- Endpoints REST: summary, avoidable, serie historica (4 testes)
- Integracao com ferramentas LangChain: tool retorna formato esperado (2 testes)
- Mock API DATASUS indisponivel: degradacao graceful (2 testes)
- **Total**: 20+ testes novos

## 5. Criterios de Aceitacao

- [ ] `DataSUSHospitalarClient` com 5 metodos funcionais
- [ ] Cache com TTLs corretos (24h mensal, 72h anual)
- [ ] Lista ICSAP com 20+ CIDs sensiveis a APS
- [ ] Calculo automatico de taxa de internacoes evitaveis
- [ ] 5 endpoints REST documentados
- [ ] 2 novas LangChain Tools registradas no ZildaAgent
- [ ] Fallback gracioso quando DATASUS indisponivel
- [ ] 68 testes v1.0 continuam passando
- [ ] 20+ testes novos
- [ ] Cobertura >= 88%

## 6. Estimativa de Complexidade

- **Arquivos novos**: `clients/datasus/hospitalar.py`, `clients/datasus/models.py`, `clients/datasus/fallback.py`, `clients/datasus/icsap.py`, `api/routes/datasus.py`
- **Arquivos modificados**: `subagent/tools.py` (2 tools novas), `api/app.py` (registrar rotas), `config.py`
- **Linhas estimadas**: ~450
- **Testes novos**: ~20
