# PC Kumanda — proje notları (Claude için)

Emir'in Windows masaüstü bilgisayarını, masada yatay duran eski bir Android telefondan yerel ağ
üzerinden yöneten küçük bir web kumandası. Telefon tarayıcısı `http://PC_IP:8765` adresini açar.

**İki konum var, karıştırma:**
- **Geliştirme kopyası:** `C:\Users\emir\Desktop\PC_Kumanda`. Claude oturumuna bağlı klasör bu; düzenlemeleri burada yap.
- **Çalışan kopya:** `C:\PC_Kumanda`. `Kur.bat` geliştirme kopyasını buraya aktarır. Tüm kullanıcılar buradan
  `pythonw` ile çalıştırır. Düzenlemeden sonra kullanıcıya **"Kur.bat'ı tekrar çalıştır"** de; bu, çalışan
  örnekleri durdurur, dosyaları kopyalar ve yeniden başlatır.

**Kurallar**
- Sadece Python standart kütüphanesi kullanılır, pip paketi yok. Python 3.8+ ile uyumlu kalmalı.
- Windows'u sadece NirSoft araçlarıyla kontrol ediyoruz: `MultiMonitorTool.exe` (ekranlar) ve
  `SoundVolumeView.exe` (ses aygıtları). İkisi de proje kök klasöründe durur.
- Web tarafında derleme adımı ve framework yok: düz `web/*.html/css/js`.
- Hedef cihaz eski bir Android telefonun Chrome'u. JS'te `?.`, `??`, `replaceAll` ve özel sınıf
  alanları gibi yeni şeyler kullanma. CSS'te flex `gap` yerine margin ya da grid-gap kullan.
- Arayüz metinleri Türkçe. Büyük harfe çevirmeyi CSS `text-transform` ile yap (`<html lang="tr">`
  sayesinde İ/I doğru çıkar). Python'da `.upper()` kullanma, "MÜZIK" gibi yanlış sonuç verir.
- Varsayılan tema sade koyu tema (Tesla ekranı gibi, 2026-10-31): düz koyu zemin (`#0b0b0c`), kenarlıksız yuvarlak
  kartlar, normal yazı (büyük harf ve mono yok), ray sadece ikon, bol boşluk. Köşe braketi, tarama çizgisi, kart numarası
  ekleme. Aktif öğe vurgu rengiyle dolar. Oyun açıkken sadece vurgu rengi değişir, zemin koyu kalır; hareketli efektler
  (`THEME_FX`) ve duvar kağıdı (`WALLPAPER`) varsayılan kapalı (`notlar/tema.md`, `notlar/arayuz.md`).
  CSS'te sabit renk yazma: `--ac` (vurgu), `--on-ac`, `--ac2`, `--bg`, `--fg`, `--panel`, `--panel2`, `--line`, `--warn`, `--r` kullan.
- İngilizce metinler (oyun adları) CSS ile büyük harfe çevriliyorsa `lang="en"` ver (item `"lang": "en"`,
  status `{"text","value","lang"}`) ya da Python'da `.upper()` yap. Yoksa Türkçe kural "SKYRİM" üretir.

## Klasör yapısı

