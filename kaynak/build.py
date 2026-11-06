# Kullanım: python3 kaynak/build.py <kök> <çıktı.html> <başlangıç YYYY-AA-GG> <onizleme: 1/0>
import json, sys
kok, cikti, bas, oniz = sys.argv[1:5]
surum = sys.argv[5] if len(sys.argv) > 5 else '0'
ay = json.load(open(kok + '/veri/sirali.json', encoding='utf-8'))
veri = json.dumps([{k: a[k] for k in ('ref', 'sure', 'konu', 'meal')} for a in ay], ensure_ascii=False).replace('</', '<\\/')
t = open(kok + '/kaynak/sablon.html', encoding='utf-8').read()
es = json.dumps([s.split('|') for s in open(kok + '/veri/esmalar.txt', encoding='utf-8').read().splitlines() if s.strip()], ensure_ascii=False)
t = t.replace('/*ESMA*/[]', es)
t = t.replace('/*VERI*/[]', veri).replace('/*BASLANGIC*/"2026-11-01"', json.dumps(bas)).replace('/*ONIZLEME*/true', 'true' if oniz == '1' else 'false').replace('/*SURUM*/0', str(int(surum)))
open(cikti, 'w', encoding='utf-8').write(t)
print(cikti, len(t) // 1024, 'KB')
