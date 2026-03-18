---
tipo: especificacao-funcional
demanda: DEM-045
titulo: CarePlanner no ClinicoUI — lista de jornadas + detalhe read-only
sprint: "4.4"
status: pronto-para-dev
planejador: Claude (PLANEJADOR)
criado: 2026-03-18
depende_de: [DEM-040, DEM-042]
habilita: [DEM-048]
tags: [careplanner, clinico, clinicoul, frontend, p1]
---

# DEM-045 — CarePlanner no ClinicoUI

## Objetivo

O médico recebe notificações de REPLIED pelo sino (DEM-042) mas ao clicar vai
para o GestorUI — módulo que ele não acessa. Esta DEM adiciona uma página
"Jornadas" ao ClinicoUI onde o médico visualiza as care tasks do tenant,
filtra pelas suas próprias (`clinico_ref = user_id`) e lê a timeline de eventos.
É acesso read-only: criar e encerrar jornadas permanecem exclusivos do GESTOR.

---

## Estado Atual vs. Estado Desejado

| Item | Hoje | DEM-045 |
|------|------|---------|
| ClinicoUI tem página CarePlanner | ❌ | ✅ `/careplanner` |
| NavLink "Jornadas" no menu | ❌ | ✅ com badge de REPLIED pendentes |
| Lista de jornadas do tenant | ❌ | ✅ com filtro "Minhas Jornadas" |
| Detalhe de jornada com timeline | ❌ | ✅ read-only (sem botões criar/encerrar) |
| Clique na notificação leva ao ClinicoUI | ❌ (leva ao GestorUI) | ✅ `/careplanner/{id}` no ClinicoUI |
| Hook de dados CarePlanner no ClinicoUI | ❌ | ✅ `useCareplanner.ts` |

---

## Critérios de Aceite

1. NavLink "Jornadas" no `ClinicoShell` (`AppShell.tsx`) com ícone `IconHeartbeat`
   e badge vermelho mostrando contagem de jornadas com status `REPLIED`.

2. Página `/careplanner` lista todas as care tasks do tenant com:
   - Colunas: Paciente, Tipo, Status (badge colorido), Atualizado em
   - Filtro toggle "Minhas Jornadas" — quando ativo, exibe apenas tarefas
     onde `clinico_ref` corresponde ao `user_id` do clínico logado
   - Paginação (10 por página)
   - Click na linha navega para `/careplanner/:id`

3. Página `/careplanner/:id` exibe:
   - Card com dados da tarefa (paciente, tipo, status, datas)
   - Timeline de eventos idêntica à do GestorUI
   - Botão "Entrar na Videoconsulta" se sessão ativa existir (`clinico_url`)
   - **Sem** botões "Encerrar" ou "Nova Jornada" (read-only para CLINICO)

4. A notificação de CarePlanner no `NotificationBell` do ClinicoUI já navega
   para `/careplanner/{correlation_id}` via `data.correlation_id` (DEM-042).
   Confirmar que o path `/careplanner/{id}` da rota corresponde ao que o
   NotificationBell envia.

5. `npm run build` sem erros no ClinicoUI.

6. 2 testes Playwright no ClinicoUI cobrindo: acesso à lista de jornadas e
   navegação para detalhe.

---

## O que NÃO está incluído

- Criar jornadas pelo ClinicoUI (exclusivo do GestorUI)
- Encerrar jornadas pelo ClinicoUI
- Triggers de workflow Kestra pelo ClinicoUI
- Templates de mensagem pelo ClinicoUI

---

## Notas para o Agente Desenvolvedor

- Criar `frontend/ClinicoUI/src/hooks/useCareplanner.ts` — **não reutilizar**
  `useGestor.ts` do GestorUI (projetos separados, buildados separadamente).
  As interfaces `CareTask`, `CareTaskDetail`, `CareEvent` podem ser copiadas
  e adaptadas.

- A URL base da API é a mesma (`/api/v1/careplanner/tasks`). O token JWT do
  clínico tem role `CLINICO` — verificar se os endpoints existentes permitem
  CLINICO. Se não, adicionar `"CLINICO"` ao `require_role` nos endpoints
  de leitura (`GET /tasks`, `GET /tasks/{id}`).

- O filtro "Minhas Jornadas" é **frontend-only** por enquanto: filtrar o array
  local por `task.clinico_ref === auth.user?.profile?.sub`. Não requer endpoint
  novo no backend.

- `ClinicoShell` (`frontend/ClinicoUI/src/components/AppShell.tsx`) usa array
  `NAV_ITEMS` — adicionar `{ path: '/careplanner', icon: IconHeartbeat, label: 'Jornadas' }`.
  `IconHeartbeat` de `@tabler/icons-react`.

- Playwright config do ClinicoUI: verificar se existe `e2e/` neste frontend;
  se não existir, criar `playwright.config.ts` similar ao do GestorUI.

- O badge de REPLIED: usar `useCareplannerTasks` com `statusFilter='REPLIED'`
  e exibir `data?.total` no badge.
