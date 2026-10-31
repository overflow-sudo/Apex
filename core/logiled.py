"""
Logitech LIGHTSYNC (LED SDK) — ctypes ile, ek paket yok.
DLL'i G HUB kuruyor. Yolu, resmi SDK sarmalayıcısının da baktığı registry anahtarından okunur:
  HKLM\\SOFTWARE\\Classes\\CLSID\\{a6519e67-7632-4375-afdf-caa889744403}\\ServerBinary
Bulunamazsa proje klasöründeki LogitechLedEnginesWrapper.dll denenir (Logitech LED SDK zip'inden, x64).
Renkler SDK'da 0–100 yüzde olarak verilir.
Gereken: G HUB açık olmalı ve G HUB ayarlarında "LIGHTSYNC / uygulamaların ışığı kontrol etmesine izin ver" açık.
"""
import ctypes, os
from core.system import BASE

CLSID = r"SOFTWARE\Classes\CLSID\{a6519e67-7632-4375-afdf-caa889744403}\ServerBinary"
DEVICE_ALL = 0x7          # tek renk + bölgesel RGB + tuş başına RGB (klavye, fare, kulaklık...)
DEVICE_PERKEY = 0x4       # sadece tuş başına RGB (G915) — tek tek tuş komutlarından önce seçilmeli

# LogiLed::KeyName = klavye tarama kodları
KEYS = {
    "ESC": 0x01, "F1": 0x3B, "F2": 0x3C, "F3": 0x3D, "F4": 0x3E, "F5": 0x3F, "F6": 0x40, "F7": 0x41,
    "F8": 0x42, "F9": 0x43, "F10": 0x44, "F11": 0x57, "F12": 0x58,
    "1": 0x02, "2": 0x03, "3": 0x04, "4": 0x05, "5": 0x06, "6": 0x07, "7": 0x08, "8": 0x09, "9": 0x0A, "0": 0x0B,
    "TAB": 0x0F, "Q": 0x10, "W": 0x11, "E": 0x12, "R": 0x13, "T": 0x14, "Y": 0x15, "U": 0x16, "I": 0x17,
    "O": 0x18, "P": 0x19, "ENTER": 0x1C, "CTRL": 0x1D, "A": 0x1E, "S": 0x1F, "D": 0x20, "F": 0x21, "G": 0x22,
    "H": 0x23, "J": 0x24, "K": 0x25, "L": 0x26, "SHIFT": 0x2A, "Z": 0x2C, "X": 0x2D, "C": 0x2E, "V": 0x2F,
    "B": 0x30, "N": 0x31, "M": 0x32, "ALT": 0x38, "SPACE": 0x39, "CAPS": 0x3A,
    "UP": 0x148, "LEFT": 0x14B, "RIGHT": 0x14D, "DOWN": 0x150,
}

# USB HID kullanım kodları (KeyName çalışmazsa yedek yol)
HID = {"ESC": 41, "TAB": 43, "SPACE": 44, "CAPS": 57, "ENTER": 40, "CTRL": 224, "SHIFT": 225, "ALT": 226,
       "RIGHT": 79, "LEFT": 80, "DOWN": 81, "UP": 82}
HID.update({chr(ord("A") + i): 4 + i for i in range(26)})
HID.update({str(i): 29 + i for i in range(1, 10)})
HID["0"] = 39
HID.update({"F%d" % i: 57 + i for i in range(1, 13)})

_dll = None
last_error = ""


def _candidates():
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, CLSID) as k:
            p = winreg.QueryValueEx(k, "")[0]
            if p:
                yield os.path.expandvars(p)
    except OSError:
        pass
    pf = os.environ.get("ProgramFiles", r"C:\Program Files")
    yield os.path.join(pf, "LGHUB", "sdks", "sdk_legacy_led_x64.dll")
    yield os.path.join(pf, "LGHUB", "sdk_legacy_led_x64.dll")
    yield os.path.join(BASE, "LogitechLedEnginesWrapper.dll")


