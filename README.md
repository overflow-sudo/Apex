# Apex

Windows bilgisayarını, masada duran eski bir Android telefondan yerel ağ üzerinden yöneten küçük bir web kumandası.
Telefonun tarayıcısı `http://BILGISAYAR_IP:8765` adresini açar; uygulama kurmaya gerek yoktur.

Tek dokunuşla "oyun / masaüstü / müzik" modları arasında geçer (hangi ekranlar açık, ana ekran, varsayılan ses çıkışı ve girişi,
Voicemeeter ayarı), o an ne olup bittiğini (çalan şarkı, açık oyun, kritik pil) büyük ve sade bir ekranda gösterir.

- **Sadece Python standart kütüphanesi.** `pip install` yok, derleme adımı yok, framework yok.
- **Eski telefonlar için.** Arayüz düz HTML/CSS/JS; eski Android Chrome'da çalışır, yatay ~780×360 ekrana göre tasarlandı.
- **Sade koyu tema.** Tesla ekranlarından esinlenen düz, kenarlıksız arayüz. Oyun açıkken vurgu rengi oyunun rengine döner.

> Program bilgisayarda **PC Kumanda** adıyla kurulur ve çalışır: kurulum klasörü `C:\PC_Kumanda`, zamanlanmış görev "PC Kumanda",
> güvenlik duvarı kuralı "PC Kumanda". Depodaki `apex` eklentisi ise ayrı bir şeydir (APEX FINANCE portföy ekranı).

## Özellikler

| Sekme / parça | Ne yapar |
|---|---|
| **Modlar** | Solda o anki durumu gösteren ana kart (çalan şarkı, açık oyun, kritik pil; boşta saat), sağda mod düğmeleri. Mod; ekranları, ana ekranı, Windows varsayılan ses aygıtlarını ve isteğe bağlı bir Voicemeeter ayarını uygular. Gamepad'e dokununca Oyun moduna kendiliğinden geçebilir. |
| **Ekran** | Tek bir monitörü açık bırak ya da hepsini aç. |
| **Ses** | Varsayılan çıkış ve girişi listeden seç. |
| **Sistem** | CPU / GPU / RAM / VRAM kullanımı, CPU ve GPU sıcaklığı, açık kalma süresi; fare / klavye / kulaklık pili. |
| **Tema** | Oyun temaları (otomatik ya da elle önizleme), duvar kağıdı, oyun efekti ve klavye ışığı anahtarları. |
| **Üst çubuk** | Saat, odak adası (o an en önemli durum), canlı maç skoru, yenile / tam ekran / güç (kapat, yeniden başlat, uyku; basılı tutarak). |
| **Şu an çalan** | Spotify, tarayıcıdaki YouTube, VLC vb. (Windows medya oturumu): kapak, ilerleme, önceki / oynat / sonraki. 90 sn dokunulmazsa "şu an çalıyor" ekranı. |
| **Oyun algılama** | Öndeki oyunu tanır (Steam, Epic, Xbox, Riot, Ubisoft, EA, GOG, Rockstar klasörleri); bilinmeyen oyunlar için logodan renk çıkarır. |
| **Bilgisayar kapalıyken** | Telefon "Bilgisayar kapalı ya da uykuda" ekranına geçer, bilgisayar açılınca kendiliğinden bağlanır. |
| **Klavye kısayolları** | Bilgisayar klavyesinden telefonun sekmesini değiştir: `Ctrl+Alt+Shift + 1–9` ve `← / →`. |
| **Eklentiler** | Kendi arayüzü olan büyük özellikler: Minecraft canlı haritası, Apple Music (EAMusic) kumandası, APEX portföy ekranı. |

## Gereksinimler

**Zorunlu**

| Ne | Not |
|---|---|
| Windows 10 / 11 (64 bit) | Ekran ve ses kontrolü Windows'a özgü. |
| Python 3.8 veya üstü, **tüm kullanıcılar için kurulu** | `Kur.bat` bulamazsa `winget` ile Python 3.12'yi tüm kullanıcılar için kurmayı teklif eder. Sadece senin hesabına kurulu Python (Microsoft Store ya da `C:\Users\...`) diğer kullanıcılarda çalışmaz. |
| Aynı yerel ağda bir telefon ya da tablet | Herhangi bir güncel ya da eski tarayıcı yeter; yatay tutmak için tasarlandı. |
| NirSoft **MultiMonitorTool** ve **SoundVolumeView** | Depoda proje kök klasöründe hazır gelir (ekranlar ve ses aygıtları bunlarla yönetilir). |

**İsteğe bağlı** — kurulu değilse ilgili parça boş ("—") görünür ya da kendini gizler, kumandanın geri kalanı çalışır.

