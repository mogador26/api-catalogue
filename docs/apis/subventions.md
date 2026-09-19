---
title: API Subventions
resume: Consulter les subventions versées aux collectivités et aux associations, par programme, bénéficiaire et année.
theme: finances
acces: [ouverte]
statut: depreciee
version: "1.4"
url_base: https://api.exemple.gouv.fr/subventions/v1
openapi: openapi/subventions.yaml
mots_cles: [subventions, budget, collectivités, transparence, données ouvertes]
demonstration: true
quota:
  requetes: 10
  periode: seconde
  portee: par adresse IP
producteur:
  nom: Direction des finances (exemple)
  equipe: Bureau des données budgétaires
  contact: donnees-budgetaires@exemple.gouv.fr
---

# API Subventions

## Description fonctionnelle

L'API publie les subventions attribuées : bénéficiaire (SIREN ou numéro RNA), programme budgétaire, montant attribué et versé, date de la décision et objet. Les données sont mises à jour chaque semaine et interrogeables par bénéficiaire, programme, département ou année.

## Présentation pour les décideurs

La transparence sur les aides publiques est une obligation légale et une attente forte des citoyens. L'API met ces données à disposition sans intermédiaire : journalistes, chercheurs et collectivités y accèdent directement, sans demande préalable.

Cette version est **dépréciée** : elle sera remplacée par l'API Aides publiques, annoncée dans la [feuille de route](../feuille-de-route.md). Elle reste disponible jusqu'à six mois après la mise en production de la nouvelle API.

## Cas d'usage

- Une collectivité suit les subventions qu'elle a reçues de l'État sur plusieurs exercices.
- Un média de données construit une carte des aides par département.
- Une association vérifie l'état de versement d'une subvention attribuée.

## Modalités d'accès

**API ouverte** : aucune authentification. Les données sont publiées sous licence ouverte Etalab 2.0. Limite : 10 requêtes par seconde par adresse IP.

```bash
curl "https://api.exemple.gouv.fr/subventions/v1/subventions?annee=2025&departement=69"
```

## Évolutions du produit

| Version | Date | Évolutions |
| --- | --- | --- |
| 1.4 | avr. 2026 | Annonce de dépréciation ; en-tête `Sunset` ajouté aux réponses |
| 1.3 | oct. 2025 | Filtre par département |
| 1.0 | janv. 2025 | Première publication |
