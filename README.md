# Catalogue des API

Catalogue d'API d'une administration, construit avec **MkDocs** et le thème **mkdocs-dsfr 0.26.1** (Système de design de l'État).

## Démarrer

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
mkdocs serve            # http://127.0.0.1:8000
mkdocs build --strict   # génère ./site et vérifie la complétude des fiches
```

Avant publication, renseignez `site_url` dans `mkdocs.yml` : il sert aux pictogrammes des tuiles DSFR.

## Docker

```bash
docker build -t catalogue-api  .
docker run --rm -p 8080:8080 catalogue-api
# → http://localhost:8080/   
```

- Construction en deux étapes : MkDocs (utilisateur `builder`, UID 10001) puis `nginxinc/nginx-unprivileged` (UID 101).
- Aucun processus root à l'exécution : port 8080, PID et fichiers temporaires dans `/tmp`, compatible système de fichiers en lecture seule.
- Le contenu du site appartient à root et n'est qu'en lecture pour nginx.
- Configuration : `docker/nginx.conf` (global) et `docker/catalogue.conf` (site : en-têtes de sécurité, CSP, cache, gzip, `/healthz`, page 404).

## Organisation

| Chemin | Rôle |
| --- | --- |
| `mkdocs.yml` | Configuration du site, du pied de page, des thèmes, des modalités d'accès et des statuts (`extra.catalogue`) |
| `docs/apis/*.md` | Une fiche Markdown par API (en-tête YAML + sections) |
| `docs/openapi/` | Spécifications OpenAPI locales |
| `data/feuille_de_route.yml` | Nouvelles API à venir, rendues en `gitGraph` Mermaid |
| `hooks/catalogue.py` | Génère le catalogue, les tuiles, les compteurs, les pages thèmes, la navigation, la feuille de route et les pages Redoc |
| `docs/assets/js/catalogue.js` | Filtres, rendu Redoc et Mermaid |
| `docs/assets/vendor/` | Redoc 2.5.4 et Mermaid 11.17.2 servis localement (aucun CDN) |
| `overrides/header.html`, `overrides/footer.html` | En-tête (mention BETA) et pied de page |
| `Dockerfile`, `docker/` | Image rootless nginx |
| `docs/assets/js/visite-guidee.js` | Visite guidée (accueil et fiche API), démarrage auto + bouton dans l'en-tête |

## Ajouter une API

Voir la page « Publier une API » du site (`docs/contribuer.md`). En résumé : déposer la spécification dans `docs/openapi/` (ou indiquer son URL), créer `docs/apis/mon-api.md` à partir du modèle, lancer `mkdocs build --strict`.

## Contenu

- **API Référentiel des applications** : fiche réelle, rédigée d'après le dépôt [dnum-mi/referentiel-applications](https://github.com/dnum-mi/referentiel-applications) (licence MIT). La spécification est chargée depuis GitHub, avec une copie locale de secours.
- Les **7 autres API sont fictives** (champ `demonstration: true`) et servent à illustrer les thèmes et modalités d'accès. Remplacez-les par vos propres API.

## Limites connues

- Le thème mkdocs-dsfr 0.26.1 produit une erreur JavaScript (`replaceAll`) dans la console sur toutes les pages. Elle est sans effet sur le catalogue.
- Redoc ne gère pas le mode sombre : la documentation reste sur fond clair.
- Une spécification chargée par URL exige que le serveur distant autorise les requêtes CORS.

## Version autonome (un seul fichier HTML)

```bash
mkdocs build && python tools/bundle_preview.py catalogue-preview.html
```

Toutes les pages sont intégrées dans un seul fichier, avec une navigation par ancre (`#/apis/…`). Redoc et Mermaid sont chargés depuis cdn.jsdelivr.net. Les boutons de téléchargement de spécification sont retirés de cette version.
