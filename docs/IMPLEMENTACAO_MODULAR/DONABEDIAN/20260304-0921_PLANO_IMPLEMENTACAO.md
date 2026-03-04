# DONABEDIAN — Plano de Implementacao
**Data:** 2026-03-04
**Versao:** 2.0.0
**Estimativa Total:** 4-6 dias
**Prioridade:** ONDA 3 — Qualidade e Inteligencia

---

## Estado Atual

Logica de calculo existe como modulo Python standalone (piloto).
Nao tem FastAPI, nao tem endpoints REST, nao e dockerizado como servico.

Pre-requisitos:
- GRAHAME funcional (dados clinicos FHIR para calcular indicadores)
- GERALDA funcional (dados de adesao terapeutica)

---

## Fase 1 — Criar API FastAPI (Dia 1-2) — ~5h

### Tarefa 1.1 — Auditar codigo existente
```bash
cd intellicare-donabedian
ls -la donabedian/  # o que existe?
pytest tests/ --co -q  # ver testes existentes
```
- [ ] Mapear o que ja esta implementado
- [ ] Identificar o que reusar vs reescrever

### Tarefa 1.2 — Criar donabedian/api/app.py
```python
# Padrao igual aos outros modulos
from intellicare_core.contracts import BaseAgent

app = FastAPI(title="DONABEDIAN", lifespan=lifespan)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # init DB
    # init engine
    yield
    # cleanup
```
- [ ] Criar `donabedian/api/app.py`
- [ ] Criar rotas health, info, analyze (BaseAgent)
- [ ] Testar: `uvicorn donabedian.api.app:app --port 8003`

### Tarefa 1.3 — Criar modelos SQLAlchemy
- [ ] Criar `donabedian/models/indicator.py` (ver spec tecnica)
- [ ] Gerar migracao Alembic
- [ ] Aplicar: `alembic upgrade head`

---

## Fase 2 — Endpoints de Indicadores (Dia 2-3) — ~5h

### Tarefa 2.1 — Rota GET /indicators
```python
@router.get("/indicators")
async def list_indicators(
    period: Optional[str] = Query(None),  # "2026-01" para janeiro
    category: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
) -> list[dict]:
    # Retornar valores mais recentes de cada indicador
    # com status semaforizacao
```
- [ ] Implementar listagem de indicadores com filtros

### Tarefa 2.2 — Endpoint /calculate
```python
@router.post("/indicators/calculate")
async def trigger_calculation(
    period_start: date,
    period_end: date,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
) -> dict:
    # Disparar calculo em background
    # Retornar job_id para acompanhar
```
- [ ] Implementar calculo em background (FastAPI BackgroundTasks)
- [ ] Calcular pelo menos DM2 HbA1c e HAS PA control

### Tarefa 2.3 — Integracao GRAHAME
- [ ] Criar `donabedian/services/grahame_client.py`
- [ ] Consultar Observations FHIR para calculo de indicadores
- [ ] Graceful degradation se GRAHAME offline

---

## Fase 3 — Semaforizacao e Historico (Dia 4) — ~3h

### Tarefa 3.1 — Semaforizacao automatica
```python
def calculate_status(value: float, definition: IndicatorDefinition) -> str:
    if value >= definition.threshold_green:
        return "green"
    elif value >= definition.threshold_yellow:
        return "yellow"
    else:
        return "red"
```
- [ ] Implementar semaforizacao em todos os indicadores

### Tarefa 3.2 — Historico de indicadores
- [ ] GET /indicators/{id}/history retorna evolucao temporal
- [ ] Dados para grafico de tendencia no portal

---

## Fase 4 — Testes e Release (Dia 5-6) — ~4h

### Tarefa 4.1 — Suite de testes
```bash
pytest tests/ -v --cov=donabedian --cov-report=term-missing
```
- [ ] Testes de motor de calculo (com GRAHAME mockado)
- [ ] Testes de rotas
- [ ] Meta: >= 75% cobertura, 0 falhas

### Tarefa 4.2 — Docker
```bash
docker compose up --build -d
curl http://localhost:8003/api/v1/health
```
- [ ] Container sobe sem erros

### Tarefa 4.3 — Smoke test global
- [ ] Adicionar DONABEDIAN ao `scripts/smoke_tests.py`

---

## Checklist de Entrega

| Item | Status |
|------|--------|
| FastAPI app criada | [ ] |
| GET /indicators funcionando | [ ] |
| POST /indicators/calculate | [ ] |
| Semaforizacao correta | [ ] |
| Historico temporal | [ ] |
| pytest >= 75% cobertura | [ ] |
| docker compose up -> healthy | [ ] |
| smoke_tests.py inclui DONABEDIAN | [ ] |

---

*DONABEDIAN v2.0 — Plano de Implementacao — 2026-03-04*
