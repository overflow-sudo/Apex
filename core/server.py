"""HTTP sunucusu: web/ klasörünü ve /api uçlarını sunar."""
import json, mimetypes, os, socket, time, traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit
import config
from core import registry
from core.system import BASE, log

WEB = os.path.join(BASE, "web")
TYPES = {".html": "text/html", ".css": "text/css", ".js": "application/javascript",
         ".json": "application/json", ".svg": "image/svg+xml", ".png": "image/png"}


def _plugin_web():
    """[(eklenti, dosya adı, tam yol)] — eklentiler/<ad>/web/ içindeki düz dosyalar (alt klasör yok)."""
    out = []
    for name, d in registry.plugin_dirs():
        w = os.path.join(d, "web")
        if os.path.isdir(w):
            out += [(name, f, os.path.join(w, f)) for f in sorted(os.listdir(w)) if os.path.isfile(os.path.join(w, f))]
    return out


# web dosyalarının (eklentilerinki dahil) son değişme zamanı: arayüz bunu görür, değişirse sayfayı kendiliğinden yeniler
VERSION = str(int(max([os.path.getmtime(os.path.join(WEB, f)) for f in os.listdir(WEB)] +
                      [os.path.getmtime(p) for _, _, p in _plugin_web()] +
                      [os.path.getmtime(os.path.join(BASE, "pc_kumanda.py"))])))


def _index():
    """index.html + yüklenen eklentilerin CSS'leri (</head> önüne) ve JS'leri (app.js'ten sonra)."""
    with open(os.path.join(WEB, "index.html"), encoding="utf-8") as f:
        html = f.read()
    loaded = set(p["id"] for p in registry.PLUGINS)
    css = js = ""
    for name, f, _ in _plugin_web():
        if name not in loaded:
            continue
        url = "/eklenti/%s/%s?v=%s" % (name, f, VERSION)
        if f.endswith(".css"):
            css += '<link rel="stylesheet" href="%s">\n' % url
        elif f.endswith(".js"):
            js += '<script src="%s"></script>\n' % url
    return html.replace("</head>", css + "</head>", 1).replace("</body>", js + "</body>", 1)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def send(self, code, body, ctype="application/json"):
        data = body if isinstance(body, bytes) else body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype + ("; charset=utf-8" if ctype.startswith(("text", "application")) else ""))
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        try:
            self.wfile.write(data)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            pass   # telefon beklemekten vazgeçti (zaman aşımı); sorun değil

    def json(self, code, obj):
        self.send(code, json.dumps(obj, ensure_ascii=False))

    def authed(self):
        return not config.PIN or self.headers.get("X-Pin") == config.PIN

    def sse(self, path):
        """Server-Sent Events: bağlantı açık kalır, her olay 'data: ...' satırı olarak gönderilir."""
        q = {k: v[0] for k, v in parse_qs(urlsplit(self.path).query).items()}
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Connection", "keep-alive")
        self.end_headers()

        def send(text):
            self.wfile.write(("data: %s\n\n" % text).encode("utf-8"))
            self.wfile.flush()
        try:
            registry.STREAMS[path](q, send)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError, OSError):
            pass   # telefon bağlantıyı kapattı

    def plugin_file(self, path):
        # /eklenti/<ad>/<dosya>: sadece yüklü eklentinin web/ klasöründeki düz dosyalar ('..' ve alt klasör yok)
        parts = path.split("/")
        if len(parts) == 4:
            for name, f, full in _plugin_web():
                if name == parts[2] and f == parts[3]:
                    with open(full, "rb") as fh:
                        ext = os.path.splitext(f)[1]
                        return self.send(200, fh.read(), TYPES.get(ext) or mimetypes.guess_type(f)[0] or "application/octet-stream")
        return self.send(404, "yok", "text/plain")

    def static(self, name):
        # sadece web/ içindeki düz dosyalar (alt klasör ve '..' yok)
        if name == "index.html":
            return self.send(200, _index(), "text/html")
        if name not in os.listdir(WEB):
            return self.send(404, "yok", "text/plain")
        ext = os.path.splitext(name)[1]
        with open(os.path.join(WEB, name), "rb") as f:
            self.send(200, f.read(), TYPES.get(ext) or mimetypes.guess_type(name)[0] or "application/octet-stream")

    def do_GET(self):
        path = self.path.split("?")[0]
        if path == "/":
            return self.static("index.html")
        if path.startswith("/eklenti/"):
            return self.plugin_file(path)
        if path in registry.STREAMS:
            return self.sse(path)
        if path in registry.ROUTES:
            try:
                q = {k: v[0] for k, v in parse_qs(urlsplit(self.path).query).items()}
                r = registry.ROUTES[path](q)
            except Exception:
                traceback.print_exc()
                r = None
            if not r:
                return self.send(404, "yok", "text/plain")
            return self.send(200, r[1], r[0])
        if not path.startswith("/api/"):
            return self.static(path.lstrip("/"))
        if not self.authed():
            return self.json(401, {})
        if path == "/api/ui":
            q = parse_qs(urlsplit(self.path).query)
            tab = (q.get("tab") or [None])[0]
            light = (q.get("light") or ["0"])[0] == "1"
            t0 = time.time()
            data = registry.ui(tab, light)
            dt = time.time() - t0
            if dt > 1.5:
                log("yavaş /api/ui: %.1f sn (sekme %s)" % (dt, tab))
            data["poll"] = config.POLL_SECONDS
            data["version"] = VERSION
            return self.json(200, data)
        self.json(404, {})

    def do_POST(self):
        path = self.path.split("?")[0]
        if path in registry.POSTS:
            # bilgisayardaki programlar (örn. Minecraft modu) için: sadece yerel bağlantı
            if self.client_address[0] not in ("127.0.0.1", "::1"):
                return self.json(403, {})
            try:
                n = int(self.headers.get("Content-Length") or 0)
                body = json.loads(self.rfile.read(n) or b"{}")
                return self.json(200, registry.POSTS[path](body) or {"ok": True})
            except Exception as e:
                traceback.print_exc()
                return self.json(200, {"ok": False, "error": str(e)})
        if not self.authed():
            return self.json(401, {})
        if self.path != "/api/action":
            return self.json(404, {})
        try:
            n = int(self.headers.get("Content-Length") or 0)
            d = json.loads(self.rfile.read(n) or b"{}")
            result = registry.call(d.get("name"), d.get("params"))
            self.json(200, {"ok": True, "result": result})
        except Exception as e:
            traceback.print_exc()
            self.json(200, {"ok": False, "error": str(e)})


