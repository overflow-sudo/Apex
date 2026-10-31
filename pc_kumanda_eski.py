"""
PC Kumanda - Windows bilgisayarını yerel ağdan yönet.
Gereksinim: Python 3 (ek paket yok) + aynı klasörde:
  MultiMonitorTool.exe  (nirsoft.net/utils/multi_monitor_tool.html)
  SoundVolumeView.exe   (nirsoft.net/utils/sound_volume_view.html)
Çalıştır:  python pc_kumanda.py   (sonra telefondan http://PC_IP:8765)
"""
import csv, ctypes, json, os, socket, subprocess, tempfile, threading, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# ---------------- AYARLAR ----------------
PORT = 8765
PIN = ""                  # boş değilse arayüz bu PIN'i ister (evde bile koymanı öneririm)
TV_MONITOR_KEYWORD = ""   # büyük ekranın adından bir parça, örn: "LG" veya "TV"
TV_AUDIO_KEYWORD = ""     # TV/monitör ses çıkışının adından bir parça, örn: "NVIDIA" veya "LG"
DESK_MONITOR_KEYWORD = "" # masaüstü monitörünün adından bir parça
DESK_AUDIO_KEYWORD = ""   # kulaklığın adından bir parça, örn: "Headphones"
AUTO_GAMEPAD = True       # gamepad tuşuna basınca otomatik TV moduna geç
# ------------------------------------------

BASE = os.path.dirname(os.path.abspath(__file__))
MMT = os.path.join(BASE, "MultiMonitorTool.exe")
SVV = os.path.join(BASE, "SoundVolumeView.exe")
LABELS = os.path.join(BASE, "monitor_adlari.json")
state = {"mode": "?", "lock": threading.Lock()}


def run(args):
    return subprocess.run(args, capture_output=True, creationflags=0x08000000)


def read_csv(tool, flag):
    fd, path = tempfile.mkstemp(suffix=".csv")
    os.close(fd)
    try:
        run([tool, flag, path])
        with open(path, encoding="utf-8-sig", errors="replace", newline="") as f:
            return list(csv.DictReader(f))
    finally:
        os.remove(path)


