# EF-D005 — Equidade e Estratificacao Demografica

> Implementar analise de equidade assistencial — o pilar mais fraco do Donabedian (4/10) — identificando disparidades no acesso e nos resultados por raca, faixa etaria, genero e regiao geografica.

## 1. Objetivo

Transformar o pilar Equidade de "conceitual" em "analitico", permitindo que gestores respondam:

- "Pacientes de baixa renda tem os mesmos resultados que os de alta renda?"
- "Ha diferenca na mortalidade hospitalar entre pacientes brancos e negros?"
- "Pacientes de municipios rurais tem acesso igual ao de centros urbanos?"
- "Idosos recebem o mesmo tempo de atendimento que pacientes jovens?"

## 2. Justificativa

- Equidade e o pilar com menor implementacao (4/10) — apenas conceitual
- LGPD permite analise estratificada para fins de saude publica (anonimizada e agregada)
- ANS cobra indicadores de equidade desde 2023 (Resolucao Normativa 560/2022)
- Sem equidade, o score de qualidade mascara disparidades criticas

## 3. Escopo

### 3.1 Dimensoes de Estratificacao

```python
from dataclasses import dataclass
from typing import Optional
from enum import Enum


class StratificationDimension(str, Enum):
    RACE = "raca"                        # Branca, Preta, Parda, Amarela, Indigena (IBGE)
    AGE_GROUP = "faixa_etaria"           # <1, 1-4, 5-14, 15-29, 30-44, 45-59, 60-74, 75+
    SEX = "sexo"                         # M / F
    GEOGRAPHY = "regiao"                 # Urbano/Rural, Municipio, Regiao de Saude
    INCOME = "renda"                     # Quartis de renda per capita (dado do IBGE municipio)
    INSURANCE = "plano"                  # SUS / Plano / Particular


@dataclass
class StratifiedIndicator:
    """
    Valor de um indicador estratificado por uma dimensao demografica.
    """
    indicator_id: str
    indicator_name: str
    period_start: str
    period_end: str

    dimension: StratificationDimension
    strata: dict[str, float]             # Ex: {"Preta": 5.2, "Branca": 2.1, "Parda": 3.8}

    # Analise de disparidade
    max_stratum: str                     # Estrato com pior resultado
    min_stratum: str                     # Estrato com melhor resultado
    disparity_ratio: float               # max/min (1.0 = equidade total)
    disparity_status: str                # "equitativo", "leve", "moderado", "grave"

    # Significancia
    has_significant_disparity: bool      # disparity_ratio > 1.5 = significativa
    reference_stratum: str               # Estrato de referencia para comparacao


@dataclass
class EquityReport:
    """
    Relatorio de equidade para um periodo.
    """
    period_start: str
    period_end: str

    # Score de equidade (0-100, 100 = equidade total)
    equity_score: float

    # Por dimensao
    disparities_by_dimension: dict[str, list[StratifiedIndicator]]

    # Indicadores mais desiguais
    most_inequitable_indicators: list[dict]   # Top 5 com maior disparity_ratio
    critical_disparities: list[dict]          # disparity_ratio > 2.0

    # Grupos mais vulneraveis
    most_affected_groups: list[dict]          # {dimension, stratum, indicators_affected}

    recommendations: list[str]
```

### 3.2 EquityAnalysisEngine

```python
class EquityAnalysisEngine:
    """
    Motor de analise de equidade.

    Limitacao importante: o Donabedian so pode analisar equidade se as medicoes
    forem registradas com estratificacao demografica. Sem esses dados, analise
    e impossivel.

    Fontes de dados estratificados:
    1. Medicoes com campo 'stratification_data' (JSON) — novo campo no schema
    2. Dados do DATASUS via Zilda (SIH tem campo raca/etnia desde 2017)
    3. Dados populacionais do IBGE via Zilda (para calcular taxas ajustadas)
    """

    def calculate_equity_score(
        self,
        stratified_indicators: list[StratifiedIndicator],
    ) -> float:
        """
        Score de equidade de 0-100.

        Algoritmo:
        - Para cada indicador estratificado: calcula disparity_ratio
        - Pesos por severidade da disparidade:
          disparity_ratio < 1.2 = 100 (equitativo)
          1.2-1.5 = 75 (leve)
          1.5-2.0 = 40 (moderado)
          > 2.0 = 0 (grave)
        - Media ponderada pelo peso do indicador nos pilares

        Score 0 = disparidade extrema em todos os indicadores
        Score 100 = equidade total
        """

    def classify_disparity(
        self,
        disparity_ratio: float,
    ) -> str:
        """
        Classifica disparidade.
        < 1.2: equitativo
        1.2-1.5: leve
        1.5-2.0: moderado
        > 2.0: grave (requer acao imediata)
        """

    async def analyze_by_race(
        self,
        indicator_id: str,
        period_start: str,
        period_end: str,
    ) -> Optional[StratifiedIndicator]:
        """
        Analise de equidade racial para um indicador.

        Busca medicoes com campo stratification_data.race_color.
        Se nao ha dados: retorna None (nao inventa dados).
        """

    async def analyze_by_geography(
        self,
        indicator_id: str,
        period_start: str,
        period_end: str,
    ) -> Optional[StratifiedIndicator]:
        """
        Analise geografica: urbano vs. rural, municipios vs. capital.
        """

    async def generate_equity_report(
        self,
        period_start: str,
        period_end: str,
    ) -> EquityReport:
        """
        Relatorio completo de equidade.
        Analisa todas as dimensoes para todos os indicadores com dados estratificados.
        """
```