```
pc_kumanda.py        giriş noktası: modülleri yükler, sunucuyu başlatır
config.py            PORT, PIN, POLL_SECONDS, AUTO_GAMEPAD, PROFILES
core/
  system.py          run(), read_csv(), norm()/match(), @cached(ttl), invalidate(), araç yolları
  state.py           lock (RLock) + mode
  plugin.py          eklenti yardımcıları: settings(ad, varsayılanlar), data_dir(eklenti)
  local.py           bu PC'ye özel ayarlar (yerel/bu_pc.json): profiles(), label(), get/put
  display.py         list_monitors(), find(), apply(keys, primary), only(), enable_all()
  audio.py           list_devices(dir), set_default(id), set_by_key(key, dir, wait), current(dir)
  registry.py        @tab, @action, @status, @on_start, @on_stop, load_modules(), ui(), call()
  reloader.py        .py değişince kendini yeniden başlatır
  server.py          HTTP: GET / ve web dosyaları, GET /api/ui, POST /api/action
modules/             her .py dosyası bir özellik. _ ile başlayanlar yüklenmez
  modes.py           Modlar sekmesi + gamepad izleyici
  wizard.py          modları bu PC'nin aygıtlarına göre ayarlama sihirbazı (Modlar sekmesinde açılır)
  screens.py         Ekran sekmesi
  sound.py           Ses sekmesi (çıkış/giriş listeleri) + üst çubuktaki durum etiketleri
  power.py           PC'yi kapat / yeniden başlat / uyku (power.* eylemleri)
  hotkeys.py         PC klavyesinden telefonun sekmesini değiştirme (Ctrl+Alt+Shift + 1-9 / ok tuşları)
  battery.py         Sistem sekmesinin altında fare/klavye/kulaklık pil kartları + üst çubukta kritik pil uyarısı
  _ornek.py          yeni modül için şablon
eklentiler/          kendi arayüzü olan büyük özellikler (rehber: eklentiler/EKLENTI_REHBERI.md)
  EKLENTI_REHBERI.md eklenti API'si ve kuralları — yeni oturumda eklenti yazdırırken bunu ver
  _ornek/            şablon eklenti (kapalı): eklenti.py + web/ornek.js + web/ornek.css
  minecraft/         canlı konum + seed haritası: eklenti.py, web/harita.js|css, native/ (DLL), mod/ (Fabric), NOTLAR.md
web/                 index.html, style.css, app.js (genel çizici), manifest.json
  system.py          Sistem sekmesi (CPU/GPU/RAM/VRAM/sıcaklık), 2 sn'de bir ölçen iş parçacığı
core/winstats.py     ctypes: GlobalMemoryStatusEx, GetTickCount64, PDH sayaçları; winreg: CPU/GPU adı, VRAM boyutu
core/hid.py          ctypes HID: find(vid, pid, usage_page) → Device.write/read (zaman aşımlı)
core/ghub.py         G HUB yerel websocket (127.0.0.1:9010) istemcisi, batteries()
core/hwmon.py        LibreHardwareMonitor web sunucusundan (127.0.0.1:8085/data.json) CPU/GPU sıcaklığı
Kur.bat              kur/güncelle: yönetici olarak kurulum/kur.ps1'i çalıştırır, sonra bu oturum için başlatır
Kaldir.bat           görevi + güvenlik duvarı kuralını kaldırır (kurulum/kaldir.ps1)
kurulum/kur.ps1      Python kontrolü, C:\PC_Kumanda'ya robocopy, Users izni, zamanlanmış görev, güvenlik duvarı
yerel/bu_pc.json     SADECE çalışan kopyada: bu PC'nin mod aygıt seçimleri + DISPLAYn -> ekran adı (core/local.py)
aygit_listesi.bat    aygıt CSV dökümü
pc_kumanda_eski.py   ilk tek dosyalık sürüm (yedek, kullanılmıyor)
```

## Yeni özellik nasıl eklenir

Kendi JS/CSS'i gerekmeyen küçük bir özellik → `modules/` (aşağıdaki adımlar). Kendi arayüzü (özel widget, harita,
oyun paneli…) olan ya da ayrı bir oturumda geliştirilecek özellik → `eklentiler/<ad>/` (`eklentiler/EKLENTI_REHBERI.md`).


1. `modules/_ornek.py` dosyasını `modules/<ad>.py` olarak kopyala.
2. Yeni sekme açmadan mevcut bir sekmeye bölüm eklemek için `@section("sekme_id", order)` kullan.
   Ray dikeyde en fazla 5 sekme alıyor (360 px), 6. sekme taşar.
