# DONABEDIAN — Especificacoes Tecnicas
**Data:** 2026-03-04
**Versao:** 2.0.0
**Modulo:** intellicare-donabedian (porta 8003)

---

## 1. Stack Tecnologica

| Componente | Tecnologia |
|-----------|-----------|
| Runtime | Python 3.11 |
| Framework | FastAPI (a adicionar) |
| ORM | SQLAlchemy 2.x async |
| Banco | PostgreSQL 15 |
| Calculo | pandas (analise de dados) |
| Graficos | matplotlib (geracao de graficos para PDF) |
| Testes | pytest + pytest-asyncio |

---

## 2. Problema Atual: Sem API

O modulo nao tem `donabedian/api/app.py`. Precisa ser criado.
Atualmente a logica de calculo existe mas nao e exposta via REST.

Estrutura a criar:
```
intellicare-donabedian/
├── donabedian/
│   ├── api/
│   │   ├── app.py              # CRIAR
│   │   └── routes/
│   │       ├── health.py       # CRIAR
│   │       ├── info.py         # CRIAR
│   │       ├── analyze.py      # CRIAR
│   │       └── indicators.py   # CRIAR
│   ├── services/
│   │   ├── indicator_engine.py # JA EXISTE (verificar)
│   │   ├── consolidation.py    # JA EXISTE (verificar)
│   │   └── grahame_client.py   # CRIAR
│   ├── models/
│   │   ├── indicator.py        # CRIAR ou verificar
│   │   └── report.py           # CRIAR
│   └── config.py               # CRIAR ou verificar
```

---

## 3. Endpoints a Criar

```
GET  /api/v1/health
GET  /api/v1/info
POST /api/v1/analyze        (BaseAgent contract)

GET  /api/v1/indicators     → List[Indicator] (query: period, category)
GET  /api/v1/indicators/{id} → Indicator + historico
POST /api/v1/indicators/calculate  → TriggerResult (calculo sob demanda)
GET  /api/v1/indicators/{id}/history → List[IndicatorValue]

GET  /api/v1/reports        → List[Report]
POST /api/v1/reports/generate  → Report (dispara geracao PDF)
GET  /api/v1/reports/{id}   → Report com link para PDF
```

---

## 4. Modelos

```python
class IndicatorValue(Base):
    __tablename__ = "indicator_values"
    id: UUID (PK)
    indicator_id: str        # "dm2_hba1c_control", "hypertension_bp_control"
    period_start: date
    period_end: date
    value: float
    numerator: int
    denominator: int
    unit: str               # "%", "por 1000", etc
    status: str             # "green", "yellow", "red"
    threshold_green: float  # meta ideal
    threshold_yellow: float # meta aceitavel
    benchmark: Optional[float]  # referencia nacional
    tenant_id: str
    calculated_at: datetime

class IndicatorDefinition(Base):
    __tablename__ = "indicator_definitions"
    id: str (PK)            # slug como "dm2_hba1c_control"
    name: str
    description: str
    category: str           # "process", "outcome", "structure"
    pmaq_code: Optional[str]
    ona_requirement: Optional[str]
    formula: str            # descricao da formula
    data_source: str        # "grahame_observations", "geralda_tasks"
    enabled: bool
```

---

## 5. Motor de Calculo

```python
# donabedian/services/indicator_engine.py

class IndicatorEngine:
    async def calculate_all(self, period: DateRange, tenant: str) -> list[IndicatorValue]:
        results = []
        for definition in await self.get_enabled_definitions():
            calculator = self._get_calculator(definition.id)
            value = await calculator.calculate(period, tenant)
            results.append(value)
        return results

    def _get_calculator(self, indicator_id: str) -> BaseCalculator:
        return CALCULATORS.get(indicator_id, NullCalculator())

# Calculadoras especificas
class DM2HbA1cControl(BaseCalculator):
    # numerador: Observations HbA1c < 7% nos ultimos 6 meses
    # denominador: Conditions DM2 ativas
    # fonte: GRAHAME FHIR

class HypertensionBPControl(BaseCalculator):
    # numerador: Observations PA < 140/90 nos ultimos 3 meses
    # denominador: Conditions HAS ativas
```

---

## 6. Configuracao

```env
DATABASE_URL=postgresql+asyncpg://intellicare:password@postgres:5432/intellicare
GRAHAME_URL=http://grahame:8012/api/v1
GERALDA_URL=http://geralda:8006/api/v1
REDIS_URL=redis://redis:6379/0
PORT=8000
CALCULATION_BATCH_SIZE=100
```

---

*DONABEDIAN v2.0 — Especificacoes Tecnicas — 2026-03-04*
