# intellicare-oswaldo — Especificacao Tecnica

## 1. Estrutura do Projeto

```
intellicare-oswaldo/
├── oswaldo/
│   ├── __init__.py              # Exports publicos
│   ├── config.py                # OswaldoConfig extends BaseConfig
│   │
│   ├── api/                     # FastAPI REST API
│   │   ├── __init__.py
│   │   ├── app.py               # create_app() factory
│   │   ├── dependencies.py      # Injecao de dependencia
│   │   └── routes/
│   │       ├── __init__.py
│   │       ├── health.py        # GET /api/v1/health
│   │       ├── info.py          # GET /api/v1/info
│   │       ├── analyze.py       # POST /api/v1/analyze
│   │       ├── staging.py       # GET /api/v1/staging/{patient_id}
│   │       ├── alerts.py        # GET /api/v1/alerts/{patient_id}
│   │       └── trends.py        # GET /api/v1/trends/{patient_id}
│   │
│   ├── engine/                  # Motor de analise clinica
│   │   ├── __init__.py
│   │   ├── core_logic.py        # ChronicDiseaseEngine — orquestrador
│   │   ├── models.py            # StagingResult, TrendResult, Alert, PatientSummary
│   │   ├── alerts/
│   │   │   ├── __init__.py
│   │   │   ├── base.py          # BaseAlertGenerator
│   │   │   ├── threshold_alert.py
│   │   │   └── trend_alert.py
│   │   ├── staging/
│   │   │   ├── __init__.py
│   │   │   ├── base.py          # BaseStagingEngine (ABC)
│   │   │   ├── ckd_staging.py   # CKDStagingEngine (KDIGO)
│   │   │   ├── dm2_staging.py   # DM2StagingEngine (ADA)
│   │   │   ├── has_staging.py   # HASStagingEngine (ESC/ESH)
│   │   │   └── factory.py       # StagingFactory — Strategy Pattern
│   │   ├── medication/
│   │   │   ├── __init__.py
│   │   │   └── advisor.py       # MedicationAdvisor
│   │   └── risk/
│   │       ├── __init__.py
│   │       └── cardiovascular.py # CVRiskCalculator
│   │
│   ├── profiles/                # Disease Profiles (YAML)
│   │   ├── __init__.py
│   │   ├── loader.py            # ProfileLoader
│   │   ├── registry.py          # ProfileRegistry (singleton)
│   │   ├── schema.py            # ProfileSchema (validacao JSON Schema)
│   │   ├── models.py            # DiseaseProfile, Biomarker, Stage
│   │   └── diseases/
│   │       ├── ckd.yaml
│   │       ├── dm2.yaml
│   │       └── has.yaml
│   │
│   ├── datastore/               # Persistencia
│   │   ├── __init__.py
│   │   ├── fhir_datastore.py    # Busca dados via FHIR
│   │   ├── database.py          # SQLAlchemy session management
│   │   └── models_db.py         # Modelos ORM (historico de analises)
│   │
│   ├── ui/                      # Interface Streamlit
│   │   ├── __init__.py
│   │   ├── main.py              # Dashboard principal
│   │   └── pages/
│   │       └── biomarkers_info.py
│   │
│   └── subagent/                # Integracao com Wanda
│       ├── __init__.py
│       └── oswaldo_subagent.py  # OswaldoSubagent extends BaseAgent
│
├── tests/
│   ├── conftest.py              # Fixtures compartilhadas
│   ├── test_alerts.py
│   ├── test_engine_core.py
│   ├── test_ckd_profile.py
│   ├── test_staging_ckd.py
│   ├── test_staging_dm2.py
│   ├── test_staging_has.py
│   ├── test_oswaldo_subagent.py
│   ├── test_end_to_end.py
│   ├── test_profiles.py
│   ├── test_ui.py
│   ├── test_api.py              # NOVO: testes da API REST
│   ├── validate_all_profiles.py
│   └── run_all_tests.py
│
├── scripts/
│   ├── generate_seed.py         # Gera dados de teste
│   └── load_seed.py             # Carrega dados no banco
│
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
├── Makefile
├── README.md
├── .env.example
└── .streamlit/
    └── config.toml
```

## 2. Migracao do Monolito

### Arquivos a Migrar (de INTELLICAREREPO/agentes/oswaldo/)

| Origem | Destino | Adaptacao |
|--------|---------|-----------|
| `engine/core_logic.py` (486 linhas) | `oswaldo/engine/core_logic.py` | Trocar FHIR imports por intellicare-core |
| `engine/models.py` | `oswaldo/engine/models.py` | Manter como esta |
| `engine/alerts/` | `oswaldo/engine/alerts/` | Manter como esta |
| `engine/staging/` | `oswaldo/engine/staging/` | Manter como esta |
| `engine/medication/` | `oswaldo/engine/medication/` | Manter como esta |
| `engine/risk/` | `oswaldo/engine/risk/` | Manter como esta |
| `profiles/` | `oswaldo/profiles/` | Manter como esta |
| `datastore/fhir_datastore.py` | `oswaldo/datastore/` | Usar FHIRClient do core |
| `ui/main.py` | `oswaldo/ui/main.py` | Adaptar imports |
| `tests/` (14+ arquivos) | `tests/` | Adaptar imports |
| `subagent/oswaldo_subagent.py` | `oswaldo/subagent/` | Extends BaseAgent do core |
| `config.py` | `oswaldo/config.py` | Extends BaseConfig do core |

### Codigo Novo a Criar

