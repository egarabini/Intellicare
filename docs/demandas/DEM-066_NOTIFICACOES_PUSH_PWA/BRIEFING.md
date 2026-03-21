# DEM-066 — Notificações Push PWA

**Sprint:** 2026-04-18
**Dev:** DEV-2
**Estimativa:** ~4h
**Prioridade:** Alta — notificações SSE/banco já existem (DEM-026/035); esta DEM adiciona push nativo mesmo com app fechado

---

## Objetivo

O IntelliCare já possui notificações em tempo real via SSE + Redis Pub/Sub (DEM-026) e o sino `NotificationBell` nos 4 módulos (DEM-035). O problema: **essas notificações só funcionam com o app aberto**. Push PWA entrega notificações mesmo com o browser fechado ou app em background — crítico para clínicos que precisam ser alertados de mensagens urgentes de pacientes ou jornadas CarePlanner.

---

## Escopo

### 1. Service Worker (`sw.js`)

Criar service worker em cada frontend que precise de push:

```javascript
// frontend/ClinicoUI/public/sw.js  (e GestorUI/public/sw.js)

self.addEventListener('push', (event) => {
  const data = event.data?.json() ?? {};
  event.waitUntil(
    self.registration.showNotification(data.title ?? 'IntelliCare', {
      body: data.body,
      icon: '/clinico-ui/icon-192.png',
      badge: '/clinico-ui/badge-72.png',
      data: { url: data.action_url },
      tag: data.tag ?? 'intellicare-notif',
      renotify: true,
    })
  );
});

self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  event.waitUntil(clients.openWindow(event.notification.data?.url ?? '/'));
});
```

### 2. Migration 016 — tabela `push_subscriptions`

```sql
-- No schema de cada tenant (via Alembic)
CREATE TABLE IF NOT EXISTS {schema}.push_subscriptions (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id      UUID NOT NULL REFERENCES {schema}.users(id) ON DELETE CASCADE,
    endpoint     TEXT NOT NULL,
    p256dh       TEXT NOT NULL,
    auth         TEXT NOT NULL,
    user_agent   VARCHAR(255),
    created_at   TIMESTAMPTZ DEFAULT now(),
    last_used_at TIMESTAMPTZ,
    UNIQUE(user_id, endpoint)
);
```

### 3. Backend — endpoints de subscription

```
POST /notifications/push/subscribe
     Body: { endpoint, keys: { p256dh, auth }, user_agent? }
     → Salva PushSubscription no banco para o usuário autenticado

DELETE /notifications/push/unsubscribe
     Body: { endpoint }
     → Remove subscription

GET /notifications/push/vapid-public-key
     → Retorna VAPID_PUBLIC_KEY (sem autenticação, necessário para o SW)
```

**Geração das chaves VAPID:**
```bash
# Uma vez, no setup do ambiente:
python -c "from py_vapid import Vapid; v = Vapid(); v.generate_keys(); print(v.public_key, v.private_key)"
```

**Variáveis de ambiente:**
```
VAPID_PUBLIC_KEY=<chave-publica-base64>
VAPID_PRIVATE_KEY=<chave-privada-base64>
VAPID_SUBJECT=mailto:admin@intellicare.ia.br
```

### 4. Push sender — integração com notificações existentes

Estender `modules/notifications/services.py` para, ao persistir uma notificação, também disparar push para as subscriptions ativas do usuário:

```python
# modules/notifications/push_sender.py (novo)

from pywebpush import webpush, WebPushException

async def send_push(subscription_info: dict, title: str, body: str, action_url: str):
    try:
        webpush(
            subscription_info=subscription_info,
            data=json.dumps({"title": title, "body": body, "action_url": action_url}),
            vapid_private_key=settings.VAPID_PRIVATE_KEY,
            vapid_claims={"sub": settings.VAPID_SUBJECT}
        )
    except WebPushException as ex:
        if ex.response and ex.response.status_code == 410:
            # Subscription expirada — remover do banco
            await remove_expired_subscription(subscription_info["endpoint"])
```

**Gatilhos de push (integrar nos eventos existentes):**
- Nova mensagem CarePlanner recebida → push para clínico responsável
- Jornada expirada → push para gestor
- Nova nota Florence criada → push para paciente (PacienteUI)

### 5. Frontend — hook `usePushNotifications`

```typescript
// frontend/ClinicoUI/src/hooks/usePushNotifications.ts

export function usePushNotifications() {
  const subscribe = async () => {
    const reg = await navigator.serviceWorker.ready;
    const vapidKey = await fetchVapidPublicKey();
    const sub = await reg.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: urlBase64ToUint8Array(vapidKey),
    });
    await api.post('/notifications/push/subscribe', sub.toJSON());
  };

  const unsubscribe = async () => { /* ... */ };

  return { subscribe, unsubscribe, isSupported: 'PushManager' in window };
}
```

**Integração no `NotificationBell`:** adicionar botão toggle "Ativar notificações" que chama `subscribe()` se `isSupported`.

### 6. Manifests PWA

Verificar/criar `manifest.json` em ClinicoUI e GestorUI com `"display": "standalone"` e ícones 192x192 e 512x512. Sem isso o browser não registra service worker em produção.

---

## Dependências Python

```
pywebpush>=2.0.0
py-vapid>=1.9.0
```

Adicionar ao `requirements.txt`.

---

## Testes esperados (mínimo 4)

```python
# tests/test_push_notifications.py

test_subscribe_saves_subscription()          # POST /notifications/push/subscribe → 201
test_duplicate_subscribe_is_idempotent()     # segunda subscrição mesmo endpoint → upsert, não erro
test_unsubscribe_removes_subscription()      # DELETE → subscription removida
test_push_sent_on_careplanner_message()      # mock webpush, verifica chamada ao receber mensagem RC
test_expired_subscription_auto_removed()     # 410 da webpush API → subscription deletada do banco
```

---

## Arquivos a criar/modificar

```
frontend/ClinicoUI/public/
├── sw.js                              (novo)
└── manifest.json                      (novo ou atualizar)
frontend/GestorUI/public/
├── sw.js                              (novo)
└── manifest.json                      (novo ou atualizar)
frontend/ClinicoUI/src/hooks/
└── usePushNotifications.ts            (novo)
modules/notifications/
├── push_sender.py                     (novo)
├── routes.py                          (adicionar /push/subscribe, /push/unsubscribe, /push/vapid-public-key)
└── services.py                        (integrar push_sender nos eventos existentes)
migrations/
└── 016_push_subscriptions.sql         (novo)
```

---

## Critério de aceite

1. ClinicoUI registra service worker sem erros no Console
2. `POST /notifications/push/subscribe` salva subscription no banco
3. Com browser fechado, ao receber mensagem RC no CarePlanner, push chega no dispositivo
4. Subscription expirada (410) é removida automaticamente do banco
5. 4/5 testes passando (push real pode ser mockado em CI)
