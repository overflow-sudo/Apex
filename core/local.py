"""Bu bilgisayara özel ayarlar: yerel/bu_pc.json (Kur.bat bu klasöre dokunmaz, proje başka PC'ye taşınınca gitmez).
- "profiles": modların aygıt seçimleri {mod: {monitors, primary, out, inp}} — modules/wizard.py yazar.
  config.PROFILES modların adını/ikonunu ve varsayılan aygıtlarını tutar; buradaki seçimler onların üstüne yazılır.
- "labels": "<mon|out|inp>:<aygıt anahtarı>" -> arayüzde görünen ad.  "monitor_labels": DISPLAYn -> ekran adı (core/display.py).
- "pc": dosyayı yazan bilgisayarın adı. Klasör başka PC'ye kopyalanırsa ayarlar yok sayılır, sihirbaz yeniden açılır.
"""
import copy, json, os, socket, threading
import config
from core.system import BASE, log

PATH = os.path.join(BASE, "yerel", "bu_pc.json")
OLD_LABELS = os.path.join(BASE, "monitor_adlari.json")     # eski konum (2026-10-31 öncesi)
DEVICE_FIELDS = ("monitors", "primary", "out", "inp")

_lock = threading.RLock()
_data = None


def _pc():
    return os.environ.get("COMPUTERNAME") or socket.gethostname()


def _load():
    global _data
    if _data is None:
        d = {}
        try:
            with open(PATH, encoding="utf-8") as f:
                d = json.load(f)
        except Exception:
            pass
        if d.get("pc") not in (None, _pc()):
            log("yerel ayarlar başka bilgisayara ait (%s), yok sayıldı" % d.get("pc"))
            d = {}
        if not d.get("monitor_labels") and os.path.exists(OLD_LABELS):
            try:
                with open(OLD_LABELS, encoding="utf-8") as f:
                    d["monitor_labels"] = json.load(f)
                os.remove(OLD_LABELS)
            except Exception:
                pass
        _data = d
    return _data


def get(key, default=None):
    with _lock:
        return copy.deepcopy(_load().get(key, default))


def put(key, value):
    with _lock:
        d = _load()
        if d.get(key) == value:
            return
        d[key] = copy.deepcopy(value)
        d["pc"] = _pc()
        try:
            os.makedirs(os.path.dirname(PATH), exist_ok=True)
            tmp = PATH + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(d, f, ensure_ascii=False, indent=1)
            os.replace(tmp, PATH)
        except Exception as e:
            log("yerel ayarlar yazılamadı:", e)


def profiles():
    """config.PROFILES + bu PC'nin aygıt seçimleri."""
    out = copy.deepcopy(config.PROFILES)
    for k, v in (get("profiles") or {}).items():
        if k in out:
            out[k].update({f: v[f] for f in DEVICE_FIELDS if f in v})
    return out


def configured():
    return bool(get("profiles"))


def label(key, kind):
    """kind: "mon" | "out" | "inp" — aynı ses kartı çıkışta "Hoparlör", girişte "Hat" olabilir."""
    return (get("labels") or {}).get(kind + ":" + key, key)
