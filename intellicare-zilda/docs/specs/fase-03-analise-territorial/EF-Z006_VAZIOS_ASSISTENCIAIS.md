# EF-Z006 — Motor de Vazios Assistenciais

> Identificar regioes e municipios com cobertura insuficiente para servicos especificos, calculando a distancia ao servico mais proximo e a populacao afetada por cada vazio.

## 1. Objetivo

Implementar o motor de analise de vazios assistenciais, permitindo que a Zilda responda:

- "Onde ha municipios sem acesso a hemodialise em um raio de 100km?"
- "Quais municipios da regiao de saude de Ribeirao Preto nao tem UTI no SUS?"
- "Qual a populacao sem acesso a oncologia em SP?"
- "O paciente em Amparo/SP tem alguma UPA num raio de 30km?"
- "Quais regioes de saude tem 'deserto de especialistas' em cardiologia?"

## 2. Justificativa

- **Gap critico**: Analise de vazios 0% implementada na v1.0.0
- **Encaminhamento critico**: Wanda e Florence precisam saber se existe servico disponivel antes de encaminhar
- **Planejamento assistencial**: Gestores precisam identificar onde investir
- **Pacientes cronicos**: Oswaldo precisa saber se paciente tem dialise acessivel para planejar tratamento IRC
- **Nao existe API direta**: precisa ser calculado localmente combinando CNES + IBGE geocodificacao

## 3. Escopo

### 3.1 Modelos de Dados

```python
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class VoidSeverity(str, Enum):
    CRITICAL = "critical"    # Servico vital sem oferta na regiao inteira
    HIGH = "high"            # Servico vital distante > 100km
    MEDIUM = "medium"        # Servico importante distante 50-100km
    LOW = "low"              # Servico disponivel mas acima do padrao


@dataclass
class ServiceVoid:
    """
    Vazio assistencial identificado — ausencia ou insuficiencia de servico.
    """
    void_id: str                        # UUID gerado localmente
    municipality_code: str
    municipality_name: Optional[str]
    state_code: str

    # Servico faltante
    service_code: str                   # Codigo CNES do servico
    service_name: str                   # Ex: "Hemodialise", "UTI Adulto"
    service_description: str

    # Disponibilidade
    is_completely_absent: bool          # True = nao existe no municipio
    is_insufficient: bool               # True = existe mas abaixo do minimo
    sus_only_void: bool                 # True = existe particular, nao no SUS

    # Acesso ao mais proximo
    nearest_establishment_cnes: Optional[str]
    nearest_establishment_name: Optional[str]
    nearest_municipality: Optional[str]
    distance_km: Optional[float]        # Distancia em linha reta

    # Impacto
    affected_population: int
    severity: VoidSeverity

    # Benchmark
    min_establishments_per_100k: Optional[float]  # Padrao MS
    current_per_100k: float

    calculated_at: str                  # ISO timestamp


@dataclass
class RegionalVoidAnalysis:
    """
    Analise de vazios para uma regiao de saude.
    """
    region_name: str
    state_code: str
    region_municipalities: list[str]
    total_population: int

    voids: list[ServiceVoid]
    critical_voids_count: int
    high_voids_count: int

    # Municipios sem acesso a servicos criticos
    municipalities_without_dialysis: list[str]
    municipalities_without_icu: list[str]
    municipalities_without_emergency: list[str]  # UPA/UPAS/PS 24h

    # Populacao sem acesso
    population_without_dialysis: int
    population_without_icu: int
    population_without_adequate_prenatal: int

    recommendations: list[str]         # Acoes sugeridas para gestor


@dataclass
class PatientAccessAnalysis:
    """
    Analise de acesso de um paciente especifico a servicos necessarios.

    Usado pelo Oswaldo/Geralda: "O paciente X tem dialise acessivel?"
    """
    patient_city: str
    patient_state: str

    needed_services: list[str]          # Servicos requeridos pelo diagnostico
    access_results: list[dict]          # Resultado por servico:
    # {
    #     "service": "Hemodialise",
    #     "has_local_access": False,
    #     "nearest_establishment": "Hospital Estadual de Campinas",
    #     "nearest_city": "Campinas",
    #     "distance_km": 47.3,
    #     "sus_available": True,
    #     "access_summary": "Hemodialise SUS disponivel em Campinas (47km)"
    # }

    overall_access_score: float         # 0.0 (sem acesso) - 1.0 (tudo local)
    has_critical_void: bool             # True = servico vital inacessivel
    recommendations: list[str]
```

