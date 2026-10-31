"""Uygulama genel durumu. Sistemi değiştiren her şey 'lock' altında çalışır."""
import threading

lock = threading.RLock()
mode = "?"          # son uygulanan mod anahtarı (config.PROFILES)
