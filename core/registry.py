"""
Modül kayıt sistemi. modules/ içindeki her .py dosyası (adı _ ile başlamayan) açılışta yüklenir
ve aşağıdaki dekoratörlerle kendini kaydeder:

    @tab("id", "Başlık", icon="monitor", order=20)   -> def view(): return [section, ...]
    @action("ad.eylem")                               -> def fn(**params): ...
    @status(order=10)                                 -> def fn(): return "KISA METİN" veya None
    @section("sekme_id", order=50)                    -> def fn(): başka bir sekmeye bölüm ekle
    @extra("anahtar")                                 -> def fn(): /api/ui cevabına ek alan (örn. tema)
    @route("/yol")                                    -> def fn(q): (content_type, bytes) döndüren GET adresi
    @stream("/yol")                                   -> def fn(q, send): SSE ile anlık veri
    @post("/yol")                                     -> def fn(body): dict döndüren yerel POST adresi (sadece 127.0.0.1)
    @on_start                                         -> def fn(): ... (arka plan işleri)
    @on_stop                                          -> def fn(): ... (yeniden başlatmadan önce temizlik)

Section/widget biçimi CLAUDE.md'de anlatılıyor.

Eklentiler: eklentiler/<ad>/eklenti.py aynı dekoratörleri kullanır, modüllerden sonra yüklenir.
eklentiler/<ad>/web/ içindeki .js/.css dosyalarını core/server.py index.html'e ekler. Rehber: eklentiler/EKLENTI_REHBERI.md
"""
import importlib, os, traceback
from core import state
from core.system import BASE, invalidate

TABS, ACTIONS, STATUSES, STARTERS, EXTRAS, SECTIONS, ROUTES, POSTS, STREAMS = [], {}, [], [], {}, {}, {}, {}, {}
STOPPERS = []
PLUGINS = []     # yüklenen eklentiler: [{"id", "dir"}]
PLUGIN_DIR = os.path.join(BASE, "eklentiler")


def tab(id, title, icon="bolt", order=50, poll=None, visible=None):
    """poll: bu sekme açıkken arayüz kaç saniyede bir yenilensin (None = config.POLL_SECONDS).
    visible: fonksiyon; False dönerse sekme rayda görünmez (örn. Harita sadece Minecraft oynanınca)."""
    def deco(fn):
        if any(t["id"] == id for t in TABS):          # iki eklenti aynı sekme kimliğini kullanmasın
            print("UYARI: '%s' sekmesi zaten var, ikincisi yok sayıldı (%s)" % (id, fn.__module__))
            return fn
        TABS.append({"id": id, "title": title, "icon": icon, "order": order, "poll": poll, "view": fn,
                     "visible": visible})
        return fn
    return deco


def stream(path):
    """Server-Sent Events adresi (anlık veri, örn. Minecraft konumu). fn(q, send) bloklar ve olay geldikçe
    send("json metni") çağırır; telefon bağlantıyı kapatınca send hata fırlatır ve fn biter. PIN istemez."""
    def deco(fn):
        STREAMS[path] = fn
        return fn
    return deco


def post(path):
    """Yerel POST adresi (örn. Minecraft modu -> "/api/mc"). fn(body: dict) -> dict (JSON cevap).
    Sadece 127.0.0.1'den kabul edilir, PIN istemez (bilgisayardaki programlar için)."""
    def deco(fn):
        POSTS[path] = fn
        return fn
    return deco


def action(name):
    def deco(fn):
        ACTIONS[name] = fn
        return fn
    return deco


def status(order=50):
    def deco(fn):
        STATUSES.append((order, fn))
        return fn
    return deco


def section(tab_id, order=50):
    """Başka bir modülün sekmesine bölüm ekler (yeni sekme açmadan). fn bir section ya da liste döndürür."""
    def deco(fn):
        SECTIONS.setdefault(tab_id, []).append((order, fn))
        return fn
    return deco


def route(path):
    """Ek GET adresi (örn. "/media/cover"). fn(q) — q: sorgu parametreleri {ad: değer} —
    (content_type, bytes) ya da None (404) döndürür.
    PIN gerektirmez; sadece resim gibi zararsız içerik için kullan."""
    def deco(fn):
        ROUTES[path] = fn
        return fn
    return deco


