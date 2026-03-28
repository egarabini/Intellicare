# DEM-095 — Finalização

## Resumo

Foi registrada e corrigida uma falha de infraestrutura de frontend no ambiente de desenvolvimento local: proxies Vite com prefixos ambíguos estavam capturando rotas das próprias SPAs.

O caso observado diretamente foi:

- Portal redirecionando para `http://localhost:5174/admin-ui/`
- `AdminUI` não iniciando o fluxo do Keycloak
- causa real: `/admin-ui/` sendo interpretado como rota de proxy `/admin`

Em seguida, a mesma DEM recebeu uma Fase 2 complementar:

- o logout dos módulos autenticados precisava encerrar a sessão no Keycloak;
- após isso, o usuário deveria voltar ao Portal, e não permanecer na origem do módulo.

Na sequência, a Fase 3 consolidou esse comportamento como contrato de configuração:

- `VITE_PORTAL_URL` no frontend;
- `PORTAL_URL` no provisionamento;
- `PORTAL_URL` registrado no Keycloak como redirect/origin permitido.

## Entregas

### Fase 1 — proxies Vite

### Arquivos alterados

- `frontend/AdminUI/vite.config.ts`
- `frontend/GestorUI/vite.config.ts`
- `frontend/ClinicoUI/vite.config.ts`
- `frontend/PacienteUI/vite.config.ts`
- `frontend/Portal/vite.config.ts`

### Padrão adotado

Prefixos simples foram substituídos por regex exata com fronteira de rota:

```ts
'^/prefixo(?:/|$)'
```

Exemplos:

- `'^/admin(?:/|$)'`
- `'^/gestor(?:/|$)'`
- `'^/health(?:/|$)'`

### Fase 2 — logout centralizado

Arquivo novo:

- `frontend/shared/authUrls.ts`

Arquivos ajustados:

- `frontend/AdminUI/src/auth/AuthProvider.tsx`
- `frontend/GestorUI/src/auth/AuthProvider.tsx`
- `frontend/ClinicoUI/src/auth/AuthProvider.tsx`
- `frontend/PacienteUI/src/auth/AuthProvider.tsx`

Regra adotada:

- dev local → logout volta para `http://localhost:5176/`
- domínio oficial → logout volta para `https://intellicare.ia.br/`

### Fase 3 — contrato explícito de URL do Portal

Arquivos novos/ajustados:

- `frontend/shared/authUrls.ts`
- `.env` dos frontends com `VITE_PORTAL_URL`
- `infra/.env.example` com `PORTAL_URL`
- `tools/scripts/setup_keycloak.py` com `PORTAL_URL` em `redirectUris` e `webOrigins`

Regra final:

- frontend resolve o destino de logout via `VITE_PORTAL_URL`
- Keycloak aceita esse destino porque o client foi provisionado com `PORTAL_URL`

## Validação executada

Builds executados com sucesso:

- `frontend/AdminUI`
- `frontend/GestorUI`
- `frontend/ClinicoUI`
- `frontend/PacienteUI`
- `frontend/Portal`

Também foi confirmado que o `AdminUI` passou a responder corretamente em `http://127.0.0.1:5174/admin-ui/` sem ser sequestrado pelo proxy `/admin`.

Na Fase 2, os módulos autenticados também passaram em build após a troca para `getPortalUrl()`:

- `frontend/AdminUI`
- `frontend/GestorUI`
- `frontend/ClinicoUI`
- `frontend/PacienteUI`

Na Fase 3:

- os 4 módulos autenticados passaram novamente em build após a introdução de `VITE_PORTAL_URL`
- `setup_keycloak.py` foi reexecutado localmente com `PORTAL_URL=http://localhost:5176`
- os clients do realm foram realinhados com o redirect do logout

## Commit publicado

```text
ca02c52 - fix(frontend): padroniza proxies Vite com match exato
60c552f - fix(auth): logout retorna ao portal
commit da Fase 3: fix(auth): padroniza portal url no logout e no Keycloak
```

## Lição registrada

Em frontends Vite servidos sob subpaths como `/admin-ui/`, `/gestor-ui/`, `/clinico-ui/` e `/paciente-ui/`, proxies baseados em prefixos curtos devem sempre usar fronteira explícita de rota. Caso contrário, o dev server pode confundir rota de SPA com rota de API e quebrar autenticação, bootstrap e navegação local.

Além disso, quando múltiplos módulos compartilham o mesmo provedor OIDC, o destino de logout não deve depender implicitamente da origem atual do módulo. O redirecionamento pós-logout precisa apontar explicitamente para o Portal para manter a navegação coerente entre ambientes.

E esse destino deve existir como contrato explícito em dois lados:

- frontend: `VITE_PORTAL_URL`
- realm/provisionamento: `PORTAL_URL` incluído nos clients OIDC
