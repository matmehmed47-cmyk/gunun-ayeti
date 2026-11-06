# 81 il + tüm ilçelerin Diyanet namaz vakitlerini indirir: vakitler/<ilçeID>.json + vakitler/iller.json
# Kaynak: ezanvakti.emushaf.net (Diyanet verisinin aynası). Doğrulama: 3 il Diyanet'in kendi sitesiyle karşılaştırılır.
import json, os, re, sys, time, urllib.request
from datetime import date, datetime, timedelta, timezone

kok = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
iller = json.load(open(os.path.join(kok, 'veri', 'iller.json'), encoding='utf-8'))
ek_ilce = json.load(open(os.path.join(kok, 'veri', 'ek_ilceler.json'), encoding='utf-8'))['ilceler']
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

def baslik(s):  # ANKARA -> Ankara, İZMİR -> İzmir, AĞRI -> Ağrı; 'KEMER (B)' -> Kemer
    s = re.sub(r'\s*\([A-ZÇĞİÖŞÜ]\)$', '', s.strip())
    s = s.replace('I', 'ı').replace('İ', 'i').lower()
    return ' '.join(k[:1].replace('i', 'İ').replace('ı', 'I').upper() + k[1:] for k in s.split())

liste, hatali, toplam = [], [], 0
_ka = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'veri', 'kible_aci.json')
KIBLE_ACI = json.load(open(_ka)) if os.path.exists(_ka) else {}
def kaydet(id_, il_adi, ilce_adi):
    global toplam
    toplam += 1
    try:
        ham = json.loads(al(f'https://ezanvakti.emushaf.net/vakitler/{id_}'))
    except Exception:
        hatali.append(ilce_adi); return
    yol = os.path.join(cikti, f'{id_}.json')
    onceki = json.load(open(yol, encoding='utf-8')) if os.path.exists(yol) else {}
    eski = onceki.get('gunler', {}); kible = onceki.get('kible', {})
    for g in ham:
        gun, ay, yil = g['MiladiTarihKisa'].split('.')
        eski[f'{yil}-{ay}-{gun}'] = [g['Imsak'], g['Gunes'], g['Ogle'], g['Ikindi'], g['Aksam'], g['Yatsi']]
        if g.get('KibleSaati'): kible[f'{yil}-{ay}-{gun}'] = g['KibleSaati']  # güneşin kıble yönünde olduğu an
    gunler = {k: v for k, v in sorted(eski.items()) if k >= (bugun - timedelta(days=1)).isoformat()}
    sinir = (bugun - timedelta(days=1)).isoformat()
    veri = {'id': id_, 'il': baslik(il_adi), 'ad': baslik(ilce_adi), 'gunler': gunler,
            'kible': {k: v for k, v in sorted(kible.items()) if k >= sinir}}
    if id_ in KIBLE_ACI: veri['aci'] = KIBLE_ACI[id_]  # Diyanet'in kıble açısı (pusulaya göre)
    json.dump(veri, open(yol, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    time.sleep(0.25)

TAKMA = {'Doğubeyazıt': 'Doğubayazıt', 'Karadeniz Ereğli': 'Ereğli', 'Ordu': 'Altınordu'}
sira = lambda s: s.lower().replace('ç', 'cz').replace('ğ', 'gz').replace('ı', 'hz').replace('i̇', 'i').replace('ö', 'oz').replace('ş', 'sz').replace('ü', 'uz')  # Türkçe alfabe sırası
for il in iller:
    for c in il['ilceler']:
        kaydet(c['id'], il['il'], c['ad'])
    ilceler = [{'ad': baslik(c['ad']), 'id': c['id']} for c in il['ilceler']]
    var = {x['ad'] for x in ilceler}
    ilceler += [{'ad': a, 'id': il['merkez']} for a in ek_ilce.get(baslik(il['il']), []) if a not in var]  # Diyanet'te ayrı yok → il merkezi
    for diy, resmi in TAKMA.items():  # Diyanet adı farklı yazılmış ilçeler: resmi adıyla da göster
        for x in list(ilceler):
            if x['ad'] == diy and resmi not in var: ilceler.append({'ad': resmi, 'id': x['id']})
    ilceler.sort(key=lambda x: sira(x['ad']))
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
