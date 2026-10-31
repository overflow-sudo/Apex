# Fare/klavye/kulaklık pili (Attack Shark, G HUB, HyperX HID)

(CLAUDE.md'den taşındı, 2026-10-31. Genel kurallar CLAUDE.md'de.)

## Pil durumu (`modules/battery.py`, Sistem sekmesinin altı)
- Kartlar `stats` + `compact: true` (3 sütun, tek satır). `config.BATTERY_LOW` (15) ve altı `hot`.
- **Üst çubuk uyarısı:** `@extra("battery")` kritik (şarj olmayan) cihazları döndürür → `#batt` yanıp sönen pil ikonu
  (960 px'ten darda sadece "%9", genişte "FARE %9 · KLAVYE %14"). Dokununca Sistem sekmesi. Medya kutusu buna yer açmak için daralır.
- **Fare = Attack Shark** (Emir'in faresi; PRO X SUPERLIGHT G HUB'da eşli ama kullanılmıyor, ACTIVE değilken yok sayılır).
  Xenta alıcısı `1D57:FA60`, MI_02 COL03, usage page `0x0A`, 5 baytlık giriş raporu. **Pasif:** alıcı ~4 sn'de bir
  `03 10 40 <durum> <seviye>` gönderir. Bu PC'de 2. bayt 0x10 ve seviye **0–10** (×10 = yüzde, `SHARK_SCALE`; yeni şarjlıyken 10 geldi). Kaynak projedeki X11 (0x55) gibi modellerde 0–100. Durum 01 pil, 02 harici güç, 03 şarj. Bağlanınca bir kez
  sahte %100 geldiği için aynı (durum, yüzde) iki kez üst üste gelince kabul edilir. 30 sn sessizlik = uykuda.
  Kaynak: daeoxide/attackshark-battery-windows docs/PROTOCOL.md. Eski not "%9" aslında %90'dı. Ayrı iş parçacığı sürekli okur.
- G HUB ve HyperX dakikada bir ölçülür.
- **Logitech** (G915 TKL = KEYBOARD, LIGHTSPEED alıcısı C547): G HUB'ın belgelenmemiş
  websocket'i `ws://127.0.0.1:9010`, alt protokol `json`, `Origin: file://`. `GET /devices/list` → `deviceInfos`
  (id, deviceType, displayName, state), `GET /battery/<id>/state` → `percentage`, `charging`, `mileage` (kalan saat).
  Uyuyan cihaz `state: NOT_CONNECTED` ve pil yolu `NO_SUCH_PATH` döner → "uykuda · son %x hh:mm". G HUB kapalıysa "G HUB kapalı".
- **HyperX Cloud III S Wireless** (03F0:02CC; HeadsetControl'de bu model yok): alıcının MI_03 arayüzünde usage page
  `0x01C0` koleksiyonu (64 bayt), rapor kimliği `0x0C`. Komut biçimi `0C 02 03 <01=oku/00=yaz> 00 <opcode>`.
  Pil: `0C 02 03 01 00 06` → cevap aynı 6 baytla başlar, `r[6]` yüzde (>100 = kulaklık kapalı), `r[7..8]` büyük endian mV.
  Kaynak: HeadsetControl issue #486 ve dddd-zdf/gear-tray. 2026-10-31'de bu PC'de doğrulandı (%67, 3884 mV).
  Opcode 0x12 cihaz adını döndürüyor. Şarj bayrağı bilinmiyor: kablo takılıyken okuma opcodelarını (0x02–0x1E, çiftler)
  tarayıp farkı bulmak gerekiyor. Alıcı kendiliğinden rapor göndermiyor (pasif dinleme boş). FF13 koleksiyonu
  (rapor 06/07) Cloud Alpha 2 komutlarına cevap vermedi.
- Senkron HID tutamacında okuma beklerken yazma da bekler; bu yüzden `core/hid.py` overlapped I/O kullanıyor.
