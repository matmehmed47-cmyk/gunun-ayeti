# iPhone kestirmesi için: bugünün ayetini şeffaf zeminli resme yazar (kullanıcının fotoğrafının üstüne bindirilir).
# Çıktı: iphone/bugun-orta.png, iphone/bugun-alt.png, iphone/bugun.txt   Kullanım: python3 iphone_resim.py <font.ttf>
import json, os, re, sys
from datetime import datetime, timedelta, timezone
from PIL import Image, ImageDraw, ImageFilter, ImageFont

kok = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
font = sys.argv[1]
bas = re.search(r'const BASLANGIC = "(\d{4})-(\d{2})-(\d{2})"', open(os.path.join(kok, 'index.html'), encoding='utf-8').read())
ay = json.load(open(os.path.join(kok, 'veri', 'sirali.json'), encoding='utf-8'))
bugun = datetime.now(timezone(timedelta(hours=3))).date()
gun = max(0, (bugun - datetime(*map(int, bas.groups())).date()).days)
a = ay[gun % len(ay)]
ref = f"{a['sure']} Suresi, {a['ref'].split(':')[1]}. ayet"
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
    gen, fs = W * 0.8, int(W * 0.056)
    while True:
        f = ImageFont.truetype(font, fs); sat = sar(d, a['meal'], f, gen)
        if len(sat) * fs * 1.45 < H * 0.3 or fs < W * 0.03: break
        fs = int(fs * 0.94)
    lh, rfs = fs * 1.45, int(fs * 0.72)
    blok = len(sat) * lh + rfs * 2.2
    merkez = H * (0.70 if yer == 'alt' else 0.52)
    ust, pay = merkez - blok / 2, fs * 2.2
    bant = Image.new('L', (1, 256))
    for y in range(256):
        t = y / 255
        bant.putpixel((0, y), int(128 * (t / .25 if t < .25 else (1 - t) / .25 if t > .75 else 1)))
    bant = bant.resize((W, int(blok + 2 * pay)))
    golge = Image.new('RGBA', bant.size, (0, 0, 0, 0)); golge.putalpha(bant)
    im.alpha_composite(golge, (0, int(ust - pay)))
    yazi = Image.new('RGBA', (W, H), (0, 0, 0, 0)); yd = ImageDraw.Draw(yazi)
    rf = ImageFont.truetype(font, rfs)
    for i, s in enumerate(sat):
        yd.text((W / 2, ust + fs + i * lh), s, font=f, fill='white', anchor='ms')
    yd.text((W / 2, ust + len(sat) * lh + rfs * 1.6), ref, font=rf, fill=(236, 208, 143, 255), anchor='ms')
    g = yazi.split()[3].filter(ImageFilter.GaussianBlur(fs * 0.25)).point(lambda v: int(v * .6))
    sh = Image.new('RGBA', (W, H), (0, 0, 0, 0)); sh.putalpha(g)
    im.alpha_composite(sh); im.alpha_composite(yazi)
    return im

os.makedirs(os.path.join(kok, 'iphone'), exist_ok=True)
for yer in ('orta', 'alt'):
    ciz(yer).save(os.path.join(kok, 'iphone', f'bugun-{yer}.png'), optimize=True)
open(os.path.join(kok, 'iphone', 'bugun.txt'), 'w', encoding='utf-8').write(f"{a['meal']}\n— {ref}\n")
print(bugun, 'gün', gun + 1, ref)
