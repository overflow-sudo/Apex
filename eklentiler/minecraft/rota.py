"""
Tekne / at rotası: biyom ızgarasında A* (sadece Overworld).
- Izgara mevcut mcmap_tile ile üretilir (DLL değişmedi): karo RGB renkleri -> biyom kimliği. Renk tablosu öğrenilerek
  dolar: bilinmeyen bir renk için çevresi aynı renk olan bir hücrenin ortasında mcmap_biome sorulur (renkler seed'den
  bağımsız, tablo süreç boyunca tutulur).
- Ölçek mesafeye göre: 4 blok/hücre (kısa, nehirler görünür) -> 16 -> 64. Izgara en fazla ~520 hücre kenar.
  16 ve 64 ölçekte dar nehirler kaybolabilir; uzun tekne rotaları okyanus ağırlıklı çıkar.
- Maliyet: tekne suda 1, kıyıda 4, karada 30 (taşıma); at düzlükte 1, ormanda 1.6, sık bitkide 3, tepede 2.5,
  dağ zirvesinde 8, nehirde 5 (yüzme), okyanusta 40.
- Sonuç kategori değişimlerinde bölünür, her parça Ramer-Douglas-Peucker ile sadeleşir. Tekne rotasında karadan geçen
  parçalar "kara" olarak işaretlenir (telefonda kesikli çizilir).
"""
import ctypes, heapq, math, threading

MAX_CELLS = 520
_colors = {}                 # (r,g,b) -> biyom adı
_lock = threading.Lock()
_cache = {}                  # (seed, mode, x0, z0, x1, z1 yuvarlanmış) -> sonuç

WATER, SHORE, LAND = "su", "kıyı", "kara"


def _kind(name):
    n = name or ""
    if "ocean" in n or n in ("river", "frozen_river"):
        return "ocean" if "ocean" in n else "river"
    if n in ("beach", "snowy_beach", "stony_shore"):
        return "shore"
    if n in ("swamp", "mangrove_swamp"):
        return "swamp"
    if any(k in n for k in ("peaks", "slopes")) or n in ("jagged_peaks",):
        return "peak"
    if "windswept" in n or n in ("badlands", "eroded_badlands", "wooded_badlands", "grove"):
        return "hill"
    if any(k in n for k in ("jungle", "dark_forest", "bamboo")):
        return "dense"
    if any(k in n for k in ("forest", "taiga", "cherry")):
        return "forest"
    return "flat"


COST = {
    "boat": {"ocean": 1, "river": 1, "shore": 4, "swamp": 2.5, "flat": 30, "forest": 30, "dense": 32, "hill": 40, "peak": 60},
    "horse": {"flat": 1, "shore": 1.2, "forest": 1.6, "hill": 2.5, "dense": 3, "swamp": 3, "peak": 8, "river": 5, "ocean": 40},
}


def _cat(mode, kind):
    if mode == "boat":
        return WATER if kind in ("ocean", "river", "swamp") else SHORE if kind == "shore" else LAND
    return WATER if kind in ("ocean", "river") else LAND


def _grid(lib, seed, sc, gx, gz, w, h):
    """[[biyom türü]] (h satır x w sütun); gx, gz: kuzeybatı köşe (ölçek biriminde)."""
    buf = ctypes.create_string_buffer(w * h * 3)
    if lib.mcmap_tile(seed, 0, sc, gx, gz, w, h, buf):
        raise RuntimeError("biyom ızgarası üretilemedi")
    raw = buf.raw
    px = [raw[i:i + 3] for i in range(0, w * h * 3, 3)]
    out = [None] * (w * h)
    for i, c in enumerate(px):
        name = _colors.get(c)
        if name is None:
            name = _learn(lib, seed, sc, gx, gz, w, h, px, c)
        out[i] = _kind(name)
    return out


def _learn(lib, seed, sc, gx, gz, w, h, px, c):
    """Bu rengin biyomunu bul: komşuları da aynı renk olan bir hücrenin ortasını sor (sınırda yanılmasın)."""
    best = None
    for i, v in enumerate(px):
        if v != c:
            continue
        x, z = i % w, i // w
        best = best or (x, z)
        if 0 < x < w - 1 and 0 < z < h - 1 and all(px[(z + dz) * w + x + dx] == c for dx in (-1, 0, 1) for dz in (-1, 0, 1)):
            best = (x, z)
            break
    bx, bz = (gx + best[0]) * sc + sc // 2, (gz + best[1]) * sc + sc // 2
    name = ""
    for y in (64, 90, 120, 160):              # y=64 tepelerde yeraltına düşebilir: mağara biyomu çıkarsa yukarı çık
        bid = lib.mcmap_biome(seed, 0, bx, y, bz)
        name = (lib.mcmap_biome_str(bid) or b"").decode("ascii", "replace") if bid >= 0 else ""
        if name not in ("dripstone_caves", "lush_caves", "deep_dark"):
            break
    with _lock:
        _colors[c] = name
    return name


