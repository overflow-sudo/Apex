"""
Sıcaklıklar — LibreHardwareMonitor'ün web sunucusundan (Options → Remote Web Server → Run).
Windows'un kendisi CPU/GPU sıcaklığını ek sürücü olmadan vermiyor, bu yüzden LHM kullanıyoruz.
Çalışmıyorsa read() None döner ve arayüz "—" gösterir.
"""
import json, urllib.request
import config

_opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

CPU_PREF = ("package", "tctl", "tdie", "core average", "cpu")
GPU_PREF = ("gpu core", "core", "edge")


def _num(v):
    try:
        return float(str(v).split()[0].replace(",", "."))
    except Exception:
        return None


def _kind(node):
    img = (node.get("ImageURL") or "").lower()
    hid = (node.get("HardwareId") or "").lower()
    if "cpu" in img or hid.startswith("/amdcpu") or hid.startswith("/intelcpu"):
        return "cpu"
    if any(x in img for x in ("ati", "amd", "nvidia", "gpu")) or hid.startswith("/gpu"):
        return "gpu"
    return None


def _walk(node, kind, out):
    kind = _kind(node) or kind
    kids = node.get("Children") or []
    val = node.get("Value") or ""
    if kind and not kids and "°C" in val:
        n = _num(val)
        if n is not None and n > 0:
            out[kind].append(((node.get("Text") or "").lower(), n))
    for c in kids:
        _walk(c, kind, out)


def _pick(items, prefs):
    for p in prefs:
        for name, v in items:
            if p in name:
                return v
    return max((v for _, v in items), default=None)


def read():
    """{'cpu': °C | None, 'gpu': °C | None} ya da LHM yoksa None."""
    try:
        with _opener.open(getattr(config, "LHM_URL", "http://127.0.0.1:8085/data.json"), timeout=0.7) as r:
            data = json.loads(r.read().decode("utf-8", "replace"))
    except Exception:
        return None
    out = {"cpu": [], "gpu": []}
    _walk(data, None, out)
    return {"cpu": _pick(out["cpu"], CPU_PREF), "gpu": _pick(out["gpu"], GPU_PREF)}
