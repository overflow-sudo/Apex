"""
Minecraft (Java 26.x) canlı konum + seed haritası.
  - "PC Kumanda Bridge" Fabric modu (mod/) saniyede 10 kez POST /api/mc gönderir:
    {x, y, z, yaw, dim, kind: single|realm|server, world, seed (tek oyunculuda), session, gameDir}
    gameDir: oyunun çalıştığı klasör (CurseForge instance'ı vb.) -> latest.log oradan okunur.
  - Seed: tek oyunculuda moddan gelir. Realm/sunucuda her yeni oturumda moda need_seed=true dönülür, mod bir kez
    "/seed" çalıştırır, cevap latest.log'daki [CHAT] satırından okunur (dil bağımsız: köşeli parantezli uzun sayı).
    Bulunamazsa config.MINECRAFT["default_seed"]. Bulunan seed'ler cache/mc_seeds.json'da (dünya adına göre).
  - Harita karoları: native/mcmap.dll (cubiomes, bu klasörde) -> 256x256 PNG, cache/mc2/<seed>/<dim>/<ölçek>/ altında önbellekli.
  - Yapılar: 2048 bloklık hücreler halinde, bellek önbellekli. Kaleler (stronghold) ve doğma noktası seed başına
    bir kez hesaplanır (128 kale ~2 sn) ve hücrelere eklenir.
  - Biyom: /mc/biome?s&d&x&z ve oyuncunun bulunduğu biyom (SSE "biome"), Türkçe adlarla (BIOME_TR).
  - Kayıtlı yerler: cache/mc_waypoints.json (dünya başına liste), eylemler mc.wp.add / mc.wp.del.
  - Harita sekmesi sadece Minecraft açıkken görünür. Oyun açıkken Minecraft teması gelir.
"""
import ctypes, json, os, re, struct, threading, time, zlib
import config
from core.system import BASE, log
from core.registry import tab, post, route, on_start, stream, action
from modules import games

CFG = getattr(config, "MINECRAFT", {})
HERE = os.path.dirname(os.path.abspath(__file__))     # eklentiler/minecraft
CACHE = os.path.join(BASE, "cache")                    # önbellek çekirdeğin cache/ klasöründe kalır (eski kayıtlar korunur)
SEEDS_FILE = os.path.join(CACHE, "mc_seeds.json")
TARGETS_FILE = os.path.join(CACHE, "mc_targets.json")
WP_FILE = os.path.join(CACHE, "mc_waypoints.json")
DIMS = {"minecraft:overworld": 0, "minecraft:the_nether": -1, "minecraft:the_end": 1}
DIM_NAMES = {0: "Overworld", -1: "Nether", 1: "End"}
# cubiomes StructureType numaraları -> (kısa, Türkçe ad, renk, anahtar, en uzak zum [blok/piksel])
# Sık görülen küçük yapılar sadece yakın görünümde çizilir (telefon ekranı dolmasın).
STRUCTS = {
    5: ("K", "Köy", "#f0c040", "village", 16),
    10: ("Ka", "Yağmacı karakolu", "#c04040", "outpost", 16),
    9: ("Ko", "Orman konağı", "#8b5a2b", "mansion", 16),
    8: ("An", "Okyanus anıtı", "#30b0c0", "monument", 16),
    13: ("AŞ", "Antik şehir", "#2a6ad0", "ancient", 16),
    1000: ("Kl", "Kale (stronghold)", "#ffffff", "stronghold", 16),
    1001: ("D", "Doğma noktası", "#ff70c0", "spawn", 16),
    1: ("ÇT", "Çöl tapınağı", "#e0c070", "desert", 16),
    2: ("OT", "Orman tapınağı", "#40a040", "jungle", 16),
    3: ("CK", "Cadı kulübesi", "#7a50a0", "hut", 16),
    4: ("İ", "İglo", "#e0f0ff", "igloo", 16),
    11: ("YP", "Yıkık portal", "#9040e0", "portal", 8),
    7: ("BG", "Batık gemi", "#b08850", "shipwreck", 8),
    6: ("OK", "Okyanus kalıntısı", "#70a0a0", "oceanruin", 8),
    24: ("DO", "Deneme odaları", "#d07a30", "trial", 4),
    23: ("İK", "İz kalıntıları", "#a08060", "trail", 4),
    16: ("ÇK", "Çöl kuyusu", "#d8c890", "well", 4),
    14: ("H", "Gömülü hazine", "#ffd700", "treasure", 2),
    18: ("NK", "Nether kalesi", "#a03030", "fortress", 16),
    19: ("B", "Bastion", "#505050", "bastion", 16),
    12: ("YP", "Yıkık portal", "#9040e0", "portal", 8),
    20: ("ŞE", "End şehri", "#d0a0e0", "endcity", 16),
}
# boyut -> o boyutta görülebilen anahtarlar (katman menüsü için, sıralı)
DIM_KEYS = {0: ["village", "outpost", "mansion", "monument", "ancient", "stronghold", "spawn", "desert", "jungle", "hut",
                "igloo", "portal", "shipwreck", "oceanruin", "trial", "trail", "well", "treasure"],
            -1: ["fortress", "bastion", "portal"], 1: ["endcity"]}

