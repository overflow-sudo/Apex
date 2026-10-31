"""Sistem sekmesi: CPU, GPU, RAM, VRAM kullanımı ve sıcaklıklar. Arka planda 2 sn'de bir ölçer."""
import re, threading, time, traceback
from core import hwmon, winstats
from core.registry import tab, on_start

GB = 1024 ** 3
latest = {}          # örnekleyici iş parçacığının son ölçümü
_info = {}


def _short(name):
    """'AMD Ryzen 7 5800X3D 8-Core Processor' -> 'Ryzen 7 5800X3D'"""
    n = re.sub(r"\(R\)|\(TM\)|\bCPU\b|@.*$|\d+-Core Processor|Processor|Graphics", "", name, flags=re.I)
    n = re.sub(r"^(AMD|Intel|NVIDIA)\s+", "", n.strip(), flags=re.I)
    return " ".join(n.split())


def _gpu_util(rows):
    """Görev Yöneticisi gibi: her motor türünün (3D, Compute, VideoDecode...) toplamı, en büyüğü."""
    groups = {}
    for name, v in rows:
        m = re.search(r"luid_(\w+?)_phys.*engtype_(\w+)", name or "")
        key = m.groups() if m else ("?", name)
        groups[key] = groups.get(key, 0.0) + v
    return min(100.0, max(groups.values())) if groups else None


def _sampler():
    try:
        pdh = winstats.Pdh()
        pdh.add("cpu", r"\Processor Information(_Total)\% Processor Utility", r"\Processor(_Total)\% Processor Time")
        pdh.add("gpu", r"\GPU Engine(*)\Utilization Percentage")
        pdh.add("vram", r"\GPU Adapter Memory(*)\Dedicated Usage")
        pdh.collect()
    except Exception:
        traceback.print_exc()
        pdh = None
    while True:
        time.sleep(2)
        d = {}
        try:
            if pdh:
                pdh.collect()
                cpu = pdh.value("cpu")
                d["cpu"] = min(100.0, cpu) if cpu is not None else None
                d["gpu"] = _gpu_util(pdh.array("gpu"))
                vr = pdh.array("vram")
                d["vram"] = max(v for _, v in vr) if vr else None
            d["ram_total"], d["ram_used"] = winstats.memory()
            d["uptime"] = winstats.uptime()
        except Exception:
            traceback.print_exc()
        d["temps"] = hwmon.read()
        latest.clear()
        latest.update(d)


@on_start
def start():
    if not winstats.IS_WIN:
        return
    try:
        _info["cpu"] = _short(winstats.cpu_name())
        g = winstats.gpu_info()
        _info["gpu"], _info["vram_total"] = _short(g[0]), g[1]
    except Exception:
        traceback.print_exc()
    threading.Thread(target=_sampler, daemon=True).start()


def _pct(v):
    return None if v is None else round(v)


def _uptime(s):
    if not s:
        return ""
    m = int(s // 60)
    d, h, m = m // 1440, (m // 60) % 24, m % 60
    return ("%d gün %d sa" % (d, h)) if d else ("%d sa %d dk" % (h, m))


def _temp_item(label, v, sub):
    return {"label": label, "value": "—" if v is None else "%d" % round(v), "unit": "°C" if v is not None else "",
            "pct": None if v is None else min(100, v), "hot": v is not None and v >= 85, "sub": sub}


@tab("system", "Sistem", icon="chip", order=40, poll=2)
def view():
    d = latest
    if not d:
        return [{"type": "text", "title": "Sistem", "text": "Ölçüm başlıyor…"}]
    temps = d.get("temps")
    lhm = "LibreHardwareMonitor kapalı" if temps is None else ""
    temps = temps or {}
    rt, ru = d.get("ram_total") or 0, d.get("ram_used") or 0
    vt, vu = _info.get("vram_total") or 0, d.get("vram")
    vram_pct = vu * 100.0 / vt if (vu is not None and vt) else None
    items = [
        {"label": "CPU", "value": _fmt(_pct(d.get("cpu"))), "unit": "%", "pct": d.get("cpu"),
         "hot": (d.get("cpu") or 0) >= 90, "sub": _info.get("cpu", "")},
        {"label": "GPU", "value": _fmt(_pct(d.get("gpu"))), "unit": "%", "pct": d.get("gpu"),
         "hot": (d.get("gpu") or 0) >= 95, "sub": _info.get("gpu", "")},
        {"label": "RAM", "value": "%.1f" % (ru / GB) if rt else "—", "unit": "/ %d GB" % round(rt / GB) if rt else "",
         "pct": ru * 100.0 / rt if rt else None, "hot": rt and ru * 100.0 / rt >= 90, "sub": "%d%% dolu" % (ru * 100 / rt) if rt else ""},
        {"label": "VRAM", "value": "%.1f" % (vu / GB) if vu is not None else "—",
         "unit": ("/ %d GB" % round(vt / GB)) if vt else "GB", "pct": vram_pct, "hot": (vram_pct or 0) >= 95,
         "sub": "%d%% dolu" % vram_pct if vram_pct is not None else ""},
        _temp_item("CPU sıcaklığı", temps.get("cpu"), lhm or _info.get("cpu", "")),
        _temp_item("GPU sıcaklığı", temps.get("gpu"), lhm or _info.get("gpu", "")),
    ]
    return [{"type": "stats", "title": "Açık kalma süresi · " + _uptime(d.get("uptime")), "fill": True, "items": items}]


def _fmt(v):
    return "—" if v is None else str(v)
