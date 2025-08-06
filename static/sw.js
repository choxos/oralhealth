/**
 * Service Worker for OralHealth PWA
 */

const CACHE_NAME = 'oralhealth-v1.0.0';
const STATIC_CACHE = 'oralhealth-static-v1.0.0';
const DYNAMIC_CACHE = 'oralhealth-dynamic-v1.0.0';

// Files to cache immediately
const STATIC_FILES = [
    '/',
    '/static/css/xera-unified-theme.css',
    '/static/css/themes/oralhealth-theme.css',
    '/static/css/dark-theme.css',
    '/static/css/modern-minimal.css',
    '/static/js/modern-minimal.js',
    '/static/js/dark-theme.js',
    '/static/js/pwa.js',
    '/static/js/translation.js',
    '/static/manifest.json',
    '/recommendations/',
    '/guidelines/',
    '/cochrane/',
    '/search/',
    '/offline.html'
];

// Install event - cache static files
self.addEventListener('install', (event) => {
    console.log('Service Worker installing');
    
    event.waitUntil(
        caches.open(STATIC_CACHE)
            .then((cache) => {
                console.log('Caching static files');
                return cache.addAll(STATIC_FILES);
            })
            .then(() => {
                // Skip waiting to activate immediately
                return self.skipWaiting();
            })
            .catch((error) => {
                console.error('Error caching static files:', error);
            })
    );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
    console.log('Service Worker activating');
    
    event.waitUntil(
        caches.keys()
            .then((cacheNames) => {
                return Promise.all(
                    cacheNames.map((cacheName) => {
                        if (cacheName !== STATIC_CACHE && cacheName !== DYNAMIC_CACHE) {
                            console.log('Deleting old cache:', cacheName);
                            return caches.delete(cacheName);
                        }
                    })
                );
            })
            .then(() => {
                // Take control of all clients immediately
                return self.clients.claim();
            })
            .then(() => {
                // Notify clients about update
                return self.clients.matchAll().then((clients) => {
                    clients.forEach((client) => {
                        client.postMessage({
                            type: 'UPDATE_AVAILABLE',
                            message: 'New version available'
                        });
                    });
                });
            })
    );
});

// Fetch event - serve from cache, fallback to network
self.addEventListener('fetch', (event) => {
    // Skip non-GET requests
    if (event.request.method !== 'GET') {
        return;
    }

    // Skip cross-origin requests
    if (!event.request.url.startsWith(self.location.origin)) {
        return;
    }

    event.respondWith(
        caches.match(event.request)
            .then((cachedResponse) => {
                // Return cached version if available
                if (cachedResponse) {
                    return cachedResponse;
                }

                // Clone the request for fetching
                const fetchRequest = event.request.clone();

                return fetch(fetchRequest)
                    .then((response) => {
                        // Check if valid response
                        if (!response || response.status !== 200 || response.type !== 'basic') {
                            return response;
                        }

                        // Clone the response for caching
                        const responseToCache = response.clone();

                        // Cache dynamic content
                        caches.open(DYNAMIC_CACHE)
                            .then((cache) => {
                                // Only cache certain types of requests
                                if (shouldCache(event.request)) {
                                    cache.put(event.request, responseToCache);
                                }
                            });

                        return response;
                    })
                    .catch(() => {
                        // Return offline page for navigation requests
                        if (event.request.mode === 'navigate') {
                            return caches.match('/offline.html');
                        }
                        
                        // Return fallback for other requests
                        return new Response('Offline', {
                            status: 503,
                            statusText: 'Service Unavailable'
                        });
                    });
            })
    );
});

// Helper function to determine if request should be cached
function shouldCache(request) {
    const url = new URL(request.url);
    
    // Cache HTML pages, CSS, JS, images
    return (
        request.destination === 'document' ||
        request.destination === 'style' ||
        request.destination === 'script' ||
        request.destination === 'image' ||
        url.pathname.startsWith('/static/') ||
        url.pathname.startsWith('/recommendations/') ||
        url.pathname.startsWith('/guidelines/') ||
        url.pathname.startsWith('/cochrane/') ||
        url.pathname.startsWith('/search/')
    );
}

// Background sync for offline actions
self.addEventListener('sync', (event) => {
    console.log('Background sync:', event.tag);
    
    if (event.tag === 'sync-search') {
        event.waitUntil(syncSearchData());
    }
});

async function syncSearchData() {
    try {
        // Sync any offline search data when online
        const searchCache = await caches.open('search-cache');
        const requests = await searchCache.keys();
        
        for (const request of requests) {
            try {
                const response = await fetch(request);
                if (response.ok) {
                    await searchCache.put(request, response);
                }
            } catch (error) {
                console.log('Sync failed for:', request.url);
            }
        }
    } catch (error) {
        console.error('Background sync failed:', error);
    }
}

// Push notification handling
self.addEventListener('push', (event) => {
    if (!event.data) return;

    const options = {
        body: event.data.text(),
        icon: '/static/images/icon-192x192.png',
        badge: '/static/images/icon-72x72.png',
        vibrate: [200, 100, 200],
        data: {
            url: '/'
        },
        actions: [
            {
                action: 'view',
                title: 'View',
                icon: '/static/images/view-icon.png'
            },
            {
                action: 'close',
                title: 'Close',
                icon: '/static/images/close-icon.png'
            }
        ]
    };

    event.waitUntil(
        self.registration.showNotification('OralHealth Update', options)
    );
});

// Notification click handling
self.addEventListener('notificationclick', (event) => {
    event.notification.close();

    if (event.action === 'view') {
        event.waitUntil(
            clients.openWindow(event.notification.data.url)
        );
    }
});

// Cache management - clean up old caches periodically
self.addEventListener('message', (event) => {
    if (event.data && event.data.type === 'CLEAN_CACHE') {
        event.waitUntil(cleanOldCaches());
    }
});

async function cleanOldCaches() {
    try {
        const cacheNames = await caches.keys();
        const oldCaches = cacheNames.filter(name => 
            name.startsWith('oralhealth-') && 
            name !== STATIC_CACHE && 
            name !== DYNAMIC_CACHE
        );
        
        await Promise.all(
            oldCaches.map(cacheName => caches.delete(cacheName))
        );
        
        console.log('Cleaned old caches:', oldCaches);
    } catch (error) {
        console.error('Cache cleanup failed:', error);
    }
}