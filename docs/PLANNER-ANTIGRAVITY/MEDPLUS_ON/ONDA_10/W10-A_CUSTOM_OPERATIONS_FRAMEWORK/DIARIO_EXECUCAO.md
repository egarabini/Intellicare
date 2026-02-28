# W10-A — Diário de Execução

## 2026-02-25 — Execução DEV2

### Escopo executado
- Implementado framework de operações customizadas por tenant no `intellicare-grahame`.
- Entregue suporte para operação customizada:
  - `instance-level`: `POST /api/v1/fhir/{ResourceType}/{id}/$<op>`
  - `system-level`: `POST /api/v1/fhir/$<op>`
- Entregue Admin API para registro/gestão:
  - `GET/POST/PUT/DELETE /api/v1/admin/custom-operations`

### Entregas técnicas
- Modelo ORM:
  - `grahame/models/custom_operation.py`
  - tabelas: `custom_operations`, `custom_operation_audit`
- Migração:
  - `migrations/versions/20260225_1800_add_custom_operations.py`
- Persistência/serviço:
  - `grahame/services/custom_operation_repository.py`
  - `grahame/services/custom_ops_service.py`
- Roteamento:
  - `grahame/api/routes/custom_operations_routes.py`
  - registro de rotas no `grahame/api/app.py`

### Comportamentos cobertos
- Validação de nome da operação (regex + bloqueio de operações nativas).
- Lookup isolado por tenant.
- Execução por `handler_type`:
  - `url` (HTTP POST externo)
  - `bot` (integração com BotService)
- Timeout por operação.
- Rate limit por `(tenant_id, operation_name)`.
- Auditoria de execução (`custom_operation_audit`) com status/erro/duração.

### Testes de regressão
- Arquivo: `tests/test_custom_operations.py`
- Cenários:
  - system-level custom op
  - instance-level custom op
  - 404 para op não registrada
  - CRUD Admin API
  - rate limit com resposta 429
- Resultado:
  - `pytest -q tests/test_custom_operations.py` → `5 passed`

### Pendências da ONDA_10
- `W10-B_CONCEPTMAP_TRANSLATE`: pendente (responsável DEV1).