### 3.2 VoidAnalysisEngine

```python
class VoidAnalysisEngine:
    """
    Motor de identificacao de vazios assistenciais.

    Estrategia de calculo:
    1. Para cada servico critico (dialise, UTI, etc.):
       a. Verificar se existe no municipio (CNES)
       b. Se nao, calcular distancia ate municipio mais proximo com o servico
       c. Classificar severidade por distancia e criticidade do servico
    2. Agregar por regiao de saude

    Distancia: calculada por formula haversine (lat/lon IBGE).
    Nao usa Google Maps — apenas coords municipio-a-municipio.

    Cache: 8h (analise computacionalmente cara).
    """

    # Servicos criticos e seus codigos CNES
    CRITICAL_SERVICES = {
        "117": ServiceDefinition(
            name="Hemodialise",
            description="Tratamento renal substitutivo",
            max_acceptable_km=100,         # Acima disso = vazio critico
            warning_km=50,                 # Acima disso = vazio alto
            min_per_100k_pop=None,         # Nao ha padrao fixo
            is_life_sustaining=True,        # Obrigatorio para IRC
        ),
        "100": ServiceDefinition(
            name="UTI Adulto",
            description="Unidade de Terapia Intensiva adulto",
            max_acceptable_km=100,
            warning_km=50,
            min_per_100k_pop=2.5,           # Padrao MS: 2.5 leitos UTI / 10k hab
            is_life_sustaining=True,
        ),
        "101": ServiceDefinition(
            name="UTI Neonatal",
            description="UTI para recém-nascidos",
            max_acceptable_km=150,
            warning_km=75,
            min_per_100k_pop=None,
            is_life_sustaining=True,
        ),
        "102": ServiceDefinition(
            name="UTI Pediatrica",
            description="UTI para criancas",
            max_acceptable_km=150,
            warning_km=75,
            min_per_100k_pop=None,
            is_life_sustaining=True,
        ),
        "158": ServiceDefinition(
            name="Atendimento a Diabetico",
            description="Tratamento especializado para diabetes",
            max_acceptable_km=50,
            warning_km=30,
            min_per_100k_pop=None,
            is_life_sustaining=False,
        ),
        "159": ServiceDefinition(
            name="Atendimento a Hipertenso",
            description="Tratamento especializado para hipertensao",
            max_acceptable_km=50,
            warning_km=30,
            min_per_100k_pop=None,
            is_life_sustaining=False,
        ),
        "PS_24H": ServiceDefinition(
            name="Pronto Socorro 24h",
            description="Urgencia e emergencia",
            max_acceptable_km=30,
            warning_km=15,
            min_per_100k_pop=None,
            is_life_sustaining=True,
        ),
        "QUIMIO": ServiceDefinition(
            name="Quimioterapia",
            description="Tratamento oncologico",
            max_acceptable_km=100,
            warning_km=50,
            min_per_100k_pop=None,
            is_life_sustaining=False,
        ),
    }

    def __init__(
        self,
        cnes_client: "CnesClient",
        ibge_client: "IBGEClient",
        cache_manager,
    ):
        self._cnes = cnes_client
        self._ibge = ibge_client
        self._cache = cache_manager

    async def analyze_municipality_voids(
        self,
        municipality_code: str,
        services: Optional[list[str]] = None,  # None = todos os criticos
    ) -> list[ServiceVoid]:
        """
        Identifica vazios assistenciais em um municipio.

        Para cada servico:
        1. Verifica presenca local (CNES)
        2. Verifica disponibilidade SUS (nao apenas particular)
        3. Se ausente, calcula distancia ao mais proximo usando haversine

        Cache: 8h.
        """

    async def analyze_patient_access(
        self,
        municipality_code: str,
        needed_services: list[str],         # ["117", "158"] para IRC + DM
    ) -> PatientAccessAnalysis:
        """
        Analisa acesso de paciente em um municipio a servicos necessarios.

        Usado pelo Oswaldo para planejar encaminhamentos.

        Cache: 4h.
        """

    async def analyze_regional_voids(
        self,
        municipality_codes: list[str],
        region_name: str,
    ) -> RegionalVoidAnalysis:
        """
        Analise completa de vazios de uma regiao de saude.

        Processa todos os municipios em paralelo.
        Agrega resultados e identifica padroes regionais.

        Cache: 8h.
        """

    def _calculate_distance_km(
        self,
        lat1: float, lon1: float,
        lat2: float, lon2: float,
    ) -> float:
        """
        Distancia haversine em km entre dois pontos.

        Nota: distancia em linha reta (crow flies).
        Nao considera estradas — pode subestimar tempo real.
        A Zilda sempre avisa isso nas respostas.
        """
        import math
        R = 6371
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)
        a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
        return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

    async def _find_nearest_with_service(
        self,
        from_municipality: str,
        service_code: str,
        max_search_km: float = 200,
    ) -> Optional[tuple[str, str, float]]:
        """
        Encontra municipio mais proximo com servico especifico.

        Retorna: (municipio_code, cnes_code, distancia_km) ou None.

        Estrategia:
        1. Pega coords do municipio origem (IBGE)
        2. Pega todos os municipios do estado com o servico (CNES)
        3. Calcula distancia haversine para cada um
        4. Retorna o mais proximo dentro do limite

        Cache: 24h (dados de localizacao mudam pouco).
        """
```

