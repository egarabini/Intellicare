# EF-O001 — Historico de Estadiamento e Endpoint de Tendencias

> Persistir o historico de estadiamento ao longo do tempo e expor endpoint dedicado de tendencias por biomarcador.

## 1. Objetivo

Persistir cada calculo de estadiamento como ponto na timeline do paciente e criar endpoint dedicado de tendencias, permitindo:

- "Como a funcao renal deste paciente evoluiu nos ultimos 12 meses?"
- "A HbA1c esta melhorando ou piorando na tendencia dos ultimos 90 dias?"
- "Em quanto tempo o paciente com IRC G3a vai atingir G4 se a progressao continuar?"

## 2. Justificativa

- **Gap critico**: Atualmente cada chamada ao Oswaldo recalcula do zero — sem memoria da evolucao
- `StagingResult.confidence_score` nunca e preenchido pois sem historico nao ha base de comparacao
- Florence e Wanda precisam de tendencia temporal para decisoes clinicas contextualizadas
- Gestao de risco requer projecao de progressao (eGFR -3 mL/min/ano → em 2 anos G4)

## 3. Escopo

### 3.1 Modelo de Historico

```python
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


@dataclass
class StagingHistoryEntry:
    """
    Um ponto no historico de estadiamento de um paciente.
    Persistido em PostgreSQL toda vez que calculate_staging() e chamado.
    """
    entry_id: str                        # UUID
    patient_id: str
    disease_id: str                      # "ckd", "dm2", "has"

    # Resultado do estadiamento
    stage: str                           # "G3a_A2", "SUBOPTIMAL", "GRADE2"
    stage_label: str                     # Descricao legivel
    severity: str                        # "info", "warning", "critical"
    confidence_score: float              # Calculado com base nos dados disponiveis

    # Observacoes usadas neste estadiamento
    observation_values: dict             # {"egfr": 52.3, "acr": 35.0}
    data_completeness: float             # % de observacoes presentes vs esperadas

    # Timestamp
    staged_at: datetime
    data_reference_period: str           # Periodo das observacoes usadas


@dataclass
class StagingTimeline:
    """
    Linha do tempo de estadiamento de um paciente para uma doenca.
    """
    patient_id: str
    disease_id: str
    entries: list[StagingHistoryEntry]

    # Progressao calculada
    current_stage: str
    previous_stage: Optional[str]        # Estadio anterior
    stage_changed: bool
    stage_change_date: Optional[datetime]

    # Tendencia geral
    progression_trend: str               # "improving", "stable", "worsening"
    progression_velocity: Optional[float]  # Velocidade de progressao por mes

    # Projecao
    projected_next_stage: Optional[str]
    projected_date: Optional[str]        # ISO date da projecao
    projection_confidence: float
```

### 3.2 StagingHistoryRepository

```python
class StagingHistoryRepository:
    """
    Persistencia do historico de estadiamento.
    Usa tabela dedicada (nao o FHIR store generico).
    """

    async def save_entry(
        self,
        entry: StagingHistoryEntry,
    ) -> None:
        """
        Persiste um novo ponto de estadiamento.
        Chamado automaticamente pelo ChronicDiseaseEngine apos cada staging.
        """

    async def get_timeline(
        self,
        patient_id: str,
        disease_id: str,
        days: int = 365,
    ) -> StagingTimeline:
        """
        Timeline completa de estadiamento de um paciente.
        Calcula progressao e projecao automaticamente.
        Cache: 30 min (dados podem mudar com nova observacao).
        """

    async def get_latest(
        self,
        patient_id: str,
        disease_id: str,
    ) -> Optional[StagingHistoryEntry]:
        """
        Estadiamento mais recente persistido.
        Util para comparar com o atual e detectar mudanca de estadio.
        """

    async def get_stage_changes(
        self,
        patient_id: str,
        disease_id: str,
    ) -> list[dict]:
        """
        Apenas os pontos de mudanca de estadio na timeline.

        Retorna:
        [
            {"from": "G2_A1", "to": "G3a_A2", "date": "2025-03-15"},
            {"from": "G3a_A2", "to": "G3a_A3", "date": "2025-09-20"},
        ]
        """
```

### 3.3 BiomarkerTrendService

```python
class BiomarkerTrendService:
    """
    Analise de tendencia para um biomarcador especifico.
    Suporta o novo endpoint GET /api/v1/trends/{patient_id}/{biomarker}.
    """

    async def get_biomarker_trend(
        self,
        patient_id: str,
        biomarker: str,           # "egfr", "hba1c", "systolic_bp", etc.
        days: int = 365,
    ) -> BiomarkerTrendResult:
        """
        Tendencia de um biomarcador especifico ao longo do tempo.

        Busca observacoes FHIR do paciente, filtra pelo codigo LOINC
        correspondente ao biomarcador, e calcula:
        - Serie temporal de valores
        - Slope (regressao linear simples)
        - Direcao (improving/stable/worsening)
        - Projecao a 6 meses

        Cache: 15 min.
        """

    def _calculate_slope(
        self,
        values: list[float],
        timestamps: list[datetime],
    ) -> float:
        """
        Regressao linear simples para calcular slope.
        Usa numpy.polyfit se disponivel, fallback para algoritmo manual.
        Retorna slope em unidade/dia.
        """

    def _project_value(
        self,
        current_value: float,
        slope_per_day: float,
        days_ahead: int = 180,
    ) -> dict:
        """
        Projeta valor futuro com intervalo de confianca.
        Retorna: {projected: 43.2, confidence_low: 38.0, confidence_high: 48.4}
        """


@dataclass
class BiomarkerTrendResult:
    patient_id: str
    biomarker: str
    loinc_code: str
    unit: str

    # Serie temporal (ordenada por data)
    data_points: list[dict]              # [{date, value, source_fhir_id}]
    period_days: int
    data_count: int

    # Estatisticas
    current_value: Optional[float]
    min_value: float
    max_value: float
    mean_value: float

    # Tendencia
    slope_per_day: float
    slope_per_month: float
    direction: str                       # "improving", "stable", "worsening"
    direction_confidence: float

    # Projecao 6 meses
    projected_6m: Optional[dict]

    # Alertas clinicos
    alerts: list[dict]                   # Alertas especificos para este biomarcador
```

