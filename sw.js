// Günün Ayeti — sürüm 9. Çevrimiçi: en yeni sürüm; çevrimdışı: kayıtlı kopya.
const AD = 'ga-9';
const DOSYALAR = ['./', 'index.html', 'manifest.webmanifest', 'simge/simge-192.png', 'simge/simge-512.png', 'simge/apple-touch-icon.png'];
self.addEventListener('install', e => { e.waitUntil(caches.open(AD).then(c => c.addAll(DOSYALAR))); self.skipWaiting(); });
self.addEventListener('activate', e => { e.waitUntil(caches.keys().then(k => Promise.all(k.filter(x => x !== AD).map(x => caches.delete(x))))); self.clients.claim(); });
self.addEventListener('fetch', e => {
  if (e.request.method !== 'GET' || new URL(e.request.url).origin !== location.origin) return;
  e.respondWith(fetch(e.request).then(r => { const k = r.clone(); caches.open(AD).then(c => c.put(e.request, k)); return r; }).catch(() => caches.match(e.request, { ignoreSearch: true })));
});
