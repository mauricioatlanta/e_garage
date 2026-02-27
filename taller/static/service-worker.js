// Service Worker para eGarage PWA
// Versión: 2.1.5 - Invalidar caché para jQuery/Select2/documentos (fix 403 y tax)
const CACHE_NAME = 'egarage-v2.1.5';
const RUNTIME_CACHE = 'egarage-runtime-v2.1.5';

// Archivos estáticos críticos para cachear
const STATIC_CACHE_URLS = [
  '/',
  '/static/css/dashboard.css',
  '/static/css/output.css',
  '/static/css/starfield.css',
  '/static/css/pwa-install-prompt.css',
  '/static/js/starfield.js',
  '/static/js/pwa-install-prompt.js',
  '/static/js/ios-password-fix.js',
  '/static/images/egarage_default_logo.png',
  '/static/images/egarage_default_logo.svg',
  '/static/images/egarage_icon_192x192.png',
  '/static/images/egarage_icon_512x512.png',
  '/static/manifest.json',
  'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.2/css/all.min.css',
  'https://code.jquery.com/jquery-3.6.4.min.js'
];

// Estrategia de caché: Cache First para estáticos, Network First para dinámicos
const CACHE_FIRST_PATTERNS = [
  /\/static\//,
  /\.(?:png|jpg|jpeg|svg|gif|webp|ico)$/,
  /\.(?:css|js|woff|woff2|ttf|eot)$/,
  /cdnjs\.cloudflare\.com/,
  /code\.jquery\.com/
];

// Instalación del Service Worker
self.addEventListener('install', (event) => {
  console.log('[Service Worker] Instalando...');
  
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('[Service Worker] Cacheando archivos estáticos');
        // Cachear archivos críticos, pero no fallar si algunos no están disponibles
        return cache.addAll(STATIC_CACHE_URLS).catch((error) => {
          console.warn('[Service Worker] Algunos archivos no se pudieron cachear:', error);
          // Continuar aunque algunos archivos fallen
          return Promise.resolve();
        });
      })
      .then(() => {
        // Forzar activación inmediata del nuevo service worker
        return self.skipWaiting();
      })
  );
});

// Activación del Service Worker
self.addEventListener('activate', (event) => {
  console.log('[Service Worker] Activando...');
  
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          // Eliminar caches antiguos
          if (cacheName !== CACHE_NAME && cacheName !== RUNTIME_CACHE) {
            console.log('[Service Worker] Eliminando cache antiguo:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    })
    .then(() => {
      // Tomar control de todas las páginas inmediatamente
      return self.clients.claim();
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

  // Ignorar peticiones a APIs que requieren autenticación en tiempo real
  if (url.pathname.includes('/api/') && 
      (url.pathname.includes('/auth/') || url.pathname.includes('/ajax/'))) {
    // Para APIs dinámicas, usar solo network
    event.respondWith(fetch(request));
    return;
  }

  // Determinar estrategia de caché
  const useCacheFirst = CACHE_FIRST_PATTERNS.some(pattern => pattern.test(url.href));

  if (useCacheFirst) {
    // Cache First: Buscar en caché primero, luego en red
    event.respondWith(
      caches.match(request)
        .then((cachedResponse) => {
          if (cachedResponse) {
            return cachedResponse;
          }
          
          return fetch(request).then((response) => {
            // Solo cachear respuestas exitosas
            if (response.status === 200) {
              const responseToCache = response.clone();
              caches.open(CACHE_NAME).then((cache) => {
                cache.put(request, responseToCache);
              });
            }
            return response;
          }).catch(() => {
            // Si falla la red y no hay caché, devolver una respuesta offline básica
            if (request.destination === 'document') {
              return caches.match('/');
            }
            // Fallbacks específicos para recursos no-documento
            if (request.destination === 'image') {
              // Intenta devolver un logo por defecto cacheado
              return caches.match('/static/images/egarage_default_logo.png');
            }
            if (request.destination === 'script' || request.destination === 'style') {
              // Para scripts/estilos críticos, intentar devolver una versión cacheada genérica
              return caches.match('/static/js/pwa-install-prompt.js')
                .then(resp => resp || caches.match('/static/css/output.css'));
            }
          });
        })
    );
  } else {
    // Network First: Intentar red primero, luego caché
    event.respondWith(
      fetch(request)
        .then((response) => {
          // Si la respuesta es exitosa, cachearla
          if (response.status === 200) {
            const responseToCache = response.clone();
            caches.open(RUNTIME_CACHE).then((cache) => {
              cache.put(request, responseToCache);
            });
          }
          return response;
        })
        .catch(() => {
          // Si falla la red, buscar en caché
          return caches.match(request).then((cachedResponse) => {
            if (cachedResponse) {
              return cachedResponse;
            }
            // Si es una página HTML y no hay caché, devolver la página principal
            if (request.destination === 'document') {
              return caches.match('/');
            }
          });
        })
    );
  }
});

// Manejar mensajes del cliente (para actualizaciones, etc.)
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
  
  if (event.data && event.data.type === 'CLEAR_CACHE') {
    event.waitUntil(
      caches.keys().then((cacheNames) => {
        return Promise.all(
          cacheNames.map((cacheName) => caches.delete(cacheName))
        );
      })
    );
  }
});













