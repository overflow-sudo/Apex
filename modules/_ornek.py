"""
ŞABLON — yüklenmez (adı _ ile başlıyor). Yeni özellik için:
  1) Bu dosyayı kopyala, adını değiştir (örn. modules/medya.py) — başında _ olmasın
  2) tab / action / status kısımlarını düzenle
  3) pc_kumanda.py'yi yeniden başlat. Arayüz kendiliğinden yeni sekmeyi gösterir.

Widget türleri (section "type"):
  tiles   : büyük kartlar   items: [{title, sub, icon, active, action, params}]   "fill": True -> alanı doldur
  list    : satır listesi   items: [{title, sub, icon, active, action, params}]
  buttons : küçük düğmeler  items: [{title, icon, action, params}]
  text    : bilgi metni     "text": "..."
Her section'a isteğe bağlı "title" verilebilir. İkonlar: web/app.js -> ICONS.
"""
from core.system import run
from core.registry import tab, action, status


@tab("ornek", "Örnek", icon="bolt", order=90)
def view():
    return [
        {"type": "text", "title": "Örnek", "text": "Bu sekme modules/_ornek.py'den geliyor."},
        {"type": "buttons", "items": [
            {"title": "Not Defteri", "icon": "bolt", "action": "ornek.notepad"},
        ]},
    ]


@action("ornek.notepad")
def notepad():
    # Uzun sürmeyen işler doğrudan; arka planda açık kalacak programlar için Popen kullan.
    import subprocess
    subprocess.Popen(["notepad.exe"])


@status(order=90)
def chip():
    return None   # üst çubukta kısa bir metin göstermek istersen döndür
