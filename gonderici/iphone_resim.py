# iPhone kestirmesi için: bugünün ayetini şeffaf zeminli resme yazar (kullanıcının fotoğrafının üstüne bindirilir).
# Çıktı (<çıktı>/iphone/): bugun-orta.png, bugun-alt[-b1..b4].png, bugun.txt, boyutlar.txt/json, vakit/<ilçeID>-<ek>.png (6 vakit, şeffaf, tam ekran)
# Kullanım: python3 iphone_resim.py <font.ttf> [çıktı klasörü]
import json, os, re, sys
from datetime import datetime, timedelta, timezone
from PIL import Image, ImageDraw, ImageFilter, ImageFont

kok = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
font = sys.argv[1]
cikti = sys.argv[2] if len(sys.argv) > 2 else kok
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kilit_veri import gun_verisi, bugun as _bugun
bugun = _bugun()
a = gun_verisi(bugun)  # meal, ref, esma, ust, ramazan
ref = a['ref']
W, H = 1290, 2796

def sar(d, metin, f, gen):
    out, s = [], ''
    for k in metin.split():
        t = (s + ' ' + k).strip()
        if d.textlength(t, font=f) > gen and s: out.append(s); s = k
        else: s = t
    return out + ([s] if s else [])

# Yazı büyüklükleri (Android ve sitedekiyle aynı): ad, çarpan, dosya eki. Normal'in dosya adları eskisiyle aynı kalır.
BOYUTLAR = [('Normal', 1.0, 'alt'), ('Büyük', 1.25, 'alt-b1'), ('Çok büyük', 1.5, 'alt-b2'), ('En büyük', 1.75, 'alt-b3'), ('Dev', 2.0, 'alt-b4')]
ORNEK_VAKIT = '  ·  '.join(['00:00'] * 6)

def yazi_tipi(boy, agirlik):
    f = ImageFont.truetype(font, max(8, int(boy)))
    try: f.set_variation_by_name(agirlik)
    except Exception: pass
    return f

def ciz(yer, k=1.0):
    """Ayet bloğunu şeffaf zemine çizer. k: yazı büyüklüğü çarpanı (sadece yazılar ve bant büyür)."""
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    gen, fs = W * 0.8, int(W * 0.044 * k)
    taban, sinir = W * 0.044 * k * (0.75 if k > 1 else 0.636), H * min(0.5, 0.22 * k)
    while True:   # uzun ayette küçül ama seçilen boyutun çok altına inme; gerekirse blok daha çok yer kaplasın
        f = yazi_tipi(fs, 'SemiBold')
        sat = sar(d, a['meal'], f, gen); yuk = len(sat) * fs * 1.45
        if yuk < sinir or (fs <= taban and yuk + fs * 4 < H * 0.66) or fs < W * 0.02: break
        fs = int(fs * 0.94)
    # Küçük satırlar (sure, esma, vakit) uzun ayette bile seçilen boyutta kalsın
    lh, rfs = fs * 1.45, int(fs * 0.72 if k <= 1 else max(fs * 0.72, W * 0.044 * k * 0.72 * 0.9))
    vfs = int(rfs * 0.92)
    # Esma sığmıyorsa iki satır (ad / anlam); vakit satırı sığmıyorsa iki satır (3 + 3)
    es_sat = [a['esma']]
    if d.textlength(a['esma'], font=yazi_tipi(vfs, 'Regular')) > W * 0.9 / 0.85 and ' · ' in a['esma']: es_sat = a['esma'].split(' · ')
    v_sat = 1 if d.textlength(ORNEK_VAKIT, font=yazi_tipi(vfs, 'SemiBold')) <= W * 0.92 else 2
    blok = len(sat) * lh + rfs * 2.2 + len(es_sat) * vfs * 1.5 + v_sat * vfs * 1.5
    merkez = H * (0.78 if yer == 'alt' else 0.52)
    ust, pay = merkez - blok / 2, fs * 2.2
    if ust + blok > H * 0.86: ust = H * 0.86 - blok
    if ust < H * 0.2: ust = H * 0.2   # saatin olduğu üst bölgeye çıkmasın
    bant = Image.new('L', (1, 256))
    for y in range(256):
        t = y / 255
        bant.putpixel((0, y), int(174 * (t / .22 if t < .22 else (1 - t) / .22 if t > .78 else 1)))
    bant = bant.resize((W, int(blok + 2 * pay)))
    golge = Image.new('RGBA', bant.size, (0, 0, 0, 0)); golge.putalpha(bant)
    im.alpha_composite(golge, (0, int(ust - pay)))
    yazi = Image.new('RGBA', (W, H), (0, 0, 0, 0)); yd = ImageDraw.Draw(yazi)
    rf = ImageFont.truetype(font, rfs)
    for i, s in enumerate(sat):
        yd.text((W / 2, ust + fs + i * lh), s, font=f, fill='white', anchor='ms')
    sy = ust + len(sat) * lh + rfs * 1.6
    yd.text((W / 2, sy), ref, font=rf, fill=(241, 214, 153, 255), anchor='ms')
    for e in es_sat:
        sy += vfs * 1.5; efs = vfs; ef = yazi_tipi(efs, 'Regular')
        while yd.textlength(e, font=ef) > W * 0.9 and efs > 12: efs = int(efs * 0.95); ef = yazi_tipi(efs, 'Regular')
        yd.text((W / 2, sy), e, font=ef, fill=(255, 255, 255, 235), anchor='ms')
    g = yazi.split()[3].filter(ImageFilter.GaussianBlur(fs * 0.3)).point(lambda v: int(v * .85))
    sh = Image.new('RGBA', (W, H), (0, 0, 0, 0)); sh.putalpha(g)
    im.alpha_composite(sh); im.alpha_composite(yazi)
    return im, sy + vfs * 1.5, vfs, v_sat

