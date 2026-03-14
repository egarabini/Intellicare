# DEM-021 — Fix Frontends: Token + Rebuild Docker

## Contexto

O AdminUI teve 3 bugs corrigidos no commit `4b4fbe6` (código já no repositório).
O GestorUI tem os **mesmos bugs** e precisa da mesma correção.
Após os fixes, reconstruir a imagem Docker e validar.

---

## Tarefa 1 — Aplicar padrão tokenRef no GestorUI

O AdminUI já foi corrigido e serve de referência.
Aplicar o mesmo padrão em `frontend/GestorUI/src/`.

### 1.1 Criar `src/auth/tokenRef.ts`

Copiar identicamente de `frontend/AdminUI/src/auth/tokenRef.ts`:

```ts
let _token: string | null = null
export function getToken(): string | null { return _token }
export function setToken(token: string | null): void { _token = token }
```

### 1.2 Atualizar `src/api/client.ts`

```ts
import axios, { InternalAxiosRequestConfig } from 'axios'
import { getToken } from '../auth/tokenRef'

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? '',
  timeout: 30_000,
})

apiClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = getToken()
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

export default apiClient
```

> Nota: GestorUI usa `baseURL: ''` (paths relativos como `/gestor/patients`).
> Não mudar o baseURL — está correto para o Gestor.

### 1.3 Atualizar `src/App.tsx` — setar token sincronamente

No componente `AppRoutes`, **antes de qualquer JSX**, adicionar:

```tsx
import { setToken } from './auth/tokenRef'

function AppRoutes() {
  const auth = useAuth()

  // Token síncrono — antes de qualquer query disparar
  setToken(auth.user?.access_token ?? null)

  // ... resto do componente (isLoading, isAuthenticated, etc.)
}
```

Remover o `<TokenSync />` do JSX se existir — ele não é mais necessário.

### 1.4 Verificar `.env.local` do GestorUI

```
dir frontend\GestorUI\.env*
```

Se existir um `.env.local` com `VITE_API_BASE_URL` apontando para porta ou path errados,
comentar ou remover a linha. O default `''` (string vazia) é o correto para o Gestor.

### 1.5 Rebuild GestorUI

```bash
cd frontend/GestorUI
npm run build
```

Confirmar que o build foi para `packages/intellicare-core/intellicare_core/static/gestor-ui/`.

---

## Tarefa 2 — Rebuild Docker e restart

Após todos os fixes de frontend:

```bash
cd C:\Users\egara\INTELLICARE
docker compose --env-file infra/.env -f infra/docker-compose.yml build intellicare-service
docker compose --env-file infra/.env -f infra/docker-compose.yml up -d --no-deps intellicare-service
```

---

## Tarefa 3 — Validação pós-deploy

### 3.1 AdminUI

```
http://127.0.0.1:9000/admin-ui/
```
Login: `platform-admin` / `Admin@2025!`

Checklist:
- [ ] Sidebar exibe: Dashboard | Tenants | Auditoria
- [ ] Dashboard mostra KPIs reais (tenants=3, não zeros)
- [ ] Menu Tenants abre lista com clinica_alfa, hospital_beta, consultorio_gamma
- [ ] Network DevTools: `/admin/dashboard/stats` retorna **200** (não 401)

### 3.2 GestorUI

```
http://127.0.0.1:9000/gestor-ui/
```
Login: `gestor.alfa` / `Demo@1234`

Checklist:
- [ ] Sidebar exibe todos os itens (Dashboard, Pacientes, Agenda, etc.)
- [ ] Dashboard mostra KPIs reais do tenant clinica_alfa
- [ ] Network DevTools: `/gestor/dashboard/stats` retorna **200** (não 401)
- [ ] Lista de pacientes carrega (seed criou 50 pacientes por tenant)

---

## Commit esperado

```
fix(frontends): token sincrono GestorUI + rebuild docker
```

Incluir no commit:
- `frontend/GestorUI/src/auth/tokenRef.ts` (novo)
- `frontend/GestorUI/src/api/client.ts` (modificado)
- `frontend/GestorUI/src/App.tsx` (modificado)
- `packages/intellicare-core/intellicare_core/static/gestor-ui/` (novo build)
