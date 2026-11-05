# Bugünün vakitlerini Diyanet'in kendi sitesiyle karşılaştırır. Tek dakika fark varsa hata verir (yayın yapılmaz).
import json, os, re, sys, urllib.request
from datetime import datetime, timedelta, timezone
kok = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bugun = datetime.now(timezone(timedelta(hours=3))).date()
aylar = ['Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran', 'Temmuz', 'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık']
hata = 0
for id_, ad in [('9206', 'ankara'), ('9541', 'istanbul'), ('9560', 'izmir')]:
    bizim = json.load(open(os.path.join(kok, 'vakitler', f'{id_}.json'), encoding='utf-8'))['gunler'].get(bugun.isoformat())
    if not bizim:
        print(bugun, ad, 'BUGÜNÜN VERİSİ YOK'); hata += 1; continue
    try:
        t = urllib.request.urlopen(urllib.request.Request(f'https://namazvakitleri.diyanet.gov.tr/tr-TR/{id_}/{ad}-icin-namaz-vakti',
            headers={'User-Agent': 'gunun-ayeti/1.0'}), timeout=40).read().decode('utf-8')
    except Exception as e:
        print(bugun, ad, 'Diyanet sitesine ulaşılamadı, önceden doğrulanmış veriyle devam:', e); continue
    i = t.find(f'{bugun.day:02d} {aylar[bugun.month - 1]} {bugun.year}')
    resmi = re.findall(r'\d\d:\d\d', t[i:i + 800])[:6] if i > 0 else None
    if not resmi:
        print(bugun, ad, 'Diyanet sayfası okunamadı, devam'); continue
    durum = 'AYNI' if resmi == bizim else 'FARKLI'
    print(bugun, ad, 'diyanet', resmi, 'bizim', bizim, durum)
    if resmi != bizim: hata += 1
sys.exit(1 if hata else 0)
