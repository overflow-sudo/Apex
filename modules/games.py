"""
Oyuna göre tema. 3 sn'de bir:
  1) öndeki pencerenin süreci config.GAME_THEMES'te varsa -> o tema
  2) öndeki süreç Steam/Epic/Xbox oyun klasöründense -> UNKNOWN_GAME_THEME + klasör adı
  3) listedeki bir oyun arka planda açıksa (alt-tab) -> o tema
  4) yoksa siyah-beyaz. Oyun algılanmayınca 15 sn bekler (kısa kesintilerde tema titremesin).
Tema sekmesinden elle önizleme yapılabilir (otomatiğe dönene kadar sabit kalır).
"""
import glob, os, re, threading, time, traceback
import config
from core import autotheme, procs
from core.system import log
from core.registry import tab, action, status, extra, focus, section, on_start

_lock = threading.Lock()
_auto = None            # algılanan tema (dict) ya da None
_override = None        # Tema sekmesinden seçilen: None = otomatik, "" = siyah-beyaz, "<id>" = oyun
_last_seen = (None, 0.0)   # son algılanan oyun ve zamanı: kısa kesintilerde tema hemen gitmesin
HOLD = 15
_fx = bool(getattr(config, "THEME_FX", False))   # oyunun hareketli arka plan efekti (Tema sekmesinden açılır)

# Oyun başlatıcılarının kurulum klasörleri: ...\<başlatıcı>\<Oyun Adı>\...
_LAUNCHER_DIRS = re.compile(
    r"\\(?:steamapps\\common|Epic Games|XboxGames|Riot Games|Ubisoft Game Launcher\\games|Ubisoft\\games"
    r"|EA Games|GOG Galaxy\\Games|GOG Games|Rockstar Games|Amazon Games\\Library)\\([^\\]+)\\", re.I)
# bu klasör adları oyun değil, başlatıcının kendisi
_NOT_GAMES = {"launcher", "riot client", "social club", "ea desktop", "ea app", "galaxy", "ubisoft connect",
              "steamworks shared", "directx", "redist", "redistributables"}
_EXE = {}
for _id, _t in config.GAME_THEMES.items():
    for _e in _t.get("exe", []):
        _EXE[_e.lower()] = _id


def logo_url(logo):
    """config'teki "steam:<appid>" kısaltmasını gerçek adrese çevirir. Telefon logoyu doğrudan yükler."""
    if not logo:
        return None
    if logo.startswith("steam:"):
        return "https://cdn.cloudflare.steamstatic.com/steam/apps/%s/logo.png" % logo[6:]
    return logo


_appid_cache = {}


def _steam_appid(exe_path):
    """.../steamapps/common/<Klasör>/oyun.exe -> steamapps/appmanifest_<id>.acf içinde installdir'i eşleşen id."""
    m = re.search(r"^(.*\\steamapps)\\common\\([^\\]+)\\", exe_path, re.I)
    if not m:
        return None
    key = (m.group(1).lower(), m.group(2).lower())
    if key in _appid_cache:
        return _appid_cache[key]
    appid = None
    for f in glob.glob(os.path.join(m.group(1), "appmanifest_*.acf")):
        try:
            with open(f, encoding="utf-8", errors="replace") as fh:
                txt = fh.read()
            d = re.search(r'"installdir"\s+"([^"]+)"', txt)
            if d and d.group(1).lower() == key[1]:
                appid = re.search(r'"appid"\s+"(\d+)"', txt).group(1)
                break
        except Exception:
            pass
    _appid_cache[key] = appid
    return appid


def _theme(id_):
    t = dict(config.GAME_THEMES[id_])
    t["id"] = id_
    return t


def _pretty(folder):
    n = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", folder)        # TheLongDark -> The Long Dark
    n = re.sub(r"[_\-]+", " ", n).strip()
    return n.upper() if len(n) <= 4 else n


def detect():
    t = _detect_now()
    global _last_seen
    if t:
        _last_seen = (t, time.time())
        return t
    last, when = _last_seen
    return last if last and time.time() - when < HOLD else None


# Program adından tanınamayan oyunlar için dış algılayıcılar (örn. Minecraft -> javaw.exe; mod üzerinden).
# Her biri tema id'si (config.GAME_THEMES anahtarı) ya da None döndürür.
DETECTORS = []


def detector(fn):
    DETECTORS.append(fn)
    return fn


