"""
Modları bu bilgisayarın ekran ve ses aygıtlarına göre ayarlama sihirbazı. Modlar sekmesinin içinde açılır
(modules/modes.py view() → wizard.view()). Seçimler yerel/bu_pc.json'a yazılır (core/local.py).
- Adımlar config.PROFILES'tan çıkar: ekran listesi olan mod → "hangi ekran açık kalsın", "all" + primary → "ana ekran",
  out/inp → "ses nereden çıksın / mikrofon hangisi". Her adımda "Değiştirme" seçeneği var. Tek ekranlı PC'de ekran adımı yok.
- Açılışta: kayıtlı seçim yoksa ve config.PROFILES'taki varsayılan aygıtların hepsi bu PC'de varsa (Emir'in PC'si)
  onlar sessizce kaydedilir; yoksa Modlar sekmesi "henüz ayarlanmadı" ekranını gösterir.
- Ses aygıtı anahtarı: aygıt adı ("2- " gibi ön ek atılmış, örn. "HyperX Cloud III S Wireless") o yönde tekse o, değilse Windows'taki ad
  ("4 - " ön eki atılmış, örn. "Smart M70F"), o da değilse aygıt kimliği.
"""
import threading
import config
from core import audio, display, local
from core.registry import action, on_start
from core.system import log, match
from modules.sound import _clean, _icon

_w = {"active": False, "step": 0, "choices": {}}
_checked = [False]

KEEP = "__keep__"
VERB = {"out": "Ses nereden çıksın?", "inp": "Mikrofon / ses girişi hangisi olsun?"}


def active():
    return _w["active"]


def needs_setup():
    return _checked[0] and not local.configured()


def _steps():
    s = []
    many = len(display.list_monitors()) > 1
    for key, p in config.PROFILES.items():
        m = p.get("monitors")
        if many and isinstance(m, list):
            s.append((key, "screen"))
        elif many and m == "all" and p.get("primary"):
            s.append((key, "primary"))
        for f in ("out", "inp"):
            if p.get(f):
                s.append((key, f))
    return s


def _mon_key(m, mons):
    if m["label"] != m["name"] and sum(1 for x in mons if x["label"] == m["label"]) == 1:
        return m["label"]
    return m["name"]


def _audio_key(d, devs):
    for k in (_clean(d["device"]), _clean(d["name"]), d["id"]):
        if k and sum(1 for x in devs if match(k, x["name"], x["device"], x["id"])) == 1:
            return k
    return d["id"]


# ---------- açılış: varsayılanlar bu PC'de var mı? ----------
def _defaults_present():
    mons = display.list_monitors()
    devs = {f: audio.list_devices(dr, active_only=False) for f, dr in (("out", audio.RENDER), ("inp", audio.CAPTURE))}
    for p in config.PROFILES.values():
        keys = (p["monitors"] if isinstance(p.get("monitors"), list) else []) + ([p["primary"]] if p.get("primary") else [])
        if any(not display.find(k, mons) for k in keys):
            return False
        for f in ("out", "inp"):
            if p.get(f) and not any(match(p[f], d["name"], d["device"], d["id"]) for d in devs[f]):
                return False
    return True


@on_start
def check():
    def go():
        try:
            if not local.configured() and _defaults_present():
                local.put("profiles", {k: {f: p.get(f) for f in local.DEVICE_FIELDS} for k, p in config.PROFILES.items()})
                log("modlar: config.PROFILES'taki aygıtlar bu PC'de bulundu, kaydedildi")
            elif not local.configured():
                log("modlar henüz bu bilgisayara göre ayarlanmadı (Modlar sekmesinde sihirbaz açılır)")
        except Exception as e:
            log("mod aygıt kontrolü:", e)
        _checked[0] = True
    threading.Thread(target=go, daemon=True).start()


# ---------- eylemler ----------
@action("wizard.start")
def start():
    prof = local.profiles()
    _w.update(active=True, step=0, choices={k: {f: p.get(f) for f in local.DEVICE_FIELDS} for k, p in prof.items()})
    _w["labels"] = local.get("labels") or {}


@action("wizard.cancel")
def cancel():
    _w["active"] = False


@action("wizard.back")
def back():
    _w["step"] = max(0, _w["step"] - 1)


@action("wizard.pick")
def pick(value, label=""):
    steps = _steps()
    if _w["step"] >= len(steps):
        return
    key, kind = steps[_w["step"]]
    c = _w["choices"][key]
    v = None if value == KEEP else value
    if kind == "screen":
        c["monitors"], c["primary"] = ([v], v) if v else ("keep", None)
    elif kind == "primary":
        c["primary"] = v
    else:
        c[kind] = v
    if v and label:
        _w["labels"][("mon" if kind in ("screen", "primary") else kind) + ":" + v] = label
    _w["step"] += 1


@action("wizard.enable_all")
def enable_all():
    display.enable_all()


@action("wizard.save")
def save():
    if len(display.list_monitors()) <= 1:          # tek ekran: modlar ekrana dokunmasın
        for c in _w["choices"].values():
            if isinstance(c.get("monitors"), list):
                c["monitors"], c["primary"] = "keep", None
    local.put("labels", _w["labels"])
    local.put("profiles", _w["choices"])
    _w["active"] = False
    log("modlar sihirbazla ayarlandı:", _w["choices"])


