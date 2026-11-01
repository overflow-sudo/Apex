/* APEX FINANCE eklentisi — "apex_portfoy" widget'ı + boşta portföy slayt gösterisi. Sadece window.PCK kullanır.
   Eski Android Chrome: ?. ?? replaceAll, sınıf alanları, async/await, flex gap yok; var + function kullan.
   Veri: her /api/ui cevabındaki "apex" alanı (eklenti.py → @extra), PIN korumalı. */
(function () {
  "use strict";
  var P = window.PCK;
  if (!P) return;

  P.icons({
    apex: '<path d="M4 19h16"/><path d="M5 15l4-5 4 3 6-7"/><path d="M15 6h4v4"/>'
  });

  var SVGNS = "http://www.w3.org/2000/svg";
  var son = null;           // son "apex" verisi
  var odak = [];            // son odak listesi (müzik çalıyorsa çekirdeğin medya ekranı öncelikli)

  // ---------- biçimlendirme ----------
  var nf0 = null, nf2 = null;
  try {
    nf0 = new Intl.NumberFormat("tr-TR", { maximumFractionDigits: 0 });
    nf2 = new Intl.NumberFormat("tr-TR", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  } catch (e) { /* eski tarayıcı: yedek biçim */ }

  function num(v, d) {
    var f = d ? nf2 : nf0;
    if (f) return f.format(v);
    return d ? v.toFixed(2) : String(Math.round(v));
  }

  function para(v, ccy, d) {
    if (v === null || v === undefined) return "—";
    var s = num(Math.abs(v), d);
    var sign = v < 0 ? "-" : "";
    if (ccy === "TRY") return sign + "₺" + s;
    if (ccy === "USD") return sign + "$" + s;
    return sign + s + " " + (ccy || "");
  }

  function isaretli(v, ccy) {
    if (v === null || v === undefined) return "—";
    return (v > 0 ? "+" : "") + para(v, ccy);
  }

  function yuzde(v) {
    if (v === null || v === undefined) return "—";
    return (v > 0 ? "+" : v < 0 ? "-" : "") + "%" + num(Math.abs(v * 100), true);
  }

  function ton(v) {
    if (v === null || v === undefined || Math.abs(v) < 1e-9) return "";
    return v > 0 ? " apex-up" : " apex-down";
  }

  function ok(v) {
    if (v === null || v === undefined || Math.abs(v) < 1e-9) return "";
    return v > 0 ? "▲ " : "▼ ";
  }

  function pad2(n) { return (n < 10 ? "0" : "") + n; }

  function tarih(iso) {
    if (!iso) return "";
    var a = String(iso).slice(0, 10).split("-");
    var ay = ["Oca", "Şub", "Mar", "Nis", "May", "Haz", "Tem", "Ağu", "Eyl", "Eki", "Kas", "Ara"];
    return parseInt(a[2], 10) + " " + ay[parseInt(a[1], 10) - 1] + " " + a[0];
  }

  function el(tag, cls, txt) { return P.el(tag, cls, txt === undefined ? undefined : txt); }

  function aktif(d) {
    return d && d.portfoyler && d.portfoyler.length ? d.portfoyler[0] : null;
  }

  function toplam(p) {
    return p.toplam !== null && p.toplam !== undefined ? p.toplam : p.fiyatli;
  }

  // ---------- performans çizgisi ----------
  // değer çizgisi (dolu) + yatırılan para çizgisi (kesikli); aradaki fark kâr/zarardır
  function cizgi(degerler, yatirilan, cls) {
    var svg = document.createElementNS(SVGNS, "svg");
    svg.setAttribute("viewBox", "0 0 300 100");
    svg.setAttribute("preserveAspectRatio", "none");
    svg.setAttribute("class", "apex-spark " + (cls || ""));
    if (!degerler || degerler.length < 2) return svg;
    var hepsi = degerler.concat(yatirilan || []);
    var mn = Infinity, mx = -Infinity, i;
    for (i = 0; i < hepsi.length; i++) {
      if (hepsi[i] < mn) mn = hepsi[i];
      if (hepsi[i] > mx) mx = hepsi[i];
    }
    if (mx - mn < 1e-9) { mx += 1; mn -= 1; }
    function noktalar(seri) {
      var pts = [];
      for (var k = 0; k < seri.length; k++) {
        var x = (k / (seri.length - 1)) * 300;
        var y = 6 + (1 - (seri[k] - mn) / (mx - mn)) * 88;
        pts.push(x.toFixed(1) + "," + y.toFixed(1));
      }
      return pts.join(" ");
    }
    var dp = noktalar(degerler);
    var alan = document.createElementNS(SVGNS, "polygon");
    alan.setAttribute("points", "0,100 " + dp + " 300,100");
    alan.setAttribute("class", "apex-spark-area");
    svg.appendChild(alan);
    if (yatirilan && yatirilan.length === degerler.length) {
      var yl = document.createElementNS(SVGNS, "polyline");
      yl.setAttribute("points", noktalar(yatirilan));
      yl.setAttribute("class", "apex-spark-inv");
      yl.setAttribute("vector-effect", "non-scaling-stroke");
      svg.appendChild(yl);
    }
    var line = document.createElementNS(SVGNS, "polyline");
    line.setAttribute("points", dp);
    line.setAttribute("class", "apex-spark-line");
    line.setAttribute("vector-effect", "non-scaling-stroke");
    svg.appendChild(line);
    return svg;
  }

  // ---------- kapalı / hata görünümü ----------
  function kapali(d) {
    var box = el("div", "apex-off");
    var ic = el("div", "apex-off-ic");
    ic.appendChild(P.iconEl("apex"));
    box.appendChild(ic);
    // APEX kapanırsa kumanda kendiliğinden yeniden başlatır (eklenti.py _bekci), düğmeye gerek yok
    box.appendChild(el("div", "apex-off-t", d && d.kapali ? "APEX başlatılıyor…" : (d && d.hata) || "Portföy verisi yok"));
    box.appendChild(el("div", "apex-off-s", d && d.kapali ? "Portföy uygulaması birazdan kendiliğinden açılacak." : "APEX'te bir portföy oluşturun."));
    return box;
  }

  // ---------- sekme widget'ı ----------
  function stat(etiket, deger, alt, cls) {
    var c = el("div", "apex-stat");
    c.appendChild(el("div", "apex-stat-l", etiket));
    c.appendChild(el("div", "apex-stat-v" + (cls || ""), deger));
    if (alt) c.appendChild(el("div", "apex-stat-s" + (cls || ""), alt));
    return c;
  }

  function varlikSatiri(v, ccy) {
    var r = el("div", "apex-row");
    var sol = el("div", "apex-row-l");
    sol.appendChild(el("div", "apex-row-sym", v.sembol));
    if (v.agirlik !== null && v.agirlik !== undefined) sol.appendChild(el("div", "apex-row-w", "%" + num(v.agirlik * 100, false)));
    r.appendChild(sol);
    var sag = el("div", "apex-row-r");
    sag.appendChild(el("div", "apex-row-v", v.deger === null ? "fiyat yok" : para(v.deger, ccy)));
    if (v.kz_yuzde !== null && v.kz_yuzde !== undefined) sag.appendChild(el("div", "apex-row-p" + ton(v.kz_yuzde), yuzde(v.kz_yuzde)));
    r.appendChild(sag);
    return r;
  }

  P.widget("apex_portfoy", function (section) {
    var d = section.data || son;
    var p = aktif(d);
    if (!p) return kapali(d);
    var ccy = p.para;
    var root = el("div", "apex");

    var ust = el("div", "apex-top");
    var t = stat(p.ad || "Portföy", para(toplam(p), ccy), p.fiyatsiz ? p.fiyatsiz + " varlığın fiyatı yok" : "Yatırılan " + para(p.yatirilan, ccy), "");
    t.className += " apex-stat-big";
    ust.appendChild(t);
    ust.appendChild(stat("Toplam K/Z", isaretli(p.kz, ccy), yuzde(p.kz_yuzde), ton(p.kz)));
    ust.appendChild(stat("Bugün", isaretli(p.gun, ccy), yuzde(p.gun_yuzde), ton(p.gun)));
    root.appendChild(ust);

    var alt = el("div", "apex-bottom");
    var gk = el("div", "apex-card apex-chart");
    var gh = el("div", "apex-card-h");
    gh.appendChild(el("span", "", "Değer · yatırılan"));
    gh.appendChild(el("span", "apex-card-x" + ton(p.kz), yuzde(p.kz_yuzde)));
    gk.appendChild(gh);
    gk.appendChild(cizgi(p.grafik, p.grafik_yatirilan, ""));
    var gt = el("div", "apex-card-f");
    gt.appendChild(el("span", "", tarih(p.grafik_ilk)));
    gt.appendChild(el("span", "", tarih(p.grafik_son)));
    gk.appendChild(gt);
    alt.appendChild(gk);

    var vk = el("div", "apex-card apex-list");
    var vh = el("div", "apex-card-h");
    vh.appendChild(el("span", "", "Varlıklar"));
    vh.appendChild(el("span", "apex-card-x", (p.varliklar || []).length + ""));
    vk.appendChild(vh);
    var liste = el("div", "apex-rows");
    (p.varliklar || []).forEach(function (v) { liste.appendChild(varlikSatiri(v, ccy)); });
    vk.appendChild(liste);
    if (p.dagilim && p.dagilim.length) vk.appendChild(dagilimCubugu(p.dagilim));
    alt.appendChild(vk);
    root.appendChild(alt);

    if (d && !d.ok && d.hata) root.appendChild(el("div", "apex-stale", "Son veri gösteriliyor · " + d.hata));
    return root;
  });

  function dagilimCubugu(dagilim) {
    var box = el("div", "apex-alloc");
    var bar = el("div", "apex-alloc-bar");
    var leg = el("div", "apex-alloc-leg");
    dagilim.forEach(function (a, i) {
      var seg = el("div", "apex-alloc-seg apex-s" + Math.min(i, 5));
      seg.style.width = Math.max(1, (a.oran || 0) * 100) + "%";
      bar.appendChild(seg);
      var l = el("span", "apex-alloc-item");
      l.appendChild(el("i", "apex-s" + Math.min(i, 5)));
      l.appendChild(document.createTextNode(a.ad + " %" + num((a.oran || 0) * 100, false)));
      leg.appendChild(l);
    });
    box.appendChild(bar);
    box.appendChild(leg);
    return box;
  }

  // ---------- boşta slayt gösterisi ----------
  var sonDokunus = Date.now();
  var ss = null, ssIdx = 0, ssTimer = null, saatTimer = null;

  ["touchstart", "mousedown", "keydown", "wheel"].forEach(function (ev) {
    document.addEventListener(ev, function () { sonDokunus = Date.now(); }, true);
  });

  function ayar() {
    return (son && son.ayar) || { slayt: true, bosta_sn: 120, slayt_sn: 9, muzik_varken: true };
  }

  function calan() {
    for (var i = 0; i < (odak || []).length; i++) {
      if (odak[i].kind === "media" && odak[i].live) return odak[i];
    }
    return null;
  }

  // müzik çalarken slayt istenmiyorsa çekirdeğin "şu an çalıyor" ekranına yol ver
  function muzikEngel() {
    return !ayar().muzik_varken && !!calan();
  }

  // slaytlar: portföy özeti (toplam birikim) + sistem durumu. Hangisinin verisi varsa o gösterilir.
  function ozetSlayti(p) {
    var ccy = p.para;
    var s = el("div", "apex-slide apex-slide-ozet");
    s.appendChild(el("div", "apex-ss-label", p.ad || "Portföy"));
    s.appendChild(el("div", "apex-ss-big", para(toplam(p), ccy)));
    var r = el("div", "apex-ss-row");
    var k1 = el("div", "apex-ss-kv");
    k1.appendChild(el("div", "apex-ss-k", "Toplam K/Z"));
    k1.appendChild(el("div", "apex-ss-v" + ton(p.kz), ok(p.kz) + isaretli(p.kz, ccy) + "  " + yuzde(p.kz_yuzde)));
    r.appendChild(k1);
    var k2 = el("div", "apex-ss-kv");
    k2.appendChild(el("div", "apex-ss-k", "Bugün"));
    k2.appendChild(el("div", "apex-ss-v" + ton(p.gun), ok(p.gun) + isaretli(p.gun, ccy) + "  " + yuzde(p.gun_yuzde)));
    r.appendChild(k2);
    s.appendChild(r);
    return s;
  }

  function sure(sn) {
    if (!sn) return "";
    var m = Math.floor(sn / 60), g = Math.floor(m / 1440), sa = Math.floor(m / 60) % 24;
    return g ? g + " gün " + sa + " sa" : sa + " sa " + (m % 60) + " dk";
  }

  function olcer(etiket, deger, birim, oran, alt, sicak) {
    var c = el("div", "apex-ss-g" + (sicak ? " apex-hot" : ""));
    c.appendChild(el("div", "apex-ss-gl", etiket));
    var v = el("div", "apex-ss-gv", deger);
    if (birim) v.appendChild(el("span", "apex-ss-gu", birim));
    c.appendChild(v);
    var tr = el("div", "apex-ss-track");
    var f = el("div", "apex-ss-fill");
    f.style.width = (oran === null || oran === undefined ? 0 : Math.max(1, Math.min(100, oran))) + "%";
    tr.appendChild(f);
    c.appendChild(tr);
    c.appendChild(el("div", "apex-ss-gs", alt || ""));
    return c;
  }

  function sicaklik(c) {
    return c === null || c === undefined ? "" : Math.round(c) + "°C";
  }

  function sistemSlayti(d) {
    var s = el("div", "apex-slide apex-slide-sistem");
    s.appendChild(el("div", "apex-ss-label", "Sistem" + (d.acik ? " · açık " + sure(d.acik) : "")));
    var g = el("div", "apex-ss-grid");
    var yok = function (v) { return v === null || v === undefined; };
    g.appendChild(olcer("CPU", yok(d.cpu) ? "—" : String(Math.round(d.cpu)), "%", d.cpu,
      [sicaklik(d.cpu_c), d.cpu_ad].filter(Boolean).join(" · "), (d.cpu || 0) >= 90 || (d.cpu_c || 0) >= 85));
    g.appendChild(olcer("GPU", yok(d.gpu) ? "—" : String(Math.round(d.gpu)), "%", d.gpu,
      [sicaklik(d.gpu_c), d.gpu_ad].filter(Boolean).join(" · "), (d.gpu || 0) >= 95 || (d.gpu_c || 0) >= 85));
    var ramO = d.ram_top ? d.ram * 100 / d.ram_top : null;
    g.appendChild(olcer("RAM", yok(d.ram) ? "—" : d.ram.toFixed(1).replace(".", ","),
      d.ram_top ? " / " + Math.round(d.ram_top) + " GB" : "GB", ramO, ramO === null ? "" : "%" + Math.round(ramO) + " dolu", (ramO || 0) >= 90));
    var vrO = d.vram_top && !yok(d.vram) ? d.vram * 100 / d.vram_top : null;
    g.appendChild(olcer("VRAM", yok(d.vram) ? "—" : d.vram.toFixed(1).replace(".", ","),
      d.vram_top ? " / " + Math.round(d.vram_top) + " GB" : "GB", vrO, vrO === null ? "" : "%" + Math.round(vrO) + " dolu", (vrO || 0) >= 95));
    s.appendChild(g);
    return s;
  }

  function slaytlar() {
    var list = [];
    var p = aktif(son);
    if (p) list.push(ozetSlayti(p));
    if (son && son.sistem) list.push(sistemSlayti(son.sistem));
    return list;
  }

  function slaytVar() {
    return !!(aktif(son) || (son && son.sistem));
  }

  function altSatir() {
    if (!ss) return;
    var m = calan();
    ss.stamp.textContent = son && !son.ok && son.hata ? "Son veri · " + son.hata
      : m ? "♪ " + m.title + (m.sub ? " · " + m.sub : "") : "APEX FINANCE";
  }

  function saat() {
    if (!ss) return;
    var d = new Date();
    ss.clock.textContent = pad2(d.getHours()) + ":" + pad2(d.getMinutes());
  }

  function slaytGoster(i) {
    if (!ss) return;
    var list = slaytlar();
    if (!list.length) { slaytKapat(); return; }
    ssIdx = i % list.length;
    ss.stage.innerHTML = "";
    ss.stage.appendChild(list[ssIdx]);
    ss.dots.innerHTML = "";
    for (var k = 0; k < list.length; k++) ss.dots.appendChild(el("i", k === ssIdx ? "on" : ""));
    altSatir();
    // bir kare sonra görünür yap: CSS geçişi (opacity) çalışsın
    setTimeout(function () { if (list[ssIdx].parentNode) list[ssIdx].className += " apex-in"; }, 30);
  }

  function slaytAc() {
    if (ss) return;
    var root = el("div", "apex-ss");
    root.clock = el("div", "apex-ss-clock");
    root.stage = el("div", "apex-ss-stage");
    root.dots = el("div", "apex-ss-dots");
    root.stamp = el("div", "apex-ss-stamp");
    root.appendChild(root.clock);
    root.appendChild(root.stage);
    root.appendChild(root.dots);
    root.appendChild(root.stamp);
    // dokunma slaytı kapatır ve kumandaya döner (dokunuş alttaki düğmelere geçmez)
    var kapat = function (e) { e.preventDefault(); e.stopPropagation(); sonDokunus = Date.now(); slaytKapat(); };
    root.addEventListener("touchstart", kapat, false);
    root.addEventListener("mousedown", kapat, false);
    document.body.appendChild(root);
    ss = root;
    saat();
    saatTimer = setInterval(saat, 10000);
    slaytGoster(0);
    ssTimer = setInterval(function () { slaytGoster(ssIdx + 1); }, Math.max(4, ayar().slayt_sn) * 1000);
  }

  function slaytKapat() {
    if (ssTimer) clearInterval(ssTimer);
    if (saatTimer) clearInterval(saatTimer);
    ssTimer = saatTimer = null;
    if (ss && ss.parentNode) ss.parentNode.removeChild(ss);
    ss = null;
  }

  setInterval(function () {
    var a = ayar();
    if (ss) {
      // müzik başlarsa ya da veri kaybolursa çekil
      if (muzikEngel() || !slaytVar() || document.hidden) slaytKapat();
      else altSatir();   // çalan şarkı satırı güncel kalsın
      return;
    }
    if (!a.slayt || document.hidden || !slaytVar() || muzikEngel()) return;
    if (Date.now() - sonDokunus >= a.bosta_sn * 1000) slaytAc();
  }, 5000);

  P.on("data", function (r) {
    if (r && r.apex) son = r.apex;
    if (r && r.focus) odak = r.focus;
    if (ss && son && son.sistem && ss.stage.firstChild && ss.stage.firstChild.className.indexOf("apex-slide-sistem") >= 0) {
      var yeni = sistemSlayti(son.sistem);
      yeni.className += " apex-in apex-nofade";
      ss.stage.replaceChild(yeni, ss.stage.firstChild);
    }
  });
  P.on("close", function () { if (ss) { slaytKapat(); return true; } });
})();
