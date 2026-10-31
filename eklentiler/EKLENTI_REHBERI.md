# PC Kumanda — Eklenti Rehberi

Bu dosya, PC Kumanda'ya **ayrı bir oturumda** eklenti yazmak için gereken her şeyi anlatır. Yeni oturumda
Claude'a önce bunu okut. Kumandanın geri kalanını bilmeden eklenti yazılabilmeli. Genel proje notları
`CLAUDE.md`'de. Çalışan bir örnek: `eklentiler/_ornek/` ve `eklentiler/minecraft/`.

---

## 1. Kumanda nedir (30 saniyede)

- Windows PC'de çalışan küçük bir Python sunucusu (`pc_kumanda.py`, port 8765). Masadaki eski bir Android telefonun
  Chrome'u `http://PC_IP:8765` adresini yatay (~780×360) açar. Masaüstü tarayıcıda da açılır, orantılı büyütülür.
- Sunucu arayüzü **tarif eder**, telefon çizer: `GET /api/ui?tab=<id>` cevabı sekmeleri ve bölümleri (section)
  JSON olarak verir, `web/app.js` bunları çizer. Düğmeler `POST /api/action {name, params}` çağırır.
- Sol rayda sekmeler, üstte durum etiketleri var. Açık sekme `poll` saniyede bir yenilenir (varsayılan 8 sn).

## 2. Modül mü, eklenti mi?

| | `modules/<ad>.py` | `eklentiler/<ad>/` |
|---|---|---|
| Ne zaman | Sadece hazır widget'lar (kart, liste, düğme, gösterge, metin) yetiyorsa | Kendi JS/CSS'i, özel widget'ı, ek dosyaları (DLL, mod, resim) varsa ya da ayrı oturumda geliştirilecekse |
| Dosyalar | Tek .py | Klasör: `eklenti.py` + `web/` + `NOTLAR.md` + istediğin ekler |
| Python API | Aynı | Aynı |

## 3. Klasör yapısı

```
eklentiler/<ad>/              <ad>: sadece küçük harf, rakam, _ (Python modül adı olmalı). _ ile başlarsa KAPALI.
  eklenti.py                  zorunlu — açılışta import edilir, dekoratörlerle kendini kaydeder
  web/                        isteğe bağlı — içindeki .css ve .js dosyaları index.html'e KENDİLİĞİNDEN eklenir
    <ad>.js                   (alfabetik sırayla, app.js'ten sonra; alt klasör desteklenmez)
    <ad>.css
    resim.png                 diğer dosyalar /eklenti/<ad>/resim.png adresinden sunulur
  NOTLAR.md                   o eklentinin kendi Claude notları (bulgular, doğrulanmamışlar, tuzaklar)
  native/, mod/, ...          eklentiye özel ekler (Python'da yol: os.path.dirname(__file__))
```

