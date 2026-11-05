# ayetler.json'u karışık sıraya dizer: art arda aynı konu grubu gelmez. Sabit tohum: hep aynı sıra çıkar.
import json, re, random, sys
kok = sys.argv[1]
grup, g = {}, None
for s in open(kok + '/veri/ayet-listesi.txt', encoding='utf-8'):
    if s.startswith('### '): g = s[4:].strip()
    m = re.match(r'^(\d+:[\d-]+) \|', s)
    if m: grup[m[1]] = g
ay = json.load(open(kok + '/veri/ayetler.json', encoding='utf-8'))
for a in ay: a['grup'] = grup[a['ref']]
rnd = random.Random(1448)
kova = {}
for a in ay: kova.setdefault(a['grup'], []).append(a)
for v in kova.values(): rnd.shuffle(v)
sira, son = [], None
while any(kova.values()):
    aday = [k for k, v in kova.items() if v and k != son] or [k for k, v in kova.items() if v]
    en = max(len(kova[k]) for k in aday)
    k = rnd.choice([k for k in aday if len(kova[k]) >= en - 3])
    sira.append(kova[k].pop()); son = k
for i, a in enumerate(sira, 1): a['gun'] = i
json.dump(sira, open(kok + '/veri/sirali.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
art = sum(sira[i]['grup'] == sira[i-1]['grup'] for i in range(1, len(sira)))
print(len(sira), 'kayıt, art arda aynı grup:', art, '| ilk 8:', [a['ref'] for a in sira[:8]])
