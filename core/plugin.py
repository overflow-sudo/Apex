"""Eklentiler için küçük yardımcılar (eklentiler/EKLENTI_REHBERI.md).

    from core.plugin import settings, data_dir
    AYAR = settings("SAYAC", {"adim": 1})      # varsayılanlar + config.py'deki SAYAC = {...} (varsa) üstüne yazılır
    YOL = data_dir("sayac")                     # cache/sayac/ — Kur.bat ezmez, eklenti güncellenince kayıtlar kalır
"""
import os
import config
from core.system import BASE


def settings(name, defaults):
    """defaults sözlüğünün kopyası; config.py'de aynı adlı bir sözlük varsa onun değerleri üstüne yazılır."""
    out = dict(defaults)
    out.update(getattr(config, name, None) or {})
    return out


def data_dir(plugin_id):
    """Eklentinin kalıcı veri klasörü: <kumanda>/cache/<eklenti>/ (yoksa oluşturulur)."""
    d = os.path.join(BASE, "cache", plugin_id)
    os.makedirs(d, exist_ok=True)
    return d
