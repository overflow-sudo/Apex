"""
Maç skorları (Süper Lig + Şampiyonlar Ligi) — ESPN'in açık skor servisi, anahtar gerekmez.
  - site.api.espn.com Türkiye'den "Access Denied" veriyor; site.web.api.espn.com çalışıyor (2026-10-25'te doğrulandı).
  - ?dates=YYYYMMDD tek gün çalışıyor, tarih ARALIĞI (A-B) 400 veriyor -> günleri tek tek soruyoruz.
  - Takım logoları a.espncdn.com'dan; telefon doğrudan yükler.
Arka planda: 5 dk'da bir dün..+3 gün, canlı maç varken 30 sn'de bir sadece bugün.
Sağ üstteki skor kutusu @extra("score") ile gelir; dokununca açılan liste "football.list" eylemiyle.
"""
import json, threading, time, traceback, urllib.request
from datetime import datetime, timedelta, timezone
import config
from core.system import log
from core.registry import action, extra, on_start

BASE = "https://site.web.api.espn.com/apis/site/v2/sports/soccer/"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
      "Accept": "application/json"}
_opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
_cfg = getattr(config, "FOOTBALL", {})
LEAGUES = _cfg.get("leagues", [("tur.1", "Süper Lig", "SL"), ("uefa.champions", "Şampiyonlar Ligi", "ŞL")])
FAVORITES = [f.lower() for f in _cfg.get("favorites", [])]

# ESPN adlarını Türkçeleştir + bilinen kısaltmalar (bilinmeyenler ESPN'deki gibi kalır)
TR_TEAMS = {
    "galatasaray": ("Galatasaray", "GS"), "fenerbahce": ("Fenerbahçe", "FB"), "besiktas": ("Beşiktaş", "BJK"),
    "trabzonspor": ("Trabzonspor", "TS"), "istanbul basaksehir": ("Başakşehir", "İBFK"), "basaksehir": ("Başakşehir", "İBFK"),
    "goztepe": ("Göztepe", "GÖZ"), "genclerbirli": ("Gençlerbirliği", "GB"), "genclerbirligi": ("Gençlerbirliği", "GB"),
    "kasimpasa": ("Kasımpaşa", "KAS"), "kayserispor": ("Kayserispor", "KAY"), "konyaspor": ("Konyaspor", "KON"),
    "alanyaspor": ("Alanyaspor", "ALA"), "antalyaspor": ("Antalyaspor", "ANT"), "rizespor": ("Rizespor", "RİZ"),
    "caykur rizespor": ("Rizespor", "RİZ"), "samsunspor": ("Samsunspor", "SAM"), "sivasspor": ("Sivasspor", "SİV"),
    "eyupspor": ("Eyüpspor", "EYÜ"), "gaziantep fk": ("Gaziantep FK", "GFK"), "kocaelispor": ("Kocaelispor", "KOC"),
    "karagumruk": ("Karagümrük", "FKG"), "fatih karagumruk": ("Karagümrük", "FKG"), "corum fk": ("Çorum FK", "ÇOR"),
    "çorum fk": ("Çorum FK", "ÇOR"), "bodrum fk": ("Bodrum FK", "BOD"), "hatayspor": ("Hatayspor", "HAT"),
    "adana demirspor": ("Adana Demirspor", "ADS"), "amedspor": ("Amedspor", "AMD"), "erzurumspor": ("Erzurumspor", "ERZ"),
    "istanbul bb": ("Başakşehir", "İBFK"), "gaziantep": ("Gaziantep FK", "GFK"), "erzurum": ("Erzurumspor", "ERZ"),
    "erzurum bb": ("Erzurumspor", "ERZ"), "amed sfk": ("Amedspor", "AMD"),
}
TURKISH = {"galatasaray", "fenerbahce", "besiktas", "trabzonspor", "istanbul basaksehir", "basaksehir", "istanbul bb"}
DAYS = ["Pzt", "Sal", "Çar", "Per", "Cum", "Cmt", "Paz"]

_lock = threading.Lock()
_matches = {}           # id -> maç
_error = ""


def _key(name):
    return " ".join((name or "").lower().replace("-", " ").split())


def _team(c):
    t = c.get("team") or {}
    raw = t.get("shortDisplayName") or t.get("displayName") or "?"
    name, abbr = TR_TEAMS.get(_key(raw)) or TR_TEAMS.get(_key(t.get("displayName"))) or (raw, t.get("abbreviation") or raw[:3].upper())
    return {"n": name, "a": abbr, "l": t.get("logo") or "", "s": c.get("score") or "0", "k": _key(raw)}


def _when(dt):
    now = datetime.now().astimezone()
    d = (dt.date() - now.date()).days
    hm = dt.strftime("%H:%M")
    if d == 0:
        return hm
    if d == 1:
        return "Yarın " + hm
    if d == -1:
        return "Dün " + hm
    return DAYS[dt.weekday()] + " " + hm


