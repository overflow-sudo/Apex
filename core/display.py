"""Monitör kontrolü (MultiMonitorTool.exe)."""
import time
from core import local
from core.system import MMT, run, read_csv, match, cached


@cached(2.0)
def list_monitors():
    """[{name, label, res, hz, active, primary}] — kapalı monitörün adı boş gelebildiği için
    görülen dostça adlar yerel/bu_pc.json'a kaydedilir (core/local.py)."""
    labels = local.get("monitor_labels") or {}
    out = []
    for r in read_csv(MMT):
        if (r.get("Disconnected") or "").strip().lower() == "yes":
            continue
        name = r.get("Name", "")
        friendly = (r.get("Monitor Name") or "").strip()
        if friendly:
            labels[name] = friendly
        out.append({
            "name": name,
            "label": labels.get(name, name),
            "res": (r.get("Resolution") or "").replace(" X ", "×"),
            "hz": r.get("Frequency", ""),
            "active": (r.get("Active") or "").strip().lower() == "yes",
            "primary": (r.get("Primary") or "").strip().lower() == "yes",
        })
    local.put("monitor_labels", labels)
    return out


def find(key, mons=None):
    for m in mons or list_monitors():
        if match(key, m["label"], m["name"]):
            return m
    return None


def apply(keys, primary=None):
    """keys: "keep" | "all" | ["ad", ...]. Sıra önemli: aç -> ana ekranı ayarla -> diğerlerini kapat
    (Windows ana ekranı kapatmayı reddeder)."""
    if keys == "keep":
        return
    mons = list_monitors()
    if keys == "all":
        wanted = [m["name"] for m in mons]
    else:
        wanted = [m["name"] for k in keys for m in [find(k, mons)] if m]
        if not wanted:
            return
    for m in mons:
        if m["name"] in wanted and not m["active"]:
            run([MMT, "/enable", m["name"]])
            time.sleep(2)
    p = find(primary, mons) if primary else None
    if not p and keys != "all":
        p = next((m for m in mons if m["name"] == wanted[0]), None)
    if p:
        run([MMT, "/SetPrimary", p["name"]])
        time.sleep(1)
    for m in mons:
        if m["name"] not in wanted and m["active"]:
            run([MMT, "/disable", m["name"]])


def only(name):
    apply([name], name)


def enable_all():
    apply("all")
