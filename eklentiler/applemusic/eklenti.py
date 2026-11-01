"""
Apple Music eklentisi — EAMusic istemcisini (C:\\Users\\emir\\Desktop\\EAMusic) telefondan yönetir.

EAMusic'in yerel köprüsüyle konuşur (yalnızca 127.0.0.1):
  GET  <url>/api/remote/state    → {connected, state: {playing, track, shuffle, repeat, volume, pos, dur, playlists...}}
  POST <url>/api/remote/command  → {cmd, args}  (toggle, next, prev, shuffle, repeat, volume, playlist...)
EAMusic sayfası komutları SSE ile anında alır ve MusicKit'te uygular.

Ayar (config.py'de isteğe bağlı):  APPLEMUSIC = {"url": "http://127.0.0.1:3000", "klasor": r"C:\\...\\EAMusic"}
Ayrıntılar: eklentiler/applemusic/NOTLAR.md
"""
import json, os, shutil, subprocess, threading, time
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

from core.plugin import settings
from core.registry import action, on_start, stream, tab
from core.system import log
from core.procs import IS_WIN

AYAR = settings("APPLEMUSIC", {
    "url": "http://127.0.0.1:3000",                      # EAMusic sunucusu
    "klasor": r"C:\Users\emir\Desktop\EAMusic",         # EAMusic kapalıysa buradaki scripts/app-mode.js çalıştırılır
    "yenile": 1.5,                                       # EAMusic açıkken durum yoklama aralığı (sn)
    "kucuk_ac": True,                                    # "Aç" ile açılan pencere görev çubuğuna küçültülsün
    "otomatik_ac": True,                                 # EAMusic hep açık kalsın: kapanırsa 30 sn içinde (küçültülmüş) yeniden açılır
    "otomatik_bekle": 20,                                # açılışta masaüstü otursun diye bekleme (sn)
})

# Küçültülmüş/arka plandaki pencerede tarayıcı zamanlayıcıları kısmasın (köprü canlı kalsın)
EDGE_BAYRAKLAR = ["--disable-background-timer-throttling", "--disable-renderer-backgrounding",
                  "--disable-backgrounding-occluded-windows", "--disable-background-media-suspend",
                  # app-mode.js ile aynı: AudioContext (spektrum) tıklama beklemeden çalışsın
                  "--autoplay-policy=no-user-gesture-required"]

CREATE_NO_WINDOW = 0x08000000
CREATE_NEW_PROCESS_GROUP = 0x00000200

_durum = {"server": False, "connected": False, "state": None, "ts": 0.0}
_kilit = threading.Lock()
_son_hata = ""


def _istek(yol, veri=None, timeout=2.0):
    """EAMusic'e istek atar → (http_kodu, json) ya da sunucu kapalıysa (None, {})."""
    url = AYAR["url"].rstrip("/") + yol
    data = json.dumps(veri).encode("utf-8") if veri is not None else None
    headers = {"Content-Type": "application/json"} if data is not None else {}
    try:
        with urlopen(Request(url, data=data, headers=headers), timeout=timeout) as r:
            return r.status, json.loads(r.read().decode("utf-8") or "{}")
    except HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode("utf-8") or "{}")
        except Exception:
            return e.code, {}
    except (URLError, OSError, ValueError):
        return None, {}


def _yokla():
    global _son_hata
    kod, govde = _istek("/api/remote/state", timeout=1.5)
    with _kilit:
        _durum["server"] = kod == 200
        _durum["connected"] = bool(govde.get("connected")) if kod == 200 else False
        _durum["state"] = govde.get("state") if kod == 200 else None
        _durum["age"] = govde.get("age") or 0          # sayfanın durumu kaç ms önce gönderdiği
        _durum["ts"] = time.time()
    if kod not in (None, 200):
        hata = "EAMusic köprüsü HTTP %s" % kod
        if hata != _son_hata:
            _son_hata = hata
            log("applemusic:", hata)


