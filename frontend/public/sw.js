const CACHE_NAME = "agribharat-v1";

const ASSETS_TO_CACHE = [
  "/",
  "/manifest.json",
  "/icons/icon-192x192.png",
  "/icons/icon-512x512.png"
];

// Install Event: Cache critical assets
self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      console.log("Opened cache");
      return cache.addAll(ASSETS_TO_CACHE);
    })
  );
});

// Fetch Event: Stratagies
self.addEventListener("fetch", (event) => {
  const url = new URL(event.request.url);

  // 1. API Calls (Network First, then Cache) - Critical for Prices/Forecasts
  if (url.pathname.startsWith("/api/v1/")) {
    event.respondWith(
      fetch(event.request)
        .then((response) => {
          // Clone and cache the valid response
          if (response.status === 200) {
            const responseClone = response.clone();
            caches.open(CACHE_NAME).then((cache) => {
                // Store only GET requests
                if(event.request.method === 'GET'){
                    cache.put(event.request, responseClone);
                }
            });
          }
          return response;
        })
        .catch(() => {
          // Fallback to cache if network fails
          return caches.match(event.request);
        })
    );
    return;
  }

  // 2. Static Assets (Cache First) - Images, JS, CSS
  if (
    url.pathname.startsWith("/_next/") || 
    url.pathname.startsWith("/static/") ||
    url.pathname.match(/\.(png|jpg|jpeg|svg|ico)$/)
  ) {
    event.respondWith(
      caches.match(event.request).then((response) => {
        return response || fetch(event.request);
      })
    );
    return;
  }

  // 3. Default (Stale While Revalidate for HTML pages)
  event.respondWith(
    caches.match(event.request).then((cachedResponse) => {
      const fetchPromise = fetch(event.request).then((networkResponse) => {
        caches.open(CACHE_NAME).then((cache) => {
          cache.put(event.request, networkResponse.clone());
        });
        return networkResponse;
      });
      return cachedResponse || fetchPromise;
    })
  );
});

// Activate Event: Cleanup old caches
self.addEventListener("activate", (event) => {
  const cacheWhitelist = [CACHE_NAME];
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheWhitelist.indexOf(cacheName) === -1) {
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
});
