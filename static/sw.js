/**
 * Service Worker para eGarage PWA
 * Gestiona el caché y permite funcionamiento offline
 */

const CACHE_NAME = 'egarage-v1';
const RUNTIME_CACHE = 'egarage-runtime-v1';

// Archivos estáticos críticos para el funcionamiento inicial
const STATIC_CACHE_FILES = [
    '/',
    '/static/css/dashboard.css',
    '/static/css/output.css',
    '/static/js/ios-password-fix.js',
    '/static/images/egarage_logo.png',
    '/static/images/egarage_icon_192x192.png',
    '/static/images/egarage_icon_512x512.png'
];

// Estrategia: Cache First para estáticos, Network First para dinámicos
const CACHE_STRATEGIES = {
    // Archivos estáticos: Cache First
    static: [
        /\/static\//,
        /\.(?:js|css|png|jpg|jpeg|svg|gif|woff|woff2|ttf|eot)$/
    ],
    // API y páginas dinámicas: Network First
    dynamic: [
        /\/api\//,
        /\/accounts\//,
        /\/documentos\//,
        /\/clientes\//,
        /\/vehiculos\//
    ]
};

// Instalación del Service Worker
self.addEventListener('install', (event) => {
    console.log('[Service Worker] Installing...');
    
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => {
                console.log('[Service Worker] Caching static files');
                return cache.addAll(STATIC_CACHE_FILES);
            })
            .then(() => {
                console.log('[Service Worker] Installed successfully');
                return self.skipWaiting(); // Activar inmediatamente
            })
            .catch((error) => {
                console.error('[Service Worker] Installation failed:', error);
            })
    );
});

// Activación del Service Worker
self.addEventListener('activate', (event) => {
    console.log('[Service Worker] Activating...');
    
    event.waitUntil(
        caches.keys()
            .then((cacheNames) => {
                return Promise.all(
                    cacheNames.map((cacheName) => {
                        // Eliminar caches antiguos
                        if (cacheName !== CACHE_NAME && cacheName !== RUNTIME_CACHE) {
                            console.log('[Service Worker] Deleting old cache:', cacheName);
                            return caches.delete(cacheName);
                        }
                    })
                );
            })
            .then(() => {
                console.log('[Service Worker] Activated');
                return self.clients.claim(); // Tomar control de todas las páginas
            })
    );
});

// Interceptar peticiones
self.addEventListener('fetch', (event) => {
    const { request } = event;
    const url = new URL(request.url);

    // Ignorar peticiones que no son GET
    if (request.method !== 'GET') {
        return;
    }

    // Ignorar peticiones a otros dominios (CORS)
    if (url.origin !== location.origin) {
        return;
    }

    // Determinar estrategia según el tipo de recurso
    const isStatic = CACHE_STRATEGIES.static.some(pattern => pattern.test(url.pathname));
    const isDynamic = CACHE_STRATEGIES.dynamic.some(pattern => pattern.test(url.pathname));

    if (isStatic) {
        // Estrategia: Cache First para archivos estáticos
        event.respondWith(cacheFirst(request));
    } else if (isDynamic) {
        // Estrategia: Network First para contenido dinámico
        event.respondWith(networkFirst(request));
    } else {
        // Estrategia por defecto: Network First
        event.respondWith(networkFirst(request));
    }
});

// Estrategia Cache First: Buscar en caché primero, luego red
async function cacheFirst(request) {
    try {
        const cachedResponse = await caches.match(request);
        if (cachedResponse) {
            return cachedResponse;
        }

        const networkResponse = await fetch(request);
        
        // Guardar en caché para próximas veces
        if (networkResponse.ok) {
            const cache = await caches.open(CACHE_NAME);
            cache.put(request, networkResponse.clone());
        }

        return networkResponse;
    } catch (error) {
        console.error('[Service Worker] Cache First error:', error);
        
        // Si falla, intentar devolver una respuesta del caché aunque sea antigua
        const cachedResponse = await caches.match(request);
        if (cachedResponse) {
            return cachedResponse;
        }

        // Si no hay caché, devolver error
        return new Response('Offline', {
            status: 503,
            statusText: 'Service Unavailable',
            headers: new Headers({
                'Content-Type': 'text/plain'
            })
        });
    }
}

// Estrategia Network First: Intentar red primero, luego caché
async function networkFirst(request) {
    try {
        const networkResponse = await fetch(request);
        
        // Si la respuesta es exitosa, actualizar caché
        if (networkResponse.ok) {
            const cache = await caches.open(RUNTIME_CACHE);
            cache.put(request, networkResponse.clone());
        }

        return networkResponse;
    } catch (error) {
        console.log('[Service Worker] Network failed, trying cache:', error);
        
        // Si falla la red, buscar en caché
        const cachedResponse = await caches.match(request);
        if (cachedResponse) {
            return cachedResponse;
        }

        // Si no hay caché, devolver página offline genérica
        return new Response('Offline', {
            status: 503,
            statusText: 'Service Unavailable',
            headers: new Headers({
                'Content-Type': 'text/plain'
            })
        });
    }
}

// Manejar mensajes del cliente (para actualizar caché manualmente)
self.addEventListener('message', (event) => {
    if (event.data && event.data.type === 'SKIP_WAITING') {
        self.skipWaiting();
    }
    
    if (event.data && event.data.type === 'CLEAR_CACHE') {
        caches.delete(CACHE_NAME);
        caches.delete(RUNTIME_CACHE);
    }
});

// Sincronización en segundo plano (para cuando vuelva la conexión)
self.addEventListener('sync', (event) => {
    if (event.tag === 'background-sync') {
        event.waitUntil(doBackgroundSync());
    }
});

async function doBackgroundSync() {
    // Aquí puedes implementar lógica de sincronización
    // Por ejemplo, sincronizar datos pendientes
    console.log('[Service Worker] Background sync triggered');
}



