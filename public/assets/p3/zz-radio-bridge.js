/* Jembatan event: zz-extra.js memindahkan blok grafik (wrap-treemap/map/splom) keluar dari root React Dash
   (#react-entry-point) ke dalam "slot" cangkang HTML. React 18 hanya mendengarkan event di root-nya,
   jadi klik radio/checklist/tombol pada blok yang dipindah tidak pernah sampai ke callback Dash.
   Skrip ini menangkap event itu di level document dan meneruskannya lewat dash_clientside.set_props. */
(function () {
  var ORDER = {                      // urutan opsi = urutan di app.py (cadangan bila atribut value kosong)
    "hier-kind": ["treemap", "sunburst"],
    "map-kind": ["choropleth", "bubble"],
    "mv-view": ["pca", "splom", "parcoords", "heat"]
  };
  var clicks = {};
  var sfx = null;                    // suara navigasi menu yang sama dengan menu utama
  function beep() {
    try { sfx = sfx || new Audio("/assets/sfx/navigation.wav"); sfx.volume = 0.35; sfx.currentTime = 0; sfx.play().catch(function () {}); }
    catch (err) { /* abaikan: suara hanya hiasan */ }
  }

  function setProps(id, props) {
    try { window.dash_clientside.set_props(id, props); }
    catch (err) { console.warn("[radio-bridge] set_props gagal untuk", id, err); }
  }
  function outsideReact(el) {        // true bila elemen sudah dipindah keluar dari root React Dash
    var root = document.getElementById("react-entry-point");
    return !(root && root.contains(el));
  }

  document.addEventListener("change", function (e) {
    var inp = e.target;
    if (!inp || inp.tagName !== "INPUT") return;
    var box = inp.closest ? inp.closest(".p3-radio") : null;
    if (!box || !box.id || !outsideReact(box)) return;
    var inputs = Array.prototype.slice.call(box.querySelectorAll("input"));
    beep();
    if (inp.type === "radio") {
      var v = (ORDER[box.id] && ORDER[box.id][inputs.indexOf(inp)]) || inp.value;
      setProps(box.id, { value: v });
    } else if (inp.type === "checkbox") {
      setProps(box.id, { value: inputs.filter(function (i) { return i.checked; }).map(function (i) { return i.value; }) });
    }
  }, true);

  document.addEventListener("click", function (e) {
    var btn = e.target.closest ? e.target.closest("#clear-sel") : null;
    if (!btn || !outsideReact(btn)) return;
    clicks["clear-sel"] = (clicks["clear-sel"] || 0) + 1;
    setProps("clear-sel", { n_clicks: clicks["clear-sel"] });
  }, true);
})();