### 3.3 Extensao do Schema de Medicoes

```python
# Adicionar campo opcional ao modelo Measurement:
# stratification_data: Optional[JSON] — dados demograficos da medicao

# Exemplo de stratification_data:
{
    "dimension": "raca",
    "strata": {
        "Branca": 2.1,
        "Preta": 5.8,
        "Parda": 4.2,
        "Amarela": 2.9,
        "Indigena": 6.1
    },
    "total_n": 1240,              # Total de casos
    "source": "SIH-DATASUS"
}
```

### 3.4 Endpoints REST Novos

```python
# GET /api/v1/equity/summary
# Query params: period_start, period_end
# Retorna: EquityReport com score e principais disparidades

# GET /api/v1/equity/indicator/{indicator_id}
# Query params: period_start, period_end, dimension (raca/faixa_etaria/sexo/regiao)
# Retorna: StratifiedIndicator com disparidade calculada

# GET /api/v1/equity/dimensions
# Retorna: dimensoes disponiveis e indicadores com dados estratificados

# POST /api/v1/measurements/{id}/stratification
# Body: stratification_data (adiciona dados demograficos a uma medicao existente)
# Retorna: Measurement atualizada
```

### 3.5 Dashboard — Nova Pagina de Equidade

```
dashboard/pages/
  5_⚖️_Equidade.py              # Nova pagina de equidade
    - Score de equidade (gauge chart)
    - Mapa de calor: indicadores vs dimensoes demograficas
    - Top disparidades com disparity_ratio
    - Grupos mais afetados (lista com acao recomendada)
```

### 3.6 Nota Etica

O Donabedian analisa equidade de forma **anonimizada e agregada**:
- Nunca identifica individuos
- Analisa apenas distribuicoes populacionais
- Conforme LGPD Art. 13 (dados anonimizados para fins de saude publica)
- Conforme Res. CFM 2.217/2018 (pesquisa com dados secundarios)

Toda interface inclui aviso:
> "Analise baseada em dados anonimizados e agregados. Uso restrito a fins de melhoria de qualidade assistencial."

## 4. Testes

- EquityAnalysisEngine: calculo de score, classificacao de disparidade (4 testes)
- StratifiedIndicator: disparity_ratio correto (2 testes)
- analyze_by_race: com dados, sem dados (2 testes)
- generate_equity_report: report completo (2 testes)
- Endpoints: summary, indicator, dimensions, stratification (4 testes)
- **Total**: 14+ testes novos

## 5. Criterios de Aceitacao

- [ ] `EquityAnalysisEngine` com 4 metodos principais
- [ ] Score de equidade de 0-100 com formula documentada
- [ ] Classificacao de disparidade (equitativo/leve/moderado/grave)
- [ ] Campo `stratification_data` adicionado ao modelo Measurement
- [ ] 4 endpoints REST funcionais
- [ ] Nova pagina Equidade no dashboard Streamlit
- [ ] Aviso etico/LGPD em todas as interfaces
- [ ] 363 testes v1.0 continuam passando
- [ ] 14+ testes novos

## 6. Estimativa de Complexidade

- **Arquivos novos**: `equity/engine.py`, `equity/models.py`, `api/routes/equity.py`, `dashboard/pages/5_⚖️_Equidade.py`
- **Arquivos modificados**: `models/measurement.py` (campo stratification_data), migrations, `api/main.py`
- **Linhas estimadas**: ~450
- **Testes novos**: ~14
