"""
Sistem sekmesinin altında fare / klavye / kulaklık pil kartları. Kritik pil (config.BATTERY_LOW) üst çubuktaki
odak adasında en öne geçer (@focus, liste @extra("battery")'de de var). Kapalı/uykudaki cihazda son bilinen değer saatiyle gösterilir.
- Fare: Attack Shark, Xenta alıcısı 1D57:FA60. MI_02 COL03 (usage page 0x0A, 5 baytlık giriş raporu): alıcı kendiliğinden
  ~2-4 sn'de bir 03 xx 40 <durum> <seviye> gönderir (xx=0x10 modelinde seviye 0-10, diğerlerinde yüzde; SHARK_SCALE); durum 01 pil, 02 harici güç, 03 şarj oluyor. Bağlanınca bir kez
  sahte %100 geldiği için aynı değer iki kez üst üste gelince kabul edilir (daeoxide/attackshark-battery-windows).
  Sessizlik = fare kapalı/uykuda. Sürekli dinleyen ayrı iş parçacığı.
- Logitech (G915 TKL): G HUB'ın yerel websocket'i (core/ghub.py). G HUB kapalıysa "—". G HUB'da eşli ama
  kullanılmayan PRO X SUPERLIGHT de var; bağlı değilken fare kartına yazılmaz.
- HyperX Cloud III S Wireless (03F0:02CC): alıcının 0x01C0 HID koleksiyonu, rapor 0x0C.
  Pil sorgusu 0C 02 03 01 00 06 → cevabın 6. baytı yüzde (>100 = kulaklık kapalı). HeadsetControl #486'dan,
  bu PC'de doğrulandı (2026-10-31). Protokolde şarj bilgisi bilinmiyor.
"""
import threading, time, traceback
import config
from core import ghub
from core.procs import IS_WIN
from core.registry import extra, focus, on_start, section
from core.system import log

HYPERX = (0x03F0, 0x02CC, 0x01C0)
SHARK = (0x1D57, 0xFA60, 0x000A)
# 2. bayt modele göre değişiyor. X11 (0x55) ve 0xE5'te 4. bayt 0-100 yüzde. Emir'in faresinde (0x10) 0-10 seviye:
# yeni şarj olmuşken 10 geldi (2026-10-31). Listede olmayan modeller yüzde sayılır.
SHARK_SCALE = {0x10: 10}
INTERVAL = 60
LOW = getattr(config, "BATTERY_LOW", 15)

latest = {}      # "mouse"/"keyboard"/"headset" -> {name, pct, charging, hours, state, at}
_ghub_err = ""


def _hyperx():
    from core import hid
    dev = hid.find(*HYPERX)
    if not dev:
        return None                       # alıcı takılı değil
    with dev:
        if not dev.write(b"\x0c\x02\x03\x01\x00\x06"):
            return None
        end = time.time() + 1.5
        while time.time() < end:
            r = dev.read(0.5)
            if r and len(r) > 6 and r[:6] == b"\x0c\x02\x03\x01\x00\x06":
                pct = r[6]
                return {"name": "Cloud III S", "pct": pct if pct <= 100 else None,
                        "state": "ACTIVE" if pct <= 100 else "OFF", "charging": False, "hours": None}
    return None


def _set(kind, d):
    old = latest.get(kind)
    if d.get("pct") is None and old:
        # uykuda/kapalı: son bilinen değeri tut
        if old.get("pct") is not None:
            d["last"], d["last_at"] = old["pct"], old["at"]
        else:
            d["last"], d["last_at"] = old.get("last"), old.get("last_at")
    d["at"] = time.time()
    latest[kind] = d


def _poll():
    global _ghub_err
    while True:
        try:
            for d in ghub.batteries():
                kind = {"MOUSE": "mouse", "KEYBOARD": "keyboard", "HEADSET": "headset"}.get(d["type"])
                cur = latest.get(kind) or {}
                if kind == "mouse" and (d["state"] != "ACTIVE" or cur.get("src") == "shark" and cur.get("pct") is not None):
                    continue                  # Attack Shark kullanılıyor; eşli Logitech fare sadece bağlıyken
                if kind and (not cur or d["state"] == "ACTIVE" or cur.get("src") == "ghub"):
                    _set(kind, dict(d, src="ghub"))
            _ghub_err = ""
        except (OSError, ValueError) as e:
            if not _ghub_err:
                log("G HUB pil bilgisi okunamadı:", e)
            _ghub_err = "G HUB kapalı"
        except Exception:
            traceback.print_exc()
        try:
            h = _hyperx()
            if h:
                _set("headset", dict(h, src="hyperx"))
            elif (latest.get("headset") or {}).get("src") == "hyperx":
                latest.pop("headset", None)
        except Exception:
            traceback.print_exc()
        time.sleep(INTERVAL)


