# F3 — Especificação Técnica: Portal Multi-Tenant

> **Módulo:** `intellicare-portal` (MODIFICAR)  
> **Stack:** React 18, TypeScript, Vite, React Router

---

## 1. Alterações Necessárias

### 1.1 — TenantContext (React Context)

**Arquivo NOVO:** `frontend/src/contexts/TenantContext.tsx`

```typescript
interface TenantInfo {
  tenantId: string;
  name: string;
  logoUrl?: string;
  primaryColor: string;
  secondaryColor: string;
  activeModules: string[];
}

const TenantContext = createContext<TenantInfo | null>(null);

export function TenantProvider({ children }: { children: React.ReactNode }) {
  const [tenant, setTenant] = useState<TenantInfo | null>(null);
  const [showSelector, setShowSelector] = useState(false);
  
  useEffect(() => {
    const token = getStoredToken();
    const decoded = jwtDecode(token);
    const tenants = decoded.tenants || [];
    const tenantId = decoded.tenant_id;
    
    if (!tenantId && tenants.length > 1) {
      // Multi-org: exibir tela de seleção
      setShowSelector(true);
      return;
    }
    
    if (!tenantId && tenants.length === 1) {
      // Auto-select: token exchange silencioso
      tokenExchange(token, tenants[0]).then(newToken => {
        storeToken(newToken);
        loadTenantInfo(tenants[0]);
      });
      return;
    }
    
    // Tenant já selecionado: carregar branding e módulos
    loadTenantInfo(tenantId);
  }, []);
  
  if (showSelector) {
    return <TenantSelectorPage onSelect={handleTenantSelect} />;
  }
  
  return <TenantContext.Provider value={tenant}>{children}</TenantContext.Provider>;
}
```

### 1.2 — CSS Variables Dinâmicas

**Arquivo MODIFICAR:** `frontend/src/index.css`

```css
:root {
  --color-primary: var(--tenant-primary, #1E88E5);
  --color-secondary: var(--tenant-secondary, #43A047);
  --logo-url: var(--tenant-logo, url('/intellicare-logo.svg'));
}
```

**Atualizar via JS:**
```typescript
function applyTenantBranding(tenant: TenantInfo) {
  document.documentElement.style.setProperty('--tenant-primary', tenant.primaryColor);
  document.documentElement.style.setProperty('--tenant-secondary', tenant.secondaryColor);
}
```

### 1.3 — Route Guard por Módulo

**Arquivo MODIFICAR:** `frontend/src/App.tsx`

```typescript
function ModuleRoute({ module, children }: { module: string; children: React.ReactNode }) {
  const tenant = useTenantContext();
  if (!tenant?.activeModules.includes(module)) {
    return <Navigate to="/dashboard" />;
  }
  return <>{children}</>;
}

// Uso:
<Route path="/oswaldo" element={
  <ModuleRoute module="oswaldo"><OswaldoPage /></ModuleRoute>
} />
```

### 1.4 — Dashboard Filtrado

**Arquivo MODIFICAR:** `frontend/src/pages/DashboardPage.tsx`

Filtrar `demoData.modules` usando `tenant.activeModules`:

```typescript
const filteredModules = modules.filter(m => tenant.activeModules.includes(m.id));
```

### 1.5 — Header com Branding

**Arquivo MODIFICAR:** `frontend/src/components/layout/Header.tsx`

- Exibir `tenant.name` e `tenant.logoUrl` ao invés do logo IntelliCare fixo
- Manter logo IntelliCare como fallback

---

## 2. Arquivos Afetados

| Arquivo | Ação | Descrição |
|---|---|---|
| `contexts/TenantContext.tsx` | NOVO | Context + Provider do tenant |
| `hooks/useTenantContext.ts` | NOVO | Hook para consumir o context |
| `App.tsx` | MODIFICAR | Wrap com `TenantProvider` + `ModuleRoute` |
| `index.css` | MODIFICAR | CSS variables dinâmicas |
| `components/layout/Header.tsx` | MODIFICAR | Branding do tenant |
| `pages/DashboardPage.tsx` | MODIFICAR | Filtrar módulos |
| `services/api.ts` | MODIFICAR | Headers com auth token |
| `utils/jwt.ts` | NOVO | Decode JWT para extrair tenant_id |

---

## 3. Dependências NPM Novas

```bash
npm install jwt-decode
```

---

## 4. Novos Componentes para Multi-Org

### 4.1 — TenantSelectorPage

**Arquivo NOVO:** `frontend/src/pages/TenantSelectorPage.tsx`

```typescript
interface TenantOption {
  tenantId: string;
  name: string;      // Buscar de /admin/tenants/{id}
  logoUrl?: string;
}

function TenantSelectorPage({ onSelect }: { onSelect: (tenantId: string) => void }) {
  const [tenants, setTenants] = useState<TenantOption[]>([]);
  
  // Buscar nomes/logos dos tenants disponíveis
  // GET /api/tenants/available (endpoint público que aceita token sem tenant_id)
  
  return (
    <div className="tenant-selector">
      <h1>Em qual organização deseja acessar?</h1>
      <div className="tenant-cards">
        {tenants.map(t => (
          <TenantCard key={t.tenantId} tenant={t} onClick={() => onSelect(t.tenantId)} />
        ))}
      </div>
    </div>
  );
}
```

### 4.2 — Token Exchange Service

**Arquivo NOVO:** `frontend/src/services/tokenExchange.ts`

```typescript
export async function tokenExchange(currentToken: string, tenantId: string): Promise<string> {
  const response = await fetch('/realms/bemcuidar/protocol/openid-connect/token', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({
      grant_type: 'urn:ietf:params:oauth:grant-type:token-exchange',
      subject_token: currentToken,
      requested_token_type: 'urn:ietf:params:oauth:token-type:access_token',
      audience: 'intellicare-portal',
      tenant_id: tenantId,
    }),
  });
  
  const data = await response.json();
  return data.access_token;
}
```

### 4.3 — OrgSwitcher (Menu Component)

**Arquivo NOVO:** `frontend/src/components/layout/OrgSwitcher.tsx`

```typescript
function OrgSwitcher() {
  const tenant = useTenantContext();
  const decoded = jwtDecode(getStoredToken());
  
  // Só exibir se usuário tem múltiplos tenants
  if (!decoded.tenants || decoded.tenants.length <= 1) return null;
  
  return (
    <button onClick={() => navigateToSelector()}>
      🏥 {tenant?.name} ▾ Trocar Organização
    </button>
  );
}
```

---

## 5. Arquivos Afetados (Atualizado)

| Arquivo | Ação | Descrição |
|---|---|---|
| `contexts/TenantContext.tsx` | NOVO | Context + Provider com lógica multi-org |
| `hooks/useTenantContext.ts` | NOVO | Hook para consumir o context |
| `pages/TenantSelectorPage.tsx` | NOVO | Tela de seleção de organização |
| `services/tokenExchange.ts` | NOVO | Token exchange com Keycloak |
| `components/layout/OrgSwitcher.tsx` | NOVO | Botão "Trocar Organização" no header |
| `utils/jwt.ts` | NOVO | Decode JWT para extrair tenant_id e tenants[] |
| `App.tsx` | MODIFICAR | Wrap com `TenantProvider` + `ModuleRoute` |
| `index.css` | MODIFICAR | CSS variables dinâmicas |
| `components/layout/Header.tsx` | MODIFICAR | Branding + OrgSwitcher |
| `pages/DashboardPage.tsx` | MODIFICAR | Filtrar módulos |
| `services/api.ts` | MODIFICAR | Headers com auth token |
