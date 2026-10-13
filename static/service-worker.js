/* Prixio Service Worker — cache offline + PWA */

const VERSION = 'prixio-v1.0.0';
const STATIC_CACHE = `${VERSION}-static`;
const RUNTIME_CACHE = `${VERSION}-runtime`;

// Ressources précachées à l'installation
const PRECACHE_URLS = [
  '/',
  '/manifest.webmanifest',
  '/static/favicons/icon-192.png',
  '/static/favicons/icon-512.png',
  '/static/logo.png',
];

// ---------- INSTALL ----------
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(STATIC_CACHE)
      .then((cache) => cache.addAll(PRECACHE_URLS).catch(() => null))
      .then(() => self.skipWaiting())
  );
});

// ---------- ACTIVATE ----------
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys
          .filter((k) => k.startsWith('prixio-') && !k.startsWith(VERSION))
          .map((k) => caches.delete(k))
      )
    ).then(() => self.clients.claim())
  );
});

// ---------- FETCH ----------
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Ignore non-GET et cross-origin (API, CDN…)
  if (request.method !== 'GET') return;
  if (url.origin !== self.location.origin) return;

  // Endpoints API et admin : network-only
  if (url.pathname.startsWith('/api/') ||
      url.pathname.startsWith('/admin/') ||
      url.pathname.startsWith('/accounts/') ||
      url.pathname.startsWith('/i18n/') ||
      url.pathname.startsWith('/rosetta/') ||
      url.pathname.startsWith('/service-worker.js') ||
      url.pathname.startsWith('/manifest.webmanifest')) {
    return; // laisse passer sans cache
  }

  // Assets statiques : cache-first
  if (url.pathname.startsWith('/static/')) {
    event.respondWith(
      caches.match(request).then((cached) => {
        if (cached) return cached;
        return fetch(request).then((response) => {
          if (response.ok) {
            const clone = response.clone();
            caches.open(STATIC_CACHE).then((cache) => cache.put(request, clone));
          }
          return response;
        }).catch(() => cached);
      })
    );
    return;
  }

  // HTML : network-first + fallback offline
  if (request.headers.get('accept')?.includes('text/html')) {
    event.respondWith(
      fetch(request)
        .then((response) => {
          const clone = response.clone();
          caches.open(RUNTIME_CACHE).then((cache) => cache.put(request, clone));
          return response;
        })
        .catch(() => caches.match(request).then((c) => c || caches.match('/')))
    );
    return;
  }

  // Autres : stale-while-revalidate
  event.respondWith(
    caches.match(request).then((cached) => {
      const network = fetch(request).then((response) => {
        if (response.ok) {
          caches.open(RUNTIME_CACHE).then((cache) => cache.put(request, response.clone()));
        }
        return response;
      }).catch(() => cached);
      return cached || network;
    })
  );
});

// ---------- MESSAGE (pour forcer la mise à jour) ----------
self.addEventListener('message', (event) => {
  if (event.data?.type === 'SKIP_WAITING') self.skipWaiting();
});