# cubiomes İngilizce biyom adı -> Türkçe (oyundaki Türkçe adlara yakın)
BIOME_TR = {
    "ocean": "Okyanus", "deep_ocean": "Derin okyanus", "warm_ocean": "Ilık okyanus", "lukewarm_ocean": "Ilıman okyanus",
    "deep_lukewarm_ocean": "Derin ılıman okyanus", "cold_ocean": "Soğuk okyanus", "deep_cold_ocean": "Derin soğuk okyanus",
    "frozen_ocean": "Donmuş okyanus", "deep_frozen_ocean": "Derin donmuş okyanus", "river": "Nehir",
    "frozen_river": "Donmuş nehir", "beach": "Kumsal", "snowy_beach": "Karlı kumsal", "stony_shore": "Taşlı kıyı",
    "plains": "Ovalar", "sunflower_plains": "Ayçiçekli ovalar", "snowy_plains": "Karlı ovalar", "ice_spikes": "Buz dikenleri",
    "desert": "Çöl", "swamp": "Bataklık", "mangrove_swamp": "Mangrov bataklığı", "forest": "Orman",
    "flower_forest": "Çiçekli orman", "birch_forest": "Huş ormanı", "old_growth_birch_forest": "Yaşlı huş ormanı",
    "dark_forest": "Kara orman", "pale_garden": "Solgun bahçe", "taiga": "Tayga", "snowy_taiga": "Karlı tayga",
    "old_growth_pine_taiga": "Yaşlı çam taygası", "old_growth_spruce_taiga": "Yaşlı ladin taygası",
    "savanna": "Savan", "savanna_plateau": "Savan platosu", "windswept_savanna": "Rüzgârlı savan",
    "jungle": "Cengel", "sparse_jungle": "Seyrek cengel", "bamboo_jungle": "Bambu cengeli",
    "badlands": "Kızıl çorak", "wooded_badlands": "Ağaçlı kızıl çorak", "eroded_badlands": "Aşınmış kızıl çorak",
    "windswept_hills": "Rüzgârlı tepeler", "windswept_gravelly_hills": "Rüzgârlı çakıllı tepeler",
    "windswept_forest": "Rüzgârlı orman", "meadow": "Çayır", "cherry_grove": "Kiraz bahçesi", "grove": "Koru",
    "snowy_slopes": "Karlı yamaçlar", "jagged_peaks": "Sivri zirveler", "frozen_peaks": "Donmuş zirveler",
    "stony_peaks": "Taşlı zirveler", "mushroom_fields": "Mantar tarlaları", "dripstone_caves": "Damlataş mağaraları",
    "lush_caves": "Yemyeşil mağaralar", "deep_dark": "Derin karanlık",
    "nether_wastes": "Nether çorakları", "soul_sand_valley": "Ruh kumu vadisi", "crimson_forest": "Kızıl orman",
    "warped_forest": "Çarpık orman", "basalt_deltas": "Bazalt deltaları",
    "the_end": "End", "small_end_islands": "Küçük End adaları", "end_midlands": "End ortaları",
    "end_highlands": "End yaylaları", "end_barrens": "End çorakları", "the_void": "Boşluk",
}

