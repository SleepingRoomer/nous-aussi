/* Nous aussi — comportements des pages (recherche, filtres, frise). Aucune dépendance. */
(function () {
  "use strict";
  var $ = function (s, el) { return (el || document).querySelector(s); };
  var $$ = function (s, el) { return Array.prototype.slice.call((el || document).querySelectorAll(s)); };
  var norm = function (s) { return (s || "").normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase(); };

  /* ---------- Recherche de l'accueil ---------- */
  function initSearch() {
    var form = $("#search"), input = $("#q"), list = $("#suggest"), data = $("#index-recherche");
    if (!form || !input || !list || !data) return;
    var items = [];
    try { items = JSON.parse(data.textContent); } catch (e) { return; }
    var current = [], active = -1;

    function render() {
      var q = norm(input.value.trim());
      active = -1;
      if (!q) { list.hidden = true; list.innerHTML = ""; current = []; return; }
      current = items.filter(function (it) { return norm(it.t).indexOf(q) !== -1 || norm(it.k).indexOf(q) !== -1; }).slice(0, 8);
      if (!current.length) {
        list.innerHTML = '<li style="padding:10px 12px;color:var(--muted)">Aucun résultat pour cette recherche.</li>';
      } else {
        list.innerHTML = current.map(function (it, i) {
          return '<li role="option" id="sug-' + i + '"><a href="' + it.u + '"><span>' + esc(it.t) + '</span><small>' + esc(it.s) + '</small></a></li>';
        }).join("");
      }
      list.hidden = false;
    }
    function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }
    function highlight() {
      $$("a", list).forEach(function (a, i) { a.classList.toggle("active", i === active); });
      input.setAttribute("aria-activedescendant", active >= 0 ? "sug-" + active : "");
    }
    input.addEventListener("input", render);
    input.addEventListener("keydown", function (e) {
      if (list.hidden || !current.length) return;
      if (e.key === "ArrowDown") { e.preventDefault(); active = Math.min(active + 1, current.length - 1); highlight(); }
      else if (e.key === "ArrowUp") { e.preventDefault(); active = Math.max(active - 1, 0); highlight(); }
      else if (e.key === "Escape") { list.hidden = true; }
    });
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var pick = current[active >= 0 ? active : 0];
      if (pick) window.location.href = pick.u;
    });
    document.addEventListener("click", function (e) { if (!form.contains(e.target)) list.hidden = true; });
  }

  /* ---------- Filtres de la page maladie ---------- */
  function initFilters() {
    var browse = $(".browse");
    if (!browse) return;
    var cards = $$("#cartes .pcard"), fr = $("#fr"), reset = $("#reset"), empty = $("#vide"), count = $("#compte");
    var total = cards.length;
    var state = { vie: "all", dom: "all", src: "all", fr: false };
    var tests = {
      vie: function (c, v) { return v === "all" || c.dataset.vie === v; },
      dom: function (c, v) { return v === "all" || c.dataset.dom === v; },
      src: function (c, v) { return v === "all" || c.dataset.src === v; }
    };
    function passes(c, skip) {
      if (state.fr && c.dataset.fr !== "1") return false;
      return Object.keys(tests).every(function (k) { return k === skip || tests[k](c, state[k]); });
    }
    function update() {
      var shown = 0;
      cards.forEach(function (c) { var ok = passes(c); c.hidden = !ok; if (ok) shown++; });
      $$(".facet").forEach(function (fs) {
        var key = fs.dataset.facet;
        $$(".opt", fs).forEach(function (b) {
          var v = b.dataset.value;
          var n = cards.filter(function (c) { return passes(c, key) && tests[key](c, v); }).length;
          b.querySelector(".n").textContent = n;
          b.setAttribute("aria-pressed", String(state[key] === v));
          b.disabled = n === 0 && state[key] !== v;
        });
      });
      count.textContent = shown === total
        ? total + (total > 1 ? " personnalités" : " personnalité")
        : shown + " sur " + total;
      empty.hidden = shown !== 0;
      var dirty = state.fr || state.vie !== "all" || state.dom !== "all" || state.src !== "all";
      reset.hidden = !dirty;
    }
    $$(".facet").forEach(function (fs) {
      fs.addEventListener("click", function (e) {
        var b = e.target.closest(".opt");
        if (!b || b.disabled) return;
        state[fs.dataset.facet] = b.dataset.value;
        update();
      });
    });
    fr.addEventListener("change", function () { state.fr = fr.checked; update(); });
    function clear() { state = { vie: "all", dom: "all", src: "all", fr: false }; fr.checked = false; update(); }
    reset.addEventListener("click", clear);
    $$("[data-reset]").forEach(function (b) { b.addEventListener("click", clear); });
    update();
  }

  /* ---------- Frise ---------- */
  function initFrise() {
    var frise = $("#frise");
    if (!frise) return;
    var chips = $$(".chip"), rows = $$("li", frise), empty = $("#frise-vide");
    function apply(m) {
      chips.forEach(function (c) { c.setAttribute("aria-pressed", String(c.dataset.maladie === m)); });
      var any = false, lastCentury = null, centuryHas = false;
      rows.forEach(function (r) {
        if (r.hasAttribute("data-century")) {
          if (lastCentury) lastCentury.hidden = !centuryHas;
          lastCentury = r; centuryHas = false; return;
        }
        var ok = m === "all" || r.dataset.maladie === m;
        r.hidden = !ok;
        if (ok) { centuryHas = true; any = true; }
      });
      if (lastCentury) lastCentury.hidden = !centuryHas;
      empty.hidden = any;
    }
    chips.forEach(function (c) { c.addEventListener("click", function () { apply(c.dataset.maladie); }); });
    var start = (window.location.hash || "").slice(1);
    apply(chips.some(function (c) { return c.dataset.maladie === start; }) ? start : "all");
  }

  function init() { initSearch(); initFilters(); initFrise(); }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init); else init();
})();
