---
tipo: plano-execucao
demanda: DEM-066
titulo: Notificações Push PWA
status: em-execucao
dev: DEV-2
criado: 2026-03-21
---

# DEM-066 — Plano de Execução

## Estimativa

Tempo estimado: ~4h | Complexidade: média-alta

O núcleo crítico é a geração das chaves VAPID e o `push_sender.py` com remoção de 410 automática. O Service Worker é simples mas tem pegadinhas de MIME type e path que precisam de atenção.

---

## Ordem de execução

### Bloco 1 — Infra e Chaves (30min)
1. Gerar chaves VAPID e adicionar ao `.env` local e `.env.example`
2. Adicionar `pywebpush` e `py-vapid` ao `requirements.txt`
3. Criar `migrations/016_push_subscriptions.sql` e aplicar

### Bloco 2 — Backend (1.5h)
4. Criar `modules/notifications/push_sender.py`
   - `send_push()` com retry e remoção 410
5. Atualizar `modules/notifications/routes.py`
   - `GET /vapid-public-key` (sem auth)
   - `POST /subscribe` (upsert por endpoint)
   - `DELETE /unsubscribe`
6. Integrar `push_sender` nos eventos em `services.py`
   - `notify_clinico_replied` → push clínico
   - `notify_task_expired` → push gestor

### Bloco 3 — Testes (45min)
7. Criar `tests/test_push_notifications.py`:
   - `test_subscribe_saves_subscription()`
   - `test_duplicate_subscribe_is_idempotent()`
   - `test_unsubscribe_removes_subscription()`
   - `test_push_sent_on_careplanner_message()` (mock webpush)
   - `test_expired_subscription_auto_removed()` (mock 410)
8. Rodar — garantir 0 regressões

### Bloco 4 — Frontend (1h)
9. Criar `frontend/ClinicoUI/public/sw.js`
10. Criar `frontend/ClinicoUI/public/manifest.json` (ícones placeholder OK)
11. Repetir para `GestorUI`
12. Criar `hooks/usePushNotifications.ts`
13. Integrar toggle no `NotificationBell.tsx`
14. Rebuild ClinicoUI + GestorUI

---

## Gotcha crítico — VAPID keys imutáveis

**Nunca regenerar** as chaves VAPID em staging/produção sem antes executar:
```sql
TRUNCATE push_subscriptions;
```
Subscriptions antigas ficam inválidas silenciosamente — o browser não notifica o usuário, simplesmente para de receber pushes.

---

## Gotcha — SW path e MIME type

O Service Worker deve ser servido com `Content-Type: application/javascript` e deve estar na raiz do scope (`/clinico-ui/sw.js`). Se o Vite processar o arquivo, pode mudar o MIME type. Colocar em `public/` (não em `src/`) garante que será copiado sem processamento.

Verificar no staging:
```bash
curl -I http://localhost:9000/clinico-ui/sw.js
# Esperado: Content-Type: application/javascript
# Esperado: Service-Worker-Allowed: /clinico-ui/
```

---

## Gotcha — iOS 16.4+

No iOS, Push API só funciona se o usuário adicionar o app à tela inicial (modo standalone). O `manifest.json` com `"display": "standalone"` é obrigatório. Sem isso, `PushManager` está `undefined` no Safari iOS.

---

## Entrega

Commit com mensagem:
```
feat(notifications): push PWA — sw.js, VAPID, migration 016, push_sender, NotificationBell toggle
```
Hash → enviar para o ARQUITETO fechar DEM-066.
