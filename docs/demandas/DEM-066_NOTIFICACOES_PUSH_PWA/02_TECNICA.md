---
tipo: especificacao-tecnica
demanda: DEM-066
titulo: Notificações Push PWA
---

# DEM-066 — Especificação Técnica

## Mapa de mudanças

| Arquivo | Tipo | O que muda |
|---------|------|-----------|
| `frontend/ClinicoUI/public/sw.js` | **Novo** | Service Worker — eventos `push` e `notificationclick` |
| `frontend/ClinicoUI/public/manifest.json` | **Novo** | PWA manifest com ícones 192/512 |
| `frontend/GestorUI/public/sw.js` | **Novo** | Idem para GestorUI |
| `frontend/GestorUI/public/manifest.json` | **Novo** | Idem para GestorUI |
| `frontend/ClinicoUI/src/hooks/usePushNotifications.ts` | **Novo** | Hook subscribe/unsubscribe/isSupported |
| `frontend/ClinicoUI/src/components/NotificationBell.tsx` | Modificar | Toggle opt-in integrado ao hook |
| `migrations/016_push_subscriptions.sql` | **Novo** | Tabela `push_subscriptions` por tenant |
| `modules/notifications/push_sender.py` | **Novo** | `send_push()` + remoção 410 automática |
| `modules/notifications/routes.py` | Modificar | 3 novos endpoints push |
| `modules/notifications/services.py` | Modificar | Integrar `push_sender` nos eventos existentes |
| `requirements.txt` | Modificar | `pywebpush>=2.0.0`, `py-vapid>=1.9.0` |
| `tests/test_push_notifications.py` | **Novo** | 5 testes |

---

## Migration 016 — `push_subscriptions`

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

---

## Endpoints novos

| Método | Path | Auth | Descrição |
|--------|------|------|-----------|
| `GET` | `/notifications/push/vapid-public-key` | Nenhuma | Retorna VAPID_PUBLIC_KEY pública |
| `POST` | `/notifications/push/subscribe` | JWT | Salva/atualiza subscription (upsert por endpoint) |
| `DELETE` | `/notifications/push/unsubscribe` | JWT | Remove subscription do banco |

**Body do subscribe:**
```json
{
  "endpoint": "https://fcm.googleapis.com/...",
  "keys": { "p256dh": "...", "auth": "..." },
  "user_agent": "Mozilla/5.0..."
}
```

---

## Variáveis de ambiente

```
VAPID_PUBLIC_KEY=<base64url>
VAPID_PRIVATE_KEY=<base64url>
VAPID_SUBJECT=mailto:admin@intellicare.ia.br
```

**Geração one-time (nunca rotacionar sem invalidar banco):**
```bash
python -c "
from py_vapid import Vapid
v = Vapid()
v.generate_keys()
print('PUBLIC:', v.public_key)
print('PRIVATE:', v.private_key)
"
```

---

## `push_sender.py` — contrato

```python
async def send_push(
    subscription_info: dict,   # {endpoint, keys: {p256dh, auth}}
    title: str,
    body: str,
    action_url: str,
    tag: str = "intellicare-notif"
) -> bool:
    """
    Retorna True se enviado, False se subscription expirada (410).
    Em caso de 410, remove subscription do banco automaticamente.
    """
```

**Gatilhos de integração (em `services.py`):**
- `notify_clinico_replied` → push para clínico responsável pela jornada
- `notify_task_expired` → push para gestor
- Nova nota Florence criada → push para clínico (fase futura: paciente)

---

## `sw.js` — contrato mínimo

```javascript
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

---

## Compatibilidade

| Browser | Suporte |
|---------|---------|
| Chrome / Edge (desktop + Android) | ✅ completo |
| Firefox (desktop) | ✅ completo |
| Safari macOS 16+ | ✅ (APNS via Web Push) |
| iOS Safari 16.4+ | ✅ (requer manifest + standalone) |
| iOS Safari < 16.4 | ❌ não suportado — SW registra mas push não chega |
