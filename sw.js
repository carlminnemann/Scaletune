/* ScaleTune service worker.

   Caches the whole app, piano samples included, so that once it has been
   opened it runs with no network at all — which is the point for a practice
   tool used in rehearsal rooms and backstage.

   Note: browsers only register a service worker on a secure origin (HTTPS, or
   localhost). Served over plain http:// on a LAN address it will not install,
   and the app still works — just without the offline cache. */

const CACHE = 'scaletune-v113';
const ASSETS = [
  './',
  './index.html',
  './manifest.webmanifest',
  './vendor/soundfont-player.min.js',
  './vendor/acoustic_grand_piano-mp3.js',
  './vendor/cello-mp3.js',
  './vendor/oboe-mp3.js',
  './vendor/drums/kick.wav',
  './vendor/drums/snare.wav',
  './vendor/drums/ride.wav',
  './vendor/drums/hhc.wav',
  './vendor/drums/hho.wav',
  './icons/apple-touch-icon.png',
  './icons/icon-192.png',
  './icons/icon-512.png',
  './icons/icon-maskable-512.png',
];

self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(CACHE)
      /* addAll is all-or-nothing; cache what we can so one bad entry cannot
         leave the app with no cache at all. Each request bypasses the browser's
         own HTTP cache: the host sends max-age=600, so a new cache version
         installed just after a deploy could otherwise be filled with the files
         it was meant to replace. */
      .then(c => Promise.allSettled(
        ASSETS.map(a => c.add(new Request(a, {cache: 'reload'})))))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

/* Two strategies, deliberately:

   - The page itself goes to the network first, falling back to the cache when
     offline. Cache-first on the HTML means a new version of the app is never
     seen until the cache is manually cleared — which is exactly the trap that
     had an old build running during testing.
   - Everything else (the 2.5 MB of piano samples, the icons) is cache-first:
     it is large, it never changes without the cache version changing, and it
     is what makes the app work with no network.                              */

const isDocument = req =>
  req.mode === 'navigate' ||
  (req.headers.get('accept') || '').includes('text/html');

self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET') return;

  if (isDocument(req)) {
    // 'reload' bypasses the browser's own HTTP cache for this one request. The
    // host serves the page with max-age=600, so without this a device could be
    // handed a ten-minute-old build even though the worker asked the network —
    // which reads exactly like the app not having been updated.
    e.respondWith(
      fetch(req, { cache: 'reload' })
        .then(res => {
          const copy = res.clone();
          caches.open(CACHE).then(c => c.put('./index.html', copy)).catch(() => {});
          return res;
        })
        .catch(() => caches.match('./index.html', { ignoreSearch: true }))
    );
    return;
  }

  e.respondWith(
    caches.match(req, { ignoreSearch: true }).then(hit => {
      if (hit) return hit;
      return fetch(req).then(res => {
        if (res && res.ok && new URL(req.url).origin === self.location.origin) {
          const copy = res.clone();
          caches.open(CACHE).then(c => c.put(req, copy)).catch(() => {});
        }
        return res;
      }).catch(() => hit);
    })
  );
});
