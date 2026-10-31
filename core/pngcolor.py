"""
Ek paket olmadan PNG'den baskın renk (sadece zlib). Oyun logosundan otomatik tema rengi çıkarmak için.
8 bit RGB / RGBA / palet / gri destekler (Steam logo.png dosyaları 8 bit RGBA).
"""
import colorsys, struct, zlib


def _decode(data):
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("PNG değil")
    pos, idat, plte, trns = 8, [], None, None
    w = h = depth = ctype = interlace = None
    while pos < len(data):
        n, typ = struct.unpack(">I4s", data[pos:pos + 8])
        body = data[pos + 8:pos + 8 + n]
        pos += 12 + n
        if typ == b"IHDR":
            w, h, depth, ctype, _, _, interlace = struct.unpack(">IIBBBBB", body)
        elif typ == b"PLTE":
            plte = [tuple(body[i:i + 3]) for i in range(0, len(body), 3)]
        elif typ == b"tRNS":
            trns = body
        elif typ == b"IDAT":
            idat.append(body)
        elif typ == b"IEND":
            break
    if depth != 8 or interlace:
        raise ValueError("desteklenmeyen PNG (bit derinliği %s, interlace %s)" % (depth, interlace))
    bpp = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[ctype]
    raw = zlib.decompress(b"".join(idat))
    stride = w * bpp
    rows, prev, i = [], bytearray(stride), 0
    for _ in range(h):
        f = raw[i]
        line = bytearray(raw[i + 1:i + 1 + stride])
        i += 1 + stride
        if f == 1:
            for x in range(bpp, stride):
                line[x] = (line[x] + line[x - bpp]) & 255
        elif f == 2:
            for x in range(stride):
                line[x] = (line[x] + prev[x]) & 255
        elif f == 3:
            for x in range(stride):
                left = line[x - bpp] if x >= bpp else 0
                line[x] = (line[x] + ((left + prev[x]) >> 1)) & 255
        elif f == 4:
            for x in range(stride):
                a = line[x - bpp] if x >= bpp else 0
                b = prev[x]
                c = prev[x - bpp] if x >= bpp else 0
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                line[x] = (line[x] + (a if pa <= pb and pa <= pc else b if pb <= pc else c)) & 255
        rows.append(line)
        prev = line
    return w, h, ctype, bpp, rows, plte, trns


def _pixel(ctype, line, x, bpp, plte, trns):
    o = x * bpp
    if ctype == 6:
        return line[o], line[o + 1], line[o + 2], line[o + 3]
    if ctype == 2:
        return line[o], line[o + 1], line[o + 2], 255
    if ctype == 3:
        k = line[o]
        r, g, b = plte[k] if plte and k < len(plte) else (0, 0, 0)
        a = trns[k] if trns and k < len(trns) else 255
        return r, g, b, a
    if ctype == 4:
        return line[o], line[o], line[o], line[o + 1]
    return line[o], line[o], line[o], 255


def dominant(data, step=3):
    """'#rrggbb' — en çok görülen doygun renk (şeffaf, gri, çok koyu pikseller sayılmaz). Bulamazsa None."""
    w, h, ctype, bpp, rows, plte, trns = _decode(data)
    bins = {}
    for y in range(0, h, step):
        line = rows[y]
        for x in range(0, w, step):
            r, g, b, a = _pixel(ctype, line, x, bpp, plte, trns)
            if a < 140:
                continue
            hh, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
            if s < 0.35 or v < 0.3:
                continue
            k = int(hh * 24) % 24
            wgt = s * v
            acc = bins.setdefault(k, [0.0, 0.0, 0.0, 0.0])
            acc[0] += r * wgt
            acc[1] += g * wgt
            acc[2] += b * wgt
            acc[3] += wgt
    if not bins:
        return None
    r, g, b, wsum = max(bins.values(), key=lambda a: a[3])
    return "#%02x%02x%02x" % (int(r / wsum), int(g / wsum), int(b / wsum))


def vivid(hex_color, min_v=0.78, min_s=0.55):
    """Tema vurgusu olarak okunur hale getir: yeterince parlak ve doygun."""
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    hh, s, v = colorsys.rgb_to_hsv(r, g, b)
    r, g, b = colorsys.hsv_to_rgb(hh, max(s, min_s), max(v, min_v))
    return "#%02x%02x%02x" % (int(r * 255), int(g * 255), int(b * 255))


def dark_bg(hex_color, mix=0.07):
    """Vurgu renginden çok koyu, hafif renkli zemin."""
    h = hex_color.lstrip("#")
    base = (7, 8, 10)
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return "#%02x%02x%02x" % tuple(int(c0 + (c - c0) * mix) for c0, c in zip(base, (r, g, b)))