def _shark():
    from core import hid
    dev, pending, last = None, None, 0.0
    while True:
        try:
            if dev is None:
                dev = hid.find(*SHARK)
                if dev is None:
                    if (latest.get("mouse") or {}).get("src") == "shark":
                        latest.pop("mouse", None)          # alıcı çıkarıldı
                    time.sleep(15)
                    continue
                last = time.time()
            t = time.time()
            r = dev.read(2.0)
            now = time.time()
            if r is None and now - t < 0.2:                # zaman aşımı değil, hata (alıcı çıkarıldı)
                raise OSError("alıcı okunamadı")
            scale = SHARK_SCALE.get(r[1], 1) if r and len(r) >= 5 else 1
            if r and len(r) >= 5 and r[0] == 3 and r[2] == 0x40 and r[3] in (1, 2, 3) and r[4] * scale <= 100:
                key = (r[3], r[4])
                if key == pending:
                    _set("mouse", {"name": "Attack Shark", "pct": r[4] * scale, "state": "ACTIVE", "charging": r[3] != 1,
                                   "hours": None, "src": "shark"})
                pending, last = key, now
            elif now - last > 30:
                cur = latest.get("mouse") or {}
                if cur.get("src") == "shark" and cur.get("pct") is not None:
                    _set("mouse", {"name": "Attack Shark", "pct": None, "state": "NOT_CONNECTED", "src": "shark"})
                    pending = None
                if now - last > 300:                       # uzun sessizlikte alıcıyı yeniden aç
                    dev.close()
                    dev = None
        except Exception as e:
            log("Attack Shark:", e)
            if dev:
                dev.close()
            dev = None
            time.sleep(10)


@on_start
def start():
    if IS_WIN:
        threading.Thread(target=_poll, daemon=True).start()
        threading.Thread(target=_shark, daemon=True).start()


@extra("battery")
def critical():
    """Üst çubuk: pili kritik olan (şarj olmayan) cihazlar, en düşük önce. Yoksa None."""
    out = []
    for kind, label in (("mouse", "Fare"), ("keyboard", "Klavye"), ("headset", "Kulaklık")):
        d = latest.get(kind) or {}
        if d.get("pct") is not None and d["pct"] <= LOW and not d.get("charging"):
            out.append({"label": label, "pct": d["pct"]})
    return sorted(out, key=lambda x: x["pct"]) or None


@focus(priority=90)
def critical_focus():
    """Kritik pil her şeyin önüne geçer. Dokununca Sistem sekmesi (pil kartları)."""
    low = critical()
    if not low:
        return None
    first = low[0]
    others = " · ".join("%s %%%d" % (x["label"], x["pct"]) for x in low[1:])
    return {"kind": "battery", "title": "%s pili %%%d" % (first["label"], first["pct"]),
            "sub": others or "Şarja tak", "icon": "battery", "badge": "%%%d" % first["pct"], "alert": True,
            "tab": "system"}


def _hours(h):
    if not h:
        return ""
    m = int(round(h * 60))
    return "~%d sa %02d dk" % (m // 60, m % 60) if m >= 60 else "~%d dk" % m


def _item(kind, label):
    d = latest.get(kind)
    if not d:
        return {"label": label, "value": "—", "unit": "", "pct": None, "sub": _ghub_err if kind != "headset" else "bulunamadı"}
    pct = d.get("pct")
    if pct is None:
        sub = "uykuda" if d.get("state") == "NOT_CONNECTED" else "kapalı"
        if d.get("last") is not None:
            sub += " · son %%%d %s" % (d["last"], time.strftime("%H:%M", time.localtime(d.get("last_at") or 0)))
        return {"label": label, "value": "—", "unit": "", "pct": None, "sub": d.get("name", "") + " · " + sub}
    sub = "şarjda" if d.get("charging") else _hours(d.get("hours"))
    return {"label": label, "value": str(pct), "unit": "%", "pct": pct, "hot": pct <= LOW and not d.get("charging"),
            "sub": d.get("name", "") + (" · " + sub if sub else "")}


@section("system", order=60)
def view():
    if not IS_WIN:
        return None
    return {"type": "stats", "compact": True, "title": "Pil",
            "items": [_item("mouse", "Fare"), _item("keyboard", "Klavye"), _item("headset", "Kulaklık")]}
