/* FCMO AI shell worker. Freshness and health data are network-only by design. */
const CACHE_NAME = "fcmo-shell-v1";
const SHELL = [
  "./",
  "./index.html",
  "./manifest.webmanifest",
  "./favicon.ico",
  "./favicon.svg",
  "./icons/icon-192.svg",
  "./icons/icon-512.svg"
];
const STATUS_MARKER = "newsroom-status";

self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(CACHE_NAME).then((cache) => cache.addAll(SHELL)));
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) => Promise.all(keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))))
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  const request = event.request;
  const url = new URL(request.url);
  if (request.method !== "GET" || url.origin !== self.location.origin) return;
  // Freshness state is never put in CacheStorage (zero seconds of cache life).
  if (url.pathname.includes(STATUS_MARKER)) {
    event.respondWith(fetch(request, { cache: "no-store" }));
    return;
  }
  if (request.mode === "navigate") {
    event.respondWith(fetch(request).catch(() => caches.match("./index.html")));
    return;
  }
  const staticAsset = /\.(?:css|js|svg|png|jpg|jpeg|webp|ico|woff2?)$/i.test(url.pathname) || url.pathname.endsWith("manifest.webmanifest");
  if (staticAsset) {
    event.respondWith(caches.match(request).then((cached) => cached || fetch(request).then((response) => {
      const copy = response.clone();
      caches.open(CACHE_NAME).then((cache) => cache.put(request, copy));
      return response;
    })));
  }
});
