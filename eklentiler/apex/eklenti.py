"""
APEX FINANCE eklentisi — Emir'in portföy uygulamasını (C:\\Users\\emir\\Desktop\\EABorsa) kumandada gösterir.

- "Portföy" sekmesi: toplam değer, kâr/zarar, günlük değişim, varlıklar, dağılım, performans çizgisi.
- Boşta slayt gösterisi: telefona bir süre dokunulmazsa tam ekran iki slayt döner (web/apex.js):
  portföy özeti (toplam birikim) ve sistem durumu (CPU/GPU/RAM/VRAM/sıcaklık, modules/system.py ölçümü).
- Odak adasında küçük portföy rozeti (dokununca Portföy sekmesi).

APEX'in yerel API'siyle konuşur (yalnızca 127.0.0.1):
  GET <url>/api/portfolios, /api/portfolios/<id>/summary, /history, /transactions
Veri arka plandaki iş parçacığında çekilir; view() ve @extra sadece son anlık görüntüyü okur.
Portföy kişisel veri olduğu için PIN korumalı /api/ui (@extra) üzerinden gider, @route kullanılmaz.

Ayar (config.py'de isteğe bağlı):  APEX = {"url": "http://127.0.0.1:8787", "bosta_sn": 120, ...}
Ayrıntılar: eklentiler/apex/NOTLAR.md
"""
import json, os, shutil, subprocess, threading, time
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from urllib.parse import quote

from core.plugin import settings
from core.registry import action, extra, focus, on_start, tab
from core.system import log
from core.procs import IS_WIN
from modules import system as sistem    # Sistem sekmesinin 2 sn'lik ölçümü (aynı modül, yeniden yüklenmez)

AYAR = settings("APEX", {
    "url": "http://127.0.0.1:8787",                     # APEX sunucusu
    "klasor": r"C:\Users\emir\Desktop\EABorsa",         # APEX kapalıysa burada node server/index.ts çalıştırılır
    "otomatik_ac": True,                                 # APEX hep açık kalsın: kapanırsa 30 sn içinde arka planda yeniden başlatılır
    "otomatik_bekle": 25,                                # açılışta masaüstü otursun diye bekleme (sn)
    "yenile": 60,                                        # özet yenileme aralığı (sn)
    "gecmis_yenile": 900,                                # performans geçmişi yenileme aralığı (sn)
    "slayt": True,                                       # boşta slayt gösterisi açık mı
    "bosta_sn": 120,                                     # dokunulmadan bu kadar sn geçince slayt başlar
    "slayt_sn": 9,                                       # her slaytın ekranda kalma süresi
    "sistem_slayt": True,                                # slaytlarda sistem durumu da olsun
    "muzik_varken": True,                                # müzik çalarken de slayt (altta çalan şarkı); False = medya ekranına bırak
    "rozet": True,                                       # odak adasında portföy rozeti
})

CREATE_NO_WINDOW = 0x08000000
CREATE_NEW_PROCESS_GROUP = 0x00000200

_kilit = threading.Lock()
_veri = {"ok": False, "hata": "Henüz bağlanılmadı", "ts": 0, "portfoyler": []}
_gecmis = {}            # portfoy_id -> (zaman, [deger...], [yatirilan...], ilk_tarih, son_tarih)
_semboller = {}         # enstruman_id -> (sembol, ad)
_semboller_ts = [0.0]
_ac_ts = [0.0]


def _istek(yol, timeout=8.0):
    """APEX'e GET atar → (http_kodu, json) ya da sunucu kapalıysa (None, {})."""
    try:
        with urlopen(Request(AYAR["url"].rstrip("/") + yol), timeout=timeout) as r:
            return r.status, json.loads(r.read().decode("utf-8") or "{}")
    except HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode("utf-8") or "{}")
        except Exception:
            return e.code, {}
    except (URLError, OSError, ValueError):
        return None, {}


def _sayi(v):
    return v if isinstance(v, (int, float)) else None


def _seyrelt(noktalar, n=60):
    """Grafik için en fazla n nokta (ilk ve son nokta korunur)."""
    if len(noktalar) <= n:
        return list(noktalar)
    adim = (len(noktalar) - 1) / float(n - 1)
    return [noktalar[int(round(i * adim))] for i in range(n)]


def _sembolleri_guncelle(pid):
    if time.time() - _semboller_ts[0] < 600 and _semboller:
        return
    kod, d = _istek("/api/portfolios/%s/transactions" % pid)
    if kod == 200:
        for iid, ins in (d.get("instruments") or {}).items():
            _semboller[iid] = (ins.get("symbol") or iid, ins.get("name") or "")
        _semboller_ts[0] = time.time()


def _gecmisi_guncelle(pid):
    eski = _gecmis.get(pid)
    if eski and time.time() - eski[0] < AYAR["gecmis_yenile"]:
        return
    kod, d = _istek("/api/portfolios/%s/history" % pid, timeout=30)
    if kod != 200:
        return
    noktalar = [p for p in (d.get("points") or []) if _sayi(p.get("valueBase")) is not None and _sayi(p.get("investedBase")) is not None]
    if noktalar:
        s = _seyrelt(noktalar)
        _gecmis[pid] = (time.time(), [p["valueBase"] for p in s], [p["investedBase"] for p in s],
                        noktalar[0].get("date"), noktalar[-1].get("date"))