_lock = threading.Lock()
_last = {}            # son paket
_last_at = 0.0        # son paket zamanı (oyunda)
_seen_at = 0.0        # Minecraft'ın en son görüldüğü an (menüde olsa bile)
_asked_sessions = set()
_pending = None       # (dünya anahtarı, bitiş zamanı) — /seed cevabı bekleniyor
_seeds = None
_dll = None
_dll_err = ""
_tile_sem = threading.Semaphore(2)
_structs_cache = {}
_pos_cond = threading.Condition()   # her yeni konumda uyanır (SSE akışı)
_pos_seq = 0
_targets = None
_specials = {}       # seed -> [[kod, x, z], ...] kaleler + doğma noktası (seed başına bir kez)
_spec_lock = threading.Lock()
_wps = None
_pbiome = {"key": None, "at": 0.0, "name": None}


# ---------------- seed deposu ----------------
def _load_seeds():
    global _seeds
    if _seeds is None:
        try:
            with open(SEEDS_FILE, encoding="utf-8") as f:
                _seeds = json.load(f)
        except Exception:
            _seeds = {}
    return _seeds


def _save_seed(key, seed):
    with _lock:
        s = _load_seeds()
        if s.get(key) == str(seed):
            return
        s[key] = str(seed)
        try:
            os.makedirs(CACHE, exist_ok=True)
            with open(SEEDS_FILE, "w", encoding="utf-8") as f:
                json.dump(s, f, ensure_ascii=False, indent=1)
        except Exception as e:
            log("seed kaydedilemedi:", e)
    log("minecraft seed: %s -> %s" % (key, seed))


def _world_key(p):
    return "%s:%s" % (p.get("kind") or "?", p.get("world") or "?")


def current_seed(p=None):
    """(seed, kaynak) — kaynak: 'dünya' (otomatik bulundu) ya da 'varsayılan'."""
    p = p or _last
    if p.get("seed"):
        return int(p["seed"]), "dünya"
    s = _load_seeds().get(_world_key(p))
    if s:
        return int(s), "dünya"
    d = CFG.get("default_seed")
    return (int(d), "varsayılan") if d is not None else (None, "")


# ---------------- moddan gelen paketler ----------------
@post("/api/mc")
def from_mod(body):
    global _last, _last_at, _seen_at, _pending
    now = time.time()
    _seen_at = now
    if not body or body.get("inWorld") is False:
        return {"ok": True}
    _last = body
    _last_at = now
    _notify()
    key = _world_key(body)
    if body.get("seed"):
        _save_seed(key, body["seed"])
        return {"ok": True}
    sess = (key, body.get("session"))
    if sess not in _asked_sessions:
        _asked_sessions.add(sess)
        _pending = (key, now + 30)
        return {"ok": True, "need_seed": True}
    return {"ok": True}


def _notify():
    global _pos_seq
    with _pos_cond:
        _pos_seq += 1
        _pos_cond.notify_all()


def active():
    return time.time() - _last_at < 5


@games.detector
def _detect():
    return "minecraft" if active() else None


# ---------------- latest.log: /seed cevabı ----------------
SEED_RE = re.compile(r"\[CHAT\].*\[(-?\d{5,20})\]")


def _log_path():
    """Mod oyunun çalıştığı klasörü bildirir (CurseForge/Prism instance'ları .minecraft'ta değil)."""
    if CFG.get("log"):
        return CFG["log"]
    gd = _last.get("gameDir")
    if gd:
        return os.path.join(gd, "logs", "latest.log")
    return os.path.join(os.environ.get("APPDATA", ""), ".minecraft", "logs", "latest.log")


def _tail():
    global _pending
    pos, path = None, None
    while True:
        time.sleep(1)
        try:
            if time.time() - _seen_at > 60:     # Minecraft açık değilse dosyaya dokunma
                pos = None
                continue
            p = _log_path()
            if p != path:                        # farklı instance -> baştan
                path, pos = p, None
                log("minecraft kayıt dosyası:", path)
            size = os.path.getsize(path)
            if pos is None or size < pos:       # ilk açılış ya da yeni log -> sondan başla
                pos = size
                continue
            if size == pos:
                continue
            with open(path, "rb") as f:
                f.seek(pos)
                chunk = f.read(size - pos)
            pos = size
            for line in chunk.decode("utf-8", "replace").splitlines():
                m = SEED_RE.search(line)
                if not m:
                    continue
                low = line.lower()
                if _pending and time.time() < _pending[1]:
                    _save_seed(_pending[0], m.group(1))
                    _pending = None
                elif ("seed" in low or "tohum" in low) and _last:
                    _save_seed(_world_key(_last), m.group(1))   # elle /seed yazıldıysa da yakala
        except Exception:
            pos = None