- Kapatmak için klasörün adını `_` ile başlat (`_ornek` böyle). Silmek için klasörü sil.
- Kurulum: Kur.bat tüm klasörü `C:\PC_Kumanda\eklentiler\<ad>\` altına kopyalar. Kaynaktan silinen eklenti klasörünü
  çalışan kopyadan da siler.
- Kalıcı veriyi **eklenti klasörüne yazma**, `data_dir()` kullan (aşağıda). Eklenti güncellenince kayıtlar kaybolmaz.

## 4. Yükleme sırası ve yaşam döngüsü

1. `modules/*.py` (alfabetik) → `eklentiler/*/eklenti.py` (alfabetik) import edilir. Hata veren eklenti log'a
   `EKLENTİ HATASI` yazar ve atlanır, kumandanın geri kalanı çalışır.
2. Tüm `@on_start` fonksiyonları çalışır (arka plan iş parçacıkları burada başlar).
3. HTTP sunucusu açılır. `index.html` istenince yüklü eklentilerin CSS'leri `</head>` önüne, JS'leri `app.js`'ten sonra eklenir.
4. Tarayıcıda: `app.js` → eklenti JS'leri → `DOMContentLoaded` → ilk `/api/ui`. Yani eklenti widget'ları ilk çizimden
   önce kayıtlı olur.
5. `.py` dosyası değişince (eklentilerinkiler dahil) kumanda kendini yeniden başlatır (`core/reloader.py`): önce `@on_stop`
   kancaları, sonra yeni süreç. Sözdizimi hatası varsa yeniden başlatmaz.
6. Web dosyası değişince sürüm değişir, telefon sayfayı kendiliğinden yeniler (yeniden başlatmadan sonra).

## 5. Python API (`eklenti.py`)

Sadece **Python standart kütüphanesi**. Python **3.8** ile uyumlu kal (`match`, `X | Y` tip birleşimi, `str.removeprefix` yok).

```python
from core.registry import tab, section, action, status, extra, route, stream, post, on_start, on_stop
from core.plugin import settings, data_dir
from core.system import log, run, cached, match, BASE
```

| Dekoratör | İmza | Ne yapar |
|---|---|---|
| `@tab(id, başlık, icon="bolt", order=50, poll=None, visible=None)` | `def view(): return [section, ...]` | Yeni sekme. `order` rayda sıra (modlar 10, ekran 20, ses 30, harita 35, sistem 40, tema 60). `poll=2` = sekme açıkken 2 sn'de bir yenile. `visible=fn` False dönerse sekme gizli. **Aynı `id` iki kez kaydedilirse ikincisi yok sayılır.** |
| `@section(sekme_id, order=50)` | `def fn(): return section` ya da liste | Başka bir sekmenin altına bölüm ekler (yeni sekme açmadan). Mevcut sekmeler: `modes`, `screens`, `sound`, `system`, `theme`. |
| `@action("ad.eylem")` | `def fn(**params)` | Düğme eylemi. Parametreler anahtar kelime olarak gelir. Dönüş değeri telefona `{ok:true, result}` olarak gider, hata `{ok:false, error}` olur. `state.lock` altında çalışır, sonra önbellek temizlenir. |
| `@status(order=50)` | `def fn(): return "Kısa · Metin"` ya da `None` | Üst çubuk etiketi. İngilizce değer için `{"text": "Oynuyor", "value": "Skyrim", "lang": "en"}`. |
| `@extra("anahtar")` | `def fn(): return json_değer` | `/api/ui` cevabına (hafif yenilemeler dahil) ek alan. JS'te `PCK.on("data", ...)` ile okunur. |
| `@route("/yol")` | `def fn(q): return (content_type, bytes)` ya da `None` (404) | Ek GET adresi. `q` = sorgu parametreleri `{ad: değer}`. **PIN istemez**, sadece resim/zararsız veri sun. |
| `@stream("/yol")` | `def fn(q, send)` | Server-Sent Events. Bloklar, `send("json metni")` ile olay yollar. Telefon kapatınca `send` hata fırlatır ve fonksiyon biter. 15 sn'de bir canlı tutma gönder. PIN istemez. |
| `@post("/yol")` | `def fn(body): return dict` | Yerel POST (sadece 127.0.0.1, PIN yok). PC'deki başka programlar için, örn. Minecraft modu. |
| `@on_start` | `def fn()` | Açılışta bir kez. Uzun işler için **kendi iş parçacığını** başlat (`threading.Thread(daemon=True)`). |
| `@on_stop` | `def fn()` | Yeniden başlatmadan önce temizlik (alt süreçleri öldür vb.). |

Yardımcılar:
- `settings("AD", {varsayılanlar})`: varsayılanların kopyası. Kullanıcı `config.py`'ye `AD = {...}` yazarsa değerleri üstüne yazılır.
- `data_dir("<eklenti>")`: `C:\PC_Kumanda\cache\<eklenti>\` (yoksa oluşturur). Kur.bat bu klasöre dokunmaz.
- `log(...)`: zaman damgalı log satırı. Kullanıcıda `%LOCALAPPDATA%\PC_Kumanda\kumanda.log` dosyasına gider.
- `run([exe, args...], timeout=30)`: konsol penceresi açmadan komut çalıştırıp **bekler**. Açık kalacak programlar için `subprocess.Popen`.
- `@cached(ttl=2, max_stale=30)`: bayat-ama-hızlı önbellek (süresi dolan değer hemen döner, yenisi arka planda hesaplanır).
- `match(anahtar, *metinler)`: büyük/küçük harf ve boşluk duyarsız "içeriyor mu".
- Çekirdek modüller import edilebilir: `core.audio`, `core.display`, `core.state`, `modules.games` (`@games.detector`:
  exe adından tanınamayan oyun için tema kimliği döndüren fonksiyon), `core.hid`, `core.winstats`...

**Kurallar**
- `view()` **hızlı** olmalı (telefon 5 sn'de zaman aşımına düşer). Yavaş ölçümü `@on_start` iş parçacığında yap, `view()` son değeri okusun.
- Bir eylemden bir program açacaksan `subprocess.Popen` kullan, `run()` beklediği için sunucuyu kilitler.
- Windows dışında (test) çalışırken Windows'a özgü çağrıları `core.procs.IS_WIN` ile koru.
- Anti-cheat'li oyunların süreçlerini **açma** (OpenProcess, bellek okuma, enjeksiyon yok).
- Python'da `.upper()` ile Türkçe metni büyütme ("MÜZIK" olur). Büyütmeyi CSS yapar.

## 6. Hazır widget'lar (section biçimi)

Her section'a isteğe bağlı `"title"` verilebilir. `"fill": true` kalan yüksekliği doldurur.

```jsonc
{ "type": "tiles",   "fill": true,  "items": [{ "title", "sub", "icon", "active", "lines": [["ANAHTAR","değer"]], "action", "params", "img", "img_white", "lang" }] }
{ "type": "list",    "items": [{ "title", "sub", "icon", "active", "action", "params" }] }
{ "type": "buttons", "items": [{ "title", "icon", "action", "params" }] }
{ "type": "stats",   "fill": true, "compact": false, "items": [{ "label", "value", "unit", "pct": 0-100|null, "hot": bool, "sub" }] }
{ "type": "text",    "text": "..." }
{ "type": "<kendi_widget_türün>", "data": { ... } }      // eklentinin JS'i çizer (bölüm 7)
```
- Art arda gelen `list`'ler yan yana sütunlara, art arda gelen `buttons`'lar tek satıra dizilir. 4'ten fazla kart olunca küçük kart düzenine geçilir.
- Ray en fazla 5 sekmeyi rahat alır, 6 ve üstünde sıkışık düzene geçer. Gerekmedikçe sekme açma, `@section` ya da `visible=` kullan.
- Hazır ikonlar: bolt, gamepad, desktop, music, monitor, volume, headphones, speaker, mic, power, battery, full, play,
  pause, next, prev, map, target, plus, minus, search, flag, moon, layers, star, pin, close, back, check, tune,
  keyboard, palette, chip, temp, refresh. Yenisi için JS'te `PCK.icons({...})`.

## 7. JS API (`window.PCK`)

Eklenti JS'i **sadece** `window.PCK` üzerinden çekirdekle konuşur. Çekirdeğin iç değişkenlerine erişemez, erişmeye de çalışma.
Her dosyayı kendi IIFE'sine sar:

```js
(function () {
  "use strict";
  var P = window.PCK;
  if (!P) return;
  // ...
})();
```

| Üye | Açıklama |
|---|---|
| `P.widget(tür, fn)` | Yeni section türü. `fn(section)` bir **DOM öğesi** döndürür. Section her yenilemede yeniden çizilir: pahalı bir widget ise (harita gibi) DOM'u bir kez oluşturup aynısını döndür, sadece içeriği güncelle (`eklentiler/minecraft/web/harita.js` → `mcWidget`). `fn` hata fırlatırsa sadece o bölümde "Bu bölüm çizilemedi" yazar. |
| `P.icons({ad: '<svg içeriği>'})` | 24×24, `stroke="currentColor"` çizgi ikon ekler (sadece `<path>`, `<circle>` vb. iç kısım). |
| `P.on(olay, fn)` | Olaylar aşağıda. |
| `P.el(etiket, sınıf, metin)` | `document.createElement` kısayolu. Metin `textContent` olarak eklenir (güvenli). |
| `P.icon(ad)` / `P.iconEl(ad)` | İkon SVG metni / ikon `<span class="ic">` öğesi. |
| `P.api(yol, gövde)` | `fetch` + PIN başlığı + zaman aşımı (GET 5 sn, POST 45 sn) → JSON Promise. Eylem: `P.api("/api/action", {name: "ad.eylem", params: {...}})` → `{ok, result}` ya da `{ok:false, error}`. |
| `P.toast(metin, ms)` | Alttaki kısa bildirim. Gelenek: büyük harfle yaz ("KAYDEDİLDİ"). `ms` yoksa açık kalır. |
| `P.store.get(k)` / `P.store.set(k, v)` | localStorage (hata yutulur). Anahtarlara eklenti adıyla ön ek ver (`sayacGorunum`). |
| `P.zoom()` | Masaüstü CSS zoom katsayısı. **Fare/dokunma koordinatlarını hesaplarken** `(clientX - rect.left) / P.zoom()`. Telefonda 1. |
| `P.tab()` / `P.goTab(id)` | Açık sekme kimliği / sekmeye geç. |
| `P.refresh()` | Açık sekmeyi hemen yeniden yükle (eylemden sonra). |

Olaylar (`P.on`):

| Olay | Argümanlar | Ne zaman |
|---|---|---|
| `"data"` | `(cevap)` | Her `/api/ui` cevabında (kendi `@extra` alanların dahil). |
| `"render"` | `(sekme_id)` | Ana alan her yeniden çizildiğinde. Sekmen kapandıysa açık bağlantıları (EventSource) burada kapat. |
| `"resize"` | — | Pencere boyutu değişti. |
| `"close"` | — | Esc ya da PC klavyesinden sekme değiştirme: açık panellerini kapat. |
| `"key"` | `(tuş, sekme_id)` | Masaüstünde basılan tuş (1–9, F, R, Esc çekirdeğe ait). İşlediysen `true` döndür. |

**Anlık veri:** Saniyede birden çok güncelleme gerekiyorsa yoklama yapma, `@stream` + `new EventSource("/yol")` kullan.
Sekme kapanınca kapat (`"render"` olayı). Örnek: harita konumu ~0,1 sn gecikmeyle geliyor.

## 8. CSS kuralları

- **Sınıf adları eklenti adıyla başlar** (`.sayac-kutu`, `.mc...`). `@keyframes` adları da (`mc-ping`).
- **`.main` sınıfını kullanma**, ana içerik alanının sınıfı (oynat düğmesinde ve güç panelinde bu yüzden sorun çıktı).
- **Sabit renk yazma**, tema değişkenlerini kullan. Oyun açıkken renkler o oyunun temasına geçer.
  `--ac` (vurgu), `--on-ac` (vurgu zemin üstündeki yazı), `--ac2`, `--bg`, `--fg`, `--panel`, `--line`, `--line-hi`,
  `--dim` (soluk yazı), `--mono` / `--cond` (yazı tipleri).
- Varsayılan görünüm siyah-beyaz "oyuncu" teması: siyah zemin, ince beyaz çizgiler, köşeli kutular, aktif öğe ters çevrilir
  (`background: var(--ac); color: var(--on-ac)`). Yuvarlak köşe ve gölge yok.
- Bölümü doldurmak için: section'a `"fill": true`, widget kök öğesine `flex: 1 1 auto; min-height: 0;`.
- Büyük harfi CSS `text-transform: uppercase` yapar (`<html lang="tr">` sayesinde İ/I doğru çıkar). İngilizce metin
  büyütülecekse öğeye `lang="en"` ver, yoksa "SKYRİM" olur.
- Fare için: `@media (hover: hover) and (pointer: fine) { ... }` içinde hover/imleç.

## 9. Eski Android Chrome kuralları (hedef cihaz)

JS'te **kullanma**: `?.`, `??`, `replaceAll`, sınıf özel alanları (`#x`), `class` alanları, `async/await` (Promise zinciri kullan),
`Array.prototype.at`, `structuredClone`. `var` + `function` yaz, mevcut kodun stilini izle.
CSS'te **kullanma**: flex `gap` (margin ya da grid `grid-gap` kullan), `aspect-ratio`, `:has()`, `inset`.