| Özellik | Gereken | Ayar |
|---|---|---|
| CPU / GPU sıcaklığı | [LibreHardwareMonitor](https://github.com/LibreHardwareMonitor/LibreHardwareMonitor) | Options → Remote Web Server → Run (port 8085). "Run On Windows Startup" ve "Start Minimized" açık olsun. Adres `config.LHM_URL`. |
| Klavye ışığı oyun rengini takip etsin | Logitech G HUB + LIGHTSYNC klavye | G HUB'da "uygulamaların ışığı kontrol etmesine izin ver" açık olmalı. SDK DLL'i G HUB'ın kurduğu yerden bulunur; bulunamazsa proje klasörüne `LogitechLedEnginesWrapper.dll` (Logitech LED SDK, x64) koy. |
| Klavye / fare pili (Logitech) | Logitech G HUB açık | G HUB'ın yerel bağlantısı (`127.0.0.1:9010`) okunur. |
| Kulaklık / fare pili (HyperX, Attack Shark) | HyperX Cloud III S Wireless, Attack Shark (Xenta alıcısı) | Doğrudan HID ile okunur, sürücü gerekmez. Başka modeller için `modules/battery.py`'ye bak. |
| Mod değişince Voicemeeter ayarı | [Voicemeeter Potato](https://vb-audio.com/Voicemeeter/potato.htm) | Voicemeeter'da Menu → Save Settings ile kaydettiğin XML'i proje klasörüne koy, `config.PROFILES` içinde ilgili moda `"voicemeeter": "dosya.xml"` yaz. Depodaki `masaüstü-oyun.xml` ve `müzik.xml` yazarın kendi aygıtlarına göre; kendi ayarınla değiştir. |
| Şu an çalan medya | Windows PowerShell 5.1 (Windows'ta hazır gelir) | Ek bir şey gerekmez. |
| Maç skorları | İnternet bağlantısı (ESPN) | `config.FOOTBALL` (ligler, favori takımlar). |
| Oyun logoları ve otomatik oyun teması | İnternet bağlantısı | Logolar telefona doğrudan Steam / Wikimedia'dan yüklenir. |

## Kurulum

1. **İndir.** Depoyu klonla ya da "Code → Download ZIP" ile indirip bir klasöre çıkar (örn. `C:\Users\<sen>\Desktop\PC_Kumanda`).

   ```bash
   git clone https://github.com/overflow-sudo/Apex.git PC_Kumanda
   ```

2. **`Kur.bat`'ı çalıştır** (çift tıkla, yönetici izni ister). Sırayla şunları yapar:
   - Tüm kullanıcılar için kurulu Python'u bulur (yoksa kurmayı teklif eder).
   - Projeyi `C:\PC_Kumanda`'ya kopyalar ve `Users` grubuna yazma izni verir. Kumanda hep buradan çalışır; indirdiğin klasör geliştirme kopyası olarak kalır.
   - "PC Kumanda" adlı zamanlanmış görevi kurar: bu bilgisayarda **herhangi bir kullanıcı** oturum açınca kumanda konsol penceresi olmadan (`pythonw`) başlar.
   - Güvenlik duvarında 8765 numaralı TCP portunu **sadece yerel ağa** açar.
   - Kumandayı hemen başlatır ve telefonda açman gereken adresi yazar (`Telefondan ac: http://192.168.x.x:8765`).

3. **İlk kurulum sihirbazı.** İlk açılışta bilgisayarda tarayıcı kendiliğinden açılır. "Ayarlamaya başla"ya bas ve her mod için hangi ekranın,
   hangi ana ekranın ve hangi ses çıkışı / girişinin kullanılacağını seç. Aynı sihirbaz telefondaki Modlar sekmesinde de var,
   sonradan "Modları ayarla" ile tekrar açılır. Seçimler `C:\PC_Kumanda\yerel\bu_pc.json` dosyasına yazılır ve güncellemelerde silinmez.

4. **Telefonu hazırla.**
   - Chrome'da adresi aç → menü → **Ana ekrana ekle**. Böylece tam ekran ve yatay açılır (`web/manifest.json`).
   - Ekran kapanmasın: Geliştirici seçenekleri → **Uyanık kal (şarj olurken)**.
   - Bilgisayarın IP adresi değişirse telefondaki adres bozulur. Modem arayüzünden bilgisayara **DHCP rezervasyonu** (sabit IP) yapman önerilir.

### Güncelleme

Geliştirme kopyasında değişiklik yaptıktan (ya da `git pull` ettikten) sonra **`Kur.bat`'ı tekrar çalıştır.** Çalışan kumandayı durdurur,
dosyaları kopyalar ve yeniden başlatır. Telefondaki sayfa yeni sürümü görünce kendini yeniler. Kaynaktan silinen modül ve eklentiler
çalışan kopyadan da silinir; `yerel\` (aygıt seçimlerin) ve `cache\` korunur.

### Kaldırma

**`Kaldir.bat`** zamanlanmış görevi ve güvenlik duvarı kuralını kaldırır. Ardından `C:\PC_Kumanda` klasörünü silebilirsin.

### Elle çalıştırma (kurmadan denemek için)

```bash
python pc_kumanda.py
```

Konsola telefonda açılacak adresi yazar. Bu şekilde güvenlik duvarı kuralı eklenmez; Windows ilk seferde izin isteyebilir.

## Ayarlar (`config.py`)

| Ayar | Varsayılan | Açıklama |
|---|---|---|
| `PORT` | `8765` | Web sunucusunun portu. Değiştirirsen `Kur.bat`'ı tekrar çalıştır (güvenlik duvarı kuralı da güncellenir). |
| `PIN` | `""` | Boş değilse telefon ilk açılışta PIN sorar ve tarayıcıda saklar. |
| `AUTO_GAMEPAD` | `True` | Gamepad'e (XInput) dokununca Oyun moduna geç. |
| `POLL_SECONDS` | `8` | Arayüzün durumu yenileme aralığı (saniye). |
| `AUTO_RELOAD` | `True` | `.py` dosyaları değişince kumanda kendini yeniden başlatır. |
| `BATTERY_LOW` | `15` | Pil bu yüzdenin altına inince odak adasında uyarı. |
| `LHM_URL` | `http://127.0.0.1:8085/data.json` | LibreHardwareMonitor web sunucusu. |
| `PROFILES` | Oyun / Masaüstü / Müzik | Modların adı, ikonu, ekranları, ses aygıtları ve Voicemeeter dosyası. Aygıt adları "içinde geçiyor mu" diye aranır. Sihirbazda yaptığın seçimler bunların üstüne yazılır. |
| `THEME_FX` | `False` | Oyun açıkken hareketli arka plan efekti (Tema sekmesinden de açılır). |
| `KEYBOARD_LIGHTING`, `KEYBOARD_BRIGHTNESS`, `KEYBOARD_KEY_EFFECT`, `FPS_KEYS` | | Logitech klavye ışığı. |
| `GAME_THEMES`, `UNKNOWN_GAME_THEME` | | Oyun temaları: exe adları, renkler, logo, efekt. Listede olmayan oyunlar için tema otomatik üretilir. |
| `FOOTBALL` | Süper Lig + Şampiyonlar Ligi | Maç skorları; `favorites` ile favori takımın maçı öne çıkar. |
| `WALLPAPER`, `WALLPAPER_DIM` | `False`, `0.55` | Arka plan olarak masaüstü duvar kağıdı. |
| `MINECRAFT` | | Minecraft eklentisi: varsayılan seed, log yolu, yapılar. |

## Eklentiler

Kendi arayüzü olan büyük özellikler `eklentiler/<ad>/` klasöründe durur ve açılışta kendiliğinden yüklenir.
**Bir eklentiyi kapatmak için klasörünün adının başına `_` koy** (örn. `eklentiler/_apex`). Bozuk bir eklenti sadece kendini bozar.

| Eklenti | Ne yapar | Gereken |
|---|---|---|
| `minecraft` | Harita sekmesi (sadece oyun açıkken görünür): oyuncunun canlı konumu ve seed'den çizilen biyom / yapı haritası. | Minecraft Java 26.x + Fabric Loader. Köprü modu `eklentiler/minecraft/mod/pckumanda-bridge-1.0.2.jar`'ı Minecraft'ın `mods` klasörüne kopyala. Harita çizimi depodaki `native/mcmap.dll` ile yapılır ([cubiomes](https://github.com/Cubitect/cubiomes) üzerine; kaynağı `mcmap.c`). Ayrıntılar: `eklentiler/minecraft/NOTLAR.md`. |
| `applemusic` | Müzik sekmesi: çalma kontrolü, çalma listeleri, canlı spektrum. | Yazarın kendi Apple Music istemcisi **EAMusic** (`127.0.0.1:3000`). EAMusic yoksa sekme "kapalı" görünür; kullanmayacaksan eklentiyi kapat. |
| `apex` | Portföy sekmesi ve boşta tam ekran slaytlar (portföy özeti + sistem). | Yazarın kendi portföy uygulaması **APEX FINANCE** (Node.js, `127.0.0.1:8787`). Yoksa sadece sistem slaytı görünür; kullanmayacaksan eklentiyi kapat. |
| `_ornek` | Yeni eklenti için şablon (kapalı). | — |

Kendi eklentini yazmak için: [`eklentiler/EKLENTI_REHBERI.md`](eklentiler/EKLENTI_REHBERI.md).

## Güvenlik

- Kumanda sadece yerel ağ için tasarlandı. **Portu internete açma** (modemde port yönlendirme yapma).
- Varsayılan olarak PIN yok: aynı ağdaki herkes ekranları, sesi değiştirebilir ve bilgisayarı kapatabilir. Paylaşılan bir ağdaysan `config.PIN` ayarla.
- Güvenlik duvarı kuralı sadece yerel alt ağdan gelen bağlantılara izin verir.
- Resim gibi zararsız içerik sunan birkaç adres (kapak resmi, duvar kağıdı) PIN istemez. Bilgisayardaki programların kullandığı yerel adresler sadece `127.0.0.1`'den kabul edilir.

## Sorun giderme

- **Kayıtlar:** `%LOCALAPPDATA%\PC_Kumanda\kumanda.log`. Yavaş cevaplar "yavaş /api/ui", eklenti hataları "EKLENTİ HATASI" diye yazılır.
- **Telefon "Bilgisayar kapalı" diyor ama bilgisayar açık:** telefon ve bilgisayar aynı ağda mı, IP değişti mi (`ipconfig`), güvenlik duvarı kuralı var mı (`Kur.bat`'ı tekrar çalıştır)?
- **"Port kullanımda":** kumanda zaten çalışıyor; aynı anda iki kopya çalışmaz.
- **TV'nin HDMI sesi listede yok:** ekran kapalıyken Windows HDMI sesini göstermez; mod ekranı açtıktan sonra birkaç saniye bekleyip tekrar dener.
- **Sıcaklıklar "—":** LibreHardwareMonitor açık değil ya da web sunucusu kapalı.
- **Kapak resmi görünmüyor:** uygulama Windows'a kapak göndermiyor olabilir; log'da "medya" satırlarına bak.
- **Voicemeeter ayarı yüklenmiyor:** Voicemeeter kurulu mu, XML yolu `config.PROFILES` ile aynı mı? Log'da "Voicemeeter" satırlarına bak.

## Klasör yapısı

```
pc_kumanda.py          giriş noktası
config.py              ayarlar
core/                  sunucu, modül kayıt sistemi, ekran / ses / Voicemeeter / donanım yardımcıları
modules/               her .py dosyası bir özellik (sekme, durum etiketi, eylem); "_" ile başlayanlar yüklenmez
eklentiler/            kendi arayüzü olan büyük özellikler
web/                   telefonda açılan arayüz (index.html, style.css, app.js, manifest.json)
kurulum/               Kur.bat ve Kaldir.bat'ın çalıştırdığı PowerShell betikleri
notlar/                konu konu geliştirici notları (Türkçe)
Kur.bat, Kaldir.bat    kurulum / güncelleme ve kaldırma
*.exe                  NirSoft MultiMonitorTool ve SoundVolumeView
*.xml                  örnek Voicemeeter Potato ayarları
```

## Geliştirme

- Küçük bir özellik: `modules/_ornek.py`'yi kopyala. Sekmeler, düğmeler ve göstergeler Python'dan döndürülen basit sözlüklerle
  tanımlanır, arayüz kendini bunlara göre çizer; JavaScript yazmak gerekmez. Biçim ve API: [`CLAUDE.md`](CLAUDE.md).
- Kendi arayüzü olan özellik: eklenti olarak yaz ([`eklentiler/EKLENTI_REHBERI.md`](eklentiler/EKLENTI_REHBERI.md)).
- Kurallar: sadece standart kütüphane, Python 3.8 uyumu; web tarafında eski Android Chrome için `?.`, `??`, `replaceAll` ve CSS flex `gap` kullanılmaz.
- Bu proje büyük ölçüde [Claude Code](https://claude.com/claude-code) ile geliştirildi. `CLAUDE.md` ve `notlar/` hem insanlar hem de yapay zekâ için tutulan proje notlarıdır.

## Üçüncü taraf yazılımlar

- **MultiMonitorTool** ve **SoundVolumeView** — Nir Sofer, [nirsoft.net](https://www.nirsoft.net). Ücretsiz dağıtılabilen freeware; değiştirilmeden dahil edildi.
- **cubiomes** — Cubitect, MIT lisansı ([github.com/Cubitect/cubiomes](https://github.com/Cubitect/cubiomes)); `eklentiler/minecraft/native/mcmap.dll` içinde.
- Voicemeeter (VB-Audio), Logitech G HUB, LibreHardwareMonitor ve Minecraft / Fabric bu depoya dahil değildir; kendi sitelerinden kurulur.