### 3.3 IBGEClient (auxiliar para geocodificacao)

```python
class IBGEClient:
    """
    Cliente para IBGE API — coordenadas e populacao dos municipios.

    API: https://servicodados.ibge.gov.br/api/v1/localidades/municipios
    Cache: 7 dias (dados mudam apenas a cada censo/estimativa anual)
    """

    async def get_municipality_coordinates(
        self,
        municipality_code: str,
    ) -> tuple[float, float]:  # (lat, lon)
        """
        Coordenadas do centroide do municipio.
        Cache: 7 dias.
        """

    async def get_municipality_population(
        self,
        municipality_code: str,
        year: Optional[int] = None,  # None = mais recente
    ) -> int:
        """
        Populacao estimada do municipio.
        Cache: 24h.
        """

    async def get_region_municipalities(
        self,
        state_code: str,
        health_region_code: Optional[str] = None,
    ) -> list[dict]:  # [{code, name, lat, lon}]
        """
        Municipios de um estado ou regiao de saude.
        Cache: 7 dias.
        """
```

### 3.4 Endpoints REST

```python
# GET /voids/municipality/{code}
# Query params: services (lista, default = todos criticos)
# Retorna: list[ServiceVoid]

# GET /voids/municipality/{code}/patient-access
# Body: {needed_services: ["117", "158"]}
# Retorna: PatientAccessAnalysis

# GET /voids/region
# Body: {municipality_codes: [...], region_name: "..."}
# Retorna: RegionalVoidAnalysis

# GET /voids/service/{service_code}
# Query params: state_code (required), max_km (default 100)
# Retorna: list de municipios com vazio para este servico no estado
```

### 3.5 LangChain Tools no ZildaAgent