def _parse(ev, lg):
    comp = ev["competitions"][0]
    cs = comp["competitors"]
    home = next((c for c in cs if c.get("homeAway") == "home"), cs[0])
    away = next((c for c in cs if c.get("homeAway") == "away"), cs[-1])
    st = ev.get("status") or {}
    ty = st.get("type") or {}
    state = ty.get("state") or "pre"
    dt = datetime.strptime(ev["date"].replace("Z", ""), "%Y-%m-%dT%H:%M").replace(tzinfo=timezone.utc).astimezone()
    short = ty.get("shortDetail") or ""
    if state == "in":
        clock = {"HT": "İY"}.get(short, st.get("displayClock") or short)
    elif state == "post":
        clock = {"FT": "MS", "AET": "UZ", "FT-Pens": "PEN"}.get(short, "MS")
    else:
        clock = _when(dt)
    if "POSTPONED" in (ty.get("name") or "") or short.lower().startswith("postp"):
        clock, state = "Ertelendi", "post"
    h, a = _team(home), _team(away)
    fav = any(f in (h["k"], a["k"], h["n"].lower(), a["n"].lower(), h["a"].lower(), a["a"].lower()) for f in FAVORITES)
    tr = h["k"] in TURKISH or a["k"] in TURKISH
    return {"id": ev["id"], "lg": lg[2], "lgname": lg[1], "ts": dt.timestamp(), "state": state, "clock": clock,
            "live": state == "in", "fav": fav, "tr": tr, "home": h, "away": a}


def _fetch(lg_code, day):
    # day=None: ESPN'in "güncel hafta"sı (ŞL'de son/sıradaki maç haftası; maçlar seyrek olduğu için gerekli)
    url = BASE + lg_code + "/scoreboard" + ("?dates=" + day.strftime("%Y%m%d") if day else "")
    req = urllib.request.Request(url, headers=UA)
    with _opener.open(req, timeout=10) as r:
        return json.loads(r.read().decode("utf-8", "replace")).get("events") or []


def _refresh(days, with_current=False):
    global _error
    got = {}
    for lg in LEAGUES:
        for d in ([None] if with_current else []) + list(days):
            for ev in _fetch(lg[0], d):
                try:
                    m = _parse(ev, lg)
                    got[m["id"]] = m
                except Exception:
                    traceback.print_exc()
    with _lock:
        _matches.update(got)
        cutoff = time.time() - 8 * 86400
        for k in [k for k, m in _matches.items() if m["ts"] < cutoff]:
            del _matches[k]
    _error = ""


def _loop():
    global _error
    last_full = 0.0
    while True:
        wait = 300
        try:
            today = datetime.now().date()
            if time.time() - last_full > 300:
                _refresh([today + timedelta(days=i) for i in range(-1, 4)], with_current=True)
                last_full = time.time()
            with _lock:
                ms = list(_matches.values())
            soon = any(m["state"] == "pre" and 0 < m["ts"] - time.time() < 20 * 60 for m in ms)
            if any(m["live"] for m in ms) or soon:
                wait = 30
                _refresh([today])
        except Exception as e:
            if not _error:
                log("maç skorları alınamadı:", e)
            _error = str(e)
            wait = 120
        time.sleep(wait)


@on_start
def start():
    if _cfg.get("enabled", True):
        threading.Thread(target=_loop, daemon=True).start()


def _rank(m):
    # favori > Türk takımı > Süper Lig > diğer
    return (0 if m["fav"] else 1, 0 if m["tr"] else 1, 0 if m["lg"] == "SL" else 1, m["ts"])


def _compact(m):
    return {"id": m["id"], "lg": m["lg"], "live": m["live"], "state": m["state"], "clock": m["clock"],
            "h": [m["home"]["a"], m["home"]["s"], m["home"]["l"]], "a": [m["away"]["a"], m["away"]["s"], m["away"]["l"]]}


@extra("score")
def featured():
    now = time.time()
    with _lock:
        ms = list(_matches.values())
    if not ms:
        return None
    live = sorted([m for m in ms if m["live"]], key=_rank)
    if live:
        pick = live[:6]
    else:
        fav = sorted([m for m in ms if m["fav"] and -3 * 3600 < m["ts"] - now < 48 * 3600], key=lambda m: m["ts"])
        recent = sorted([m for m in ms if m["state"] == "post" and 0 < now - m["ts"] < 3.5 * 3600], key=_rank)
        today = datetime.now().date()
        upcoming = sorted([m for m in ms if m["state"] == "pre" and 0 < m["ts"] - now < 30 * 3600],
                          key=lambda m: (0 if m["fav"] else 1,
                                         0 if datetime.fromtimestamp(m["ts"]).date() == today else 1,
                                         0 if m["tr"] else 1, m["ts"]))
        pick = (fav or recent[:2] + upcoming[:2] or upcoming[:3])[:4]
    if not pick:
        return None
    return {"items": [_compact(m) for m in pick], "live": len(live)}


def _day(ts):
    dt = datetime.fromtimestamp(ts)
    d = (dt.date() - datetime.now().date()).days
    return {0: "Bugün", 1: "Yarın", -1: "Dün"}.get(d, DAYS[dt.weekday()] + " " + dt.strftime("%d.%m"))


@action("football.list")
def full_list():
    with _lock:
        ms = list(_matches.values())
    out = []
    for code, name, short in LEAGUES:
        lm = sorted([m for m in ms if m["lg"] == short], key=lambda m: m["ts"])
        out.append({"name": name, "short": short, "matches": [
            {"clock": m["clock"], "live": m["live"], "state": m["state"], "fav": m["fav"], "day": _day(m["ts"]),
             "home": {k: m["home"][k] for k in "nals"}, "away": {k: m["away"][k] for k in "nals"}} for m in lm]})
    return {"leagues": out, "error": _error}
