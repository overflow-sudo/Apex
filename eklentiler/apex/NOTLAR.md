# APEX FINANCE eklentisi — notlar

Emir'in portföy uygulamasını (APEX FINANCE, `C:\Users\emir\Desktop\EABorsa`, Node sunucusu `127.0.0.1:8787`) kumandada gösterir.

## Ne yapıyor
- **Portföy sekmesi** (`apex`, order 45, ikon `apex`): toplam değer, yatırılan, toplam K/Z, bugünkü değişim; "değer · yatırılan"
  çizgisi (düz = değer, kesikli = yatırılan para; başlıkta toplam getiri %); varlık listesi (değer, ağırlık, K/Z %); tür dağılımı çubuğu.
- **Boşta slayt gösterisi**: `bosta_sn` (120) saniye dokunulmazsa tam ekran iki slayt döner (`slayt_sn`, 9 sn):
  1) portföy özeti (toplam birikim, toplam K/Z, bugün), 2) sistem (CPU/GPU %, RAM/VRAM GB, CPU/GPU sıcaklığı, açık kalma süresi).
  Hangisinin verisi varsa o gösterilir (APEX kapalıyken sadece sistem). Sistem slaytı açıkken her `/api/ui` yenilemesinde geçişsiz
  güncellenir. Sağ üstte saat, altta çalan şarkı (♪) ya da "APEX FINANCE". Dokununca kapanır (dokunuş alttaki düğmelere geçmez).
  Esc / PC klavyesiyle sekme değiştirme (`close` olayı) de kapatır. (2026-11-01: Emir'in isteğiyle portföyden sadece özet ekranı kaldı.)
- **Odak rozeti** (`@focus` priority 20): ana kartın sağ üstünde küçük portföy rozeti (bugünkü %), dokununca Portföy sekmesi.
  30'un altında olduğu için arayüzü kendine odaklamaz.
- **APEX hep açık (2026-11-01, Emir'in isteği):** `_bekci` (`otomatik_ac`) kumanda açılışından `otomatik_bekle` sn sonra başlar,
  30 sn'de bir `/api/health`'e bakar, cevap yoksa konsolsuz `node server/index.ts` başlatır; üst üste çökerse bekleme 5 dk'ya kadar
  uzar. Sekmede düğme yok, kapalıyken "APEX başlatılıyor…" yazar. Eskiden sadece açılışta bir kez deneniyordu; sonradan kapanan
  APEX geri gelmiyordu. Bağlantı koparsa son iyi veri gösterilmeye devam eder (telefondaki rakamlar o sırada eski olabilir).

## Veri akışı
- `@on_start` iş parçacığı `yenile` (60 sn) aralıkla APEX API'sini okur: `/api/portfolios` → her portföy için `/summary`;
  semboller `/transactions`'tan (10 dk önbellek); geçmiş `/history` (`gecmis_yenile`, 15 dk) 60 noktaya seyreltilir.
- Özet her `/api/ui` cevabına `@extra("apex")` ile eklenir (~3 KB). Slayt gösterisi hangi sekme açık olursa olsun çalışabilsin diye.
  Portföy kişisel veri: PIN korumalı `/api/ui` üzerinden gider, bilerek `@route` kullanılmadı (route'lar PIN istemez).
- Aktif portföy (APEX'teki `activePortfolioId`) ilk sırada; sekme ve slaytlar ilk portföyü gösterir.
- Sistem slaytı `modules/system.py`'nin ölçümünü okur (`latest`, `_info`, `GB`; `from modules import system`). Ayrı ölçüm yapılmaz.
  O modülde bu adlar değişirse sistem slaytı kaybolur (eklenti `_sistem()` → None döner, `getattr` ile korunuyor sadece `_info`).

## Ayarlar (`config.py` → `APEX = {...}`, hepsi isteğe bağlı)
`url`, `klasor`, `otomatik_ac`, `otomatik_bekle`, `yenile`, `gecmis_yenile`, `slayt` (False = slayt kapalı), `bosta_sn`, `slayt_sn`,
`sistem_slayt` (False = sistem slaytı yok),
`muzik_varken` (True: müzik çalarken de slayt; False: çekirdeğin "şu an çalıyor" ekranına bırakır), `rozet`.

## Doğrulananlar (2026-11-01, test kopyası port 8766, 780×360)
- Eklenti yükleniyor, sekme çiziliyor, rakamlar APEX özetiyle aynı (₺235.376, K/Z +₺29.794 / +%14,49).
- Slayt gösterisi 20 sn boşta beklemeyle açıldı, portföy özeti ve sistem slaytı sırayla döndü, sistem değerleri canlı güncellendi,
  dokununca kapandı; müzik çalarken alt satırda şarkı göründü.
- Odak rozeti göründü, dokununca Portföy sekmesine geçti. APEX kapalı görünümü (yanlış porta yönlendirerek) doğru.
- Modlar sekmesi önceki gibi çiziliyor.

## Doğrulanmayanlar
- Gerçek eski Android telefonda (yalnızca masaüstü tarayıcıda 780×360 denendi). JS yeni sözdizimi kullanmıyor (`?.`, `??`, async yok).
- `_bekci` (otomatik başlatma) ayrı bir Python sürecinde denendi (2026-11-01, ~5 sn'de açıldı), ama gerçek kurulumda (`C:\PC_Kumanda`, pythonw) denenmedi: `node` PATH'te yoksa
  `C:\Program Files\nodejs\node.exe` aranır. APEX'in `dist/` klasörü derlenmiş olmalı (`npm.cmd run build`), API buna bağlı değil.

## Tuzaklar
- Çekirdeğin medya "ambient" ekranı 90 sn'de açılır; slayt (z-index 9000) onun üstünde durur. Slayt kapanınca altta medya paneli kalabilir.
- Grafikte değer para eklendikçe büyür; yüzdeyi değer serisinin başından sonuna göre hesaplama (eskiden "+%2.231" gösteriyordu),
  getiri = toplam K/Z / yatırılan.
