# iPhone kestirmesi için: bugünün ayetini şeffaf zeminli resme yazar (kullanıcının fotoğrafının üstüne bindirilir).
# Çıktı (<çıktı>/iphone/): bugun-orta.png, bugun-alt.png, bugun.txt, vakit/<ilçeID>-<yer>.png (6 vakit, şeffaf, tam ekran)
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

def ciz(yer):
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    gen, fs = W * 0.8, int(W * 0.044)
    while True:
        f = ImageFont.truetype(font, fs)
        try: f.set_variation_by_name('SemiBold')
        except Exception: pass
        sat = sar(d, a['meal'], f, gen)
        if len(sat) * fs * 1.45 < H * 0.22 or fs < W * 0.028: break
        fs = int(fs * 0.94)
    lh, rfs = fs * 1.45, int(fs * 0.72)
    vfs = int(rfs * 0.92)
    blok = len(sat) * lh + rfs * 2.2 + vfs * 3.0  # esma ve vakit satırlarına da yer
    merkez = H * (0.78 if yer == 'alt' else 0.52)
    ust, pay = merkez - blok / 2, fs * 2.2
    if ust + blok > H * 0.86: ust = H * 0.86 - blok
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
    yd.text((W / 2, ust + len(sat) * lh + rfs * 1.6), ref, font=rf, fill=(241, 214, 153, 255), anchor='ms')
    ef = ImageFont.truetype(font, vfs)
    efs = vfs
    while True:
        try: ef.set_variation_by_name('Regular')
        except Exception: pass
        if yd.textlength(a['esma'], font=ef) <= W * 0.9 or efs < 12: break
        efs = int(efs * 0.95); ef = ImageFont.truetype(font, efs)
    yd.text((W / 2, ust + len(sat) * lh + rfs * 1.6 + vfs * 1.5), a['esma'], font=ef, fill=(255, 255, 255, 235), anchor='ms')
    g = yazi.split()[3].filter(ImageFilter.GaussianBlur(fs * 0.3)).point(lambda v: int(v * .85))
    sh = Image.new('RGBA', (W, H), (0, 0, 0, 0)); sh.putalpha(g)
    im.alpha_composite(sh); im.alpha_composite(yazi)
    return im, ust + len(sat) * lh + rfs * 1.6 + vfs * 3.0, vfs

ip = os.path.join(cikti, 'iphone'); os.makedirs(os.path.join(ip, 'vakit'), exist_ok=True)
satir_y = {}
for yer in ('orta', 'alt'):
    im, y, vfs = ciz(yer)
    im.save(os.path.join(ip, f'bugun-{yer}.png'), optimize=True)
    satir_y[yer] = y
open(os.path.join(ip, 'bugun.txt'), 'w', encoding='utf-8').write(f"{a['meal']}\n— {ref}\n{a['esma']}\n")
open(os.path.join(ip, 'tarih.txt'), 'w', encoding='utf-8').write(bugun.isoformat())  # kestirme 'bugün yenilendi mi' kontrolünü buna göre yapar
print(bugun, ref, '|', a['esma'])

# Her ilçe için vakit satırı: "05:51 · 07:16 · 12:37 · 15:23 · 17:49 · 19:09"
vf = ImageFont.truetype(font, vfs)
try: vf.set_variation_by_name('SemiBold')
except Exception: pass
vk = os.path.join(kok, 'vakitler'); sayi = eksik = 0
for ad in os.listdir(vk):
    if ad == 'iller.json' or not ad.endswith('.json'): continue
    v = json.load(open(os.path.join(vk, ad), encoding='utf-8'))
    dz = v['gunler'].get(bugun.isoformat())
    if not dz: eksik += 1; continue
    metin = '  ·  '.join(dz)
    for yer, y in satir_y.items():
        k = Image.new('RGBA', (W, int(vfs * 2.2)), (0, 0, 0, 0)); kd = ImageDraw.Draw(k)
        kd.text((W / 2, vfs * 1.4), metin, font=vf, fill=(241, 214, 153, 255), anchor='ms')
        g = k.split()[3].filter(ImageFilter.GaussianBlur(vfs * 0.3)).point(lambda q: int(q * .85))
        sh = Image.new('RGBA', k.size, (0, 0, 0, 0)); sh.putalpha(g); sh.alpha_composite(k)
        tam = Image.new('RGBA', (W, H), (0, 0, 0, 0)); tam.alpha_composite(sh, (0, int(y - vfs * 1.4)))
        tam.quantize(64, method=Image.Quantize.FASTOCTREE).save(os.path.join(ip, 'vakit', f"{v['id']}-{yer}.png"), optimize=True)
    sayi += 1
print('vakit satırı', sayi, 'ilçe, verisi olmayan', eksik)

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
