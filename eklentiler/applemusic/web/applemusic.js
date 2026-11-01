/* Apple Music eklentisi — "applemusic" widget'ı. Sadece window.PCK kullanır.
   Eski Android Chrome: ?. ?? replaceAll, sınıf alanları, async/await, flex gap yok; var + function kullan.
   DOM bir kez kurulur, her yenilemede sadece içerik güncellenir (liste kaydırma konumu korunur). */
(function () {
  "use strict";
  var P = window.PCK;
  if (!P) return;

  P.icons({
    applemusic: '<path d="M9 18V6l10-2v12"/><circle cx="6.5" cy="18" r="2.5"/><circle cx="16.5" cy="16" r="2.5"/>',
    am_shuffle: '<path d="M3 7h3.5c2 0 3.2 1 4.3 2.7l2.4 4.6c1.1 1.7 2.3 2.7 4.3 2.7H21M3 17h3.5c1.4 0 2.4-.5 3.3-1.4M14.2 8.4c.9-.9 1.9-1.4 3.3-1.4H21"/><path d="M18.5 4.5L21 7l-2.5 2.5M18.5 14.5L21 17l-2.5 2.5"/>',
    am_repeat: '<path d="M4 11V9.5A2.5 2.5 0 016.5 7H19M20 13v1.5a2.5 2.5 0 01-2.5 2.5H5"/><path d="M16.5 4.5L19 7l-2.5 2.5M7.5 19.5L5 17l2.5-2.5"/>',
    am_repeat1: '<path d="M4 11V9.5A2.5 2.5 0 016.5 7H19M20 13v1.5a2.5 2.5 0 01-2.5 2.5H5"/><path d="M16.5 4.5L19 7l-2.5 2.5M7.5 19.5L5 17l2.5-2.5"/><path d="M11.2 10.6l1.3-.8v4.6"/>',
    am_vol: '<path d="M4 9.5h3.5L12 5v14l-4.5-4.5H4z" fill="currentColor"/><path d="M15.5 8.5a5 5 0 010 7M18 6a8.5 8.5 0 010 12"/>'
  });

  var root = null, ui = {};
  var cur = null;                 // son veri {server, connected, state}
  var clock = { pos: 0, dur: 0, playing: false, at: 0 };
  var listSig = "", listScroll = 0, timer = null, volBusy = false;

  function fmt(s) {
    s = Math.max(0, Math.floor(s || 0));
    var m = Math.floor(s / 60), r = s % 60;
    return m + ":" + (r < 10 ? "0" : "") + r;
  }

  function iconBtn(cls, icon, label, fn) {
    var b = P.el("button", "applemusic-btn " + cls);
    b.setAttribute("aria-label", label);
    b.appendChild(P.iconEl(icon));
    b.onclick = fn;
    return b;
  }

  function setIcon(btn, icon) {
    btn.innerHTML = "";
    btn.appendChild(P.iconEl(icon));
  }

  function send(cmd, args) {
    var params = { cmd: cmd };
    for (var k in (args || {})) params[k] = args[k];
    return P.api("/api/action", { name: "applemusic.komut", params: params }).then(function (r) {
      if (!r || !r.ok) {
        P.toast("HATA: " + ((r && r.error) || "EAMUSİC CEVAP VERMEDİ"), 2500);
        return;
      }
      if (r.result) update(r.result);
    });
  }

  function build() {
    root = P.el("div", "applemusic");

    // --- kapalı / bağlanmadı görünümü ---
    ui.off = P.el("div", "applemusic-off");
    ui.offIcon = P.el("div", "applemusic-off-ic");
    ui.offIcon.appendChild(P.iconEl("applemusic"));
    ui.offTitle = P.el("div", "applemusic-off-t", "");
    ui.offSub = P.el("div", "applemusic-off-s", "");
    ui.openBtn = P.el("button", "applemusic-open", "Aç");
    ui.openBtn.onclick = function () {
      ui.openBtn.disabled = true;
      P.api("/api/action", { name: "applemusic.ac" }).then(function (r) {
        P.toast(r && r.ok ? String(r.result || "AÇILIYOR") : "HATA: " + ((r && r.error) || ""), 2500);
        setTimeout(function () { ui.openBtn.disabled = false; P.refresh(); }, 2500);
      });
    };
    ui.off.appendChild(ui.offIcon);
    ui.off.appendChild(ui.offTitle);
    ui.off.appendChild(ui.offSub);
    ui.off.appendChild(ui.openBtn);
    root.appendChild(ui.off);

    // --- oynatıcı ---
    ui.on = P.el("div", "applemusic-on");
    var left = P.el("div", "applemusic-sol");

    var top = P.el("div", "applemusic-ust");
    ui.art = P.el("div", "applemusic-art");
    ui.artImg = P.el("img", "");
    ui.artImg.alt = "";
    ui.art.appendChild(ui.artImg);
    ui.art.appendChild(P.iconEl("applemusic"));
    var meta = P.el("div", "applemusic-meta");
    ui.title = P.el("div", "applemusic-title", "");
    ui.artist = P.el("div", "applemusic-artist", "");
    meta.appendChild(ui.title);
    meta.appendChild(ui.artist);
    top.appendChild(ui.art);
    top.appendChild(meta);
    left.appendChild(top);

    ui.spek = P.el("canvas", "applemusic-spek");
    left.appendChild(ui.spek);

    var prog = P.el("div", "applemusic-prog");
    ui.bar = P.el("div", "applemusic-bar");
    ui.fill = P.el("div", "applemusic-fill");
    ui.bar.appendChild(ui.fill);
    ui.bar.onclick = function (e) {
      if (!clock.dur) return;
      var rect = ui.bar.getBoundingClientRect();
      var ratio = Math.min(1, Math.max(0, ((e.clientX - rect.left) / P.zoom()) / (rect.width / P.zoom())));
      clock.pos = ratio * clock.dur;
      clock.at = Date.now();
      paintClock();
      send("seek", { pos: Math.round(clock.pos) });
    };
    var times = P.el("div", "applemusic-times");
    ui.tCur = P.el("span", "", "0:00");
    ui.tDur = P.el("span", "", "0:00");
    times.appendChild(ui.tCur);
    times.appendChild(ui.tDur);
    prog.appendChild(ui.bar);
    prog.appendChild(times);
    left.appendChild(prog);

    var ctr = P.el("div", "applemusic-ctr");
    ui.shuffle = iconBtn("applemusic-tog", "am_shuffle", "Karışık", function () { send("shuffle"); });
    ui.prev = iconBtn("", "prev", "Önceki", function () { send("prev"); });
    ui.play = iconBtn("applemusic-play", "play", "Oynat", function () {
      // anında geri bildirim: simgeyi hemen değiştir
      clock.playing = !clock.playing;
      clock.at = Date.now();
      setIcon(ui.play, clock.playing ? "pause" : "play");
      send("toggle");
    });
    ui.next = iconBtn("", "next", "Sonraki", function () { send("next"); });
    ui.repeat = iconBtn("applemusic-tog", "am_repeat", "Tekrar", function () { send("repeat"); });
    [ui.shuffle, ui.prev, ui.play, ui.next, ui.repeat].forEach(function (b) { ctr.appendChild(b); });
    left.appendChild(ctr);

    var vol = P.el("div", "applemusic-vol");
    vol.appendChild(P.iconEl("am_vol"));
    ui.vol = P.el("input", "applemusic-range");
    ui.vol.type = "range";
    ui.vol.min = "0";
    ui.vol.max = "100";
    ui.vol.oninput = function () { volBusy = true; };
    ui.vol.onchange = function () {
      send("volume", { v: Number(ui.vol.value) }).then(function () { volBusy = false; });
    };
    vol.appendChild(ui.vol);
    left.appendChild(vol);

    var right = P.el("div", "applemusic-sag");
    right.appendChild(P.el("div", "applemusic-h", "Çalma listeleri"));
    ui.lists = P.el("div", "applemusic-lists");
    ui.lists.onscroll = function () { listScroll = ui.lists.scrollTop; };
    right.appendChild(ui.lists);

    ui.on.appendChild(left);
    ui.on.appendChild(right);
    root.appendChild(ui.on);
  }

  function renderLists(list) {
    var sig = list.map(function (p) { return p.id; }).join(",");
    if (sig === listSig) return;
    listSig = sig;
    ui.lists.innerHTML = "";
    if (!list.length) {
      ui.lists.appendChild(P.el("div", "applemusic-empty", "Çalma listesi yok"));
      return;
    }
    list.forEach(function (pl) {
      var card = P.el("div", "applemusic-card");
      var cover = P.el("button", "applemusic-cover");
      cover.setAttribute("aria-label", pl.name + " çal");
      if (pl.artwork) {
        var img = P.el("img", "");
        img.src = pl.artwork;
        img.alt = "";
        img.loading = "lazy";
        cover.appendChild(img);
      } else {
        cover.appendChild(P.iconEl("applemusic"));
      }
      cover.onclick = function () {
        P.toast("ÇALINIYOR: " + pl.name, 1500);
        send("playlist", { id: pl.id });
      };
      var mix = iconBtn("applemusic-mix", "am_shuffle", pl.name + " karışık çal", function () {
        P.toast("KARIŞIK: " + pl.name, 1500);
        send("playlist", { id: pl.id, shuffle: true });
      });
      card.appendChild(cover);
      card.appendChild(mix);
      card.appendChild(P.el("div", "applemusic-name", pl.name));
      ui.lists.appendChild(card);
    });
  }

  function paintClock() {
    var pos = clock.pos + (clock.playing ? (Date.now() - clock.at) / 1000 : 0);
    if (clock.dur) pos = Math.min(pos, clock.dur);
    ui.fill.style.width = (clock.dur ? (pos / clock.dur) * 100 : 0) + "%";
    ui.tCur.textContent = fmt(pos);
    ui.tDur.textContent = fmt(clock.dur);
  }

  function update(d) {
    cur = d || {};
    var st = cur.state || null;
    var ready = cur.connected && st && st.authorized;

    ui.off.style.display = ready ? "none" : "";
    ui.on.style.display = ready ? "" : "none";

    if (!ready) {
      if (!cur.server) {
        ui.offTitle.textContent = "EAMusic kapalı";
        ui.offSub.textContent = "PC'de Apple Music istemcisini açın.";
        ui.openBtn.style.display = "";
        ui.openBtn.textContent = "EAMusic'i aç";
      } else if (!cur.connected) {
        ui.offTitle.textContent = "Pencere açık değil";
        ui.offSub.textContent = "EAMusic sunucusu çalışıyor ama pencere bağlı değil.";
        ui.openBtn.style.display = "";
        ui.openBtn.textContent = "Pencereyi aç";
      } else {
        ui.offTitle.textContent = "Giriş yapılmadı";
        ui.offSub.textContent = "PC'deki EAMusic penceresinde “Apple Kimliği ile Bağlan” düğmesine basın.";
        ui.openBtn.style.display = "none";
      }
      return;
    }

    var t = st.track;
    ui.title.textContent = t ? t.title : "Çalan şarkı yok";
    ui.artist.textContent = t ? t.artist : "Bir çalma listesi seçin";
    if (t && t.artwork) {
      if (ui.artImg.getAttribute("src") !== t.artwork) ui.artImg.src = t.artwork;
      ui.art.className = "applemusic-art has";
    } else {
      ui.art.className = "applemusic-art";
    }

    clock.pos = st.pos || 0;
    clock.dur = st.dur || 0;
    clock.playing = !!st.playing;
    // durum gönderildiğinden bu yana geçen süre (PC ve telefon saatleri farklı olabilir → göreli "age")
    clock.at = Date.now() - Math.min(Math.max(cur.age || 0, 0), 10000);
    paintClock();

    setIcon(ui.play, st.playing ? "pause" : "play");
    ui.play.className = "applemusic-btn applemusic-play" + (st.loading ? " applemusic-loading" : "");
    ui.shuffle.className = "applemusic-btn applemusic-tog" + (st.shuffle ? " on" : "");
    ui.repeat.className = "applemusic-btn applemusic-tog" + (st.repeat !== "none" ? " on" : "");
    setIcon(ui.repeat, st.repeat === "one" ? "am_repeat1" : "am_repeat");
    if (!volBusy) ui.vol.value = String(Math.round((st.volume || 0) * 100));

    renderLists(st.playlists || []);
  }

  /* ---- Spektrum: EAMusic'in 32 bantlık analizi, SSE ile (/applemusic/spektrum) ----
     Akış sadece Müzik sekmesi açık, oynatıcı görünür ve sayfa ön plandayken açıktır.
     Çizim requestAnimationFrame ile; çubuklar sönünce döngü durur (boşta CPU yok). */
  var BANDS = 32;
  var spek = {
    es: null, raf: 0, last: 0, lastFrame: 0, color: "", w: 0, h: 0, ctx: null,
    target: new Array(BANDS), level: new Array(BANDS)
  };
  for (var bi = 0; bi < BANDS; bi++) { spek.target[bi] = 0; spek.level[bi] = 0; }

  function spekWanted() {
    return !!(root && cur && cur.connected && cur.state && cur.state.authorized &&
      !document.hidden && P.tab() === "applemusic" && document.body.contains(root));
  }

  function spekOpen() {
    if (spek.es || !window.EventSource) return;
    spek.es = new EventSource("/applemusic/spektrum");
    spek.es.onmessage = function (e) {
      var v;
      try { v = JSON.parse(e.data); } catch (x) { return; }
      if (typeof v !== "string") return;           // canlı tutma
      var parts = v ? v.split(",") : [];
      for (var i = 0; i < BANDS; i++) spek.target[i] = Math.min(1, (Number(parts[i]) || 0) / 255);
      spek.lastFrame = Date.now();
      spekKick();
    };
  }

  function spekClose() {
    if (spek.es) { spek.es.close(); spek.es = null; }
    for (var i = 0; i < BANDS; i++) spek.target[i] = 0;
  }

  function spekSync() {
    if (spekWanted()) spekOpen(); else spekClose();
    spekKick();
  }

  function spekKick() {
    if (!spek.raf && !document.hidden && ui.spek) {
      spek.last = 0;
      spek.raf = requestAnimationFrame(spekLoop);
    }
  }

  function spekSize() {
    var c = ui.spek;
    var dpr = window.devicePixelRatio || 1;
    var w = Math.round(c.clientWidth * dpr), h = Math.round(c.clientHeight * dpr);
    if (w !== spek.w || h !== spek.h) {           // sadece boyut değişince (gereksiz DOM değişikliği yok)
      spek.w = c.width = w;
      spek.h = c.height = h;
      spek.ctx = null;
    }
    if (!spek.ctx) spek.ctx = c.getContext("2d");
    if (!spek.color) spek.color = getComputedStyle(root).getPropertyValue("--ac").trim() || "#fff";
  }

  function spekLoop(ts) {
    spek.raf = 0;
    if (document.hidden || !root || !document.body.contains(root)) return;
    var dt = spek.last ? Math.min(100, ts - spek.last) : 16.7;
    spek.last = ts;
    // Kare gelmiyorsa (müzik durdu, bağlantı koptu) hedef sıfır → çubuklar yavaşça söner
    var stale = Date.now() - spek.lastFrame > 400;
    var up = 1 - Math.pow(0.35, dt / 16.7);       // çıkış hızlı
    var down = 1 - Math.pow(0.94, dt / 16.7);     // iniş yavaş (~1 sn'de söner)
    var active = false, i;
    for (i = 0; i < BANDS; i++) {
      var t = stale ? 0 : spek.target[i], l = spek.level[i];
      l += (t - l) * (t > l ? up : down);
      if (l < 0.004) l = 0;
      spek.level[i] = l;
      if (l > 0 || t > 0) active = true;
    }
    spekDraw();
    if (active) spek.raf = requestAnimationFrame(spekLoop);
  }

  function spekDraw() {
    spekSize();
    var g = spek.ctx, w = spek.w, h = spek.h;
    if (!g || !w || !h) return;
    g.clearRect(0, 0, w, h);
    var step = w / BANDS;
    var bw = Math.max(2, step * 0.45);              // ince çubuk
    var r = bw / 2;
    g.lineWidth = bw;
    g.lineCap = "round";
    g.strokeStyle = spek.color;
    // Boşta: soluk noktalar (çubuğun dibi)
    g.globalAlpha = 0.25;
    g.beginPath();
    var i, x;
    for (i = 0; i < BANDS; i++) {
      x = step * i + step / 2;
      g.moveTo(x, h - r);
      g.lineTo(x, h - r);
    }
    g.stroke();
    g.globalAlpha = 1;
    g.beginPath();
    for (i = 0; i < BANDS; i++) {
      var bh = spek.level[i] * (h - bw);
      if (bh < 0.5) continue;
      x = step * i + step / 2;
      g.moveTo(x, h - r);
      g.lineTo(x, h - r - bh);
    }
    g.stroke();
  }

  P.on("render", function (tab) {
    spek.color = "";                                 // tema (oyun) değişmiş olabilir
    if (tab !== "applemusic") spekClose(); else spekSync();
  });
  P.on("resize", function () { spek.ctx = null; spekKick(); });
  document.addEventListener("visibilitychange", function () {
    if (document.hidden) {
      spekClose();
      if (spek.raf) { cancelAnimationFrame(spek.raf); spek.raf = 0; }
    } else {
      spekSync();
    }
  });

  function ensureTimer() {
    if (timer) return;
    timer = setInterval(function () {
      if (!root || !document.body.contains(root)) {
        clearInterval(timer);
        timer = null;
        return;
      }
      if (clock.playing) paintClock();
    }, 500);
  }

  P.widget("applemusic", function (s) {
    if (!root) build();
    update(s.data || {});
    ensureTimer();
    // Aynı DOM yeni bölüme taşınınca kaydırma konumu sıfırlanabilir → geri yükle
    var keep = listScroll;
    setTimeout(function () {
      if (ui.lists && keep) ui.lists.scrollTop = keep;
      spekSync();                                    // kök artık sayfada: akışı aç/kapat, boşta noktaları çiz
    }, 0);
    return root;
  });
})();
