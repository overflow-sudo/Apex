"""Voicemeeter (VB-Audio, Potato) ayar dosyası yükleme — Voicemeeter'ın kendi Remote API'si (VoicemeeterRemote64.dll, ctypes).
Modlar config.PROFILES[...]["voicemeeter"] ile bir XML verir (Voicemeeter'da Menu > Save Settings ile kaydedilmiş);
mod uygulanınca "Command.Load" ile o XML yüklenir. Voicemeeter kapalıysa açılır.
"""
import ctypes, os, time
from core.procs import IS_WIN
from core.system import BASE, log

_UNINSTALL = r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\VB:Voicemeeter {17359A74-1236-5467}"
_DEFAULT_DIR = r"C:\Program Files (x86)\VB\Voicemeeter"
_dll = None


def _dll_path():
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, _UNINSTALL) as k:
            d = os.path.dirname(winreg.QueryValueEx(k, "UninstallString")[0])
    except OSError:
        d = _DEFAULT_DIR
    return os.path.join(d, "VoicemeeterRemote64.dll")


def _lib():
    global _dll
    if _dll is None:
        dll = ctypes.WinDLL(_dll_path())
        dll.VBVMR_SetParameterStringW.argtypes = [ctypes.c_char_p, ctypes.c_wchar_p]
        _dll = dll
    return _dll


def load(xml):
    """xml: proje klasörüne göre ya da tam yol. Yüklendiyse True; olmazsa log'a yazar, False döner (mod yine uygulanır)."""
    path = xml if os.path.isabs(xml) else os.path.join(BASE, xml)
    if not IS_WIN:
        log("Voicemeeter: sadece Windows'ta (%s)" % os.path.basename(path))
        return False
    if not os.path.exists(path):
        log("Voicemeeter ayarı bulunamadı:", path)
        return False
    try:
        dll = _lib()
    except OSError as e:
        log("Voicemeeter Remote yüklenemedi (Voicemeeter kurulu mu?):", e)
        return False
    r = dll.VBVMR_Login()          # 0 = bağlandı, 1 = Voicemeeter kapalı, <0 = hata
    try:
        if r == 1:
            dll.VBVMR_RunVoicemeeter(3)     # 3 = Potato
            for _ in range(20):
                time.sleep(0.5)
                if dll.VBVMR_IsParametersDirty() >= 0:
                    break
        elif r < 0:
            log("Voicemeeter'a bağlanılamadı (%d)" % r)
            return False
        rc = dll.VBVMR_SetParameterStringW(b"Command.Load", path)
        time.sleep(0.3)                # komut kuyruğa alınır; hemen çıkış yapılırsa kaybolabiliyor
        if rc != 0:
            log("Voicemeeter ayarı yüklenemedi (%d): %s" % (rc, path))
            return False
        log("Voicemeeter ayarı yüklendi:", os.path.basename(path))
        return True
    finally:
        dll.VBVMR_Logout()
