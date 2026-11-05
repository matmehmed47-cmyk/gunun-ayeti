import json, re, sys
ind, repo = sys.argv[1], sys.argv[2]
def yukle(p):
    d = json.load(open(p, encoding='utf-8'))['data']['surahs']
    return {(s['number'], a['numberInSurah']): a['text'] for s in d for a in s['ayahs']}, {s['number']: len(s['ayahs']) for s in d}
tr, say = yukle(ind + '/yazir.json')
en, _ = yukle(ind + '/sahih.json')
kayit, bolum, sorun, sure_ad = [], None, [], {}
for satir in open(repo + '/veri/ayet-listesi.txt', encoding='utf-8'):
    if satir.startswith('## BÖLÜM'): bolum = satir.split()[-1]
    m = re.match(r'^(\d+):(\d+)(?:-(\d+))? \| (.+?) \| (.+?) \| (.+)$', satir.strip())
    if not m: continue
    s, a1 = int(m[1]), int(m[2]); a2 = int(m[3] or a1)
    if s not in say or a2 > say[s] or a1 > a2: sorun.append(('NUMARA YOK', satir.strip())); continue
    parca = []
    for a in range(a1, a2 + 1):
        x = tr[(s, a)].split('{*}')[0].strip()
        if x and (not parca or x != parca[-1]): parca.append(x)
    mt = ' '.join(parca)
    mt = mt.replace("genişlik ver, İşimi kolaylaştır, Dilimden düğümü çöz Ki,", "genişlik ver, işimi kolaylaştır, dilimden düğümü çöz ki").replace("muhtaç değildir Doğurmadı", "muhtaç değildir). Doğurmadı").replace("O 'na", "O'na")
    if mt.count('"') % 2:
        if mt.endswith('"') and not mt.lstrip().startswith('"'): mt = mt[:-1].rstrip()
        elif mt.startswith('"'): mt = mt[1:].lstrip()
        elif mt.endswith('".'): mt = mt[:-2] + '.'
        else: mt = mt + '"'
    if mt.count('"') % 2: sorun.append(('TIRNAK', f'{s}:{a1}'))
    mt = mt.replace('  ', ' ').strip()
    me = ' '.join(en[(s, a)] for a in range(a1, a2 + 1))
    for a in range(a1, a2 + 1):
        if not tr[(s, a)].strip(): sorun.append(('BOŞ METİN', f'{s}:{a}'))
        if a > 1 and tr[(s, a)] == tr[(s, a - 1)] and a == a1: sorun.append(('ÖNCEKİYLE AYNI', f'{s}:{a}'))
        if '{' in tr[(s, a)] or '[' in tr[(s, a)]: sorun.append(('İŞARET', f'{s}:{a}'))
    sure_ad.setdefault(s, m[4])
    kayit.append(dict(sure_no=s, ref=f'{s}:{a1}' + (f'-{a2}' if a2 != a1 else ''), sure=m[4], konu=m[5], ozet=m[6], bolum=bolum, meal=mt, en=me))
for k in kayit: k['sure'] = sure_ad[k.pop('sure_no')]
json.dump(kayit, open(sys.argv[3], 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
uz = sorted(kayit, key=lambda k: -len(k['meal']))
print('kayit', len(kayit)); print('sorunlar', sorun)
print('350 ustu:', sum(len(k['meal']) > 350 for k in kayit), ' 500 ustu:', sum(len(k['meal']) > 500 for k in kayit))
for k in uz[:15]: print(len(k['meal']), k['ref'], k['ozet'])
