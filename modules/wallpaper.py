"""
Masaüstü duvar kağıdı = kumanda arka planı (oyun teması yokken).
Windows o an gösterilen duvar kağıdının bir kopyasını %APPDATA%\\Microsoft\\Windows\\Themes\\TranscodedWallpaper
dosyasında tutar (uzantısız, genelde JPEG). Slayt gösterisinde de güncellenir. Yoksa registry'deki yol kullanılır.
Her kullanıcının kendi duvar kağıdı (kumanda zaten kullanıcının oturumunda çalışıyor).
Oyun teması aktifken arayüz duvar kağıdını gizler (app.js -> body.game).
"""
import os
import config
from core.registry import action, extra, route, section

_enabled = bool(getattr(config, "WALLPAPER", True))


def _path():
    t = os.path.join(os.environ.get("APPDATA", ""), "Microsoft", "Windows", "Themes", "TranscodedWallpaper")
    if os.path.isfile(t) and os.path.getsize(t) > 1000:
        return t
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Control Panel\Desktop") as k:
            p = winreg.QueryValueEx(k, "WallPaper")[0]
            if p and os.path.isfile(p):
                return p
    except OSError:
        pass
    return None


def _ctype(head):
    if head[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if head[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if head[:2] == b"BM":
        return "image/bmp"
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return "image/webp"
    return "image/jpeg"


@extra("wallpaper")
def wallpaper_payload():
    if not _enabled:
        return None
    p = _path()
    if not p:
        return None
    try:
        v = int(os.path.getmtime(p))
    except OSError:
        return None
    return {"url": "/wallpaper?v=%d" % v, "dim": getattr(config, "WALLPAPER_DIM", 0.55)}


@route("/wallpaper")
def wallpaper_file(q=None):
    p = _path()
    if not p:
        return None
    with open(p, "rb") as f:
        data = f.read()
    return _ctype(data[:12]), data


@section("theme", order=10)
def wp_section():
    return {"type": "buttons", "items": [
        {"title": "Duvar kağıdı", "icon": "monitor", "on": _enabled, "action": "wallpaper.toggle"},
    ]}


@action("wallpaper.toggle")
def toggle():
    global _enabled
    _enabled = not _enabled
