---
tipo: plano-execucao
demanda: DEM-041
titulo: Templates CarePlanner — CRUD + integração TriggerModal
status: pendente
dev: CODEX
criado: 2026-03-18
---

# DEM-041 — Plano de Execução

## Estimativa

Tempo estimado: 1.5–2h | Complexidade: baixa-média

Backend é incremental (nenhuma migration, apenas 2 métodos novos no repo + 4
endpoints). Frontend segue o padrão já estabelecido pelas DEMs anteriores.
O risco maior é o `IntegrityError` do SQLAlchemy no `create_template` — precisa
ser capturado corretamente.

---

## STEPs

### STEP-001 — Atualizar `repository.py`

**Status:** pendente

Ações (Bloco 1 de `02_TECNICA.md`):
1. Adicionar `get_template(ctx, template_id)` após `list_templates`
2. Adicionar `update_template(ctx, template_id, content, variables, active)` após `get_template`
3. Alterar assinatura de `list_templates` adicionando parâmetro `active_only: bool = False`
   com cláusula `WHERE active = TRUE` condicional

Critério: `pytest test_careplanner_phase_a.py` ainda passa (não-regressão mínima).

---

### STEP-002 — Atualizar `services.py`

**Status:** pendente

Ações (Bloco 2 de `02_TECNICA.md`):
1. Adicionar `list_templates(ctx, active_only)` — wrap do repo
2. Adicionar `create_template_record(ctx, payload)` — captura `IntegrityError` → 409
3. Adicionar `update_template_record(ctx, id, content, variables, active)`
4. Adicionar `toggle_template(ctx, id)`
5. Adicionar `seed_default_templates(ctx)` com os 4 templates padrão

Atenção: `from sqlalchemy.exc import IntegrityError` deve ser importado dentro
do método (evitar import global que pode mascarar outros erros).

Critério: `from modules.careplanner.services import CareplannerService` sem erros.

---

### STEP-003 — Atualizar `main.py` (seed no startup)

**Status:** pendente

Adicionar chamada ao `seed_default_templates` no método `startup()` de `Module`,
**após** as migrações e **antes** de iniciar os workers (Bloco 4 de `02_TECNICA.md`).

Critério: reiniciar o container localmente e verificar em `psql` que a tabela
`care_templates` do schema `tenant_alfa` contém os 4 templates default.

```bash
docker exec -it intellicare_postgres psql -U postgres -c \
  "SELECT template_code, active FROM tenant_alfa.care_templates;"
```

---

### STEP-004 — Adicionar endpoints em `routes.py`

**Status:** pendente

Ações (Bloco 3 de `02_TECNICA.md`):
1. Adicionar `TemplateCreateRequest` e `TemplateUpdateRequest` com os modelos Pydantic
2. Adicionar as 4 rotas: `GET /templates`, `POST /templates`,
   `PUT /templates/{id}`, `PATCH /templates/{id}/toggle`

Atenção: `require_role("GESTOR")` — verificar se aceita a string `"GESTOR"` ou
precisa de `"TENANT_GESTOR"`. Conferir o padrão dos outros endpoints no arquivo.

Critério: `GET /careplanner/templates` retorna 200 (mesmo que lista vazia).

---

### STEP-005 — Testes Python (`test_careplanner_phase_f.py`)

**Status:** pendente

Criar `packages/intellicare-core/tests/test_careplanner_phase_f.py` com
5 testes (Bloco 9 de `02_TECNICA.md`):

```
test_list_templates_vazio
test_create_template_sucesso
test_create_template_duplicate_409
test_update_template
test_toggle_template
```

Executar:
```bash
pytest packages/intellicare-core/tests/test_careplanner_phase_f.py -v
```

Critério: 5 passed.

---

### STEP-006 — Hooks TypeScript (`useGestor.ts`)

**Status:** pendente

Adicionar ao final de `frontend/GestorUI/src/hooks/useGestor.ts`:
- Interfaces: `CareTemplate`, `TemplateCreatePayload`, `TemplateUpdatePayload`
- Hooks: `useCareplannerTemplates`, `useCreateTemplate`, `useUpdateTemplate`,
  `useToggleTemplate`

(Bloco 5 de `02_TECNICA.md`)

Critério: `npm run build` sem erros em `useGestor.ts`.

---

### STEP-007 — Criar `CareplannerTemplates.tsx`

