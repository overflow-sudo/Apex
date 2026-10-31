"""Ses sekmesi: varsayılan çıkış ve girişi seç."""
import re
from core import audio
from core.system import match
from core.registry import tab, action, status


def _icon(d, direction):
    if direction == audio.CAPTURE:
        return "mic"
    if match("hyperx", d["device"]) or match("kulak", d["name"]):
        return "headphones"
    if match("hoparl", d["name"]) or match("speaker", d["name"]):
        return "speaker"
    return "monitor"


def _clean(name):
    """Windows'un HDMI çıkışlarına koyduğu '4 - ' gibi ön ekleri at."""
    return re.sub(r"^\d+\s*-\s*", "", name)


def _rows(direction):
    return [{
        "title": _clean(d["name"]),
        "sub": d["device"],
        "icon": _icon(d, direction),
        "active": d["default"],
        "action": "audio.set",
        "params": {"id": d["id"]},
    } for d in audio.list_devices(direction)]


@tab("sound", "Ses", icon="volume", order=30)
def view():
    return [
        {"type": "list", "title": "Çıkış", "items": _rows(audio.RENDER)},
        {"type": "list", "title": "Giriş", "items": _rows(audio.CAPTURE)},
    ]


@action("audio.set")
def set_(id):
    audio.set_default(id)


@status(order=20)
def out_chip():
    d = audio.current(audio.RENDER)
    return "Çıkış · " + _clean(d["name"]) if d else None


@status(order=30)
def in_chip():
    d = audio.current(audio.CAPTURE)
    return "Giriş · " + _clean(d["name"]) if d else None
