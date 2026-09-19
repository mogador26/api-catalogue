/* Visite guidée du catalogue (coach marks).
 * Deux parcours possibles selon la page : l'accueil (6 étapes) et une fiche API (2 étapes).
 * Se déclenche automatiquement une fois par navigateur (mémorisé en localStorage), et à tout
 * moment via le bouton « Visite guidée » de l'en-tête. */
(function () {
  "use strict";

  var CLE_ACCUEIL = "catalogue-api:visite-accueil-vue";
  var CLE_FICHE = "catalogue-api:visite-fiche-vue";
  var REDUIT = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  function vu(cle) {
    try { return localStorage.getItem(cle) === "1"; } catch (e) { return true; }
  }
  function marquerVu(cle) {
    try { localStorage.setItem(cle, "1"); } catch (e) {}
  }

  /* ------------------------------------------------------------ Étapes */
  var ETAPES_ACCUEIL = [
    {
      titre: "Bienvenue sur le catalogue des API",
      texte: "Ce catalogue recense les API de l'administration : à quoi elles servent, comment y accéder et qui contacter. Cette courte visite vous montre l'essentiel en six étapes.",
    },
    {
      selecteur: "#search-540, .fr-header__navbar .fr-search-bar, .fr-header__navbar .fr-btn--search",
      titre: "Rechercher une API",
      texte: "Recherchez par nom, mot-clé ou usage métier : « fourrière », « subvention », « associations »…",
    },
    {
      selecteur: ".catalogue-sidemenu",
      titre: "Thèmes et filtres",
      texte: "Parcourez les API par thème, ou filtrez-les par modalité d'accès et par statut. Sur mobile, ce panneau se replie : touchez « Thèmes et filtres » pour l'ouvrir.",
      avant: function (el) { return _ouvrirSiReplie(el); },
    },
    {
      selecteur: ".catalogue-chiffres",
      titre: "Les chiffres clés",
      texte: "D'un coup d'œil : combien d'API sont au catalogue, combien sont ouvertes sans authentification, et combien sont soumises à un contrôle d'accès. Ces chiffres suivent vos filtres.",
    },
    {
      selecteur: "#catalogue-tuiles .api-item",
      titre: "Une fiche API en un coup d'œil",
      texte: "Chaque tuile indique si l'API est ouverte ou soumise à contrôle d'accès, ainsi que son thème, son statut et sa version. Cliquez dessus pour ouvrir la fiche complète.",
    },
    {
      selecteur: "#parcours-titre",
      titre: "Besoin d'aide pour choisir ?",
      texte: "Ce parcours en quatre questions vous recommande les API adaptées à votre domaine, à votre capacité d'accès et à votre calendrier — et vous annonce celles qui arrivent bientôt.",
    },
  ];

  var ETAPES_FICHE = [
    {
      selecteur: ".api-aside",
      titre: "Le panneau d'accès",
      texte: "Toutes les informations pratiques sont ici : l'API est-elle ouverte ou soumise à contrôle, quels types d'accès existent, le lien vers le swagger, le contact du producteur et le nombre d'appels autorisés.",
    },
    {
      selecteur: ".cas-usage .cas-usage__item",
      titre: "Les cas d'usage",
      texte: "Chaque cas d'usage précise qui l'utilise et le bénéfice obtenu, pour comprendre rapidement si cette API répond à votre besoin.",
    },
  ];

  function _cible(selecteur) {
    if (!selecteur) return null;
    var candidats = document.querySelectorAll(selecteur);
    for (var i = 0; i < candidats.length; i++) {
      var r = candidats[i].getBoundingClientRect();
      if (r.width > 0 && r.height > 0) return candidats[i];
    }
    return candidats[0] || null;
  }

  function _ouvrirSiReplie(el) {
    var bouton = document.querySelector('.fr-sidemenu__btn[aria-controls="sidemenu-catalogue"]');
    if (bouton && bouton.offsetParent !== null && bouton.getAttribute("aria-expanded") === "false") {
      bouton.click();
      return new Promise(function (ok) { setTimeout(ok, REDUIT ? 0 : 350); });
    }
    return null;
  }

  /* -------------------------------------------------------------- Moteur */
  var etat = null; // { etapes, index, cle }
  var els = {};

  function construireDom() {
    if (els.voile) return;
    els.voile = document.createElement("div");
    els.voile.className = "visite-guidee__voile";
    els.voile.setAttribute("tabindex", "-1");

    els.bulle = document.createElement("div");
    els.bulle.className = "visite-guidee__bulle";
    els.bulle.setAttribute("role", "dialog");
    els.bulle.setAttribute("aria-modal", "true");
    els.bulle.setAttribute("aria-labelledby", "visite-guidee-titre");
    els.bulle.setAttribute("aria-describedby", "visite-guidee-texte");
    els.bulle.innerHTML =
      '<p class="visite-guidee__etat"></p>' +
      '<h2 class="visite-guidee__titre" id="visite-guidee-titre"></h2>' +
      '<p class="visite-guidee__texte" id="visite-guidee-texte"></p>' +
      '<div class="visite-guidee__actions">' +
      '<button type="button" class="fr-btn fr-btn--tertiary-no-outline fr-btn--sm" data-action="passer">Passer la visite</button>' +
      '<span class="visite-guidee__nav">' +
      '<button type="button" class="fr-btn fr-btn--secondary fr-btn--sm" data-action="precedent">Précédent</button>' +
      '<button type="button" class="fr-btn fr-btn--sm" data-action="suivant">Suivant</button>' +
      "</span></div>";
    document.body.appendChild(els.voile);
    document.body.appendChild(els.bulle);

    els.bulle.addEventListener("click", function (e) {
      var action = e.target.closest && e.target.closest("[data-action]");
      if (!action) return;
      if (action.dataset.action === "suivant") avancer(1);
      else if (action.dataset.action === "precedent") avancer(-1);
      else if (action.dataset.action === "passer") terminer();
    });
    els.bulle.addEventListener("keydown", function (e) {
      if (e.key === "Escape") { terminer(); return; }
      if (e.key !== "Tab") return;
      var focusables = els.bulle.querySelectorAll("button");
      var premier = focusables[0], dernier = focusables[focusables.length - 1];
      if (e.shiftKey && document.activeElement === premier) { e.preventDefault(); dernier.focus(); }
      else if (!e.shiftKey && document.activeElement === dernier) { e.preventDefault(); premier.focus(); }
    });
    window.addEventListener("resize", function () { if (etat) positionner(); });
  }

  function demarrer(etapes, cle) {
    construireDom();
    marquerVu(cle);
    etat = { etapes: etapes, index: 0, cle: cle };
    afficherEtape();
  }

  function avancer(sens) {
    if (!etat) return;
    var suivant = etat.index + sens;
    if (suivant < 0) return;
    if (suivant >= etat.etapes.length) { terminer(); return; }
    etat.index = suivant;
    afficherEtape();
  }

  function terminer() {
    if (!etat) return;
    var declencheur = document.getElementById("visite-guidee-demarrer");
    etat = null;
    els.voile.classList.remove("visite-guidee__voile--visible");
    els.bulle.classList.remove("visite-guidee__bulle--visible");
    document.querySelectorAll(".visite-guidee__cible").forEach(function (el) {
      el.classList.remove("visite-guidee__cible");
    });
    if (declencheur) declencheur.focus();
  }

  function afficherEtape() {
    var pas = etat.etapes[etat.index];
    document.querySelectorAll(".visite-guidee__cible").forEach(function (el) {
      el.classList.remove("visite-guidee__cible");
    });

    var cible = pas.selecteur ? _cible(pas.selecteur) : null;
    var suite = function () {
      if (cible) {
        cible.classList.add("visite-guidee__cible");
        var bloc = cible.getBoundingClientRect().height > window.innerHeight * .7 ? "start" : "center";
        cible.scrollIntoView({ block: bloc, behavior: REDUIT ? "auto" : "smooth" });
      }
      setTimeout(function () {
        remplirBulle(pas);
        positionner();
        els.voile.classList.add("visite-guidee__voile--visible");
        els.bulle.classList.add("visite-guidee__bulle--visible");
        els.bulle.querySelector('[data-action="suivant"]').focus();
      }, cible && !REDUIT ? 300 : 0);
    };

    var resultat = pas.avant ? pas.avant(cible) : null;
    if (resultat && typeof resultat.then === "function") resultat.then(suite);
    else suite();
  }

  function remplirBulle(pas) {
    var n = etat.etapes.length;
    els.bulle.querySelector(".visite-guidee__etat").textContent = "Étape " + (etat.index + 1) + " sur " + n;
    els.bulle.querySelector(".visite-guidee__titre").textContent = pas.titre;
    els.bulle.querySelector(".visite-guidee__texte").textContent = pas.texte;
    els.bulle.querySelector('[data-action="precedent"]').hidden = etat.index === 0;
    els.bulle.querySelector('[data-action="suivant"]').textContent = etat.index === n - 1 ? "Terminer" : "Suivant";
  }

  function positionner() {
    var pas = etat.etapes[etat.index];
    var cible = pas.selecteur ? _cible(pas.selecteur) : null;
    var bulle = els.bulle;
    var marge = 16;

    if (!cible) {
      els.voile.style.clipPath = "";
      bulle.style.top = "50%";
      bulle.style.left = "50%";
      bulle.style.transform = "translate(-50%, -50%)";
      return;
    }

    var r = cible.getBoundingClientRect();
    var rayon = 8;
    els.voile.style.clipPath =
      "polygon(0 0,0 100%,100% 100%,100% 0,0 0," +
      (r.left - rayon) + "px " + (r.top - rayon) + "px," +
      (r.left - rayon) + "px " + (r.bottom + rayon) + "px," +
      (r.right + rayon) + "px " + (r.bottom + rayon) + "px," +
      (r.right + rayon) + "px " + (r.top - rayon) + "px," +
      (r.left - rayon) + "px " + (r.top - rayon) + "px)";

    bulle.style.transform = "none";
    var bw = bulle.offsetWidth, bh = bulle.offsetHeight;
    var vw = window.innerWidth, vh = window.innerHeight;
    var centreH = Math.max(marge, Math.min(vw - bw - marge, r.left + r.width / 2 - bw / 2));
    var centreV = Math.max(marge, Math.min(vh - bh - marge, r.top + r.height / 2 - bh / 2));

    // Quatre positions candidates autour de la cible ; on choisit celle qui offre le plus de
    // marge après avoir logé la bulle (fonctionne quelle que soit la forme de la cible : barre
    // horizontale, colonne verticale, ou bloc occupant tout l'écran).
    var candidats = [
      { cote: "bas", marge: vh - r.bottom - marge - bh, top: r.bottom + marge, left: centreH },
      { cote: "haut", marge: r.top - marge - bh, top: r.top - marge - bh, left: centreH },
      { cote: "droite", marge: vw - r.right - marge - bw, top: centreV, left: r.right + marge },
      { cote: "gauche", marge: r.left - marge - bw, top: centreV, left: r.left - marge - bw },
    ];
    var choix = candidats.reduce(function (a, b) { return b.marge > a.marge ? b : a; });
    var top = choix.marge >= 0 ? choix.top : (choix.cote === "haut" || choix.cote === "bas"
      ? (vh - r.bottom - marge >= r.top - marge ? vh - bh - marge : marge)
      : centreV);
    var left = choix.marge >= 0 ? choix.left : (choix.cote === "gauche" || choix.cote === "droite"
      ? (vw - r.right - marge >= r.left - marge ? vw - bw - marge : marge)
      : centreH);
    top = Math.max(marge, Math.min(vh - bh - marge, top));
    left = Math.max(marge, Math.min(vw - bw - marge, left));
    bulle.style.top = top + "px";
    bulle.style.left = left + "px";
  }

  /* --------------------------------------------------------------- Amorçage */
  function disponibleAccueil() {
    return document.querySelector("[data-parcours]") && document.getElementById("catalogue-tuiles");
  }
  function disponibleFiche() {
    return document.querySelector(".api-aside");
  }

  function init() {
    // Dans la version à page unique (visite via #/...), le contenu change sans recharger la
    // page : cette fonction est donc rappelable, et rebranche proprement le bouton à chaque fois.
    if (etat) terminer();
    var declencheur = document.getElementById("visite-guidee-declencheur");
    var bouton = document.getElementById("visite-guidee-demarrer");
    if (!declencheur || !bouton) return;

    var etapes = null, cle = null;
    if (disponibleAccueil()) { etapes = ETAPES_ACCUEIL; cle = CLE_ACCUEIL; }
    else if (disponibleFiche()) { etapes = ETAPES_FICHE; cle = CLE_FICHE; }

    if (bouton._visiteGuideeEcouteur) bouton.removeEventListener("click", bouton._visiteGuideeEcouteur);
    if (!etapes) { declencheur.hidden = true; return; }

    declencheur.hidden = false;
    bouton._visiteGuideeEcouteur = function () { demarrer(etapes, cle); };
    bouton.addEventListener("click", bouton._visiteGuideeEcouteur);

    var force = /(?:^|[?&])visite=1(?:&|$)/.test(location.search);
    if (force || !vu(cle)) {
      setTimeout(function () { demarrer(etapes, cle); }, 600);
    }
  }

  // Exposée pour la version à page unique (tools/preview_app.js), qui rappelle cette
  // fonction après chaque changement de route puisque la page ne se recharge pas.
  window.__initVisiteGuidee = init;

  if (document.readyState === "complete") init();
  else window.addEventListener("load", init);
})();
