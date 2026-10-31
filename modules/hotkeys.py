"""
PC klavyesinden telefondaki sekmeleri değiştirme (genel kısayol, oyun açıkken de çalışır).
- Varsayılan Ctrl+Alt+Shift + 1..9 = telefondaki sıraya göre n. sekme, + ←/→ = önceki/sonraki sekme.
  Sadece Ctrl+Alt kullanılmıyor: Türkçe klavyede AltGr = Ctrl+Alt, AltGr+3/7/8/9 (#{[]) yazılamaz hale gelirdi.
  config.HOTKEY_MODS ile değiştirilebilir ("ctrl+alt+shift", "win+alt" ...), config.HOTKEYS = False kapatır.
- RegisterHotKey (user32, ctypes) kendi iş parçacığında, mesaj döngüsüyle. Başka program aynı kısayolu aldıysa log'a yazılır.
- Telefon /nav/stream SSE akışını hep açık tutar; olay {"n": seq, "tab": index} ya da {"n": seq, "step": ±1}.
  Sekme listesini telefon bildiği için (görünürlük dahil) sıra çözümü telefonda yapılır.
"""
import json, threading
import config
from core.procs import IS_WIN
from core.registry import on_start, stream
from core.system import log

MODS = {"alt": 0x1, "ctrl": 0x2, "shift": 0x4, "win": 0x8}
MOD_NOREPEAT = 0x4000
VK_LEFT, VK_RIGHT = 0x25, 0x27

_cond = threading.Condition()
_seq = 0
_event = {}


def _push(ev):
    global _seq, _event
    with _cond:
        _seq += 1
        ev["n"] = _seq
        _event = ev
        _cond.notify_all()


def _loop():
    import ctypes
    import ctypes.wintypes as W
    u32 = ctypes.WinDLL("user32", use_last_error=True)
    combo = getattr(config, "HOTKEY_MODS", "ctrl+alt+shift")
    mods = MOD_NOREPEAT
    for m in combo.lower().split("+"):
        mods |= MODS.get(m.strip(), 0)
    keys = {i: (0x30 + i, {"tab": i - 1}) for i in range(1, 10)}       # 1..9
    keys[10] = (VK_LEFT, {"step": -1})
    keys[11] = (VK_RIGHT, {"step": 1})
    ok = []
    for hid, (vk, _) in keys.items():
        if u32.RegisterHotKey(None, hid, mods, vk):
            ok.append(hid)
        else:
            log("kısayol alınamadı (başka program kullanıyor olabilir):", combo, vk, ctypes.get_last_error())
    if not ok:
        return
    log("sekme kısayolları:", combo, "+ 1-9 / sol / sağ ok")
    msg = W.MSG()
    while u32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
        if msg.message == 0x0312 and msg.wParam in keys:                 # WM_HOTKEY
            _push(dict(keys[msg.wParam][1]))


@on_start
def start():
    if IS_WIN and getattr(config, "HOTKEYS", True):
        threading.Thread(target=_loop, daemon=True).start()


@stream("/nav/stream")
def nav_stream(q, send):
    """Bağlanınca eski olay gönderilmez; 15 sn olay yoksa canlı tutma satırı ({})."""
    with _cond:
        seq = _seq
    while True:
        with _cond:
            _cond.wait_for(lambda: _seq != seq, timeout=15)
            ev, seq = (_event if _seq != seq else {}), _seq
        send(json.dumps(ev))