**Status:** pendente

Criar `frontend/GestorUI/src/pages/CareplannerTemplates.tsx` conforme Bloco 6
de `02_TECNICA.md`.

Atenção: `IconToggleLeft` e `IconToggleRight` de `@tabler/icons-react` — verificar
se existem na versão instalada. Se não existirem, substituir por `IconCheck` e
`IconBan` respectivamente.

Critério: `npm run build` sem erros; página renderiza no browser em
`http://localhost:5173/careplanner/templates`.

---

### STEP-008 — Atualizar `TriggerJourneyModal.tsx`

**Status:** pendente

Substituir o campo `template_code` de `TextInput` para `Select` dinâmico
(Bloco 7 de `02_TECNICA.md`).

Critério: ao abrir o modal "Nova Jornada" com templates cadastrados, o Select
exibe as opções; sem templates, exibe placeholder e permite deixar vazio.

---

### STEP-009 — Rota e navegação (`App.tsx`)

**Status:** pendente

Ações (Bloco 8 de `02_TECNICA.md`):
1. Importar `CareplannerTemplates`
2. Adicionar `<Route path="/careplanner/templates" .../>`
3. Transformar o NavLink "CarePlanner" em item expansível com sub-itens
   "Dashboard" e "Templates"

Critério: clicar em "Templates" no menu navega para `/careplanner/templates`
sem erro 404 ou recarregamento de página.

---

### STEP-010 — Testes Playwright e commit

**Status:** pendente

Adicionar 2 testes ao final de `e2e/careplanner.spec.ts` (Bloco 10 de `02_TECNICA.md`).

Executar suite completa:
```bash
npm run test:e2e
```

Critério: 9 passed (7 anteriores + 2 novos).

Commit:
```bash
cd C:\Users\egara\INTELLICARE
del .git\index.lock 2>nul

git add modules\careplanner\repository.py modules\careplanner\services.py ^
        modules\careplanner\api\routes.py modules\careplanner\main.py ^
        packages\intellicare-core\tests\test_careplanner_phase_f.py ^
        frontend\GestorUI\src\hooks\useGestor.ts ^
        frontend\GestorUI\src\pages\CareplannerTemplates.tsx ^
        frontend\GestorUI\src\components\TriggerJourneyModal.tsx ^
        frontend\GestorUI\src\App.tsx ^
        frontend\GestorUI\e2e\careplanner.spec.ts ^
        docs\demandas\DEM-041_TEMPLATES_CAREPLANNER\

echo feat(careplanner): DEM-041 Templates CRUD + integracao TriggerModal > commit_msg.txt
echo. >> commit_msg.txt
echo - repository: get_template, update_template, list_templates active_only >> commit_msg.txt
echo - services: CRUD completo + seed_default_templates (4 templates) >> commit_msg.txt
echo - routes: GET/POST /templates, PUT/PATCH /templates/:id/toggle >> commit_msg.txt
echo - CareplannerTemplates.tsx: tabela com editar e toggle ativo >> commit_msg.txt
echo - TriggerJourneyModal: template_code TextInput substituido por Select >> commit_msg.txt
echo - test_careplanner_phase_f.py: 5 testes Python >> commit_msg.txt
echo - careplanner.spec.ts: 2 testes Playwright (9 total) >> commit_msg.txt
git commit -F commit_msg.txt && del commit_msg.txt
```

---

## Riscos e Mitigações

| Risco | Prob. | Mitigação |
|-------|-------|-----------|
| `IntegrityError` não capturado lança 500 | Média | Capturar explicitamente `from sqlalchemy.exc import IntegrityError` dentro do método, não no topo do arquivo |
| `require_role("GESTOR")` vs `"TENANT_GESTOR"` | Média | Verificar padrão dos endpoints existentes (`/tasks/close`, etc.) antes de escrever os novos |
| `IconToggleLeft/Right` inexistente na versão instalada do Tabler | Baixa | Substituir por `IconPlayerPlay` / `IconPlayerPause` se necessário |
| Seed no `startup` aumenta tempo de boot | Baixa | `ON CONFLICT DO NOTHING` equivalente (try/except) — impacto < 50ms para 4 templates |
| `active_only` no `list_templates` quebra dispatcher que usa `get_template_by_code` | Nenhuma | `get_template_by_code` é método separado, não afetado |
