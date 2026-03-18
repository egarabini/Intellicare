---
tipo: plano-execucao
demanda: DEM-040
titulo: CarePlanner UI Completo — GestorUI
status: pendente
dev: CODEX
criado: 2026-03-18
---

# DEM-040 — Plano de Execução

## Estimativa

Tempo estimado: 2–3h | Complexidade: média

Todo o backend está pronto; é trabalho de frontend puro. O maior risco é a
integração do `@mantine/form` e o roteamento do React Router para o detalhe.

---

## STEPs

### STEP-001 — Instalar dependência `@mantine/form` (se ausente)

**Status:** pendente

```bash
cd frontend/GestorUI
npm list @mantine/form | grep mantine
```

Se não estiver instalado:
```bash
npm install @mantine/form
```

Critério: `npm list @mantine/form` retorna a versão sem `UNMET DEPENDENCY`.

---

### STEP-002 — Adicionar tipos e hooks em `useGestor.ts`

**Status:** pendente

Arquivo: `src/hooks/useGestor.ts`

Ação: Adicionar ao final do arquivo (sem alterar nenhum hook existente):
- Interfaces: `CareTask`, `CareEvent`, `CareConversation`, `CareTaskDetail`,
  `CareTaskList`, `TriggerJourneyPayload`, `TriggerJourneyResult`, `VideoSession`
- Hooks: `useCareplannerTasks`, `useCareplannerTask`, `useVideoSession`,
  `useTriggerJourney`, `useCloseTask`

Verificar imports: `useMutation`, `useQueryClient` de `@tanstack/react-query`
e `api` de `../api/client` devem já estar no arquivo. Adicionar se faltarem.

Critério: `npm run build` sem erros de TypeScript em `useGestor.ts`.

---

### STEP-003 — Criar `components/TriggerJourneyModal.tsx`

**Status:** pendente

Arquivo novo: `src/components/TriggerJourneyModal.tsx`

Implementar conforme Bloco 4 de `02_TECNICA.md`.

Atenção: `@mantine/form` exporta `useForm` — diferente de `react-hook-form`.
O Mantine form usa `form.getInputProps('campo')` para spreador nos inputs.

Critério: componente renderiza sem erros; modal abre/fecha corretamente no browser.

---

### STEP-004 — Criar `pages/CareplannerJourneyDetail.tsx`

**Status:** pendente

Arquivo novo: `src/pages/CareplannerJourneyDetail.tsx`

Implementar conforme Bloco 5 de `02_TECNICA.md`.

Verificar: `@mantine/modals` precisa estar em `package.json` e o `ModalsProvider`
precisa envolver o app em `App.tsx`. Se não estiver:

```bash
npm install @mantine/modals
```

E em `App.tsx`, dentro de `<MantineProvider>`:
```tsx
import { ModalsProvider } from '@mantine/modals'
// envolver:
<ModalsProvider>
  {/* ... resto da app */}
</ModalsProvider>
```

Critério: navegar para `/careplanner/jornadas/qualquer-uuid` renderiza a tela
de detalhe (mesmo que com erro de 404 do backend em dev).

---

### STEP-005 — Refatorar `pages/CareplannerDashboard.tsx`

**Status:** pendente

Ação: Substituir o conteúdo do arquivo conforme Bloco 3 de `02_TECNICA.md`.

Os cards de status permanecem no topo; a lista de "Atividade Recente" é substituída
pela lista paginada com filtro + botão "Nova Jornada" + `TriggerJourneyModal`.

Importar `useState` do React se não estiver. Importar `useNavigate` do `react-router-dom`.

Critério: cards de status exibem os contadores corretamente; lista de jornadas carrega;
clique em uma linha navega para `/careplanner/jornadas/:id`.

---

### STEP-006 — Adicionar rota em `App.tsx`

**Status:** pendente

Ação:
1. Importar `CareplannerJourneyDetail` de `./pages/CareplannerJourneyDetail`
2. Adicionar `<Route path="/careplanner/jornadas/:id" element={<CareplannerJourneyDetail />} />`
   logo após a rota `/careplanner` existente

Critério: `npm run build` sem erros; rota funciona no browser.

---

### STEP-007 — Adicionar testes Playwright

**Status:** pendente

Arquivo: `e2e/careplanner.spec.ts`

Ação: Adicionar os 3 testes do Bloco 6 de `02_TECNICA.md` ao final do arquivo,
sem remover ou alterar os 4 testes existentes.

Executar:
```bash
npm run test:e2e
```

Critério: 7 passed (4 existentes + 3 novos), 0 failed.

Observação: se houver 404 em `/notifications/*` ou `/gestor/dashboard/stats`
nos novos testes, é comportamento esperado (já documentado na Fase D da DEM-038).
Não é necessário mockar essas rotas a menos que causem falha nos testes.

---

### STEP-008 — Build e commit

**Status:** pendente

```bash
cd frontend/GestorUI
npm run build
```

```bash
cd C:\Users\egara\INTELLICARE

del .git\index.lock 2>nul

git add frontend\GestorUI\src\hooks\useGestor.ts
git add frontend\GestorUI\src\pages\CareplannerDashboard.tsx
git add frontend\GestorUI\src\pages\CareplannerJourneyDetail.tsx
git add frontend\GestorUI\src\components\TriggerJourneyModal.tsx
git add frontend\GestorUI\src\App.tsx
git add frontend\GestorUI\e2e\careplanner.spec.ts
git add frontend\GestorUI\package.json
git add frontend\GestorUI\package-lock.json
git add docs\demandas\DEM-040_CAREPLANNER_UI\

echo feat(careplanner): DEM-040 CarePlanner UI Completo GestorUI > commit_msg.txt
echo. >> commit_msg.txt
echo - CareplannerDashboard refatorado: lista paginada + filtro status + botao Nova Jornada >> commit_msg.txt
echo - CareplannerJourneyDetail: timeline de eventos, botao encerrar, link video >> commit_msg.txt
echo - TriggerJourneyModal: form validado, toggle video, submit POST /journeys/trigger >> commit_msg.txt
echo - useGestor.ts: 6 novos hooks + 8 interfaces TypeScript >> commit_msg.txt
echo - careplanner.spec.ts: 3 testes Playwright (7 total) >> commit_msg.txt
git commit -F commit_msg.txt && del commit_msg.txt
```

Critério: push aceito; CI verde.

---

## Riscos e Mitigações

| Risco | Probabilidade | Mitigação |
|-------|--------------|-----------|
| `@mantine/modals` não instalado → `modals.openConfirmModal` undefined | Média | Verificar no STEP-004 e instalar se necessário |
| `useQueryClient` não importado em `useGestor.ts` → erro TS | Baixa | Verificar imports antes de salvar |
| `useParams` retorna `undefined` para `:id` em rotas mal configuradas | Baixa | Garantir que a rota do STEP-006 usa exatamente `/careplanner/jornadas/:id` |
| Backend retorna `events` com campo `recorded_at` diferente do esperado | Baixa | Verificar `GET /careplanner/tasks/:id` manualmente no Swagger antes de codificar |
| Playwright falha por ausência de `data-testid` em algum elemento | Baixa | Todos os `data-testid` estão explicitados no spec; conferir antes do STEP-007 |
