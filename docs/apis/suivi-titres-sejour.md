---
title: API Suivi des demandes de titre de séjour
resume: Donner à l'usager et aux structures qui l'accompagnent l'état d'avancement de sa demande de titre de séjour.
theme: etrangers
acces: [oauth2]
statut: beta
version: "0.9"
url_base: https://api.exemple.gouv.fr/titres-sejour/v1
openapi: openapi/suivi-titres-sejour.yaml
mots_cles: [titre de séjour, étrangers, demande, préfecture, suivi, récépissé]
demonstration: true
quota:
  requetes: 30
  periode: minute
  portee: par structure partenaire
  complement: "Pendant la bêta, quota révisable sur demande"
producteur:
  nom: Direction générale des étrangers en France (exemple)
  equipe: Équipe produit Démarches étrangers
  contact: api-etrangers@exemple.gouv.fr
---

# API Suivi des demandes de titre de séjour

## Description fonctionnelle

L'API renvoie l'état d'une demande de titre de séjour : dépôt, instruction, pièces complémentaires demandées, décision, titre disponible au retrait. Elle précise les pièces attendues le cas échéant et la date de fin de validité du récépissé.

L'usager consent explicitement à ce que la structure qui l'accompagne consulte son dossier ; le consentement est révocable à tout moment.

## Présentation pour les décideurs

L'attente d'information sur l'avancement d'un dossier génère une part importante des sollicitations des préfectures. Rendre ce suivi accessible aux associations d'aide aux étrangers et aux employeurs, avec l'accord de l'usager, réduit les déplacements en guichet et sécurise la continuité du droit au séjour.

## Cas d'usage

- Une association d'accompagnement suit les dossiers des personnes qu'elle aide.
- Un employeur vérifie, avec l'accord du salarié, qu'une demande de renouvellement est en cours.
- L'usager consulte l'état de sa demande depuis une application mobile.

## Modalités d'accès

Accès **OAuth2** en flux `authorization_code` : l'usager s'authentifie et donne son consentement, la structure obtient un jeton limité à son dossier (scope `demande:lecture`). Pendant la bêta, l'accès est réservé aux partenaires pilotes.

## Évolutions du produit

| Version | Date | Évolutions |
| --- | --- | --- |
| 0.9 | août 2026 | Bêta privée avec cinq structures partenaires ; gestion du consentement |
| 0.5 | avr. 2026 | Prototype interne |
