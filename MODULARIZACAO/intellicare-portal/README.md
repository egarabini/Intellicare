# intellicare-portal

Interface web unificada do ecossistema IntelliCare.

Detecta automaticamente quais modulos estao ativos e monta o dashboard correspondente. Funciona com 1 modulo ou com todos — arquitetura LEGO.

## O que faz

- **Module Discovery**: Detecta modulos ativos via `/api/v1/info` com polling automatico
- **Dashboard dinamico**: Adapta UI conforme modulos disponiveis e suas capabilities
- **Catalogo de agentes**: 6 agentes nomeados com descricao, features e status
- **Gestao de acesso**: Formularios de solicitacao por secretaria/unidade de saude
- **Compliance**: LGPD, termos, privacidade, cookies
- **Status real-time**: Pagina `/modulos` mostra health de cada modulo

## Tech Stack

- React 19 + TypeScript 5.9
- Vite 7 (build)
- Tailwind CSS 4 (estilos)
- Zustand 5 (state management)
- React Router 7 (routing)
- Recharts 3 (graficos)
- Framer Motion 12 (animacoes)
- Vitest 4 (testes)

## Desenvolvimento

```bash
cd frontend
pnpm install
pnpm dev        # dev server em http://localhost:5173
pnpm build      # build de producao
pnpm vitest run # testes
```

## Docker

```bash
docker compose up -d    # portal em http://localhost:3000
```

## Arquitetura LEGO

O portal descobre modulos automaticamente consultando suas APIs:

```
Portal (3000) ──> Oswaldo (8001) /api/v1/info
               ──> Florence (8002) /api/v1/info
               ──> Zilda (8003) /api/v1/info
               ──> Donabedian (8004) /api/v1/info
```

### Arquivos novos (module discovery)

| Arquivo | Descricao |
|---------|-----------|
| `src/config/modules.ts` | Registro de modulos conhecidos e suas URLs |
| `src/services/moduleDiscovery.ts` | Servico de discovery (fetch /api/v1/info + /health) |
| `src/store/moduleStore.ts` | Store Zustand com estado dos modulos |
| `src/hooks/useModules.ts` | Hook React com polling automatico |
| `src/pages/ModulesPage.tsx` | Pagina `/modulos` com status real-time |

### Variaveis de ambiente

```env
VITE_OSWALDO_URL=http://localhost:8001
VITE_FLORENCE_URL=http://localhost:8002
VITE_ZILDA_URL=http://localhost:8003
VITE_DONABEDIAN_URL=http://localhost:8004
VITE_COMUNICACAO_URL=http://localhost:8005
```

## Rotas

| Rota | Pagina |
|------|--------|
| `/` | Home (landing page) |
| `/agentes` | Catalogo de agentes |
| `/agentes/:slug` | Detalhe do agente |
| `/dashboards` | Dashboards |
| `/modulos` | Status dos modulos LEGO (NOVO) |
| `/solicitacao` | Formulario de solicitacao |
| `/acompanhamento/:protocol?` | Acompanhar solicitacao |
| `/status` | Status dos servicos |
| `/sobre` | Sobre o projeto |
| `/contato` | Formulario de contato |
| `/faq` | Perguntas frequentes |
| `/lgpd` | Politica LGPD |

## Metricas

- **14 paginas** + 1 nova (ModulesPage)
- **37 componentes** React
- **6 testes** (module discovery)
- Build de producao com code splitting (4 chunks)
