# Duvar kağıdı, masaüstü tarayıcı, klavye kısayolları, güç paneli, bağlantı kopunca/uyku, telefon kurulumu

(CLAUDE.md'den taşındı, 2026-10-31. Genel kurallar CLAUDE.md'de.)

## Masaüstü duvar kağıdı arka planı (`modules/wallpaper.py`)
- Oyun teması yokken kumandanın arka planı, kullanıcının o an gördüğü duvar kağıdı olur. Kaynak
  `%APPDATA%\Microsoft\Windows\Themes\TranscodedWallpaper` (Windows'un kopyası, uzantısız, genelde JPEG; slayt
  gösterisinde de güncellenir). Yoksa `HKCU\Control Panel\Desktop\WallPaper` kullanılır. `/wallpaper?v=<mtime>`
  adresinden sunulur. Telefon resmi önce yükler, sonra yumuşakça gösterir.
- `body.game` sınıfı (applyTheme, oyun teması varsa) duvar kağıdını gizler, oyunun zemini görünür. Oyun bitince geri gelir.
- Okunurluk için `WALLPAPER_DIM` (varsayılan 0.55) karartma katmanı var, kart zeminleri `rgba(0,0,0,.42)`.
- Tema sekmesinde "Masaüstü duvar kağıdı" aç/kapa düğmesi var (sunucu yeniden başlayınca config değerine döner).
- Art arda gelen `buttons` section'ları tek satırda yan yana dizilir (`.brow`), art arda gelen `list`'ler sütunlara.

## Masaüstü tarayıcı
- Düzen telefona göre (yatay ~780×360). `deskScale()` (app.js): pencere yüksekliği ≥ 560 ve genişliği ≥ 900 ise
  `z = min(2.2, h/640, w/1150)` → `body.desk { zoom: var(--z) }`, `.app { height: calc(100vh / var(--z)) }`.
  Telefon bu eşiğe hiç ulaşmaz → mobil birebir aynı (ekran görüntüsü farkıyla doğrulandı).
- Standart CSS zoom: `getBoundingClientRect`/`clientX` görünüm pikseli, `clientWidth` iç piksel → harita hareketleri
  `DZ`'ye bölünür (`rel`, sürükleme). Yeni bir fare/dokunuş koordinatı kodu yazarsan aynı dönüşümü uygula.
- Fare: haritada tekerlekle imlecin altına zum, sağ tık = basılı tutma, `@media (hover: hover) and (pointer: fine)`
  ile hover/imleç. Klavye: 1–9 sekmeler, Esc panelleri kapatır, F tam ekran, R yenile, +/− harita zumu.
- Masaüstünde sistem kartları 3 sütun (`body.desk .stats`).

## Klavye kısayolları (`modules/hotkeys.py`)
- PC klavyesinden telefondaki sekmeyi değiştirir (oyun açıkken de): **Ctrl+Alt+Shift + 1–9** = telefondaki sıraya göre
  n. sekme, **Ctrl+Alt+Shift + ←/→** = önceki/sonraki. Açık paneller (medya, maçlar, güç, harita panelleri) kapanır.
- Sadece Ctrl+Alt değil: Türkçe klavyede AltGr = Ctrl+Alt, kısayol AltGr+3/7/8/9 (#{[]) yazmayı bozardı.
  `config.HOTKEY_MODS` (örn. "win+alt") ile değiştirilebilir, `config.HOTKEYS = False` kapatır.
- `RegisterHotKey` + `GetMessageW` döngüsü ayrı iş parçacığında. Telefon `/nav/stream` SSE akışını hep açık tutar
  (`navStream()` app.js), olay `{n, tab}` ya da `{n, step}`; sıra telefondaki sekme listesine göre çözülür.
  Alınamayan kısayol log'a "kısayol alınamadı" diye yazılır. Windows'ta keybd_event ile test edildi (2026-10-31).

## Güç (`modules/power.py`)
- Üst çubukta güç ikonu (`#btnPower`) → `#pwpanel`: Kapat (kırmızı) / Yeniden başlat / Uyku. Her düğme **1,2 sn basılı
  tutulunca** çalışır (dolum çubuğu), bırakınca iptal. Eylemler `power.shutdown` (`shutdown /s /t 0`),
  `power.restart` (`/r`), `power.sleep` (`powrprof.SetSuspendState(False, False, False)`); komut 1 sn gecikmeli
  ki cevap telefona ulaşsın. Windows dışında komut çalıştırılmaz, sadece loglanır (test sunucusu için güvenli).
- Sınıf adı `.main` KULLANMA (ana içerik alanıyla çakışır) → kırmızı düğme `.pwb.red`.

## Bağlantı kopunca / güncelleme
- **Kapalı sayılma:** Tek hata yetmez. Üst üste 3 hata gerekir (`fails`), hatadan sonra 1,5 sn'de tekrar denenir.
  Test: 9 sn'lik takılmada gözler çıkmıyor; gerçek kesintide ~22 sn'de çıkıyor, dönüşte ~4 sn'de bağlanıyor.
- Kapalı sayılınca `body.offline` sınıfı eklenir ve tam ekran "BİLGİSAYAR KAPALI" ekranı açılır.
  Bu ekranda JS ile çizilen SVG anime gözler var (`buildOff()`/`eye()` app.js'te, stiller `.off` altında).
  Gözler 5.6 sn'de bir kırpıyor (arada çift kırpma), etrafa bakıyor ve küçük parıltı yanıp sönüyor.
  Kapalıyken 3 sn'de bir yeniden deneniyor, tuşlar kilitli. Bağlantı gelince `.wake` sınıfı eklenir:
  gözler büyür, ekran kaybolur. Gözler Emir'in isteği, kaldırma.
- **Uyku:** PC uykudayken istekler reddedilmez, cevapsız asılı kalır. `api()` bu yüzden zaman aşımı kullanıyor
  (`withTimeout` + AbortController, GET 5 sn, POST 45 sn). Zaman aşımı kaldırılırsa uyku ekranı dakikalarca gelmez.
  Linux'ta sunucu `kill -STOP` ile dondurularak test edildi: ekran ~12 sn içinde çıkıyor, uyanınca ~3 sn içinde geri dönüyor.
- `/api/ui` cevabında `version` var (web/ dosyalarının ve pc_kumanda.py'nin en yeni mtime'ı). Arayüz
  farklı bir sürüm görürse `location.reload()` yapar. Kur.bat sonrası telefonda F5 gerekmez.
- Telefon tarayıcısı PC kapalıyken sayfayı **yenilerse** Chrome hata sayfası açılır ve kendiliğinden geri
  gelmez. Service worker HTTPS istediği için LAN'da http üzerinden kullanılamıyor.
- PC'nin IP'si değişirse telefondaki adres bozulur. Modemden DHCP rezervasyonu yapılması önerildi.

## Telefon kurulumu
- Chrome'da sayfayı aç → menüden "Ana ekrana ekle". `manifest.json` sayesinde tam ekran ve yatay açılır.
- Sağ üstteki ⛶ düğmesi tam ekrana geçirir.
- Ekranın kapanmaması için: Geliştirici seçenekleri → "Uyanık kal (şarj olurken)".
