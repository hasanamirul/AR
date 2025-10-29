self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open("smart-env-v2").then((cache) => {
      return cache.addAll([
        "index.html",
        "style.css",
        "manifest.json",
        "js/api.js",
        "js/ai-insight.js",
        "js/chart.js",
        "js/camera.js",
        "js/script.js",
        "assets/icon-192.png",
        "assets/icon-512.png",
        "assets/beep.mp3"
      ]);
    })
  );
});

self.addEventListener("fetch", (event) => {
  event.respondWith(
    caches.match(event.request).then((response) => response || fetch(event.request))
  );
});
