# Kullanım: python3 kaynak/pwa_yap.py <kök> <başlangıç YYYY-AA-GG> <sürüm no>
# Çıktı (kökte): index.html, manifest.webmanifest, sw.js, simge/*.png
import json, os, subprocess, sys
from PIL import Image, ImageDraw

kok, bas, surum = sys.argv[1], sys.argv[2], sys.argv[3]
os.makedirs(kok + '/simge', exist_ok=True)

ZEMIN, ALTIN = (15, 42, 44), (201, 162, 78)

def simge(boyut, guvenli=1.0):
    k = 4  # pürüzsüz kenar için büyük çiz, sonra küçült
    S = boyut * k
    im = Image.new('RGB', (S, S), ZEMIN)
    d = ImageDraw.Draw(im)
    c, r = S / 2, S * 0.27 * guvenli
    import math
    def kare(aci):
        pts = [(c + r * math.cos(aci + i * math.pi / 2), c + r * math.sin(aci + i * math.pi / 2)) for i in range(4)]
        d.line(pts + [pts[0]], fill=ALTIN, width=int(S * 0.035 * guvenli), joint='curve')
    kare(math.pi / 4); kare(0)
    rr = S * 0.06 * guvenli
    d.ellipse([c - rr, c - rr, c + rr, c + rr], fill=ALTIN)
    return im.resize((boyut, boyut), Image.LANCZOS)

simge(192).save(kok + '/simge/simge-192.png')
simge(512).save(kok + '/simge/simge-512.png')
simge(512, 0.8).save(kok + '/simge/simge-maskeli-512.png')
simge(180).save(kok + '/simge/apple-touch-icon.png')

json.dump({
    "id": "./gunun-ayeti",
    "name": "Günün Ayeti",
    "short_name": "Günün Ayeti",
    "description": "Her gün sıradaki ayetin Elmalılı Hamdi Yazır meali.",
    "lang": "tr",
    "start_url": "./",
    "scope": "./",
    "display": "standalone",
    "background_color": "#0f2a2c",
    "theme_color": "#11706f",
    "icons": [
        {"src": "simge/simge-192.png", "sizes": "192x192", "type": "image/png"},
        {"src": "simge/simge-512.png", "sizes": "512x512", "type": "image/png"},
        {"src": "simge/simge-maskeli-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"}
    ]
}, open(kok + '/manifest.webmanifest', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

open(kok + '/sw.js', 'w', encoding='utf-8').write(f"""// Günün Ayeti — sürüm {surum}. Çevrimiçi: en yeni sürüm; çevrimdışı: kayıtlı kopya.
const AD = 'ga-{surum}';
const DOSYALAR = ['./', 'index.html', 'manifest.webmanifest', 'simge/simge-192.png', 'simge/simge-512.png', 'simge/apple-touch-icon.png'];
self.addEventListener('install', e => {{ e.waitUntil(caches.open(AD).then(c => c.addAll(DOSYALAR))); self.skipWaiting(); }});
self.addEventListener('activate', e => {{ e.waitUntil(caches.keys().then(k => Promise.all(k.filter(x => x !== AD).map(x => caches.delete(x))))); self.clients.claim(); }});
self.addEventListener('fetch', e => {{
  if (e.request.method !== 'GET' || new URL(e.request.url).origin !== location.origin) return;
  e.respondWith(fetch(e.request).then(r => {{ const k = r.clone(); caches.open(AD).then(c => c.put(e.request, k)); return r; }}).catch(() => caches.match(e.request, {{ ignoreSearch: true }})));
}});
""")

gecici = kok + '/_govde.html'
subprocess.run([sys.executable, '-I', kok + '/kaynak/build.py', kok, gecici, bas, '0'], check=True)
govde = open(gecici, encoding='utf-8').read(); os.remove(gecici)
bas_html = """<!doctype html>
<html lang="tr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="theme-color" content="#11706f">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="Günün Ayeti">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<link rel="manifest" href="manifest.webmanifest">
<link rel="icon" href="simge/simge-192.png">
<link rel="apple-touch-icon" href="simge/apple-touch-icon.png">
<style>:root{padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}body{margin:0}[hidden]{display:none!important}</style>
"""
govde = govde.replace('<meta name="claude:viewport-fit-sides" content="cover">\n', '')
i = govde.index('<div class="sayfa">')
html = bas_html + govde[:i] + '</head>\n<body>\n' + govde[i:] + '\n</body>\n</html>\n'
html = html.replace('<title>Günün Ayeti</title>', f'<title>Günün Ayeti</title>\n<!-- sürüm {surum} -->', 1)
open(kok + '/index.html', 'w', encoding='utf-8').write(html)
print('index.html', len(html) // 1024, 'KB, sürüm', surum, 'başlangıç', bas)