def _rdp(pts, eps):
    if len(pts) < 3:
        return pts
    (ax, az), (bx, bz) = pts[0], pts[-1]
    dx, dz = bx - ax, bz - az
    L = math.hypot(dx, dz) or 1e-9
    far, idx = -1, 0
    for i in range(1, len(pts) - 1):
        d = abs(dz * (pts[i][0] - ax) - dx * (pts[i][1] - az)) / L
        if d > far:
            far, idx = d, i
    if far <= eps:
        return [pts[0], pts[-1]]
    return _rdp(pts[:idx + 1], eps)[:-1] + _rdp(pts[idx:], eps)


def route(lib, seed, mode, x0, z0, x1, z1):
    """-> {"pts": [[x, z], ...], "segs": ["su"|"kıyı"|"kara", ...] (nokta arası), "len", "land", "scale"} ya da {"error"}."""
    if mode not in COST:
        return {"error": "bilinmeyen rota türü"}
    key = (seed, mode, int(x0) >> 3, int(z0) >> 3, int(x1) >> 3, int(z1) >> 3)
    if key in _cache:
        return _cache[key]
    span = max(abs(x1 - x0), abs(z1 - z0))
    margin = max(256, span * 0.25)
    for sc in (4, 16, 64):
        if (span + 2 * margin) / sc <= MAX_CELLS:
            break
    else:
        return {"error": "çok uzak (kuş uçuşu kullan)"}
    gx, gz = int(math.floor((min(x0, x1) - margin) / sc)), int(math.floor((min(z0, z1) - margin) / sc))
    w = int(math.ceil((max(x0, x1) + margin) / sc)) - gx + 1
    h = int(math.ceil((max(z0, z1) + margin) / sc)) - gz + 1
    kinds = _grid(lib, seed, sc, gx, gz, w, h)
    cost = COST[mode]
    cells = [cost[k] for k in kinds]
    sx, sz = int(x0 // sc) - gx, int(z0 // sc) - gz
    tx, tz = int(x1 // sc) - gx, int(z1 // sc) - gz
    start, goal = sz * w + sx, tz * w + tx
    # A*: sekiz yön, adım maliyeti = (iki hücrenin ortalaması) x uzunluk
    INF = float("inf")
    g = {start: 0.0}
    came = {}
    heap = [(0.0, start)]
    R2 = math.sqrt(2)
    steps = [(-1, 0, 1), (1, 0, 1), (0, -1, 1), (0, 1, 1), (-1, -1, R2), (1, -1, R2), (-1, 1, R2), (1, 1, R2)]
    done = set()
    while heap:
        f, cur = heapq.heappop(heap)
        if cur == goal:
            break
        if cur in done:
            continue
        done.add(cur)
        cx, cz = cur % w, cur // w
        gc = g[cur]
        cc = cells[cur]
        for dx, dz, ln in steps:
            nx, nz = cx + dx, cz + dz
            if nx < 0 or nz < 0 or nx >= w or nz >= h:
                continue
            n = nz * w + nx
            if n in done:
                continue
            ng = gc + (cc + cells[n]) * 0.5 * ln
            if ng < g.get(n, INF):
                g[n] = ng
                came[n] = cur
                heapq.heappush(heap, (ng + math.hypot(tx - nx, tz - nz), n))
    if goal not in came and goal != start:
        return {"error": "rota bulunamadı"}
    path = [goal]
    while path[-1] != start:
        path.append(came[path[-1]])
    path.reverse()
    # kategoriye göre parçalara böl, her parçayı sadeleştir
    runs = []
    for c in path:
        cat = _cat(mode, kinds[c])
        p = ((gx + c % w) * sc + sc / 2.0, (gz + c // w) * sc + sc / 2.0)
        if runs and runs[-1][0] == cat:
            runs[-1][1].append(p)
        else:
            if runs:
                runs[-1][1].append(p)            # parçalar birbirine bağlansın
            runs.append([cat, [p]])
    pts, segs = [[float(x0), float(z0)]], []
    for cat, rp in runs:
        rp = _rdp(rp, sc * 1.2)
        for p in rp[1:] if pts and len(rp) > 1 else rp:
            pts.append([round(p[0], 1), round(p[1], 1)])
            segs.append(cat)
    pts.append([float(x1), float(z1)])
    segs.append(segs[-1] if segs else LAND)
    total = land = 0.0
    for i in range(len(pts) - 1):
        d = math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1])
        total += d
        if mode == "boat" and segs[i] == LAND:
            land += d
        elif mode == "horse" and segs[i] == WATER:
            land += d                              # at için "su" uzunluğu (yüzerek geçilecek)
    res = {"pts": pts, "segs": segs, "len": round(total), "land": round(land), "scale": sc, "mode": mode}
    if len(_cache) > 64:
        _cache.clear()
    _cache[key] = res
    return res
