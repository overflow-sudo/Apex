"""Logitech G HUB'ın yerel websocket API'si (ws://127.0.0.1:9010, alt protokol "json"). Belgelenmemiş;
LGSTrayBattery gibi araçlar da kullanıyor. Paket gerekmesin diye websocket istemcisi burada elle yazıldı.
Kullanılan yollar: /devices/list, /battery/<id>/state."""
import base64, json, os, socket, struct, time

HOST, PORT = "127.0.0.1", 9010


class Client(object):
    def __init__(self, timeout=3.0):
        self.s = socket.create_connection((HOST, PORT), timeout=timeout)
        key = base64.b64encode(os.urandom(16)).decode()
        self.s.sendall(("GET / HTTP/1.1\r\nHost: localhost:%d\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n"
                        "Sec-WebSocket-Key: %s\r\nSec-WebSocket-Version: 13\r\nSec-WebSocket-Protocol: json\r\n"
                        "Origin: file://\r\n\r\n" % (PORT, key)).encode())
        buf = b""
        while b"\r\n\r\n" not in buf:
            d = self.s.recv(4096)
            if not d:
                raise OSError("G HUB bağlantıyı kapattı")
            buf += d
        head, self.buf = buf.split(b"\r\n\r\n", 1)
        if b" 101 " not in head.split(b"\r\n")[0]:
            raise OSError("G HUB websocket reddedildi")

    def close(self):
        try:
            self.s.close()
        except OSError:
            pass

    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.close()

    def _send(self, obj):
        data = json.dumps(obj).encode()
        n, mask = len(data), os.urandom(4)
        if n < 126:
            hdr = struct.pack("BB", 0x81, 0x80 | n)
        elif n < 65536:
            hdr = struct.pack(">BBH", 0x81, 0xFE, n)
        else:
            hdr = struct.pack(">BBQ", 0x81, 0xFF, n)
        self.s.sendall(hdr + mask + bytes(b ^ mask[i % 4] for i, b in enumerate(data)))

    def _need(self, k):
        while len(self.buf) < k:
            d = self.s.recv(65536)
            if not d:
                raise OSError("G HUB bağlantıyı kapattı")
            self.buf += d

    def _frame(self):
        """Bir tam metin mesajı (parçalı çerçeveler birleştirilir)."""
        msg = b""
        while True:
            self._need(2)
            n, off = self.buf[1] & 0x7F, 2
            if n == 126:
                self._need(4)
                n, off = struct.unpack(">H", self.buf[2:4])[0], 4
            elif n == 127:
                self._need(10)
                n, off = struct.unpack(">Q", self.buf[2:10])[0], 10
            self._need(off + n)
            b = self.buf
            op, fin, payload = b[0] & 0x0F, b[0] & 0x80, b[off:off + n]
            self.buf = b[off + n:]
            if op in (0, 1):
                msg += payload
                if fin:
                    return msg.decode("utf-8", "replace")
            elif op == 8:
                raise OSError("G HUB bağlantıyı kapattı")
            # ping/pong ve ikili çerçeveler yok sayılır

    def get(self, path, timeout=3.0):
        """GET isteği; cevabın payload'ını döndürür, yol yoksa None."""
        self._send({"msgId": "", "verb": "GET", "path": path})
        end = time.time() + timeout
        while time.time() < end:
            d = json.loads(self._frame())
            if d.get("verb") == "GET" and d.get("path") == path:
                if (d.get("result") or {}).get("code") != "SUCCESS":
                    return None
                return d.get("payload")
        return None


def batteries():
    """[{type, name, state, pct, charging, hours}] — G HUB kapalıysa OSError."""
    out = []
    with Client() as c:
        devs = (c.get("/devices/list") or {}).get("deviceInfos") or []
        for d in devs:
            if d.get("isSubdevice") or not d.get("hasWirelessInterface"):
                continue
            item = {"type": d.get("deviceType", ""), "name": d.get("displayName", ""), "state": d.get("state", ""),
                    "pct": None, "charging": False, "hours": None}
            if d.get("state") == "ACTIVE":
                b = c.get("/battery/%s/state" % d.get("id")) or {}
                if b.get("percentage") is not None:
                    item["pct"] = int(b["percentage"])
                    item["charging"] = bool(b.get("charging"))
                    item["hours"] = b.get("mileage")
            out.append(item)
    return out
