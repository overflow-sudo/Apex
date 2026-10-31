# Minecraft canlı konum + seed haritası — eklenti notları

Dosyalar (hepsi `eklentiler/minecraft/` altında): `eklenti.py` (sunucu), `web/harita.js` + `web/harita.css` ("mcmap" widget'ı),
`native/` (cubiomes DLL + `mcmap.c`), `mod/` (Fabric köprü modu: kaynak + jar'lar). Ayarlar `config.MINECRAFT`.
Önbellek çekirdeğin `cache/` klasöründe kalır (`mc_seeds.json`, `mc_targets.json`, `mc_waypoints.json`, `mc2/`).
2026-10-31'de `modules/minecraft.py`'den eklentiye taşındı. Çekirdekle sadece `window.PCK` üzerinden konuşur
(olaylar: render → akışı kapat, resize → yeniden çiz, close → paneller, key → +/- zum). Genel kurallar: `../EKLENTI_REHBERI.md`.

- Emir: Minecraft **Java 26.3**, Fabric Loader 0.19.5, Iris + Sodium. Oyun Türkçe. Kullanıcı adı Themiskyra.
  Iris profili modları `%APPDATA%\.minecraft\iris-reserved\26.3\` klasöründen yüklüyor (`-Dfabric.modsFolder`).
  Ana dünya bir Realm, seed `271664881382654292` (`config.MINECRAFT["default_seed"]`).
- **Mod (PC Kumanda Bridge, `mod/`):** 26.x'te Mojang obfuscation'ı kaldırdı, bu yüzden Mojang adlarına
  yansıma ile erişiliyor ve Minecraft'a derleme anında bağımlılık yok. Gradle/Loom gerekmedi (bu ortamdan Fabric
  ve Mojang maven'larına erişim yok). Derleme: `javac --release 21` (stub `ClientModInitializer` ile) → jar.
  Adlar 26.3 jar'ında javap ile doğrulandı: `Minecraft.getInstance/player/getConnection/getCurrentServer/
  hasSingleplayerServer/getSingleplayerServer/submit(Supplier)`, `Entity.getX/getY/getZ/getYRot/level`,
  `Level.dimension`, `ResourceKey.identifier` (26.x'te `location()` değil!), `ServerData.isRealm/name/ip`,
  `ClientPacketListener.sendCommand`, `MinecraftServer.overworld/getWorldData`, `ServerLevel.getSeed`,
  `WorldData.getLevelName`.
  Mod 1.0.2'den beri saniyede 10 kez `POST http://127.0.0.1:8765/api/mc` gönderir. 1.0.1'den beri `gameDir` (Minecraft.gameDirectory)
  de gönderiyor; kumanda `latest.log`'u `<gameDir>\\logs\\` altından okuyor (CurseForge/Prism instance'ları için şart). Cevapta `need_seed:true` gelirse oturumda bir
  kez `/seed` çalıştırır. Kumanda kapalıyken giderek seyreltir (en fazla 10 sn'de bir).
  Kurulu jar'lar (aynı mod id iki kez olmasın diye yeni sürüm ESKİ dosya adlarının üzerine yazılır):
  `curseforge\minecraft\Instances\Horizon\mods\pckumanda-bridge-1.0.1.jar`, `.minecraft\iris-reserved\26.3\pckumanda-bridge-1.0.0.jar`.
- **Seed:** tek oyunculuda moddan doğrudan gelir. Realm/sunucuda her yeni oturumda `/seed` cevabı
  `latest.log`'daki `[CHAT] ... [<sayı>]` satırından okunur (Türkçe "Tohum: [..]" dahil, dil bağımsız).
  Elle `/seed` yazılırsa da yakalanır. `cache/mc_seeds.json`'da dünya anahtarına (`realm:<ad>`) göre saklanır,
  yoksa `default_seed` kullanılır. Yetki yoksa (başkasının Realm'i) varsayılana düşer.
- **Harita:** cubiomes (Cubitect/cubiomes, MC_NEWEST = 1.21 Winter Drop; 26.x için ayrı seçenek yok, aynı
  dünya üretimi varsayılıyor — bilinen bir köyle doğrulanmalı: spawn yakınında köy (-144, 288) olmalı).
  `native/mcmap.c` ince katman: `mcmap_tile` (256×256, ölçek 4/16/64/256; örnekleme yüksekliği `r.y = 64/scale` — eskiden sabit 15'ti, büyük ölçekte dünyanın üstünü örnekliyordu) ve `mcmap_structs` (2048 blokluk hücre).
  **flip=1 şart** (cubiomes `biomesToImage` flip=0'da görüntüyü dikey ters çeviriyor; karolar birleşmiyordu).
  Windows DLL'i Linux'tan `pip install ziglang` → `python -m ziglang cc -target x86_64-windows-gnu -O2 -shared`.
  Sadece UCRT'ye bağlı, Python 64 bit olmalı. Karolar `cache/mc2/<seed>/<dim>/<ölçek>/x_y.png` (y düzeltmesiyle `mc`→`mc2`; eski klasör silinebilir).
- **Arayüz:** "Harita" sekmesi (`visible=_recent`: sadece Minecraft açıkken — mod son 10 sn içinde haber verdiyse; menüde de gelir). 6 sekme olunca ray `dense` olur.
  `mcmap` widget'ı kalıcı DOM: her saniyelik yenilemede karolar ve kaydırma korunur. Kaydırma (sürükle),
  +/− ve çift dokunuşla yakınlaştırma, takip düğmesi, yapı işaretleri (dokununca ad, koordinat, uzaklık).
  Deneme odaları ve iz kalıntıları sadece 1 px ≤ 4 blokta gösterilir. Yön oku: rotate(yaw+180).
  Nether'da Overworld karşılığı (×8) gösterilir.
- **Zum:** `BPP = [256..0.5]` blok/piksel; karo ölçeği `mcScale`. 1:256'da biyomlar pikselden küçük, karolar
  `.mclayer.far` ile soluk gösterilir (rota öne çıksın). Art arda zumda ara ölçek karoları istenmez (`zoomAt`,
  260 ms) ve yüklenmemiş eski karolar `src=""` ile iptal edilir — yoksa 1:256 karoları kuyrukta kalıyordu.
- **Yapılar (hepsi):** `STRUCTS` kod → (kısa, ad, renk, anahtar, en uzak zum). Overworld: köy, karakol, konak,
  anıt, antik şehir, kale, doğma noktası (1001), tapınaklar, cadı kulübesi, iglo, yıkık portal (≤8), batık gemi (≤8),
  okyanus kalıntısı (≤8), deneme odaları / iz kalıntıları / çöl kuyusu (≤4), gömülü hazine (≤2). Nether: kale, bastion,
  yıkık portal. End: End şehri. Madenler/geodlar yok (cubiomes'ta getStructurePos ile gelmiyor).
  Kaleler (128 tane ~2 sn!) ve doğma noktası `mcmap_strongholds`/`mcmap_spawn` ile seed başına bir kez (`_special`,
  `_state` arka planda ısıtır); eskiden her hücrede hesaplanıyordu (hücre 2 sn → 4 ms).
  Katman menüsü (katman ikonu): tür başına aç/kapat, `localStorage` `mcHide` / `mcStructs`. `_state().types`.
- **Biyom:** `mcmap_biome(seed, dim, x, y, z)` (ölçek 1); oyuncu için kendi y'si, harita noktası için y bilinmediğinden 63/90/120/160 sırayla, mağara biyomu (damlataş/yemyeşil/derin karanlık) çıktıkça yukarı + `mcmap_biome_str` → `BIOME_TR`. `/mc/biome?s&d&x&z`; oyuncunun biyomu
  SSE'de `biome` (`player_biome`, 4 blok hareket / 0,25 sn sınırı) → HUD'da çip. İpucu kutusu biyomu ayrıca çeker.
- **Kayıtlı yerler:** yıldız ikonu; `cache/mc_waypoints.json` dünya anahtarına göre liste, `mc.wp.add` (listeyi
  döner) / `mc.wp.del`. Haritada yıldız + ad; dokununca Hedef yap / Sil. İpucundaki "Kaydet" paneli koordinatla açar.
  Panellerden (arama, katmanlar, yerler) aynı anda biri açık (`mcPanel`). Düğme sütunu sığmazsa sola sarar.
- **Hedef/rota:** `@action("mc.target")` (x None → sil), `cache/mc_targets.json` dünya anahtarına göre.
  Hedef yapma: koordinat arama formu (X/Z, ± düğmeleri, "Git"/"Hedef yap"), haritada 550 ms basılı tutma,
  yapı ipucundaki "Hedef yap". Kuş uçuşu SVG kesikli çizgi + bayrak; HUD'da "HEDEF <mesafe> · sağa/sola N°"
  (yaw'a göre; Nether'da ÷8 çevrilir).
- **Gecikme:** `@stream("/mc/stream")` SSE; `from_mod` her POST'ta `_notify()` → istemci ~0,1 sn gecikmeyle
  konum alır (önceden yoklama ile 1–1,5 sn). Sekmeden çıkınca `mcStreamClose`. Ölçüm: ~8 olay/sn.
- Minecraft teması `games.detector` kancasıyla moddan gelen nabızla açılır (javaw.exe ile tanınamaz).
  `GAME_THEMES["minecraft"]["preview"] = False` → Tema sekmesinde kart yok.
