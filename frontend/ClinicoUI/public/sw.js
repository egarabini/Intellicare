// sw.js - Service Worker for Push Notifications
self.addEventListener('push', function(event) {
  if (event.data) {
    const data = event.data.json();
    const title = data.title || 'Nova Notificação';
    const options = {
      body: data.body || '',
      icon: '/pulse.svg', // Assumindo que o ícone do sistema esteja disponível
      data: data.data || {}
    };
    event.waitUntil(self.registration.showNotification(title, options));
  }
});

self.addEventListener('notificationclick', function(event) {
  event.notification.close();
  // Foca ou abre a janela da aplicação, extraindo url se houver
  const url = event.notification.data.url || '/';
  
  event.waitUntil(
    clients.matchAll({ type: 'window' }).then(windowClients => {
      for (let client of windowClients) {
        if (client.url === url && 'focus' in client) {
          return client.focus();
        }
      }
      if (clients.openWindow) {
        return clients.openWindow(url);
      }
    })
  );
});