## 10. Test (Windows'ta, çalışan kumandaya dokunmadan)

1. Sözdizimi: `python -m py_compile eklentiler/<ad>/eklenti.py` ve `node -e "new Function(require('fs').readFileSync('eklentiler/<ad>/web/<ad>.js','utf8'))"`.
2. Ayrı bir test kopyası, ayrı bir portta:
   - Projeyi scratchpad'e kopyala (`core modules web eklentiler config.py pc_kumanda.py *.exe`).
   - Test kopyasının `config.py` dosyasında: `PORT = 8766`, `AUTO_RELOAD = False`, `KEYBOARD_LIGHTING = False`, en alta `HOTKEYS = False`.
   - Çalıştır: `PYTHONIOENCODING=utf-8 python -u pc_kumanda.py` (arka planda). Log'da `eklenti yüklendi: <ad>` olmalı.
3. API: `curl "http://127.0.0.1:8766/api/ui?tab=<sekme>"`, eylem: `curl -X POST -d '{"name":"ad.eylem","params":{}}' http://127.0.0.1:8766/api/action`.
4. Görsel kontrol (telefon boyutu 780×360), headless Edge:
   ```
   "/c/Program Files (x86)/Microsoft/Edge/Application/msedge.exe" --headless=new --disable-gpu --hide-scrollbars \
     --user-data-dir=<scratch>/edge --window-size=780,360 --virtual-time-budget=7000 --screenshot=<scratch>/x.png "http://127.0.0.1:8766/#<sekme>"
   ```
   Açık kalan SSE bağlantıları yüzünden headless Edge bitmez. **Sadece test kopyasının** `web/app.js` dosyasında en üste
   `window.EventSource = null;` ekle ve `var currentTab = store.get("tab") || "";` satırını
   `var currentTab = location.hash.slice(1) || store.get("tab") || "";` yap (adresteki `#sekme` açılsın).
   Asıl `web/app.js` dosyasına bu değişiklikleri **koyma**.
