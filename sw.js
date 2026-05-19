// Service Worker for Vault PWA
// The scope is set by the location of this file, which is at the root.

const CACHE_NAME = 'vault-cache-v1';

// We don't necessarily need to cache everything right away for a basic installable PWA,
// but providing a fetch listener is required by some browsers to show the install prompt.
self.addEventListener('install', (event) => {
    self.skipWaiting();
});

self.addEventListener('activate', (event) => {
    event.waitUntil(self.clients.claim());
});

self.addEventListener('fetch', (event) => {
    // Only use cache fallback for GET requests; other methods should go directly to the network.
    if (event.request.method !== 'GET') {
        event.respondWith(fetch(event.request));
        return;
    }

    // Basic network-first strategy with an explicit offline fallback response.
    event.respondWith(
        fetch(event.request).catch(() => {
            return caches.match(event.request).then((cachedResponse) => {
                if (cachedResponse) {
                    return cachedResponse;
                }

                return new Response('Offline and no cached version is available.', {
                    status: 503,
                    statusText: 'Service Unavailable',
                    headers: {
                        'Content-Type': 'text/plain'
                    }
                });
            });
        })
    );
});
