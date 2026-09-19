/* Version autonome du catalogue : routeur par ancre (#/chemin/?filtres) + filtres, Redoc et Mermaid. */
(function () {
  "use strict";

  var SPECS = JSON.parse(document.getElementById("specs").textContent);
  var main = document.getElementById("content");
  var libs = {};

  function charger(nom, url) {
    if (!libs[nom]) {
      libs[nom] = new Promise(function (ok, ko) {
        var s = document.createElement("script");
        s.src = url;
        s.onload = ok;
        s.onerror = function () { ko(new Error("Chargement impossible : " + url)); };
        document.head.appendChild(s);
      });
    }
    return libs[nom];
  }

  /* ------------------------------------------------------------- Routeur */
  function lireRoute() {
    var h = decodeURIComponent(location.hash.replace(/^#\/?/, ""));
    var ancre = "";
    if (h.indexOf("::") !== -1) { ancre = h.split("::")[1]; h = h.split("::")[0]; }
    var query = "";
    if (h.indexOf("?") !== -1) { query = h.split("?")[1]; h = h.split("?")[0]; }
    return { chemin: h.replace(/\/+$/, ""), query: new URLSearchParams(query), ancre: ancre };
  }

  function majNav(chemin) {
    document.querySelectorAll("#header-navigation a.fr-nav__link, .fr-header__tools-links a").forEach(function (a) {
      var cible = (a.getAttribute("href") || "").replace(/^#\/?/, "").replace(/\/+$/, "");
      if (cible === chemin) a.setAttribute("aria-current", "page");
      else a.removeAttribute("aria-current");
    });
  }

  function afficher() {
    var r = lireRoute();
    // Ferme les menus/modales DSFR ouverts (navigation mobile, recherche)
    document.querySelectorAll(".fr-modal--opened").forEach(function (m) {
      if (window.dsfr) try { dsfr(m).modal.conceal(); } catch (e) {}
    });

    if (r.chemin.indexOf("redoc/") === 0) {
      var slug = r.chemin.split("/")[1];
      var spec = SPECS[slug];
      main.innerHTML =
        '<div class="preview-redoc-bar"><a class="fr-link" href="#/apis/' + slug + '/">Retour à la fiche ' +
        (spec ? spec.title : "") + '</a></div><div class="preview-redoc api-redoc"><div data-spec-id="' + slug + '"></div></div>';
      document.title = (spec ? spec.title : "API") + " – Documentation OpenAPI";
      initRedoc();
      if (window.__initVisiteGuidee) window.__initVisiteGuidee();
      window.scrollTo(0, 0);
      return;
    }

    var id = "tpl-" + (r.chemin ? r.chemin.replace(/\//g, "--") : "accueil");
    var tpl = document.getElementById(id);
    if (!tpl) {
      main.innerHTML =
        '<div class="fr-container fr-py-6w"><h1>Page introuvable</h1><p>Cette page n\'existe pas. ' +
        '<a href="#/">Revenir au catalogue</a>.</p></div>';
      return;
    }
    main.innerHTML = "";
    main.appendChild(tpl.content.cloneNode(true));
    document.title = tpl.dataset.title || "Catalogue des API";
    majNav(r.chemin);
    initFiltres(r.query);
    initRedoc();
    initMermaid();
    if (window.__initVisiteGuidee) window.__initVisiteGuidee();

    if (r.ancre) {
      var cible = document.getElementById(r.ancre);
      if (cible) { cible.scrollIntoView(); return; }
    }
    window.scrollTo(0, 0);
    var h1 = main.querySelector("h1");
    if (h1 && !premierAffichage) { h1.setAttribute("tabindex", "-1"); h1.focus({ preventScroll: true }); }
  }

  // Ancres internes (#section) : défilement sans changer de route
  document.addEventListener("click", function (e) {
    var a = e.target.closest && e.target.closest("a[href^='#']");
    if (!a) return;
    var href = a.getAttribute("href");
    if (href === "#" ) { e.preventDefault(); return; }
    if (href.indexOf("#/") === 0) return;
    var cible = document.getElementById(href.slice(1));
    if (cible) {
      e.preventDefault();
      cible.scrollIntoView({ behavior: "auto" });
      if (cible.tabIndex < 0) cible.setAttribute("tabindex", "-1");
      cible.focus({ preventScroll: true });
    }
  });

  // Recherche de l'en-tête : bascule vers le catalogue filtré
  var formRecherche = document.getElementById("preview-search");
  if (formRecherche) {
    formRecherche.addEventListener("submit", function (e) {
      e.preventDefault();
      var q = (formRecherche.querySelector("input") || {}).value || "";
      location.hash = "#/?q=" + encodeURIComponent(q);
    });
  }

  /* ------------------------------------------------------------- Filtres */
  function initFiltres(params) {
    var form = document.getElementById("catalogue-filtres");
    var items = Array.prototype.slice.call(main.querySelectorAll(".api-item"));
    if (!form || !items.length) return;
    var resultat = document.getElementById("catalogue-resultat");
    var vide = document.getElementById("catalogue-vide");
    var recherche = document.getElementById("filtre-recherche");

    function valeurs(name) {
      return Array.prototype.slice.call(form.querySelectorAll('input[name="' + name + '"]:checked'))
        .map(function (i) { return i.value; });
    }
    function normaliser(t) {
      return (t || "").toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
    }

    function appliquer() {
      var acces = valeurs("acces"), statuts = valeurs("statut");
      var termes = normaliser(recherche.value).split(/\s+/).filter(Boolean);
      var visibles = 0, ouvertes = 0;
      items.forEach(function (item) {
        var modes = (item.dataset.acces || "").split(" ");
        var texte = normaliser(item.dataset.recherche);
        var ok = (!acces.length || acces.some(function (a) { return modes.indexOf(a) !== -1; })) &&
          (!statuts.length || statuts.indexOf(item.dataset.statut) !== -1) &&
          termes.every(function (t) { return texte.indexOf(t) !== -1; });
        item.hidden = !ok;
        if (ok) { visibles++; if (item.dataset.ouverte === "true") ouvertes++; }
      });
      var set = function (k, v) { var el = main.querySelector('[data-stat="' + k + '"]'); if (el) el.textContent = v; };
      set("total", visibles); set("ouvertes", ouvertes); set("auth", visibles - ouvertes);
      main.querySelectorAll("[data-stat-mode]").forEach(function (el) {
        var mode = el.dataset.statMode;
        el.textContent = items.filter(function (i) {
          return !i.hidden && (i.dataset.acces || "").split(" ").indexOf(mode) !== -1;
        }).length;
      });
      resultat.textContent = visibles + (visibles > 1 ? " API affichées" : " API affichée");
      vide.hidden = visibles !== 0;

      var p = new URLSearchParams();
      acces.forEach(function (a) { p.append("acces", a); });
      statuts.forEach(function (s) { p.append("statut", s); });
      if (recherche.value) p.set("q", recherche.value);
      var chemin = lireRoute().chemin;
      var qs = p.toString();
      history.replaceState(null, "", "#/" + (chemin ? chemin + "/" : "") + (qs ? "?" + qs : ""));
    }

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

  /* --------------------------------------------------------------- Redoc */
  var REDOC_OPTIONS = {
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

  function initRedoc() {
    var viewers = main.querySelectorAll("[data-spec-id]");
    if (!viewers.length) return;
    charger("redoc", "__REDOC_CDN__").then(function () {
      viewers.forEach(function (el) {
        var entree = SPECS[el.dataset.specId];
        if (!entree) { el.innerHTML = '<p class="fr-error-text">Spécification introuvable.</p>'; return; }
        Redoc.init(entree.spec, REDOC_OPTIONS, el);
      });
    }).catch(function (e) {
      viewers.forEach(function (el) { el.innerHTML = '<p class="fr-error-text fr-p-3w">' + e.message + "</p>"; });
    });
  }

  /* ------------------------------------------------------------- Mermaid */
  var mermaidPret = false;
  function initMermaid() {
    var graphes = main.querySelectorAll(".mermaid");
    if (!graphes.length) return;
    charger("mermaid", "__MERMAID_CDN__").then(function () {
      if (!mermaidPret) {
        mermaid.initialize({
          startOnLoad: false, theme: "base", securityLevel: "strict",
          fontFamily: "Marianne, arial, sans-serif",
          themeVariables: {
            fontFamily: "Marianne, arial, sans-serif",
            git0: "#000091", git1: "#18753c", git2: "#b34000", git3: "#6e445a",
            git4: "#006a6f", git5: "#716043", git6: "#a558a0", git7: "#3a3a3a",
            gitBranchLabel0: "#ffffff", gitBranchLabel1: "#ffffff", gitBranchLabel2: "#ffffff",
            gitBranchLabel3: "#ffffff", gitBranchLabel4: "#ffffff", gitBranchLabel5: "#ffffff",
            tagLabelColor: "#161616", tagLabelBackground: "#e3e3fd", tagLabelBorder: "#000091",
            commitLabelColor: "#161616", commitLabelBackground: "#f6f6f6"
          }
        });
        mermaidPret = true;
      }
      graphes.forEach(function (el, i) {
        mermaid.render("graphe-" + Date.now() + "-" + i, el.textContent).then(function (res) {
          el.innerHTML = res.svg;
          var svg = el.querySelector("svg");
          if (svg) {
            svg.setAttribute("role", "img");
            svg.setAttribute("aria-label", "Graphe de la feuille de route ; détail dans le tableau qui suit");
          }
        });
      });
    }).catch(function (e) { console.error(e); });
  }

  var premierAffichage = true;
  window.addEventListener("hashchange", afficher);
  afficher();
  premierAffichage = false;
})();
