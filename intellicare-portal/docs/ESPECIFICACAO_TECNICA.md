# intellicare-portal — Especificacao Tecnica

## 1. Estrutura

```
intellicare-portal/
├── src/
│   ├── components/
│   │   ├── home/               # Landing page
│   │   ├── agents/             # Catalogo de agentes
│   │   ├── dashboard/          # Dashboard dinamico
│   │   ├── forms/              # Formularios
│   │   └── common/             # Componentes compartilhados
│   ├── pages/
│   │   ├── HomePage.tsx
│   │   ├── AgentsPage.tsx
│   │   ├── AgentDetailPage.tsx
│   │   ├── DashboardPage.tsx   # NOVO: dashboard por modulo
│   │   └── RequestPage.tsx
│   ├── services/
│   │   ├── api.ts
│   │   └── moduleDiscovery.ts  # NOVO: detecta modulos ativos
│   ├── hooks/
│   │   └── useModules.ts       # NOVO: hook de modulos
│   ├── store/
│   │   └── moduleStore.ts      # NOVO: estado dos modulos
│   ├── types/
│   │   └── index.ts
│   ├── config/
│   │   └── modules.ts          # NOVO: URLs dos modulos
│   └── App.tsx
├── backend/                     # API Node.js (Fastify + Prisma)
│   ├── src/
│   │   ├── routes/
│   │   ├── services/
│   │   └── prisma/
│   ├── Dockerfile
│   └── package.json
├── Dockerfile                   # Multi-stage (frontend + nginx)
├── docker-compose.yml
├── package.json
└── vite.config.ts
```

## 2. Descoberta de Modulos

```typescript
// services/moduleDiscovery.ts

interface ModuleInfo {
  name: string;
  version: string;
  status: string;
  capabilities: string[];
}

class ModuleDiscovery {
  private modules: Map<string, ModuleInfo> = new Map();

  async discover(urls: string[]): Promise<ModuleInfo[]> {
    const results = await Promise.allSettled(
      urls.map(url => fetch(`${url}/api/v1/info`).then(r => r.json()))
    );
    // Registra modulos que responderam
    return results
      .filter(r => r.status === 'fulfilled')
      .map(r => r.value);
  }
}
```

## 3. Docker

```yaml
# docker-compose.yml
services:
  portal-frontend:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "3000:80"
    environment:
      - VITE_MODULE_URLS=http://localhost:8000,http://localhost:8001

  portal-backend:
    build:
      context: ./backend
    ports:
      - "4000:4000"
    environment:
      - DATABASE_URL=postgresql://portal:portal@db:5432/portal
    depends_on:
      - db

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: portal
      POSTGRES_PASSWORD: portal
      POSTGRES_DB: portal
```

## 4. Maturidade Atual: 6/10

- Frontend funcional (React 19, Sprint 1 completo)
- Backend funcional (Fastify + Prisma)
- Falta: descoberta de modulos, dashboard dinamico
