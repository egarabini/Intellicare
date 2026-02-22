# intellicare-core

SDK compartilhado para modulos IntelliCare. Fornece contratos, FHIR client, configuracao e logging padronizados.

## Instalacao

```bash
# Basico
pip install -e .

# Com suporte a eventos (Redis)
pip install -e ".[events]"

# Desenvolvimento
pip install -e ".[dev]"
```

## Uso Rapido

### Configuracao

```python
from intellicare_core.config import BaseModuleConfig

class MeuModuloConfig(BaseModuleConfig):
    module_name: str = "intellicare-meumodulo"
    module_version: str = "1.0.0"
    # campos especificos do modulo
    meu_parametro: str = "valor"

config = MeuModuloConfig()  # carrega de .env e variaveis de ambiente
```

### Contratos

```python
from intellicare_core.contracts import ModuleInfo, HealthCheck

# Info do modulo (GET /api/v1/info)
info = ModuleInfo(
    name="intellicare-oswaldo",
    version="1.0.0",
    capabilities=["chronic-disease-monitoring", "staging"],
)

# Health check (GET /api/v1/health)
health = HealthCheck(
    status="healthy",
    module_name="intellicare-oswaldo",
    version="1.0.0",
    uptime_seconds=3600.0,
)
```

### FHIR Client

```python
from intellicare_core.fhir import FHIRClient

client = FHIRClient("http://localhost:8080/fhir")

# Buscar paciente
patient = await client.get_patient("patient-123")

# Resumo consolidado (IPS)
summary = await client.get_patient_summary("patient-123")
print(summary.name, summary.age, summary.active_conditions)
```

### Logging

```python
from intellicare_core.logging import configure_logging, get_logger

configure_logging("intellicare-oswaldo", level="INFO")
logger = get_logger(__name__)
logger.info("Analise iniciada", patient_id="123", disease="ckd")
```

## Desenvolvimento

```bash
make install-dev   # instala dependencias de dev
make test          # roda testes
make lint          # verifica estilo
make coverage      # cobertura de testes
make check         # lint + typecheck + test
```

## Estrutura

```
intellicare_core/
  config/       # BaseModuleConfig (pydantic-settings)
  contracts/    # ModuleInfo, HealthCheck, BaseAgent
  fhir/         # FHIRClient + modelos simplificados
  logging/      # structlog configurado
  events/       # EventPublisher via Redis Streams (opcional)
```

## Contrato Padrao

Todo modulo IntelliCare expoe:

| Endpoint | Descricao |
|----------|-----------|
| `GET /api/v1/health` | Health check (retorna `HealthCheck`) |
| `GET /api/v1/info` | Info do modulo (retorna `ModuleInfo`) |