def _ozet():
    with _kilit:
        # age: durum ne kadar eski (ms). Telefon ilerlemeyi buna göre hesaplar; saatler farklı olabileceği
        # için mutlak zaman damgası kullanılmaz.
        age = int(_durum.get("age", 0) + (time.time() - _durum["ts"]) * 1000) if _durum["ts"] else 0
        return {"server": _durum["server"], "connected": _durum["connected"], "state": _durum["state"],
                "age": age}


def _dongu():
    while True:
        try:
            _yokla()
        except Exception as e:                      # iş parçacığı asla ölmesin
            log("applemusic yoklama hatası:", e)
        # EAMusic kapalıyken seyrek yokla
        time.sleep(AYAR["yenile"] if _durum["server"] else 5)


_son_acma = [0.0]


def _bekci():
    """
    EAMusic hep açık kalsın (Emir'in isteği, 2026-11-01): 30 sn'de bir bakar, sayfa köprüye bağlı değilse açar
    (sunucu kapalıysa sunucu + pencere, sunucu açıksa sadece pencere). Açtıktan sonra 60 sn bekler ki yavaş
    açılışta ikinci pencere açılmasın. Üst üste açılamıyorsa bekleme 5 dk'ya kadar uzar.
    """
    time.sleep(AYAR["otomatik_bekle"])
    hata = 0
    while True:
        try:
            _yokla()
            if _durum["connected"]:
                hata = 0
            elif time.time() - _son_acma[0] > 60:
                log("applemusic: EAMusic kapalı, açılıyor")
                ac()
                _son_acma[0] = time.time()
                hata += 1
        except Exception as e:
            log("applemusic: otomatik açma başarısız:", e)
            hata += 1
        time.sleep(min(30 * 2 ** max(hata - 1, 0), 300))


@on_start
def basla():
    threading.Thread(target=_dongu, daemon=True).start()
    # Klasöre erişilemiyorsa (başka Windows kullanıcısı) otomatik açma yapılmaz
    if IS_WIN and AYAR["otomatik_ac"] and os.path.isfile(os.path.join(AYAR["klasor"], "scripts", "app-mode.js")):
        threading.Thread(target=_bekci, daemon=True).start()


# ---- Spektrum ----
# EAMusic sayfası çalan sesin 32 bantlık spektrumunu saniyede 25 kez gönderir (GET /api/remote/spectrum, SSE).
# Tek bir yukarı akış iş parçacığı, yalnızca en az bir telefon dinlerken EAMusic'e bağlanır ve kareleri dağıtır.
# Kimse dinlemeyince bağlantı kapanır → EAMusic hesaplamayı durdurur.

_spk = {"dinleyen": 0, "kare": "", "seq": 0, "calisiyor": False}
_spk_kosul = threading.Condition()


def _spektrum_yukari():
    """EAMusic'in spektrum akışını okur. EAMusic kapalıysa 3 sn'de bir yeniden dener."""
    try:
        while True:
            with _spk_kosul:
                if _spk["dinleyen"] <= 0:
                    _spk["calisiyor"] = False
                    return
            try:
                # Sunucu 2 sn'de bir ping yollar; 6 sn sessizlik = kopuk
                with urlopen(AYAR["url"].rstrip("/") + "/api/remote/spectrum", timeout=6) as r:
                    for satir in r:
                        if _spk["dinleyen"] <= 0:
                            break
                        if not satir.startswith(b"data:"):
                            continue
                        kare = satir[5:].strip().decode("ascii", "ignore")
                        if len(kare) > 400:
                            continue
                        with _spk_kosul:
                            _spk["kare"] = kare
                            _spk["seq"] += 1
                            _spk_kosul.notify_all()
            except (URLError, OSError, ValueError):
                pass
            # Akış koptu: telefondaki çubuklar sönsün
            with _spk_kosul:
                _spk["kare"] = ""
                _spk["seq"] += 1
                _spk_kosul.notify_all()
            time.sleep(3)
    finally:
        with _spk_kosul:
            _spk["calisiyor"] = False


