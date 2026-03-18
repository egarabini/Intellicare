---
tipo: especificacao-funcional
demanda: DEM-040
titulo: CarePlanner UI Completo — GestorUI
sprint: "4.2"
status: pronto-para-dev
planejador: Claude (PLANEJADOR)
criado: 2026-03-18
depende_de: [DEM-038, DEM-039]
habilita: [DEM-041]
tags: [frontend, careplanner, gestorui, react, mantine, p0]
---

# DEM-040 — CarePlanner UI Completo (GestorUI)

## Objetivo

Transformar a tela `/careplanner` do GestorUI de um dashboard de métricas somente
leitura em um centro de operações completo do CarePlanner. O gestor precisa
conseguir ver todas as jornadas, filtrar por status, abrir o detalhe de uma jornada
(com timeline de eventos), iniciar novas jornadas via modal e encerrar jornadas
ativas — tudo sem sair do GestorUI.

---

## Estado Atual vs. Estado Desejado

| Funcionalidade | Hoje | DEM-040 |
|---------------|------|---------|
| Cards de status com totais | ✅ CareplannerDashboard.tsx | mantido |
| Lista de atividade recente (5 itens, sem filtro) | ✅ parcial | substituído por lista completa paginada |
| Filtro de jornadas por status | ❌ | ✅ Select com todos os status |
| Paginação da lista | ❌ | ✅ botões Anterior/Próxima |
| Clique em jornada → tela de detalhe | ❌ | ✅ `/careplanner/jornadas/:id` |
| Timeline de eventos da jornada | ❌ | ✅ lista de CareEvents ordenada |
| Botão "Nova Jornada" com modal | ❌ | ✅ POST /journeys/trigger |
| Botão "Encerrar Jornada" | ❌ | ✅ POST /tasks/:id/close (status REPLIED/SENT) |
| Link para sessão de vídeo | ❌ | ✅ GET /consultations/video/:id |

---

## Personas e Fluxos

**Persona: Coordenador de Cuidado (role TENANT_GESTOR)**

Fluxo principal:
1. Entra em `/careplanner` → vê cards de status + lista de jornadas
2. Filtra por status "REPLIED" para ver pacientes que já responderam
3. Clica em uma jornada → tela de detalhe com timeline de eventos
4. Vê a resposta do paciente no último evento do tipo INBOUND_RECEIVED
5. Decide encerrar → clica "Encerrar Jornada" → modal de confirmação
6. Jornada muda para CLOSED; Kestra retoma e fecha o ciclo automaticamente

Fluxo secundário:
1. Gestor quer iniciar uma nova jornada manualmente
2. Clica "Nova Jornada" → modal com campos: paciente (patient_ref), tipo (task_type),
   template, telefone, incluir vídeo (toggle)
3. Submete → POST /journeys/trigger → toast de sucesso com execution_id
4. Nova jornada aparece na lista com status CREATED → DISPATCHED em segundos

---

## Critérios de Aceite

1. `/careplanner` exibe lista paginada de jornadas (page_size=10) com filtro de status.
2. Navegação para `/careplanner/jornadas/:correlation_id` funciona ao clicar em qualquer linha.
3. Tela de detalhe exibe: status atual, patient_ref, task_type, data de criação e
   timeline de todos os CareEvents em ordem cronológica.
4. Botão "Encerrar Jornada" aparece somente para jornadas em status SENT ou REPLIED.
   Após confirmação, refaz fetch e exibe status CLOSED.
5. Modal "Nova Jornada" valida campos obrigatórios (patient_ref, task_type) antes de
   submeter. Exibe toast de sucesso com execution_id ou toast de erro em caso de 502.
6. Se a jornada tiver sessão de vídeo (`GET /consultations/video/:id` retorna 200),
   exibir link "Entrar na Videoconsulta" na tela de detalhe.
7. Todos os textos em português brasileiro; datas formatadas com `toLocaleString('pt-BR')`.
8. Loading states em todas as queries; mensagem de erro amigável em caso de falha de rede.
9. 3 testes Playwright cobrindo: (a) lista com filtro, (b) detalhe com eventos,
   (c) trigger modal com submit.
10. Nenhuma regressão nos 4 testes Playwright existentes (`careplanner.spec.ts`).

---

## O que NÃO está incluído

- CRUD de templates de mensagem (próxima iteração)
- Relatório exportável de jornadas (DEM-027 já tem infraestrutura)
- Filtro por patient_ref ou por data
- Visualização de sessões de vídeo em andamento (apenas link externo ao Jitsi)
- Push de notificações em tempo real na lista (SSE já existe no DEM-026/035 — integração futura)

---

## Notas para o Agente Desenvolvedor

- O backend já entrega `GET /careplanner/tasks?status_filter=X&page=N` e
  `GET /careplanner/tasks/{correlation_id}` com `task`, `conversation` e `events`.
- `events` vem ordenado por `recorded_at`; não reordenar no frontend.
- O `correlation_id` no backend é UUID — a URL da rota React usa a string UUID diretamente.
- `POST /journeys/trigger` retorna `{ ok, execution_id, flow_id, status }`. O
  `correlation_id` só existe depois que o Kestra chama `/tasks/open`; não exibir ainda.
- Manter o padrão do projeto: hooks em `useGestor.ts`, chamadas em `api/client.ts`.
- Ícones Tabler já instalados: use `IconTimeline`, `IconPlayerPlay`, `IconX`,
  `IconVideo`, `IconPlus` conforme disponível.
- O `CareplannerDashboard.tsx` existente deve ser refatorado, não substituído: os
  cards de status permanecem no topo, a lista de atividade recente é substituída
  pela lista completa paginada.
