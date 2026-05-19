// Service Worker for Vault PWA
// The scope is set by the location of this file, which is at the root.

// We don't pre-cache assets yet, but this fetch listener provides an
// offline fallback from any previously cached GET requests.
self.addEventListener('install', (event) => {
    self.skipWaiting();
});

self.addEventListener('activate', (event) => {
    event.waitUntil(self.clients.claim());
});

self.addEventListener('fetch', (event) => {
    if (event.request.method !== 'GET') {
        return;
    }

    event.respondWith((async () => {
        try {
            return await fetch(event.request);
        } catch (error) {
            const cachedResponse = await caches.match(event.request);
            return cachedResponse || new Response('Offline', {
                status: 503,
                statusText: 'Service Unavailable'
            });
        }
    })());
});
