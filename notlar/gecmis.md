# Değişiklik geçmişi ve henüz yapılmamış fikirler

(CLAUDE.md'den taşındı, 2026-10-31. Genel kurallar CLAUDE.md'de.)

## Değişiklik geçmişi
- 2026-10-31: Eklenti sistemi (`eklentiler/`, `window.PCK`, `core/plugin.py`). Minecraft haritası ilk eklenti oldu; önce/sonra
  ekran görüntüleri birebir aynı. Kur.bat artık kaldırılan modül/eklenti dosyalarını çalışan kopyadan siliyor.
- 2026-10-31: Taşınabilirlik: bu PC'ye özel ayarlar `yerel/bu_pc.json`'a taşındı (monitor_adlari.json dahil), Modlar sekmesinde
  kurulum sihirbazı, yeni PC'de Kur.bat kurulum sayfasını açıyor.
- 2026-10-31: PC klavyesinden telefonun sekmelerini değiştirme (Ctrl+Alt+Shift + 1–9 / ←→). Attack Shark pili 0–10 seviye (×10).
- 2026-10-31: Sistem sekmesine fare/klavye/kulaklık pil kartları (Attack Shark + G HUB websocket + HyperX HID),
  kritik pilde üst çubukta yanıp sönen ikon.
- 2026-10-31: .py dosyaları değişince kumanda kendini yeniden başlatıyor (`core/reloader.py`).
- 2026-10-25: İlk sürüm tek dosyaydı (`pc_kumanda_eski.py`). Mod ayarları boş olduğu için Oyun ve Masaüstü modları çalışmıyordu.
- 2026-10-25: Aygıt adlarıyla modlar dolduruldu, Müzik modu eklendi.
- 2026-10-31: CurseForge desteği: mod 1.0.1 oyun klasörünü bildiriyor, Horizon instance'ına kuruldu.
- 2026-10-31: Masaüstü tarayıcı desteği (orantılı zoom, fare tekerleği/sağ tık, klavye kısayolları). Biyom yüksekliğe göre.
- 2026-10-31: Güç paneli (kapat / yeniden başlat / uyku, basılı tutarak). Harita sekmesi sadece oyun açıkken.
- 2026-10-31: Harita: kayıtlı yerler, biyom adları, tüm yapı türleri + katman menüsü, kaleler seed başına bir kez.
- 2026-10-31: Harita: 1:256 zum, hedef + kuş uçuşu rota, X/Z arama, SSE (~0,1 sn), mod 1.0.2 (10 Hz).
- 2026-10-31: Minecraft canlı konum + seed haritası (Fabric köprü modu, cubiomes DLL, otomatik seed).
- 2026-10-26: Oyun yokken masaüstü duvar kağıdı kumanda arka planı oluyor. Oyun teması gelince gizleniyor.
- 2026-10-26: Şu an çalan medya kutusu ve kontrol paneli eklendi (SMTC, PowerShell). `@route` kancası eklendi.
- 2026-10-25: Otomatik oyun teması eklendi (logodan renk, SteamSpy etiketlerinden efekt ve tuşlar, önbellekli).
  Riot, Ubisoft, EA, GOG, Rockstar ve Amazon klasörleri de tanınıyor.
- 2026-10-25: Sağ üstte canlı maç skoru (Süper Lig + ŞL, ESPN, takım logolarıyla) ve maç listesi eklendi.
  Oyun logoları eklendi (kartlarda ve filigran olarak). Klavyede tuş başına renk düzeltmesi yapıldı (doğrulanmadı).
- 2026-10-25: Logitech G915 klavye ışığı oyun temasını takip ediyor (LIGHTSYNC SDK, ctypes). `@section` kancası eklendi.
- 2026-10-25: Ara sıra çıkan "kapalı" ekranı düzeltildi: bayat-ama-hızlı önbellek, 3 hata kuralı,
  önbellek ön ısıtma, BrokenPipe susturma, oyun teması 15 sn tutma, CamelCase klasör adları ("The Long Dark").
- 2026-10-25: Oyuna göre tema eklendi (8 oyun + bilinmeyen Steam/Epic/Xbox oyunları), arka plan efektleri,
  Tema sekmesi, `@extra` kayıt kancası, durum etiketlerinde `{text,value,lang}` desteği.
- 2026-10-25: PC kapalıyken anime gözlü bekleme ekranı, otomatik yeniden bağlanma ("BAĞLANTI YOK"
  etiketinin geri gelince silinmemesi hatası düzeltildi), sürüm değişince sayfanın kendiliğinden yenilenmesi eklendi.
- 2026-10-25: Tüm kullanıcılar için otomatik başlatma (Kur.bat/Kaldir.bat, C:\PC_Kumanda) ve Sistem sekmesi eklendi.
  `/api/ui` artık sekme bazlı çalışıyor, sekmeye göre `poll` süresi verilebiliyor, `stats` widget'ı eklendi.
- 2026-10-25: Modüler yapıya geçildi (core/ + modules/ + web/). Yatay siyah-beyaz arayüz yapıldı,
  ses girişi listesi eklendi, aktif mod artık sistem durumundan hesaplanıyor.

## Fikirler (henüz yapılmadı)
- Kulaklık şarj oluyor bilgisi (bkz. `notlar/pil.md`).
- Ses seviyesi kaydırıcısı: SVV `/SetVolume`, `/Mute`. Bunun için yeni bir `slider` widget türü gerekir.
- Medya tuşları (oynat/duraklat/ileri): `ctypes` ile `keybd_event` VK_MEDIA_*.
- Bilgisayarı uyku/kapat: `shutdown /s /t 0`, `rundll32 powrprof.dll,SetSuspendState`. Onay iste.
- Oyun başlatıcı sekmesi: Steam `steam://rungameid/<id>` bağlantıları.
- Smart M70F'yi ağ üzerinden açıp kapatma (Samsung Tizen WebSocket / SmartThings).
- Müzik modu için akort aleti + metronom.
- Uygulama/oyun başlatıcı, ekran koruyucu (saat + mod).
