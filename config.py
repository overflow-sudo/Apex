"""
PC Kumanda ayarları. Sadece burayı düzenleyerek modları değiştirebilirsin.
Adlar küçük/büyük harf duyarsız, "içinde geçiyor mu" diye aranır.
"""

PORT = 8765
PIN = ""                # boş değilse arayüz bu PIN'i ister
AUTO_GAMEPAD = True     # gamepad tuşuna basınca otomatik "tv" moduna geç
POLL_SECONDS = 8        # arayüz kaç saniyede bir durumu yeniler
AUTO_RELOAD = True      # .py dosyaları değişince kumanda kendini yeniden başlatsın
BATTERY_LOW = 15        # fare/klavye/kulaklık pili bu yüzdeye inince üst çubukta yanıp sönen uyarı
LHM_URL = "http://127.0.0.1:8085/data.json"   # LibreHardwareMonitor web sunucusu (sıcaklıklar için)

# Modlar (Modlar sekmesindeki büyük kartlar). Sıra = ekrandaki sıra.
#   monitors : "all" = hepsini aç | "keep" = ekranlara dokunma | ["ad", ...] = sadece bunlar açık
#   primary  : ana ekran olacak monitör (None = değiştirme)
#   out / inp: varsayılan ses çıkışı / girişi (None = değiştirme)
#   icon     : web/app.js içindeki ICONS anahtarlarından biri
PROFILES = {
    "tv": {
        "title": "Oyun",
        "sub": "TV · gamepad",
        "icon": "gamepad",
        "monitors": ["Smart M70F"],
        "primary": "Smart M70F",
        "out": "Smart M70F",
        "inp": None,
    },
    "desk": {
        "title": "Masaüstü",
        "sub": "Çalışma · kulaklık",
        "icon": "desktop",
        "monitors": "all",
        "primary": "EI242QR",
        "out": "HyperX",
        "inp": "HyperX",
    },
    "music": {
        "title": "Müzik",
        "sub": "Gitar · mikrofon",
        "icon": "music",
        "monitors": "keep",
        "primary": None,
        "out": "USB AUDIO",
        "inp": "USB AUDIO",
    },
}

# ---------------- OYUN TEMALARI ----------------
# Öndeki pencerenin programı (veya arka planda açık bir oyun) aşağıdaki exe'lerden biriyse arayüz o
# oyunun temasına geçer. exe adları büyük/küçük harf duyarsız.
#   short  : kartlarda ve üst çubukta görünen kısa ad
#   accent : vurgu rengi   accent2: ikinci renk (efektlerde)   bg: zemin   fg: yazı rengi
#   fx     : arka plan efekti — radar | hex | tactical | glitch | snow | dust | road | "" (yok)
#   logo   : "steam:<appid>" ya da resim adresi; logo_white: True = koyu logoyu beyaza çevir
#            (telefon logoyu doğrudan internetten yükler; listede olmayan Steam oyunlarının logosu otomatik bulunur)
THEME_FX = False         # True = oyunun hareketli arka plan efekti de gelsin (sade tema: kapalı, sadece vurgu rengi değişir)

# Klavye ışığı (Logitech G HUB / LIGHTSYNC): oyun açıkken tüm klavye "accent", "keys" tuşları "key_color"
# (yoksa accent2, o da yoksa beyaz). Oyun kapanınca G HUB'daki kendi profilin geri gelir.
# Oyunun kendi Logitech ışık desteği varsa ve onu tercih edersen o oyuna "lighting": False yaz.
KEYBOARD_LIGHTING = True
KEYBOARD_BRIGHTNESS = 60   # ana renk parlaklığı (0–100); vurgulu tuşlar hep 100
KEYBOARD_KEY_EFFECT = "static"   # "static" = sabit | "pulse" = vurgulu tuşlar ana renkle arasında yavaşça nefes alır
FPS_KEYS = ["W", "A", "S", "D", "SHIFT", "CTRL", "SPACE", "R", "1", "2", "3"]

