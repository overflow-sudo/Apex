# Maç skorları (ESPN)

(CLAUDE.md'den taşındı, 2026-10-31. Genel kurallar CLAUDE.md'de.)

## Maç skorları (`modules/football.py`)
- Kaynak ESPN, anahtar gerekmez. `site.api.espn.com` Türkiye'den **Access Denied** veriyor; **`site.web.api.espn.com`
  çalışıyor**. Ligler: `tur.1` (Süper Lig), `uefa.champions`. `?dates=YYYYMMDD` tek gün çalışıyor, tarih aralığı
  400 veriyor. Tarih vermeden çağırınca güncel hafta geliyor (ŞL için gerekli).
- 5 dk'da bir güncel hafta + dün..+3 gün çekilir. Canlı maç varken ya da 20 dk içinde maç başlayacaksa 30 sn'de bir
  sadece bugün çekilir. 8 günden eski maçlar silinir.
- Adlar Türkçeleştiriliyor ve kısaltılıyor (`TR_TEAMS`: GS, FB, BJK, TS, İBFK...). Durum: İY, MS, UZ, PEN, dakika,
  "Yarın 21:30". `FOOTBALL["favorites"]`'e takım yazılırsa o takımın maçları hep öne çıkar.
- Sağ üst kutu (`@extra("score")`): canlı maçlar (favori > Türk takımı > SL), yoksa favori / son biten / bugünün
  maçları. Birden çok maç varsa 6 sn'de bir sırayla gösterilir. Dokununca iki sütunlu maç listesi açılır
  (`football.list` eylemi, açıkken 30 sn'de bir yenilenir). Skor varken dar ekranda ikincil durum etiketleri gizlenir.
- Takım logoları `a.espncdn.com`'dan, telefon doğrudan yükler.
