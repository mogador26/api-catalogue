/* Catalogue des API : filtres, rendu Redoc et rendu Mermaid. */
(function () {
  "use strict";

  /* ---------------------------------------------------------------- Filtres */
  function initFiltres() {
    var form = document.getElementById("catalogue-filtres");
    var items = Array.prototype.slice.call(document.querySelectorAll(".api-item"));
    if (!form || !items.length) return;

    var resultat = document.getElementById("catalogue-resultat");
    var vide = document.getElementById("catalogue-vide");
    var recherche = document.getElementById("filtre-recherche");

    function valeurs(name) {
      return Array.prototype.slice
        .call(form.querySelectorAll('input[name="' + name + '"]:checked'))
        .map(function (i) { return i.value; });
    }

    function normaliser(texte) {
      return (texte || "").toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
    }

    function appliquer() {
      var acces = valeurs("acces");
      var statuts = valeurs("statut");
      var termes = normaliser(recherche.value).split(/\s+/).filter(Boolean);
      var visibles = 0, ouvertes = 0;

      items.forEach(function (item) {
        var modes = (item.dataset.acces || "").split(" ");
        var texte = normaliser(item.dataset.recherche);
        var ok =
          (!acces.length || acces.some(function (a) { return modes.indexOf(a) !== -1; })) &&
          (!statuts.length || statuts.indexOf(item.dataset.statut) !== -1) &&
          termes.every(function (t) { return texte.indexOf(t) !== -1; });
        item.hidden = !ok;
        if (ok) {
          visibles++;
          if (item.dataset.ouverte === "true") ouvertes++;
        }
      });

      // Compteurs recalculés automatiquement selon les filtres
      var set = function (k, v) {
        var el = document.querySelector('[data-stat="' + k + '"]');
        if (el) el.textContent = v;
      };
      set("total", visibles);
      set("ouvertes", ouvertes);
      set("auth", visibles - ouvertes);
      document.querySelectorAll("[data-stat-mode]").forEach(function (el) {
        var mode = el.dataset.statMode;
        el.textContent = items.filter(function (i) {
          return !i.hidden && (i.dataset.acces || "").split(" ").indexOf(mode) !== -1;
        }).length;
      });
      if (resultat) resultat.textContent = visibles + (visibles > 1 ? " API affichées" : " API affichée");
      if (vide) vide.hidden = visibles !== 0;

      // Filtres conservés dans l'URL (partage de lien)
      var params = new URLSearchParams();
      acces.forEach(function (a) { params.append("acces", a); });
      statuts.forEach(function (s) { params.append("statut", s); });
      if (recherche.value) params.set("q", recherche.value);
      var qs = params.toString();
      history.replaceState(null, "", location.pathname + (qs ? "?" + qs : "") + location.hash);
    }

    // Restauration depuis l'URL
    var params = new URLSearchParams(location.search);
    params.getAll("acces").concat(params.getAll("statut")).forEach(function (v) {
      var input = form.querySelector('input[value="' + CSS.escape(v) + '"]');
      if (input) input.checked = true;
    });
    if (params.get("q")) recherche.value = params.get("q");

    form.addEventListener("input", appliquer);
    form.addEventListener("change", appliquer);
    form.addEventListener("submit", function (e) { e.preventDefault(); });
    form.addEventListener("reset", function () { setTimeout(appliquer, 0); });
    appliquer();
  }

  /* ------------------------------------------------------------------ Redoc */
  var REDOC_OPTIONS = {
    hideHostname: false,
    expandResponses: "200,201",
    pathInMiddlePanel: true,
    nativeScrollbars: true,
    theme: {
      colors: { primary: { main: "#000091" }, success: { main: "#18753c" }, error: { main: "#ce0500" } },
      typography: {
        fontFamily: "Marianne, arial, sans-serif",
        headings: { fontFamily: "Marianne, arial, sans-serif" },
        code: { fontFamily: "'Courier New', monospace" }
      },
      sidebar: { width: "220px", backgroundColor: "#f6f6f6", textColor: "#161616", activeTextColor: "#000091" },
      rightPanel: { width: "38%", backgroundColor: "#1e1e1e" }
    }
  };

  function chargerSpec(el) {
    var url = el.dataset.specUrl;
    var secours = el.dataset.fallbackUrl;
    if (!secours) return Promise.resolve(url);
    return fetch(url, { method: "GET" })
      .then(function (r) { return r.ok ? url : secours; })
      .catch(function () { return secours; });
  }

  function initRedoc() {
    var viewers = document.querySelectorAll("[data-spec-url]");
    if (!viewers.length) return;
    if (typeof Redoc === "undefined") {
      viewers.forEach(function (el) {
        el.innerHTML = '<p class="fr-error-text">La bibliothèque Redoc n\'a pas pu être chargée.</p>';
      });
      return;
    }
    viewers.forEach(function (el) {
      chargerSpec(el).then(function (spec) {
        Redoc.init(spec, REDOC_OPTIONS, el, function (err) {
          if (err) {
            el.innerHTML =
              '<p class="fr-error-text">Impossible de charger la spécification ' +
              '<a href="' + spec + '">' + spec + "</a>.</p>";
          }
        });
      });
    });
  }

  /* ---------------------------------------------------------------- Mermaid */
  function initMermaid() {
    if (typeof mermaid === "undefined" || !document.querySelector(".mermaid")) return;
    mermaid.initialize({
      startOnLoad: false,
      theme: "base",
      securityLevel: "strict",
      fontFamily: "Marianne, arial, sans-serif",
      themeVariables: {
        fontFamily: "Marianne, arial, sans-serif",
        git0: "#000091", git1: "#18753c", git2: "#b34000", git3: "#6e445a",
        git4: "#006a6f", git5: "#716043", git6: "#a558a0", git7: "#3a3a3a",
        gitBranchLabel0: "#ffffff", gitBranchLabel1: "#ffffff", gitBranchLabel2: "#ffffff",
        gitBranchLabel3: "#ffffff", gitBranchLabel4: "#ffffff", gitBranchLabel5: "#ffffff",
        gitBranchLabel6: "#ffffff", gitBranchLabel7: "#ffffff",
        tagLabelColor: "#161616", tagLabelBackground: "#e3e3fd", tagLabelBorder: "#000091",
        commitLabelColor: "#161616", commitLabelBackground: "#f6f6f6"
      }
    });
    document.querySelectorAll(".mermaid").forEach(function (el, i) {
      var source = el.textContent;
      mermaid
        .render("mermaid-graphe-" + i, source)
        .then(function (res) {
          el.innerHTML = res.svg;
          var svg = el.querySelector("svg");
          if (svg) {
            svg.setAttribute("role", "img");
            svg.setAttribute("aria-label", "Graphe de la feuille de route ; détail dans le tableau qui suit");
          }
        })
        .catch(function (e) {
          console.error("Mermaid :", e);
        });
    });
  }

  function init() {
    initFiltres();
    initRedoc();
    initMermaid();
  }

  // Initialisation après le post-traitement du thème (qui peut réécrire le contenu au DOMContentLoaded)
  if (document.readyState === "complete") {
    init();
  } else {
    window.addEventListener("load", init);
  }
})();
