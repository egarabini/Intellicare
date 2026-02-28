# W10-A — Custom Operations Framework — Plano de Implementação

**Workstream:** W10-A
**Estimativa:** 21 dias
**Responsável:** DEV0 (execução DEV2 em 2026-02-25)
**Status Atual:** ✅ Concluído

---

## Ordem de Execução

| # | Task | Dias | Depende |
|---|------|------|---------|
| 1 | Modelo + migração `custom_operations` | 2 | — |
| 2 | CustomOperationRepository (CRUD) | 2 | 1 |
| 3 | CustomOpsService (lookup + validação) | 2 | 2 |
| 4 | Handler URL (HTTP POST externo) | 2 | 3 |
| 5 | Handler Bot (disparo de bot) | 2 | 3 |
| 6 | Router FHIR para $custom-op | 3 | 3, 4, 5 |
| 7 | Admin API para registro de ops | 2 | 2 |
| 8 | Rate limit + auditoria | 2 | 6 |
| 9 | Testes unitários + integração | 4 | 1-8 |

---

## Passo a Passo

### Passo 1: Modelo + Migração
- Criar tabela `custom_operations` no schema tenant
- Campos: tenant_id, name, type, resource_type, handler_type, handler_config, timeout_seconds
- Índice único: (tenant_id, name, resource_type)

### Passo 2: Repository
- `CustomOperationRepository.create/update/delete/get_by_tenant_and_name`
- Validação de nome (regex, blacklist nativas)

### Passo 3: CustomOpsService
- `lookup(tenant_id, name, resource_type?) -> CustomOperation | None`
- `execute(operation, request_params, resource?) -> Parameters`
- Orquestrar chamada ao handler

### Passo 4: Handler URL
- HTTP POST para URL configurada
- Passar Parameters + resource (se instance) no body
- Timeout configurável
- Tratar erros de rede

### Passo 5: Handler Bot
- Integrar com Bot Engine (intellicare-bots)
- Disparar bot com trigger "custom-op"
- Passar parâmetros como input
- Aguardar resposta (com timeout)

### Passo 6: Router FHIR
- Interceptar `POST /fhir/{ResourceType}/{id}/$op` quando $op não é nativo
- Interceptar `POST /fhir/$op` quando $op não é nativo
- Chamar CustomOpsService.execute
- Retornar Parameters ou recurso

### Passo 7: Admin API
- `GET/POST/PUT/DELETE /admin/custom-operations`
- Apenas para admins do tenant
- Validar handler_config antes de salvar

### Passo 8: Rate Limit + Auditoria
- Rate limit por (tenant_id, operation_name)
- AuditEvent para cada execução (success/failure)
- Métricas Prometheus (opcional)

### Passo 9: Testes
- `test_custom_operation_repository`
- `test_custom_ops_service_url_handler`
- `test_custom_ops_service_bot_handler`
- `test_custom_ops_router_instance`
- `test_custom_ops_router_system`
- `test_custom_ops_404_when_not_registered`

---

## Checklist de Entrega

- [x] Tabela custom_operations criada
- [x] CRUD de operações via Admin API
- [x] Instance-level custom op funcional
- [x] System-level custom op funcional
- [x] Handler URL funcional
- [x] Handler Bot funcional
- [x] Rate limit
- [x] Auditoria
- [x] Testes passando

---

## Evidências de Execução (2026-02-25)

### Código Implementado
- `grahame/models/custom_operation.py`
- `grahame/services/custom_operation_repository.py`
- `grahame/services/custom_ops_service.py`
- `grahame/api/routes/custom_operations_routes.py`
- `migrations/versions/20260225_1800_add_custom_operations.py`

### Integrações e Ajustes de Runtime
- Registro de rotas no `grahame/api/app.py`:
  - `POST /api/v1/fhir/{ResourceType}/{id}/$<op>`
  - `POST /api/v1/fhir/$<op>`
  - `GET/POST/PUT/DELETE /api/v1/admin/custom-operations`
- Importações opcionais com fallback em ambiente sem dependências externas:
  - `cds_hooks_routes`
  - `bulk_export_routes`
  - `terminology_routes`

### Testes
- Arquivo novo: `tests/test_custom_operations.py`
- Comando executado:
  - `pytest -q tests/test_custom_operations.py`
- Resultado:
  - `5 passed`
