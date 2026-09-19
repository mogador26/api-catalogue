---
title: API Référentiel des services préfectoraux
resume: Liste à jour des préfectures, sous-préfectures et de leurs services, avec adresses, horaires et démarches traitées.
theme: referentiel
acces: [ouverte]
statut: production
version: "1.5"
url_base: https://api.exemple.gouv.fr/services-prefectoraux/v1
openapi: openapi/services-prefectoraux.yaml
picto: buildings/city-hall
mots_cles: [préfecture, sous-préfecture, guichet, horaires, adresse, annuaire]
demonstration: true
quota:
  requetes: 20
  periode: seconde
  portee: par adresse IP
producteur:
  nom: Secrétariat général (exemple)
  equipe: Équipe Référentiels
  contact: referentiels@exemple.gouv.fr
---

# API Référentiel des services préfectoraux

## Description fonctionnelle

L'API décrit chaque site préfectoral : identifiant stable, type (préfecture, sous-préfecture, antenne), adresse géolocalisée, horaires d'accueil, coordonnées et démarches traitées sur place. Elle permet de trouver le site compétent pour une commune et une démarche.

## Présentation pour les décideurs

De nombreux services en ligne orientent l'usager vers « sa » préfecture. Chacun maintenait sa propre liste d'adresses, rapidement obsolète. Un référentiel unique et ouvert garantit une information juste partout, et fait gagner du temps aux équipes qui n'ont plus à la mettre à jour.

## Cas d'usage

- Un téléservice indique à l'usager le site où déposer son dossier.
- Une carte interactive affiche les sites et leurs horaires.
- L'API Rendez-vous en préfecture, en préparation, s'appuie sur ces identifiants.

## Modalités d'accès

**API ouverte**, sans authentification. Données sous licence ouverte Etalab 2.0.

```bash
curl "https://api.exemple.gouv.fr/services-prefectoraux/v1/sites?code_commune=33063"
```

## Évolutions du produit

| Version | Date | Évolutions |
| --- | --- | --- |
| 1.5 | juin 2026 | Démarches traitées par site |
| 1.4 | déc. 2025 | Géolocalisation des sites |
| 1.0 | mai 2025 | Première publication |
