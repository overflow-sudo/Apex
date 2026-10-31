/* Minecraft seed haritası — eklentiler/minecraft/eklenti.py'nin "mcmap" widget'ı.
   Çekirdekle sadece window.PCK üzerinden konuşur (eklentiler/EKLENTI_REHBERI.md). Eski Android Chrome: ?. ?? kullanma. */
(function () {
  "use strict";
  var P = window.PCK;
  if (!P) return;
  var el = P.el, icon = P.icon, api = P.api, toast = P.toast, store = P.store;

  // Bileşen bir kez oluşturulur ve her yenilemede aynı DOM yeniden eklenir: karolar, kaydırma ve
  // yakınlaştırma korunur. Karo = 256 px, ölçek (blok/piksel) 4 / 16 / 64 / 256. Görünüm "bpp" (blok/ekran pikseli).
  // Konum /mc/stream (Server-Sent Events) ile anlık gelir (mod saniyede 10 kez gönderir); sekme yenilemesi sadece
  // seed/dünya bilgisi için. Hedef: basılı tut / yapıya dokun / koordinat ara -> "Hedef yap" -> kuş uçuşu çizgi.
  var MC = null, mcES = null, mcRaf = 0;
  var BPP = [256, 128, 64, 32, 16, 8, 4, 2, 1, 0.5];
  var SVGNS = "http://www.w3.org/2000/svg";

  function mcCreate() {
    var m = { bpp: 4, cx: 0, cz: 0, follow: true, tiles: {}, marks: {}, cells: {}, showStructs: true, data: {}, pin: null,
      wpEls: {}, hide: {} };
    try { m.hide = JSON.parse(store.get("mcHide") || "{}") || {}; } catch (e) { m.hide = {}; }
    if (store.get("mcStructs") === "0") m.showStructs = false;
    var root = el("div", "mcmap");
    m.layer = el("div", "mclayer");
    m.mlayer = el("div", "mcmarks");
    m.svg = document.createElementNS(SVGNS, "svg");
    m.svg.setAttribute("class", "mcroute");
    m.line = document.createElementNS(SVGNS, "line");
    m.svg.appendChild(m.line);
    m.flag = el("div", "mcflag");
    m.flag.innerHTML = icon("flag");
    m.pinEl = el("div", "mcpin");
    m.player = el("div", "mcplayer");
    m.player.innerHTML = '<svg viewBox="0 0 24 24"><path d="M12 2 20 21 12 16.5 4 21z" fill="currentColor" stroke="#000" stroke-width="1.5" stroke-linejoin="round"/></svg>';
    m.hud = el("div", "mchud");
    m.info = el("div", "mcinfo");
    m.tip = el("div", "mctip");
    m.form = mcForm(m);
    m.layersP = el("div", "mcform mcpanel");
    m.wpP = el("div", "mcform mcpanel");
    m.wpLayer = el("div", "mcwps");
    var ctl = el("div", "mcctl");
    function btn(ic, fn, title) {
      var b = el("button", "mcb");
      b.innerHTML = icon(ic);
      b.title = title;
      b.onclick = function (e) { e.stopPropagation(); fn(); };
      ctl.appendChild(b);
      return b;
    }
    btn("plus", function () { mcZoom(1); }, "Yakınlaştır");
    btn("minus", function () { mcZoom(-1); }, "Uzaklaştır");
    m.followBtn = btn("target", function () { m.follow = true; mcDraw(); }, "Beni takip et");
    m.structBtn = btn("layers", function () { mcPanel(m.layersP, mcLayers); }, "Katmanlar");
    m.wpBtn = btn("star", function () { mcPanel(m.wpP, mcWpPanel); }, "Kayıtlı yerler");
    m.searchBtn = btn("search", function () { mcPanel(m.form); }, "Koordinat ara");
    [m.layer, m.mlayer, m.wpLayer, m.svg, m.pinEl, m.flag, m.player, m.hud, m.info, m.tip, m.form, m.layersP, m.wpP, ctl]
      .forEach(function (e) { root.appendChild(e); });
    m.root = root;
    mcGestures(m);
    return m;
  }

  // ---- koordinat arama formu ----
  // X/Z sayı alanı; ± düğmesi: eski telefon klavyelerinde eksi tuşu olmayabiliyor
  function mcNum(parent, label) {
    var w = el("div", "mcf");
    w.appendChild(el("span", "", label));
    var sg = el("button", "mcsign", "±");
    var inp = document.createElement("input");
    inp.type = "number";
    inp.setAttribute("inputmode", "numeric");
    inp.placeholder = "0";
    sg.onclick = function (e) {
      e.preventDefault();
      inp.value = inp.value.charAt(0) === "-" ? inp.value.slice(1) : "-" + (inp.value || "");
    };
    w.appendChild(sg);
    w.appendChild(inp);
    parent.appendChild(w);
    return inp;
  }

  // panellerden (arama, katmanlar, kayıtlı yerler) aynı anda sadece biri açık
  function mcPanel(p, fill) {
    var open = p.style.display === "block";
    [MC.form, MC.layersP, MC.wpP].forEach(function (x) { x.style.display = "none"; });
    MC.tip.style.display = "none";
    if (!open) {
      if (fill) fill(p);
      p.style.display = "block";
    }
  }

  function mcForm(m) {
    var f = el("div", "mcform");
    function field(label) { return mcNum(f, label); }
    var ix = field("X"), iz = field("Z");
    var row = el("div", "mcfrow");
    function act(label, fn, cls) {
      var b = el("button", "mcfb" + (cls ? " " + cls : ""), label);
      b.onclick = function (e) {
        e.preventDefault();
        var x = parseInt(ix.value, 10), z = parseInt(iz.value, 10);
        if (isNaN(x) || isNaN(z)) { toast("X VE Z GİR", 1500); return; }
        fn(x, z);
      };
      row.appendChild(b);
    }
    act("Git", function (x, z) {
      m.follow = false; m.cx = x; m.cz = z; m.pin = { x: x, z: z };
      if (m.bpp > 8) m.bpp = 8;
      f.style.display = "none";
      mcDraw();
    });
    act("Hedef yap", function (x, z) { f.style.display = "none"; mcSetTarget(x, z, ""); }, "pri");
    f.appendChild(row);
    return f;
  }

  function mcZoom(dir) {
    var i = BPP.indexOf(MC.bpp);
    i = Math.max(0, Math.min(BPP.length - 1, i + dir));
    MC.bpp = BPP[i];
    // art arda zum yaparken ara ölçeklerin karolarını isteme: durulunca yükle
    MC.zoomAt = Date.now();
    clearTimeout(MC.zoomT);
    MC.zoomT = setTimeout(mcDraw, 260);
    mcDraw();
  }

  function mcSize() { return { W: MC.root.clientWidth, H: MC.root.clientHeight }; }

  function mcToWorld(sx, sy) {
    var s = mcSize();
    return { x: Math.round(MC.cx + (sx - s.W / 2) * MC.bpp), z: Math.round(MC.cz + (sy - s.H / 2) * MC.bpp) };
  }

  function mcShowTip(text, x, z, name, wp) {
    var t = MC.tip, d = MC.data;
    [MC.form, MC.layersP, MC.wpP].forEach(function (p) { p.style.display = "none"; });
    t.innerHTML = "";
    var line = el("div", "mctl");
    line.appendChild(el("span", "", text));
    var bio = el("span", "mcbio");
    line.appendChild(bio);
    t.appendChild(line);
    if (x != null) {
      if (d.seed) {                                           // bu noktanın biyomu
        fetch("/mc/biome?s=" + d.seed + "&d=" + (d.dim || 0) + "&x=" + x + "&z=" + z)
          .then(function (r) { return r.json(); })
          .then(function (j) { if (j.name) bio.textContent = " · " + j.name; }).catch(function () {});
      }
      var row = el("div", "mctrow");
      function tb(label, fn) {
        var b = el("button", "mctb", label);
        b.onclick = function (e) { e.stopPropagation(); t.style.display = "none"; fn(); };
        row.appendChild(b);
      }
      tb("Hedef yap", function () { mcSetTarget(x, z, name || ""); });
      if (wp) tb("Sil", function () { mcWpDel(wp.id); });
      else tb("Kaydet", function () { mcPanel(MC.wpP, function (p) { mcWpPanel(p, { x: x, z: z, name: name || "" }); }); });
      t.appendChild(row);
    }
    t.style.display = "block";
  }

  // ---- katmanlar: yapı türlerini tek tek aç/kapat (telefonda hatırlanır) ----
  function mcLayers(p) {
    var m = MC, d = m.data;
    p.innerHTML = "";
    p.appendChild(el("div", "mcph", "Katmanlar"));
    function row(label, on, fn, badge) {
      var r = el("button", "mclr" + (on ? " on" : ""));
      if (badge) {
        var bd = el("span", "mcbadge", badge[0]);
        bd.style.background = badge[1];
        r.appendChild(bd);
      }
      r.appendChild(el("span", "mcln", label));
      r.appendChild(el("span", "mcck", on ? "✓" : ""));
      r.onclick = function (e) { e.stopPropagation(); fn(); mcLayers(p); mcDraw(); };
      p.appendChild(r);
    }
    row("Tüm yapılar", m.showStructs, function () {
      m.showStructs = !m.showStructs;
      store.set("mcStructs", m.showStructs ? "1" : "0");
    });
    var list = el("div", "mclist");
    p.appendChild(list);
    var keep = p;
    p = list;
    (d.types || []).forEach(function (t) {     // [anahtar, kısa, ad, renk]
      row(t[2], !m.hide[t[0]], function () {
        if (m.hide[t[0]]) delete m.hide[t[0]]; else m.hide[t[0]] = 1;
        store.set("mcHide", JSON.stringify(m.hide));
      }, [t[1], t[3]]);
    });
    p = keep;
    p.appendChild(el("div", "mcnote", "Küçük yapılar (portal, gemi, hazine…) yakınlaşınca görünür."));
  }

  // ---- kayıtlı yerler ----
  function mcWpPanel(p, pre) {
    var m = MC, d = m.data;
    p.innerHTML = "";
    p.appendChild(el("div", "mcph", "Kayıtlı yerler"));
    var nm = document.createElement("input");
    nm.className = "mcname";
    nm.placeholder = "Ad (ör. Ev, Maden)";
    nm.maxLength = 30;
    p.appendChild(nm);
    var ix = mcNum(p, "X"), iz = mcNum(p, "Z");
    if (pre) { ix.value = pre.x; iz.value = pre.z; nm.value = pre.name || ""; }
    else if (d.x != null) { ix.value = Math.floor(d.x); iz.value = Math.floor(d.z); }
    var row = el("div", "mcfrow");
    var me = el("button", "mcfb", "Konumum");
    me.onclick = function (e) {
      e.preventDefault();
      if (d.x != null) { ix.value = Math.floor(d.x); iz.value = Math.floor(d.z); }
    };
    var sv = el("button", "mcfb pri", "Kaydet");
    sv.onclick = function (e) {
      e.preventDefault();
      var x = parseInt(ix.value, 10), z = parseInt(iz.value, 10);
      if (isNaN(x) || isNaN(z)) { toast("X VE Z GİR", 1500); return; }
      api("/api/action", { name: "mc.wp.add", params: { x: x, z: z, dim: d.dim || 0, name: nm.value } }).then(function (r) {
        if (r && r.ok && r.result) { d.waypoints = r.result; mcWpPanel(p); mcDraw(); toast("KAYDEDİLDİ", 1200); }
        else toast("KAYDEDİLEMEDİ", 1500);
      }).catch(function () { toast("KAYDEDİLEMEDİ", 1500); });
    };
    row.appendChild(me);
    row.appendChild(sv);
    p.appendChild(row);
    var list = el("div", "mclist");
    var wps = d.waypoints || [];
    if (!wps.length) list.appendChild(el("div", "mcnote", "Henüz kayıtlı yer yok. Haritada basılı tut → Kaydet."));
    wps.forEach(function (w) {
      var r = el("div", "mcwr");
      var info = el("div", "mcwi");
      info.appendChild(el("b", "", w.name));
      var here = mcTargetHere(w, d.dim || 0), dist = "";
      if (here && d.x != null) dist = " · " + Math.round(Math.sqrt(Math.pow(here.x - d.x, 2) + Math.pow(here.z - d.z, 2))).toLocaleString("tr-TR") + " blok";
      info.appendChild(el("span", "", w.x + ", " + w.z + (w.dim !== (d.dim || 0) ? (w.dim === -1 ? " (Nether)" : w.dim === 1 ? " (End)" : " (Overworld)") : "") + dist));
      info.onclick = function (e) {                              // haritada göster
        e.stopPropagation();
        if (!here) { toast("BAŞKA BOYUTTA", 1400); return; }
        m.follow = false; m.cx = here.x; m.cz = here.z;
        if (m.bpp > 8) m.bpp = 8;
        p.style.display = "none";
        mcDraw();
      };
      r.appendChild(info);
      var fb = el("button", "mcwb");
      fb.innerHTML = icon("flag");
      fb.onclick = function (e) { e.stopPropagation(); p.style.display = "none"; mcSetTarget(w.x, w.z, w.name, w.dim); };
      var db = el("button", "mcwb", "×");
      db.onclick = function (e) { e.stopPropagation(); mcWpDel(w.id); };
      r.appendChild(fb);
      r.appendChild(db);
      list.appendChild(r);
    });
    p.appendChild(list);
  }

  function mcWpDel(id) {
    var d = MC.data;
    d.waypoints = (d.waypoints || []).filter(function (w) { return w.id !== id; });
    if (MC.wpP.style.display === "block") mcWpPanel(MC.wpP);
    mcDraw();
    api("/api/action", { name: "mc.wp.del", params: { id: id } }).then(function (r) {
      if (r && r.ok && r.result) { d.waypoints = r.result; mcDraw(); }
    }).catch(function () {});
    toast("SİLİNDİ", 1200);
  }

  function mcSetTarget(x, z, name, dim) {
    var tg = x == null ? null : { x: x, z: z, dim: dim != null ? dim : (MC.data.dim || 0), name: name };
    MC.data.target = tg;
    MC.pin = null;
    mcDraw();
    api("/api/action", { name: "mc.target", params: tg ? tg : { x: null } });
    toast(tg ? "HEDEF AYARLANDI" : "HEDEF KALDIRILDI", 1400);
  }

  function mcGestures(m) {
    var drag = null, lastTap = 0, hold = null;
    function rel(cx, cy) { var r = m.root.getBoundingClientRect(); return { x: (cx - r.left) / P.zoom(), y: (cy - r.top) / P.zoom() }; }
    function start(cx, cy) {
      drag = { x: cx, y: cy, moved: false };
      clearTimeout(hold);
      hold = setTimeout(function () {                    // basılı tut: bu noktayı hedef yapmayı öner
        if (!drag || drag.moved) return;
        var p = rel(drag.x, drag.y), w = mcToWorld(p.x, p.y);
        drag.held = true;
        m.pin = { x: w.x, z: w.z };
        mcDraw();
        mcShowTip(w.x + ", " + w.z, w.x, w.z, "");
      }, 550);
    }
    function move(cx, cy) {
      if (!drag) return;
      var dx = cx - drag.x, dy = cy - drag.y;
      if (Math.abs(dx) + Math.abs(dy) > 6) { drag.moved = true; clearTimeout(hold); }
      if (!drag.moved) return;
      m.follow = false;
      m.cx -= dx / P.zoom() * m.bpp;
      m.cz -= dy / P.zoom() * m.bpp;
      drag.x = cx;
      drag.y = cy;
      mcDraw();
    }
    function end() {
      clearTimeout(hold);
      if (drag && !drag.moved && !drag.held) {
        var now = Date.now();
        if (now - lastTap < 320) mcZoom(1);              // çift dokunuş: yakınlaştır
        lastTap = now;
        m.tip.style.display = "none";
        [m.form, m.layersP, m.wpP].forEach(function (p) { p.style.display = "none"; });
      }
      drag = null;
    }
    m.root.addEventListener("touchstart", function (e) { if (e.touches.length === 1 && !mcInUi(e.target)) start(e.touches[0].clientX, e.touches[0].clientY); }, { passive: true });
    m.root.addEventListener("touchmove", function (e) { if (drag && e.touches.length === 1) { move(e.touches[0].clientX, e.touches[0].clientY); e.preventDefault(); } }, { passive: false });
    m.root.addEventListener("touchend", end);
    m.root.addEventListener("mousedown", function (e) { if (!mcInUi(e.target)) start(e.clientX, e.clientY); });
    window.addEventListener("mousemove", function (e) { if (drag) move(e.clientX, e.clientY); });
    window.addEventListener("mouseup", end);
    m.root.addEventListener("contextmenu", function (e) {
      e.preventDefault();
      if (mcInUi(e.target) || e.button !== 2) return;          // masaüstü: sağ tık = basılı tutma
      clearTimeout(hold);
      drag = null;
      var p = rel(e.clientX, e.clientY), w = mcToWorld(p.x, p.y);
      m.pin = { x: w.x, z: w.z };
      mcDraw();
      mcShowTip(w.x + ", " + w.z, w.x, w.z, "");
    });
    // masaüstü: fare tekerleği imlecin altındaki noktaya doğru yakınlaştırır
    var wheelAt = 0;
    m.root.addEventListener("wheel", function (e) {
      if (mcInUi(e.target)) return;
      e.preventDefault();
      var now = Date.now();
      if (now - wheelAt < 120) return;                         // dokunmatik yüzeyde çok hızlı zum olmasın
      wheelAt = now;
      var p = rel(e.clientX, e.clientY), before = mcToWorld(p.x, p.y);
      mcZoom(e.deltaY < 0 ? 1 : -1);
      var after = mcToWorld(p.x, p.y);
      m.follow = false;
      m.cx += before.x - after.x;
      m.cz += before.z - after.z;
      mcDraw();
    }, { passive: false });
  }

  function mcInUi(t) {
    while (t && t !== MC.root) {
      if (/\b(mcctl|mcform|mctip|mcmk|mchud|mcwp)\b/.test(t.className || "")) return true;
      t = t.parentNode;
    }
    return false;
  }

  function mcWidget(d) {
    if (!MC) MC = mcCreate();
    var prev = MC.data;
    // anlık akıştan gelen konum daha yeniyse yerinde bırak
    if (MC.liveAt && Date.now() - MC.liveAt < 3000) {
      d.x = prev.x; d.y = prev.y; d.z = prev.z; d.yaw = prev.yaw; d.active = prev.active; d.biome = prev.biome;
    }
    MC.data = d;
    if (prev.seed !== d.seed || prev.dim !== d.dim) mcReset();
    mcStreamOpen();
    setTimeout(mcDraw, 0);                                    // DOM'a eklendikten sonra ölç
    return MC.root;
  }

  function mcReset() {
    MC.layer.innerHTML = "";
    MC.mlayer.innerHTML = "";
    MC.tiles = {};
    MC.marks = {};
    MC.cells = {};
  }

  // ---- anlık konum (SSE) ----
  function mcStreamOpen() {
    if (mcES || !window.EventSource) return;
    mcES = new EventSource("/mc/stream");
    mcES.onmessage = function (ev) {
      if (!MC) return;
      var p;
      try { p = JSON.parse(ev.data); } catch (e) { return; }
      var d = MC.data;
      if (p.dim !== d.dim && p.x != null) { d.dim = p.dim; mcReset(); }
      d.x = p.x; d.y = p.y; d.z = p.z; d.yaw = p.yaw; d.active = p.active;
      if ("target" in p) d.target = p.target;
      if ("biome" in p) d.biome = p.biome;
      MC.liveAt = Date.now();
      if (!mcRaf) {
        mcRaf = (window.requestAnimationFrame || function (f) { return setTimeout(f, 16); })(function () { mcRaf = 0; mcDraw(); });
      }
    };
  }

  function mcStreamClose() {
    if (mcES) { mcES.close(); mcES = null; }
  }

  function mcScale(bpp) { return bpp >= 192 ? 256 : bpp >= 48 ? 64 : bpp >= 12 ? 16 : 4; }

  // hedefi oyuncunun bulunduğu boyuta çevir (Nether = Overworld / 8)
  function mcTargetHere(t, dim) {
    if (!t) return null;
    if (t.dim === dim) return { x: t.x, z: t.z };
    if (t.dim === 0 && dim === -1) return { x: t.x / 8, z: t.z / 8 };
    if (t.dim === -1 && dim === 0) return { x: t.x * 8, z: t.z * 8 };
    return null;
  }

  function mcPlace(e, wx, wz, W, H) {
    e.style.left = Math.round((wx - MC.cx) / MC.bpp + W / 2) + "px";
    e.style.top = Math.round((wz - MC.cz) / MC.bpp + H / 2) + "px";
  }

  function mcDraw() {
    var m = MC, d = m && m.data;
    if (!m || !m.root.parentNode) return;
    var W = m.root.clientWidth, H = m.root.clientHeight;
    if (!W || !H) return;
    m.root.scrollTop = m.root.scrollLeft = 0;   // tarayıcı odak/dokunuşla kutuyu kaydırmasın
    if (m.follow && d.x != null) { m.cx = d.x; m.cz = d.z; }
    m.followBtn.className = "mcb" + (m.follow ? " on" : "");
    m.structBtn.className = "mcb" + (m.showStructs ? " on" : "");
    m.wpBtn.className = "mcb" + ((d.waypoints || []).length ? " on" : "");
    var bpp = m.bpp;
    m.layer.className = "mclayer" + (bpp >= 128 ? " far" : "");
    var x0 = m.cx - W / 2 * bpp, z0 = m.cz - H / 2 * bpp;
    // ---- karolar ----
    if (d.seed && d.ok) {
      var sc = mcScale(bpp), T = 256 * sc, size = T / bpp;
      var tx0 = Math.floor(x0 / T), tx1 = Math.floor((x0 + W * bpp) / T);
      var tz0 = Math.floor(z0 / T), tz1 = Math.floor((z0 + H * bpp) / T);
      var want = {};
      for (var tz = tz0; tz <= tz1; tz++) {
        for (var tx = tx0; tx <= tx1; tx++) {
          var key = sc + ":" + tx + ":" + tz;
          want[key] = 1;
          var im = m.tiles[key];
          if (!im && Date.now() - (m.zoomAt || 0) < 250) continue;
          if (!im) {
            im = document.createElement("img");
            im.className = "mctile";
            im.alt = "";
            im.src = "/mc/tile?s=" + d.seed + "&d=" + d.dim + "&sc=" + sc + "&x=" + tx + "&y=" + tz;
            m.tiles[key] = im;
          }
          mcPlace(im, tx * T, tz * T, W, H);
          im.style.width = im.style.height = Math.ceil(size) + "px";
          if (im.parentNode !== m.layer) m.layer.appendChild(im);
        }
      }
      for (var k in m.tiles) {
        if (want[k]) continue;
        var old = m.tiles[k];
        if (old.parentNode) m.layer.removeChild(old);
        // henüz yüklenmemiş eski karoyu iptal et: bağlantıyı yeni karolara bırakır
        if (!old.complete) { old.src = ""; delete m.tiles[k]; }
      }
      // ---- yapılar (2048 bloklık hücreler; çok uzaktayken yüklenmez) ----
      for (var mk in m.marks) m.marks[mk].style.display = "none";
      if (m.showStructs && d.structures && bpp <= 16) {
        var c0x = Math.floor(x0 / 2048), c1x = Math.floor((x0 + W * bpp) / 2048);
        var c0z = Math.floor(z0 / 2048), c1z = Math.floor((z0 + H * bpp) / 2048);
        for (var cz = c0z; cz <= c1z; cz++) {
          for (var cx = c0x; cx <= c1x; cx++) {
            var ck = cx + ":" + cz;
            if (!m.cells[ck]) {
              m.cells[ck] = "yükleniyor";
              mcLoadCell(d.seed, d.dim, cx, cz);
            } else if (m.cells[ck] !== "yükleniyor") {
              m.cells[ck].forEach(function (s) {
                // s: [kısa, x, z, ad, renk, en uzak zum, anahtar] — küçük yapılar sadece yakın görünümde
                if (bpp > s[5] || m.hide[s[6]]) return;
                mcMark(s, W, H);
              });
            }
          }
        }
      }
    }
    // ---- kayıtlı yerler ----
    for (var wk in m.wpEls) m.wpEls[wk].style.display = "none";
    (d.waypoints || []).forEach(function (w) {
      var here = mcTargetHere(w, d.dim || 0);
      if (!here) return;
      var e = m.wpEls[w.id];
      if (!e || e.wpName !== w.name) {
        if (e && e.parentNode) e.parentNode.removeChild(e);
        e = el("div", "mcwp");
        e.innerHTML = icon("star");
        e.appendChild(el("span", "", w.name));
        e.wpName = w.name;
        m.wpEls[w.id] = e;
        m.wpLayer.appendChild(e);
      }
      e.onclick = function (ev) {
        ev.stopPropagation();
        var dist = d.x != null ? " · " + Math.round(Math.sqrt(Math.pow(here.x - d.x, 2) + Math.pow(here.z - d.z, 2))).toLocaleString("tr-TR") + " blok" : "";
        mcShowTip(w.name + " · " + w.x + ", " + w.z + dist, w.x, w.z, w.name, w);
      };
      e.style.display = "";
      mcPlace(e, here.x, here.z, W, H);
    });
    // ---- arama iğnesi ----
    if (m.pin) { m.pinEl.style.display = ""; mcPlace(m.pinEl, m.pin.x, m.pin.z, W, H); }
    else m.pinEl.style.display = "none";
    // ---- oyuncu ----
    var px = null, pz = null;
    if (d.x != null) {
      px = (d.x - m.cx) / bpp + W / 2;
      pz = (d.z - m.cz) / bpp + H / 2;
      m.player.style.display = "";
      m.player.style.left = Math.round(px) + "px";
      m.player.style.top = Math.round(pz) + "px";
      // Minecraft yaw: 0 = güney (+Z), 90 = batı. Ok varsayılan olarak kuzeyi (yukarı) gösteriyor.
      var rot = "rotate(" + (((d.yaw || 0) + 180) % 360) + "deg)";
      m.player.style.transform = m.player.style.webkitTransform = "translate(-50%,-50%) " + rot;
      m.player.className = "mcplayer" + (d.active ? "" : " stale");
    } else {
      m.player.style.display = "none";
    }
    // ---- hedef + kuş uçuşu rota ----
    var tg = mcTargetHere(d.target, d.dim || 0), route = null;
    if (tg) {
      var tx = (tg.x - m.cx) / bpp + W / 2, tzs = (tg.z - m.cz) / bpp + H / 2;
      m.flag.style.display = "";
      m.flag.style.left = Math.round(tx) + "px";
      m.flag.style.top = Math.round(tzs) + "px";
      if (px != null) {
        m.svg.style.display = "";
        m.svg.setAttribute("width", W);
        m.svg.setAttribute("height", H);
        m.line.setAttribute("x1", px); m.line.setAttribute("y1", pz);
        m.line.setAttribute("x2", tx); m.line.setAttribute("y2", tzs);
        var dx = tg.x - d.x, dz = tg.z - d.z;
        var dist = Math.sqrt(dx * dx + dz * dz);
        // hedefin yaw cinsinden yönü; pozitif fark = sağa dön (yaw saat yönünde artar)
        var want = Math.atan2(-dx, dz) * 180 / Math.PI;
        var rel = ((want - (d.yaw || 0)) % 360 + 540) % 360 - 180;
        route = { dist: dist, rel: rel };
      } else m.svg.style.display = "none";
    } else {
      m.flag.style.display = "none";
      m.svg.style.display = "none";
    }
    // ---- bilgi ----
    m.hud.innerHTML = "";
    if (d.x != null) {
      [["X", Math.floor(d.x)], ["Y", Math.floor(d.y)], ["Z", Math.floor(d.z)]].forEach(function (a) {
        var c = el("span", "mcc");
        c.appendChild(el("b", "", a[0]));
        c.appendChild(document.createTextNode(" " + a[1]));
        m.hud.appendChild(c);
      });
      var dm = el("span", "mcdim", (d.dim === -1 ? "Nether" : d.dim === 1 ? "End" : "Overworld") + (d.active ? "" : " · son konum"));
      dm.lang = "en";
      m.hud.appendChild(dm);
      if (d.biome) m.hud.appendChild(el("span", "mcbiome", d.biome));
      if (d.dim === -1) m.hud.appendChild(el("span", "mcdim", "Overworld ≈ " + Math.floor(d.x * 8) + ", " + Math.floor(d.z * 8)));
      if (route) {
        var r = el("span", "mcroutei");
        var dir = Math.abs(route.rel) < 8 ? "tam önünde" : Math.abs(route.rel) > 172 ? "tam arkanda"
          : (route.rel > 0 ? "sağa " : "sola ") + Math.round(Math.abs(route.rel)) + "°";
        r.appendChild(el("b", "", "HEDEF"));
        r.appendChild(document.createTextNode(" " + Math.round(route.dist).toLocaleString("tr-TR") + " blok · " + dir));
        var xb = el("button", "mcx", "×");
        xb.onclick = function (e) { e.stopPropagation(); mcSetTarget(null); };
        r.appendChild(xb);
        m.hud.appendChild(r);
      }
    } else {
      m.hud.appendChild(el("span", "mcdim", "Konum bekleniyor · PC Kumanda Bridge modu yüklü mü?"));
    }
    var w = d.world ? (d.kind === "realm" ? "Realm · " : d.kind === "single" ? "Dünya · " : "Sunucu · ") + d.world + " · " : "";
    m.info.textContent = !d.ok ? "Harita kütüphanesi yüklenemedi: " + (d.err || "?")
      : d.seed ? w + "seed " + d.seed + (d.seedSrc === "varsayılan" ? " (varsayılan)" : "") + " · 1 px = " + bpp + " blok"
      : "Seed bilinmiyor";
  }

  function mcLoadCell(seed, dim, cx, cz) {
    fetch("/mc/structs?s=" + seed + "&d=" + dim + "&cx=" + cx + "&cz=" + cz).then(function (r) { return r.json(); })
      .then(function (list) {
        if (!MC || MC.data.seed !== seed || MC.data.dim !== dim) return;
        MC.cells[cx + ":" + cz] = list;
        mcDraw();
      }).catch(function () { if (MC) delete MC.cells[cx + ":" + cz]; });
  }

  function mcMark(s, W, H) {
    var m = MC, key = s[0] + ":" + s[1] + ":" + s[2];
    var e = m.marks[key];
    if (!e) {
      e = el("div", "mcmk", s[0]);
      e.style.background = s[4];
      e.onclick = function (ev) {
        ev.stopPropagation();
        var dist = m.data.x != null ? " · " + Math.round(Math.sqrt(Math.pow(s[1] - m.data.x, 2) + Math.pow(s[2] - m.data.z, 2))).toLocaleString("tr-TR") + " blok" : "";
        mcShowTip(s[3] + " · " + s[1] + ", " + s[2] + dist, s[1], s[2], s[3]);
      };
      m.marks[key] = e;
      m.mlayer.appendChild(e);
    }
    e.style.display = "";
    mcPlace(e, s[1], s[2], W, H);
  }

  // ---------- çekirdeğe bağlantı ----------
  P.widget("mcmap", function (s) { return mcWidget(s.data || {}); });
  P.on("render", function (tab) { if (tab !== "mcmap") mcStreamClose(); });   // harita kapalıyken anlık akışı kapat
  P.on("resize", function () { if (MC) mcDraw(); });
  P.on("close", function () {                                                 // Esc / sekme kısayolu: panelleri kapat
    if (MC) { [MC.form, MC.layersP, MC.wpP, MC.tip].forEach(function (p) { p.style.display = "none"; }); }
  });
  P.on("key", function (k, tab) {                                             // masaüstü: +/- haritada zum
    if ((k === "+" || k === "=" || k === "-") && MC && tab === "mcmap") { mcZoom(k === "-" ? -1 : 1); return true; }
  });
})();