ip = os.path.join(cikti, 'iphone'); os.makedirs(os.path.join(ip, 'vakit'), exist_ok=True)
satir_y = {}   # dosya eki → (vakit satırının y'si, yazı boyu, satır sayısı)
for ek, yer, k in [('orta', 'orta', 1.0)] + [(e, 'alt', kk) for _, kk, e in BOYUTLAR]:
    im, y, vfs, vs = ciz(yer, k)
    im.save(os.path.join(ip, f'bugun-{ek}.png'), optimize=True)
    satir_y[ek] = (y, vfs, vs)
# Kestirmenin "Yazı büyüklüğü" listesi: boyutlar.txt (adlar), boyutlar.json {ad: dosya eki}
open(os.path.join(ip, 'boyutlar.txt'), 'w', encoding='utf-8').write('\n'.join(ad for ad, _, _ in BOYUTLAR))
json.dump({ad: e for ad, _, e in BOYUTLAR}, open(os.path.join(ip, 'boyutlar.json'), 'w', encoding='utf-8'), ensure_ascii=False)
open(os.path.join(ip, 'bugun.txt'), 'w', encoding='utf-8').write(f"{a['meal']}\n— {ref}\n{a['esma']}\n")
open(os.path.join(ip, 'tarih.txt'), 'w', encoding='utf-8').write(bugun.isoformat())  # kestirme 'bugün yenilendi mi' kontrolünü buna göre yapar
print(bugun, ref, '|', a['esma'])

# Her ilçe için vakit satırı: "05:51 · 07:16 · 12:37 · 15:23 · 17:49 · 19:09" (büyük yazıda 3 + 3 iki satır)
def vakit_katmani(satirlar, y, vfs):
    vf = yazi_tipi(vfs, 'SemiBold')
    k = Image.new('RGBA', (W, int(vfs * (0.8 + 1.5 * len(satirlar)))), (0, 0, 0, 0)); kd = ImageDraw.Draw(k)
    for i, m in enumerate(satirlar): kd.text((W / 2, vfs * 1.4 + i * vfs * 1.5), m, font=vf, fill=(241, 214, 153, 255), anchor='ms')
    g = k.split()[3].filter(ImageFilter.GaussianBlur(vfs * 0.3)).point(lambda q: int(q * .85))
    sh = Image.new('RGBA', k.size, (0, 0, 0, 0)); sh.putalpha(g); sh.alpha_composite(k)
    tam = Image.new('RGBA', (W, H), (0, 0, 0, 0)); tam.alpha_composite(sh, (0, int(y - vfs * 1.4)))
    return tam.quantize(64, method=Image.Quantize.FASTOCTREE)

vk = os.path.join(kok, 'vakitler'); sayi = eksik = 0
for ad in os.listdir(vk):
    if ad == 'iller.json' or not ad.endswith('.json'): continue
    v = json.load(open(os.path.join(vk, ad), encoding='utf-8'))
    dz = v['gunler'].get(bugun.isoformat())
    if not dz: eksik += 1; continue
    for ek, (y, vfs, vs) in satir_y.items():
        satirlar = ['  ·  '.join(dz)] if vs == 1 else ['  ·  '.join(dz[:3]), '  ·  '.join(dz[3:])]
        vakit_katmani(satirlar, y, vfs).save(os.path.join(ip, 'vakit', f"{v['id']}-{ek}.png"), optimize=True)
    sayi += 1
print('vakit satırı', sayi, 'ilçe ×', len(satir_y), 'boyut, verisi olmayan', eksik)

# Kestirmenin il/ilçe seçimi için listeler: iller.txt, iller.json {İl: kısa ad}, ilce/<kısa>.txt, ilce/<kısa>.json {İlçe: kod}
import unicodedata
def kisa(s):
    s = s.replace('ı', 'i').replace('İ', 'i').replace('ğ', 'g').replace('Ğ', 'g').replace('ş', 's').replace('Ş', 's').replace('ç', 'c').replace('Ç', 'c').replace('ö', 'o').replace('Ö', 'o').replace('ü', 'u').replace('Ü', 'u')
    return ''.join(c for c in unicodedata.normalize('NFKD', s.lower()) if c.isalnum())
il_listesi = json.load(open(os.path.join(kok, 'vakitler', 'iller.json'), encoding='utf-8'))
os.makedirs(os.path.join(ip, 'ilce'), exist_ok=True)
open(os.path.join(ip, 'iller.txt'), 'w', encoding='utf-8').write('\n'.join(i['ad'] for i in il_listesi))
json.dump({i['ad']: kisa(i['ad']) for i in il_listesi}, open(os.path.join(ip, 'iller.json'), 'w', encoding='utf-8'), ensure_ascii=False)
for i in il_listesi:
    sec = [('Merkez', i['id'])] + [(c['ad'], c['id']) for c in i.get('ilceler', []) if c['ad'] != i['ad']]
    open(os.path.join(ip, 'ilce', kisa(i['ad']) + '.txt'), 'w', encoding='utf-8').write('\n'.join(a for a, _ in sec))
    json.dump(dict(sec), open(os.path.join(ip, 'ilce', kisa(i['ad']) + '.json'), 'w', encoding='utf-8'), ensure_ascii=False)
print('il/ilçe listeleri', len(il_listesi))