GAME_THEMES = {
    "valorant": {"name": "VALORANT", "short": "Valorant", "logo": "https://commons.wikimedia.org/wiki/Special:FilePath/Valorant_logo_-_pink_color_version.svg",
                 "exe": ["VALORANT-Win64-Shipping.exe"],
                 "accent": "#ff4655", "bg": "#0f1923", "fg": "#ece8e1", "fx": "radar",
                 "key_color": "#ece8e1", "keys": FPS_KEYS + ["C", "Q", "E", "X", "F", "4"]},
    "cs2":      {"name": "Counter-Strike 2", "short": "CS2", "logo": "steam:730", "logo_white": True,
                 "exe": ["cs2.exe", "csgo.exe"],
                 "accent": "#e8a33d", "bg": "#0c0f14", "fx": "radar",
                 "keys": FPS_KEYS + ["E", "G", "B", "4", "5", "TAB"]},
    "tft":      {"name": "Teamfight Tactics", "short": "TFT", "logo": "https://commons.wikimedia.org/wiki/Special:FilePath/Teamfight_Tactics_logo.svg",
                 "exe": ["League of Legends.exe"],
                 "accent": "#c8aa6e", "accent2": "#0ac8b9", "bg": "#0a1428", "fg": "#f0e6d2", "fx": "hex",
                 "keys": ["D", "F", "E", "W", "Q", "SPACE", "TAB"]},
    "r6":       {"name": "Rainbow Six Siege", "short": "R6 Siege", "logo": "steam:359550",
                 "exe": ["RainbowSix.exe", "RainbowSix_Vulkan.exe", "RainbowSix_DX11.exe", "RainbowSix_BE.exe"],
                 "accent": "#4aa8ff", "bg": "#0a0d12", "fx": "tactical",
                 "keys": FPS_KEYS + ["Q", "E", "F", "G", "C", "Z", "X", "5"]},
    "cyberpunk": {"name": "Cyberpunk 2077", "short": "Cyberpunk", "logo": "steam:1091500",
                 "exe": ["Cyberpunk2077.exe"],
                 "accent": "#fcee0a", "accent2": "#02d7f2", "bg": "#08080e", "fx": "glitch",
                 "keys": FPS_KEYS + ["F", "Q", "E", "C", "V", "Z", "TAB", "I", "M"]},
    "skyrim":   {"name": "Skyrim", "short": "Skyrim", "logo": "steam:489830",
                 "exe": ["SkyrimSE.exe", "TESV.exe", "SkyrimVR.exe"],
                 "accent": "#d6ccb4", "bg": "#0b0d10", "fg": "#ece6d6", "fx": "snow", "key_color": "#7fc8ff",
                 "keys": ["W", "A", "S", "D", "E", "R", "Z", "Q", "TAB", "SHIFT", "SPACE", "CTRL", "ALT", "J", "M"]},
    "rdr2":     {"name": "Red Dead Redemption 2", "short": "RDR2", "logo": "steam:1174180",
                 "exe": ["RDR2.exe"],
                 "accent": "#c8352c", "bg": "#120c09", "fg": "#efe3cf", "fx": "dust", "key_color": "#f0c27a",
                 "keys": ["W", "A", "S", "D", "SHIFT", "SPACE", "CTRL", "E", "R", "F", "Q", "TAB", "C", "V", "B", "M"]},
    # Minecraft Java javaw.exe olarak çalışır; tema PC Kumanda Bridge modundan gelen konumla açılır
    "minecraft": {"name": "Minecraft", "short": "Minecraft", "exe": [], "preview": False,
                 "accent": "#62c143", "accent2": "#8b5a2b", "bg": "#0a100a", "fx": "tactical", "key_color": "#ffffff",
                 "keys": ["W", "A", "S", "D", "SPACE", "SHIFT", "CTRL", "E", "Q", "F", "T", "1", "2", "3", "4", "5", "6", "7", "8", "9"]},
    "ets2":     {"name": "Euro Truck Simulator 2", "short": "ETS2", "logo": "steam:227300",
                 "exe": ["eurotrucks2.exe"],
                 "accent": "#f5b400", "bg": "#0b0e12", "fx": "road", "key_color": "#ffffff",
                 "keys": ["W", "A", "S", "D", "SPACE", "E", "L", "H", "K", "B", "C", "T", "F", "Q", "UP", "DOWN", "LEFT", "RIGHT"]},
}
# Listede olmayan ama Steam / Epic / Xbox klasöründen açılan oyunlar için (ad klasörden alınır)
UNKNOWN_GAME_THEME = {"accent": "#8fd3ff", "bg": "#0a0c10", "fx": "tactical"}

# ---------------- MAÇ SKORLARI ----------------
# Sağ üstte canlı skor kutusu (ESPN). favorites: takım adları ("Galatasaray", "Fenerbahçe", "GS", "FB"...)
# favori takımın maçı varsa hep o gösterilir.
FOOTBALL = {
    "enabled": True,
    "favorites": [],
    "leagues": [("tur.1", "Süper Lig", "SL"), ("uefa.champions", "Şampiyonlar Ligi", "ŞL")],
}

# ---------------- ARKA PLAN ----------------
# True = oyun teması yokken kumandanın arka planı bilgisayarın masaüstü duvar kağıdı olsun
# (sade tema: kapalı, düz koyu zemin; Tema sekmesinden açılabilir)
WALLPAPER = False
WALLPAPER_DIM = 0.55     # duvar kağıdının üstündeki karartma (0 = hiç, 1 = simsiyah); yazılar okunsun diye

# ---------------- MINECRAFT ----------------
# Harita sekmesi: "PC Kumanda Bridge" Fabric modu konumu gönderir, seed haritası cubiomes ile çizilir.
# Seed otomatik bulunur (tek oyunculu: doğrudan; Realm/sunucu: mod girişte /seed çalıştırır, cevap latest.log'dan okunur).
# Bulunamazsa default_seed kullanılır.
MINECRAFT = {
    "default_seed": 271664881382654292,
    "log": None,            # None = %APPDATA%\.minecraft\logs\latest.log
    "structures": True,
}
