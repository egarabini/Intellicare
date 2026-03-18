---
tipo: especificacao-funcional
demanda: DEM-042
titulo: Notificações CarePlanner — integração sino + badge NavLink
sprint: "4.3"
status: pronto-para-dev
planejador: Claude (PLANEJADOR)
criado: 2026-03-18
depende_de: [DEM-026, DEM-035, DEM-040, DEM-041]
habilita: [DEM-043]
tags: [careplanner, notifications, frontend, gestorui, realtime, p1]
---

# DEM-042 — Notificações CarePlanner (integração sino + badge NavLink)

## Objetivo

Quando um paciente responde via Rocket.Chat a jornada CarePlanner transita para
`REPLIED` — mas hoje o gestor só descobre se entrar manualmente no dashboard e
varrer a lista. Esta DEM fecha esse gap: a resposta do paciente persiste no banco
de notificações, aparece no sino (NotificationBell) já existente, e o NavLink
"CarePlanner" exibe um badge com a contagem de respostas pendentes. Clicar na
notificação navega diretamente para a jornada.

Nenhuma nova tabela, nenhuma nova infra. Reaproveitamento 100% de DEM-026 e
DEM-035.

---

## Estado Atual vs. Estado Desejado

| Item | Hoje | DEM-042 |
|------|------|---------|
| `notify_clinico_replied` persiste no banco | ❌ usa `publish_notification` direto | ✅ usa `NotificationService.send()` |
| Gestores recebem notificação quando paciente responde | ❌ só vai para `clinico_ref` ou broadcast raw | ✅ persiste para `clinico_ref` + broadcast para todo o tenant |
| Sino (NotificationBell) exibe respostas de pacientes | ❌ não aparece | ✅ aparece com título "Paciente respondeu" |
| Clicar na notificação de CarePlanner navega para a jornada | ❌ sem ação | ✅ navega para `/careplanner/{correlation_id}` |
| Badge no NavLink "CarePlanner" | ❌ texto estático | ✅ badge com contagem de `REPLIED` não lidas |
| Expiração de jornada notifica gestor | ❌ silenciosa | ✅ notificação persistida tipo "alert" quando tarefa expira |

---

## Critérios de Aceite

1. Quando `care_task` transita para `REPLIED` (via webhook RC), uma notificação
   é persistida no banco para `clinico_ref` (se existir) **e** um broadcast é
   publicado para todo o tenant — ambos aparecem no sino do GestorUI em até 2s.

2. O campo `data` da notificação contém:
   ```json
   {
     "module": "careplanner",
     "event": "REPLIED",
     "correlation_id": "<uuid>",
     "task_type": "<string>",
     "patient_ref": "<string>"
   }
   ```

3. Ao clicar em uma notificação CarePlanner no popover do sino, o frontend
   navega para `/careplanner/<correlation_id>`.

4. O NavLink "CarePlanner" no AppShell do GestorUI exibe um `Badge` com a
   contagem de notificações não lidas cujo `data.module === "careplanner"`.
   O badge desaparece quando a contagem chega a zero.

5. Quando `care_task` expira (EXPIRED via `expiry_worker`), uma notificação
   tipo `"alert"` com priority `"normal"` é persistida e aparece no sino.

6. 2 testes Python e 2 testes Playwright passando sem regressão.

---

## O que NÃO está incluído

- Notificações push (browser push API / PWA)
- Email ou SMS quando gestor não está online
- Notificação de transição para outros estados além de `REPLIED` e `EXPIRED`
- Preferências de notificação específicas por tipo CarePlanner
- Filtro "apenas CarePlanner" no popover do sino

---

## Notas para o Agente Desenvolvedor

- **Não alterar `NotificationType` em `schemas.py`** — usar `"message"` para
  `REPLIED` e `"alert"` para `EXPIRED`. O campo `data.module = "careplanner"`
  é o discriminador no frontend.

- **`notify_clinico_replied` em `integrations.py`** precisa importar e instanciar
  `NotificationService` internamente (lazy import para evitar circular). O padrão
  já existe no arquivo — seguir o mesmo `try/except` não-fatal.

- **Para notificar gestores sem `user_id` individual**: usar `publish_broadcast`
  já existente para SSE em tempo real. A persistência individual no banco só é
  feita para `clinico_ref` (quando presente). Gestores recebem via broadcast
  SSE (sem persistência por usuário, apenas o clinico_ref tem registro no banco).
  Isso é aceitável para V3 — evita query de todos os user_ids de GESTOR.

- **`useNotifications`** em `hooks/useNotifications.ts` já retorna todas as
  notificações. Adicionar `careplannerUnread` como propriedade derivada:
  `notifications.filter(n => !n.is_read && n.data?.module === 'careplanner').length`.

- **Badge no NavLink**: usar `<Badge size="xs" color="red" circle>` do Mantine 7
  com `{careplannerUnread}` ao lado do label "CarePlanner". Ocultar quando zero.
  Verificar como o NavLink expansível de DEM-041 foi implementado para não quebrar
  a estrutura.

- **Navegação ao clicar**: o `NotificationItem` em `NotificationBell.tsx` recebe
  `onRead` — adicionar `onNavigate?: (path: string) => void` opcional. Quando
  `data.module === "careplanner"` e `data.correlation_id` existir, chamar
  `navigate('/careplanner/' + data.correlation_id)` após marcar como lida.

- **Notificação de expiração**: adicionar `notify_task_expired` em
  `integrations.py`, chamada no `expiry_worker.py` após cada transição para
  `EXPIRED`. Usar `publish_broadcast` (sem persistência por usuário individual).
