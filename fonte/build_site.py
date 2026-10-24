"""Gera a versão de site (GitHub Pages) do Observatório Eleitoral PE, instalável como app no Windows."""
import json, re, sys, hashlib
from pathlib import Path

ELEI = Path(sys.argv[1]); SITE = Path(sys.argv[2])
tpl = (ELEI / "template.html").read_text(encoding="utf-8")
body = tpl.replace("/*__SEATS__*/", (ELEI / "seats.js").read_text(encoding="utf-8")) \
          .replace("/*__DATA__*/null", (ELEI / "work/dados.json").read_text(encoding="utf-8"))
# separa <title>/<meta>/<link>/<style> do topo (vão para o <head>) do corpo
m = re.match(r"(.*?</style>)(.*)", body, re.S)
head_part, body_part = m.group(1), m.group(2)
head_part = head_part.replace('<meta name="claude:viewport-fit-sides" content="cover">\n', '')
version = hashlib.sha1(body.encode()).hexdigest()[:10]
head = f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="description" content="Desempenho de candidatos, partidos e federações nas eleições de 2022 e 2026 em Pernambuco: deputados, Senado, governo e Presidência, com simulador de cadeiras.">
<meta name="theme-color" content="#0b6e64">
<link rel="manifest" href="manifest.webmanifest">
<link rel="icon" type="image/png" href="favicon.png">
<link rel="apple-touch-icon" href="apple-touch-icon.png">
<meta property="og:title" content="Observatório Eleitoral PE">
<meta property="og:description" content="Resultados de 2022 e 2026 em Pernambuco por candidato, partido, federação e município.">
<meta property="og:image" content="icon-512.png">
<style>
:root {{ color-scheme: light; padding-top: env(safe-area-inset-top, 0px); padding-bottom: env(safe-area-inset-bottom, 0px); }}
body {{ margin: 0; font: 14px system-ui, -apple-system, "Segoe UI", sans-serif; }}
img {{ max-width: 100%; }}
[hidden] {{ display: none !important; }}
</style>
{head_part}
</head>
<body>
"""
tail = f"""
<script>
if ('serviceWorker' in navigator) window.addEventListener('load', () => navigator.serviceWorker.register('sw.js').catch(() => {{}}));
</script>
</body>
</html>
"""
(SITE / "index.html").write_text(head + body_part + tail, encoding="utf-8")
(SITE / "manifest.webmanifest").write_text(json.dumps({
    "name": "Observatório Eleitoral PE", "short_name": "Observatório PE",
    "description": "Resultados eleitorais de 2022 e 2026 em Pernambuco, com simulador de cadeiras.",
    "lang": "pt-BR", "start_url": "./", "scope": "./", "display": "standalone",
    "background_color": "#f4f6f4", "theme_color": "#0b6e64",
    "icons": [{"src": "icon-192.png", "sizes": "192x192", "type": "image/png"},
              {"src": "icon-512.png", "sizes": "512x512", "type": "image/png"},
              {"src": "icon-maskable-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"}],
}, ensure_ascii=False, indent=2), encoding="utf-8")
(SITE / "sw.js").write_text(f"""// Mantém o painel disponível sem internet. Versão {version}: muda a cada publicação, o que renova o cache.
const CACHE = 'observatorio-pe-{version}';
const ARQUIVOS = ['./', 'index.html', 'manifest.webmanifest', 'icon-192.png', 'icon-512.png', 'favicon.png'];
self.addEventListener('install', e => {{ e.waitUntil(caches.open(CACHE).then(c => c.addAll(ARQUIVOS))); self.skipWaiting(); }});
self.addEventListener('activate', e => {{
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim()));
}});
// Página: busca a versão mais nova na rede e usa a guardada quando estiver sem internet.
// Demais arquivos (fontes, ícones): usa o que estiver guardado e atualiza em segundo plano.
self.addEventListener('fetch', e => {{
  const req = e.request; if (req.method !== 'GET') return;
  if (req.mode === 'navigate') {{
    e.respondWith(fetch(req).then(r => {{ const c = r.clone(); caches.open(CACHE).then(x => x.put('index.html', c)); return r; }})
      .catch(() => caches.match('index.html')));
    return;
  }}
  e.respondWith(caches.match(req).then(hit => {{
    const rede = fetch(req).then(r => {{ if (r.ok || r.type === 'opaque') {{ const c = r.clone(); caches.open(CACHE).then(x => x.put(req, c)); }} return r; }}).catch(() => hit);
    return hit || rede;
  }}));
}});
""", encoding="utf-8")
(SITE / ".nojekyll").write_text("")
print("ok", version, (SITE / "index.html").stat().st_size)