@on_start
def start():
    if os.name == "nt":
        threading.Thread(target=_tail, daemon=True).start()


# ---------------- harita (cubiomes DLL) ----------------
def _lib():
    global _dll, _dll_err
    if _dll or _dll_err:
        return _dll
    name = "mcmap.dll" if os.name == "nt" else "libmcmap.so"
    try:
        d = ctypes.CDLL(os.path.join(HERE, "native", name))
        d.mcmap_tile.argtypes = [ctypes.c_uint64, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
                                 ctypes.c_int, ctypes.c_int, ctypes.c_char_p]
        d.mcmap_structs.argtypes = [ctypes.c_uint64, ctypes.c_int] + [ctypes.c_int] * 4 + \
                                   [ctypes.POINTER(ctypes.c_int), ctypes.c_int]
        d.mcmap_biome.argtypes = [ctypes.c_uint64, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int]
        d.mcmap_biome_str.argtypes = [ctypes.c_int]
        d.mcmap_biome_str.restype = ctypes.c_char_p
        d.mcmap_spawn.argtypes = [ctypes.c_uint64, ctypes.POINTER(ctypes.c_int)]
        d.mcmap_strongholds.argtypes = [ctypes.c_uint64, ctypes.POINTER(ctypes.c_int), ctypes.c_int]
        _dll = d
    except Exception as e:
        _dll_err = str(e)
        log("harita kütüphanesi yüklenemedi:", e)
    return _dll


def _png(w, h, rgb):
    raw = b"".join(b"\x00" + rgb[y * w * 3:(y + 1) * w * 3] for y in range(h))

    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xffffffff)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw, 6)) + chunk(b"IEND", b""))


def _u64(seed):
    return int(seed) & 0xFFFFFFFFFFFFFFFF


@route("/mc/tile")
def tile(q):
    """?s=seed&d=dim&sc=ölçek(4|16|64|256)&x=karo&y=karo -> 256x256 PNG (karo = 256*ölçek blok)."""
    seed, dim, sc, tx, ty = int(q["s"]), int(q.get("d", 0)), int(q.get("sc", 16)), int(q["x"]), int(q["y"])
    if sc not in (4, 16, 64, 256) or dim not in (0, -1, 1):
        return None
    path = os.path.join(CACHE, "mc2", str(seed), str(dim), str(sc), "%d_%d.png" % (tx, ty))
    try:
        with open(path, "rb") as f:
            return "image/png", f.read()
    except OSError:
        pass
    lib = _lib()
    if not lib:
        return None
    buf = ctypes.create_string_buffer(256 * 256 * 3)
    with _tile_sem:
        err = lib.mcmap_tile(_u64(seed), dim, sc, tx * 256, ty * 256, 256, 256, buf)
    if err:
        return None
    data = _png(256, 256, buf.raw)
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            f.write(data)
    except OSError:
        pass
    return "image/png", data


def _entry(t, x, z):
    k = STRUCTS[t]
    return [k[0], x, z, k[1], k[2], k[4], k[3]]


def _special(seed):
    """Kaleler + doğma noktası: pahalı (~2 sn), seed başına bir kez."""
    with _spec_lock:
        if seed in _specials:
            return _specials[seed]
        lib = _lib()
        res = []
        if lib:
            out = (ctypes.c_int * 256)()
            n = lib.mcmap_strongholds(_u64(seed), out, 128)
            res = [[1000, out[i * 2], out[i * 2 + 1]] for i in range(max(n, 0))]
            if lib.mcmap_spawn(_u64(seed), out) == 0:
                res.append([1001, out[0], out[1]])
        _specials[seed] = res
        return res


