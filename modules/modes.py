"""Modlar sekmesi: her mod büyük bir kart + gamepad ile otomatik Oyun modu.
Modlar config.PROFILES'ta, bu PC'nin aygıt seçimleri yerel/bu_pc.json'da (core/local.py, modules/wizard.py)."""
import ctypes, threading, time
import config
from core import audio, display, local, state, voicemeeter
from core.system import match
from core.registry import tab, action, status, on_start


def _lines(p):
    m = p["monitors"]
    screen = "Değişmez" if m == "keep" else "Hepsi" if m == "all" else ", ".join(local.label(x, "mon") for x in m)
    return [["EKRAN", screen], ["ÇIKIŞ", local.label(p["out"], "out") if p.get("out") else "Değişmez"],
            ["GİRİŞ", local.label(p["inp"], "inp") if p.get("inp") else "Değişmez"]]


def _matches(p):
    """Bu modun istediği durum şu an sistemde geçerli mi?"""
    for key, direction in (("out", audio.RENDER), ("inp", audio.CAPTURE)):
        if p.get(key):
            d = audio.current(direction)
            if not d or not match(p[key], d["name"], d["device"]):
                return False
    m = p["monitors"]
    if m == "keep":
        return True
    mons = display.list_monitors()
    active = set(x["name"] for x in mons if x["active"])
    if m == "all":
        return active == set(x["name"] for x in mons)
    wanted = set(x["name"] for k in m for x in [display.find(k, mons)] if x)
    return active == wanted


def current():
    """Sistemin şu anki durumuna uyan mod (elle değiştirildiyse None)."""
    for key, p in local.profiles().items():
        if _matches(p):
            return key
    return None


@tab("modes", "Modlar", icon="bolt", order=10)
def view():
    from modules import wizard
    if wizard.active():
        return wizard.view()
    if wizard.needs_setup():
        return wizard.intro()
    cur = current()
    profiles = local.profiles()
    # solda ana kart (o an çalan şarkı / oyun / kritik pil, yoksa saat), sağda tek sütun mod düğmeleri
    return [{"type": "hero", "fill": True,
             "mode": (profiles[cur]["title"] + " modu") if cur in profiles else "Özel ayar"}, {
        "type": "tiles",
        "layout": "stack",
        "side": True,
        "fill": True,
        "items": [{
            "title": p["title"],
            "sub": p.get("sub", ""),
            "icon": p.get("icon", "bolt"),
            "lines": _lines(p),
            "active": cur == key,
            "action": "mode.apply",
            "params": {"name": key},
        } for key, p in profiles.items()],
    }, {"type": "buttons", "items": [{"title": "Modları ayarla", "icon": "tune", "action": "wizard.start"}]}]


@action("mode.apply")
def apply(name):
    p = local.profiles()[name]
    with state.lock:
        # önce Voicemeeter ayarı (motor yeniden başlar), sonra ekranlar ve Windows varsayılan aygıtları
        if p.get("voicemeeter"):
            voicemeeter.load(p["voicemeeter"])
        display.apply(p["monitors"], p.get("primary"))
        changed = p["monitors"] != "keep"
        if p.get("out"):
            audio.set_by_key(p["out"], audio.RENDER, wait=12 if changed else 0)
        if p.get("inp"):
            audio.set_by_key(p["inp"], audio.CAPTURE)
        state.mode = name


@status(order=10)
def mode_chip():
    from modules import wizard
    if wizard.needs_setup():
        return "Mod · Ayarlanmadı"
    p = config.PROFILES.get(current())
    return "Mod · " + p["title"] if p else "Mod · Özel"


# ---------- Gamepad izleme (XInput) ----------
class _XState(ctypes.Structure):
    _fields_ = [("packet", ctypes.c_uint32), ("buttons", ctypes.c_uint16),
                ("lt", ctypes.c_ubyte), ("rt", ctypes.c_ubyte),
                ("lx", ctypes.c_short), ("ly", ctypes.c_short),
                ("rx", ctypes.c_short), ("ry", ctypes.c_short)]


def _watch():
    try:
        xin = ctypes.windll.xinput1_4
    except Exception:
        return
    while True:
        time.sleep(0.5)
        if state.mode == "tv":
            continue
        for i in range(4):
            s = _XState()
            if xin.XInputGetState(i, ctypes.byref(s)) == 0 and s.buttons != 0:
                try:
                    apply("tv")
                finally:
                    from core.system import invalidate
                    invalidate()
                break


@on_start
def warm_cache():
    """İlk telefon isteği araçları beklemesin diye ekran/ses listelerini açılışta doldur."""
    def go():
        try:
            display.list_monitors()
            audio.list_devices(audio.RENDER)
        except Exception as e:
            print("ön ısıtma hatası:", e)
    threading.Thread(target=go, daemon=True).start()


@on_start
def start_gamepad():
    if config.AUTO_GAMEPAD and "tv" in config.PROFILES:
        threading.Thread(target=_watch, daemon=True).start()
