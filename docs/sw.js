const CACHE_NAME = 'ihh-rapor-v1';
const urlsToCache = ['/', '/index.html', '/manifest.json'];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(urlsToCache))
  );
});

self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request).then(response => response || fetch(event.request))
  );
});

// Push notification handler
self.addEventListener('push', event => {
  const data = event.data ? event.data.json() : {};
  const options = {
    body: data.body || 'Haftalık raporunuzu kontrol edin.',
    icon: '/icon-192.png',
    badge: '/icon-192.png',
    vibrate: [200, 100, 200],
    data: { url: data.url || '/' },
    actions: [
      { action: 'open', title: '📋 Önizle & Gönder' },
      { action: 'close', title: 'Kapat' }
    ]
  };
  event.waitUntil(
    self.registration.showNotification(data.title || 'İHH ATOM Rapor', options)
  );
});

self.addEventListener('notificationclick', event => {
  event.notification.close();
  if (event.action === 'open' || !event.action) {
    event.waitUntil(clients.openWindow(event.notification.data.url || '/'));
  }
});

// Schedule Sunday 20:45 reminder check
self.addEventListener('periodicsync', event => {
  if (event.tag === 'weekly-report-reminder') {
    event.waitUntil(checkAndNotify());
  }
});

async function checkAndNotify() {
  const now = new Date();
  if (now.getDay() === 0) { // Sunday
    self.registration.showNotification('📋 İHH ATOM Haftalık Rapor', {
      body: 'Pazar 21:00\'a 15 dakika kaldı! Raporunuzu gözden geçirin.',
      icon: '/icon-192.png',
      vibrate: [300, 100, 300, 100, 300],
      actions: [{ action: 'open', title: '📋 Raporu Aç' }]
    });
  }
}
