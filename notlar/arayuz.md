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

## Odak arayüzü (`@focus`, `renderFocus()` app.js) — 2026-10-31
- Felsefe: ekran her şeyi aynı anda göstermez, o an aktif olana odaklanır. Python tarafı `@focus(priority)` ile
  öğe verir (`core/registry.py`, `/api/ui` → `focus` listesi, hafif yenilemelerde de var, önceliğe göre sıralı).
  Şu an: kritik pil 90 (`battery.py`, dokununca Sistem), oyun 70 (`games.py`, logo), çalan şarkı 50 / duraklatılmış 15
  (`media.py`, dokununca medya paneli, adada oynat/duraklat).
- Üst çubukta `#focus` (.island): en öndeki öğe büyük, diğerleri sağında küçük rozet (ayrı ayrı dokunulabilir).
  Öğe değişince içerik kayarak girer (`.swap`), ada max-width geçişiyle açılıp kapanır.
- Öncelik >= 30 → `body.focus`: "PC//KUMANDA" yazısı çekilir, sadece ilk durum etiketi (mod) kalır. Duraklatılmış
  şarkı (15) odak sayılmaz, ada küçük kalır. `@status` dict'i `kind` verirse ve o kind adadaysa etiket çizilmez
  (Oynuyor etiketi, ilk etiketin vurgu rengini kapmasın diye filtre JS'te, gizleme değil).
- Eski `#media` ve `#batt` kutuları kaldırıldı. `@extra("battery")` ve `@extra("media")` duruyor (panel ve eklentiler için).
- Gruplar: aktif öğesi olan tiles/list `.has-on` alır, diğer öğeler %55 opaklık (dokununca/hover'da netleşir).
  Yeni aktif olan öğe `.lit` ile yumuşakça dolar (önceki çizimle `sekme|başlık` karşılaştırması, `onCls()`).
- Geçişler: sekme değişiminde eski içerik soluklaşır (`.main.leaving`, "YÜKLENİYOR" yanıp sönmesi yok), yenisi
  `.main.enter` ile kayarak gelir. Medya/maç/güç panelleri display yerine opacity+visibility ile solar.
  Hepsi `prefers-reduced-motion`'da kapanır. Sadece opacity/transform animasyonu (eski telefon).
- Ambient: `IDLE_MS` (90 sn) dokunulmazsa ve en öndeki odak çalan şarkıysa medya paneli kendiliğinden açılır
  (`.mpanel.ambient`). Oyun ya da kritik pil öne geçerse ya da şarkı durursa kendiliğinden kapanır.
- Test: `focus_test.py` benzeri betik — `procs.IS_WIN=False`, `media.current`/`games._auto`/`battery.latest` sahte,
  127.0.0.1'de ayrı portta sunucu; 780×360'ta tarayıcı panosunda doğrulandı.

## Sade tema (Tesla tarzı) — 2026-10-31, 1. adım
- Emir'in isteği: Tesla ekranları kadar sade, ama hiçbir işlev kaybolmadan. Ekranda tek bir ana şey, gerisi ikon ve boşluk.
- `style.css` baştan yazıldı. Değişkenler: `--bg #0b0b0c`, `--panel #18181a` (kart), `--panel2 #232326` (basılı/seçili satır),
  `--dim`, `--mute`, `--warn #ff6b5e` (kritik pil, sıcak gösterge, Kapat), `--r` köşe. Eklentiler `--line-hi`, `--mono`, `--dim`
  kullandığı için bu adlar duruyor. Oyun efektleri (`.fx-*`) ve kapalı ekranındaki gözler aynen korundu.
- Ray sadece ikon (sekme adı `title`'da), seçili ikon yuvarlak zeminli ve vurgu renginde. Üst çubukta marka yok, saat solda,
  durum etiketleri kutusuz düz metin (· ile ayrılır). Kart numaraları ve "● AKTİF" etiketi gizli. Göstergeler ince düz çubuk.
- Oyun teması: `applyTheme` sadece `--ac/--ac2/--on-ac` ayarlar, oyunun `bg/fg`'si kullanılmaz. Filigran logo (`#wm`) gizli.
- `config.THEME_FX = False`, `config.WALLPAPER = False` (ikisi de açılabilir; duvar kağıdı Tema sekmesinden).
- Arayüz yazıları cümle düzeninde ("Uygulanıyor…", "Bilgisayar kapalı ya da uykuda"). Yeni metni BÜYÜK yazma.
- Sistem kartları 780×360'ta sığsın diye sayı 28 px, dolgu 9 px (2 sıra + pil satırı).

## Sade tema 2. adım — Modlar ana ekranı (2026-10-31)
- `modules/modes.py` view: `{"type": "hero", "mode": "<mod> modu"}` + mod tiles'ı `layout: "stack", side: true` + "Modları ayarla".
- `hero` widget'ı (app.js `drawHero`): `focusList[0]`'ı büyük gösterir. Medya: kapak, ad, ilerleme çubuğu (`tickMedia`),
  önceki/oynat/sonraki; kapağa dokununca medya paneli. Oyun: logo + ad + "Oynuyor" (vurgu renginde). Kritik pil: kırmızı ikon
  + ad, dokununca Sistem. Boşta: büyük saat (`tick()` günceller), Türkçe tarih, mod adı. Diğer odak öğeleri sağ üstte rozet.
  Odak değişince sayfa yeniden çizilmeden `refreshHero()` ile güncellenir (anahtar değişmezse dokunmaz, titreme yok).
- `side: true`: renderMain bölümü bir öncekiyle `.duo` (1.3fr / 1fr) içine alır; dikeyde alt alta.
- Ana kart ekrandayken (`body.has-hero`) üst çubuktaki odak adası gizlenir, aynı şey iki kez görünmesin.
- Mod kartındaki EKRAN/ÇIKIŞ/GİRİŞ satırları (`lines`) stack düzeninde gizli; ayrıntı "Modları ayarla" sihirbazında.

## Sade tema 3. adım — diğer sekmeler (2026-10-31)
- `buttons` öğesine `"on": true/false` verilirse aç/kapa anahtarı çizilir (`.btn.tg`, `.sw`); yazıya "· Açık" ekleme.
  Tema sekmesinde tek satır: Oyun efekti (`theme.fx`, `games._fx`, başlangıç `config.THEME_FX`), Duvar kağıdı, Klavye ışığı.
  Ayarlar sunucu yeniden başlayınca config değerine döner. `.brow` düğmeleri alttan hizalı (başlıklı/başlıksız karışık olabilir).
- Tema: başlık "Şu an · <oyun>" (`.upper()` yok), "Siyah-beyaz" seçeneğinin adı artık "Sade".
- Birden çok kart aktifse (`hasOn` → `multi`, örn. iki ekran açık) seçim değil durumdur: kart dolmaz, ikon vurgu renginde.
- Sistem kartı: etiket solda, ayrıntı (CPU adı, sıcaklık) aynı satırda sağda, altta 32 px sayı + çubuk. 780×360'ta 2 sıra + pil satırı sığıyor.
- Ekran alt yazısı "ana ekran" / "kapalı", sıcaklık kartları "CPU sıcaklığı" / "GPU sıcaklığı", başlık "Açık kalma süresi".
- Görsel kontrol: tarayıcı panosu daralırsa 780×360 küçülerek gösterilir ve emülasyon sıfırlanır; ölçüm için
  `scrollHeight - clientHeight` ile taşma kontrolü yap, ekran görüntüsünü pano genişken al.