| Arquivo | Descricao |
|---------|-----------|
| `api/app.py` | FastAPI application factory |
| `api/routes/health.py` | Health check endpoint |
| `api/routes/info.py` | Module info endpoint |
| `api/routes/analyze.py` | Analise clinica endpoint |
| `api/routes/staging.py` | Estadiamento endpoint |
| `api/routes/alerts.py` | Alertas endpoint |
| `api/routes/trends.py` | Tendencias endpoint |
| `Dockerfile` | Container autonomo |
| `docker-compose.yml` | Orquestracao local |
| `Makefile` | Comandos de dev |

## 3. API REST

### Endpoints

```
GET  /api/v1/health                          → HealthCheck
GET  /api/v1/info                            → ModuleInfo
POST /api/v1/analyze                         → AnalysisResult
GET  /api/v1/staging/{patient_id}            → StagingResult
GET  /api/v1/staging/{patient_id}/{disease}  → StagingResult (doenca especifica)
GET  /api/v1/alerts/{patient_id}             → list[Alert]
GET  /api/v1/trends/{patient_id}/{biomarker} → TrendResult
GET  /api/v1/diseases                        → list[DiseaseProfile] (doenças suportadas)
```

### Exemplo: POST /api/v1/analyze

```json
// Request
{
    "patient_id": "fhir-patient-123",
    "diseases": ["ckd", "dm2"],       // opcional, default: todas
    "include_medication": true,        // opcional
    "include_risk": true               // opcional
}

// Response
{
    "patient_id": "fhir-patient-123",
    "timestamp": "2026-02-08T14:30:00Z",
    "staging": {
        "ckd": {
            "stage": "G3a",
            "substage": "A2",
            "egfr": 52.3,
            "acr": 45.0,
            "confidence": 0.92
        },
        "dm2": {
            "stage": "controlled",
            "hba1c": 6.8,
            "confidence": 0.88
        }
    },
    "alerts": [
        {
            "severity": "attention",
            "type": "trend",
            "message": "eGFR em queda progressiva: -4.2 ml/min/ano",
            "recommendation": "Considerar encaminhamento a nefrologista"
        }
    ],
    "trends": {
        "egfr": {
            "direction": "declining",
            "velocity": -4.2,
            "unit": "ml/min/1.73m2/year"
        }
    }
}
```

## 4. Docker

### Dockerfile

```dockerfile
FROM python:3.11-slim AS base

WORKDIR /app

# Instalar dependencias do sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev && rm -rf /var/lib/apt/lists/*

# Instalar dependencias Python
COPY pyproject.toml .
RUN pip install --no-cache-dir .

# Copiar codigo
COPY oswaldo/ ./oswaldo/
COPY scripts/ ./scripts/

# Expor portas
EXPOSE 8000 8501

# Comando padrao: API + Streamlit
CMD ["sh", "-c", "uvicorn oswaldo.api.app:create_app --host 0.0.0.0 --port 8000 & streamlit run oswaldo/ui/main.py --server.port 8501 --server.headless true"]
```

### docker-compose.yml

```yaml
services:
  oswaldo:
    build: .
    ports:
      - "8000:8000"   # API REST
      - "8501:8501"   # Streamlit UI
    environment:
      - INTELLICARE_DATABASE_URL=postgresql://oswaldo:oswaldo@db:5432/oswaldo
      - INTELLICARE_FHIR_SERVER_URL=http://fhir:8080/fhir
      - INTELLICARE_LOG_LEVEL=INFO
    depends_on:
      db:
        condition: service_healthy

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: oswaldo
      POSTGRES_PASSWORD: oswaldo
      POSTGRES_DB: oswaldo
    ports:
      - "5432:5432"
    volumes:
      - oswaldo_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U oswaldo"]
      interval: 5s
      timeout: 3s
      retries: 5

volumes:
  oswaldo_data:
```

## 5. Dependencias

```toml
[project]
name = "intellicare-oswaldo"
version = "1.0.0"
requires-python = ">=3.11"
dependencies = [
    "intellicare-core>=1.0.0,<2.0.0",
    # Engine
    "pydantic>=2.5.0",
    "PyYAML>=6.0.1",
    "jsonschema>=4.20.0",
    # Database
    "SQLAlchemy>=2.0.0",
    "psycopg2-binary>=2.9.9",
    # API
    "fastapi>=0.115.0",
    "uvicorn>=0.30.0",
    # UI
    "streamlit>=1.28.0",
    "plotly>=5.17.0",
    "pandas>=2.1.0",
    # LangGraph (para subagent)
    "langgraph>=0.2.0",
    "langchain>=0.3.0",
]
```

## 6. Patterns Arquiteturais

### Strategy Pattern (Staging)
Cada doenca tem sua propria estrategia de estadiamento. O `StagingFactory` seleciona a estrategia correta baseada no disease profile.

### Registry Pattern (Profiles)
`ProfileRegistry` carrega todos os profiles YAML e os disponibiliza para o engine.

### Factory Pattern (Alerts)
`AlertFactory` cria geradores de alerta baseados no tipo (threshold, trend).

## 7. Testes

### Migrados do Monolito (14+ arquivos):
- `test_alerts.py` — geracao de alertas
- `test_engine_core.py` — logica principal
- `test_ckd_profile.py` — profile CKD
- `test_staging_ckd.py` — estadiamento KDIGO
- `test_staging_dm2.py` — estadiamento ADA
- `test_staging_has.py` — estadiamento ESC/ESH
- `test_oswaldo_subagent.py` — integracao com Wanda
- `test_end_to_end.py` — fluxo completo
- `test_profiles.py` — carregamento de profiles
- `test_ui.py` — testes de UI
- `validate_all_profiles.py` — validacao de YAML

### Novos:
- `test_api.py` — testes dos endpoints FastAPI

### Cobertura Minima: 80%
