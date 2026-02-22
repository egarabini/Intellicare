# EF-D004 — Benchmarking e Referencia Nacional

> Comparar os indicadores de qualidade do servico com referencias nacionais e regionais do DATASUS, padroes do Ministerio da Saude e medias de servicos similares.

## 1. Objetivo

Implementar benchmarking dos indicadores de qualidade, respondendo a pergunta fundamental que o score isolado nao responde: **"73% e bom ou ruim?"**

- Comparar cada indicador com meta nacional do MS/DATASUS
- Identificar em qual percentil o servico se encontra (acima/abaixo de quantos servicos similares?)
- Calcular gap para a "melhor pratica" (top quartil nacional)
- Exibir no dashboard com comparativo visual

## 2. Justificativa

- Score de 73/100 sem referencia e desinformativo — pode ser excelente ou pessimo
- Pilares de Efetividade e Equidade sao impossíveis de avaliar sem benchmarks
- MS publica metas nacionais para 30+ indicadores hospitalares (SAS/DATASUS)
- Donabedian sem benchmarking e "avaliacao no vazio" — contra o proprio conceito do autor

## 3. Escopo

### 3.1 Modelos de Dados

```python
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class BenchmarkReference:
    """
    Referencia de benchmark para um indicador especifico.
    """
    indicator_id: str
    indicator_name: str

    # Referencia nacional (MS/DATASUS)
    national_target: Optional[float]       # Meta do MS para este indicador
    national_avg: Optional[float]          # Media nacional atual
    national_p25: Optional[float]          # Percentil 25
    national_p50: Optional[float]          # Mediana
    national_p75: Optional[float]          # Percentil 75 (boas praticas)
    national_p90: Optional[float]          # Percentil 90 (excelencia)
    national_best: Optional[float]         # Melhor resultado documentado

    # Referencia regional (quando disponivel)
    regional_avg: Optional[float]
    regional_state: Optional[str]          # UF de referencia

    # Metadados
    benchmark_source: str                  # "DATASUS", "OMS", "Joint Commission", "SAS-MS"
    reference_year: int
    target_operator: str                   # ">=" ou "<="
    last_updated: str


@dataclass
class BenchmarkComparison:
    """
    Comparacao de um indicador do servico contra os benchmarks.
    """
    indicator_id: str
    current_value: float
    benchmark: BenchmarkReference

    # Posicao relativa
    vs_national_target: float        # current - national_target (positivo = acima da meta)
    vs_national_avg: float           # current - national_avg
    percentile_position: Optional[str]  # "abaixo_p25", "p25_p50", "p50_p75", "acima_p75", "top10"
    gap_to_excellence: float         # distancia para p90 (melhor pratica)

    # Status comparativo
    meets_national_target: bool
    is_above_national_avg: bool
    benchmark_status: str            # "excelencia", "acima_media", "media", "abaixo_media", "critico"
```

### 3.2 BenchmarkEngine

```python
class BenchmarkEngine:
    """
    Motor de benchmarking.

    Fontes de dados de benchmark (em ordem de preferencia):
    1. DATASUS API (via Zilda — indicadores hospitalares do SIH)
    2. SAS/MS tabelas publicas (cache local em JSON)
    3. OMS metas globais (hardcoded, revisadas anualmente)

    Cache: 7 dias (dados de benchmark nao mudam com frequencia).
    """

    # Benchmarks nacionais (fonte: MS/SAS — atualizados por YAML)
    # Complementados por dados em tempo real do DATASUS via Zilda
    NATIONAL_BENCHMARKS = {
        "taxa_infeccao_hospitalar": {
            "national_target": 2.0,        # Meta MS: < 2%
            "national_avg": 3.1,
            "p75": 2.3,                    # Boas praticas
            "p90": 1.5,                    # Excelencia
            "source": "ANVISA/IRAS",
            "operator": "<=",
        },
        "tempo_porta_balao_iam": {
            "national_target": 90,         # Minutos — meta SBC
            "national_avg": 120,
            "p75": 85,
            "p90": 60,
            "source": "SBC-2022",
            "operator": "<=",
        },
        "taxa_cesarea": {
            "national_target": 40.0,       # OMS recomenda < 15%, COFEN aceita < 40%
            "national_avg": 56.0,          # Brasil acima da media mundial
            "p75": 45.0,
            "p90": 30.0,
            "source": "OMS/MS",
            "operator": "<=",
        },
        "mortalidade_hospitalar_geral": {
            "national_target": 3.5,        # Meta SAS
            "national_avg": 4.2,
            "p75": 3.0,
            "p90": 2.0,
            "source": "SIH/DATASUS",
            "operator": "<=",
        },
        "taxa_reinternacao_30d": {
            "national_target": 10.0,       # Meta MS
            "national_avg": 12.5,
            "p75": 9.0,
            "p90": 7.0,
            "source": "SIH/DATASUS",
            "operator": "<=",
        },
        "taxa_ocupacao_leitos": {
            "national_target": 85.0,       # OMS: 80-85% = ideal
            "national_avg": 78.0,
            "p75": 83.0,
            "p90": 87.0,
            "source": "OMS/CNES",
            "operator": "<=",
        },
        "satisfacao_paciente": {
            "national_target": 80.0,       # % satisfeitos
            "national_avg": 72.0,
            "p75": 82.0,
            "p90": 90.0,
            "source": "ANS/OUVs",
            "operator": ">=",
        },
        "cobertura_esf": {
            "national_target": 60.0,       # Previne Brasil
            "national_avg": 55.0,
            "p75": 65.0,
            "p90": 75.0,
            "source": "Previne-Brasil-2025",
            "operator": ">=",
        },
    }

    async def compare_indicator(
        self,
        indicator_id: str,
        current_value: float,
    ) -> Optional[BenchmarkComparison]:
        """
        Compara um indicador com seus benchmarks.
        Retorna None se nao ha benchmark disponivel para este indicador.
        Cache: 7 dias.
        """

    async def get_service_benchmark_summary(
        self,
        period_start: str,
        period_end: str,
    ) -> dict:
        """
        Sumario de benchmarking para todos os indicadores do servico.

        Retorna:
        {
            "benchmarked_count": 12,     # Indicadores com benchmark disponivel
            "meets_national_target": 8,  # Atingem meta nacional
            "above_national_avg": 10,    # Acima da media
            "excellence_count": 3,       # Acima do p90
            "critical_gaps": [
                {
                    "indicator": "taxa_cesarea",
                    "current": 58.0,
                    "national_target": 40.0,
                    "gap": 18.0,
                    "percentile": "abaixo_p25"
                }
            ],
            "overall_benchmark_score": 67.0  # Score ponderado vs benchmarks nacionais
        }
        """
```

