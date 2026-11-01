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

  // ---- yapı ve rota ikonları: 24x24 dolu siluetler (fill-rule evenodd: iç boşluklar delik olur) ----
  var MCI = {
    village: "M5 2h14v14h-4.5v6h-5v-6H5zM7.5 7h3v2.5h-3zm6 0h3v2.5h-3z",                       // köylü başı + burun
    outpost: "M7 22V9H5V3h3v2h2V3h4v2h2V3h3v6h-2v13zM10.5 12h3v4h-3z",                          // gözetleme kulesi
    mansion: "M1 11L12 2l11 9h-3v11h-6v-6h-4v6H4V11z",                                          // konak
    monument: "M12 5a7 7 0 1 0 0 14a7 7 0 1 0 0-14zM12 9a3 3 0 1 0 0 6a3 3 0 1 0 0-6zM11 0h2v4h-2zM11 20h2v4h-2zM0 11h4v2H0zM20 11h4v2h-4z", // muhafız gözü
    ancient: "M4 11a8 8 0 0 1 16 0v5l-2 2v4H6v-4l-2-2zM7 10h4v4H7zm6 0h4v4h-4zM10 18h1.5v3H10zm2.5 0H14v3h-1.5z", // kafatası
    stronghold: "M1 12C5 4.5 19 4.5 23 12C19 19.5 5 19.5 1 12zM12 7.5a4.5 4.5 0 1 0 0 9a4.5 4.5 0 1 0 0-9zM11 8.5h2v7h-2z", // ender gözü
    spawn: "M2 19V7h2.5v6H11V9h8.5a2.5 2.5 0 0 1 2.5 2.5V19h-2.5v-2.5h-15V19zM5 9.5h4.5V12H5z",    // yatak
    desert: "M12 2L1 22h22zM10.5 16h3v6h-3z",                                                   // piramit
    jungle: "M7 3h10v4h2v4h2v4h2v7H1v-7h2v-4h2V7h2zM10.5 16h3v6h-3z",                           // basamaklı tapınak
    hut: "M1 18h22v3H1zM6.5 18L10 6.5 18 3l-3.5 4.5L17.5 18z",                                   // cadı şapkası
    igloo: "M1 20a11 11 0 0 1 22 0zM9 20a3 3 0 0 1 6 0z",                                       // iglo
    portal: "M4 2h16v20H4zM7.5 5.5h9v13h-9z",                                                   // portal çerçevesi
    shipwreck: "M1 14h22l-3.5 7h-15zM11 2h2v11h-2zM13 3.5l6.5 8H13z",                           // gemi
    oceanruin: "M3 21V9h3.5v12zM10.25 21V4h3.5v17zM17.5 21v-7.5H21V21zM1 21h22v2.5H1z",         // yıkık sütunlar
    trial: "M2 2h20v20H2zM5 5h5.5v5.5H5zm8.5 0H19v5.5h-5.5zM5 13.5h5.5V19H5zm8.5 0H19V19h-5.5z", // canavar kafesi
    trail: "M8 2h8v3l-1.5 1.5L19 11v7l-3.5 4.5h-7L5 18v-7l4.5-4.5L8 5zM9 13h6v3H9z",             // süslü çömlek
    well: "M3 11h18v11H3zM6 14h12v5H6zM4 3h16v3H4zM5.5 6H8v5H5.5zm10.5 0h2.5v5H16z",            // kuyu
    treasure: "M2 9.5A5.5 5.5 0 0 1 7.5 4h9A5.5 5.5 0 0 1 22 9.5V11H2zM2 12h20v9H2zM10.5 12h3v4.5h-3z", // sandık
    fortress: "M2 22V7h3.5v3H8V7h3.5v3H14V7h3.5v3H20V7h2v15zM9.5 22v-5a2.5 2.5 0 0 1 5 0v5z",    // nether kalesi
    bastion: "M2 5h20v14H2zM6.5 9.5h4v5h-4zm7 0h4v5h-4z",                                       // piglin burnu
    endcity: "M8 22V10H4.5V6H8V2h8v4h3.5v4H16v12zM10.5 13h3v4h-3z",                             // end kulesi
    "r-air": "M1.5 11.5L22.5 2 16 22l-4.5-7.5z",                                                // kağıt uçak
    "r-boat": "M1 14h22l-3.5 7h-15zM11 2h2v11h-2zM13 3.5l6.5 8H13z",                            // tekne
    "r-horse": "M5 22l1.5-7.5-2.5-1L6 7l4.5-5 2 1.5L17 2l1.5 3.5-2 1.5 4.5 7-2.5 1.5-3.5-4-2.5 2.5 1 8z" // at
  };

  function mcSvg(d) { return '<svg viewBox="0 0 24 24" fill="currentColor" fill-rule="evenodd"><path d="' + d + '"/></svg>'; }

  // renkli zemin üstünde okunur ikon rengi
  function mcInk(hex) {
    var n = parseInt(String(hex || "#fff").replace("#", ""), 16);
    var l = 0.299 * ((n >> 16) & 255) + 0.587 * ((n >> 8) & 255) + 0.114 * (n & 255);
    return l > 140 ? "#111" : "#fff";
  }

  function mcFmt(n) { return Math.round(n).toLocaleString("tr-TR"); }

  function mcCreate() {
    var m = { bpp: 4, cx: 0, cz: 0, follow: true, tiles: {}, marks: {}, cells: {}, showStructs: true, data: {}, pin: null,
      wpEls: {}, hide: {}, mode: store.get("mcRouteMode") || "air", rt: null };
    try { m.hide = JSON.parse(store.get("mcHide") || "{}") || {}; } catch (e) { m.hide = {}; }
    if (store.get("mcStructs") === "0") m.showStructs = false;
    var root = el("div", "mcmap");
    m.layer = el("div", "mclayer");
    m.mlayer = el("div", "mcmarks");
    m.svg = document.createElementNS(SVGNS, "svg");
    m.svg.setAttribute("class", "mcroute");
    m.line = document.createElementNS(SVGNS, "line");
    m.svg.appendChild(m.line);
    m.pathB = document.createElementNS(SVGNS, "path");          // koyu kontur: yeşil arazide de görünsün
    m.pathB.setAttribute("class", "mcrb");
    m.svg.appendChild(m.pathB);
    m.pathW = document.createElementNS(SVGNS, "path");          // rota: suyolu / yürünecek kısım
    m.pathW.setAttribute("class", "mcrw");
    m.pathL = document.createElementNS(SVGNS, "path");          // tekne için kara (taşıma), at için yüzme
    m.pathL.setAttribute("class", "mcrl");
    m.svg.appendChild(m.pathW);
    m.svg.appendChild(m.pathL);
    m.modes = el("div", "mcmodes");                               // rota türü: kuş uçuşu / tekne / at
    m.modeBtns = {};
    [["air", "Kuş uçuşu"], ["boat", "Tekne"], ["horse", "At"]].forEach(function (o) {
      var b = el("button", "mcmb");
      b.innerHTML = mcSvg(MCI["r-" + o[0]]);
      b.appendChild(el("span", "", o[1]));
      b.onclick = function (e) {
        e.stopPropagation();
        m.mode = o[0];
        store.set("mcRouteMode", o[0]);
        m.rt = null;
        mcDraw();
      };
      m.modes.appendChild(b);
      m.modeBtns[o[0]] = b;
    });
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
    [m.layer, m.mlayer, m.wpLayer, m.svg, m.pinEl, m.flag, m.player, m.hud, m.info, m.tip, m.form, m.layersP, m.wpP, m.modes, ctl]
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
        if (MCI[badge[2]]) {
          bd.innerHTML = mcSvg(MCI[badge[2]]);
          bd.className = "mcbadge ic";
          bd.style.color = mcInk(badge[1]);
        }
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
      }, [t[1], t[3], t[0]]);
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
      if (/\b(mcctl|mcform|mctip|mcmk|mchud|mcwp|mcmodes)\b/.test(t.className || "")) return true;
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
    // ---- hedef + rota (kuş uçuşu / tekne / at) ----
    var tg = mcTargetHere(d.target, d.dim || 0), route = null;
    m.modes.style.display = tg ? "" : "none";
    for (var mb in m.modeBtns) m.modeBtns[mb].className = "mcmb" + (mb === m.mode ? " on" : "");
    m.pathW.setAttribute("d", "");
    m.pathL.setAttribute("d", "");
    m.pathB.setAttribute("d", "");
    if (tg) {
      var tx = (tg.x - m.cx) / bpp + W / 2, tzs = (tg.z - m.cz) / bpp + H / 2;
      m.flag.style.display = "";
      m.flag.style.left = Math.round(tx) + "px";
      m.flag.style.top = Math.round(tzs) + "px";
      if (px != null) {
        m.svg.style.display = "";
        m.svg.setAttribute("width", W);
        m.svg.setAttribute("height", H);
        var rt = mcRouteFor(d, tg), aim = tg, note = "";
        var dist = Math.sqrt(Math.pow(tg.x - d.x, 2) + Math.pow(tg.z - d.z, 2));
        if (rt && rt.data && !rt.data.error) {
          var al = mcAlong(rt.data.pts, d.x, d.z);
          var chain = [[d.x, d.z], al.proj].concat(rt.data.pts.slice(al.seg + 1));
          var cats = [rt.data.segs[al.seg], rt.data.segs[al.seg]].concat(rt.data.segs.slice(al.seg + 1));
          var bad = m.mode === "boat" ? "kara" : "su", dw = "", dl = "";
          for (var ci = 0; ci < chain.length - 1; ci++) {
            var sg = "M" + ((chain[ci][0] - m.cx) / bpp + W / 2).toFixed(1) + " " + ((chain[ci][1] - m.cz) / bpp + H / 2).toFixed(1) +
              "L" + ((chain[ci + 1][0] - m.cx) / bpp + W / 2).toFixed(1) + " " + ((chain[ci + 1][1] - m.cz) / bpp + H / 2).toFixed(1);
            if (cats[ci] === bad) dl += sg; else dw += sg;
          }
          m.pathW.setAttribute("d", dw);
          m.pathL.setAttribute("d", dl);
          m.pathB.setAttribute("d", dw + dl);
          m.line.style.display = "none";
          aim = { x: al.ahead[0], z: al.ahead[1] };
          dist = al.remain;
          if (rt.data.land > 0) note = (m.mode === "boat" ? "karada " : "yüzerek ") + mcFmt(rt.data.land) + " blok";
          if (rt.pending) note = (note ? note + " · " : "") + "yenileniyor…";
        } else {
          m.line.style.display = "";
          m.line.setAttribute("x1", px); m.line.setAttribute("y1", pz);
          m.line.setAttribute("x2", tx); m.line.setAttribute("y2", tzs);
          if (rt && rt.pending) note = "rota hesaplanıyor…";
          else if (rt && rt.data && rt.data.error) note = "rota yok: " + rt.data.error;
          else if (m.mode !== "air" && (d.dim || 0) !== 0) note = "tekne/at rotası sadece Overworld'de";
        }
        // hedefin (rotada: ~32 blok ilerideki noktanın) yaw cinsinden yönü; pozitif fark = sağa dön
        var wantDeg = Math.atan2(-(aim.x - d.x), aim.z - d.z) * 180 / Math.PI;
        var relDeg = ((wantDeg - (d.yaw || 0)) % 360 + 540) % 360 - 180;
        route = { dist: dist, rel: relDeg, note: note };
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
        r.appendChild(document.createTextNode(" " + mcFmt(route.dist) + " blok · " + dir + (route.note ? " · " + route.note : "")));
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

  // ---- tekne / at rotası (sunucuda A*, rota.py) ----
  // Aynı hedef + tür için bir kez istenir; oyuncu rotadan uzaklaşırsa (en fazla 5 sn'de bir) yeniden hesaplanır.
  function mcRouteFor(d, tg) {
    var m = MC;
    if (m.mode === "air" || (d.dim || 0) !== 0 || !d.seed) return null;
    var key = m.mode + ":" + d.seed + ":" + Math.round(tg.x) + ":" + Math.round(tg.z), rt = m.rt, now = Date.now();
    if (rt && rt.key === key) {
      if (rt.pending || !rt.data || rt.data.error || now - rt.at < 5000) return rt;
      if (mcAlong(rt.data.pts, d.x, d.z).dist < Math.max(48, rt.data.scale * 4)) return rt;
    }
    var nr = { key: key, pending: true, at: now, data: rt && rt.key === key ? rt.data : null };
    m.rt = nr;
    fetch("/mc/route?s=" + d.seed + "&m=" + m.mode + "&x0=" + Math.round(d.x) + "&z0=" + Math.round(d.z) +
          "&x1=" + Math.round(tg.x) + "&z1=" + Math.round(tg.z))
      .then(function (r) { return r.json(); })
      .then(function (j) { nr.data = j; })
      .catch(function () { nr.data = { error: "bağlantı" }; })
      .then(function () { nr.pending = false; nr.at = Date.now(); if (MC && MC.rt === nr) mcDraw(); });
    return nr;
  }

  // oyuncunun rotadaki yeri: en yakın parça, izdüşüm, kalan uzunluk, ~32 blok ilerideki nokta (köşede yön erken dönsün)
  function mcAlong(pts, x, z) {
    var best = { dist: Infinity, seg: 0, proj: pts[0] };
    for (var i = 0; i < pts.length - 1; i++) {
      var ax = pts[i][0], az = pts[i][1], vx = pts[i + 1][0] - ax, vz = pts[i + 1][1] - az, L2 = vx * vx + vz * vz;
      var t = L2 ? Math.max(0, Math.min(1, ((x - ax) * vx + (z - az) * vz) / L2)) : 0;
      var qx = ax + vx * t, qz = az + vz * t, dd = Math.sqrt((x - qx) * (x - qx) + (z - qz) * (z - qz));
      if (dd < best.dist) best = { dist: dd, seg: i, proj: [qx, qz] };
    }
    var remain = 0, look = 32, ahead = null, cur = best.proj;
    for (var j = best.seg; j < pts.length - 1; j++) {
      var nx = pts[j + 1][0], nz = pts[j + 1][1];
      var sl = Math.sqrt((nx - cur[0]) * (nx - cur[0]) + (nz - cur[1]) * (nz - cur[1]));
      if (!ahead && remain + sl >= look) {
        var f = (look - remain) / (sl || 1);
        ahead = [cur[0] + (nx - cur[0]) * f, cur[1] + (nz - cur[1]) * f];
      }
      remain += sl;
      cur = [nx, nz];
    }
    best.remain = remain + best.dist;
    best.ahead = ahead || pts[pts.length - 1];
    return best;
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
      if (MCI[s[6]]) {                                          // harf yerine ikon (anahtar s[6])
        e.innerHTML = mcSvg(MCI[s[6]]);
        e.className = "mcmk ic";
        e.style.color = mcInk(s[4]);
      }
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
