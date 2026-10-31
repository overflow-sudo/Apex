"""
ÖRNEK EKLENTİ (şablon). Yüklenmez, çünkü klasör adı _ ile başlıyor.
Yeni eklenti için bu klasörü kopyala ve adını değiştir, örn. eklentiler/sayac/ (sadece harf, rakam, _).
Rehber: eklentiler/EKLENTI_REHBERI.md

Gösterdikleri: sekme, hazır widget'lar (text, buttons), kendi widget'ı (web/ornek.js → "ornek_sayac"),
eylem, üst çubuk etiketi, ayarlar (config.py'de ORNEK = {...} ile değişir), kalıcı veri (cache/ornek/).
"""
import json, os
from core.plugin import data_dir, settings
from core.registry import action, status, tab

AYAR = settings("ORNEK", {"adim": 1, "etiket": True})
DOSYA = os.path.join(data_dir("ornek"), "sayi.json")


def _oku():
    try:
        with open(DOSYA, encoding="utf-8") as f:
            return json.load(f)["sayi"]
    except Exception:
        return 0


def _yaz(n):
    with open(DOSYA, "w", encoding="utf-8") as f:
        json.dump({"sayi": n}, f)


@tab("ornek", "Örnek", icon="ornek", order=90)
def view():
    return [
        {"type": "text", "title": "Örnek eklenti", "text": "Bu sekme eklentiler/_ornek/ klasöründen geliyor."},
        {"type": "ornek_sayac", "fill": True, "data": {"sayi": _oku(), "adim": AYAR["adim"]}},
        {"type": "buttons", "items": [
            {"title": "Artır", "icon": "plus", "action": "ornek.artir"},
            {"title": "Sıfırla", "icon": "refresh", "action": "ornek.sifirla"},
        ]},
    ]


@action("ornek.artir")
def artir():
    n = _oku() + AYAR["adim"]
    _yaz(n)
    return n                      # telefon {ok: true, result: n} alır


@action("ornek.sifirla")
def sifirla():
    _yaz(0)


@status(order=90)
def etiket():
    n = _oku()
    return "Sayaç · %d" % n if AYAR["etiket"] and n else None
