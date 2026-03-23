# DEM-066 — Notificações Push PWA — FINALIZAÇÃO

**Data de entrega:** 2026-03-21
**Dev responsável:** DEV-2
**Commit final:** `98d0310f`
**Sprint:** 2026-04-18

---

## Resumo da entrega

Push nativo PWA implementado de ponta a ponta — clínicos e gestores agora recebem notificações mesmo com o browser fechado. Subscriptions gerenciadas por tenant, com remoção automática de entradas expiradas (410 GONE).

---

## O que foi entregue

| Camada | Arquivo | Descrição |
|--------|---------|-----------|
| DB | `016_push_subscriptions.sql` | Tabela `push_subscriptions` isolada por tenant |
| Backend | `push_sender.py` | `send_push()` via `pywebpush` + remoção automática 410 |
| Backend | `router.py` | Endpoints `subscribe`, `unsubscribe`, `vapid-public-key` |
| Backend | `NotificationService` | Orquestração push integrada aos eventos existentes |
| Frontend | `sw.js` + `manifest.json` | Service Worker + PWA manifest (ClinicoUI + GestorUI) |
| Frontend | `NotificationBell.tsx` | Toggle Mantine UI opt-in/opt-out integrado ao hook |
| Env | `.env.staging` | Chaves VAPID geradas e configuradas |

---

## Comportamento de remoção 410

Quando o serviço de push (FCM/APNS/Mozilla) retorna `410 Gone`, a subscription é removida automaticamente do banco no mesmo request — sem acumular entradas mortas. Isso garante que o banco de `push_subscriptions` reflita sempre o estado real dos dispositivos registrados.

---

## Gotcha de produção — VAPID imutável

As chaves VAPID geradas para staging **não devem ser rotacionadas** sem truncar a tabela `push_subscriptions` primeiro. Subscriptions antigas ficam inválidas silenciosamente — o browser para de receber pushes sem nenhum erro visível.

Se uma rotação de chave for necessária em produção:
```sql
TRUNCATE {tenant_schema}.push_subscriptions;
```
Todos os usuários precisarão re-aceitar a permissão de notificação.

---

## Impacto em DEM-068

DEV-3/4 deve validar no staging:
- `GET /notifications/push/vapid-public-key` → 200 sem auth
- `POST /notifications/push/subscribe` (com JWT válido) → 201
- `GET /clinico-ui/sw.js` → `Content-Type: application/javascript`
- Variáveis `VAPID_PUBLIC_KEY`, `VAPID_PRIVATE_KEY`, `VAPID_SUBJECT` presentes no `.env.staging` ✅ (já providenciadas por DEV-2)

## Próximos passos (fora do escopo desta DEM)

- Push para `PacienteUI` (segunda fase)
- Agrupamento de notificações por tipo/jornada
- Suporte a iOS < 16.4 (não há Web Push API disponível)
