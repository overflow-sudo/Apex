# Logitech G915 klavye ışığı (LED SDK)

(CLAUDE.md'den taşındı, 2026-10-31. Genel kurallar CLAUDE.md'de.)

## Klavye ışığı (`modules/lighting.py`, `core/logiled.py`)
- Emir'in klavyesi **Logitech G915** (tuş başına RGB). Logitech LED SDK ctypes ile çağrılıyor, ek paket yok.
  DLL yolu registry'den okunuyor: `HKLM\SOFTWARE\Classes\CLSID\{a6519e67-7632-4375-afdf-caa889744403}\ServerBinary`
  (G HUB kuruyor, genelde `C:\Program Files\LGHUB\sdk_legacy_led_x64.dll`). Yedek: proje klasöründe
  `LogitechLedEnginesWrapper.dll` (SDK zip'inden).
- G HUB açık olmalı ve "LIGHTSYNC / uygulamaların ışığı kontrol etmesine izin ver" ayarı açık olmalı.
- Davranış: `games.current()` bir tema döndürürse tüm cihazlar (DEVICE_ALL=0x7) `accent` rengine
  `KEYBOARD_BRIGHTNESS` parlaklıkla boyanır, temanın `keys` listesindeki tuşlar `key_color` ile %100 boyanır
  (`key_color` yoksa `accent2`, o da yoksa beyaz). Tema yoksa `LogiLedShutdown` çağrılır ve G HUB profili geri gelir.
  Dakikada bir yeniden boyanır (G HUB profili geri almışsa diye). G HUB'a bağlanamazsa 30 sn'de bir dener.
- Tuş adları → tarama kodları: `logiled.KEYS`. Yeni tuş gerekirse buraya ekle.
- Oyunun kendi Logitech ışık desteği varsa o temaya `"lighting": False` yazılınca kumanda ışığa dokunmaz.
- Tema sekmesinde `@section("theme")` ile "Işık takibi" aç/kapa düğmesi ve durum metni var.
- G HUB DLL'i bu PC'de `C:\Program Files\LGHUB\sdks\sdk_legacy_led_x64.dll`. İhraç ettiği fonksiyonlar
  (pefile ile bakıldı): SetLighting, SetLightingForKeyWith{KeyName,ScanCode,HidCode,QuartzCode},
  SetLightingFromBitmap, SetTargetDevice, Pulse/FlashSingleKey, StopEffects, Save/Restore, InitWithName.
- **2026-10-25 sorunu:** İlk sürümde tüm klavye tek renk oldu, tuş vurguları görünmedi. Düzeltme: ana renkten
  sonra 0,35 sn bekleme, `SetTargetDevice(PERKEY=0x4)`, tuşlar için KeyName → ScanCode → HidCode yedekleri
  (çalışan yöntem `logiled.key_method`'da tutuluyor), tuşlar 2 tur boyanıyor, init sonrası 1 sn bekleniyor.
  Tema sekmesindeki durum yazısı "x/y tuş" gösteriyor. **Doğrulanmadı.** Hâlâ tek renkse sıradaki adım
  `LogiLedSetLightingFromBitmap` (21×6 BGRA, tuş→indeks tablosu gerekiyor).
- `KEYBOARD_KEY_EFFECT = "pulse"`: vurgulu tuşlar `LogiLedPulseSingleKey` ile nefes alır.
- Log'da "Logitech LED DLL:" satırı DLL'in bulunduğunu, "klavye ışığı: <oyun> · x/y tuş · yöntem <..>" boyamayı gösterir.
