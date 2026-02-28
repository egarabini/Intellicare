# W8-B — Diário de Execução

## 2026-02-26 — Validação de fechamento (DEV2)

### Validação funcional
- Execução da suíte HL7v2 principal:
  - `pytest -q tests/hl7v2 tests/test_hl7v2_api_key_model.py tests/test_hl7v2_audit_model.py tests/test_hl7v2_auth_dependency.py -k "not audit_endpoints"`
  - Resultado: **92 passed**

### Bloqueios observados
- Suítes de endpoint/admin que inicializam `grahame.api.app` falham em coleta por dependência de bootstrap:
  - erro: `ModuleNotFoundError: No module named 'grahame.database'`
- Testes de `audit_endpoints` dependem de fixture `client` não registrada no contexto atual.

### Encaminhamento
- W8-B foi considerado concluído para ONDA_8 no escopo de desenvolvimento.
- Pendência pós-onda: alinhar `tests/api/test_hl7v2_endpoint.py` ao requisito atual de autenticação por `X-API-Key`.

## 2026-02-26 — Atualização de Pendências (DEV2)

### Correções aplicadas
- Ajuste de bootstrap do app para tornar Excalidraw opcional quando dependências extras não estão presentes.
- Correção de import em `excalidraw_routes.py` (`grahame.api.deps.get_db`).
- Reativação de fixtures em `tests/conftest.py` (`client` + `db_session`).
- Ajustes de compatibilidade em autenticação/dependencies para patch dinâmico em testes.

### Evidências
- `pytest -q tests/api/test_hl7v2_admin_endpoints.py tests/api/test_hl7v2_endpoint_auth.py` → **18 passed**
- `pytest -q tests/test_hl7v2_audit_endpoints.py` → **8 passed**
