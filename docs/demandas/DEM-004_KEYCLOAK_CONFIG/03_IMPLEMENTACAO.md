# DEM-004 - Implementacao

## Arquivos alterados

- `infra/keycloak/realm-export.json`
- `infra/.env.example`

## Arquivos criados

- `tools/scripts/setup_keycloak.py`
- `tools/scripts/test_keycloak.py`

## Decisoes tomadas

- A configuracao do realm foi aplicada programaticamente pela Admin REST API via `tools/scripts/setup_keycloak.py`, e depois exportada do container para versionamento.
- O setup atualiza realm, roles, grupo `tenant_dev`, clients e usuarios de desenvolvimento de forma idempotente.
- O teste `tools/scripts/test_keycloak.py` valida o fluxo real: password grant no Keycloak -> `verify_token()` do `intellicare_core` -> `TenantContext`.
- O `infra/.env.example` foi ampliado com as variaveis de client secret e URLs do Keycloak esperadas pelos scripts e pela aplicacao.

## Desvios da especificacao

- O mapper `tenant_id` foi implementado como `oidc-usermodel-attribute-mapper`, nao `oidc-group-attribute-mapper`. Na pratica, isso foi o caminho confiavel para emitir `tenant_id` no JWT do ambiente atual.
- Os usuarios `gestor-dev` e `clinico-dev` recebem `attributes.tenant_id=["dev"]` diretamente. Isso mantem compatibilidade com a DEM-003, onde `verify_token()` construi `schema = tenant_{tenant_id}`.
- O valor de `tenant_id` emitido no token ficou `dev`, nao `tenant_dev`. Esse ajuste e intencional: `tenant_dev` como claim faria o core montar `tenant_tenant_dev`.
- A exportacao do realm nao funcionou pela Admin API (`404` no endpoint testado). O estado real foi exportado com `docker exec intellicare-keycloak /opt/keycloak/bin/kc.sh export --realm intellicare --dir /tmp --users same_file` e copiado com `docker cp`.

## Validacao executada

- `curl http://localhost:8080/realms/intellicare/.well-known/openid-configuration`
- `python tools/scripts/setup_keycloak.py`
- `python tools/scripts/setup_keycloak.py` novamente para validar idempotencia
- password grant para `platform-admin / Admin@2025!`
- password grant para `gestor-dev / Gestor@2025!`
- password grant para `clinico-dev / Clinico@2025!`
- `python tools/scripts/test_keycloak.py`
- inspecao direta do token do `gestor-dev` confirmando claim `tenant_id=dev`
- inspecao direta do token do `platform-admin` confirmando role `PLATFORM_ADMIN`

## Resultado

- Realm `intellicare` operacional e configurado.
- Roles `PLATFORM_ADMIN`, `TENANT_GESTOR`, `CLINICO` e `PACIENTE` presentes.
- Grupo `tenant_dev` criado.
- Clients `intellicare-service` e `intellicare-frontend` presentes.
- Usuarios `platform-admin`, `gestor-dev` e `clinico-dev` criados/atualizados.
- JWT do `gestor-dev` e `clinico-dev` inclui `tenant_id=dev`.
- `verify_token()` retorna `TenantContext` com `tenant_id=dev` e `schema=tenant_dev`.

## Observacoes

- O `infra/.env` local foi atualizado para incluir `KEYCLOAK_CLIENT_SECRET`, `KEYCLOAK_URL`, `KEYCLOAK_REALM`, `KEYCLOAK_CLIENT_ID` e `KEYCLOAK_INTERNAL_URL`; esse arquivo nao foi commitado.
- O workspace ainda emite warnings ao listar alguns diretorios temporarios de `pip/pytest` criados em DEMs anteriores. Eles nao entraram no diff da DEM-004.
