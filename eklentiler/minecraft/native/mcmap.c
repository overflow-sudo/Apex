/*
 * PC Kumanda - Minecraft seed haritası (cubiomes üzerine ince katman).
 * Python ctypes ile çağrılır (modules/minecraft.py). Her çağrı kendi Generator'ını kurar: thread-safe.
 *
 *   mcmap_version()                    -> kullanılan cubiomes MC sürümü (MC_NEWEST)
 *   mcmap_tile(seed, dim, scale, x, z, w, h, rgb)
 *        dim: 0 overworld, -1 nether, 1 end; scale: 4/16/64 (blok/piksel); x,z: kuzeybatı köşe (scale biriminde)
 *        rgb: w*h*3 bayt çıktı
 *   mcmap_biome(seed, dim, x, y, z)    -> (x, y, z) bloğundaki biyom kimliği; mcmap_biome_str(id) -> İngilizce ad
 *   mcmap_strongholds(seed, out, maxn), mcmap_spawn(seed, out) -> seed başına bir kez (pahalı)
 *   mcmap_structs(seed, dim, x0, z0, x1, z1, out, maxn)
 *        blok koordinatlı kutu içindeki yapılar; out: (tip, x, z) üçlüleri; dönüş: bulunan sayı
 *
 * Derleme (Windows DLL, Linux'tan):  python -m ziglang cc -target x86_64-windows-gnu -O2 -shared \
 *        -o mcmap.dll mcmap.c cubiomes/{noise,biomes,layers,biomenoise,generator,finders,util,quadbase}.c -lm
 */
#include "generator.h"
#include "finders.h"
#include "util.h"
#include <stdlib.h>
#include <string.h>

#ifdef _WIN32
#define EXPORT __declspec(dllexport)
#else
#define EXPORT __attribute__((visibility("default")))
#endif

#define MC MC_NEWEST

static unsigned char g_colors[256][3];
static int g_colors_ready = 0;

EXPORT int mcmap_version(void) { return MC; }

EXPORT int mcmap_tile(uint64_t seed, int dim, int scale, int x, int z, int w, int h, unsigned char *rgb)
{
    if (!g_colors_ready) { initBiomeColors(g_colors); g_colors_ready = 1; }
    Generator *g = (Generator *) malloc(sizeof(Generator));
    if (!g) return -1;
    setupGenerator(g, MC, 0);
    applySeed(g, dim, seed);
    Range r;
    r.scale = scale; r.x = x; r.z = z; r.sx = w; r.sz = h;
    r.y = 64 / scale;   /* deniz seviyesi civarı düzlem (y ölçek biriminde: 4->16, 16->4, 64->1, 256->0) */
    r.sy = 1;
    int *ids = allocCache(g, r);
    if (!ids) { free(g); return -2; }
    int err = genBiomes(g, ids, r);
    /* flip=1: satır 0 = en küçük z (kuzey yukarıda). flip=0 cubiomes'ta görüntüyü dikey ters çevirir! */
    if (!err) biomesToImage(rgb, g_colors, ids, w, h, 1, 1);
    free(ids);
    free(g);
    return err;
}

static const int OVERWORLD_TYPES[] = { Village, Outpost, Mansion, Monument, Ancient_City, Trial_Chambers,
                                       Desert_Pyramid, Jungle_Temple, Swamp_Hut, Igloo, Trail_Ruins,
                                       Ruined_Portal, Ocean_Ruin, Shipwreck, Treasure, Desert_Well };
static const int NETHER_TYPES[] = { Fortress, Bastion, Ruined_Portal_N };
static const int END_TYPES[] = { End_City };

/* floordiv: cubiomes rng.h içinde zaten var */

EXPORT int mcmap_structs(uint64_t seed, int dim, int x0, int z0, int x1, int z1, int *out, int maxn)
{
    Generator *g = (Generator *) malloc(sizeof(Generator));
    if (!g) return -1;
    setupGenerator(g, MC, 0);
    applySeed(g, dim, seed);

    const int *types; int ntypes;
    if (dim == -1) { types = NETHER_TYPES; ntypes = 3; }
    else if (dim == 1) { types = END_TYPES; ntypes = 1; }
    else { types = OVERWORLD_TYPES; ntypes = (int)(sizeof(OVERWORLD_TYPES) / sizeof(int)); }

    int n = 0;
    for (int i = 0; i < ntypes && n < maxn; i++) {
        StructureConfig sc;
        if (!getStructureConfig(types[i], MC, &sc)) continue;
        int reg = sc.regionSize * 16;
        int rx0 = floordiv(x0, reg) - 1, rx1 = floordiv(x1, reg) + 1;
        int rz0 = floordiv(z0, reg) - 1, rz1 = floordiv(z1, reg) + 1;
        for (int rz = rz0; rz <= rz1 && n < maxn; rz++)
            for (int rx = rx0; rx <= rx1 && n < maxn; rx++) {
                Pos p;
                if (!getStructurePos(types[i], MC, seed, rx, rz, &p)) continue;
                if (p.x < x0 || p.x > x1 || p.z < z0 || p.z > z1) continue;
                if (!isViableStructurePos(types[i], g, p.x, p.z, 0)) continue;
                out[n * 3] = types[i]; out[n * 3 + 1] = p.x; out[n * 3 + 2] = p.z;
                n++;
            }
    }
    free(g);
    return n;
}

EXPORT int mcmap_biome(uint64_t seed, int dim, int x, int y, int z)
{
    Generator *g = (Generator *) malloc(sizeof(Generator));
    if (!g) return -1;
    setupGenerator(g, MC, 0);
    applySeed(g, dim, seed);
    int id = getBiomeAt(g, 1, x, y, z);
    free(g);
    return id;
}

EXPORT const char *mcmap_biome_str(int id) { return biome2str(MC, id); }

/* dünya doğma noktası (yaklaşık; ağır bir arama, Python tarafında seed başına bir kez) */
EXPORT int mcmap_spawn(uint64_t seed, int *out)
{
    Generator *g = (Generator *) malloc(sizeof(Generator));
    if (!g) return -1;
    setupGenerator(g, MC, 0);
    applySeed(g, 0, seed);
    Pos p = getSpawn(g);
    out[0] = p.x; out[1] = p.z;
    free(g);
    return 0;
}

/* kaleler (stronghold): seed başına bir kez (128 tanesi ~2 sn), out: (x, z) çiftleri */
EXPORT int mcmap_strongholds(uint64_t seed, int *out, int maxn)
{
    Generator *g = (Generator *) malloc(sizeof(Generator));
    if (!g) return -1;
    setupGenerator(g, MC, 0);
    applySeed(g, 0, seed);
    StrongholdIter sh;
    initFirstStronghold(&sh, MC, seed);
    int n = 0;
    while (n < maxn) {
        int more = nextStronghold(&sh, g);
        out[n * 2] = sh.pos.x; out[n * 2 + 1] = sh.pos.z;
        n++;
        if (more <= 0) break;
    }
    free(g);
    return n;
}
