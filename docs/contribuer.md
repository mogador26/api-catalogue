---
title: Publier une API
sidemenu: false
---

# Publier une API dans le catalogue

Une API est décrite par un seul fichier Markdown placé dans `docs/apis/`. Le nom du fichier devient l'identifiant de l'API dans l'URL. Le catalogue, les pages thématiques, les compteurs et le menu sont mis à jour automatiquement à la construction du site.

## Étape 1 : déposer la spécification OpenAPI

Deux options :

- **Fichier local** : copiez la spécification (YAML ou JSON, OpenAPI 3) dans `docs/openapi/` et indiquez `openapi: openapi/mon-api.yaml`.
- **URL** : indiquez l'URL publique de la spécification, par exemple `openapi: https://exemple.fr/api/openapi.yaml`. Le serveur doit autoriser les requêtes CORS. Ajoutez `openapi_local` pour afficher une copie locale si l'URL ne répond pas.

La documentation est rendue avec Redoc, servi localement depuis `docs/assets/vendor/`. Une page Redoc en pleine page est également publiée pour chaque API.

## Étape 2 : créer la fiche

Copiez le modèle ci-dessous dans `docs/apis/mon-api.md`.

```markdown
---
title: API Mon service
resume: Une phrase qui dit ce que l'API permet de faire.
theme: referentiel            # un ou plusieurs thèmes (liste)
acces: [oauth2, api-key]      # ouverte | api-key | oauth2 | habilitation
statut: production            # production | beta | depreciee
version: "1.0"
url_base: https://api.exemple.gouv.fr/v1
openapi: openapi/mon-api.yaml # chemin local ou URL
openapi_local:                # facultatif : copie locale de secours
picto: digital/coding         # facultatif : pictogramme DSFR (sinon celui du thème)
mots_cles: [recherche, exemple]
quota:                        # appels autorisés par client (ou : quota: non communiqué)
  requetes: 50
  periode: seconde            # seconde | minute | heure | jour
  portee: par clé d'API       # facultatif (défaut : par client)
  complement: Plafond journalier de 100 000 appels   # facultatif
producteur:
  nom: Direction productrice
  equipe: Équipe produit
  contact: equipe-api@exemple.gouv.fr   # adresse ou URL
  support: https://support.exemple.gouv.fr
---

# API Mon service

## Description fonctionnelle
## Présentation pour les décideurs
## Cas d'usage
## Modalités d'accès
## Évolutions du produit
```

Les cinq sections sont obligatoires. Sont ajoutés automatiquement :

- en haut, la fiche d'identité (badges, résumé, producteur, URL de base) ;
- à droite, le panneau d'accès : API ouverte ou soumise à contrôle, types d'accès, liens vers le swagger, contact du producteur et nombre d'appels autorisés par client ;
- en bas, la documentation OpenAPI (Redoc). Pour la placer ailleurs, insérez le marqueur `<!-- openapi -->`.

## Étape 3 : vérifier

```bash
mkdocs build --strict
```

La construction échoue si une métadonnée ou une section obligatoire manque (y compris le quota), ou si un thème ou une modalité d'accès n'est pas déclaré dans `mkdocs.yml` (rubrique `extra.catalogue`).

## Ajouter un thème ou une modalité d'accès

Déclarez-les dans `mkdocs.yml`, rubrique `extra.catalogue.themes` ou `extra.catalogue.acces`. Une modalité marquée `ouverte: true` est comptée parmi les API ouvertes ; toutes les autres sont comptées parmi les API avec authentification.

## Annoncer une nouvelle API

Ajoutez un projet dans `data/feuille_de_route.yml`. Il apparaît dans la feuille de route du catalogue sous la forme d'une branche du graphe.
