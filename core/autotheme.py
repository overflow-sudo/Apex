"""
Listede olmayan oyunlar için otomatik tema. Bir oyun için bir kez hesaplanır, cache/auto_themes.json'a yazılır.
  1) Steam appid (appmanifest'ten; yoksa Steam mağaza aramasıyla oyunun adından)
  2) SteamSpy etiketleri (oy sırasına göre: FPS, Racing, Survival...) -> efekt + vurgulu tuşlar
  3) Steam logo.png -> baskın renk -> vurgu + zemin
Ağ işleri arka planda yapılır; hazır olana kadar genel tema (UNKNOWN_GAME_THEME) kullanılır.
"""
import json, os, re, threading, time, traceback, urllib.parse, urllib.request
import config
from core import pngcolor
from core.system import BASE, log

CACHE = os.path.join(BASE, "cache", "auto_themes.json")
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"}
_opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
_lock = threading.Lock()
_pending = set()
_cache = None

FPS = list(getattr(config, "FPS_KEYS", ["W", "A", "S", "D", "SHIFT", "CTRL", "SPACE", "R", "1", "2", "3"]))
PRESETS = {
    "fps":      FPS + ["Q", "E", "F", "G", "C"],
    "drive":    ["W", "A", "S", "D", "SPACE", "SHIFT", "CTRL", "E", "L", "H", "UP", "DOWN", "LEFT", "RIGHT"],
    "strategy": ["Q", "W", "E", "R", "D", "F", "1", "2", "3", "4", "5", "SPACE", "TAB", "CTRL", "SHIFT"],
    "action":   ["W", "A", "S", "D", "SHIFT", "SPACE", "CTRL", "E", "R", "F", "Q", "TAB", "I", "M"],
    "basic":    ["W", "A", "S", "D", "SPACE", "SHIFT"],
}
# (etiketler, efekt, tuş seti, efektin varsayılan rengi) — oyunun etiketleri oy sırasıyla taranır, ilk eşleşen kazanır
RULES = [
    ({"racing", "driving", "automobile sim", "truck", "motorbike", "offroad"}, "road", "drive", "#f5b400"),
    ({"fps", "shooter", "hero shooter", "battle royale", "looter shooter", "arena shooter"}, "radar", "fps", "#ff4655"),
    ({"tactical", "military", "war", "stealth"}, "tactical", "fps", "#4aa8ff"),
    ({"cyberpunk", "sci-fi", "futuristic", "space", "robots", "hacking"}, "glitch", "action", "#fcee0a"),
    ({"horror", "psychological horror", "survival horror", "zombies", "post-apocalyptic", "western", "survival",
      "open world survival craft"}, "dust", "action", "#c8352c"),
    ({"strategy", "rts", "turn-based strategy", "grand strategy", "4x", "auto battler", "moba", "card game",
      "city builder", "deckbuilding", "tower defense", "turn-based tactics"}, "hex", "strategy", "#c8aa6e"),
    ({"rpg", "fantasy", "medieval", "action rpg", "crpg", "souls-like", "dragons", "magic", "open world"},
     "snow", "action", "#9fd4ff"),
]


def _load():
    global _cache
    if _cache is None:
        try:
            with open(CACHE, encoding="utf-8") as f:
                _cache = json.load(f)
        except Exception:
            _cache = {}
    return _cache


def _save():
    try:
        os.makedirs(os.path.dirname(CACHE), exist_ok=True)
        tmp = CACHE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(_cache, f, ensure_ascii=False, indent=1)
        os.replace(tmp, CACHE)
    except Exception as e:
        log("otomatik tema kaydedilemedi:", e)


def _get(url, timeout=8):
    req = urllib.request.Request(url, headers=UA)
    with _opener.open(req, timeout=timeout) as r:
        return r.read()


def _norm(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def search_appid(name):
    """Steam mağaza araması: adı en iyi eşleşen oyunun appid'i (Epic/Ubisoft/EA oyunları için)."""
    q = urllib.parse.quote(name)
    data = json.loads(_get("https://store.steampowered.com/api/storesearch/?term=%s&l=english&cc=TR" % q))
    want = _norm(name)
    for it in data.get("items") or []:
        got = _norm(it.get("name"))
        if got and (got == want or got.startswith(want) or want.startswith(got)):
            return str(it.get("id"))
    return None


def build(name, appid=None):
    """Ağ üzerinden temayı hesapla (yavaş; arka planda çağır)."""
    t = {"name": name, "short": name}
    if not appid:
        try:
            appid = search_appid(name)
        except Exception as e:
            log("Steam araması başarısız:", name, e)
    tags = []
    if appid:
        t["logo"] = "steam:" + appid
        try:
            j = json.loads(_get("https://steamspy.com/api.php?request=appdetails&appid=" + appid))
            tags = [k.lower() for k in (j.get("tags") or {})][:12]
            if j.get("name") and len(j["name"]) < 40:
                t["name"] = j["name"]
        except Exception as e:
            log("SteamSpy etiketleri alınamadı:", name, e)
    fx, keys, fallback = "tactical", "basic", config.UNKNOWN_GAME_THEME.get("accent", "#8fd3ff")
    for tag in tags:
        rule = next((r for r in RULES if tag in r[0]), None)
        if rule:
            fx, keys, fallback = rule[1], rule[2], rule[3]
            break
    color = None
    if appid:
        try:
            color = pngcolor.dominant(_get("https://cdn.cloudflare.steamstatic.com/steam/apps/%s/logo.png" % appid))
        except Exception as e:
            log("logo rengi çıkarılamadı:", name, e)
    accent = pngcolor.vivid(color) if color else fallback
    t.update({"accent": accent, "bg": pngcolor.dark_bg(accent), "fx": fx, "keys": PRESETS[keys],
              "tags": tags[:5], "auto": True, "made": int(time.time())})
    return t


def get(key, name, appid=None):
    """Önbellekte varsa temayı döndür; yoksa arka planda hesaplamayı başlat ve None döndür."""
    with _lock:
        c = _load()
        if key in c:
            return c[key]
        if key in _pending:
            return None
        _pending.add(key)

    def work():
        try:
            t = build(name, appid)
            with _lock:
                _load()[key] = t
                _save()
            log("otomatik tema: %s · %s · %s · etiketler %s" % (t["name"], t["accent"], t["fx"], ", ".join(t["tags"])))
            # elle düzenlemek istersen config.GAME_THEMES'e yapıştırılabilir satır
            log('  config için: "%s": {"name": %r, "exe": ["<exe adı>"], "logo": %r, "accent": %r, "bg": %r, "fx": %r, "keys": %r},'
                % (re.sub(r"\W+", "", key.split(":")[-1])[:16], t["name"], t.get("logo"), t["accent"], t["bg"], t["fx"], t["keys"]))
        except Exception:
            traceback.print_exc()
        finally:
            with _lock:
                _pending.discard(key)

    threading.Thread(target=work, daemon=True).start()
    return None
