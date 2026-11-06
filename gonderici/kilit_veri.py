# Kilit ekranına ne yazılacağını tek yerden hesaplar (Android, iPhone ve site aynı bilgiyi kullanır).
# Kullanım: python3 gonderici/kilit_veri.py <çıktı klasörü>  → <çıktı>/kilit.json (bugünden 60 gün)
# Gün bilgisi: meal, ref, esma ("ad · anlam"), ust (özel gün etiketi, boş olabilir), ramazan (true ise İmsak/İftar gösterilir)
import json, os, re, sys
from datetime import date, datetime, timedelta, timezone

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def _baslangic():
    m = re.search(r'const BASLANGIC = "(\d{4})-(\d{2})-(\d{2})"', open(os.path.join(KOK, 'index.html'), encoding='utf-8').read())
    return date(*map(int, m.groups()))

AYETLER = json.load(open(os.path.join(KOK, 'veri', 'sirali.json'), encoding='utf-8'))
ESMALAR = [s.split('|') for s in open(os.path.join(KOK, 'veri', 'esmalar.txt'), encoding='utf-8').read().splitlines() if s.strip()]
BAS = _baslangic()

def bugun():
    return datetime.now(timezone(timedelta(hours=3))).date()

def gun_verisi(t):
    g = max(0, (t - BAS).days)
    a = AYETLER[g % len(AYETLER)]
    ad, anlam = ESMALAR[g % len(ESMALAR)]
    return {'meal': a['meal'], 'ref': f"{a['sure']} Suresi, {a['ref'].split(':')[1]}. ayet",
            'esma': f'{ad} · {anlam}', 'ust': '', 'ramazan': False}

if __name__ == '__main__':
    cikti = sys.argv[1] if len(sys.argv) > 1 else KOK
    b = bugun()
    veri = {(b + timedelta(days=i)).isoformat(): gun_verisi(b + timedelta(days=i)) for i in range(-1, 60)}
    json.dump({'surum': 1, 'gunler': veri}, open(os.path.join(cikti, 'kilit.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    print('kilit.json', len(veri), 'gün; bugün:', veri[b.isoformat()]['ref'], '|', veri[b.isoformat()]['esma'])