def _detect_now():
    for fn in DETECTORS:
        try:
            id_ = fn()
            if id_ and id_ in config.GAME_THEMES:
                return _theme(id_)
        except Exception:
            pass
    plist = procs.processes()
    fg = procs.foreground_pid()
    fname = (plist.get(fg) or "").lower() if fg else ""
    if fname in _EXE:
        return _theme(_EXE[fname])
    if fg and fname:
        path = procs.image_path(fg) or ""
        m = _LAUNCHER_DIRS.search(path)
        if m and m.group(1).lower() not in _NOT_GAMES:
            folder = m.group(1)
            key = "auto:" + folder.lower()
            appid = _steam_appid(path)
            # otomatik tema: logodan renk + Steam etiketlerinden efekt/tuşlar (ilk seferde arka planda hesaplanır)
            auto = autotheme.get(key, _pretty(folder), appid)
            t = dict(config.UNKNOWN_GAME_THEME)
            t["name"] = t["short"] = _pretty(folder)
            if appid:
                t["logo"] = "steam:" + appid
            if auto:
                t.update(auto)
            t["id"] = key
            return t
    for name in plist.values():
        id_ = _EXE.get(name.lower())
        if id_:
            return _theme(id_)
    return None


def _loop():
    global _auto
    while True:
        try:
            t = detect()
            with _lock:
                if (t or {}).get("id") != (_auto or {}).get("id"):
                    log("tema:", (t or {}).get("name", "siyah-beyaz"))
                _auto = t
        except Exception:
            traceback.print_exc()
        time.sleep(3)


@on_start
def start():
    if procs.IS_WIN:
        threading.Thread(target=_loop, daemon=True).start()


def current():
    with _lock:
        if _override is None:
            t = _auto
        elif _override == "":
            t = None
        else:
            t = _theme(_override) if _override in config.GAME_THEMES else None
    if t and not _fx:
        t = dict(t, fx="")
    return t


@extra("theme")
def theme_payload():
    t = current()
    if not t:
        return None
    d = {k: t.get(k) for k in ("id", "name", "short", "accent", "accent2", "bg", "fg", "fx", "logo_white")}
    d["logo"] = logo_url(t.get("logo"))
    return d


@status(order=5)
def playing_chip():
    with _lock:
        t = _auto
    # İngilizce ad Türkçe büyük harfe çevrilmesin (TEAMFİGHT olmasın) diye lang="en" ile ayrı parça
    # kind: odak adası bu oyunu zaten gösteriyorsa arayüz bu etiketi gizler
    return {"text": "Oynuyor", "value": t.get("short") or t["name"], "lang": "en", "kind": "game"} if t else None


@focus(priority=70)
def playing_focus():
    with _lock:
        t = _auto
    if not t:
        return None
    return {"kind": "game", "title": t.get("short") or t["name"], "sub": "Oynuyor", "lang": "en", "icon": "gamepad",
            "img": logo_url(t.get("logo")), "img_white": t.get("logo_white", False), "live": True}


@tab("theme", "Tema", icon="palette", order=60)
def view():
    with _lock:
        ov, auto = _override, _auto
    cur = current()
    auto_sub = ("Şu an: " + (auto.get("short") or auto["name"])) if auto else "Oyunla değişir"
    items = [
        {"title": "Otomatik", "sub": auto_sub, "icon": "bolt", "active": ov is None,
         "action": "theme.set", "params": {"id": None}},
        {"title": "Sade", "sub": "Renk değişmez", "icon": "monitor", "active": ov == "",
         "action": "theme.set", "params": {"id": ""}},
    ]
    for id_, t in config.GAME_THEMES.items():
        if t.get("preview") is False:
            continue
        items.append({"title": t.get("short") or t["name"], "sub": t["name"], "lang": "en", "icon": "gamepad",
                      "img": logo_url(t.get("logo")), "img_white": t.get("logo_white", False),
                      "active": ov == id_, "action": "theme.set", "params": {"id": id_}})
    name = (cur or {}).get("short") or (cur or {}).get("name") or "Sade"
    title = "Şu an · " + name + ("" if ov is None else " (önizleme)")
    return [{"type": "tiles", "title": title, "fill": True, "items": items}]


@section("theme", order=5)
def fx_section():
    return {"type": "buttons", "items": [
        {"title": "Oyun efekti", "icon": "layers", "on": _fx, "action": "theme.fx"}]}


@action("theme.fx")
def toggle_fx():
    global _fx
    _fx = not _fx


@action("theme.set")
def set_theme(id=None):
    global _override
    with _lock:
        _override = id
