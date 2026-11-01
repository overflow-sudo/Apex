# Apple Music eklentisi (`eklentiler/applemusic/`)

Emir'in kendi Apple Music istemcisi **EAMusic**'i (`C:\Users\emir\Desktop\EAMusic`, Node.js + MusicKit JS) telefondan yönetir.
Müzik sekmesi (order 32, her zaman görünür): solda kapak + şarkı + canlı spektrum + ilerleme + karışık/önceki/oynat/sonraki/tekrar + ses,
sağda çalma listeleri (dokun = çal, köşedeki karışık simgesi = karışık çal). EAMusic kapalıysa "EAMusic'i aç" düğmesi.

## Nasıl çalışıyor
```
Telefon ─POST /api/action applemusic.komut─▶ eklenti.py ─POST 127.0.0.1:3000/api/remote/command─▶ EAMusic sunucusu
                                                                         │ SSE (/api/remote/events)
EAMusic sayfası (Edge app penceresi, MusicKit) ◀──────────────────────────┘
EAMusic sayfası ─POST /api/remote/state (olay başına + 5 sn'de bir)─▶ sunucu ◀─GET /api/remote/state (1,5 sn)─ eklenti.py
```
- Köprü EAMusic tarafında: `remote.js` (sunucu) + `public/app.js` içindeki `remote` nesnesi (sayfa). Uçlar **yalnızca
  127.0.0.1**'den erişilebilir (403). Telefon EAMusic'e doğrudan bağlanmaz, her şey kumanda üzerinden geçer.
- `view()` hızlıdır: `@on_start` iş parçacığı durumu yoklar (EAMusic açıkken 1,5 sn, kapalıyken 5 sn), `view()` son değeri okur.
- `applemusic.komut` komutu gönderir, 0,35 sn bekler, durumu tazeler ve cevapta döndürür → telefon hemen güncellenir.
- "Aç": sunucu kapalıysa `node scripts/app-mode.js` (EAMusic klasöründe; sunucu + Edge `--app` penceresi). Sunucu açık ama
  pencere yoksa doğrudan Edge `--app` penceresi (aynı profil: `%APPDATA%\EAMusic\browser-profile`).
- Widget DOM'u bir kez kurulur; liste ancak çalma listesi kimlikleri değişince yeniden çizilir, kaydırma konumu korunur.
- İlerleme telefonda yerelde akar. PC/telefon saatleri farklı olabileceği için mutlak zaman değil, durumun yaşı (`age`, ms) kullanılır.

## Spektrum (2026-11-01)
Kapağın altında tek `<canvas>`'ta 32 ince, yuvarlak uçlu çubuk (`--ac`). Veri EAMusic'in kendi ses analizinden gelir
(WASAPI loopback ve Voicemeeter seviyeleri bilerek seçilmedi).
```
EAMusic sayfası (AnalyserNode) ─POST /api/remote/spectrum "12,40,..." (25/sn)─▶ EAMusic sunucusu
   ◀── SSE event 'spectrum' {on} (dinleyen var mı) ──┘      │ SSE GET /api/remote/spectrum (2 sn ping)
eklenti.py tek yukarı akış iş parçacığı ◀────────────────────┘ ──@stream /applemusic/spektrum──▶ telefon(lar)
```
- **EAMusic'te değişenler:** `remote.js`: `GET /spectrum` (kumanda için SSE, 2 sn ping), `POST /spectrum` (sayfadan düz metin kare,
  doğrulanır ve dinleyenlere dağıtılır), sayfaya `spectrum` {on} olayı (ilk dinleyen gelince / son dinleyen gidince / sayfa
  bağlanınca), `/log`'da `spectrumFrames`, `spectrumClients`. `server.js`: `/api/remote/spectrum` sıkıştırmadan hariç.
  `public/app.js`: `spectrum` nesnesi (Uzaktan kontrol bölümünün hemen üstü) + `remote.start()` içinde `spectrum` ve
  `playbackStateDidChange` dinleyicileri. Değişiklik öncesi yedek: bu oturumun scratchpad'inde `eamusic_yedek/` (geçici).
- **Sayfa:** MusicKit'in `<audio>` öğesi `createMediaElementSource → AnalyserNode (fft 2048) → hoparlör` ile bağlanır. 40 Hz–16 kHz
  logaritmik 32 bant, bant içi en büyük kutu, tize hafif eğim. Ölçek `m.volume`'a göre kaydırılır (kısık seste de çubuklar oynar).
  Sadece dinleyen varken **ve** çalarken `setInterval(40 ms)`; duraklayınca bir sıfır kare yollayıp durur. Önceki POST bitmeden
  yeni kare gitmez (kare atlanır). Öğe gölge DOM'da olsa da bulunsun diye `HTMLMediaElement.prototype.play` sarılıp son öğe tutulur.
