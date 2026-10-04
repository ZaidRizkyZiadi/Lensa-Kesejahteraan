/* zz-mobile.js : pelengkap tampilan ponsel/tablet (lebar < 1024px).
   Dimuat setelah main.js dan zz-extra.js. Tidak mengubah perilaku desktop.
   Perubahan: bagian 5 ditulis ulang. Grafik BELANJA (treemap/sunburst) dan PETA (choropleth/simbol)
   tidak lagi memakai colorbar Plotly di ponsel (colorbar mendesak area plot jadi strip kecil).
   Gantinya: margin dikunci (autoexpand:false) dan legenda warna berupa elemen HTML (.p3m-leg). */
(function () {
  "use strict";
  var $ = function (i) { return document.getElementById(i); };
  var mq = window.matchMedia("(max-width:1023px)");
  var narrow = function () { return mq.matches; };

  /* ---------- 1. skala menu utama mengikuti layar ---------- */
  function setMenuScale() {
    var w = window.innerWidth, h = window.innerHeight;
    // lebar menu asli kira-kira 720px dan tingginya 430px (sebelum diskalakan)
    var s = Math.max(0.35, Math.min(0.95, w / 720, (h * 0.78) / 430));
    document.documentElement.style.setProperty("--p3-ms", s.toFixed(3));
  }
  setMenuScale();
  window.addEventListener("resize", setMenuScale);
  window.addEventListener("orientationchange", function () { setTimeout(setMenuScale, 250); });

  /* ---------- 2. main.js tidak memulai pengalaman pada layar < 1024px: mulai di sini ---------- */
  try {
    if (narrow() && typeof enterExperience === "function" && typeof isStarted !== "undefined" && !isStarted) {
      enterExperience();
    }
  } catch (e) { /* bila gagal, menu tetap muncul lewat hero (zz-extra.js) */ }

  /* ---------- 3. hero: petunjuk dan ketuk ---------- */
  var cue = document.querySelector(".hero-cue-text");
  if (cue && (narrow() || window.matchMedia("(pointer:coarse)").matches)) {
    cue.textContent = "Geser ke atas atau ketuk untuk memilih menu";
  }
  var hero = $("intro-hero"), cueBtn = $("hero-cue");
  if (hero && cueBtn) {
    hero.addEventListener("click", function (e) {
      if (narrow() && e.target !== cueBtn && !cueBtn.contains(e.target)) cueBtn.click();
    });
  }

  /* ---------- 4. tombol Kembali bawaan perangkat (Android) menutup halaman, bukan keluar situs ---------- */
  var BACK = { "project-page": "slink-back-btn", "skill-page": "skill-back-btn", "about-page": "about-back-btn", "contact-page": "contact-back-btn" };
  var openId = null;
  Object.keys(BACK).forEach(function (id) {
    var el = $(id);
    if (!el) return;
    new MutationObserver(function () {
      if (!narrow()) return;
      var c = el.classList, active = c.contains("active"), moving = c.contains("circle-transitioning");
      if (active && openId !== id) {
        openId = id;
        try { history.pushState({ p3: id }, ""); } catch (e) {}
      } else if (!active && !moving && openId === id) {
        openId = null;
        try { if (history.state && history.state.p3) history.back(); } catch (e) {}   // buang entri riwayat yang kita tambahkan
      }
    }).observe(el, { attributes: true, attributeFilter: ["class"] });
  });
  window.addEventListener("popstate", function () {
    if (!openId) return;
    var b = $(BACK[openId]);
    openId = null;
    if (b) b.click();
  });

  /* ---------- 5. grafik Plotly di layar sempit ---------- */
  var fmt = function (v) { return (Math.round(v * 10) / 10).toString().replace(".", ","); };
  var esc = function (s) {
    return String(s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; });
  };

  // pecah teks panjang menjadi beberapa baris (<br>) agar catatan sumber tidak terpotong di layar sempit
  function wrapText(t, n) {
    var words = String(t).replace(/<br>/g, " ").split(/\s+/), lines = [], cur = "";
    words.forEach(function (w) {
      if (cur && (cur + " " + w).length > n) { lines.push(cur); cur = w; }
      else { cur = cur ? cur + " " + w : w; }
    });
    if (cur) lines.push(cur);
    return lines.join("<br>");
  }

  function annIndex(gd, prefix) {
    var a = (gd.layout && gd.layout.annotations) || [];
    for (var i = 0; i < a.length; i++) {
      if (a[i] && typeof a[i].text === "string" && a[i].text.indexOf(prefix) === 0) return i;
    }
    return -1;
  }

  // isi legenda HTML pengganti colorbar. "" = tidak ada legenda (mis. peta simbol proporsional).
  function legendHTML(gd) {
    var d0 = (gd.data && gd.data[0]) || {}, L = gd.layout || {}, i, out;

    if (d0.type === "treemap" || d0.type === "sunburst") {
      var mk = d0.marker || {}, cs = mk.colorscale, cb = mk.colorbar || {};
      if (!Array.isArray(cs) || typeof mk.cmin !== "number" || typeof mk.cmax !== "number") return "";
      var suf = cb.ticksuffix || "";
      var sg = function (v) { return (v > 0 ? "+" : "") + fmt(v) + suf; };
      var stops = cs.map(function (s) { return s[1] + " " + Math.round(s[0] * 100) + "%"; }).join(",");
      return '<div class="p3m-leg-t">' + esc((cb.title && cb.title.text) || "") + "</div>" +
        '<div class="p3m-leg-bar" style="background:linear-gradient(90deg,' + stops + ')"></div>' +
        '<div class="p3m-leg-l"><span>' + sg(mk.cmin) + "</span><span>" + sg((mk.cmin + mk.cmax) / 2) + "</span><span>" + sg(mk.cmax) + "</span></div>";
    }

    var ca = L.coloraxis, cb2 = (ca && ca.colorbar) || {};
    if (ca && Array.isArray(ca.colorscale) && Array.isArray(cb2.tickvals) && cb2.tickvals.length > 1) {
      var ed = cb2.tickvals, cl = [];
      var head = '<div class="p3m-leg-t">' + esc((cb2.title && cb2.title.text) || "") + "</div>";
      for (i = 0; i < ca.colorscale.length; i += 2) cl.push(ca.colorscale[i][1]);   // skala bertangga: tiap kelas = sepasang entri
      if (cl.length === ed.length - 1) {
        out = "";
        for (i = 0; i < cl.length; i++) {
          out += '<div><i style="background:' + cl[i] + '"></i><b>' + fmt(ed[i]) + "\u2013" + fmt(ed[i + 1]) + "</b></div>";
        }
        return head + '<div class="p3m-leg-c">' + out + "</div>";
      }
      var st = ca.colorscale.map(function (s) { return s[1] + " " + Math.round(s[0] * 100) + "%"; }).join(",");
      return head + '<div class="p3m-leg-bar" style="background:linear-gradient(90deg,' + st + ')"></div>' +
        '<div class="p3m-leg-l"><span>' + fmt(ed[0]) + "</span><span>" + fmt(ed[ed.length - 1]) + "</span></div>";
    }
    return "";
  }

  // pasang/perbarui/hapus legenda di dalam slot grafik (melayang di atas margin bawah plot)
  function syncLegend(gd) {
    var box = gd.closest && gd.closest(".p3-slot");
    if (!box) return;                                   // masih di #dash-stage; dipasang lagi setelah grafik dipindah ke slot
    var html = "";
    try { html = legendHTML(gd); } catch (e) { html = ""; }
    var cur = box.querySelector(".p3m-leg");
    if (!html) { if (cur && cur.parentNode) cur.parentNode.removeChild(cur); return; }
    if (!cur) { cur = document.createElement("div"); cur.className = "p3m-leg"; box.appendChild(cur); }
    if (cur._h !== html) { cur.innerHTML = html; cur._h = html; }
  }

  // BELANJA (treemap/sunburst) dan PETA (choropleth/simbol): satu kali per figure baru
  function adaptWide(gd, t) {
    var Pl = window.Plotly, L = gd.layout || {}, m = L.margin || {};
    if (m.autoexpand === false) { syncLegend(gd); return; }   // sudah disesuaikan

    var lay = { "margin.autoexpand": false, "margin.l": 4, "margin.r": 4, "margin.t": 30, "margin.b": 84 };
    var dat = {}, idx = [0], i;

    var si = annIndex(gd, "Sumber:");
    if (si > -1) {
      lay["annotations[" + si + "].text"] = wrapText(L.annotations[si].text, 58);
      lay["annotations[" + si + "].font.size"] = 8;
    }

    if (t === "treemap" || t === "sunburst") {
      dat = { "marker.showscale": false, "textfont.size": 11 };   // colorbar diganti legenda HTML
      lay["uniformtext.minsize"] = 8;
      if (t === "treemap") dat["pathbar.thickness"] = 22;
    } else {
      lay["margin.l"] = 0; lay["margin.r"] = 0;
      if (L.coloraxis) lay["coloraxis.showscale"] = false;      // choropleth: colorbar diganti legenda kelas
      var bi = -1;
      (gd.data || []).forEach(function (tr, k) { if (tr.type === "scattergeo") bi = k; });
      if (bi > -1) {                                            // peta simbol: lingkaran lebih kecil agar tidak saling menutup
        var s0 = gd.data[bi].marker && gd.data[bi].marker.sizeref;
        if (typeof s0 === "number") { dat = { "marker.sizeref": s0 * Math.pow(26 / 14, 2) }; idx = [bi]; }
        lay["legend.font.size"] = 10;
        var ci = annIndex(gd, "Luas lingkaran");
        if (ci > -1) {
          lay["annotations[" + ci + "].text"] = "Luas lingkaran proporsional<br>dengan persentase kemiskinan";
          lay["annotations[" + ci + "].font.size"] = 9;
        }
      }
    }

    Pl.update(gd, dat, lay, idx).then(function () { syncLegend(gd); }).catch(function () {});
  }

  // Idempoten: aman dipanggil tiap plotly_afterplot.
  function adapt(gd) {
    var Pl = window.Plotly;
    if (!narrow() || !Pl || !gd || !gd._fullData || !gd._fullLayout) return;
    var t = gd._fullData[0] && gd._fullData[0].type;

    if (t === "treemap" || t === "sunburst" || t === "choropleth" || t === "scattergeo") {
      adaptWide(gd, t);
      return;
    }

    var rel = {}, rst = {};
    var L = gd._fullLayout;
    if (t === "splom") {
      if (L.title && L.title.font && L.title.font.size > 13) { rel = { "title.font.size": 13, "title.subtitle.font.size": 9, "margin.l": 50, "margin.r": 8 }; }
      if (gd._fullData[0].marker && gd._fullData[0].marker.size > 6) { rst = { "marker.size": 6 }; }
    } else if (t === "scatter" || t === "heatmap" || t === "parcoords") {
      if (L.title && L.title.font && L.title.font.size > 13) {
        rel = { "title.font.size": 13, "title.subtitle.font.size": 9 };
        if (t === "heatmap") {
          rst = { "colorbar.thickness": 8, "colorbar.len": 0.7 };
          rel["margin.r"] = 6;
        }
      }
    }

    var jobs = [];
    if (Object.keys(rst).length) jobs.push(function () { return Pl.restyle(gd, rst); });
    if (Object.keys(rel).length) jobs.push(function () { return Pl.relayout(gd, rel); });
    jobs.reduce(function (p, j) { return p.then(j); }, Promise.resolve()).catch(function () {});
  }
  window.p3mAdapt = adapt;   // untuk pengujian/debug

  function hook(gd) {
    if (gd._p3mHook) return;
    gd._p3mHook = true;
    gd.on("plotly_afterplot", function () { adapt(gd); });
    adapt(gd);
  }
  function scan() {
    document.querySelectorAll(".p3-slot .js-plotly-plot, #dash-stage .js-plotly-plot").forEach(hook);
  }
  new MutationObserver(function () { if (narrow()) scan(); }).observe(document.body, { childList: true, subtree: true });
  scan();

  /* ---------- 6. melewati batas 1024px (putar tablet, ubah ukuran jendela): muat ulang agar tata letak bersih ---------- */
  var was = narrow(), t0 = Date.now();
  var onChange = function () {
    var now = narrow();
    if (now !== was && Date.now() - t0 > 2000) { was = now; location.reload(); }
    was = now;
  };
  if (mq.addEventListener) mq.addEventListener("change", onChange); else if (mq.addListener) mq.addListener(onChange);
})();