5. Bozulmadı mı: Modlar ve Sistem sekmelerinin ekran görüntüsü önceki gibi mi? Başka eklentilerin sekmeleri açılıyor mu?
6. Asıl `C:\PC_Kumanda` kopyasına veya kullanıcının cihazlarına (ekran, ses, güç) dokunan eylemleri testte çalıştırma.

## 11. Entegrasyon (eklenti bitince)

- [ ] Klasör `eklentiler/<ad>/` altında, adında `_` yok (kapalı değil).
- [ ] `NOTLAR.md` var: ne yapıyor, dosyalar, veri kaynakları, **doğrulananlar / doğrulanmayanlar** (tarihle), bilinen tuzaklar.
- [ ] `config.py`'ye ayar gerekiyorsa `settings("AD", {...})` varsayılanları eklenti içinde. `config.py`'ye satır eklemek isteğe bağlı.
- [ ] Sekme kimliği, eylem adları (`<ad>.` ön ekli), CSS sınıfları ve localStorage anahtarları eklenti adıyla başlıyor.
- [ ] Test (bölüm 10) yapıldı ve ekran görüntüsüne bakıldı.
- [ ] `CLAUDE.md` → "Eklentiler" bölümüne 1–2 satırlık özet, `notlar/gecmis.md` başına bir satır.
- [ ] Kullanıcıya: **"Kur.bat'ı tekrar çalıştır"** (çalışan kopya `C:\PC_Kumanda`, geliştirme kopyası masaüstünde).