@route("/mc/structs")
def structs(q):
    """?s=seed&d=dim&cx=hücre&cz=hücre -> 2048x2048 bloklık hücredeki yapılar (JSON).
    Her öğe: [kısa, x, z, ad, renk, en uzak zum, anahtar]."""
    seed, dim, cx, cz = int(q["s"]), int(q.get("d", 0)), int(q["cx"]), int(q["cz"])
    key = (seed, dim, cx, cz)
    if key not in _structs_cache:
        lib = _lib()
        if not lib:
            return None
        out = (ctypes.c_int * 3000)()
        x0, z0 = cx * 2048, cz * 2048
        with _tile_sem:
            n = lib.mcmap_structs(_u64(seed), dim, x0, z0, x0 + 2047, z0 + 2047, out, 1000)
        res = []
        for i in range(max(n, 0)):
            t = out[i * 3]
            if t in STRUCTS:
                res.append(_entry(t, out[i * 3 + 1], out[i * 3 + 2]))
        if dim == 0:
            for t, x, z in _special(seed):
                if x0 <= x < x0 + 2048 and z0 <= z < z0 + 2048:
                    res.append(_entry(t, x, z))
        _structs_cache[key] = res
        if len(_structs_cache) > 2000:
            _structs_cache.clear()
    return "application/json", json.dumps(_structs_cache[key], ensure_ascii=False).encode("utf-8")


# ---------------- biyom ----------------
CAVES = ("dripstone_caves", "lush_caves", "deep_dark")


def biome_at(seed, dim, x, z, y=None):
    """y verilmezse yüzey biyomu: yükseklik bilinmediği için 63'ten başlar, mağara biyomu çıkarsa yukarı çıkar."""
    lib = _lib()
    if not lib or seed is None:
        return None
    en = None
    for yy in ([int(y)] if y is not None else [63, 90, 120, 160]):
        bid = lib.mcmap_biome(_u64(seed), int(dim), int(x), yy, int(z))
        if bid < 0:
            return None
        en = (lib.mcmap_biome_str(bid) or b"").decode("ascii", "replace")
        if en not in CAVES:
            break
    return BIOME_TR.get(en, en.replace("_", " ").capitalize())


@route("/mc/biome")
def biome_route(q):
    name = biome_at(int(q["s"]), int(q.get("d", 0)), int(float(q["x"])), int(float(q["z"])))
    return "application/json", json.dumps({"name": name}, ensure_ascii=False).encode("utf-8")


