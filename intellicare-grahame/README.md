# intellicare-grahame

**Agente de Interoperabilidade FHIR R4**

Homenagem a **Grahame Grieve** — criador e principal arquiteto do padrão HL7 FHIR (Fast Healthcare Interoperability Resources), que revolucionou a troca de dados de saúde no mundo.

## Responsabilidades

- Armazenamento e recuperação de recursos FHIR R4 (Patient, Observation, Condition, Encounter, DiagnosticReport)
- API RESTful FHIR-compatível com Bundle responses para operações de busca
- Persistência de recursos em PostgreSQL (coluna JSON para flexibilidade máxima)
- Serve como barramento de dados clínicos estruturados entre os módulos IntelliCare
- Suporte a multi-tenancy via TenantContext do intellicare-core

## Porta

`8012` (externo) → `8000` (interno)

## Endpoints

| Método | Path | Descrição |
|--------|------|-----------|
| `GET` | `/api/v1/health` | Health check |
| `GET` | `/api/v1/info` | Informações do módulo |
| `GET` | `/api/v1/Patient` | Busca pacientes (Bundle) |
| `POST` | `/api/v1/Patient` | Cria/atualiza recurso Patient |
| `GET` | `/api/v1/Patient/{patient_id}` | Recupera paciente por ID |
| `GET` | `/api/v1/Observation` | Busca observações (Bundle) |
| `POST` | `/api/v1/Observation` | Cria/atualiza recurso Observation |
| `GET` | `/api/v1/Observation/{obs_id}` | Recupera observação por ID |
| `GET` | `/api/v1/{resource_type}` | Busca genérica por tipo de recurso |
| `POST` | `/api/v1/{resource_type}` | Salva recurso FHIR genérico |
| `GET` | `/api/v1/{resource_type}/{fhir_id}` | Recupera recurso FHIR por tipo+ID |
| `DELETE` | `/api/v1/{resource_type}/{fhir_id}` | Remove recurso FHIR |

## Executar standalone

```bash
docker compose up
```

## Executar testes

```bash
pytest tests/ -v --cov=grahame
```

## Variáveis de Ambiente

| Variável | Default | Descrição |
|----------|---------|-----------|
| `INTELLICARE_GRAHAME_DATABASE_URL` | — | PostgreSQL async URL |
| `INTELLICARE_REDIS_URL` | `redis://localhost:6379/0` | Redis URL |
| `INTELLICARE_LOG_LEVEL` | `INFO` | Nível de log |
| `INTELLICARE_ENVIRONMENT` | `development` | Ambiente |
| `INTELLICARE_MULTI_TENANT_ENABLED` | `false` | Multi-tenancy |
