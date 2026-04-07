/* Guide Bookshop — POS Service Worker
   Scope: / (set via Service-Worker-Allowed header)
   Strategy:
     - CDN assets  → cache-first (stale-while-revalidate)
     - POS page    → network-first, cache fallback
     - Everything else → network only (pass-through)
*/

const CACHE = 'gb-pos-v1';

const CDN_HOSTS = [
  'cdn.tailwindcss.com',
  'cdnjs.cloudflare.com',
  'fonts.googleapis.com',
  'fonts.gstatic.com',
  'cdn.jsdelivr.net',
  'ka-f.fontawesome.com',
];

// ── Install: claim immediately, pre-cache POS page ────────────────────────
self.addEventListener('install', e => {
  self.skipWaiting();
  e.waitUntil(
    caches.open(CACHE).then(c =>
      c.add('/sales/pos/').catch(() => { /* ignore if user not logged in yet */ })
    )
  );
});

// ── Activate: delete old caches, take control right away ─────────────────
self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

// ── Fetch ────────────────────────────────────────────────────────────────
self.addEventListener('fetch', e => {
  const req  = e.request;
  const url  = new URL(req.url);

  // Never intercept POST / non-GET (sales API calls handled by page JS)
  if (req.method !== 'GET') return;

  // CDN assets — cache-first, background refresh
  if (CDN_HOSTS.some(h => url.hostname.includes(h))) {
    e.respondWith(
      caches.open(CACHE).then(async cache => {
        const cached = await cache.match(req);
        const fresh  = fetch(req).then(res => {
          if (res.ok) cache.put(req, res.clone());
          return res;
        }).catch(() => null);
        return cached || fresh;
      })
    );
    return;
  }

  // POS page — network-first, serve cached shell when offline
  if (url.pathname === '/sales/pos/') {
    e.respondWith(
      fetch(req)
        .then(res => {
          if (res.ok) caches.open(CACHE).then(c => c.put(req, res.clone()));
          return res;
        })
        .catch(() => caches.match(req))
    );
    return;
  }

  // Everything else — network only (don't cache admin pages / API)
});