- **Kumanda:** `_spektrum_yukari()` yalnızca en az bir telefon dinlerken EAMusic'e bağlanır (6 sn okuma zaman aşımı, kopunca 3 sn'de
  bir yeniden dener, kopunca telefona `""` yollar). Telefona olay: JSON metin `"12,40,..."`, `""` = veri yok, `0` = canlı tutma (5 sn).
- **Telefon:** akış yalnızca Müzik sekmesi açık + oynatıcı görünür + sayfa ön plandayken açık (`render`, `visibilitychange`).
  Çizim `requestAnimationFrame`; çıkış hızlı (0,35^n), iniş yavaş (0,94^n, ~1 sn). 400 ms kare gelmezse hedef 0 → söner.
  Hepsi sönünce döngü durur; boşta soluk noktalar kalır. Canvas boyutu sadece değişince ayarlanır.
- **Tuzak:** `createMediaElementSource` kalıcıdır ve AudioContext askıdayken öğenin sesi **kesilir**. Bu yüzden bağlama yalnızca bağlam
  `running` iken yapılır, askıya düşerse `resume()` edilir. app-mode.js Edge'i `--autoplay-policy=no-user-gesture-required` ile
  açtığı için bağlam hemen çalışır; kumandanın "Pencereyi aç" yolu (EDGE_BAYRAKLAR) da aynı bayrağı verir. Bayrak yoksa
  sayfada bir tıklama olana kadar spektrum gelmez ama müzik etkilenmez. Bağlama hata verirse spektrum o oturumda kapanır, müzik etkilenmez.
- Chromium, Widevine'li (EME) sesin Web Audio'dan geçmesine izin veriyor (`captureStream` ise EME'de reddediliyor).
- **Doğrulandı (2026-11-01):** gerçek EAMusic sunucu kodu (3010 portunda) + sahte sayfa + test kumandası (8766) ile uçtan uca:
  kareler telefona ulaşıyor, sekmeden çıkınca yukarı akış kapanıyor ve sayfa `on=false` alıp duruyor, duraklatınca çubuklar
  sönüyor, EAMusic kapalıyken sekme hatasız "EAMusic kapalı" gösteriyor, 780×360'ta taşma yok.
  Emir gerçek EAMusic'le (yeniden başlatıp Kur.bat sonrası) denedi: spektrum çalan şarkıyla oynuyor → Widevine'li ses Web Audio'dan
  geçiyor, müzik kesilmiyor.
  **Doğrulanmadı:** eski Android Chrome'da uzun süreli akıcılık/pil etkisi.

## EAMusic'e eklenen yeni bir özelliği kumandaya taşımak
Örnek: "şarkıyı beğen". Dört yer, sırayla:

| # | Dosya | Ne eklenir |
|---|---|---|
| 1 | EAMusic `public/app.js` | Özelliğin kendisi (örn. `loveSong()`), sonra `remote` nesnesinde: `handle()` → `case 'love': return loveSong();`. Telefonda bir durum gösterilecekse `snapshot()`'a alan ekle (örn. `loved: true`). |
| 2 | EAMusic `remote.js` | `COMMANDS` kümesine `'love'`. Yoksa sunucu "Bilinmeyen komut" der. |
| 3 | Kumanda `eklentiler/applemusic/web/applemusic.js` | `build()` içinde düğme: `iconBtn("", "ikon", "Beğen", function () { send("love"); })`. Durumu `update()` içinde `st.loved` ile çiz. Yeni ikon → dosyanın başındaki `P.icons({...})`. Parametre: `send("love", {id: "..."})` → sayfada `args.id`. |
| 4 | Kumanda `web/applemusic.css` | Gerekirse stil (`applemusic-` ön ekli sınıflar, tema değişkenleri). |

`eklenti.py`'ye dokunmak **gerekmez**: komutu ve `snapshot()` alanlarını olduğu gibi taşır. Sonra: EAMusic'i yeniden başlat,
Kur.bat'ı çalıştır. JS'te eski Android Chrome kuralları geçerli (`var`, `function`; `?.`, `=>`, `async` yok).

## Windows ile başlatma
Kumanda zaten oturum açılışında başladığı için EAMusic'i o başlatır (`otomatik_ac`, varsayılan açık): `@on_start` →
`otomatik_bekle` (20 sn) sonra EAMusic bağlı değilse `ac()` (küçültülmüş). **Oturum başına bir kez:** oturum kimliği
(explorer.exe başlama dakikası) `cache/applemusic/acilis.txt`'ye yazılır; kumanda gün içinde yeniden başlarsa (kod değişikliği,
Kur.bat) kimlik aynı olduğu için tekrar açmaz → kullanıcının kapattığı EAMusic geri gelmez. Sistem çalışma süresi
kullanılmıyor: Hızlı Başlangıç açıkken kapatmada sıfırlanmıyor. EAMusic klasörüne erişemeyen kullanıcıda otomatik açma yok.