@stream("/applemusic/spektrum")
def spektrum_akisi(q, send):
    """Telefon Müzik sekmesi açıkken dinler. Her olay: "12,40,..." (32 sayı, 0–255) ya da "" (veri yok)."""
    with _spk_kosul:
        _spk["dinleyen"] += 1
        if not _spk["calisiyor"]:
            _spk["calisiyor"] = True
            threading.Thread(target=_spektrum_yukari, daemon=True).start()
        seq = _spk["seq"]
    try:
        send('""')
        while True:
            with _spk_kosul:
                _spk_kosul.wait_for(lambda: _spk["seq"] != seq, timeout=5)
                yeni = _spk["seq"] != seq
                seq = _spk["seq"]
                kare = _spk["kare"]
            # 5 sn kare yoksa canlı tutma: telefon gittiyse send hata verir ve döngü biter
            send(json.dumps(kare) if yeni else "0")
    finally:
        with _spk_kosul:
            _spk["dinleyen"] -= 1


@tab("applemusic", "Müzik", icon="applemusic", order=32, poll=2)
def view():
    # Hızlı: sadece arka plan iş parçacığının son ölçümünü okur
    return [{"type": "applemusic", "fill": True, "data": _ozet()}]


# ---- EAMusic'i açma ----

def _node():
    yol = shutil.which("node")
    if yol:
        return yol
    for aday in (os.path.join(os.environ.get("ProgramFiles", r"C:\Program Files"), "nodejs", "node.exe"),
                 os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "nodejs", "node.exe")):
        if aday and os.path.isfile(aday):
            return aday
    return None


def _tarayici():
    pf86 = os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")
    pf = os.environ.get("ProgramFiles", r"C:\Program Files")
    for aday in (os.path.join(pf86, "Microsoft", "Edge", "Application", "msedge.exe"),
                 os.path.join(pf, "Microsoft", "Edge", "Application", "msedge.exe"),
                 os.path.join(pf, "Google", "Chrome", "Application", "chrome.exe")):
        if os.path.isfile(aday):
            return aday
    return None


def _calistir(args, cwd=None):
    subprocess.Popen(args, cwd=cwd, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                     stderr=subprocess.DEVNULL, creationflags=CREATE_NO_WINDOW | CREATE_NEW_PROCESS_GROUP)


def _eamusic_pencereleri():
    """Başlığı 'EAMusic' ile biten görünür Edge/Chrome pencereleri (sayfa başlığı: 'Şarkı — Sanatçı · EAMusic')."""
    import ctypes
    from ctypes import wintypes
    u = ctypes.windll.user32
    bulunan = []

    def cb(hwnd, _):
        if not u.IsWindowVisible(hwnd):
            return True
        n = u.GetWindowTextLengthW(hwnd)
        if n <= 0:
            return True
        baslik = ctypes.create_unicode_buffer(n + 1)
        u.GetWindowTextW(hwnd, baslik, n + 1)
        sinif = ctypes.create_unicode_buffer(64)
        u.GetClassNameW(hwnd, sinif, 64)
        if sinif.value == "Chrome_WidgetWin_1" and baslik.value.rstrip().endswith("EAMusic"):
            bulunan.append(hwnd)
        return True

    PROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    u.EnumWindows(PROC(cb), 0)
    return bulunan