# ---------- görünüm ----------
def intro():
    return [
        {"type": "text", "title": "Hoş geldin",
         "text": "Modlar bu bilgisayara göre henüz ayarlanmadı. Oyun, Masaüstü ve Müzik modlarının hangi ekranı ve "
                 "hangi ses aygıtını kullanacağını bir kere seçmen yeterli. Birkaç dokunuş sürer, sonra istediğin "
                 "zaman bu sekmenin altından değiştirebilirsin."},
        {"type": "buttons", "items": [{"title": "Ayarlamaya başla", "icon": "tune", "action": "wizard.start"}]},
    ]


def _summary_lines(c):
    lab = lambda k, kind: _w["labels"].get(kind + ":" + k, k) if k else "Değişmez"
    m = c.get("monitors")
    screen = ("Değişmez" if m == "keep" else ("Hepsi · ana: " + lab(c["primary"], "mon") if c.get("primary") else "Hepsi") if m == "all" else
              ", ".join(lab(x, "mon") for x in m))
    return [["EKRAN", screen], ["ÇIKIŞ", lab(c.get("out"), "out")], ["GİRİŞ", lab(c.get("inp"), "inp")]]


def view():
    steps = _steps()
    n = len(steps)
    nav = [{"title": "Geri", "icon": "back", "action": "wizard.back"}] if _w["step"] > 0 else []
    nav.append({"title": "Vazgeç", "icon": "close", "action": "wizard.cancel"})
    if _w["step"] >= n:
        return [
            {"type": "text", "title": "Son adım · kontrol et",
             "text": "Her mod böyle çalışacak. Doğruysa Kaydet'e dokun. Yanlış bir şey varsa Geri ile düzelt."},
            {"type": "tiles", "fill": True, "items": [
                {"title": p["title"], "icon": p.get("icon", "bolt"), "lines": _summary_lines(_w["choices"][k])}
                for k, p in config.PROFILES.items()]},
            {"type": "buttons", "items": [{"title": "Kaydet", "icon": "check", "action": "wizard.save"}] + nav},
        ]
    key, kind = steps[_w["step"]]
    p, c = config.PROFILES[key], _w["choices"][key]
    head = "Adım %d / %d · %s modu" % (_w["step"] + 1, n, p["title"])
    if kind in ("screen", "primary"):
        mons = display.list_monitors()
        cur = c.get("primary") if kind == "primary" else (c["monitors"][0] if isinstance(c.get("monitors"), list) else None)
        text = ("%s moduna geçince hangi ekran açık kalsın? Diğer ekranlar kapanır." % p["title"] if kind == "screen" else
                "%s modunda bütün ekranlar açılır. Ana ekran hangisi olsun? (Görev çubuğu ve masaüstü simgeleri orada durur.)"
                % p["title"])
        items = []
        for m in mons:
            k = _mon_key(m, mons)
            items.append({"title": m["label"], "icon": "monitor", "active": bool(cur) and display.find(cur, [m]) is not None,
                          "sub": " · ".join(x for x in (m["res"], m["hz"] and m["hz"] + " Hz", "" if m["active"] else "şu an kapalı") if x),
                          "action": "wizard.pick", "params": {"value": k, "label": m["label"]}})
        if kind == "screen":
            items.append({"title": "Ekranlara dokunma", "sub": "Bu modda ekranlar olduğu gibi kalsın", "icon": "close",
                          "active": c.get("monitors") == "keep", "action": "wizard.pick", "params": {"value": KEEP}})
    else:
        direction = audio.RENDER if kind == "out" else audio.CAPTURE
        devs = audio.list_devices(direction)
        allk = audio.list_devices(direction, active_only=False)
        cur = c.get(kind)
        text = "%s modunda %s" % (p["title"], VERB[kind][0].lower() + VERB[kind][1:])
        if kind == "out" and any(not m["active"] for m in display.list_monitors()):
            text += " Aradığın aygıt listede yoksa (TV'nin sesi gibi) o ekran kapalı olabilir: aşağıdan ekranları aç."
            nav.insert(0, {"title": "Ekranları aç", "icon": "monitor", "action": "wizard.enable_all"})
        items = []
        for d in devs:
            k = _audio_key(d, allk)
            items.append({"title": _clean(d["name"]), "sub": _clean(d["device"]), "icon": _icon(d, direction),
                          "active": bool(cur) and match(cur, d["name"], d["device"], d["id"]),
                          "action": "wizard.pick", "params": {"value": k, "label": _clean(d["name"])}})
        items.append({"title": "Değiştirme", "sub": "Bu modda %s olduğu gibi kalsın" % ("ses" if kind == "out" else "mikrofon"),
                      "icon": "close", "active": not cur, "action": "wizard.pick", "params": {"value": KEEP}})
    return [
        {"type": "text", "title": head, "text": text},
        {"type": "list", "items": items},
        {"type": "buttons", "items": nav},
    ]