2b. `@tab(id, başlık, icon, order, poll=None)` ile bir `view()` yaz. Bu fonksiyon section listesi döndürür.
   `poll=2` verilirse o sekme açıkken arayüz 2 saniyede bir yenilenir. Yavaş ölçümleri `view()` içinde
   yapma: `@on_start` ile bir iş parçacığında ölç, `view()` sadece son değeri okusun (system.py'deki gibi).
3. Her düğme için `@action("ad.eylem")` ekle. Parametreler `**params` olarak gelir.
   `registry.call` eylemi zaten `state.lock` altında çalıştırır ve sonra önbelleği temizler.
4. İstersen üst çubuk için `@status(order)` ekle (kısa metin ya da None döndürür), arka plan işleri
   için `@on_start` ekle.
5. Yeni ikon gerekiyorsa `web/app.js` → `ICONS` içine 24×24 çizgi SVG içeriği ekle.
6. JS'e dokunmaya gerek yok: arayüz `/api/ui`'den gelen tanıma göre kendini çizer.

### Section / widget biçimi

```jsonc
{ "type": "tiles",   "title": "?", "fill": true,   // büyük kartlar, fill = kalan yüksekliği doldur
  "items": [{ "title", "sub", "icon", "active", "lines": [["ANAHTAR","değer"]], "action", "params" }] }
{ "type": "list",    "title": "?", "items": [{ "title", "sub", "icon", "active", "action", "params" }] }
{ "type": "buttons", "title": "?", "items": [{ "title", "icon", "action", "params", "on": true|false }] }  // "on" = aç/kapa anahtarı
{ "type": "stats",   "title": "?", "fill": true,   // gösterge kartı: büyük sayı + segmentli çubuk; "compact": true = tek satır küçük kartlar
  "items": [{ "label", "value", "unit", "pct": 0-100|null, "hot": bool, "sub" }] }
{ "type": "text",    "title": "?", "text": "..." }
{ "type": "hero",    "fill": true, "mode": "Masaüstü modu" }  // ana kart: focus listesinin başı büyük, boşta saat + tarih
// tiles + "layout": "stack" = tek sütun geniş düğmeler; herhangi bir section + "side": true = öncekinin sağına yerleşir
```
Art arda gelen `list` section'ları yan yana sütunlara yerleşir. 4'ten fazla kart olursa küçük kart
düzenine geçilir. Mevcut ikonlar: bolt, gamepad, desktop, music, monitor, volume, headphones,
speaker, mic, power, full, refresh, chip, temp, palette, keyboard, close, battery.
Kart öğesine `"img": url` (ve `"img_white": true`) verilirse ikon yerine resim gösterilir.

### API
- `GET /api/ui?tab=<id>[&light=1]` → `{tabs:[{id,title,icon,poll,sections}], status:[str], tab, poll}`.
  Sadece istenen sekmenin `sections` alanı doldurulur, diğerleri null gelir. Böylece arka planda gereksiz
  yere MMT/SVV çalışmaz. `light=1` sadece o sekmeyi döndürür, durum etiketlerini atlar (hızlı yenileme için).
- `POST /api/action` `{name, params}` → `{ok, result}` ya da `{ok:false, error}`
- PIN ayarlıysa her istekte `X-Pin` başlığı gönderilir. Arayüz 401 alırsa PIN'i sorar ve tarayıcıda saklar.

## Eklentiler (`eklentiler/`)
- Büyük, kendi arayüzü olan özellikler `eklentiler/<ad>/` klasöründe durur: `eklenti.py` (modules/ ile aynı dekoratörler),
  `web/*.js|*.css` (index.html'e kendiliğinden eklenir, sadece `window.PCK` API'sini kullanır), `NOTLAR.md` (o eklentinin notları).
  **Yeni eklenti yazarken ya da bir eklentide çalışırken önce `eklentiler/EKLENTI_REHBERI.md`'yi oku.** Şablon: `eklentiler/_ornek/`.
- Klasör adı `_` ile başlarsa eklenti kapalı. Bozuk bir eklenti (Python hatası, JS hatası) sadece kendini bozar; log'da
  "EKLENTİ HATASI", arayüzde "Bu bölüm çizilemedi". Aynı sekme kimliği iki kez kaydedilirse ikincisi yok sayılır ("UYARI").
- Kur.bat kaynaktan kaldırılan eklenti klasörlerini ve `modules/*.py` dosyalarını çalışan kopyadan siler (iki kez yüklenmesin diye).
- **Minecraft haritası** (`eklentiler/minecraft/`): ayrıntılar `eklentiler/minecraft/NOTLAR.md`. Kısaca: Fabric köprü modu
  konumu 10 Hz gönderir, cubiomes DLL karoları çizer, Harita sekmesi sadece oyun açıkken görünür.
- Odak adası: `@focus(priority)` fn() → `{kind, title, sub, img, badge, live, alert, tab|panel}` ya da None (`notlar/arayuz.md`).
- Yeni kancalar: `@stream(path)` fn(q, send) (SSE, `send(text)`), `@post(path)` (sadece 127.0.0.1, PIN yok), `@route(path)` artık `fn(q)` alır,
  `@tab(..., visible=fn)`, `games.detector`.

## Bilinen tuzaklar

- **HDMI sesi geç beliriyor:** Smart M70F'nin ses çıkışı, ekran kapalıyken listede görünmez.
  Ekran açıldıktan birkaç saniye sonra belirir. `set_by_key(..., wait=12)` bu yüzden tekrar dener.
- **Ana ekran kapatılamaz:** Windows ana ekranın kapatılmasına izin vermez. Sıra her zaman şöyle olmalı:
  önce aç → sonra `/SetPrimary` → en son diğerlerini `/disable` (`display.apply`).
- **HDMI ön eki değişebilir:** Ses çıkışı adlarının başındaki "4 - " gibi numaralar değişebilir.
  Eşleştirmede hep "Smart M70F" gibi ad parçası kullan. Arayüzde bu ön ek `_clean()` ile gizleniyor.
- **Çift boşluk:** Aygıt adı `USB AUDIO  CODEC` iki boşluk içeriyor. `norm()` bunu tek boşluğa indiriyor.
- **DISPLAY numaraları:** Kablo ya da port değişirse DISPLAY1/2 numaraları değişebilir.
  Bu yüzden ekranlar numarayla değil adla eşleştiriliyor.
- **Önbellek ("bayat ama hızlı"):** NirSoft araçları normalde yüzlerce ms, oyun sırasında saniyeler
  sürebiliyor. `@cached(ttl=2, max_stale=30)`: süresi dolan değer hemen döner, yenisi arka planda
  hesaplanır. `/api/ui` bu yüzden ~20–50 ms'de cevap verir. `invalidate()` (her eylemden sonra) önbelleği
  boşaltır, sonraki çağrı taze değeri bekler. Açılışta `modes.warm_cache()` önbelleği doldurur.
  **Bunu geri alma:** eskiden Modlar sekmesi iki aracı arka arkaya bekliyordu, oyun sırasında 5 sn'yi
  geçip telefonu "kapalı" ekranına düşürüyordu (2026-10-25 hatası).
- `/api/ui` 1,5 sn'yi geçerse log'a "yavaş /api/ui" yazılır. Log satırları `core.system.log()` ile zaman damgalı.
- Telefonun vazgeçtiği istekler BrokenPipe/ConnectionAborted verir. Bunlar susturuluyor (`Server.handle_error`).
- **Arka plan programları:** Uygulama açacak bir eylemde `subprocess.Popen` kullan. `run()` beklediği
  için sunucuyu kilitler.
- **Test:** Linux'ta `core.system.read_csv/run` yerine sahte fonksiyonlar koyup gerçek CSV dökümleriyle
  sunucu çalıştırılabilir. Arayüzü 780×360 yatay boyutta Playwright ile görsel olarak kontrol et.

## Koruma ve geri alma
- Proje bir git deposu (2026-10-31, dal `main`). Yeni bir işe başlamadan `git status` temiz olmalı; bir şey bozulursa
  `git restore <dosya>` / `git checkout -- .` ile son kayda dönülür. Commit'i kullanıcı isteyince at.
- `.claude/settings.json`: `core/`, `web/`, `modules/`, `kurulum/`, `config.py`, `pc_kumanda.py`, `Kur.bat`, `Kaldir.bat`
  düzenlemesi her seferinde kullanıcı onayı ister. Eklenti oturumunda bu onay çıkıyorsa yanlış yerdesin demektir.

## Konu notları (`notlar/`) — sadece o konuda çalışırken oku

| Dosya | İçerik |
|---|---|
| `notlar/modlar.md` | Donanım, ses/ekran aygıt adları, modlar, kurulum sihirbazı, bu PC'ye özel ayarlar |
| `notlar/tema.md` | Oyun algılama, oyun temaları, otomatik tema, logolar, Tema sekmesi |
| `notlar/isik.md` | Logitech G915 klavye ışığı (LED SDK) |
| `notlar/mac.md` | Maç skorları (ESPN) |
| `notlar/medya.md` | Şu an çalan medya (SMTC, PowerShell) |
| `notlar/arayuz.md` | Duvar kağıdı, masaüstü tarayıcı, klavye kısayolları, güç paneli, bağlantı kopunca/uyku, telefon kurulumu |
| `notlar/kurulum.md` | Kur.bat, otomatik başlatma, tek örnek, otomatik yeniden başlatma, log |
| `notlar/pil.md` | Fare/klavye/kulaklık pili (Attack Shark, G HUB, HyperX HID) |
| `notlar/sistem.md` | Sistem paneli (CPU/GPU/RAM/VRAM/sıcaklık, PDH, LHM) |
| `notlar/gecmis.md` | Değişiklik geçmişi ve henüz yapılmamış fikirler |
| `eklentiler/EKLENTI_REHBERI.md` | Eklenti yazma kuralları ve API (eklenti oturumunda sadece bunu + o eklentinin klasörünü oku) |
| `eklentiler/<ad>/NOTLAR.md` | O eklentinin notları (örn. Minecraft haritası) |

Bir konuda yeni bir şey öğrenince ilgili `notlar/` dosyasına yaz; CLAUDE.md'ye sadece her oturumda gereken kurallar girer.
Değişiklik geçmişine `notlar/gecmis.md` dosyasının başına bir satır ekle.
