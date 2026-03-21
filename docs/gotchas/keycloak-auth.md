# Gotchas Keycloak e Auth

Entradas derivadas de DEM-004, DEM-045 e da configuracao real dos frontends GestorUI, ClinicoUI e PacienteUI.

## `VITE_KEYCLOAK_URL` ausente ou errado quebra login sem erro claro

### Situacao real
- Os tres frontends montam `authority` a partir de `import.meta.env.VITE_KEYCLOAK_URL`.
- Exemplos reais:
- [`frontend/GestorUI/src/auth/AuthProvider.tsx`](/c:/Users/egara/INTELLICARE/frontend/GestorUI/src/auth/AuthProvider.tsx)
- [`frontend/ClinicoUI/src/auth/AuthProvider.tsx`](/c:/Users/egara/INTELLICARE/frontend/ClinicoUI/src/auth/AuthProvider.tsx)
- [`frontend/PacienteUI/src/auth/AuthProvider.tsx`](/c:/Users/egara/INTELLICARE/frontend/PacienteUI/src/auth/AuthProvider.tsx)

### Sintoma
- Redirect vai para dominio errado, authority vira `undefined/realms/intellicare` ou o OIDC entra em loop de login.

### Fix
- Validar `VITE_KEYCLOAK_URL` no `.env` do frontend antes do build.
- Nao assumir que a URL do backend cobre o frontend.

## `redirect_uri` da SPA precisa apontar para a raiz publicada da app

### Situacao real
- GestorUI usa `/gestor-ui/`, ClinicoUI usa `/clinico-ui/` e PacienteUI usa `/paciente-ui/`.
- Nenhum deles usa rota `/callback`.

### Sintoma
- Login autentica no Keycloak, mas o retorno cai em rota inexistente e a SPA nao consome o codigo OIDC.

### Fix
- Configurar `redirect_uri` e `post_logout_redirect_uri` na raiz da SPA publicada, com barra final.

## Role de leitura tambem precisa entrar nos endpoints GET

### Situacao real
- Em [`modules/careplanner/api/routes.py`](/c:/Users/egara/INTELLICARE/modules/careplanner/api/routes.py), `get_video_session`, `get_task` e `list_tasks` aceitam `GESTOR` ou `CLINICO`.
- Esse ajuste foi necessario para DEM-045, quando o ClinicoUI passou a ler jornadas do CarePlanner.

### Sintoma
- Clinico autenticado recebe `403 forbidden` em endpoint de leitura que foi pensado so para GestorUI.

### Fix
- Quando um fluxo de leitura ganhar novo publico, revisar decorators e checks explicitos de role nos endpoints GET.

## Cada SPA tem `client_id` proprio e storage key diferente

### Situacao real
- `gestor-ui`, `clinico-ui` e `paciente-ui` usam `client_id` distintos.
- Os testes E2E do GestorUI gravam sessao em chave especifica, por exemplo `oidc.user:http://localhost:8080/realms/intellicare:gestor-ui`.

### Sintoma
- Sessao parece "sumir" ao trocar app ou ao reutilizar fixture de auth entre frontends diferentes.

### Fix
- Nao reaproveitar storage key ou fixture de OIDC sem alinhar `authority` e `client_id`.
- Em E2E, sempre conferir a combinacao realm + client da SPA testada.
