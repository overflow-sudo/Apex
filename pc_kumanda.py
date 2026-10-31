"""
PC Kumanda - Windows bilgisayarını yerel ağdaki telefondan yönet.
Gereksinim: Python 3.8+ (ek paket yok) + bu klasörde:
  MultiMonitorTool.exe  (nirsoft.net/utils/multi_monitor_tool.html)
  SoundVolumeView.exe   (nirsoft.net/utils/sound_volume_view.html)
Elle çalıştır:  python pc_kumanda.py   (sonra telefondan http://PC_IP:8765)
Otomatik başlatma (tüm kullanıcılar): Kur.bat

Ayarlar: config.py   ·   Yeni özellik: modules/_ornek.py'yi kopyala   ·   Notlar: CLAUDE.md
"""
import os, sys, time


def _setup_log():
    """pythonw ile (konsolsuz) çalışırken çıktıyı kullanıcının LOCALAPPDATA klasörüne yaz."""
    if sys.stdout is not None and sys.stderr is not None:
        return
    folder = os.path.join(os.environ.get("LOCALAPPDATA") or os.path.expanduser("~"), "PC_Kumanda")
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, "kumanda.log")
    try:
        if os.path.getsize(path) > 1_000_000:
            os.remove(path)
    except OSError:
        pass
    f = open(path, "a", encoding="utf-8", buffering=1)
    sys.stdout = sys.stderr = f
    print("\n==== başladı %s · kullanıcı %s ====" % (time.strftime("%Y-%m-%d %H:%M:%S"), os.environ.get("USERNAME", "?")))


_setup_log()
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from core import registry, reloader, server  # noqa: E402
from core.system import MMT, SVV    # noqa: E402

if __name__ == "__main__":
    for t in (MMT, SVV):
        if not os.path.exists(t):
            print("EKSIK:", t)
    registry.load_modules()
    reloader.start()
    server.serve()
