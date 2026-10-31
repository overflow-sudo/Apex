# Oyun algılama, oyun temaları, otomatik tema, logolar, Tema sekmesi

(CLAUDE.md'den taşındı, 2026-10-31. Genel kurallar CLAUDE.md'de.)

## Oyun temaları (`modules/games.py`, `core/procs.py`, `config.GAME_THEMES`)
- 3 sn'de bir algılama sırası: (1) öndeki pencerenin exe'si listede varsa o oyun, (2) öndeki süreç
  `steamapps\common\<Ad>`, `Epic Games\<Ad>` ya da `XboxGames\<Ad>` altındaysa `UNKNOWN_GAME_THEME` ve
  klasör adı, (3) listedeki bir oyun arka planda açıksa (alt-tab) o oyun, (4) hiçbiri yoksa siyah-beyaz.
  Oyun algılanmayınca tema 15 sn daha tutulur (`HOLD`). Valorant'ta titreme görüldüğü için eklendi.
- **Anti-cheat:** Oyun süreçleri AÇILMIYOR (OpenProcess yok). Adlar CreateToolhelp32Snapshot ile,
  öndeki PID GetWindowThreadProcessId ile alınıyor. Tam yol sadece listede olmayan öndeki süreç için soruluyor.
  Vanguard/BattlEye'li oyunlara dokunacak kod yazma.
- TFT, LoL ile aynı exe'yi kullanıyor (`League of Legends.exe`), bu yüzden LoL açılınca da TFT teması gelir.
- Tema `/api/ui` cevabında `theme` alanıyla gelir (`@extra("theme")`, hafif yenilemelerde de var).
  `app.js` → `applyTheme()` CSS değişkenlerini ayarlar, `body`'ye `fx-<ad>` sınıfı ekler. `--on-ac`
  kontrasta göre otomatik seçilir. PC kapanınca/uyuyunca tema siyah-beyaza döner.
- Efektler (`style.css`, `.fx` katmanı, sadece transform/opacity animasyonu): radar (Valorant, CS2),
  hex (TFT), tactical (R6, bilinmeyen oyunlar), glitch (Cyberpunk; logo yazısında RGB kayması), snow (Skyrim),
  dust (RDR2; sepya, film greni), road (ETS2). `config.THEME_FX = False` ise sadece renkler değişir.
- **Logolar** (Emir istedi): `GAME_THEMES[...]["logo"]` = `"steam:<appid>"` ya da resim adresi. Telefon logoyu
  doğrudan internetten yükler (PC'de indirme ya da önbellek yok). Steam: `cdn.cloudflare.steamstatic.com/steam/apps/<id>/logo.png`.
  Valorant ve TFT: Wikimedia `Special:FilePath`. Siyah Valorant logosu görünmüyor, pembe sürümü kullanılıyor.
  CS2 logosu çok koyu: `logo_white: True` → CSS filtresiyle beyaz. Listede olmayan Steam oyunlarında appid,
  `steamapps\appmanifest_*.acf` dosyasındaki `installdir` eşleşmesinden bulunur. Logo, Tema kartlarında ve
  arka planda %10 opaklıkta filigran (`#wm`) olarak görünür. Logo yüklenemezse karttaki ikon geri gelir.
- Tema sekmesi: Otomatik / Siyah-beyaz / her oyunun önizlemesi (`theme.set`). Seçim Otomatik'e dönene
  kadar sabit kalır, sunucu yeniden başlayınca sıfırlanır.
- Yeni oyun eklemek için `GAME_THEMES`'e bir satır ekle: exe adını Görev Yöneticisi → Ayrıntılar'dan al.
  **Ama genelde gerek yok**, aşağıdaki otomatik tema yeterli.

### Otomatik tema (`core/autotheme.py`, `core/pngcolor.py`)
- Öndeki süreç bir başlatıcı klasöründeyse (steamapps\common, Epic Games, XboxGames, Riot Games,
  Ubisoft…\games, EA Games, GOG Galaxy\Games, GOG Games, Rockstar Games, Amazon Games\Library) ve klasör adı
  başlatıcının kendisi değilse (`_NOT_GAMES`), oyun için bir kez tema üretilir:
  1. appid: Steam ise appmanifest'ten, değilse `store.steampowered.com/api/storesearch` ile addan (noktalama yok sayılır).
  2. Etiketler: `steamspy.com/api.php?request=appdetails&appid=` → `tags` (oy sırasıyla). Steam'in kendi
     "genres" bilgisi çok kaba olduğu için kullanılmıyor. `RULES` sırayla eşleşir: racing → road, fps/shooter → radar,
     tactical/military → tactical, sci-fi/cyberpunk → glitch, horror/survival/western → dust,
     strategy/moba/card → hex, rpg/fantasy/open world → snow. Tuş setleri `PRESETS`'te.
  3. Renk: Steam `logo.png` → saf Python PNG çözücü (zlib; 8 bit RGB/RGBA/gri/palet, interlace yok) → en yoğun doygun
     renk → `vivid()` → vurgu, `dark_bg()` → zemin. Gri logolarda kuralın varsayılan rengi kullanılır.
- Sonuç `C:\PC_Kumanda\cache\auto_themes.json`'a yazılır (anahtar `auto:<klasör>`). Kötü bir tema çıkarsa satırı
  silmek yeterli, bir sonraki açılışta yeniden hesaplanır. Log'a `config.GAME_THEMES`'e yapıştırılabilir bir satır yazılır.
- Hesaplanana kadar (ilk birkaç saniye) `UNKNOWN_GAME_THEME` kullanılır. Steam'de olmayan oyunlar (örn. Fortnite)
  adla ve genel temayla görünür.
- 2026-10-25'te senin ağından doğrulandı: storesearch, SteamSpy ve Steam logo CDN erişilebilir. Logolar 8 bit,
  renk tipi 6 (RGBA) ya da 4 (gri+alfa), interlace yok.