```python
# Adicionar ao ZildaAgent._build_tools():
Tool(
    name="analyze_service_void",
    description="Identifica vazios assistenciais em um municipio — servicos de saude "
                "ausentes ou inacessiveis. Use para perguntas como 'tem dialise perto', "
                "'ha UTI SUS no municipio', 'onde fica o pronto socorro mais proximo'. "
                "Calcula distancia ao servico mais proximo quando ausente localmente.",
    func=self._tool_analyze_service_void,
),
Tool(
    name="analyze_patient_access",
    description="Analisa acesso de um paciente a servicos necessarios para seu diagnostico. "
                "Use quando Oswaldo ou Florence perguntarem sobre disponibilidade de servico "
                "para encaminhamento especifico. Retorna summary de acesso e distancias.",
    func=self._tool_analyze_patient_access,
),
```

### 3.6 Configuracao

```env
INTELLICARE_VOID_ANALYSIS_CACHE_TTL=28800  # 8h
INTELLICARE_VOID_MAX_SEARCH_KM=200         # Raio maximo de busca do mais proximo
INTELLICARE_IBGE_CACHE_TTL=604800          # 7 dias para coords
```

### 3.7 Arquitetura de Arquivos

```
zilda/
  analysis/
    __init__.py
    voids.py               # VoidAnalysisEngine
    service_definitions.py # CRITICAL_SERVICES + ServiceDefinition
  clients/
    ibge.py                # IBGEClient (geocodificacao + populacao)
  api/
    routes/
      voids.py             # Endpoints /voids/...
```

## 4. Testes

- VoidAnalysisEngine: municipio com/sem servico, calcular distancia (5 testes)
- PatientAccessAnalysis: paciente com acesso, sem acesso critico (3 testes)
- RegionalVoidAnalysis: agregacao regional, contagem criticos (3 testes)
- Haversine: calculo de distancia entre pares conhecidos (2 testes)
- IBGEClient: coords, populacao (3 testes)
- Endpoints (4 testes)
- LangChain Tools (2 testes)
- Sem coordenadas IBGE: fallback gracioso (1 teste)
- **Total**: 23+ testes novos

## 5. Criterios de Aceitacao

- [ ] `VoidAnalysisEngine` com 3 metodos principais
- [ ] 8 servicos criticos mapeados com parametros de severidade
- [ ] Calculo haversine correto (validado com pares conhecidos)
- [ ] `PatientAccessAnalysis` retorna acesso por servico com distancia
- [ ] `RegionalVoidAnalysis` agrega municipios em paralelo
- [ ] `IBGEClient` com coordenadas e populacao
- [ ] 4 endpoints REST funcionais
- [ ] 2 novas LangChain Tools no ZildaAgent
- [ ] Aviso explicito de "distancia em linha reta" nas respostas
- [ ] 68 testes v1.0 continuam passando
- [ ] 23+ testes novos
- [ ] Cobertura >= 87%

## 6. Estimativa de Complexidade

- **Arquivos novos**: `analysis/voids.py`, `analysis/service_definitions.py`, `clients/ibge.py`, `api/routes/voids.py`
- **Arquivos modificados**: `subagent/tools.py` (2 tools), `api/app.py`
- **Linhas estimadas**: ~500
- **Testes novos**: ~23

## 7. Notas de Implementacao

### Distancia em linha reta

A Zilda SEMPRE avisa que a distancia e calculada em linha reta (haversine), nao por estradas. Para regioes com Serra, rios ou estradas ruins (ex: interior do Amazonas), a distancia real pode ser significativamente maior.

Texto padrao incluido na resposta:
> "Distancia calculada em linha reta. A distancia real por estrada pode ser maior, especialmente em regioes serranas ou com infraestrutura viaria limitada."

### Servico SUS vs. Particular

A Zilda distingue:
- `is_completely_absent`: servico nao existe no municipio (SUS nem particular)
- `sus_only_void`: existe particular mas nao no SUS

Para pacientes SUS, `sus_only_void=True` e um vazio real. A resposta deve diferenciar claramente.