def extra(key):
    """/api/ui cevabına (hafif yenilemeler dahil) ek bir alan ekler, örn. @extra("theme")."""
    def deco(fn):
        EXTRAS[key] = fn
        return fn
    return deco


def _extras(data):
    for k, fn in EXTRAS.items():
        try:
            data[k] = fn()
        except Exception:
            traceback.print_exc()
    return data


def on_start(fn):
    STARTERS.append(fn)
    return fn


def on_stop(fn):
    STOPPERS.append(fn)
    return fn


def stop():
    for fn in STOPPERS:
        try:
            fn()
        except Exception:
            traceback.print_exc()


def load_modules():
    folder = os.path.join(BASE, "modules")
    for f in sorted(os.listdir(folder)):
        if f.endswith(".py") and not f.startswith("_"):
            try:
                importlib.import_module("modules." + f[:-3])
                print("modül yüklendi:", f[:-3])
            except Exception:
                print("MODÜL HATASI:", f)
                traceback.print_exc()
    load_plugins()
    for fn in STARTERS:
        try:
            fn()
        except Exception:
            traceback.print_exc()


def plugin_dirs():
    """Etkin eklenti klasörleri: eklentiler/<ad>/eklenti.py olanlar; adı _ ya da . ile başlayanlar kapalı."""
    out = []
    if os.path.isdir(PLUGIN_DIR):
        for name in sorted(os.listdir(PLUGIN_DIR)):
            d = os.path.join(PLUGIN_DIR, name)
            if name[:1] not in "_." and os.path.isfile(os.path.join(d, "eklenti.py")):
                out.append((name, d))
    return out


def load_plugins():
    for name, d in plugin_dirs():
        if not name.isidentifier():
            print("EKLENTİ ATLANDI (klasör adı harf, rakam ve _ olmalı):", name)
            continue
        try:
            importlib.import_module("eklentiler.%s.eklenti" % name)
            PLUGINS.append({"id": name, "dir": d})
            print("eklenti yüklendi:", name)
        except Exception:
            print("EKLENTİ HATASI:", name)
            traceback.print_exc()


def _visible(t):
    try:
        return not t.get("visible") or bool(t["visible"]())
    except Exception:
        return False


def _sections(t):
    try:
        out = list(t["view"]() or [])
    except Exception as e:
        traceback.print_exc()
        out = [{"type": "text", "title": "Hata", "text": str(e)}]
    for _, fn in sorted(SECTIONS.get(t["id"], []), key=lambda x: x[0]):
        try:
            r = fn()
            if r:
                out.extend(r if isinstance(r, list) else [r])
        except Exception as e:
            traceback.print_exc()
            out.append({"type": "text", "title": "Hata", "text": str(e)})
    return out


def ui(tab_id=None, light=False):
    """Sadece istenen sekmenin içeriği hesaplanır (diğerleri sections=None), böylece
    arka planda gereksiz yere araç çalıştırılmaz. light=True: sadece o sekme, durum etiketi yok."""
    ordered = [t for t in sorted(TABS, key=lambda t: t["order"]) if _visible(t)]
    if not any(t["id"] == tab_id for t in ordered) and ordered:
        tab_id = ordered[0]["id"]
    tabs = []
    for t in ordered:
        if light and t["id"] != tab_id:
            continue
        tabs.append({"id": t["id"], "title": t["title"], "icon": t["icon"], "poll": t["poll"],
                     "sections": _sections(t) if t["id"] == tab_id else None})
    if light:
        return _extras({"tabs": tabs, "light": True, "tab": tab_id})
    chips = []
    for _, fn in sorted(STATUSES, key=lambda s: s[0]):
        try:
            v = fn()
            if v:
                chips.append(v)
        except Exception:
            pass
    return _extras({"tabs": tabs, "status": chips, "mode": state.mode, "tab": tab_id})


def call(name, params):
    fn = ACTIONS.get(name)
    if not fn:
        raise KeyError("bilinmeyen eylem: %s" % name)
    try:
        with state.lock:
            return fn(**(params or {}))
    finally:
        invalidate()
