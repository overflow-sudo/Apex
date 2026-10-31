"""
.py dosyaları değişince kumandayı yeniden başlatır (config.AUTO_RELOAD).
2 sn'de bir değişme zamanlarına bakar; dosyalar 2 sn boyunca sabit kalınca (Kur.bat/editör yazmayı bitirsin)
hepsini derler. Sözdizimi hatası varsa yeniden başlatmaz, log'a yazar ve bir sonraki kayıtta tekrar dener.
Yeni süreç aynı Python ile başlar, eski süreç portu bırakınca bağlanır (server.serve, PCK_RESTART).
"""
import glob, os, subprocess, sys, threading, time
import config
from core import registry, server
from core.system import BASE, log

CHECK = 2.0


def _files():
    out = {}
    pats = [os.path.join(BASE, "*.py"), os.path.join(BASE, "core", "*.py"), os.path.join(BASE, "modules", "*.py"),
            os.path.join(BASE, "eklentiler", "*", "**", "*.py")]
    for pat in pats:
        for p in glob.glob(pat, recursive=True):
            name = os.path.basename(p)
            if name == "pc_kumanda_eski.py" or (name.startswith("_") and name != "__init__.py"):
                continue
            try:
                out[p] = os.path.getmtime(p)
            except OSError:
                pass
    return out


def _compile_errors(paths):
    errs = []
    for p in paths:
        try:
            with open(p, "rb") as f:
                compile(f.read(), p, "exec")
        except (SyntaxError, ValueError) as e:
            errs.append("%s: %s" % (os.path.relpath(p, BASE), e))
        except OSError:
            pass
    return errs


def _restart(changed):
    log("dosya değişti (%s), kumanda yeniden başlatılıyor" % ", ".join(changed[:4]))
    registry.stop()
    env = dict(os.environ, PCK_RESTART="1")
    subprocess.Popen([sys.executable, os.path.join(BASE, "pc_kumanda.py")] + sys.argv[1:], cwd=BASE, env=env)
    server.RESTARTING = True
    if server.HTTPD:
        server.HTTPD.server_close()
    try:
        sys.stdout.flush()
    except Exception:
        pass
    os._exit(0)


def _watch():
    seen = _files()
    while True:
        time.sleep(CHECK)
        now = _files()
        if now == seen:
            continue
        # yazma bitene kadar bekle
        while True:
            time.sleep(CHECK)
            again = _files()
            if again == now:
                break
            now = again
        changed = sorted(os.path.relpath(p, BASE) for p in set(now) | set(seen) if now.get(p) != seen.get(p))
        seen = now
        errs = _compile_errors(list(now))
        if errs:
            log("yeniden başlatılmadı, sözdizimi hatası:", " | ".join(errs))
            continue
        _restart(changed)


def start():
    if getattr(config, "AUTO_RELOAD", True):
        threading.Thread(target=_watch, daemon=True).start()
