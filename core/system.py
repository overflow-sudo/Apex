"""Ortak yardımcılar: komut çalıştırma, NirSoft CSV okuma, ad eşleştirme, kısa önbellek."""
import csv, functools, os, subprocess, tempfile, threading, time

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MMT = os.path.join(BASE, "MultiMonitorTool.exe")
SVV = os.path.join(BASE, "SoundVolumeView.exe")

_NO_WINDOW = 0x08000000 if os.name == "nt" else 0


def run(args, timeout=30):
    """Konsol penceresi açmadan bir program çalıştırır."""
    try:
        return subprocess.run(args, capture_output=True, creationflags=_NO_WINDOW, timeout=timeout)
    except Exception as e:
        print("run hatası:", args, e)
        return None


def read_csv(tool, flag="/scomma"):
    """NirSoft aracını '/scomma <dosya>' ile çalıştırıp CSV satırlarını döndürür."""
    fd, path = tempfile.mkstemp(suffix=".csv")
    os.close(fd)
    try:
        run([tool, flag, path])
        with open(path, encoding="utf-8-sig", errors="replace", newline="") as f:
            return list(csv.DictReader(f))
    finally:
        try:
            os.remove(path)
        except OSError:
            pass


def norm(s):
    """Küçük harf + fazla boşlukları teke indir ('USB AUDIO  CODEC' -> 'usb audio codec')."""
    return " ".join(str(s or "").lower().split())


def match(key, *texts):
    k = norm(key)
    return bool(k) and any(k in norm(t) for t in texts)


# ---- önbellek: "bayat ama hızlı" ----
# Süresi dolan değer hemen döndürülür, yenisi arka planda hesaplanır. Böylece /api/ui hiçbir zaman
# MultiMonitorTool/SoundVolumeView'ın bitmesini beklemez (oyun sırasında bunlar saniyeler sürebiliyor
# ve telefon zaman aşımına düşüp "kapalı" ekranını gösteriyordu). Değer max_stale'den eskiyse ya da
# invalidate() çağrıldıysa (bir eylem sistemi değiştirdi) beklenip taze değer alınır.
_cache = {}
_refreshing = set()
_cache_lock = threading.Lock()


def _refresh(key, fn, args):
    try:
        val = fn(*args)
        with _cache_lock:
            _cache[key] = (time.time(), val)
    except Exception as e:
        print("önbellek yenileme hatası:", key[1], e)
    finally:
        with _cache_lock:
            _refreshing.discard(key)


def cached(ttl=2.0, max_stale=30.0):
    def deco(fn):
        @functools.wraps(fn)
        def wrapper(*args):
            key = (fn.__module__, fn.__name__, args)
            now = time.time()
            with _cache_lock:
                hit = _cache.get(key)
                if hit:
                    age = now - hit[0]
                    if age < ttl:
                        return hit[1]
                    if age < max_stale:
                        if key not in _refreshing:
                            _refreshing.add(key)
                            threading.Thread(target=_refresh, args=(key, fn, args), daemon=True).start()
                        return hit[1]
            val = fn(*args)
            with _cache_lock:
                _cache[key] = (time.time(), val)
            return val
        return wrapper
    return deco


def invalidate():
    """Bir eylem sistemi değiştirdiğinde çağrılır (registry.call bunu otomatik yapar)."""
    with _cache_lock:
        _cache.clear()


def log(*a):
    print(time.strftime("%H:%M:%S"), *a)
