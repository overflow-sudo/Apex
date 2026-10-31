"""Güç: PC'yi kapat / yeniden başlat / uykuya al.
Telefondaki güç düğmesi (üst çubuk) bir panel açar; her seçenek 1,2 sn basılı tutularak onaylanır.
Komut 1 sn gecikmeyle çalışır ki eylemin cevabı telefona ulaşsın (yoksa telefon hata gösterir)."""
import os, subprocess, threading
from core.registry import action
from core.system import log

NO_WINDOW = 0x08000000


def _later(fn):
    threading.Timer(1.0, fn).start()


def _run(args):
    if os.name != "nt":
        log("güç komutu (Windows değil, çalıştırılmadı):", " ".join(args))
        return
    subprocess.Popen(args, creationflags=NO_WINDOW)


@action("power.shutdown")
def shutdown():
    log("PC kapatılıyor (telefondan)")
    _later(lambda: _run(["shutdown", "/s", "/t", "0"]))
    return "ok"


@action("power.restart")
def restart():
    log("PC yeniden başlatılıyor (telefondan)")
    _later(lambda: _run(["shutdown", "/r", "/t", "0"]))
    return "ok"


@action("power.sleep")
def sleep():
    log("PC uykuya alınıyor (telefondan)")

    def go():
        if os.name != "nt":
            return
        import ctypes
        ctypes.windll.powrprof.SetSuspendState(False, False, False)   # uyku (hazırda bekletme değil)
    _later(go)
    return "ok"