def player_biome():
    """Oyuncunun biyomu: 4 bloktan fazla yer değiştirince ya da en geç 2 sn'de bir yeniden hesaplanır."""
    p = _last
    if p.get("x") is None:
        return None
    seed = current_seed(p)[0]
    dim = DIMS.get(p.get("dim"), 0)
    key = (seed, dim, int(p["x"]) // 4, int(p.get("y") or 64) // 4, int(p["z"]) // 4)
    now = time.time()
    if key != _pbiome["key"] and now - _pbiome["at"] > 0.25:
        _pbiome["key"], _pbiome["at"] = key, now
        try:
            _pbiome["name"] = biome_at(seed, dim, p["x"], p["z"], p.get("y"))   # oyuncunun gerçek yüksekliği
        except Exception:
            _pbiome["name"] = None
    return _pbiome["name"]


# ---------------- kayıtlı yerler ----------------
def _load_wps():
    global _wps
    if _wps is None:
        try:
            with open(WP_FILE, encoding="utf-8") as f:
                _wps = json.load(f)
        except Exception:
            _wps = {}
    return _wps


def _save_wps():
    try:
        os.makedirs(CACHE, exist_ok=True)
        with open(WP_FILE, "w", encoding="utf-8") as f:
            json.dump(_wps, f, ensure_ascii=False, indent=1)
    except OSError as e:
        log("kayıtlı yerler yazılamadı:", e)


def waypoints():
    return _load_wps().get(_world_key(_last), []) if _last else []


@action("mc.wp.add")
def wp_add(x=0, z=0, dim=0, name=""):
    """Yer kaydet; güncel listeyi döner."""
    with _lock:
        w = _load_wps()
        lst = w.setdefault(_world_key(_last) if _last else "?", [])
        nid = max([p.get("id", 0) for p in lst] + [0]) + 1
        lst.append({"id": nid, "name": (name or "").strip()[:30] or "Yer %d" % nid,
                    "x": int(float(x)), "z": int(float(z)), "dim": int(dim)})
        _save_wps()
        return lst


@action("mc.wp.del")
def wp_del(id=0):
    with _lock:
        w = _load_wps()
        key = _world_key(_last) if _last else "?"
        w[key] = [p for p in w.get(key, []) if p.get("id") != int(id)]
        _save_wps()
        return w[key]


# ---------------- hedef (dünya başına bir tane, diskte) ----------------
def _load_targets():
    global _targets
    if _targets is None:
        try:
            with open(TARGETS_FILE, encoding="utf-8") as f:
                _targets = json.load(f)
        except Exception:
            _targets = {}
    return _targets


def current_target():
    return _load_targets().get(_world_key(_last)) if _last else None


@action("mc.target")
def set_target(x=None, z=None, dim=0, name=""):
    """Hedef koy (x, z, boyut) ya da x=None ile kaldır."""
    t = _load_targets()
    key = _world_key(_last) if _last else "?"
    if x is None:
        t.pop(key, None)
    else:
        t[key] = {"x": int(float(x)), "z": int(float(z)), "dim": int(dim), "name": (name or "")[:40]}
    try:
        os.makedirs(CACHE, exist_ok=True)
        with open(TARGETS_FILE, "w", encoding="utf-8") as f:
            json.dump(t, f, ensure_ascii=False, indent=1)
    except OSError:
        pass
    _notify()


# ---------------- anlık konum akışı (SSE) ----------------
def _live():
    p = _last
    return {"x": p.get("x"), "y": p.get("y"), "z": p.get("z"), "yaw": p.get("yaw"),
            "dim": DIMS.get(p.get("dim"), 0), "active": active(), "target": current_target(), "biome": player_biome()}


@stream("/mc/stream")
def live_stream(q, send):
    """Mod her konum gönderdiğinde (saniyede ~10) telefona anında iletilir. 15 sn olay yoksa canlı tutma satırı."""
    seq = -1
    send(json.dumps(_live()))
    while True:
        with _pos_cond:
            _pos_cond.wait_for(lambda: _pos_seq != seq, timeout=15)
            seq = _pos_seq
        send(json.dumps(_live()))


# ---------------- arayüz ----------------
def _type_codes(dim):
    """Katman menüsü: [(anahtar, örnek kod)] bu boyutta."""
    first = {}
    for c, v in STRUCTS.items():
        first.setdefault(v[3], c)
    return [(k, first[k]) for k in DIM_KEYS.get(dim, [])]


def _recent():
    """Sekme sadece Minecraft açıkken görünür (mod menüde de 2 sn'de bir haber verir; 10 sn ses yoksa kapalı)."""
    return time.time() - _seen_at < 10


def _state():
    p = dict(_last)
    seed, src = current_seed(p)
    if seed is not None and seed not in _specials and _lib():   # kaleleri arka planda önceden hesapla
        threading.Thread(target=_special, args=(seed,), daemon=True).start()
    return {
        "active": active(),
        "x": p.get("x"), "y": p.get("y"), "z": p.get("z"), "yaw": p.get("yaw"),
        "dim": DIMS.get(p.get("dim"), 0), "dimName": DIM_NAMES.get(DIMS.get(p.get("dim"), 0), p.get("dim")),
        "world": p.get("world"), "kind": p.get("kind"),
        "seed": str(seed) if seed is not None else None, "seedSrc": src,
        "structures": CFG.get("structures", True),
        "target": current_target(),
        "waypoints": waypoints(),
        "biome": player_biome(),
        "types": [[k] + [STRUCTS[c][i] for i in (0, 1, 2)] for k, c in _type_codes(DIMS.get(p.get("dim"), 0))],
        "ok": _lib() is not None, "err": _dll_err,
    }


@tab("mcmap", "Harita", icon="map", order=35, poll=4, visible=_recent)   # konum SSE ile anlık geliyor
def view():
    return [{"type": "mcmap", "fill": True, "data": _state()}]