### 3.4 Confidence Score (preenchimento real)

O `StagingResult.confidence_score` deve ser calculado com base em:

```python
def calculate_confidence(
    observations: dict,               # Observacoes disponiveis
    profile: DiseaseProfile,          # Perfil da doenca
    history: list[StagingHistoryEntry],  # Historico
) -> float:
    """
    Score de 0.0 a 1.0 indicando confianca no estadiamento.

    Fatores:
    1. Completude dos dados (40%): % observacoes presentes vs esperadas
       - CKD: egfr + acr = 100%; so egfr = 60%; so acr = 40%
    2. Recencia dos dados (30%): observacoes < 30 dias = 100%, > 90 dias = 50%
    3. Consistencia historica (20%): estadio consistente com historico
    4. Multiplas medicoes (10%): > 2 pontos no periodo = bonus

    Exemplo:
    - Todos os exames presentes e recentes + historico consistente = 0.95
    - So eGFR disponivel, exame de 60 dias atras, sem historico = 0.45
    """
```

### 3.5 Endpoint Novo

```python
# GET /api/v1/trends/{patient_id}/{biomarker}
# Query params:
#   days: int (default 365, max 1825 = 5 anos)
# Retorna: BiomarkerTrendResult

# GET /api/v1/staging/{patient_id}/history
# Query params:
#   disease: str (opcional — "ckd", "dm2", "has")
#   days: int (default 365)
# Retorna: StagingTimeline (ou dict com timeline por doenca)

# GET /api/v1/staging/{patient_id}/changes
# Retorna: list de mudancas de estadio (data, de, para) para todas as doencas
```

### 3.6 Schema SQL

```sql
CREATE TABLE oswaldo_staging_history (
    id BIGSERIAL PRIMARY KEY,
    entry_id UUID UNIQUE NOT NULL,
    patient_id VARCHAR(64) NOT NULL,
    disease_id VARCHAR(20) NOT NULL,
    stage VARCHAR(20) NOT NULL,
    stage_label VARCHAR(100),
    severity VARCHAR(20),
    confidence_score FLOAT,
    observation_values JSONB DEFAULT '{}',
    data_completeness FLOAT,
    staged_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    data_reference_period VARCHAR(50)
);

CREATE INDEX idx_staging_patient ON oswaldo_staging_history(patient_id);
CREATE INDEX idx_staging_patient_disease ON oswaldo_staging_history(patient_id, disease_id);
CREATE INDEX idx_staging_at ON oswaldo_staging_history(staged_at);
```

### 3.7 Modificacoes no ChronicDiseaseEngine

```python
# Em calculate_staging():
# Apos calcular o estadiamento, automaticamente:
# 1. Calcular confidence_score (novo metodo)
# 2. Comparar com historico (detectar mudanca de estadio)
# 3. Persistir entry no StagingHistoryRepository
# 4. Preencher StagingResult.confidence_score
```

## 4. Testes

- StagingHistoryRepository: save, get_timeline, get_latest, get_changes (6 testes)
- BiomarkerTrendService: slope, direction, projecao (5 testes)
- Confidence score: completo, parcial, sem historico (4 testes)
- Endpoints novos: /trends, /history, /changes (4 testes)
- Integracao: ChronicDiseaseEngine persiste apos calcular (3 testes)
- **Total**: 22+ testes novos

## 5. Criterios de Aceitacao

- [ ] `StagingHistoryRepository` persiste cada calculo automaticamente
- [ ] `StagingResult.confidence_score` sempre preenchido (nunca None)
- [ ] Formula de confidence documentada e testada
- [ ] `BiomarkerTrendService` com regressao linear e projecao 6 meses
- [ ] `GET /api/v1/trends/{patient_id}/{biomarker}` implementado
- [ ] `GET /api/v1/staging/{patient_id}/history` implementado
- [ ] Deteccao de mudanca de estadio com data registrada
- [ ] 98 testes v1.0 continuam passando
- [ ] 22+ testes novos
- [ ] Cobertura >= 85%

## 6. Estimativa de Complexidade

- **Arquivos novos**: `datastore/staging_history.py`, `engine/biomarker_trends.py`
- **Arquivos modificados**: `engine/core_logic.py` (auto-persistir), `engine/models.py` (BiomarkerTrendResult), `api/app.py` (3 endpoints), `config.py`
- **Linhas estimadas**: ~400
- **Testes novos**: ~22
