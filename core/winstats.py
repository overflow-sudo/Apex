"""
Windows sistem ölçümleri — sadece ctypes + winreg, ek paket yok.
  memory()        -> (toplam_bayt, kullanılan_bayt)
  uptime()        -> saniye
  cpu_name(), gpu_info() -> registry'den adlar / VRAM boyutu
  Pdh             -> performans sayaçları (CPU %, GPU %, VRAM kullanımı)
Sayaç yolları İngilizce (PdhAddEnglishCounterW) olduğu için Türkçe Windows'ta da çalışır.
"""
import ctypes, os
from ctypes import wintypes

IS_WIN = os.name == "nt"


# ---------- bellek / açık kalma süresi ----------
class _MEMSTATUSEX(ctypes.Structure):
    _fields_ = [("dwLength", wintypes.DWORD), ("dwMemoryLoad", wintypes.DWORD),
                ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]


def memory():
    s = _MEMSTATUSEX()
    s.dwLength = ctypes.sizeof(s)
    ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(s))
    return s.ullTotalPhys, s.ullTotalPhys - s.ullAvailPhys


def uptime():
    f = ctypes.windll.kernel32.GetTickCount64
    f.restype = ctypes.c_ulonglong
    return f() / 1000.0


# ---------- registry ----------
def _reg(path, name):
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path) as k:
            return winreg.QueryValueEx(k, name)[0]
    except OSError:
        return None


def cpu_name():
    n = _reg(r"HARDWARE\DESCRIPTION\System\CentralProcessor\0", "ProcessorNameString") or "CPU"
    return " ".join(n.split())


def gpu_info():
    """(ad, vram_bayt) — en çok belleği olan ekran kartı."""
    import winreg
    base = r"SYSTEM\CurrentControlSet\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}"
    best = ("GPU", 0)
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, base) as root:
            i = 0
            while True:
                try:
                    sub = winreg.EnumKey(root, i)
                except OSError:
                    break
                i += 1
                if not sub.isdigit():
                    continue
                name = _reg(base + "\\" + sub, "DriverDesc")
                mem = _reg(base + "\\" + sub, "HardwareInformation.qwMemorySize") or \
                    _reg(base + "\\" + sub, "HardwareInformation.MemorySize") or 0
                if isinstance(mem, bytes):
                    mem = int.from_bytes(mem, "little")
                if name and int(mem) >= best[1]:
                    best = (name, int(mem))
    except OSError:
        pass
    return best


# ---------- PDH performans sayaçları ----------
_PDH_FMT_DOUBLE = 0x00000200
_PDH_FMT_NOCAP100 = 0x00008000
_PDH_MORE_DATA = 0x800007D2


class _FMTVAL(ctypes.Structure):
    _fields_ = [("CStatus", wintypes.DWORD), ("doubleValue", ctypes.c_double)]


class _FMTITEM(ctypes.Structure):
    _fields_ = [("szName", ctypes.c_wchar_p), ("FmtValue", _FMTVAL)]


class Pdh:
    def __init__(self):
        d = self.dll = ctypes.WinDLL("pdh")
        H = ctypes.c_void_p
        d.PdhOpenQueryW.argtypes = [wintypes.LPCWSTR, ctypes.c_size_t, ctypes.POINTER(H)]
        d.PdhAddEnglishCounterW.argtypes = [H, wintypes.LPCWSTR, ctypes.c_size_t, ctypes.POINTER(H)]
        d.PdhCollectQueryData.argtypes = [H]
        d.PdhGetFormattedCounterValue.argtypes = [H, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD), ctypes.POINTER(_FMTVAL)]
        d.PdhGetFormattedCounterArrayW.argtypes = [H, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD),
                                                   ctypes.POINTER(wintypes.DWORD), ctypes.c_void_p]
        for f in ("PdhOpenQueryW", "PdhAddEnglishCounterW", "PdhCollectQueryData",
                  "PdhGetFormattedCounterValue", "PdhGetFormattedCounterArrayW"):
            getattr(d, f).restype = wintypes.DWORD
        self.q = H()
        r = d.PdhOpenQueryW(None, 0, ctypes.byref(self.q))
        if r:
            raise OSError("PdhOpenQuery 0x%08X" % r)
        self.c = {}

    def add(self, key, *paths):
        """İlk çalışan yolu ekler (örn. yeni sayaç yoksa eskisine düşer)."""
        for p in paths:
            h = ctypes.c_void_p()
            if self.dll.PdhAddEnglishCounterW(self.q, p, 0, ctypes.byref(h)) == 0:
                self.c[key] = h
                return True
        print("PDH sayacı eklenemedi:", paths)
        return False

    def collect(self):
        self.dll.PdhCollectQueryData(self.q)

    def value(self, key):
        h = self.c.get(key)
        if not h:
            return None
        v = _FMTVAL()
        r = self.dll.PdhGetFormattedCounterValue(h, _PDH_FMT_DOUBLE | _PDH_FMT_NOCAP100, None, ctypes.byref(v))
        return v.doubleValue if r == 0 and v.CStatus in (0, 1) else None

    def array(self, key):
        """[(örnek_adı, değer)] — joker (*) örnekli sayaçlar için."""
        h = self.c.get(key)
        if not h:
            return []
        size, count = wintypes.DWORD(0), wintypes.DWORD(0)
        flags = _PDH_FMT_DOUBLE | _PDH_FMT_NOCAP100
        r = self.dll.PdhGetFormattedCounterArrayW(h, flags, ctypes.byref(size), ctypes.byref(count), None)
        if r != _PDH_MORE_DATA or not size.value:
            return []
        buf = ctypes.create_string_buffer(size.value)
        r = self.dll.PdhGetFormattedCounterArrayW(h, flags, ctypes.byref(size), ctypes.byref(count), buf)
        if r != 0:
            return []
        items = ctypes.cast(buf, ctypes.POINTER(_FMTITEM * count.value)).contents
        return [(it.szName, it.FmtValue.doubleValue) for it in items if it.FmtValue.CStatus in (0, 1)]
