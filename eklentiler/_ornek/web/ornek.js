/* Örnek eklentinin arayüzü: "ornek_sayac" widget'ı ve "ornek" ikonu. Sadece window.PCK kullanır.
   Eski Android Chrome: ?. ?? replaceAll, sınıf alanları, flex gap yok; var + function kullan. */
(function () {
  "use strict";
  var P = window.PCK;
  if (!P) return;

  P.icons({ ornek: '<circle cx="12" cy="12" r="8"/><path d="M12 8v8M8 12h8"/>' });

  // s = sunucudan gelen section: {type: "ornek_sayac", fill, data: {sayi, adim}}. Bir DOM öğesi döndür.
  P.widget("ornek_sayac", function (s) {
    var d = s.data || {};
    var box = P.el("div", "ornek-kutu");
    box.appendChild(P.el("div", "ornek-sayi", String(d.sayi)));
    var b = P.el("button", "ornek-btn");
    b.appendChild(P.iconEl("plus"));
    b.appendChild(P.el("span", "", "+" + d.adim + " (JS'ten)"));
    b.onclick = function () {
      P.api("/api/action", { name: "ornek.artir" }).then(function (r) {
        P.toast(r.ok ? "SAYI " + r.result : "HATA", 1200);
        P.refresh();
      });
    };
    box.appendChild(b);
    return box;
  });
})();
