# 81 il + tüm ilçelerin Diyanet namaz vakitlerini indirir: vakitler/<ilçeID>.json + vakitler/iller.json
# Kaynak: ezanvakti.emushaf.net (Diyanet verisinin aynası). Doğrulama: 3 il Diyanet'in kendi sitesiyle karşılaştırılır.
import json, os, re, sys, time, urllib.request
from datetime import date, datetime, timedelta, timezone

kok = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
iller = json.load(open(os.path.join(kok, 'veri', 'iller.json'), encoding='utf-8'))
cikti = os.path.join(kok, 'vakitler'); os.makedirs(cikti, exist_ok=True)
bugun = datetime.now(timezone(timedelta(hours=3))).date()
UA = {'User-Agent': 'gunun-ayeti/1.0 (+https://github.com/matmehmed47-cmyk/gunun-ayeti)'}

def al(url):
    for i in range(4):
        try:
            return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40).read().decode('utf-8')
        except Exception as e:
            hata = e; time.sleep(3 * (i + 1))
    raise hata

def baslik(s):  # ANKARA -> Ankara, İZMİR -> İzmir, AĞRI -> Ağrı
    s = s.replace('I', 'ı').replace('İ', 'i').lower()
    return ' '.join(k[:1].replace('i', 'İ').replace('ı', 'I').upper() + k[1:] for k in s.split())

liste, hatali, toplam = [], [], 0
def kaydet(id_, il_adi, ilce_adi):
    global toplam
    toplam += 1
    try:
        ham = json.loads(al(f'https://ezanvakti.emushaf.net/vakitler/{id_}'))
    except Exception:
        hatali.append(ilce_adi); return
    yol = os.path.join(cikti, f'{id_}.json')
    eski = json.load(open(yol, encoding='utf-8'))['gunler'] if os.path.exists(yol) else {}
    for g in ham:
        gun, ay, yil = g['MiladiTarihKisa'].split('.')
        eski[f'{yil}-{ay}-{gun}'] = [g['Imsak'], g['Gunes'], g['Ogle'], g['Ikindi'], g['Aksam'], g['Yatsi']]
    gunler = {k: v for k, v in sorted(eski.items()) if k >= (bugun - timedelta(days=1)).isoformat()}
    json.dump({'id': id_, 'il': baslik(il_adi), 'ad': baslik(ilce_adi), 'gunler': gunler}, open(yol, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    time.sleep(0.25)

sira = lambda s: s.replace('Ç', 'Cz').replace('Ş', 'Sz').replace('İ', 'Iz').replace('Ö', 'Oz').replace('Ü', 'Uz').replace('Ğ', 'Gz')
for il in iller:
    for c in il['ilceler']:
        kaydet(c['id'], il['il'], c['ad'])
    ilceler = sorted(({'ad': baslik(c['ad']), 'id': c['id']} for c in il['ilceler']), key=lambda x: sira(x['ad']))
    liste.append({'ad': baslik(il['il']), 'id': il['merkez'], 'ilceler': ilceler})

# Doğrulama: Diyanet'in kendi sitesi
for id_, ad in [('9206', 'ankara'), ('9541', 'istanbul'), ('9560', 'izmir')]:
    t = al(f'https://namazvakitleri.diyanet.gov.tr/tr-TR/{id_}/{ad}-icin-namaz-vakti')
    aylar = ['Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran', 'Temmuz', 'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık']
    i = t.find(f'{bugun.day:02d} {aylar[bugun.month - 1]} {bugun.year}')
    resmi = re.findall(r'\d\d:\d\d', t[i:i + 800])[:6] if i > 0 else None
    bizim = json.load(open(os.path.join(cikti, f'{id_}.json'), encoding='utf-8'))['gunler'].get(bugun.isoformat())
    print(ad, 'diyanet', resmi, 'bizim', bizim)
    if resmi and bizim != resmi:
        print('UYUMSUZ: yayınlanmıyor'); sys.exit(1)

json.dump(sorted(liste, key=lambda x: sira(x['ad'])),
          open(os.path.join(cikti, 'iller.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print('il', len(liste), 'ilçe', toplam, 'hatalı', len(hatali), hatali[:20])
if len(liste) < 81 or len(hatali) > toplam * 0.05: sys.exit(1)
