# intellicare-core — Especificacao Tecnica

## 1. Estrutura do Pacote

```
intellicare-core/
├── intellicare_core/
│   ├── __init__.py              # Exports publicos
│   ├── version.py               # __version__ = "1.0.0"
│   │
│   ├── fhir/
│   │   ├── __init__.py
│   │   ├── client.py            # FHIRClient — comunicacao HTTP
│   │   ├── models.py            # PatientSummary, ConditionSummary, etc.
│   │   ├── ips.py               # InternationalPatientSummary (IPS Brasil)
│   │   └── resources.py         # Helpers para manipulacao de recursos FHIR
│   │
│   ├── config/
│   │   ├── __init__.py
│   │   ├── base.py              # BaseConfig (pydantic_settings.BaseSettings)
│   │   └── env.py               # get_env(), require_env()
│   │
│   ├── logging/
│   │   ├── __init__.py
│   │   └── setup.py             # configure_logging() — structlog
│   │
│   ├── contracts/
│   │   ├── __init__.py
│   │   ├── module_info.py       # ModuleInfo (Pydantic model)
│   │   ├── health.py            # HealthCheck (Pydantic model)
│   │   └── base_agent.py        # BaseAgent (ABC)
│   │
│   └── events/
│       ├── __init__.py
│       └── publisher.py         # EventPublisher (Redis Streams)
│
├── tests/
│   ├── conftest.py
│   ├── test_fhir_client.py
│   ├── test_config.py
│   ├── test_logging.py
│   ├── test_contracts.py
│   └── test_events.py
│
├── pyproject.toml
├── README.md
├── Makefile
└── .env.example
```

## 2. Componentes Detalhados

### 2.1 FHIRClient

```python
# intellicare_core/fhir/client.py

class FHIRClient:
    """Cliente HTTP para servidores FHIR R4."""

    def __init__(self, base_url: str, timeout: int = 30):
        ...

    async def get_patient(self, patient_id: str) -> Patient:
        """Busca paciente por ID FHIR."""

    async def search_patient(self, cpf: str = None, name: str = None) -> list[Patient]:
        """Busca pacientes por CPF ou nome."""

    async def get_observations(self, patient_id: str, code: str = None) -> list[Observation]:
        """Busca observacoes clinicas de um paciente."""

    async def get_conditions(self, patient_id: str) -> list[Condition]:
        """Busca condicoes clinicas de um paciente."""

    async def get_ips(self, patient_id: str) -> InternationalPatientSummary:
        """Gera International Patient Summary."""

    async def get_resource(self, resource_type: str, resource_id: str) -> Resource:
        """Busca generica de recurso FHIR."""
```

**Origem:** Extrair de `agentes/mcp_servers/fhir_mcp_server.py` as classes de comunicacao HTTP e modelos Pydantic.

### 2.2 BaseConfig

```python
# intellicare_core/config/base.py

from pydantic_settings import BaseSettings

class BaseConfig(BaseSettings):
    """Configuracao base para modulos IntelliCare."""

    module_name: str
    module_version: str
    environment: str = "development"  # development | staging | production
    log_level: str = "INFO"
    fhir_server_url: str = "http://localhost:8080/fhir"
    redis_url: str = "redis://localhost:6379"
    database_url: str = ""

    class Config:
        env_prefix = "INTELLICARE_"
        env_file = ".env"
```

### 2.3 Contratos

```python
# intellicare_core/contracts/module_info.py

class ModuleInfo(BaseModel):
    name: str                    # "intellicare-oswaldo"
    version: str                 # "1.0.0"
    status: str                  # "healthy" | "degraded" | "unhealthy"
    capabilities: list[str]      # ["chronic-disease-monitoring", "staging"]
    fhir_version: str = "R4"
    metadata: dict = {}          # dados extras especificos do modulo

# intellicare_core/contracts/health.py

class HealthCheck(BaseModel):
    status: str                  # "healthy" | "degraded" | "unhealthy"
    uptime_seconds: float
    dependencies: dict[str, str] # {"database": "connected", "fhir": "connected"}
    timestamp: datetime

# intellicare_core/contracts/base_agent.py

class BaseAgent(ABC):
    """Interface que todo agente IntelliCare deve implementar."""

    @abstractmethod
    def get_info(self) -> ModuleInfo: ...

    @abstractmethod
    def get_health(self) -> HealthCheck: ...

    @abstractmethod
    async def analyze(self, request: dict) -> dict: ...
```

### 2.4 Logging

```python
# intellicare_core/logging/setup.py

def configure_logging(
    module_name: str,
    level: str = "INFO",
    json_output: bool = False,  # True em producao
) -> structlog.BoundLogger:
    """Configura logging estruturado para um modulo IntelliCare."""
```

## 3. Dependencias

```toml
# pyproject.toml
[project]
name = "intellicare-core"
version = "1.0.0"
requires-python = ">=3.11"
dependencies = [
    "pydantic>=2.5.0",
    "pydantic-settings>=2.0.0",
    "httpx>=0.27.0",
    "fhir.resources>=7.0.0",
    "structlog>=24.0.0",
    "python-dotenv>=1.0.0",
    "redis>=5.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "pytest-cov>=4.1.0",
    "ruff>=0.4.0",
    "mypy>=1.10.0",
]
```

## 4. Como Usar (Exemplo)

```python
# Em qualquer modulo IntelliCare:
from intellicare_core.fhir import FHIRClient
from intellicare_core.config import BaseConfig
from intellicare_core.contracts import BaseAgent, ModuleInfo, HealthCheck
from intellicare_core.logging import configure_logging

class OswaldoConfig(BaseConfig):
    module_name: str = "intellicare-oswaldo"
    module_version: str = "1.0.0"
    profiles_dir: str = "./profiles/diseases"

class OswaldoAgent(BaseAgent):
    def get_info(self) -> ModuleInfo:
        return ModuleInfo(
            name="intellicare-oswaldo",
            version="1.0.0",
            status="healthy",
            capabilities=["chronic-disease-monitoring", "staging", "alerts"],
        )
```

## 5. Testes

```bash
# Rodar testes
make test

# Cobertura
make coverage

# Lint
make lint
```

Cobertura minima: **90%** (por ser biblioteca fundacional).
