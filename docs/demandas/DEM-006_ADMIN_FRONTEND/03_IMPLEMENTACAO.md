# DEM-006 - Implementacao

## Arquivos criados

- `frontend/AdminUI/package.json`
- `frontend/AdminUI/package-lock.json`
- `frontend/AdminUI/tsconfig.json`
- `frontend/AdminUI/vite.config.ts`
- `frontend/AdminUI/index.html`
- `frontend/AdminUI/.env.local`
- `frontend/AdminUI/src/main.tsx`
- `frontend/AdminUI/src/App.tsx`
- `frontend/AdminUI/src/vite-env.d.ts`
- `frontend/AdminUI/src/auth/AuthProvider.tsx`
- `frontend/AdminUI/src/auth/TokenSync.tsx`
- `frontend/AdminUI/src/api/client.ts`
- `frontend/AdminUI/src/components/StatusBadge.tsx`
- `frontend/AdminUI/src/hooks/useTenants.ts`
- `frontend/AdminUI/src/pages/DashboardPage.tsx`
- `frontend/AdminUI/src/pages/TenantList.tsx`
- `frontend/AdminUI/src/pages/TenantForm.tsx`
- `frontend/AdminUI/src/pages/TenantDetail.tsx`
- `tools/scripts/build_admin_ui.sh`
- `packages/intellicare-core/intellicare_service/__init__.py`
- `packages/intellicare-core/intellicare_service/app.py`

## Arquivos alterados

- `tools/scripts/setup_keycloak.py`
- `packages/intellicare-core/pyproject.toml`
- `packages/intellicare-core/intellicare_core/main.py`
- `infra/keycloak/realm-export.json`

## Decisoes de implementacao

- O frontend foi criado em `frontend/AdminUI` com React + TypeScript + Vite.
- A autenticacao usa Keycloak via OIDC (`react-oidc-context`) com armazenamento do access token apenas em memoria e sincronizacao em `sessionStorage` para o interceptor do Axios.
- O build de producao gera artefatos em `packages/intellicare-core/intellicare_core/static/admin-ui`, permitindo servir a SPA pelo mesmo processo FastAPI.
- Foi criado um entrypoint compatível com o `deploy/Dockerfile` em `intellicare_service.app:app`, reaproveitando `intellicare_core.main`.
- O script `setup_keycloak.py` passou a garantir o client publico `admin-ui`, com redirect URIs para `http://localhost:5174/*` e `http://localhost:8000/admin-ui/*`.

## Validacoes executadas

- `npm run build` em `frontend/AdminUI`
- `python -m pip install -e packages\intellicare-core[dev]`
- `python tools\scripts\setup_keycloak.py`
- `docker exec intellicare-keycloak /opt/keycloak/bin/kc.sh export --realm intellicare --dir /tmp --users same_file`
- `docker cp intellicare-keycloak:/tmp/intellicare-realm.json infra/keycloak/realm-export.json`
- `python -c "from fastapi.testclient import TestClient; from intellicare_service.app import app; ..."` validando:
  - `GET /health` -> `200`
  - `GET /admin-ui/` -> `200`

## Desvios da spec

- O `build_admin_ui.sh` foi tornado tolerante à ausência de `package-lock.json`: usa `npm ci` quando o lockfile existe e `npm install` caso contrário. Isso foi necessário porque a spec pedia build reproducível, mas o frontend ainda não tinha lockfile versionado.
- Foi adicionado `src/vite-env.d.ts` porque o build TypeScript falhava com `Property 'env' does not exist on type 'ImportMeta'`.
- O backend atual publica o módulo admin em `/admin/admin/...` por combinação do `ModuleLoader` com o prefixo já definido no router. Para não ampliar o escopo da DEM-006, o frontend foi alinhado a esse path real em `VITE_API_BASE_URL=http://localhost:8000/admin/admin`.
- O entrypoint FastAPI da DEM-006 foi mantido carregando apenas `admin`. A tentativa de incluir `gestor` falhou por um problema preexistente em `intellicare_core.vector.__init__`, que importa `generate` de `embeddings.py` sem essa função existir.

## Resultado

- AdminUI buildado e empacotado no backend.
- Client `admin-ui` provisionado no Keycloak ativo e refletido no `realm-export.json`.
- Serviço Python consegue responder `/health` e servir `/admin-ui/` a partir do pacote `intellicare-core`.
