"""
Klavye ışığı (Logitech G915 vb.) aktif temayı izler:
  oyun teması varsa -> tüm klavye vurgu rengi (KEYBOARD_BRIGHTNESS), oyunun "keys" tuşları ikinci renkle
  tema yoksa        -> SDK bırakılır, G HUB'daki kendi profilin geri gelir
SDK çağrıları tek bir iş parçacığından yapılır. Tema sekmesine bir bölüm ekler (@section).
"""
import threading, time
import config
from core import logiled, procs
from core.system import log
from core.registry import action, on_start, section
from modules import games

_enabled = bool(getattr(config, "KEYBOARD_LIGHTING", True))
_status = "Başlıyor…"
_wake = threading.Event()


def _paint(t):
    """Önce tüm cihazlar ana renge, sonra (tuş başına RGB moduna geçip) vurgulu tuşlar.
    G HUB komutları kendi sırasıyla işliyor: ana renk komutu tuşları ezmesin diye araya bekleme
    koyuyoruz ve tuşları iki tur boyuyoruz. Dönen (başarılı, toplam) Tema sekmesinde görünür."""
    base = t.get("accent") or "#ffffff"
    key_color = t.get("key_color") or t.get("accent2") or "#ffffff"
    if key_color.lower() == base.lower():
        key_color = "#ffffff"
    keys = t.get("keys") or []
    effect = getattr(config, "KEYBOARD_KEY_EFFECT", "static")
    logiled.stop_effects()
    logiled.set_all(base, getattr(config, "KEYBOARD_BRIGHTNESS", 60))
    time.sleep(0.35)
    logiled.set_target(logiled.DEVICE_PERKEY)
    ok = 0
    for rnd in range(2):
        ok = 0
        for k in keys:
            if effect == "pulse":
                good = logiled.pulse_key(k, key_color, base)
            else:
                good = logiled.set_key(k, key_color, 100)
            ok += 1 if good else 0
            time.sleep(0.004)
        if rnd == 0:
            time.sleep(0.6)
    logiled.set_target(logiled.DEVICE_ALL)
    return ok, len(keys)


def _loop():
    global _status
    applied, painted_at, inited, next_try = None, 0.0, False, 0.0
    while True:
        _wake.wait(1.5)
        _wake.clear()
        try:
            t = games.current() if _enabled else None
            if t and t.get("lighting") is False:      # oyunun kendi Logitech ışığı varsa ona bırak
                t = None
            if not t:
                if inited:
                    logiled.shutdown()
                    inited = False
                    log("klavye ışığı G HUB'a bırakıldı")
                applied = None
                _status = "Kapalı" if not _enabled else "Oyun bekleniyor · G HUB profili aktif"
                continue
            if not inited:
                if time.time() < next_try:
                    continue
                inited = logiled.init()
                if not inited:
                    _status = logiled.last_error or "G HUB'a bağlanılamadı"
                    next_try = time.time() + 30
                    continue
                time.sleep(1.0)                         # SDK hazır olsun (G HUB'a bağlanması ~1 sn)
            # tema değiştiyse ya da G HUB profili geri almış olabilir diye dakikada bir yeniden boya
            if t.get("id") != applied or time.time() - painted_at > 60:
                ok, total = _paint(t)
                if t.get("id") != applied:
                    log("klavye ışığı: %s · %d/%d tuş · yöntem %s" % (t.get("name"), ok, total, logiled.key_method))
                applied, painted_at = t.get("id"), time.time()
                _status = "%s · %d/%d tuş" % (t.get("short") or t.get("name") or "", ok, total)
        except Exception as e:
            _status = "Hata: %s" % e
            log("klavye ışığı hatası:", e)
            inited = False
            next_try = time.time() + 30


@on_start
def start():
    if procs.IS_WIN:
        threading.Thread(target=_loop, daemon=True).start()
    else:
        globals()["_status"] = "Sadece Windows'ta"


@section("theme", order=20)
def light_section():
    return {"type": "buttons", "title": ("Klavye ışığı · " + _status) if _enabled else None, "items": [
        {"title": "Klavye ışığı", "icon": "keyboard", "on": _enabled, "action": "lighting.toggle"},
    ]}


@action("lighting.toggle")
def toggle():
    global _enabled
    _enabled = not _enabled
    _wake.set()
