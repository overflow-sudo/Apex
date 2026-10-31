# Donanım, ses/ekran aygıt adları, modlar, kurulum sihirbazı, bu PC'ye özel ayarlar

(CLAUDE.md'den taşındı, 2026-10-31. Genel kurallar CLAUDE.md'de.)

## Donanım (2026-10-25 itibarıyla)

| Tür | Ad (eşleştirme anahtarı) | Ayrıntı |
|---|---|---|
| Ekran | **Smart M70F** | Samsung 4K 60 Hz, `\\.\DISPLAY2`. "TV" olarak kullanılıyor, oyun ekranı |
| Ekran | **EI242QR P** | Acer 1080p 165 Hz, `\\.\DISPLAY1`. Masaüstü monitörü |
| Ekran kartı | AMD Radeon RX 6800 XT | |
| Ses çıkışı | `4 - Smart M70F` (AMD HD Audio) | TV'nin HDMI sesi |
| Ses çıkışı | `5 - EI242QR P` (AMD HD Audio) | Monitörün sesi, kullanılmıyor |
| Ses çıkışı | `Hoparlör` (USB AUDIO CODEC) | Ses kartı. Müzik modunda kullanılır |
| Ses çıkışı | `Kulaklıklar` (HyperX Cloud III S Wireless) | Masaüstü modunda kullanılır |
| Ses girişi | `Hat` (USB AUDIO CODEC) | Gitar + mikrofon ses kartına bağlı |
| Ses girişi | `Mikrofon` (HyperX) | Kulaklığın mikrofonu |

Aygıt listesini yenilemek için kullanıcı `aygit_listesi.bat` dosyasına çift tıklar. Bu dosya
`ses_aygitlari.csv` ve `monitorler.csv` dosyalarını oluşturur, sen de onları okursun.
Bulut oturumlarında genelde Windows'ta komut çalıştıramıyorum (`device_bash` yok), bu yüzden bu yol kullanılıyor.

## Modlar (`config.PROFILES`)

| Anahtar | Tuş | Ekran | Çıkış | Giriş |
|---|---|---|---|---|
| `tv` | Oyun | Sadece Smart M70F (ana ekran) | Smart M70F | değişmez |
| `desk` | Masaüstü | İkisi de açık, ana ekran EI242QR | HyperX | HyperX |
| `music` | Müzik | değişmez | USB AUDIO (Hoparlör) | USB AUDIO (Hat) |

Gamepad'de bir tuşa basılınca (XInput) program otomatik olarak `tv` moduna geçer (`AUTO_GAMEPAD`).
Hangi modun aktif olduğu kaydedilmez; ekran ve ses durumuna bakılarak hesaplanır (`modes.current()`).
Hiçbir mod uymuyorsa üst çubukta "Mod · Özel" yazar.

### Bu PC'ye özel ayarlar ve kurulum sihirbazı (`core/local.py`, `modules/wizard.py`)
- `config.PROFILES` modların adını, ikonunu, ekran politikasını (liste / "all" / "keep") ve **varsayılan** aygıtlarını tutar.
  Bu PC'de gerçekten kullanılan aygıtlar `C:\PC_Kumanda\yerel\bu_pc.json` → `profiles` içinde, üstüne yazılır
  (`local.profiles()`). Mod kodu her yerde `local.profiles()` kullanmalı, `config.PROFILES`'ı doğrudan değil.
- `bu_pc.json` içinde `pc` (COMPUTERNAME) var. Klasör başka PC'ye kopyalanırsa dosya yok sayılır. Kur.bat `yerel\` ve `cache\`
  klasörlerini kopyalamaz ve ezmez, yani güncelleme ayarları sıfırlamaz.
- Açılışta `wizard.check()`: kayıt yoksa ve config'teki varsayılan aygıtların hepsi bu PC'de varsa (ses: takılı olmayanlar
  dahil, `audio.list_devices(active_only=False)`) sessizce kaydeder. Emir'in PC'si böyle (2026-10-31'de doğrulandı). Yoksa Modlar
  sekmesi "Hoş geldin · Ayarlamaya başla" ekranını, üst çubuk "Mod · Ayarlanmadı" yazısını gösterir.
- Sihirbaz Modlar sekmesinin içinde açılır (yeni sekme yok). Adımlar PROFILES'tan çıkar: ekran listesi → "hangi ekran açık kalsın",
  "all"+primary → "ana ekran", out/inp → ses/mikrofon. Her adımda "Değiştirme". Dokununca bir sonraki adıma geçer. Sonda özet kartları + Kaydet.
  Tek ekranlı PC'de ekran adımı yok, modlar ekrana dokunmaz. Ses adımında kapalı ekran varsa "Ekranları aç" düğmesi var (TV'nin HDMI sesi için).
  Modlar sekmesinin altındaki "Modları ayarla" düğmesi sihirbazı tekrar açar.
- Ses anahtarı: `_clean(device)` (örn. "HyperX Cloud III S Wireless", "USB AUDIO CODEC"; "2- " ön eki atılır) o yönde tekse o,
  değilse `_clean(name)` ("Smart M70F"), o da değilse id. Görünen adlar `labels["out:<anahtar>"]` (çıkış "Hoparlör", giriş "Hat" ayrı).
- Kur.bat: başlattıktan 6 sn sonra `bu_pc.json`'da "profiles" yoksa PC'de tarayıcıyla `http://localhost:8765` açar ve ne yapılacağını yazar.