## Ayarlar (`settings("APPLEMUSIC", ...)`)
`url` (varsayılan `http://127.0.0.1:3000`), `klasor` (EAMusic klasörü), `yenile` (yoklama sn), `kucuk_ac`, `otomatik_ac`,
`otomatik_bekle`. `config.py`'ye
`APPLEMUSIC = {...}` yazılırsa üstüne yazılır. EAMusic'in portu `.env` → `PORT` ile aynı olmalı.

## Durum
- Doğrulandı (2026-11-01): EAMusic köprüsü (komut sayfaya ~5 ms'de ulaşıyor, durum okuma, geçersiz komut reddi, SSE
  sıkıştırılmadan geliyor). Eklenti ayrı portta (8766) test kopyasıyla: sekme, kapalı/bağlı görünümler, eylemler (sahte EAMusic ile).
- Doğrulanmadı: gerçek telefonda dokunma, gerçek MusicKit oynatmasının kumandadan kontrolü, "Aç" düğmesinin pythonw altından
  pencere açması.

## Tuzaklar
- **"Pencere açık değil" (2026-11-01 hatası):** Edge, küçültülmüş/arka plandaki sayfanın zamanlayıcılarını ~5 dk sonra
  dakikada bire indiriyor. Bağlılık eskiden "son 15 sn'de durum geldi mi"ye bakıyordu → 5 dk sonra kopmuş görünüyordu.
  Şimdi: bağlı = açık SSE bağlantısı var (`remote.js`). Sayfa durumu `setTimeout` yerine mikro görevle gönderiyor; Edge
  `--disable-background-timer-throttling --disable-renderer-backgrounding --disable-backgrounding-occluded-windows` ile açılıyor
  (bayraklar sadece o profilde yeni Edge süreci başlarken geçerli).
- **Küçültülmüş açma:** Edge'in güvenilir bir "küçük başlat" bayrağı yok. "Aç" sonrası bir iş parçacığı başlığı
  `EAMusic` ile biten yeni `Chrome_WidgetWin_1` penceresini arar ve `ShowWindow(SW_MINIMIZE)` yapar (`kucuk_ac` ayarı).
- **Küçültülmüşken çalmıyordu (2026-11-01):** Chromium, hiç görünür olmamış sayfanın medyasını pencere gösterilene kadar
  erteliyor. Pencere hemen küçültülünce müzik ancak pencere açılınca başlıyordu. Şimdi küçültme, sayfa köprüye bağlanana
  kadar (+1 sn) bekliyor → pencere açılışta ~1-3 sn görünür. Ek bayrak: `--disable-background-media-suspend`.
- **Küçültülmüşken şarkı adı/kapak güncellenmiyordu (2026-11-01):** müzik çalıyordu ama sayfanın durum bildirimi (zamanlayıcı
  ve MusicKit olayları) kısılıyordu. Şimdi EAMusic sunucusu, kumanda `/api/remote/state` sorduğunda sayfaya SSE ile `sync`
  olayı yollar (saniyede en fazla 1); sayfa anında durumunu gönderir. Ağ olayları kısılmaz. Komut bitince de durum hemen gider.
  Sonuç: durum en fazla bir yoklama (~1,5 sn) geriden gelir.
- EAMusic tarafında `compression` SSE'yi tamponluyordu (komutlar sayfaya hiç ulaşmıyordu). `server.js`'te
  `/api/remote/events` sıkıştırmadan hariç; filtrede `req.originalUrl` kullanılmalı (`req.path` alt yönlendiricide `/events` olur).
- Tam şarkı çalmak için EAMusic Edge/Chrome'da çalışmalı (Widevine). Electron sürümü castlabs EVS imzası olmadan `MEDIA_LICENSE` verir.
- Mevcut medya modülü (SMTC) EAMusic'i de "Edge" olarak üst çubukta gösterebilir; bu eklentiyle çakışmaz.
