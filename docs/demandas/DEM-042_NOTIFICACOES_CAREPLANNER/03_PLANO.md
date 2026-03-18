---
tipo: plano-execucao
demanda: DEM-042
titulo: Notificações CarePlanner — integração sino + badge NavLink
status: pendente
dev: CODEX
criado: 2026-03-18
---

# DEM-042 — Plano de Execução

## Estimativa

Tempo estimado: 1–1.5h | Complexidade: baixa

Sem migration. Sem novo endpoint. Sem nova tabela. Todas as mudanças são
cirúrgicas em arquivos existentes — o maior risco é não quebrar a estrutura
do NavLink expansível entregue na DEM-041.

---

## Pré-condição obrigatória

**DEM-041 deve estar commitada** antes de iniciar esta DEM. O NavLink expansível
"CarePlanner" (com sub-itens Dashboard/Templates) é o ponto de integração do
badge — é preciso ler o código exato entregue pelo DEV-1 antes de editar.

---

## STEPs

### STEP-001 — Modificar `integrations.py`

**Status:** pendente

Arquivo: `modules/careplanner/integrations.py`

1. Substituir o corpo de `notify_clinico_replied` pelo código do **Bloco 1**
   de `02_TECNICA.md`.
2. Adicionar `notify_task_expired` logo abaixo (também do **Bloco 1**).

Critério: `python -c "from modules.careplanner.integrations import notify_clinico_replied, notify_task_expired"` sem erros.

---

### STEP-002 — Atualizar `expiry_worker.py`

**Status:** pendente

Arquivo: `modules/careplanner/workers/expiry_worker.py`

1. Importar `notify_task_expired` no topo do arquivo.
2. Após cada transição para `EXPIRED` no loop de varredura, chamar
   `await notify_task_expired(...)` conforme **Bloco 2** de `02_TECNICA.md`.

Critério: worker inicia sem erros (`python -c "from modules.careplanner.workers.expiry_worker import expiry_worker"`).

---

### STEP-003 — Testes Python

**Status:** pendente

Criar `packages/intellicare-core/tests/test_careplanner_phase_g.py` com os
2 testes do **Bloco 6** de `02_TECNICA.md`.

```bash
pytest packages/intellicare-core/tests/test_careplanner_phase_g.py -v
```

Critério: **2 passed**.

---

### STEP-004 — Atualizar `useNotifications.ts`

**Status:** pendente

Arquivo: `frontend/GestorUI/src/hooks/useNotifications.ts`

Adicionar `careplannerUnread` derivado ao retorno do hook conforme **Bloco 3**
de `02_TECNICA.md`.

Critério: `npm run build` sem erros de tipo em `useNotifications.ts`.

---

### STEP-005 — Atualizar `NotificationBell.tsx`

**Status:** pendente

Arquivo: `frontend/GestorUI/src/components/NotificationBell.tsx`

Implementar navegação ao clicar em notificação CarePlanner conforme **Bloco 4**
de `02_TECNICA.md`.

⚠️ Atenção: o cursor do `NotificationItem` muda de condicional para sempre
`pointer` — confirmar que não introduz regressão visual.

Critério: `npm run build` sem erros.

---

### STEP-006 — Atualizar `App.tsx` (badge NavLink)

**Status:** pendente

Arquivo: `frontend/GestorUI/src/App.tsx`

1. **Ler o código exato** do NavLink "CarePlanner" entregue na DEM-041 antes
   de editar — a estrutura de sub-itens deve ser preservada.
2. Adicionar `careplannerUnread` do hook `useNotifications`.
3. Envolver o label do NavLink em `<Group>` com `<Badge>` condicional conforme
   **Bloco 5** de `02_TECNICA.md`.
4. Adicionar `data-testid="careplanner-badge"` no Badge.

Critério: ao abrir o GestorUI no browser, o NavLink "CarePlanner" exibe o
badge vermelho quando há notificações não lidas com `module === "careplanner"`.

---

### STEP-007 — Testes Playwright + Commit

**Status:** pendente

Adicionar 2 testes ao final de `frontend/GestorUI/e2e/careplanner.spec.ts`
conforme **Bloco 7** de `02_TECNICA.md`.

Rodar suite completa:
```bash
npm run test:e2e
```
Critério: **11 passed** (9 DEM-041 + 2 novos).

Commit com os arquivos:
```
modules\careplanner\integrations.py
modules\careplanner\workers\expiry_worker.py
packages\intellicare-core\tests\test_careplanner_phase_g.py
frontend\GestorUI\src\hooks\useNotifications.ts
frontend\GestorUI\src\components\NotificationBell.tsx
frontend\GestorUI\src\App.tsx
frontend\GestorUI\e2e\careplanner.spec.ts
docs\demandas\DEM-042_NOTIFICACOES_CAREPLANNER\
```

Mensagem de commit:
```
feat(careplanner): DEM-042 notificacoes REPLIED/EXPIRED no sino + badge NavLink
```

---

## Riscos e Mitigações

| Risco | Prob. | Mitigação |
|-------|-------|-----------|
| `NotificationService()` instanciado dentro do `try` cria sessão DB desnecessária se Redis falhar | Baixa | O `try/except` externo já é non-fatal; a sessão DB só é aberta no `send()` |
| NavLink DEM-041 usa estrutura customizada que quebra com `<Group>` no label | Média | Ler o arquivo exato antes de editar (STEP-006); adaptar ao padrão entregue |
| `data` da notificação pode ser `null` no frontend (notificações antigas) | Baixa | Usar optional chaining: `n.data?.module === 'careplanner'` |
| `useNotifications` pode não estar disponível no escopo do NavLink do AppShell | Baixa | Hook é chamável em qualquer componente dentro do `BrowserRouter`; confirmar que AppShell está dentro do router |
| Broadcast SSE não persiste no banco para gestores (só clinico_ref persiste) | Aceitável | Decisão de design para V3; gestores veem em tempo real mas recarregar a página limpa o badge deles |
