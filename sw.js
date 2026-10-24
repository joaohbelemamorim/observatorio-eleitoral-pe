// Mantém o painel disponível sem internet. Versão 0617f1ac40: muda a cada publicação, o que renova o cache.
const CACHE = 'observatorio-pe-0617f1ac40';
const ARQUIVOS = ['./', 'index.html', 'manifest.webmanifest', 'icon-192.png', 'icon-512.png', 'favicon.png'];
self.addEventListener('install', e => { e.waitUntil(caches.open(CACHE).then(c => c.addAll(ARQUIVOS))); self.skipWaiting(); });
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});
// Página: busca a versão mais nova na rede e usa a guardada quando estiver sem internet.
// Demais arquivos (fontes, ícones): usa o que estiver guardado e atualiza em segundo plano.
self.addEventListener('fetch', e => {
  const req = e.request; if (req.method !== 'GET') return;
  if (req.mode === 'navigate') {
    e.respondWith(fetch(req).then(r => { const c = r.clone(); caches.open(CACHE).then(x => x.put('index.html', c)); return r; })
      .catch(() => caches.match('index.html')));
    return;
  }
  e.respondWith(caches.match(req).then(hit => {
    const rede = fetch(req).then(r => { if (r.ok || r.type === 'opaque') { const c = r.clone(); caches.open(CACHE).then(x => x.put(req, c)); } return r; }).catch(() => hit);
    return hit || rede;
  }));
});
