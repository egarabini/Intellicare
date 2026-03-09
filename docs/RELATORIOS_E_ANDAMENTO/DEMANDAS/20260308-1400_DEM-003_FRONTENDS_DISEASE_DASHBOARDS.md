# DEM-003 — Frontends React + Disease Dashboards (Admin e Gestor)

| Campo | Valor |
|---|---|
| **ID** | DEM-003 |
| **Título** | Frontends React para Admin e Gestor + endpoints Donabedian (4 programas de saúde) |
| **Módulos** | intellicare-admin-frontend, intellicare-gestor-frontend, intellicare-donabedian |
| **Prioridade** | 🟡 ALTA |
| **Status** | DEPLOYED (dev2 — entrega concluída em 2026-03-08) |
| **Dev responsável** | dev2 |
| **Branch** | A confirmar com dev2 |
| **Data entrega** | 2026-03-08 |

---

## O que foi entregue

### 1. Gestor Frontend

- **Stack:** React 19 + Vite 7 + TypeScript + Tailwind 4 + Recharts + Leaflet
- **Porta:** 5174 (dev) / 3002 (Docker)
- **Auth:** Keycloak PKCE com cliente `intellicare-gestor` (realm `intellicare`)
- **Rota Traefik:** `gestor.intellicare.ia.br` → nginx → React SPA + `/api/*` → gestor backend
- **Conteúdo:** Dashboards dos 4 programas prioritários:
  - DRC (Doença Renal Crônica)
  - Diabetes
  - Hipertensão
  - Câncer
- **Visualizações:** KPIs, linhas de tendência, distribuição de estágios (barra/pizza), mapa geográfico (Leaflet), tabela de pacientes
- **Fallback:** mock data quando API indisponível (`VITE_SKIP_AUTH=true` para dev)

### 2. Admin Frontend

- **Stack:** Mesma stack do gestor
- **Porta:** 5175 (dev) / 3003 (Docker)
- **Auth:** Keycloak PKCE com cliente `intellicare-admin` (realm `intellicare`)
- **Rota Traefik:** `admin.intellicare.ia.br` → nginx → React SPA + `/api/*` → admin backend
- **Diferencial em relação ao gestor:**
  - Visão cross-tenant (todos os tenants da plataforma)
  - Página Tenants: comparação entre tenants
  - Página Consolidado Nacional: agregação nationwide
  - Identidade visual: esquema índigo + Shield na sidebar

### 3. Endpoints Donabedian — disease_dashboard.py

Novos endpoints no módulo `intellicare-donabedian` (registrado em `main.py:103`):

```
GET /api/v1/dashboard/disease/{code}          ← dashboard completo
GET /api/v1/dashboard/disease/{code}/kpis     ← indicadores principais
GET /api/v1/dashboard/disease/{code}/trends   ← tendências temporais
GET /api/v1/dashboard/disease/{code}/stages   ← distribuição de estágios
GET /api/v1/dashboard/disease/{code}/geo      ← distribuição geográfica
GET /api/v1/dashboard/disease/{code}/patients ← listagem de pacientes
```

Códigos suportados: mapeamento ICD-10 para DRC, Diabetes, Hipertensão, Câncer.
Inclui gerador de mock data com dados estágio-aware para cada doença.

### 4. Docker e Deploy

- Dockerfiles criados para ambos os frontends (build Node → nginx produção)
- `nginx.conf` com proxy reverso `/api/*` para backends gestor/admin e donabedian
- Serviços `gestor-frontend` e `admin-frontend` adicionados ao `docker-compose.full.yml`
- Rotas Traefik atualizadas para servir os SPAs

---

## Mudança arquitetural relevante

Esta entrega altera a arquitetura dos módulos admin e gestor:

| | Antes (DEM-002 spec) | Depois (DEM-003 entrega) |
|---|---|---|
| `admin.intellicare.ia.br` | FastAPI serve `dashboard.html` diretamente | nginx serve React SPA; `/api/*` vai para FastAPI |
| `gestor.intellicare.ia.br` | FastAPI serve API pura (sem HTML) | nginx serve React SPA; `/api/*` vai para FastAPI |

A arquitetura nginx + SPA é a abordagem correta para produção.
O `dashboard.html` do admin (Python template) permanece como fallback de desenvolvimento.

---

## Pendente para revisão com Eduardo

- [ ] Confirmar que os dashboards de doenças só aparecem para establishments registrados (não para todos os tenants)
- [ ] Validar que o `VITE_SKIP_AUTH=true` está removido dos ambientes de staging/produção
- [ ] Confirmar branch do dev2 para PR
- [ ] FASE 4 do DEM-002 (smoke test integrado) — pendente correção das 2 rotas pelo dev1

---

## Aprendizados

- Dashboards de doenças crônicas ficam nos frontends React de admin e gestor
- A separação nginx (SPA) + FastAPI (API) é o padrão definitivo para esses módulos
- Mock data com fallback é boa prática para desenvolvimento desconectado