def _load():
    global _dll, last_error
    if _dll:
        return _dll
    for path in _candidates():
        if not os.path.exists(path):
            continue
        try:
            d = ctypes.CDLL(path)
            for name in ("LogiLedInit", "LogiLedShutdown", "LogiLedSetTargetDevice", "LogiLedSetLighting",
                         "LogiLedSetLightingForKeyWithKeyName", "LogiLedSaveCurrentLighting", "LogiLedRestoreLighting"):
                getattr(d, name).restype = ctypes.c_bool
            d.LogiLedSetLighting.argtypes = [ctypes.c_int] * 3
            d.LogiLedSetLightingForKeyWithKeyName.argtypes = [ctypes.c_int] * 4
            for name in ("LogiLedSetLightingForKeyWithScanCode", "LogiLedSetLightingForKeyWithHidCode"):
                try:
                    getattr(d, name).restype = ctypes.c_bool
                    getattr(d, name).argtypes = [ctypes.c_int] * 4
                except AttributeError:
                    pass
            try:
                d.LogiLedPulseSingleKey.restype = ctypes.c_bool
                d.LogiLedPulseSingleKey.argtypes = [ctypes.c_int] * 8 + [ctypes.c_bool]
                d.LogiLedStopEffects.restype = ctypes.c_bool
            except AttributeError:
                pass
            d.LogiLedSetTargetDevice.argtypes = [ctypes.c_int]
            try:
                d.LogiLedInitWithName.restype = ctypes.c_bool
                d.LogiLedInitWithName.argtypes = [ctypes.c_char_p]
            except AttributeError:
                pass
            _dll = d
            print("Logitech LED DLL:", path)
            return d
        except Exception as e:
            last_error = "DLL yüklenemedi: %s" % e
    if not last_error:
        last_error = "G HUB bulunamadı"
    return None


def init():
    global last_error
    d = _load()
    if not d:
        return False
    ok = False
    try:
        ok = d.LogiLedInitWithName(b"PC Kumanda")
    except AttributeError:
        ok = d.LogiLedInit()
    if not ok:
        last_error = "G HUB kapalı ya da ışık kontrolüne izin verilmemiş"
        return False
    d.LogiLedSetTargetDevice(DEVICE_ALL)
    last_error = ""
    return True


def shutdown():
    if _dll:
        try:
            _dll.LogiLedShutdown()      # kontrol G HUB'a geri döner, kullanıcının profili geri gelir
        except Exception:
            pass


def pct(hex_color, scale=100):
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return [round(v * 100 / 255 * scale / 100) for v in (r, g, b)]


def set_target(device):
    return _dll.LogiLedSetTargetDevice(device)


def set_all(hex_color, brightness=100):
    set_target(DEVICE_ALL)
    return _dll.LogiLedSetLighting(*pct(hex_color, brightness))


# Hangi tuş yönteminin çalıştığını hatırla (G HUB sürümüne göre değişebiliyor)
key_method = None


def set_key(name, hex_color, brightness=100):
    """Tek tuş. Sırayla KeyName -> ScanCode -> HidCode dener, çalışanı hatırlar. True/False döner.
    Öncesinde set_target(DEVICE_PERKEY) çağrılmış olmalı."""
    global key_method
    n = name.upper()
    rgb = pct(hex_color, brightness)
    tries = []
    if n in KEYS:
        tries += [("keyname", "LogiLedSetLightingForKeyWithKeyName", KEYS[n]),
                  ("scancode", "LogiLedSetLightingForKeyWithScanCode", KEYS[n])]
    if n in HID:
        tries.append(("hid", "LogiLedSetLightingForKeyWithHidCode", HID[n]))
    if key_method:
        tries.sort(key=lambda t: t[0] != key_method)
    for method, fn, code in tries:
        f = getattr(_dll, fn, None)
        if f is not None and f(code, *rgb):
            key_method = method
            return True
    return False


def pulse_key(name, hex_from, hex_to, ms=1600):
    code = KEYS.get(name.upper())
    f = getattr(_dll, "LogiLedPulseSingleKey", None)
    if code is None or f is None:
        return False
    return f(code, *pct(hex_from), *pct(hex_to), ms, True)


def stop_effects():
    f = getattr(_dll, "LogiLedStopEffects", None)
    if f:
        f()