def _portfoy(p):
    pid = p["id"]
    kod, s = _istek("/api/portfolios/%s/summary" % pid, timeout=20)
    if kod != 200:
        raise IOError(s.get("error") or "özet alınamadı (HTTP %s)" % kod)
    _sembolleri_guncelle(pid)
    _gecmisi_guncelle(pid)
    varliklar = []
    for x in s.get("positions") or []:
        sem, ad = _semboller.get(x["instrumentId"], (x["instrumentId"].split(":")[-1], ""))
        varliklar.append({
            "sembol": sem, "ad": ad,
            "deger": _sayi(x.get("valueBase")), "kz": _sayi(x.get("unrealizedBase")),
            "kz_yuzde": _sayi(x.get("unrealizedPct")), "gun": _sayi(x.get("dayChangeBase")),
            "agirlik": _sayi(x.get("weight")), "fiyat": _sayi(x.get("price")), "para": x.get("priceCurrency"),
        })
    nakit = _sayi(s.get("cashBase")) or 0
    if nakit > 0.005:
        varliklar.append({"sembol": "Nakit", "ad": "", "deger": nakit, "kz": None, "kz_yuzde": None,
                          "gun": None, "agirlik": None, "fiyat": None, "para": None})
    dagilim = [{"ad": a.get("label"), "oran": a.get("weight")} for a in ((s.get("allocation") or {}).get("type") or [])[:6]]
    g = _gecmis.get(pid)
    return {
        "id": pid, "ad": p.get("name"), "para": s.get("baseCurrency"),
        "toplam": _sayi(s.get("totalValueBase")), "fiyatli": _sayi(s.get("pricedValueBase")),
        "yatirilan": _sayi(s.get("investedBase")), "kz": _sayi(s.get("totalPnlBase")),
        "kz_yuzde": _sayi(s.get("totalReturnPct")), "gun": _sayi(s.get("dayChangeBase")),
        "gun_yuzde": _sayi(s.get("dayChangePct")), "gerceklesen": _sayi(s.get("realizedBase")),
        "gerceklesmeyen": _sayi(s.get("unrealizedBase")), "fiyatsiz": len(s.get("unpricedInstrumentIds") or []),
        "varliklar": varliklar, "dagilim": dagilim,
        # değer + yatırılan para: değer para ekledikçe büyür, getiri ikisi arasındaki farktır
        "grafik": g[1] if g else [], "grafik_yatirilan": g[2] if g else [],
        "grafik_ilk": g[3] if g else None, "grafik_son": g[4] if g else None,
        "zaman": s.get("generatedAt"),
    }


def _yokla():
    kod, d = _istek("/api/portfolios")
    if kod is None:
        return {"ok": False, "hata": "APEX kapalı", "kapali": True, "ts": time.time(), "portfoyler": []}
    if kod != 200:
        return {"ok": False, "hata": "APEX hatası (HTTP %s)" % kod, "ts": time.time(), "portfoyler": []}
    aktif = d.get("activePortfolioId")
    liste = sorted(d.get("portfolios") or [], key=lambda p: 0 if p.get("id") == aktif else 1)
    portfoyler = []
    for p in liste:
        try:
            portfoyler.append(_portfoy(p))
        except Exception as e:
            log("apex: %s özeti alınamadı: %s" % (p.get("name"), e))
    if liste and not portfoyler:
        return {"ok": False, "hata": "Portföy özeti alınamadı", "ts": time.time(), "portfoyler": []}
    return {"ok": True, "hata": "", "ts": time.time(), "portfoyler": portfoyler}


def _dongu():
    while True:
        try:
            yeni = _yokla()
        except Exception as e:
            yeni = {"ok": False, "hata": "Okuma hatası: %s" % e, "ts": time.time(), "portfoyler": []}
        with _kilit:
            # bağlantı koparsa son iyi veriyi koru (slaytlar boş kalmasın), sadece hata bilgisini ekle
            if not yeni["ok"] and _veri.get("portfoyler"):
                _veri.update({"ok": False, "hata": yeni["hata"], "kapali": yeni.get("kapali", False)})
            else:
                _veri.clear()
                _veri.update(yeni)
        time.sleep(AYAR["yenile"] if yeni["ok"] else 15)


def _node():
    yol = shutil.which("node")
    if yol:
        return yol
    for aday in (r"C:\Program Files\nodejs\node.exe", r"C:\Program Files (x86)\nodejs\node.exe"):
        if os.path.exists(aday):
            return aday
    return None


