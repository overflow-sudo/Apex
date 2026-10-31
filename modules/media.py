"""
Şu an çalan medya (Spotify, YouTube/Chrome/Edge, Medya Oynatıcı, VLC...) — Windows medya oturumu (SMTC).
Python'da WinRT için paket gerekirdi; onun yerine core/media.ps1 sürekli çalışan bir PowerShell süreci olarak
1,5 sn'de bir JSON satırı yazar, biz okuruz. Kapak resmi kullanıcının LOCALAPPDATA klasörüne yazılır ve
/media/cover adresinden sunulur. Kontroller (önceki/oynat-durdur/sonraki) Windows medya tuşlarıyla yapılır.
Sağ üstteki medya kutusu @extra("media") ile gelir.
"""
import ctypes, json, os, subprocess, threading, time
from core.system import BASE, log
from core.registry import action, extra, on_start, on_stop, route
from core.procs import IS_WIN

SCRIPT = os.path.join(BASE, "core", "media.ps1")
COVER = os.path.join(os.environ.get("LOCALAPPDATA") or os.path.expanduser("~"), "PC_Kumanda", "cover.img")
_state = {}            # son satır
_stamp = 0.0           # son satırın geldiği an
_err = ""
_proc = None         # media.ps1 süreci

APPS = [("spotify", "Spotify"), ("chrome", "Chrome"), ("msedge", "Edge"), ("firefox", "Firefox"),
        ("308046b0af4a39cb", "Firefox"), ("zunemusic", "Medya Oynatıcı"), ("microsoft.media", "Medya Oynatıcı"),
        ("vlc", "VLC"), ("opera", "Opera"), ("brave", "Brave"), ("discord", "Discord"), ("youtube", "YouTube"),
        ("applemusic", "Apple Music"), ("deezer", "Deezer"), ("tidal", "TIDAL")]


def _app_name(aumid):
    a = (aumid or "").lower()
    for k, v in APPS:
        if k in a:
            return v
    return (aumid or "").split("!")[0].split("\\")[-1].replace(".exe", "")[:20]


def _reader():
    global _stamp, _err, _proc
    os.makedirs(os.path.dirname(COVER), exist_ok=True)
    wait = 5
    while True:
        started = time.time()
        try:
            proc = subprocess.Popen(
                ["powershell.exe", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
                 "-File", SCRIPT, COVER],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=0x08000000)
            _proc = proc
            for raw in proc.stdout:
                line = raw.decode("utf-8", "replace").strip().lstrip("﻿")
                if not line.startswith("{"):
                    continue
                try:
                    d = json.loads(line)
                except ValueError:
                    continue
                if d.get("ok"):
                    _state.clear()
                    _state.update(d)
                    _stamp = time.time()
                    _err = ""
                elif d.get("error") and d["error"] != _err:
                    _err = d["error"]
                    log("medya okunamadı:", _err)
            err = proc.stderr.read().decode("utf-8", "replace").strip()
            if err:
                log("medya süreci durdu:", err[-400:])
        except Exception as e:
            log("medya süreci başlatılamadı:", e)
        # hemen çöktüyse giderek daha geç dene
        wait = 5 if time.time() - started > 60 else min(wait * 2, 120)
        time.sleep(wait)


@on_start
def start():
    if IS_WIN:
        threading.Thread(target=_reader, daemon=True).start()


@on_stop
def stop():
    if _proc and _proc.poll() is None:
        _proc.kill()


def current():
    d = dict(_state)
    if not d or time.time() - _stamp > 10:
        return None
    if d.get("status") not in ("Playing", "Paused") or not (d.get("title") or "").strip():
        return None
    playing = d["status"] == "Playing"
    pos = float(d.get("pos") or 0) + ((time.time() - _stamp) if playing else 0)
    dur = float(d.get("dur") or 0)
    return {
        "title": d.get("title") or "",
        "artist": d.get("artist") or d.get("album") or "",
        "app": _app_name(d.get("app")),
        "playing": playing,
        "pos": round(min(pos, dur) if dur else pos, 1),
        "dur": round(dur, 1),
        "cover": ("/media/cover?v=%s" % d["cover"]) if d.get("cover") else None,
    }


@extra("media")
def media_payload():
    return current()


@route("/media/cover")
def cover(q=None):
    try:
        with open(COVER, "rb") as f:
            data = f.read()
    except OSError:
        return None
    ctype = "image/png" if data[:4] == b"\x89PNG" else "image/jpeg"
    return ctype, data


# ---- kontroller: Windows medya tuşları (hangi uygulama çalıyorsa ona gider) ----
VK = {"toggle": 0xB3, "next": 0xB0, "prev": 0xB1}


def _press(vk):
    u = ctypes.windll.user32
    u.keybd_event(vk, 0, 0x1, 0)          # KEYEVENTF_EXTENDEDKEY
    u.keybd_event(vk, 0, 0x1 | 0x2, 0)    # + KEYEVENTF_KEYUP
    time.sleep(0.6)                        # oturum güncellensin


@action("media.toggle")
def toggle():
    _press(VK["toggle"])


@action("media.next")
def next_():
    _press(VK["next"])


@action("media.prev")
def prev():
    _press(VK["prev"])
