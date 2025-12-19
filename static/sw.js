const CACHE_NAME = "nova-v1";
const STATIC_ASSETS = [
  "/",
  "/static/app.js",
  "/static/index.html",
  "/static/manifest.json",
  "/static/sw.js",
];

// Install: cache static assets
self.addEventListener("install", (e) => {
  e.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      cache.addAll(STATIC_ASSETS).catch(() => {});
      self.skipWaiting();
    })
  );
});

// Activate: clean up old caches
self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches.keys().then((names) => {
      return Promise.all(
        names.map((name) => {
          if (name !== CACHE_NAME) return caches.delete(name);
        })
      );
    })
  );
  self.clients.claim();
});

// Fetch: network-first with cache fallback
self.addEventListener("fetch", (e) => {
  // API calls: network with cache fallback
  if (e.request.url.includes("/api/")) {
    e.respondWith(
      fetch(e.request)
        .then((res) => {
          // Cache successful responses
          if (res.status === 200) {
            const clone = res.clone();
            caches.open(CACHE_NAME).then((cache) => {
              cache.put(e.request, clone);
            });
          }
          return res;
        })
        .catch(() => {
          // Offline: return cached response if available
          return caches.match(e.request).then((cached) => {
            if (cached) return cached;
            // Fallback for offline API
            if (e.request.url.includes("/api/history")) {
              return new Response(
                JSON.stringify({ history: JSON.parse(localStorage.getItem("nova_history") || "[]") }),
                { headers: { "Content-Type": "application/json" } }
              );
            }
            return new Response(
              JSON.stringify({ error: "offline" }),
              { status: 503, headers: { "Content-Type": "application/json" } }
            );
          });
        })
    );
    return;
  }

  // Static assets: cache-first
  e.respondWith(
    caches
      .match(e.request)
      .then((cached) => cached || fetch(e.request))
      .catch(() => {
        // Return offline page if available
        return caches.match("/");
      })
  );
});