Çekirdekte (`core/`, `web/app.js`, `web/style.css`) bir değişiklik gerekiyorsa eklenti oturumunda **yapma**. Ne gerektiğini
`NOTLAR.md`'ye "Çekirdekten istenenler" başlığıyla yaz. Çekirdek değişikliği ayrı yapılır ve bu rehbere eklenir
(örn. yeni bir `PCK` olayı).

## 12. Yeni oturum için hazır istem

> PC Kumanda'ya `<ad>` adında bir eklenti yazacağız: <ne yapacağı>. Önce `eklentiler/EKLENTI_REHBERI.md`'yi,
> sonra şablon olarak `eklentiler/_ornek/` klasörünü oku. Sadece `eklentiler/<ad>/` içinde çalış. Çekirdeğe
> (`core/`, `web/`, `modules/`) dokunma, gerekirse `NOTLAR.md`'ye yaz. Bitince rehberin 10. bölümündeki gibi
> ayrı portta test et, ekran görüntüsüne bak ve 11. bölümdeki listeyi tamamla.

## 13. Örnekler

- **`eklentiler/_ornek/`**: en küçük tam eklenti. Sekme, kendi widget'ı (`ornek_sayac`), kendi ikonu, eylem, üst çubuk
  etiketi, ayar, kalıcı veri. Denemek için klasörü `eklentiler/ornek/` olarak kopyala.
- **`eklentiler/minecraft/`**: büyük gerçek örnek. `@post` (oyundaki mod konum gönderir), `@stream` (SSE ile anlık konum),
  `@route` (harita karoları PNG), `visible=` (sekme sadece oyun açıkken görünür), `games.detector`, ctypes DLL, kalıcı DOM'lu
  widget, `render`/`resize`/`close`/`key` olayları.
