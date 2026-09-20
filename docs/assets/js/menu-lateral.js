/* Repli du sommaire latéral des fiches API (menu de gauche généré par le thème DSFR à partir
 * des titres de la page). Un bouton en haut du menu permet de le réduire à une simple bande
 * d'icône pour lire la fiche sur toute la largeur, puis de le rouvrir en un clic. Le choix de
 * l'utilisateur est mémorisé et s'applique à toutes les fiches. Sans effet sur le panneau
 * « Thèmes et filtres » du catalogue, qui a son propre repli (mobile) fourni par le thème. */
(function () {
  "use strict";

  var CLE = "catalogue-api:menu-lateral-replie";

  function repliePreferee() {
    try { return localStorage.getItem(CLE) === "1"; } catch (e) { return false; }
  }
  function memoriser(replie) {
    try { localStorage.setItem(CLE, replie ? "1" : "0"); } catch (e) {}
  }

  function appliquer(colonne, bouton, texte, replie) {
    colonne.classList.toggle("menu-lateral-col--repliee", replie);
    bouton.setAttribute("aria-expanded", String(!replie));
    bouton.className = "menu-lateral-bouton fr-btn fr-btn--tertiary fr-btn--sm fr-btn--icon-left " +
      (replie ? "fr-icon-arrow-right-s-line" : "fr-icon-arrow-left-s-line");
    var libelle = replie ? "Afficher le sommaire de la page" : "Réduire le sommaire de la page";
    bouton.title = libelle;
    bouton.setAttribute("aria-label", libelle);
    texte.textContent = replie ? "Afficher le sommaire" : "Réduire le sommaire";
    texte.classList.toggle("fr-sr-only", replie); // libellé toujours accessible, visible seulement quand déplié
  }

  function init() {
    // Le sommaire d'une fiche API : <nav class="fr-sidemenu fr-sidemenu--sticky-full-height">,
    // distinct du panneau « Thèmes et filtres » (nav.catalogue-sidemenu) du catalogue.
    var nav = document.querySelector(".fr-sidemenu--sticky-full-height:not(.catalogue-sidemenu)");
    if (!nav) return;
    var colonne = nav.closest(".fr-col-md-3");
    if (!colonne) return;

    if (!nav.id) nav.id = "menu-lateral-sommaire";

    var bouton = document.createElement("button");
    bouton.type = "button";
    bouton.setAttribute("aria-controls", nav.id);
    var texte = document.createElement("span");
    texte.className = "menu-lateral-bouton__texte";
    bouton.appendChild(texte);
    nav.insertBefore(bouton, nav.firstChild);

    bouton.addEventListener("click", function () {
      var replie = !colonne.classList.contains("menu-lateral-col--repliee");
      appliquer(colonne, bouton, texte, replie);
      memoriser(replie);
    });

    appliquer(colonne, bouton, texte, repliePreferee());
  }

  // Exposée pour la version à page unique (tools/preview_app.js), qui rappelle cette fonction
  // après chaque changement de route puisque la page ne se recharge pas.
  window.__initMenuLateral = init;

  if (document.readyState === "complete") init();
  else window.addEventListener("load", init);
})();
