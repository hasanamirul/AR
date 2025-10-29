self.addEventListener("install", e => {
  e.waitUntil(
    caches.open("env-monitor").then(cache => {
      return cache.addAll(["./", "./index.html", "./css/style.css", "./js/main.js", "./js/api.js"]);
    })
  );
});

self.addEventListener("fetch", e => {
  e.respondWith(caches.match(e.request).then(res => res || fetch(e.request)));
});
