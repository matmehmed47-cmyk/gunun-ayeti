# Günün ayetini OneSignal ile herkese gönderir. GitHub Actions çalıştırır.
# Ortam: ONESIGNAL_KEY (gizli), HEMEN=1 ise hemen gönderir, yoksa bugün 07:00'ye (Türkiye) zamanlar.
import json, os, re, sys, urllib.request
from datetime import datetime, timedelta, timezone

TR = timezone(timedelta(hours=3))
APP_ID = 'bbccad47-3dde-4d34-9477-e1150081ba92'
SITE = 'https://matmehmed47-cmyk.github.io/gunun-ayeti/'
kok = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Başlangıç tarihini yayındaki index.html'den değil, depodaki index.html'den oku (uygulamayla aynı olsun)
html = open(os.path.join(kok, 'index.html'), encoding='utf-8').read()
bas = re.search(r'const BASLANGIC = "(\d{4})-(\d{2})-(\d{2})"', html)
ayetler = json.load(open(os.path.join(kok, 'veri', 'sirali.json'), encoding='utf-8'))

bugun = datetime.now(TR).date()
gun = max(0, (bugun - datetime(*map(int, bas.groups())).date()).days)
a = ayetler[gun % len(ayetler)]
ayet_no = a['ref'].split(':')[1]
alt = f"{a['sure']} Suresi, {ayet_no}. ayet"
metin = f"{a['meal']}\n— {alt}"

govde = {
    'app_id': APP_ID,
    'target_channel': 'push',
    'included_segments': ['Total Subscriptions'],
    'headings': {'en': 'Günün Ayeti', 'tr': 'Günün Ayeti'},
    'contents': {'en': metin, 'tr': metin},
    'url': SITE,
    'web_push_topic': 'gunun-ayeti',
    'idempotency_key': None,
}
if os.environ.get('HEMEN') == '1':
    del govde['idempotency_key']
else:
    govde['send_after'] = f'{bugun.isoformat()} 07:00:00 GMT+0300'
    # aynı gün iki kez gönderilmesin
    import uuid
    govde['idempotency_key'] = str(uuid.uuid5(uuid.NAMESPACE_URL, f'gunun-ayeti/{bugun.isoformat()}'))

print(f'Gün {gun + 1} (sıra {gun % len(ayetler) + 1}/{len(ayetler)}): {alt}')
istek = urllib.request.Request(
    'https://api.onesignal.com/notifications?c=push',
    data=json.dumps(govde).encode(),
    headers={'Content-Type': 'application/json', 'Authorization': 'Key ' + os.environ['ONESIGNAL_KEY']},
    method='POST')
try:
    with urllib.request.urlopen(istek, timeout=60) as r:
        cevap = json.load(r)
except urllib.error.HTTPError as e:
    print('HATA', e.code, e.read().decode()[:500]); sys.exit(1)
print('Cevap:', json.dumps(cevap, ensure_ascii=False)[:500])
if cevap.get('errors'): sys.exit(1)