# ---------- Monitör ----------
def load_labels():
    try:
        with open(LABELS, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def get_monitors():
    labels = load_labels()
    out = []
    for r in read_csv(MMT, "/scomma"):
        if (r.get("Disconnected") or "").strip().lower() == "yes":
            continue
        name = r.get("Name", "")
        active = (r.get("Active") or "").strip().lower() == "yes"
        friendly = (r.get("Monitor Name") or "").strip()
        if friendly:
            labels[name] = friendly
        out.append({
            "name": name,
            "label": labels.get(name, name),
            "res": r.get("Resolution", ""),
            "active": active,
            "primary": (r.get("Primary") or "").strip().lower() == "yes",
        })
    try:
        with open(LABELS, "w", encoding="utf-8") as f:
            json.dump(labels, f, ensure_ascii=False)
    except Exception:
        pass
    return out


def only_monitor(name):
    mons = get_monitors()
    run([MMT, "/enable", name]); time.sleep(2)
    run([MMT, "/SetPrimary", name]); time.sleep(1)
    for m in mons:
        if m["name"] != name and m["active"]:
            run([MMT, "/disable", m["name"]])


def all_monitors():
    for m in get_monitors():
        if not m["active"]:
            run([MMT, "/enable", m["name"]])
            time.sleep(1)


# ---------- Ses ----------
def get_audio():
    out = []
    for r in read_csv(SVV, "/scomma"):
        if r.get("Type") != "Device" or r.get("Direction") != "Render":
            continue
        if r.get("Device State", "Active") != "Active":
            continue
        out.append({
            "id": r.get("Command-Line Friendly ID", ""),
            "name": "%s (%s)" % (r.get("Name", ""), r.get("Device Name", "")),
            "default": "Render" in (r.get("Default") or ""),
        })
    return out


def set_audio(dev_id):
    run([SVV, "/SetDefault", dev_id, "all"])


# ---------- Profiller ----------
def find(items, key, fields):
    key = key.lower()
    for it in items:
        if any(key in str(it[f]).lower() for f in fields):
            return it
    return None


def apply_profile(kind):
    with state["lock"]:
        mk, ak = (TV_MONITOR_KEYWORD, TV_AUDIO_KEYWORD) if kind == "tv" else (DESK_MONITOR_KEYWORD, DESK_AUDIO_KEYWORD)
        if mk:
            m = find(get_monitors(), mk, ["label", "name"])
            if m:
                only_monitor(m["name"])
        elif kind == "desk":
            all_monitors()
        if ak:
            a = find(get_audio(), ak, ["name"])
            if a:
                set_audio(a["id"])
        state["mode"] = kind


# ---------- Gamepad izleme (XInput) ----------
class XState(ctypes.Structure):
    _fields_ = [("packet", ctypes.c_uint32), ("buttons", ctypes.c_uint16),
                ("lt", ctypes.c_ubyte), ("rt", ctypes.c_ubyte),
                ("lx", ctypes.c_short), ("ly", ctypes.c_short),
                ("rx", ctypes.c_short), ("ry", ctypes.c_short)]


def gamepad_watcher():
    try:
        xin = ctypes.windll.xinput1_4
    except Exception:
        return
    while True:
        time.sleep(0.5)
        if state["mode"] == "tv" or not TV_MONITOR_KEYWORD:
            continue
        for i in range(4):
            s = XState()
            if xin.XInputGetState(i, ctypes.byref(s)) == 0 and s.buttons != 0:
                apply_profile("tv")
                break


# ---------- Web ----------
HTML = r"""<!doctype html><html lang="tr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>PC Kumanda</title>
<style>
:root{--bg:#14161a;--card:#1e2128;--tx:#e8eaed;--mut:#8b919c;--ac:#4f8cff;--ok:#34c37a}
@media(prefers-color-scheme:light){:root{--bg:#f3f4f6;--card:#fff;--tx:#1b1d21;--mut:#6b7280}}
*{box-sizing:border-box}body{margin:0;padding:16px;background:var(--bg);color:var(--tx);font-family:system-ui,sans-serif;max-width:560px;margin-inline:auto}
h1{font-size:20px}h2{font-size:13px;color:var(--mut);text-transform:uppercase;letter-spacing:.06em;margin:22px 0 8px}
.card{background:var(--card);border-radius:12px;padding:12px;margin-bottom:8px;display:flex;align-items:center;gap:10px;justify-content:space-between}
.card.on{outline:2px solid var(--ok)}.nm{flex:1;min-width:0;font-size:15px}.sub{color:var(--mut);font-size:12px}
button{background:var(--ac);color:#fff;border:0;border-radius:9px;padding:10px 14px;font-size:14px;cursor:pointer}
button.big{width:100%;padding:16px;font-size:16px;margin-bottom:8px}button.alt{background:#5b6270}
#msg{position:fixed;bottom:12px;left:50%;transform:translateX(-50%);background:#000c;color:#fff;padding:8px 14px;border-radius:20px;display:none}
</style></head><body>
<h1>PC Kumanda</h1>
<button class="big" onclick="act('/api/profile',{name:'tv'})">Oyun modu (TV + ses)</button>
<button class="big alt" onclick="act('/api/profile',{name:'desk'})">Masaüstü modu</button>
<h2>Monitör</h2><div id="mon"></div>
<button class="alt" onclick="act('/api/monitor',{mode:'all'})">Hepsini aç</button>
<h2>Ses çıkışı</h2><div id="aud"></div><div id="msg"></div>
<script>
let pin=localStorage.getItem('pin')||'';
function msg(t){const m=document.getElementById('msg');m.textContent=t;m.style.display='block';setTimeout(()=>m.style.display='none',2500)}
async function api(u,b){const r=await fetch(u,{method:b?'POST':'GET',headers:{'X-Pin':pin,'Content-Type':'application/json'},body:b?JSON.stringify(b):undefined});
 if(r.status==401){pin=prompt('PIN:')||'';localStorage.setItem('pin',pin);return api(u,b)}return r.json()}
async function act(u,b){msg('Uygulanıyor...');await api(u,b);msg('Tamam');load()}
function row(n,s,on,fn,btn){const d=document.createElement('div');d.className='card'+(on?' on':'');
 d.innerHTML='<div class="nm"></div>';d.firstChild.textContent=n;const sp=document.createElement('div');sp.className='sub';sp.textContent=s;d.firstChild.appendChild(sp);
 const b=document.createElement('button');b.textContent=btn;b.onclick=fn;d.appendChild(b);return d}
async function load(){const s=await api('/api/state');const m=document.getElementById('mon'),a=document.getElementById('aud');m.innerHTML='';a.innerHTML='';
 s.monitors.forEach(x=>m.appendChild(row(x.label,x.res+(x.primary?' - ana ekran':'')+(x.active?'':' - kapalı'),x.active,()=>act('/api/monitor',{mode:'only',name:x.name}),'Sadece bu')));
 s.audio.forEach(x=>a.appendChild(row(x.name,x.default?'Şu an aktif':'',x.default,()=>act('/api/audio',{id:x.id}),'Seç')))}
load();
</script></body></html>"""


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def send(self, code, body, ctype="application/json"):
        data = body if isinstance(body, bytes) else body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype + "; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def authed(self):
        return not PIN or self.headers.get("X-Pin") == PIN

    def do_GET(self):
        if self.path == "/":
            return self.send(200, HTML, "text/html")
        if not self.authed():
            return self.send(401, "{}")
        if self.path == "/api/state":
            return self.send(200, json.dumps({"monitors": get_monitors(), "audio": get_audio(), "mode": state["mode"]}))
        self.send(404, "{}")

    def do_POST(self):
        if not self.authed():
            return self.send(401, "{}")
        n = int(self.headers.get("Content-Length") or 0)
        d = json.loads(self.rfile.read(n) or b"{}")
        with_lock = state["lock"]
        if self.path == "/api/monitor":
            with with_lock:
                all_monitors() if d.get("mode") == "all" else only_monitor(d["name"])
        elif self.path == "/api/audio":
            with with_lock:
                set_audio(d["id"])
        elif self.path == "/api/profile":
            apply_profile(d["name"])
        else:
            return self.send(404, "{}")
        self.send(200, '{"ok":true}')


def local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except Exception:
        return "PC_IP"


if __name__ == "__main__":
    for t in (MMT, SVV):
        if not os.path.exists(t):
            print("EKSIK:", t)
    if AUTO_GAMEPAD:
        threading.Thread(target=gamepad_watcher, daemon=True).start()
    print("Telefondan ac: http://%s:%d" % (local_ip(), PORT))
    ThreadingHTTPServer(("0.0.0.0", PORT), H).serve_forever()
