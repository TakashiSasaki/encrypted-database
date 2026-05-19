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
    // Basic network-first strategy or fallback
    event.respondWith(
        fetch(event.request).catch(() => {
            return caches.match(event.request);
        })
    );
});
