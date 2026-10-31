package pckumanda;

import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.TimeUnit;
import java.util.function.Supplier;

/**
 * PC Kumanda köprüsü (sadece istemci). Oyuncunun konumunu saniyede 10 kez yerel kumandaya
 * (http://127.0.0.1:8765/api/mc) gönderir. Sunucuya hiçbir şey göndermez; tek istisna, kumanda
 * istediğinde (yeni oturum, seed bilinmiyor) bir kez "/seed" komutunu çalıştırmasıdır.
 *
 * Minecraft 26.x kodu karıştırılmadığı için Mojang adlarına yansıma (reflection) ile erişilir;
 * Minecraft'a derleme anında bağımlılık yoktur, bu yüzden küçük sürüm farklarında kırılmaz.
 */
public class Bridge implements net.fabricmc.api.ClientModInitializer {
    private static final String URL = System.getProperty("pckumanda.url", "http://127.0.0.1:8765/api/mc");

    private Method getInstance, submit, getX, getY, getZ, getYRot, level, dimension, identifier,
            getCurrentServer, isRealm, hasSingle, getSingle, overworld, getSeed, getWorldData, getLevelName,
            getConnection, sendCommand;
    private Field playerF, sdName, sdIp, gameDirF;
    private Object lastConn;
    private int session;
    private volatile boolean seedAskedThisSession;

    @Override
    public void onInitializeClient() {
        Thread t = new Thread(this::loop, "PCKumanda-Bridge");
        t.setDaemon(true);
        t.start();
    }

    private void bind() throws Exception {
        Class<?> mc = Class.forName("net.minecraft.client.Minecraft");
        getInstance = mc.getMethod("getInstance");
        submit = mc.getMethod("submit", Supplier.class);
        playerF = mc.getField("player");
        gameDirF = mc.getField("gameDirectory");   // CurseForge/Prism instance klasörü -> logs/latest.log burada
        getCurrentServer = mc.getMethod("getCurrentServer");
        hasSingle = mc.getMethod("hasSingleplayerServer");
        getSingle = mc.getMethod("getSingleplayerServer");
        getConnection = mc.getMethod("getConnection");
        Class<?> ent = Class.forName("net.minecraft.world.entity.Entity");
        getX = ent.getMethod("getX");
        getY = ent.getMethod("getY");
        getZ = ent.getMethod("getZ");
        getYRot = ent.getMethod("getYRot");
        level = ent.getMethod("level");
        dimension = Class.forName("net.minecraft.world.level.Level").getMethod("dimension");
        identifier = Class.forName("net.minecraft.resources.ResourceKey").getMethod("identifier");
        Class<?> sd = Class.forName("net.minecraft.client.multiplayer.ServerData");
        isRealm = sd.getMethod("isRealm");
        sdName = sd.getField("name");
        sdIp = sd.getField("ip");
        Class<?> srv = Class.forName("net.minecraft.server.MinecraftServer");
        overworld = srv.getMethod("overworld");
        getWorldData = srv.getMethod("getWorldData");
        getSeed = Class.forName("net.minecraft.server.level.ServerLevel").getMethod("getSeed");
        getLevelName = Class.forName("net.minecraft.world.level.storage.WorldData").getMethod("getLevelName");
        sendCommand = Class.forName("net.minecraft.client.multiplayer.ClientPacketListener").getMethod("sendCommand", String.class);
    }

    private static String esc(String s) {
        if (s == null) return "";
        StringBuilder b = new StringBuilder();
        for (char c : s.toCharArray()) {
            if (c == '"' || c == '\\') b.append('\\').append(c);
            else if (c < 0x20) b.append(' ');
            else b.append(c);
        }
        return b.toString();
    }

    /** Ana oyun iş parçacığında çalışır: anlık durum JSON'u (dünyada değilse null). */
    private String snapshot(Object mc) {
        try {
            Object p = playerF.get(mc);
            if (p == null) return null;
            Object conn = getConnection.invoke(mc);
            if (conn != lastConn) { lastConn = conn; session++; seedAskedThisSession = false; }
            String dim = String.valueOf(identifier.invoke(dimension.invoke(level.invoke(p))));
            String kind, name = "", seed = "";
            if ((Boolean) hasSingle.invoke(mc)) {
                Object s = getSingle.invoke(mc);
                kind = "single";
                name = (String) getLevelName.invoke(getWorldData.invoke(s));
                seed = String.valueOf(getSeed.invoke(overworld.invoke(s)));
            } else {
                Object sd = getCurrentServer.invoke(mc);
                if (sd != null && (Boolean) isRealm.invoke(sd)) { kind = "realm"; name = (String) sdName.get(sd); }
                else if (sd != null) { kind = "server"; name = (String) sdIp.get(sd); }
                else { kind = "realm"; name = "realms"; }   // Realms'te ServerData bazen boş gelir
            }
            String gameDir = String.valueOf(((java.io.File) gameDirF.get(mc)).getAbsolutePath());
            return String.format(java.util.Locale.ROOT,
                    "{\"x\":%.2f,\"y\":%.2f,\"z\":%.2f,\"yaw\":%.1f,\"dim\":\"%s\",\"kind\":\"%s\",\"world\":\"%s\",\"seed\":\"%s\",\"session\":%d,\"gameDir\":\"%s\"}",
                    (Double) getX.invoke(p), (Double) getY.invoke(p), (Double) getZ.invoke(p), (Float) getYRot.invoke(p),
                    esc(dim), kind, esc(name), seed, session, esc(gameDir));
        } catch (Throwable t) {
            return null;
        }
    }

    private void askSeed(Object mc) {
        try {
            submit.invoke(mc, (Supplier<Object>) () -> {
                try {
                    Object conn = getConnection.invoke(mc);
                    if (conn != null) sendCommand.invoke(conn, "seed");
                } catch (Throwable ignored) { }
                return null;
            });
        } catch (Throwable ignored) { }
    }

    @SuppressWarnings("unchecked")
    private void loop() {
        try {
            bind();
        } catch (Throwable t) {
            System.err.println("[PCKumanda] bağlanamadı: " + t);
            return;
        }
        HttpClient http = HttpClient.newBuilder().connectTimeout(Duration.ofMillis(800)).build();
        int fails = 0;
        while (true) {
            long wait = 100;          // saniyede 10 konum (haritada gecikme ~0,1 sn)
            try {
                Object mc = getInstance.invoke(null);
                String json = null;
                if (mc != null) {
                    CompletableFuture<String> f = (CompletableFuture<String>) submit.invoke(mc, (Supplier<String>) () -> snapshot(mc));
                    json = f.get(1, TimeUnit.SECONDS);
                }
                if (json == null) { json = "{\"inWorld\":false}"; wait = 2000; }
                HttpRequest req = HttpRequest.newBuilder(URI.create(URL)).timeout(Duration.ofSeconds(1))
                        .header("Content-Type", "application/json")
                        .POST(HttpRequest.BodyPublishers.ofString(json)).build();
                String resp = http.send(req, HttpResponse.BodyHandlers.ofString()).body();
                fails = 0;
                if (resp.contains("\"need_seed\":true") && !seedAskedThisSession && mc != null) {
                    seedAskedThisSession = true;
                    askSeed(mc);
                }
            } catch (Throwable t) {
                fails++;
                wait = Math.min(10000, 1000L * fails);     // kumanda kapalıysa yavaşla
            }
            try { Thread.sleep(wait); } catch (InterruptedException e) { return; }
        }
    }
}
