/* PC Kumanda arayüzü — sunucudan gelen /api/ui tanımına göre her şeyi çizer.
   Yeni bir sekme için JS'e dokunmaya gerek yok (modules/ altına Python dosyası ekle).
   Kendi widget'ı olan özellikler eklenti olarak yazılır (eklentiler/EKLENTI_REHBERI.md, window.PCK en altta).
   Yeni ikon gerekirse ICONS'a 24x24 SVG içeriği ekle. Eski Android Chrome'u için ?. ve ?? kullanma. */
(function () {
  "use strict";

  var ICONS = {
    bolt: '<path d="M13 2 4 14h7l-1 8 9-12h-7z"/>',
    gamepad: '<path d="M7 7h10a5 5 0 0 1 5 5v1.5a3.5 3.5 0 0 1-6.3 2.1L14.5 14h-5l-1.2 1.6A3.5 3.5 0 0 1 2 13.5V12a5 5 0 0 1 5-5z"/><path d="M7.5 9.5v4M5.5 11.5h4"/><path d="M15.5 10.5h.01M18 12.5h.01" stroke-width="2.6"/>',
    desktop: '<rect x="1.5" y="4" width="13" height="9"/><path d="M4.5 16h7"/><rect x="11" y="8" width="11.5" height="8.5" fill="#000"/><path d="M14 20h6M17 16.5V20"/>',
    music: '<path d="M9 18V5l11-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="17" cy="16" r="3"/>',
    monitor: '<rect x="2" y="4" width="20" height="13"/><path d="M8 21h8M12 17v4"/>',
    volume: '<path d="M11 5 6 9H2v6h4l5 4z"/><path d="M15.5 8.5a5 5 0 0 1 0 7M18.5 5.5a9.5 9.5 0 0 1 0 13"/>',
    headphones: '<path d="M3 18v-6a9 9 0 0 1 18 0v6"/><path d="M21 19a2 2 0 0 1-2 2h-2v-7h4zM3 19a2 2 0 0 0 2 2h2v-7H3z"/>',
    speaker: '<rect x="5" y="2" width="14" height="20" rx="1"/><circle cx="12" cy="14" r="4"/><path d="M12 6h.01" stroke-width="2.6"/>',
    mic: '<rect x="9" y="2" width="6" height="12" rx="3"/><path d="M5 11a7 7 0 0 0 14 0M12 18v4M8 22h8"/>',
    power: '<path d="M12 2v10"/><path d="M18.4 6.6a9 9 0 1 1-12.8 0"/>',
    battery: '<rect x="2" y="7" width="17" height="10" rx="1"/><path d="M22 10.5v3"/><path d="M5.5 10v4" stroke-width="2.6"/>',
    full: '<path d="M3 9V3h6M21 9V3h-6M3 15v6h6M21 15v6h-6"/>',
    play: '<path d="M7 4.5v15l12-7.5z" fill="currentColor"/>',
    pause: '<path d="M7 4h3.5v16H7zM13.5 4H17v16h-3.5z" fill="currentColor" stroke="none"/>',
    next: '<path d="M5 5l10 7-10 7z" fill="currentColor"/><path d="M18.5 5v14"/>',
    prev: '<path d="M19 5L9 12l10 7z" fill="currentColor"/><path d="M5.5 5v14"/>',
    map: '<path d="M9 4 3 6.5v13.5l6-2.5 6 2.5 6-2.5V4l-6 2.5z"/><path d="M9 4v13.5M15 6.5V20"/>',
    target: '<circle cx="12" cy="12" r="7"/><circle cx="12" cy="12" r="1.6" fill="currentColor"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3"/>',
    plus: '<path d="M12 5v14M5 12h14"/>',
    minus: '<path d="M5 12h14"/>',
    search: '<circle cx="10.5" cy="10.5" r="6.5"/><path d="M15.5 15.5 21 21"/>',
    flag: '<path d="M5 21V4"/><path d="M5 4h12l-2.5 4 2.5 4H5" fill="currentColor"/>',
    moon: '<path d="M20 14.5A8.5 8.5 0 1 1 9.5 4a7 7 0 0 0 10.5 10.5z"/>',
    layers: '<path d="M12 3 2 8l10 5 10-5z"/><path d="M2 13l10 5 10-5"/>',
    star: '<path d="M12 3l2.7 5.6 6.1.9-4.4 4.3 1 6.1L12 17l-5.4 2.9 1-6.1-4.4-4.3 6.1-.9z"/>',
    pin: '<path d="M12 21s-6-5.6-6-11a6 6 0 0 1 12 0c0 5.4-6 11-6 11z"/><circle cx="12" cy="10" r="2"/>',
    close: '<path d="M6 6l12 12M18 6L6 18"/>',
    back: '<path d="M15 5l-7 7 7 7"/>',
    check: '<path d="M4.5 12.5l5 5L20 7"/>',
    tune: '<path d="M3 6h11M18 6h3M3 12h4M11 12h10M3 18h13M20 18h1"/><circle cx="16" cy="6" r="2"/><circle cx="9" cy="12" r="2"/><circle cx="18" cy="18" r="2"/>',
    keyboard: '<rect x="2" y="6" width="20" height="12" rx="1"/><path d="M6 10h.01M9.5 10h.01M13 10h.01M16.5 10h.01M6 13.5h.01M18 10h.01M18 13.5h.01" stroke-width="2.4"/><path d="M8.5 14.5h7"/>',
    palette: '<path d="M12 3a9 9 0 1 0 0 18c1.1 0 1.6-.8 1.6-1.6 0-.5-.2-.8-.5-1.2-.3-.4-.5-.7-.5-1.2 0-.9.7-1.6 1.6-1.6H16a5 5 0 0 0 5-5C21 6.6 17 3 12 3z"/><path d="M7.5 11.5h.01M10 7.5h.01M14.5 7.5h.01M17 11h.01" stroke-width="2.6"/>',
    chip: '<rect x="6" y="6" width="12" height="12"/><rect x="9.5" y="9.5" width="5" height="5"/><path d="M9 2v4M15 2v4M9 18v4M15 18v4M2 9h4M2 15h4M18 9h4M18 15h4"/>',
    temp: '<path d="M14 14.8V4a2 2 0 0 0-4 0v10.8a4 4 0 1 0 4 0z"/><path d="M12 9v8"/>',
    refresh: '<path d="M21 12a9 9 0 1 1-2.6-6.4L21 8"/><path d="M21 3v5h-5"/>'
  };

  function icon(name) {
    return '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">' +
      (ICONS[name] || ICONS.bolt) + "</svg>";
  }

  var store = {
    get: function (k) { try { return localStorage.getItem(k); } catch (e) { return null; } },
    set: function (k, v) { try { localStorage.setItem(k, v); } catch (e) {} }
  };

  var pin = store.get("pin") || "";
  var currentTab = store.get("tab") || "";
  var ui = null, lastJson = "", busy = false, offline = false, pollTimer = null;
  var version = null, attempts = 0, lastOk = null, fails = 0;

  var $ = function (id) { return document.getElementById(id); };

  // ---------- masaüstü ----------
  // Arayüz telefona (yatay, ~780x360) göre çizildi. Büyük ekranda (yükseklik >= 560) aynı düzen CSS zoom ile
  // orantılı büyütülür; telefon bu eşiğe hiç ulaşmaz, mobil görünüm değişmez. DZ: harita fare koordinatları için.
  var DZ = 1;
  function deskScale() {
    var w = window.innerWidth, h = window.innerHeight, z = 1;
    if (h >= 560 && w >= 900) z = Math.max(1, Math.min(2.2, h / 640, w / 1150));
    z = Math.round(z * 100) / 100;
    DZ = z;
    document.documentElement.style.setProperty("--z", z);
    document.body.classList.toggle("desk", z > 1);
  }

  function el(tag, cls, text) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text != null) e.textContent = text;
    return e;
  }

  function iconEl(name) {
    var s = el("span", "ic");
    s.innerHTML = icon(name);
    return s;
  }

  // ---------- API ----------
  // PC uykudayken istekler reddedilmez, cevapsız asılı kalır. Zaman aşımı olmazsa "kapalı" ekranı
  // dakikalarca gelmez. Durum isteği 5 sn (sunucu önbellekten anında cevap verir), eylemler (Oyun modu ~20 sn sürebilir) 45 sn.
  function withTimeout(p, ms, ctrl) {
    return new Promise(function (resolve, reject) {
      var t = setTimeout(function () {
        if (ctrl) ctrl.abort();
        reject(new Error("zaman aşımı"));
      }, ms);
      p.then(function (v) { clearTimeout(t); resolve(v); },
             function (e) { clearTimeout(t); reject(e); });
    });
  }

  function api(path, body) {
    var ctrl = window.AbortController ? new AbortController() : null;
    return withTimeout(fetch(path, {
      method: body ? "POST" : "GET",
      headers: { "X-Pin": pin, "Content-Type": "application/json" },
      body: body ? JSON.stringify(body) : undefined,
      signal: ctrl ? ctrl.signal : undefined
    }), body ? 45000 : 5000, ctrl).then(function (r) {
      if (r.status === 401) {
        pin = window.prompt("PIN") || "";
        store.set("pin", pin);
        return api(path, body);
      }
      return r.json();
    });
  }

  var seq = 0, ticks = 0;

  function tabObj() {
    if (!ui) return null;
    return ui.tabs.filter(function (t) { return t.id === currentTab; })[0] || null;
  }

  // light=true: sadece açık sekmenin içeriği (hızlı yenilenen sekmeler için, durum etiketleri hariç)
  function load(force, light) {
    if (busy && !force) return Promise.resolve();
    var my = ++seq;
    var url = "/api/ui?tab=" + encodeURIComponent(currentTab || "") + (light ? "&light=1" : "");
    return api(url).then(function (data) {
      if (my !== seq) return;            // bu arada sekme değişti, daha yeni istek var
      var was = offline;
      offline = false;
      attempts = 0;
      fails = 0;
      lastOk = new Date();
      // Kur.bat ile güncellendiyse sunucu sürümü değişir -> sayfayı kendiliğinden yenile
      if (data.version) {
        if (version && version !== data.version) { location.reload(); return; }
        version = data.version;
      }
      if (was) setOffline(false);
      if ("theme" in data) applyTheme(data.theme);
      if ("score" in data) renderScore(data.score);
      if ("media" in data) renderMedia(data.media);
      if ("wallpaper" in data) renderWallpaper(data.wallpaper);
      if ("focus" in data) renderFocus(data.focus);
      fire("data", data);                // eklentiler: /api/ui cevabı (kendi @extra alanları dahil)
      if (data.light) {
        if (!ui) return;
        var nt = data.tabs[0];
        ui.tabs.forEach(function (t) { t.sections = t.id === nt.id ? nt.sections : null; });
      } else {
        ui = data;
      }
      if (data.tab) currentTab = data.tab;
      var t = tabObj();
      var j = JSON.stringify(t && t.sections) + JSON.stringify(ui.status) + currentTab;
      if (j === lastJson && !force && !was) return;
      lastJson = j;
      render();
    }).catch(function () {
      if (my !== seq) return;
      // Tek bir yavaş/kayıp cevap (Wi-Fi güç tasarrufu, PC yoğun) kapalı sayılmaz: üst üste 3 hata gerekir.
      fails++;
      if (fails < 3) return;
      attempts++;
      if (!offline) { offline = true; setOffline(true); applyTheme(null); renderScore(null); renderMedia(null); renderFocus(null); closeMedia(); }
      offSub();
      renderChips();
    });
  }

  function schedule() {
    clearTimeout(pollTimer);
    var t = tabObj();
    var fast = t && t.poll;
    var sec = offline ? 3 : fails ? 1.5 : (fast || (ui && ui.poll) || 8);   // hata sonrası hemen tekrar dene
    pollTimer = setTimeout(function () {
      ticks++;
      var light = !offline && !!fast && ticks % 4 !== 0;   // hızlı sekmede her 4 turda bir tam yenileme
      var p = document.hidden ? Promise.resolve() : load(false, light);
      p.then(schedule, schedule);
    }, sec * 1000);
  }

  function act(item, node) {
    if (busy || offline || !item.action) return;
    busy = true;
    node.classList.add("busy");
    document.body.classList.add("working");
    toast("Uygulanıyor…", 0);
    api("/api/action", { name: item.action, params: item.params || {} }).then(function (res) {
      toast(res.ok ? "Tamam" : "Hata · " + (res.error || "?"), 2200);
    }).catch(function () {
      toast("Bağlantı hatası", 2500);
    }).then(function () {
      busy = false;
      document.body.classList.remove("working");
      load(true);
    });
  }

  // ---------- çizim ----------
  function render() {
    if (!ui) return;
    var tabs = ui.tabs || [];
    if (!tabs.some(function (t) { return t.id === currentTab; })) currentTab = tabs.length ? tabs[0].id : "";
    renderRail(tabs);
    renderChips();
    var t = tabObj(), main = $("main");
    if (t && t.sections) renderMain(t.sections);
    // sekme değişirken eski içerik silinip "YÜKLENİYOR" yanıp sönmesin: yeni içerik gelene kadar soluklaşır
    else if (main.firstChild && !main.querySelector(".boot")) main.classList.add("leaving");
    else main.innerHTML = '<div class="boot">Yükleniyor…</div>';
  }

  var enterNext = true;     // sonraki çizim yumuşakça girsin (ilk açılış, sekme değişimi)

  function goTab(id) {
    if (id === currentTab) return;
    currentTab = id;
    store.set("tab", id);
    lastJson = "";
    enterNext = true;
    render();
    load(true).then(schedule);
  }

  function renderRail(tabs) {
    var rail = $("rail");
    rail.innerHTML = "";
    rail.className = "rail" + (tabs.length > 5 ? " dense" : "");   // 6+ sekme dikeyde sığsın
    tabs.forEach(function (t) {
      var b = el("button", t.id === currentTab ? "on" : "");
      b.title = t.title;                 // ray sadece ikon gösterir, ad ipucunda
      b.appendChild(iconEl(t.icon));
      b.appendChild(el("span", "", t.title));
      b.onclick = function () { goTab(t.id); };
      rail.appendChild(b);
    });
  }

  // ---------- odak adası (üst çubuk) ----------
  // Sunucu "focus" listesini önceliğe göre sıralı gönderir (core/registry.py @focus): oyun, çalan şarkı, kritik pil...
  // En öndeki büyük gösterilir, diğerleri yanında küçük rozet olur. Öncelik >= 30 ise body.focus: marka yazısı ve
  // ikincil durum etiketleri çekilir, ekran o duruma odaklanır.
  var FOCUS_AT = 30;
  var focusList = [], focusJson = "", focusKinds = {};

  function focusImg(it, cls) {
    if (!it.img) { var ic = iconEl(it.icon || "bolt"); ic.className = "ic " + cls; return ic; }
    var i = document.createElement("img");
    i.className = cls + (it.img_white ? " white" : "");
    i.alt = "";
    i.src = it.img;
    i.onerror = function () {
      var ic = iconEl(it.icon || "bolt");
      ic.className = "ic " + cls;
      if (this.parentNode) this.parentNode.replaceChild(ic, this);
    };
    return i;
  }

  function focusGo(it) {
    if (it.panel === "media") openMedia();
    else if (it.tab) goTab(it.tab);
  }

  function renderFocus(list) {
    list = list || [];
    var j = JSON.stringify(list);
    if (j === focusJson) return;
    var prevTop = focusList[0];
    focusJson = j;
    focusList = list;
    var kinds = {};
    list.forEach(function (it) { kinds[it.kind] = 1; });
    var kindsChanged = JSON.stringify(kinds) !== JSON.stringify(focusKinds);
    focusKinds = kinds;
    var top = list[0], b = $("focus");
    document.body.classList.toggle("focus", !!top && top.priority >= FOCUS_AT);
    if (kindsChanged) renderChips();
    refreshHero();
    if (!top) { b.className = "island"; return; }      // içerik kalsın: ada daralarak kaybolur
    b.innerHTML = "";
    // öndeki öğe değiştiyse içerik yumuşakça kayarak girsin (aynı öğe güncellenince titremesin)
    var swap = !prevTop || prevTop.kind !== top.kind || prevTop.title !== top.title;
    var fin = el("div", "fin" + (swap ? " swap" : ""));
    fin.appendChild(focusImg(top, "fi"));
    if (top.live && top.kind === "media") {
      var eq = el("span", "eq");
      eq.innerHTML = "<i></i><i></i><i></i>";
      fin.appendChild(eq);
    }
    var tx = el("span", "ftx");
    var tt = el("span", "ftt", top.title);
    if (top.lang) tt.lang = top.lang;
    tx.appendChild(tt);
    if (top.sub) tx.appendChild(el("span", "fsb", top.sub));
    fin.appendChild(tx);
    if (top.controls === "media") {
      var pp = el("button", "fpp");
      pp.innerHTML = icon(top.live ? "pause" : "play");
      pp.onclick = function (e) { e.stopPropagation(); mediaAct("media.toggle"); };
      fin.appendChild(pp);
    }
    list.slice(1).forEach(function (it) {          // ikincil öğeler: küçük, dokunulabilir rozetler
      var r = el("button", "fb" + (it.alert ? " alert" : "") + (it.live ? " live" : ""));
      r.appendChild(focusImg(it, "fbi"));
      if (it.badge) r.appendChild(el("span", "", it.badge));
      r.onclick = function (e) { e.stopPropagation(); focusGo(it); };
      fin.appendChild(r);
    });
    b.appendChild(fin);
    b.className = "island show k-" + top.kind + (top.priority >= FOCUS_AT ? " big" : "") +
      (top.alert ? " alert" : "") + (top.live ? " live" : "");
    b.onclick = function () { focusGo(top); };
    if (top.kind !== "media") closeAmbient();
  }

  function renderChips() {
    var box = $("chips");
    box.innerHTML = "";
    if (offline) { box.appendChild(el("span", "chip err", "Bağlantı yok")); return; }
    // durum metni ya da {text, value, lang, kind}: value ayrı span'da (örn. İngilizce oyun adı lang="en").
    // kind odak adasında zaten gösteriliyorsa etiket tekrar edilmez.
    ((ui && ui.status) || []).forEach(function (s) {
      if (typeof s === "string") { box.appendChild(el("span", "chip", s)); return; }
      if (s.kind && focusKinds[s.kind]) return;
      var c = el("span", "chip", s.text + " · ");
      var v = el("span", "", s.value);
      if (s.lang) v.lang = s.lang;
      c.appendChild(v);
      box.appendChild(c);
    });
  }

  function renderMain(sections) {
    var main = $("main");
    fire("render", currentTab);                           // eklentiler: açık sekme (örn. harita akışını kapatmak için)
    main.innerHTML = "";
    main.classList.remove("leaving");
    if (enterNext) {                                      // animasyonu baştan başlat (sınıfı kaldır, yeniden ekle)
      enterNext = false;
      main.classList.remove("enter");
      void main.offsetWidth;
      main.classList.add("enter");
    }
    litNext = {};
    // art arda gelen list'ler yan yana sütunlara, art arda gelen buttons'lar tek satıra dizilir.
    // "side": true olan bölüm bir öncekinin sağına yerleşir (örn. Modlar: ana kart + mod düğmeleri).
    var group = null, gtype = null, prev = null;
    sections.forEach(function (s) {
      var node = section(s);
      if (s.side && prev) {
        var duo = el("div", "duo");
        main.replaceChild(duo, prev);
        duo.appendChild(prev);
        duo.appendChild(node);
        prev = group = gtype = null;
        return;
      }
      prev = null;
      if (s.type === "list" || s.type === "buttons") {
        if (!group || gtype !== s.type) {
          group = el("div", s.type === "list" ? "cols" : "brow");
          gtype = s.type;
          main.appendChild(group);
        }
        group.appendChild(node);
      } else {
        group = null;
        gtype = null;
        main.appendChild(node);
        prev = node;
      }
    });
    litPrev = litNext;
    // ana kart ekrandayken üst çubuktaki ada aynı şeyi tekrar göstermesin
    document.body.classList.toggle("has-hero", !!main.querySelector(".hero"));
  }

  // Bir öğe yeni aktif olduysa (önceki çizimde değildi) vurgu rengi bir anda değil, yumuşakça dolsun.
  var litPrev = {}, litNext = {};
  function onCls(it) {
    if (!it.active) return "";
    var k = currentTab + "|" + it.title;
    litNext[k] = 1;
    return litPrev[k] ? " on" : " on lit";
  }

  // aktif öğesi olan grupta diğerleri geri çekilir (has-on): göz doğrudan seçili olana gider.
  // Birden çok öğe aktifse (örn. iki ekran da açık) bu bir seçim değil durumdur: "multi" ile daha sakin çizilir.
  function hasOn(items) {
    var n = items.filter(function (it) { return it.active; }).length;
    return n > 1 ? " has-on multi" : n ? " has-on" : "";
  }

  function section(s) {
    var wrap = el("section", "sec" + (s.fill ? " fill" : ""));
    if (s.title) wrap.appendChild(el("div", "st", s.title));
    var fn = WIDGETS[s.type] || WIDGETS.text;
    try {
      wrap.appendChild(fn(s));
    } catch (e) {                         // bozuk bir eklenti widget'ı sadece kendi bölümünü bozsun
      if (window.console) console.error(e);
      wrap.appendChild(el("div", "txt", "Bu bölüm çizilemedi (" + s.type + "): " + e.message));
    }
    return wrap;
  }

  function pad2(n) { return (n < 10 ? "0" : "") + n; }

  var WIDGETS = {
    tiles: function (s) {
      var items = s.items || [];
      // layout "stack": tek sütun, satır gibi geniş düğmeler (ikon + ad + seçiliyse tik)
      var stack = s.layout === "stack";
      var g = el("div", "tiles" + (stack ? " stack" : items.length > 4 ? " small" : "") + hasOn(items));
      items.forEach(function (it, i) {
        var b = el("button", "tile" + onCls(it));
        if (it.lang) b.lang = it.lang;
        if (it.img) {
          var im = document.createElement("img");
          im.className = "lg" + (it.img_white ? " white" : "");
          im.alt = "";
          im.src = it.img;
          (function (im, ic) {           // logo yüklenemezse ikona dön
            im.onerror = function () { if (im.parentNode) im.parentNode.replaceChild(iconEl(ic), im); };
          })(im, it.icon);
          b.appendChild(im);
        } else {
          b.appendChild(iconEl(it.icon));
        }
        b.appendChild(el("span", "idx", pad2(i + 1)));
        if (it.lines && it.lines.length) {
          var kv = el("span", "kv");
          it.lines.forEach(function (ln) {
            kv.appendChild(el("span", "k", ln[0]));
            kv.appendChild(el("span", "v", ln[1]));
          });
          b.appendChild(kv);
        }
        b.appendChild(el("span", "tt", it.title));
        if (it.sub) b.appendChild(el("span", "sb", it.sub));
        b.appendChild(el("span", "tag", "● AKTİF"));
        if (stack) {
          var ck = el("span", "ck");
          ck.innerHTML = icon("check");
          b.appendChild(ck);
        }
        b.onclick = function () { act(it, b); };
        g.appendChild(b);
      });
      return g;
    },
    list: function (s) {
      var box = el("div", "list" + hasOn(s.items || []));
      (s.items || []).forEach(function (it) {
        var b = el("button", "row" + onCls(it));
        b.appendChild(iconEl(it.icon));
        var tx = el("span", "tx");
        tx.appendChild(el("div", "tt", it.title));
        if (it.sub) tx.appendChild(el("div", "sb", it.sub));
        b.appendChild(tx);
        b.appendChild(el("span", "mk"));
        b.onclick = function () { act(it, b); };
        box.appendChild(b);
      });
      return box;
    },
    buttons: function (s) {
      var box = el("div", "btns");
      (s.items || []).forEach(function (it) {
        // "on": true/false verilirse düğme aç/kapa anahtarı olarak çizilir (yazıda "· Açık" yazmaya gerek yok)
        var tg = it.on === true || it.on === false;
        var b = el("button", "btn" + (tg ? " tg" + (it.on ? " on" : "") : ""));
        if (it.icon) b.appendChild(iconEl(it.icon));
        b.appendChild(el("span", "", it.title));
        if (tg) b.appendChild(el("i", "sw"));
        b.onclick = function () { act(it, b); };
        box.appendChild(b);
      });
      return box;
    },
    stats: function (s) {
      var g = el("div", "stats" + (s.compact ? " mini" : ""));
      (s.items || []).forEach(function (it) {
        var c = el("div", "stat" + (it.hot ? " hot" : ""));
        c.appendChild(el("div", "lb", it.label));
        var v = el("div", "vl");
        v.appendChild(el("span", "n", it.value));
        if (it.unit) v.appendChild(el("span", "u", it.unit));
        c.appendChild(v);
        var bar = el("div", "bar" + (it.pct == null ? " none" : ""));
        var f = el("div", "f");
        f.style.width = (it.pct == null ? 0 : Math.max(0, Math.min(100, it.pct))) + "%";
        bar.appendChild(f);
        c.appendChild(bar);
        if (it.sub) c.appendChild(el("div", "sb", it.sub));
        g.appendChild(c);
      });
      return g;
    },
    // ana kart: o an en önemli durum (focus listesinin başı) büyük; hiçbir şey yoksa sakin saat + tarih.
    // Odak değişince sayfa yeniden çizilmeden kendini günceller (refreshHero). s.mode: boşta altta yazan mod adı.
    hero: function (s) {
      var box = el("div", "hero");
      box._spec = s;
      drawHero(box);
      return box;
    },
    text: function (s) {
      return el("div", "txt", s.text || "");
    }
  };

  // ---------- oyun teması ----------
  // Sunucu /api/ui cevabında "theme" gönderir (modules/games.py). null = varsayılan sade tema.
  // Sade tema: oyun sadece vurgu rengini değiştirir, zemin ve yazı rengi hep aynı koyu kalır (oyunun bg/fg'si kullanılmaz).
  var BG = "#0b0b0c", FG = "#f2f2f2";
  var DEFAULT_THEME = { id: "", accent: FG, accent2: FG, fx: "" };
  var themeId = null;

  function hexRgb(h) {
    h = (h || "#fff").replace("#", "");
    if (h.length === 3) h = h[0] + h[0] + h[1] + h[1] + h[2] + h[2];
    var n = parseInt(h, 16);
    return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
  }

  function luminance(h) {
    var c = hexRgb(h).map(function (v) {
      v /= 255;
      return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4);
    });
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2];
  }

  function applyTheme(t) {
    t = t || DEFAULT_THEME;
    var id = t.id || "";
    if (id === themeId) return;
    themeId = id;
    var r = document.documentElement.style;
    r.setProperty("--ac", t.accent || FG);
    r.setProperty("--ac2", t.accent2 || t.accent || FG);
    // vurgu zemininde okunur yazı: açık renkte koyu, koyu renkte beyaz
    var L = luminance(t.accent || FG);
    r.setProperty("--on-ac", (L + 0.05) / 0.05 >= 1.05 / (L + 0.05) ? BG : "#ffffff");
    var cls = document.body.className.replace(/\bfx-\S+/g, "").replace(/\bgame\b/g, "").replace(/\s+/g, " ").trim();
    // body.game: oyun teması aktif -> duvar kağıdı gizlenir, oyunun zemini görünür
    document.body.className = cls + (t.fx ? " fx-" + t.fx : "") + (id ? " game" : "");
    // oyun logosu: arka planda silik filigran (logo_white = koyu logoyu beyaza çevir)
    var wm = $("wm"), wi = $("wmimg");
    if (t.logo) {
      wi.onerror = function () { wm.className = "wm"; };
      wi.src = t.logo;
      wm.className = "wm on" + (t.logo_white ? " white" : "");
    } else {
      wm.className = "wm";
    }
    var meta = document.querySelector('meta[name="theme-color"]');
    if (meta) meta.setAttribute("content", BG);
  }

  // ---------- masaüstü duvar kağıdı (oyun teması yokken arka plan) ----------
  var wpUrl = "";

  function renderWallpaper(w) {
    var url = w && w.url;
    if (url === wpUrl) return;
    wpUrl = url || "";
    var box = $("wp");
    if (!url) {
      document.body.classList.remove("has-wp");
      box.style.backgroundImage = "";
      return;
    }
    var img = new Image();               // önce yükle, sonra yumuşakça göster (yarım resim görünmesin)
    img.onload = function () {
      box.style.backgroundImage = 'url("' + url + '")';
      box.style.setProperty("--dim", w.dim == null ? 0.55 : w.dim);
      document.body.classList.add("has-wp");
    };
    img.src = url;
  }

  // ---------- maç skoru (sağ üst) + maç listesi ----------
  // Sunucu "score" alanında öne çıkan maçları gönderir (modules/football.py). Birden çok maç varsa
  // 6 sn'de bir sırayla gösterilir. Dokununca tüm maçların listesi açılır.
  var scoreData = null, scoreIdx = 0, scoreJson = "";

  function teamLogo(url) {
    var i = document.createElement("img");
    i.className = "tl";
    i.alt = "";
    i.onerror = function () { this.style.visibility = "hidden"; };
    if (url) i.src = url;
    return i;
  }

  function renderScore(sc) {
    var j = JSON.stringify(sc);
    if (j === scoreJson) return;
    scoreJson = j;
    scoreData = sc;
    var b = $("score");
    if (!sc || !sc.items || !sc.items.length) {
      b.style.display = "none";
      document.body.classList.remove("has-score");
      return;
    }
    b.style.display = "";
    document.body.classList.add("has-score");     // dar ekranda ikincil etiketler gizlenir
    if (scoreIdx >= sc.items.length) scoreIdx = 0;
    drawScore();
  }

  function drawScore() {
    var b = $("score"), m = scoreData.items[scoreIdx];
    b.innerHTML = "";
    b.className = "score" + (m.live ? " live" : "") + (m.state === "pre" ? " pre" : "");
    b.appendChild(el("span", "lg", m.lg));
    b.appendChild(teamLogo(m.h[2]));
    b.appendChild(el("span", "ab", m.h[0]));
    b.appendChild(el("span", "sc", m.state === "pre" ? "–" : m.h[1] + "–" + m.a[1]));
    b.appendChild(el("span", "ab", m.a[0]));
    b.appendChild(teamLogo(m.a[2]));
    b.appendChild(el("span", "ck", m.clock));
  }

  setInterval(function () {
    if (scoreData && scoreData.items && scoreData.items.length > 1) {
      scoreIdx = (scoreIdx + 1) % scoreData.items.length;
      drawScore();
    }
  }, 6000);

  var matchTimer = null;

  function openMatches() {
    var o = $("match");
    o.className = "match show";
    o.innerHTML = '<div class="mh"><span>Maçlar</span><button class="ib" id="mclose"></button></div>' +
      '<div class="mb" id="mbody"><div class="boot">Yükleniyor…</div></div>';
    $("mclose").innerHTML = icon("close");
    $("mclose").onclick = closeMatches;
    loadMatches();
    clearInterval(matchTimer);
    matchTimer = setInterval(loadMatches, 30000);
  }

  function closeMatches() {
    clearInterval(matchTimer);
    $("match").className = "match";
  }

  function loadMatches() {
    api("/api/action", { name: "football.list" }).then(function (res) {
      var body = $("mbody");
      if (!body) return;
      var data = (res && res.result) || { leagues: [] };
      body.innerHTML = "";
      data.leagues.forEach(function (lg) {
        var col = el("div", "mcol");
        col.appendChild(el("div", "st", lg.name));
        if (!lg.matches.length) col.appendChild(el("div", "txt", "Yakın tarihte maç yok"));
        var lastDay = null;
        lg.matches.forEach(function (m) {
          if (m.day !== lastDay) { col.appendChild(el("div", "mday", m.day)); lastDay = m.day; }
          var r = el("div", "mrow" + (m.live ? " live" : "") + (m.fav ? " fav" : ""));
          r.appendChild(el("span", "mck", m.state === "pre" ? m.clock.replace(/^(Yarın|Dün|\S+) /, "") : m.clock));
          var h = el("span", "mt h");
          h.appendChild(el("span", "mn", m.home.n));
          h.appendChild(teamLogo(m.home.l));
          r.appendChild(h);
          r.appendChild(el("span", "msc", m.state === "pre" ? "–" : m.home.s + " – " + m.away.s));
          var a = el("span", "mt a");
          a.appendChild(teamLogo(m.away.l));
          a.appendChild(el("span", "mn", m.away.n));
          r.appendChild(a);
          col.appendChild(r);
        });
        body.appendChild(col);
      });
      if (data.error) body.appendChild(el("div", "txt", "Skor servisine ulaşılamadı: " + data.error));
    }).catch(function () {});
  }

  // ---------- şu an çalan medya + medya paneli ----------
  // Sunucu "media" alanında {title, artist, app, playing, pos, dur, cover} gönderir (modules/media.py).
  // Üst çubukta odak adası gösterir (renderFocus); burada sadece durum ve panel tutulur.
  var media = null, mediaKey = "", mediaAt = 0;

  function fmtTime(sec) {
    sec = Math.max(0, Math.floor(sec || 0));
    var m = Math.floor(sec / 60), s = sec % 60;
    return m + ":" + (s < 10 ? "0" : "") + s;
  }

  function mediaPos() {
    if (!media) return 0;
    var p = media.pos + (media.playing ? (Date.now() - mediaAt) / 1000 : 0);
    return media.dur ? Math.min(p, media.dur) : p;
  }

  function coverEl(cls) {
    if (media && media.cover) {
      var i = document.createElement("img");
      i.className = cls;
      i.alt = "";
      i.src = media.cover;
      i.onerror = function () { this.parentNode && this.parentNode.replaceChild(iconEl("music"), this); };
      return i;
    }
    var ic = iconEl("music");
    ic.className = "ic " + cls;
    return ic;
  }

  function renderMedia(md) {
    media = md;
    mediaAt = Date.now();
    if (!md) { closeMedia(); mediaKey = ""; return; }
    var key = [md.title, md.artist, md.playing, md.cover].join("|");
    if (key !== mediaKey) {                 // sadece şarkı/durum değişince yeniden çiz (titreme olmasın)
      mediaKey = key;
      if ($("mpanel").className.indexOf("show") >= 0) drawMediaPanel();
    }
    if (!md.playing) closeAmbient();
  }

  // ambient: dokunulmadan IDLE_MS geçtiyse ve öndeki odak çalan şarkıysa medya paneli kendiliğinden açılır
  // (masadaki telefon "şu an çalıyor" ekranına döner). Oyun ya da kritik pil öndeyse açılmaz.
  function openMedia(ambient) {
    if (!media) return;
    $("mpanel").className = "mpanel show" + (ambient ? " ambient" : "");
    drawMediaPanel();
  }

  function closeMedia() {
    $("mpanel").className = "mpanel";
  }

  function closeAmbient() {
    if ($("mpanel").className.indexOf("ambient") >= 0) closeMedia();
  }

  var IDLE_MS = 90000, lastInput = Date.now();
  function anyOpen() {
    return ["mpanel", "match", "pwpanel"].some(function (id) { return $(id).className.indexOf("show") >= 0; });
  }
  ["touchstart", "mousedown", "keydown", "wheel"].forEach(function (ev) {
    document.addEventListener(ev, function () { lastInput = Date.now(); }, true);
  });
  setInterval(function () {
    var top = focusList[0];
    if (offline || busy || document.hidden || Date.now() - lastInput < IDLE_MS) return;
    if (top && top.kind === "media" && top.live && media && media.playing && !anyOpen()) openMedia(true);
  }, 5000);

  function mediaAct(name) {
    api("/api/action", { name: name }).then(function () { load(true); });
  }

  function drawMediaPanel() {
    var o = $("mpanel");
    if (!media) { closeMedia(); return; }
    o.innerHTML = "";
    var x = el("button", "ib mpx");
    x.innerHTML = icon("close");
    x.onclick = closeMedia;
    o.appendChild(x);
    var row = el("div", "mprow");
    var cw = el("div", "mpcover");
    cw.appendChild(coverEl("big"));
    row.appendChild(cw);
    var info = el("div", "mpinfo");
    info.appendChild(el("div", "mpapp", (media.playing ? "Çalıyor" : "Duraklatıldı") + " · " + media.app));
    info.appendChild(el("div", "mptitle", media.title));
    info.appendChild(el("div", "mpartist", media.artist || ""));
    var bar = el("div", "mpbar");
    var f = el("div", "f");
    f.id = "mpfill";
    bar.appendChild(f);
    info.appendChild(bar);
    var tm = el("div", "mptime");
    tm.appendChild(el("span", "", ""));
    tm.appendChild(el("span", "", ""));
    tm.id = "mptime";
    info.appendChild(tm);
    var ctl = el("div", "mpctl");
    [["prev", "media.prev"], [media.playing ? "pause" : "play", "media.toggle"], ["next", "media.next"]].forEach(function (c, i) {
      var bt = el("button", "mpb" + (i === 1 ? " pp" : ""));
      bt.innerHTML = icon(c[0]);
      bt.onclick = function () { mediaAct(c[1]); };
      ctl.appendChild(bt);
    });
    info.appendChild(ctl);
    row.appendChild(info);
    o.appendChild(row);
    tickMedia();
  }

  // ---------- ana kart (hero) ----------
  var MONTHS = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"];
  var DAYS = ["Pazar", "Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi"];

  function heroDate(d) { return d.getDate() + " " + MONTHS[d.getMonth()] + " " + DAYS[d.getDay()]; }

  function refreshHero() {
    var list = document.querySelectorAll(".hero");
    for (var i = 0; i < list.length; i++) drawHero(list[i]);
  }

  function drawHero(box) {
    var s = box._spec || {}, top = focusList[0];
    var id = top ? top.kind + "|" + top.title : "idle";
    var key = top ? [id, top.sub, top.img, top.live, top.alert].join("|") : "idle";
    if (box._key === key) return;            // değişmediyse dokunma (ilerleme çubuğu tickMedia ile akar)
    var swap = box._key !== undefined && box._id !== id;
    box._key = key;
    box._id = id;
    box.innerHTML = "";
    box.className = "hero " + (top ? "k-" + top.kind + (top.alert ? " alert" : "") : "idle");
    var c = el("div", "hin" + (swap ? " swap" : ""));
    if (!top) heroIdle(c, s);
    else if (top.kind === "media" && media) heroMedia(c, top);
    else heroItem(c, top);
    box.appendChild(c);
    box.onclick = top && top.kind !== "media" ? function () { focusGo(top); } : null;
    var rest = focusList.slice(1);
    if (rest.length) {                        // diğer durumlar: sağ üstte küçük rozetler
      var bs = el("div", "hbadges");
      rest.forEach(function (it) {
        var r = el("button", "hbg" + (it.alert ? " alert" : ""));
        r.appendChild(focusImg(it, "fbi"));
        if (it.badge) r.appendChild(el("span", "", it.badge));
        r.onclick = function (e) { e.stopPropagation(); focusGo(it); };
        bs.appendChild(r);
      });
      box.appendChild(bs);
    }
  }

  function heroIdle(c, s) {
    var d = new Date();
    c.appendChild(el("div", "hclock", pad2(d.getHours()) + ":" + pad2(d.getMinutes())));
    c.appendChild(el("div", "hdate", heroDate(d)));
    if (s.mode) c.appendChild(el("div", "hmode", s.mode));
  }

  function heroMedia(c, top) {
    var row = el("div", "hrow");
    var cv = el("div", "hcover");
    cv.appendChild(coverEl("hcv"));
    row.appendChild(cv);
    var tx = el("div", "htx");
    tx.appendChild(el("div", "htt", media.title));
    if (top.sub) tx.appendChild(el("div", "hsb", top.sub));
    row.appendChild(tx);
    row.onclick = function () { openMedia(); };
    c.appendChild(row);
    var bar = el("div", "hbar");
    bar.appendChild(el("div", "f"));
    c.appendChild(bar);
    var ctl = el("div", "hctl");
    [["prev", "media.prev"], [media.playing ? "pause" : "play", "media.toggle"], ["next", "media.next"]].forEach(function (x, i) {
      var b = el("button", "hb" + (i === 1 ? " pp" : ""));
      b.innerHTML = icon(x[0]);
      b.onclick = function (e) { e.stopPropagation(); mediaAct(x[1]); };
      ctl.appendChild(b);
    });
    c.appendChild(ctl);
    tickMedia();
  }

  function heroItem(c, top) {
    c.appendChild(focusImg(top, top.img ? "hlogo" : "hicon"));
    var tt = el("div", "htt big", top.title);
    if (top.lang) tt.lang = top.lang;
    c.appendChild(tt);
    if (top.sub) c.appendChild(el("div", "hsb", top.sub));
  }

  function tickMedia() {
    var f = $("mpfill"), tm = $("mptime"), hb = document.querySelectorAll(".hero .hbar .f");
    if (!media || (!f && !hb.length)) return;
    var p = mediaPos(), w = (media.dur ? Math.min(100, p * 100 / media.dur) : 0) + "%";
    for (var i = 0; i < hb.length; i++) hb[i].style.width = w;
    if (!f) return;
    f.style.width = w;
    tm.firstChild.textContent = fmtTime(p);
    tm.lastChild.textContent = media.dur ? fmtTime(media.dur) : "";
  }
  setInterval(tickMedia, 1000);

  // ---------- PC kapalı ekranı: göz kırpan anime gözler ----------
  function eye(mirror, id) {
    // tek göz, yerel koordinatlar ~0..195 x 0..140; mirror=true soldaki göz (dış köşe solda)
    var clip = "ec" + id;
    // parıltılar iki gözde de izleyicinin sol üstünde dursun (aynalanan gözde x'i iris merkezine göre çevir)
    var hx = function (x) { return mirror ? 188 - x : x; };
    return '<g transform="' + (mirror ? "translate(204,26) scale(-1,1)" : "translate(236,26)") + '">' +
      '<path class="brow" d="M36 6 C78 -8 128 -6 162 12"/>' +
      '<g class="lid' + (mirror ? " m" : "") + '">' +
        '<clipPath id="' + clip + '"><path d="M10 72 C42 26 140 18 172 56 C150 100 52 116 10 72Z"/></clipPath>' +
        '<path class="sclera" d="M10 72 C42 26 140 18 172 56 C150 100 52 116 10 72Z"/>' +
        '<g clip-path="url(#' + clip + ')">' +
          '<g class="look' + (mirror ? " m" : "") + '">' +
            '<ellipse class="iris" cx="94" cy="72" rx="37" ry="45"/>' +
            '<ellipse class="ring" cx="94" cy="74" rx="25" ry="31"/>' +
            '<ellipse class="pupil" cx="94" cy="76" rx="13" ry="19"/>' +
            '<ellipse class="hl" cx="' + hx(78) + '" cy="52" rx="11" ry="14"/>' +
            '<circle class="hl" cx="' + hx(111) + '" cy="94" r="5"/>' +
            '<circle class="hl s" cx="' + hx(104) + '" cy="49" r="3"/>' +
          '</g>' +
          '<path class="shade" d="M0 0 H200 V40 C150 22 60 28 0 70Z"/>' +
        '</g>' +
        '<path class="upper" d="M5 75 C38 22 140 12 176 52"/>' +
        '<path class="lash" d="M168 44 L190 30 M174 52 L196 46"/>' +
        '<path class="lower" d="M64 110 C96 114 132 104 152 90"/>' +
      '</g></g>';
  }

  function buildOff() {
    var o = $("off");
    o.innerHTML =
      '<svg class="eyes" viewBox="0 0 440 170" fill="none">' + eye(true, 1) + eye(false, 2) +
      '<defs><linearGradient id="irisG" x1="0" y1="0" x2="0" y2="1">' +
      '<stop offset="0" stop-color="#1c1c1c"/><stop offset=".55" stop-color="#5a5a5a"/><stop offset="1" stop-color="#d8d8d8"/>' +
      '</linearGradient></defs></svg>' +
      '<div class="off-t">Bilgisayar kapalı ya da uykuda</div>' +
      '<div class="off-s" id="offSub"></div>';
  }

  function offSub() {
    var e = $("offSub");
    if (!e) return;
    e.textContent = "Açılınca kendiliğinden bağlanacak · deneme " + attempts +
      (lastOk ? " · son bağlantı " + pad2(lastOk.getHours()) + ":" + pad2(lastOk.getMinutes()) : "");
  }

  function setOffline(on) {
    var o = $("off");
    if (on) {
      o.classList.remove("wake");
      document.body.classList.add("offline");
      offSub();
    } else {
      o.classList.add("wake");                 // gözler kocaman açılır, sonra kaybolur
      setTimeout(function () {
        if (!offline) document.body.classList.remove("offline");
        o.classList.remove("wake");
      }, 1100);
    }
  }

  // ---------- küçük şeyler ----------
  var toastTimer = null;
  function toast(text, ms) {
    var t = $("toast");
    t.textContent = text;
    t.className = "toast show";
    clearTimeout(toastTimer);
    if (ms) toastTimer = setTimeout(function () { t.className = "toast"; }, ms);
  }

  function tick() {
    var d = new Date();
    $("clock").textContent = pad2(d.getHours()) + ":" + pad2(d.getMinutes());
    var hc = document.querySelectorAll(".hero .hclock"), hd = document.querySelectorAll(".hero .hdate");
    for (var i = 0; i < hc.length; i++) hc[i].textContent = $("clock").textContent;
    for (i = 0; i < hd.length; i++) hd[i].textContent = heroDate(d);
  }

  // ---------- güç (modules/power.py) ----------
  // Yanlışlıkla kapanmasın: düğme 1,2 sn basılı tutulunca çalışır, bırakılırsa iptal.
  var POWER = [
    ["power.shutdown", "Kapat", "Bilgisayar kapatılıyor"],
    ["power.restart", "Yeniden başlat", "Yeniden başlatılıyor"],
    ["power.sleep", "Uyku", "Uykuya alınıyor"]
  ];

  function openPower() {
    var o = $("pwpanel");
    o.innerHTML = "";
    var x = el("button", "ib mpx");
    x.innerHTML = icon("close");
    x.onclick = closePower;
    o.appendChild(x);
    var box = el("div", "pwbox");
    box.appendChild(el("div", "pwh", "Güç"));
    POWER.forEach(function (p, i) {
      var b = el("button", "pwb" + (i === 0 ? " red" : ""));
      b.appendChild(el("i", "pwfill"));
      var lb = el("span", "pwl");
      lb.innerHTML = icon(i === 0 ? "power" : i === 1 ? "refresh" : "moon");
      lb.appendChild(document.createTextNode(p[1]));
      b.appendChild(lb);
      var t = null;
      function down(e) {
        e.preventDefault();
        b.className = b.className.replace(" hold", "") + " hold";
        clearTimeout(t);
        t = setTimeout(function () {
          t = null;
          closePower();
          toast(p[2], 4000);
          api("/api/action", { name: p[0] }).catch(function () {});
        }, 1200);
      }
      function up() {
        if (t) { clearTimeout(t); t = null; }
        b.className = b.className.replace(" hold", "");
      }
      b.addEventListener("touchstart", down, { passive: false });
      b.addEventListener("touchend", up);
      b.addEventListener("touchcancel", up);
      b.addEventListener("mousedown", down);
      b.addEventListener("mouseup", up);
      b.addEventListener("mouseleave", up);
      b.addEventListener("contextmenu", function (e) { e.preventDefault(); });
      box.appendChild(b);
    });
    box.appendChild(el("div", "pwn", "Basılı tut"));
    o.appendChild(box);
    o.className = "pwpanel show";
  }

  function closePower() { $("pwpanel").className = "pwpanel"; }

  function fullscreen() {
    var d = document, e = d.documentElement;
    if (d.fullscreenElement || d.webkitFullscreenElement) {
      (d.exitFullscreen || d.webkitExitFullscreen).call(d);
    } else {
      var f = e.requestFullscreen || e.webkitRequestFullscreen;
      if (f) f.call(e);
    }
  }

  buildOff();
  $("score").onclick = openMatches;
  $("btnFull").innerHTML = icon("full");
  $("btnRefresh").innerHTML = icon("refresh");
  $("btnFull").onclick = fullscreen;
  $("btnPower").innerHTML = icon("power");
  $("btnPower").onclick = openPower;
  deskScale();
  window.addEventListener("resize", function () { deskScale(); fire("resize"); });
  // masaüstü klavye: 1-9 sekmeler, Esc paneli kapatır, F tam ekran, R yenile, +/- haritada zum
  document.addEventListener("keydown", function (e) {
    var t = e.target;
    if (e.ctrlKey || e.altKey || e.metaKey || (t && (t.tagName === "INPUT" || t.tagName === "TEXTAREA"))) return;
    var k = e.key;
    if (k === "Escape") {
      closePanels();
    } else if (/^[1-9]$/.test(k) && ui && ui.tabs && ui.tabs[+k - 1]) {
      goTab(ui.tabs[+k - 1].id);
    } else if (k === "f" || k === "F") {
      fullscreen();
    } else if (k === "r" || k === "R") {
      load(true);
    } else if (!fire("key", k, currentTab)) {   // eklentiler (örn. haritada +/- zum)
      return;
    }
    e.preventDefault();
  });
  function closePanels() {
    closePower(); closeMedia(); closeMatches();
    fire("close");
  }

  // PC klavyesindeki genel kısayollar (modules/hotkeys.py): {tab: sıra} ya da {step: ±1}. Bağlantı koparsa
  // EventSource kendisi yeniden bağlanır.
  function navStream() {
    if (!window.EventSource) return;
    var es = new EventSource("/nav/stream");
    es.onmessage = function (e) {
      var d;
      try { d = JSON.parse(e.data); } catch (x) { return; }
      if (!d.n || offline || !ui || !ui.tabs || !ui.tabs.length) return;
      var tabs = ui.tabs, i = -1;
      tabs.forEach(function (t, j) { if (t.id === currentTab) i = j; });
      var to = d.step ? tabs[(i + d.step + tabs.length) % tabs.length] : tabs[d.tab];
      if (!to) return;
      closePanels();
      goTab(to.id);
    };
  }

  $("btnRefresh").onclick = function () { load(true); };
  document.addEventListener("visibilitychange", function () { if (!document.hidden) load(false); });
  tick();
  setInterval(tick, 5000);
  // ---------- eklenti API'si (eklentiler/EKLENTI_REHBERI.md) ----------
  // Eklenti JS'leri index.html'de app.js'ten hemen sonra yüklenir (core/server.py ekler) ve sadece window.PCK'yi kullanır.
  // Olaylar: "data"(/api/ui cevabı) · "render"(sekme id) her çizimde · "resize" · "close" (Esc, panelleri kapat)
  //         · "key"(tuş, sekme id) → true döndüren işlemiş sayılır
  var HOOKS = {};
  function fire(name, a, b) {
    var done = false;
    (HOOKS[name] || []).forEach(function (fn) {
      try { if (fn(a, b)) done = true; } catch (e) { if (window.console) console.error(e); }
    });
    return done;
  }
  window.PCK = {
    widget: function (type, fn) { WIDGETS[type] = fn; },
    icons: function (o) { for (var k in o) ICONS[k] = o[k]; },
    on: function (name, fn) { (HOOKS[name] = HOOKS[name] || []).push(fn); },
    el: el, icon: icon, iconEl: iconEl, api: api, toast: toast, store: store,
    zoom: function () { return DZ; },                 // masaüstü CSS zoom: fare koordinatlarını buna böl
    tab: function () { return currentTab; },
    goTab: function (id) { goTab(id); },
    refresh: function () { return load(true); }
  };

  // ilk yükleme eklenti JS'leri çalıştıktan sonra (widget'ları kayıtlı olsun)
  function boot() {
    navStream();
    load(true).then(schedule);
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();
})();