def local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except Exception:
        return "PC_IP"


class Server(ThreadingHTTPServer):
    # Windows'ta SO_REUSEADDR iki sürecin aynı portu almasına izin verir; kapatınca ikinci örnek
    # bağlanamaz ve sessizce çıkar (aynı anda iki kullanıcı oturumu açıksa ilk açılan kazanır).
    allow_reuse_address = os.name != "nt"
    daemon_threads = True

    def handle_error(self, request, client_address):
        import sys
        if isinstance(sys.exc_info()[1], (BrokenPipeError, ConnectionResetError, ConnectionAbortedError)):
            return
        super().handle_error(request, client_address)


HTTPD = None
RESTARTING = False   # core/reloader kapatırken soket hatası yazılmasın


def serve():
    global HTTPD
    # kendini yeniden başlatan kumandada eski süreç portu bırakana kadar biraz bekle
    tries = 40 if os.environ.get("PCK_RESTART") else 1
    for i in range(tries):
        try:
            HTTPD = httpd = Server(("0.0.0.0", config.PORT), Handler)
            break
        except OSError as e:
            if i + 1 == tries:
                print("Port %d kullanımda, kumanda zaten çalışıyor olabilir: %s" % (config.PORT, e))
                return
            time.sleep(0.25)
    print("Telefondan ac: http://%s:%d" % (local_ip(), config.PORT))
    try:
        httpd.serve_forever()
    except Exception:
        if not RESTARTING:
            raise
        while True:
            time.sleep(1)
