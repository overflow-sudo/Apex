"""Ses aygıtı kontrolü (SoundVolumeView.exe)."""
import re, time
from core.system import SVV, run, read_csv, match, cached, invalidate

RENDER, CAPTURE = "Render", "Capture"


@cached(2.0)
def _all_rows():
    return read_csv(SVV)


_pins = {}      # Item ID -> sürücü pin adı (değişmez, bir kez okunur)


def _pin(item_id):
    """Uç noktanın sürücüdeki pin adı, örn. "...vbvoicemeetervaio2023_out6_wave_..." (kayıt defteri, MMDevices)."""
    if item_id not in _pins:
        val = ""
        m = re.search(r"\{[0-9a-fA-F-]+\}$", item_id or "")
        if m:
            try:
                import winreg
                key = r"SOFTWARE\Microsoft\Windows\CurrentVersion\MMDevices\Audio\Render\%s\Properties" % m.group(0)
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key) as k:
                    val = winreg.QueryValueEx(k, "{233164c8-1b2c-4c7d-bc68-b671687a2567},1")[0]
            except (OSError, ImportError):
                pass
        _pins[item_id] = val
    return _pins[item_id]


def list_devices(direction=RENDER, active_only=True):
    """[{id, name, device, default}] — active_only=False: takılı olmayanlar da (ekranı kapalı TV'nin HDMI sesi gibi).
    Voicemeeter Potato'nun 8 sanal girişi Windows'ta aynı adla ("Hoparlör", "VB-Audio Voicemeeter VAIO") ve aynı
    komut satırı kimliğiyle görünür; pin numarasından "Voicemeeter In N" adı verilir. Kimliği aynı olan aygıtlarda
    SoundVolumeView'a Item ID verilir, yoksa hep ilki seçilir."""
    rows = [r for r in _all_rows() if r.get("Type") == "Device" and r.get("Direction") == direction
            and (not active_only or r.get("Device State", "Active") == "Active")]
    ids = [r.get("Command-Line Friendly ID", "") for r in rows]
    out = []
    for r in rows:
        cid, name = r.get("Command-Line Friendly ID", ""), r.get("Name", "")
        if ids.count(cid) > 1 and r.get("Item ID"):
            cid = r["Item ID"]
        if direction == RENDER and "voicemeeter" in (r.get("Device Name") or "").lower():
            m = re.search(r"vaio\w*_out(\d+)_wave", _pin(r.get("Item ID")), re.I)
            if m:
                name = "Voicemeeter In " + m.group(1)
        out.append({
            "id": cid,
            "name": name,
            "device": " ".join((r.get("Device Name") or "").split()),
            "default": direction in (r.get("Default") or ""),
        })
    return out


def set_default(dev_id):
    """Konsol + multimedya + iletişim varsayılanı yapar."""
    run([SVV, "/SetDefault", dev_id, "all"])


def set_by_key(key, direction=RENDER, wait=0):
    """Ada göre bul ve varsayılan yap. HDMI sesi ekran açıldıktan birkaç saniye sonra
    belirdiği için 'wait' saniye boyunca tekrar dener."""
    end = time.time() + wait
    while True:
        for d in list_devices(direction):
            if match(key, d["name"], d["device"], d["id"]):
                set_default(d["id"])
                return True
        if time.time() >= end:
            return False
        time.sleep(1.5)
        invalidate()


def current(direction=RENDER):
    return next((d for d in list_devices(direction) if d["default"]), None)
