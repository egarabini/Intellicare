# DEM-095 — Especificação Técnica

## Causa raiz

O `server.proxy` do Vite faz matching por prefixo. Isso significa:

- `'/admin'` também casa com `/admin-ui/...`
- `'/gestor'` também casa com `/gestor-ui/...`

No caso do `AdminUI`, a própria rota da SPA foi enviada para o proxy do backend, produzindo erro interno no dev server e impedindo que o frontend carregasse o suficiente para iniciar `signinRedirect()` com Keycloak.

## Estratégia

### Fase 1 — match exato nos proxies Vite

Trocar os prefixos simples por regex explícita com fronteira de rota:

```ts
'^/admin(?:/|$)': 'http://localhost:8000'
```

Esse padrão garante que:

- `/admin`
- `/admin/tenants`

continuam sendo tratados como API, mas:

- `/admin-ui/`

não é mais capturado.

### Fase 2 — logout centralizado no Portal

Após a correção dos proxies, surgiu um ajuste complementar de UX e integração:

- ao clicar em `Sair` dentro dos módulos autenticados;
- a sessão do Keycloak devia ser encerrada;
- o usuário devia voltar ao Portal, e não permanecer na origem do módulo.

Para isso, o `post_logout_redirect_uri` deixou de usar `window.location.origin` e passou a usar uma resolução centralizada da URL do Portal.

### Fase 3 — `PORTAL_URL` e `VITE_PORTAL_URL` como contrato explícito

Na validação da Fase 2, o Keycloak passou a responder `invalid redirect uri` no logout.

Causa raiz:

- o frontend já apontava para o Portal como destino pós-logout;
- porém o client do Keycloak não tinha esse redirect registrado de forma explícita e padronizada;
- além disso, a URL do Portal ainda dependia parcialmente de heurística em runtime.

Correção adotada:

- criar `VITE_PORTAL_URL` como variável pública de frontend;
- criar/manter `PORTAL_URL` como variável de referência de infraestrutura/provisionamento;
- usar `VITE_PORTAL_URL` no helper compartilhado de autenticação;
- incluir `PORTAL_URL` nos `redirectUris` e `webOrigins` dos clients OIDC provisionados por `setup_keycloak.py`.

## Helper compartilhado

Arquivo criado:

```ts
frontend/shared/authUrls.ts
```

Responsabilidade:

- em dev local, retornar `http://localhost:5176/`
- em domínio `*.intellicare.ia.br`, retornar `https://intellicare.ia.br/`
- em fallback, retornar a `origin` atual

Na Fase 3, o helper passou a priorizar:

```ts
import.meta.env.VITE_PORTAL_URL
```

com fallback apenas se a variável não estiver definida.

## Arquivos e ajustes

### `frontend/AdminUI/vite.config.ts`

Antes:

```ts
'/admin': 'http://localhost:8000',
'/health': 'http://localhost:8000',
```

Depois:

```ts
'^/admin(?:/|$)': 'http://localhost:8000',
'^/health(?:/|$)': 'http://localhost:8000',
```

### `frontend/GestorUI/vite.config.ts`

Antes:

```ts
'/gestor': 'http://localhost:8000',
'/vector': 'http://localhost:8000',
```

Depois:

```ts
'^/gestor(?:/|$)': 'http://localhost:8000',
'^/vector(?:/|$)': 'http://localhost:8000',
```

### `frontend/ClinicoUI/vite.config.ts`

Padronização preventiva:

```ts
'^/cuidado(?:/|$)': 'http://localhost:8000',
'^/gestor(?:/|$)': 'http://localhost:8000',
'^/slm(?:/|$)': 'http://localhost:8000',
'^/vector(?:/|$)': 'http://localhost:8000',
'^/auth(?:/|$)': 'http://localhost:8000',
```

### `frontend/PacienteUI/vite.config.ts`

Padronização preventiva:

```ts
'^/cuidado(?:/|$)': 'http://localhost:9000',
'^/health(?:/|$)': 'http://localhost:9000',
```

### `frontend/Portal/vite.config.ts`

Padronização preventiva:

```ts
'^/health(?:/|$)': 'http://localhost:8000',
```

### `frontend/*/src/auth/AuthProvider.tsx`

Ajuste de Fase 2:

Antes:

```ts
post_logout_redirect_uri: `${window.location.origin}/`
```

Depois:

```ts
post_logout_redirect_uri: getPortalUrl()
```

Aplicado em:

- `frontend/AdminUI/src/auth/AuthProvider.tsx`
- `frontend/GestorUI/src/auth/AuthProvider.tsx`
- `frontend/ClinicoUI/src/auth/AuthProvider.tsx`
- `frontend/PacienteUI/src/auth/AuthProvider.tsx`

### Variáveis padronizadas de ambiente

Frontend:

```text
VITE_PORTAL_URL=http://localhost:5176
VITE_PORTAL_URL=https://intellicare.ia.br
```

Infra/provisionamento:

```text
PORTAL_URL=http://localhost:5176
```

Arquivos ajustados:

- `frontend/AdminUI/.env.local`
- `frontend/AdminUI/.env.production`
- `frontend/GestorUI/.env.local`
- `frontend/GestorUI/.env.production`
- `frontend/ClinicoUI/.env.local`
- `frontend/ClinicoUI/.env.production`
- `frontend/PacienteUI/.env`
- `frontend/PacienteUI/.env.production`
- `frontend/Portal/.env.local`
- `frontend/Portal/.env.production`
- `infra/.env.example`

### `tools/scripts/setup_keycloak.py`

Fase 3:

- `PORTAL_URL` passa a ser usado explicitamente no provisionamento;
- clients `admin-ui`, `gestor-ui`, `clinico-ui` e `paciente-ui` recebem `PORTAL_URL` em:
  - `redirectUris`
  - `webOrigins`

Isso alinha o destino de logout do frontend com os redirects permitidos no realm.

## Validação técnica

Comandos usados para validar a integridade após a mudança:

```bash
cd frontend/AdminUI && npm run build
cd frontend/GestorUI && npm run build
cd frontend/ClinicoUI && npm run build
cd frontend/PacienteUI && npm run build
cd frontend/Portal && npm run build
```

## Commit de referência

```text
ca02c52 - fix(frontend): padroniza proxies Vite com match exato
60c552f - fix(auth): logout retorna ao portal
commit da Fase 3: fix(auth): padroniza portal url no logout e no Keycloak
```
