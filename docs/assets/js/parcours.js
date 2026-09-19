/* Parcours guidé « Trouver l'API adaptée à votre besoin » (page d'accueil).
   Délégation d'événements : fonctionne aussi quand le contenu est injecté dynamiquement. */
(function () {
  "use strict";

  var NOMS = { 1: "parcours-theme", 2: "parcours-acces", 3: "parcours-calendrier" };
  var MESSAGES = {
    1: "Choisissez un domaine, ou « Je ne sais pas encore ».",
    2: "Indiquez si vous pouvez demander un accès.",
    3: "Indiquez l'usage prévu."
  };

  function valeur(section, etape) {
    var input = section.querySelector('input[name="' + NOMS[etape] + '"]:checked');
    return input ? input.value : null;
  }

  function erreur(section, etape, afficher) {
    var fs = section.querySelector('[data-etape="' + etape + '"]');
    var zone = section.querySelector("#parcours-q" + etape + "-erreur");
    if (!fs || !zone) return;
    fs.classList.toggle("fr-fieldset--error", afficher);
    zone.innerHTML = afficher ? '<p class="fr-message fr-message--error">' + MESSAGES[etape] + "</p>" : "";
  }

  function libelle(section, etape) {
    var input = section.querySelector('input[name="' + NOMS[etape] + '"]:checked');
    if (!input) return "";
    var label = section.querySelector('label[for="' + input.id + '"]');
    return label ? label.childNodes[0].textContent.trim() : input.value;
  }

  function minuscule(t) { return t ? t.charAt(0).toLowerCase() + t.slice(1) : t; }

  function calculer(section) {
    var theme = valeur(section, 1), acces = valeur(section, 2), cal = valeur(section, 3);
    var n = 0;
    section.querySelectorAll(".parcours__api").forEach(function (li) {
      var ok = (theme === "*" || (li.dataset.themes || "").split(" ").indexOf(theme) !== -1) &&
        (acces === "toutes" || li.dataset.ouverte === "true") &&
        (cal === "tout" || li.dataset.statut === "production");
      li.hidden = !ok;
      if (ok) n++;
    });
    var futurs = 0;
    section.querySelectorAll(".parcours__futur").forEach(function (li) {
      var ok = theme !== "*" && li.dataset.theme === theme;
      li.hidden = !ok;
      if (ok) futurs++;
    });
    section.querySelector("[data-parcours-vide]").hidden = n !== 0;
    section.querySelector("[data-parcours-futurs]").hidden = futurs === 0;
    section.querySelector("[data-parcours-synthese]").innerHTML =
      "<strong>" + n + (n > 1 ? " API correspondent" : " API correspond") + "</strong> à vos critères : " +
      [libelle(section, 1), minuscule(libelle(section, 2)), minuscule(libelle(section, 3))].join(" ; ") + ".";
  }

  function aller(section, etape) {
    var etapes = JSON.parse(section.dataset.etapes);
    section.dataset.courante = etape;
    section.querySelectorAll(".parcours__etape").forEach(function (el) {
      el.hidden = Number(el.dataset.etape) !== etape;
    });
    section.querySelector(".fr-stepper__steps").setAttribute("data-fr-current-step", etape);
    section.querySelector("[data-parcours-titre]").textContent = etapes[etape - 1];
    section.querySelector("[data-parcours-etat]").textContent = "Étape " + etape + " sur " + etapes.length;
    var suivante = section.querySelector("[data-parcours-suivante]");
    suivante.hidden = etape === etapes.length;
    if (etape < etapes.length) {
      suivante.innerHTML = '<span class="fr-text--bold">Étape suivante :</span> ' + etapes[etape];
    }
    var btn = function (a) { return section.querySelector('[data-parcours-action="' + a + '"]'); };
    btn("precedent").hidden = etape === 1;
    btn("suivant").hidden = etape === etapes.length;
    btn("suivant").textContent = etape === etapes.length - 1 ? "Voir les API recommandées" : "Suivant";
    btn("recommencer").hidden = etape !== etapes.length;
    if (etape === etapes.length) calculer(section);

    var cible = section.querySelector('[data-etape="' + etape + '"]');
    var focus = etape === etapes.length ? cible : cible.querySelector("input:checked") || cible.querySelector("input");
    if (focus) focus.focus({ preventScroll: true });
    var top = section.getBoundingClientRect().top;
    if (top < 0) section.scrollIntoView({ block: "start" });
  }

  document.addEventListener("click", function (e) {
    var bouton = e.target.closest && e.target.closest("[data-parcours-action]");
    if (!bouton) return;
    var section = bouton.closest("[data-parcours]");
    var etape = Number(section.dataset.courante || 1);
    var action = bouton.dataset.parcoursAction;
    if (action === "suivant") {
      if (!valeur(section, etape)) { erreur(section, etape, true); return; }
      erreur(section, etape, false);
      aller(section, etape + 1);
    } else if (action === "precedent") {
      aller(section, Math.max(1, etape - 1));
    } else if (action === "recommencer") {
      section.querySelectorAll('input[type="radio"]').forEach(function (i) { i.checked = false; });
      aller(section, 1);
    }
  });

  document.addEventListener("change", function (e) {
    var section = e.target.closest && e.target.closest("[data-parcours]");
    if (!section) return;
    erreur(section, Number(section.dataset.courante || 1), false);
  });

  // Entrée dans un champ radio = étape suivante
  document.addEventListener("keydown", function (e) {
    if (e.key !== "Enter") return;
    var section = e.target.closest && e.target.closest("[data-parcours]");
    if (!section || e.target.type !== "radio") return;
    e.preventDefault();
    section.querySelector('[data-parcours-action="suivant"]').click();
  });
})();
