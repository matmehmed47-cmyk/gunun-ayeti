# İmzasız kestirmeyi RoutineHub HubSign servisiyle imzalar (Mac gerekmez). Kullanım: imzala.py <girdi> <çıktı>
import json, plistlib, sys, urllib.request
xml = plistlib.dumps(plistlib.load(open(sys.argv[1], 'rb')), fmt=plistlib.FMT_XML).decode()
req = urllib.request.Request('https://hubsign.routinehub.services/sign',
    data=json.dumps({'shortcutName': 'Günün Ayeti', 'shortcut': xml}).encode(),
    headers={'Content-Type': 'application/json', 'User-Agent': 'gunun-ayeti/1.0'}, method='POST')
b = urllib.request.urlopen(req, timeout=90).read()
if b[:4] != b'AEA1': sys.exit('İmzalı kestirme gelmedi')
open(sys.argv[2], 'wb').write(b); print('imzalandı', len(b), 'bayt')
