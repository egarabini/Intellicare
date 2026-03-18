---
tipo: plano-execucao
demanda: DEM-045
titulo: CarePlanner no ClinicoUI — lista de jornadas + detalhe read-only
status: pendente
dev: DEV-2
criado: 2026-03-18
---

# DEM-045 — Plano de Execução

## Estimativa

Tempo estimado: 2–2.5h | Complexidade: média

O maior cuidado é não misturar o código do GestorUI com o ClinicoUI
(projetos separados, buildados separadamente). Todos os hooks e componentes
devem ser criados do zero no ClinicoUI.

---

## STEPs

### STEP-001 — Verificar roles nos endpoints GET do CarePlanner

```bash
grep -n "require_role\|has_role\|GESTOR\|CLINICO" modules/careplanner/api/routes.py | head -30
```

Se os GETs exigem apenas GESTOR, alterar para aceitar também CLINICO
conforme **Bloco 1** de `02_TECNICA.md`.

Critério: `pytest packages/intellicare-core/tests/test_careplanner_phase_a.py -v`
ainda passa (não-regressão).

---

### STEP-002 — Criar `useCareplanner.ts`

Criar `frontend/ClinicoUI/src/hooks/useCareplanner.ts` conforme **Bloco 2**.

Verificar o caminho correto do `api` (axios instance) no ClinicoUI —
provavelmente em `src/auth/api.ts` ou `src/utils/api.ts`. Ajustar o import.

Critério: `cd frontend/ClinicoUI && npm run build` sem erros de tipo.

---

### STEP-003 — Criar `CareplannerPage.tsx`

Criar `frontend/ClinicoUI/src/pages/CareplannerPage.tsx` conforme **Bloco 3**.

Critério: `npm run build` sem erros; página renderiza em `/clinico-ui/careplanner`.

---

### STEP-004 — Criar `CareplannerDetail.tsx`

Criar `frontend/ClinicoUI/src/pages/CareplannerDetail.tsx` conforme **Bloco 4**.
Basear na `CareplannerJourneyDetail.tsx` do GestorUI mas remover todas as
mutações (useCloseTask, useCreateVideoSession) e botões de ação.
Manter apenas: card de dados, timeline de eventos, botão "Entrar na Videoconsulta".

Critério: `npm run build` sem erros.

---

### STEP-005 — Atualizar `AppShell.tsx`

Adicionar NavLink "Jornadas" com badge de REPLIED conforme **Bloco 5**.

⚠️ `IconHeartbeat` — verificar se existe na versão Tabler instalada no ClinicoUI.
Se não, usar `IconActivity` ou `IconPulse`.

Critério: NavLink "Jornadas" aparece no menu lateral.

---

### STEP-006 — Atualizar `App.tsx`

Adicionar rotas `/careplanner` e `/careplanner/:id` conforme **Bloco 6**.

Critério: navegar para `/clinico-ui/careplanner` sem 404.

---

### STEP-007 — Build final + Commit

```bash
cd frontend/ClinicoUI && npm run build
```

Critério: build OK sem erros.

Commit:
```
feat(clinico): DEM-045 CarePlanner view — lista jornadas + detalhe read-only
```

Arquivos:
```
modules\careplanner\api\routes.py
frontend\ClinicoUI\src\hooks\useCareplanner.ts
frontend\ClinicoUI\src\pages\CareplannerPage.tsx
frontend\ClinicoUI\src\pages\CareplannerDetail.tsx
frontend\ClinicoUI\src\components\AppShell.tsx
frontend\ClinicoUI\src\App.tsx
docs\demandas\DEM-045_CAREPLANNER_CLINICO\
```

---

## Riscos

| Risco | Mitigação |
|-------|-----------|
| `api` axios instance tem caminho diferente | Verificar em STEP-002 antes de criar hook |
| `IconHeartbeat` não existe no Tabler da versão instalada | Usar `IconActivity` |
| CLINICO não tem permissão nos endpoints GET | STEP-001 corrige antes de prosseguir |
| ClinicoUI não tem diretório `e2e/` | Criar `playwright.config.ts` mínimo se quiser Playwright; ou omitir testes E2E desta DEM |