### 3.3 Atualizacao Automatica de Benchmarks

```python
class BenchmarkUpdater:
    """
    Atualiza benchmarks via Zilda (DATASUS) e arquivos YAML locais.

    Frequencia: semanal (dados do DATASUS tem publicacao mensal)
    """

    async def refresh_from_zilda(self) -> None:
        """
        Busca indicadores hospitalares atualizados do DATASUS via Zilda.
        Atualiza nacional_avg com dados do ano corrente.
        """

    async def refresh_from_yaml(self, yaml_path: str) -> None:
        """
        Carrega benchmarks de arquivo YAML editavel.
        Permite adicionar benchmarks de fontes nao automatizaveis.
        """
```

### 3.4 Endpoints REST Novos

```python
# GET /api/v1/benchmarks
# Retorna: lista de todos os benchmarks disponíveis

# GET /api/v1/benchmarks/indicator/{indicator_id}
# Retorna: BenchmarkReference para o indicador

# GET /api/v1/benchmarks/compare
# Query params: period_start, period_end
# Retorna: BenchmarkComparison para todos os indicadores com benchmark

# GET /api/v1/benchmarks/summary
# Query params: period_start, period_end
# Retorna: sumario comparativo (quantos atingem meta, percentil medio, gaps)

# GET /api/v1/dashboard (ATUALIZADO)
# Inclui: benchmarks_summary no response do dashboard existente
```

### 3.5 Visualizacao no Dashboard

Adicionar a pagina `2_📊_Pilares.py` e `3_📈_Indicadores.py`:
- Coluna adicional "Benchmark Nacional" na tabela de indicadores
- Indicador visual de percentil (barra com marcacao de onde o servico esta)
- "Gap para excelencia" em cada indicador
- Novo card no home: "X indicadores acima da media nacional"

## 4. Testes

- BenchmarkEngine.compare_indicator: acima da meta, abaixo, sem benchmark (4 testes)
- get_service_benchmark_summary: contagem correta, gaps identificados (3 testes)
- NATIONAL_BENCHMARKS: validacao de estrutura (2 testes)
- Endpoints: lista, indicador, compare, summary (4 testes)
- BenchmarkUpdater: refresh_from_yaml (2 testes)
- **Total**: 15+ testes novos

## 5. Criterios de Aceitacao

- [ ] Benchmarks para os 15+ indicadores do seed
- [ ] Fontes citadas em cada benchmark (MS, OMS, ANVISA, SBC)
- [ ] Posicionamento percentil calculado (abaixo_p25 ate top10)
- [ ] Gap para excelencia (p90) calculado
- [ ] Dashboard atualizado com coluna benchmark
- [ ] 4 endpoints REST funcionais
- [ ] Arquivo YAML editavel para novos benchmarks
- [ ] 363 testes v1.0 continuam passando
- [ ] 15+ testes novos

## 6. Estimativa de Complexidade

- **Arquivos novos**: `benchmarks/engine.py`, `benchmarks/models.py`, `benchmarks/updater.py`, `data/benchmarks.yaml`, `api/routes/benchmarks.py`
- **Arquivos modificados**: `api/routes/dashboard.py`, `dashboard/pages/3_📈_Indicadores.py`
- **Linhas estimadas**: ~450
- **Testes novos**: ~15