def _baslat():
    """APEX sunucusunu konsol penceresi açmadan başlatır (zaten açıksa dokunmaz)."""
    if _istek("/api/health", timeout=2)[0] == 200:
        return "zaten açık"
    if time.time() - _ac_ts[0] < 20:
        return "başlatılıyor"
    klasor = AYAR["klasor"]
    node = _node()
    if not node:
        raise RuntimeError("Node.js bulunamadı")
    if not os.path.exists(os.path.join(klasor, "server", "index.ts")):
        raise RuntimeError("APEX klasörü bulunamadı: %s" % klasor)
    bayrak = (CREATE_NO_WINDOW | CREATE_NEW_PROCESS_GROUP) if IS_WIN else 0
    subprocess.Popen([node, os.path.join("server", "index.ts")], cwd=klasor, creationflags=bayrak,
                     stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    _ac_ts[0] = time.time()
    log("apex: sunucu başlatıldı (%s)" % klasor)
    return "başlatıldı"


def _bekci():
    """APEX hep açık kalsın: 30 sn'de bir bakar, kapalıysa başlatır. Üst üste çöküyorsa bekleme 5 dk'ya kadar uzar."""
    time.sleep(AYAR["otomatik_bekle"])
    hata = 0                                  # son ayağa kalkıştan beri başarısız başlatma sayısı
    while True:
        try:
            if _istek("/api/health", timeout=2)[0] == 200:
                hata = 0
            elif _baslat() == "başlatıldı":
                hata += 1
        except Exception as e:
            log("apex: otomatik başlatma başarısız: %s" % e)
            hata += 1
        time.sleep(min(30 * 2 ** max(hata - 1, 0), 300))


@on_start
def basla():
    threading.Thread(target=_dongu, name="apex", daemon=True).start()
    # klasöre erişilemiyorsa (başka Windows kullanıcısı) başlatma denenmez
    if AYAR["otomatik_ac"] and os.path.isfile(os.path.join(AYAR["klasor"], "server", "index.ts")):
        threading.Thread(target=_bekci, name="apex-ac", daemon=True).start()


def _anlik():
    with _kilit:
        return json.loads(json.dumps(_veri))


def _sistem():
    """Sistem sekmesinin son ölçümü → slayt için sade sözlük (ölçüm yoksa None)."""
    d = sistem.latest
    if not d or not AYAR["sistem_slayt"]:
        return None
    info = getattr(sistem, "_info", {}) or {}
    temps = d.get("temps") or {}
    gb = float(sistem.GB)
    vt = info.get("vram_total")
    return {
        "cpu": _sayi(d.get("cpu")), "gpu": _sayi(d.get("gpu")),
        "ram": (d.get("ram_used") or 0) / gb if d.get("ram_total") else None,
        "ram_top": (d.get("ram_total") or 0) / gb if d.get("ram_total") else None,
        "vram": d.get("vram") / gb if _sayi(d.get("vram")) is not None else None,
        "vram_top": vt / gb if vt else None,
        "cpu_c": _sayi(temps.get("cpu")), "gpu_c": _sayi(temps.get("gpu")),
        "cpu_ad": info.get("cpu", ""), "gpu_ad": info.get("gpu", ""),
        "acik": _sayi(d.get("uptime")),
    }


@extra("apex")
def ekstra():
    """Slayt gösterisi her sekmede çalışabilsin diye özet her /api/ui cevabına eklenir (birkaç KB)."""
    d = _anlik()
    d["sistem"] = _sistem()
    d["ayar"] = {"slayt": AYAR["slayt"], "bosta_sn": AYAR["bosta_sn"], "slayt_sn": AYAR["slayt_sn"],
                 "muzik_varken": AYAR["muzik_varken"]}
    return d


@tab("apex", "Portföy", icon="apex", order=45, poll=30)
def view():
    return [{"type": "apex_portfoy", "fill": True, "data": _anlik()}]


@action("apex.ac")
def ac():
    sonuc = _baslat()
    return sonuc


@action("apex.yenile")
def yenile():
    _gecmis.clear()
    yeni = _yokla()
    with _kilit:
        _veri.clear()
        _veri.update(yeni)
    return yeni["ok"]


def _tl(v, para):
    if v is None:
        return "—"
    s = "{:,.0f}".format(abs(v)).replace(",", ".")
    isaret = "-" if v < 0 else ""
    return (isaret + "₺" + s) if para == "TRY" else ("%s%s %s" % (isaret, s, para))


@focus(priority=20)
def rozet():
    """Odak adasında küçük rozet: toplam değer + bugünkü değişim. Dokununca Portföy sekmesi."""
    if not AYAR["rozet"]:
        return None
    d = _anlik()
    if not d.get("portfoyler"):
        return None
    p = d["portfoyler"][0]
    gun = p.get("gun_yuzde")
    rozet_metni = ("%+.1f%%" % (gun * 100)).replace(".", ",") if gun is not None else None
    return {
        "kind": "apex", "title": _tl(p.get("toplam") if p.get("toplam") is not None else p.get("fiyatli"), p.get("para")),
        "sub": p.get("ad") or "Portföy", "icon": "apex", "badge": rozet_metni, "priority": 20, "tab": "apex",
    }
