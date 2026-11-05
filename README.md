# Günün Ayeti

Her gün herkese aynı ayetin Türkçe meali gelen, link ile paylaşılan web uygulaması (yapım aşamasında).

- `veri/ayet-listesi.txt`: 400 ayetlik liste (bitince başa döner).
- `veri/ayetler.json`: listeye Elmalılı Hamdi Yazır meali eklenmiş hâli (kaynak: alquran.cloud `tr.yazir`, temizlenmiş).
- `veri/birlestir.py`: listeyi ve meali birleştiren araç.

## Yeni sürüm nasıl yapılır
1. `kaynak/sablon.html` (ekran) veya `veri/` (ayetler) güncellenir.
2. `python3 veri/sirala.py .` (liste değiştiyse)
3. `python3 kaynak/pwa_yap.py . <başlangıç YYYY-AA-GG> <sürüm no>` → index.html, sw.js, manifest, simgeler
4. commit + push. Başlangıç tarihi yayından sonra DEĞİŞTİRİLMEZ (herkesin günü kayar).