def _kucult_bekle(onceki, sure=30):
    """
    Yeni açılan EAMusic penceresini bulup küçültür (Edge'in güvenilir bir 'küçük başlat' bayrağı yok).

    Sayfa yüklenip köprüye BAĞLANANA kadar beklenir: Chromium, hiç görünür olmamış bir sayfanın medyasını
    pencere ilk kez gösterilene kadar ertelediği için erken küçültülen pencerede müzik çalmıyordu
    (açınca başlıyordu). Bağlandıktan sonra sayfa en az bir kez görünür çizilmiş olur.
    """
    import ctypes
    SW_MINIMIZE = 6                       # küçült ve odağı önceki pencereye geri ver
    bitis = time.time() + sure
    yeni = []
    try:
        # 1) pencerenin belirmesini bekle
        while time.time() < bitis and not yeni:
            yeni = [h for h in _eamusic_pencereleri() if h not in onceki]
            if not yeni:
                time.sleep(0.15)
        if not yeni:
            log("applemusic: küçültülecek pencere bulunamadı")
            return
        # 2) sayfanın yüklenip köprüye bağlanmasını bekle (MusicKit hazır, sayfa görünür çizildi)
        while time.time() < bitis:
            _yokla()
            if _durum["connected"]:
                break
            time.sleep(0.3)
        time.sleep(1.0)                   # medya öğesi görünürken hazırlansın
        for h in yeni:
            ctypes.windll.user32.ShowWindow(h, SW_MINIMIZE)
    except Exception as e:
        log("applemusic: pencere küçültülemedi:", e)


def _ac_ve_kucult(args, cwd=None):
    onceki = set(_eamusic_pencereleri()) if AYAR["kucuk_ac"] else set()
    _calistir(args, cwd)
    if AYAR["kucuk_ac"]:
        threading.Thread(target=_kucult_bekle, args=(onceki,), daemon=True).start()


@action("applemusic.ac")
def ac():
    """EAMusic'i PC'de açar. Sunucu zaten çalışıyorsa sadece pencereyi açar."""
    if not IS_WIN:
        raise RuntimeError("Sadece Windows'ta açılabilir")
    _yokla()
    if _durum["connected"]:
        return "EAMusic zaten açık"

    if _durum["server"]:
        # Sunucu var ama pencere yok (ör. start:web) → aynı profille uygulama penceresi aç
        tarayici = _tarayici()
        if not tarayici:
            raise RuntimeError("Edge/Chrome bulunamadı")
        profil = os.path.join(os.environ.get("APPDATA", ""), "EAMusic", "browser-profile")
        _ac_ve_kucult([tarayici, "--app=" + AYAR["url"], "--user-data-dir=" + profil,
                       "--window-size=1280,800", "--no-first-run", "--no-default-browser-check"] + EDGE_BAYRAKLAR)
        return "Pencere açılıyor"

    klasor = AYAR["klasor"]
    betik = os.path.join(klasor, "scripts", "app-mode.js")
    if not os.path.isfile(betik):
        raise RuntimeError("EAMusic bulunamadı: " + betik)
    node = _node()
    if not node:
        raise RuntimeError("Node.js bulunamadı")
    _ac_ve_kucult([node, betik], cwd=klasor)     # .env, klasörden okunur
    log("applemusic: EAMusic başlatıldı")
    return "EAMusic açılıyor"


# ---- Oynatma komutları ----

@action("applemusic.komut")
def komut(cmd="", **args):
    # Komut listesi burada TUTULMAZ: geçerli komutlar EAMusic'in remote.js → COMMANDS kümesinde.
    # Bilinmeyen komutu EAMusic "Bilinmeyen komut" hatasıyla reddeder. Yeni özellik için NOTLAR.md.
    if not cmd or not isinstance(cmd, str):
        raise RuntimeError("Komut eksik")
    kod, govde = _istek("/api/remote/command", {"cmd": cmd, "args": args}, timeout=3)
    if kod is None:
        raise RuntimeError("EAMusic kapalı")
    if not govde.get("ok"):
        raise RuntimeError(govde.get("error") or ("HTTP %s" % kod))
    # Sayfa durumu ~200 ms içinde bildirir; taze durumu cevapla döndür ki telefon hemen güncellensin
    time.sleep(0.35)
    _yokla()
    return _ozet()
