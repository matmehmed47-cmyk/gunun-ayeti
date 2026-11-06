# Diyanet'in her konum için verdiği kıble açısını (pusulaya göre, derece) toplar → veri/kible_aci.json {id: açı}
# Açılar değişmez; bir kez çalıştırmak yeter. Eksik kalanları tamamlamak için tekrar çalıştırılabilir.
import json, os, re, html, time, urllib.request
KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = {'User-Agent': 'gunun-ayeti/1.0 (+https://github.com/matmehmed47-cmyk/gunun-ayeti)'}
yol = os.path.join(KOK, 'veri', 'kible_aci.json')
aci = json.load(open(yol)) if os.path.exists(yol) else {}
idler = sorted(f[:-5] for f in os.listdir(os.path.join(KOK, 'vakitler')) if f.endswith('.json') and f != 'iller.json')
for i, id_ in enumerate(idler):
    if id_ in aci: continue
    for d in range(3):
        try:
            t = html.unescape(urllib.request.urlopen(urllib.request.Request(f'https://namazvakitleri.diyanet.gov.tr/tr-TR/{id_}/x', headers=UA), timeout=30).read().decode('utf-8'))
            m = re.search(r'için kıble açısı (\d+(?:[.,]\d+)?) derecedir', t) or re.search(r'Kıble Açısı\D{0,200}?(\d+(?:[.,]\d+)?)', t, re.S)
            if m: aci[id_] = float(m.group(1).replace(',', '.'))
            break
        except Exception: time.sleep(5)
    if i % 25 == 0: json.dump(aci, open(yol, 'w'), sort_keys=True); print(i, len(aci), flush=True)
    time.sleep(1)
json.dump(aci, open(yol, 'w'), sort_keys=True)
print('bitti', len(aci), 'eksik', [x for x in idler if x not in aci])
