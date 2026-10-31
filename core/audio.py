"""Ses aygıtı kontrolü (SoundVolumeView.exe)."""
import time
from core.system import SVV, run, read_csv, match, cached, invalidate

RENDER, CAPTURE = "Render", "Capture"


@cached(2.0)
def _all_rows():
    return read_csv(SVV)


def list_devices(direction=RENDER, active_only=True):
    """[{id, name, device, default}] — active_only=False: takılı olmayanlar da (ekranı kapalı TV'nin HDMI sesi gibi)."""
    out = []
    for r in _all_rows():
        if r.get("Type") != "Device" or r.get("Direction") != direction:
            continue
        if active_only and r.get("Device State", "Active") != "Active":
            continue
        out.append({
            "id": r.get("Command-Line Friendly ID", ""),
            "name": r.get("Name", ""),
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
