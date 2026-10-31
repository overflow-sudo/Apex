"""Windows HID erişimi (ctypes, hid.dll + setupapi): aygıt bulma, rapor yazma, zaman aşımlı okuma.
Aygıt paylaşımlı açılır (FILE_SHARE_READ|WRITE), başka programlar (NGENUITY, G HUB) etkilenmez."""
import ctypes
import ctypes.wintypes as W

hid = ctypes.WinDLL("hid")
_setup = ctypes.WinDLL("setupapi")
_k32 = ctypes.WinDLL("kernel32", use_last_error=True)

GENERIC_RW = 0xC0000000
OPEN_EXISTING = 3
FILE_FLAG_OVERLAPPED = 0x40000000
INVALID = W.HANDLE(-1).value


class GUID(ctypes.Structure):
    _fields_ = [("a", W.DWORD), ("b", W.WORD), ("c", W.WORD), ("d", ctypes.c_ubyte * 8)]


class _IFD(ctypes.Structure):
    _fields_ = [("cb", W.DWORD), ("g", GUID), ("f", W.DWORD), ("r", ctypes.c_void_p)]


class _CAPS(ctypes.Structure):
    _fields_ = [("Usage", W.USHORT), ("UsagePage", W.USHORT), ("In", W.USHORT), ("Out", W.USHORT),
                ("Feat", W.USHORT), ("r", W.USHORT * 17), ("x", W.USHORT * 10)]


class _OVL(ctypes.Structure):
    _fields_ = [("Internal", ctypes.c_void_p), ("InternalHigh", ctypes.c_void_p), ("Offset", W.DWORD),
                ("OffsetHigh", W.DWORD), ("hEvent", W.HANDLE)]


_setup.SetupDiGetClassDevsW.restype = ctypes.c_void_p
_setup.SetupDiGetClassDevsW.argtypes = [ctypes.POINTER(GUID), W.LPCWSTR, W.HWND, W.DWORD]
_setup.SetupDiEnumDeviceInterfaces.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.POINTER(GUID), W.DWORD,
                                               ctypes.POINTER(_IFD)]
_setup.SetupDiGetDeviceInterfaceDetailW.argtypes = [ctypes.c_void_p, ctypes.POINTER(_IFD), ctypes.c_void_p, W.DWORD,
                                                    ctypes.POINTER(W.DWORD), ctypes.c_void_p]
_setup.SetupDiDestroyDeviceInfoList.argtypes = [ctypes.c_void_p]
_k32.CreateFileW.restype = W.HANDLE
_k32.CreateFileW.argtypes = [W.LPCWSTR, W.DWORD, W.DWORD, ctypes.c_void_p, W.DWORD, W.DWORD, W.HANDLE]
_k32.CreateEventW.restype = W.HANDLE
_k32.CreateEventW.argtypes = [ctypes.c_void_p, W.BOOL, W.BOOL, W.LPCWSTR]
for _f in ("ReadFile", "WriteFile"):
    getattr(_k32, _f).argtypes = [W.HANDLE, ctypes.c_void_p, W.DWORD, ctypes.POINTER(W.DWORD), ctypes.POINTER(_OVL)]
_k32.GetOverlappedResult.argtypes = [W.HANDLE, ctypes.POINTER(_OVL), ctypes.POINTER(W.DWORD), W.BOOL]
_k32.WaitForSingleObject.argtypes = [W.HANDLE, W.DWORD]
_k32.CancelIo.argtypes = [W.HANDLE]
_k32.CloseHandle.argtypes = [W.HANDLE]
hid.HidD_GetPreparsedData.argtypes = [W.HANDLE, ctypes.POINTER(ctypes.c_void_p)]
hid.HidD_FreePreparsedData.argtypes = [ctypes.c_void_p]
hid.HidP_GetCaps.argtypes = [ctypes.c_void_p, ctypes.POINTER(_CAPS)]


def _paths():
    g = GUID()
    hid.HidD_GetHidGuid(ctypes.byref(g))
    h = _setup.SetupDiGetClassDevsW(ctypes.byref(g), None, None, 0x12)   # PRESENT | DEVICEINTERFACE
    out, i = [], 0
    try:
        while True:
            d = _IFD()
            d.cb = ctypes.sizeof(_IFD)
            if not _setup.SetupDiEnumDeviceInterfaces(h, None, ctypes.byref(g), i, ctypes.byref(d)):
                break
            i += 1
            n = W.DWORD()
            _setup.SetupDiGetDeviceInterfaceDetailW(h, ctypes.byref(d), None, 0, ctypes.byref(n), None)
            buf = ctypes.create_string_buffer(n.value)
            ctypes.cast(buf, ctypes.POINTER(W.DWORD))[0] = 8 if ctypes.sizeof(ctypes.c_void_p) == 8 else 6
            if _setup.SetupDiGetDeviceInterfaceDetailW(h, ctypes.byref(d), buf, n, None, None):
                out.append(ctypes.wstring_at(ctypes.addressof(buf) + 4))
    finally:
        _setup.SetupDiDestroyDeviceInfoList(h)
    return out


def _caps(handle):
    pp = ctypes.c_void_p()
    if not hid.HidD_GetPreparsedData(handle, ctypes.byref(pp)):
        return None
    c = _CAPS()
    hid.HidP_GetCaps(pp, ctypes.byref(c))
    hid.HidD_FreePreparsedData(pp)
    return c


class Device(object):
    def __init__(self, path, caps):
        self.path, self.in_len, self.out_len = path, caps.In, caps.Out
        self.h = _k32.CreateFileW(path, GENERIC_RW, 3, None, OPEN_EXISTING, FILE_FLAG_OVERLAPPED, None)
        if self.h in (None, INVALID):
            raise OSError("HID açılamadı: %d" % ctypes.get_last_error())
        self.ev = _k32.CreateEventW(None, True, False, None)

    def _io(self, fn, buf, n, timeout):
        ov = _OVL()
        ov.hEvent = self.ev
        got = W.DWORD()
        if not fn(self.h, buf, n, None, ctypes.byref(ov)) and ctypes.get_last_error() != 997:   # IO_PENDING
            return None
        if _k32.WaitForSingleObject(self.ev, int(timeout * 1000)) != 0:
            _k32.CancelIo(self.h)
            _k32.GetOverlappedResult(self.h, ctypes.byref(ov), ctypes.byref(got), True)
            return None
        if not _k32.GetOverlappedResult(self.h, ctypes.byref(ov), ctypes.byref(got), False):
            return None
        return got.value

    def write(self, data, timeout=1.0):
        data = bytes(data) + bytes(max(0, self.out_len - len(data)))
        return self._io(_k32.WriteFile, data, self.out_len, timeout) is not None

    def read(self, timeout=1.0):
        buf = ctypes.create_string_buffer(self.in_len)
        n = self._io(_k32.ReadFile, buf, self.in_len, timeout)
        return buf.raw[:n] if n else None

    def close(self):
        _k32.CloseHandle(self.h)
        _k32.CloseHandle(self.ev)

    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.close()


def find(vid, pid, usage_page):
    """vid/pid/usage_page'e uyan ilk HID koleksiyonunu açar, yoksa None."""
    key = "vid_%04x&pid_%04x" % (vid, pid)
    for p in _paths():
        if key not in p.lower():
            continue
        h = _k32.CreateFileW(p, 0, 3, None, OPEN_EXISTING, 0, None)
        if h in (None, INVALID):
            continue
        try:
            c = _caps(h)
        finally:
            _k32.CloseHandle(h)
        if c and c.UsagePage == usage_page:
            return Device(p, c)
    return None
