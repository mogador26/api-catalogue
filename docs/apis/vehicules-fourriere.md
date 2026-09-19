---
title: API Véhicules en fourrière
resume: Savoir si un véhicule a été mis en fourrière, où il se trouve et comment le récupérer.
theme: transport
acces: [api-key]
statut: production
version: "1.3"
url_base: https://api.exemple.gouv.fr/fourriere/v1
openapi: openapi/vehicules-fourriere.yaml
mots_cles: [fourrière, immatriculation, enlèvement, stationnement, assurance]
demonstration: true
quota:
  requetes: 20
  periode: seconde
  portee: par clé d'API
  complement: "Plafond journalier : 50 000 appels par clé"
producteur:
  nom: Direction de la sécurité routière (exemple)
  equipe: Équipe produit Fourrières
  contact: api-fourriere@exemple.gouv.fr
---

# API Véhicules en fourrière

## Description fonctionnelle

L'API indique, à partir d'un numéro d'immatriculation, si un véhicule fait l'objet d'une mise en fourrière en cours. Elle renvoie la fourrière de rattachement (adresse, horaires, contact), la date d'enlèvement, le motif, la catégorie de frais applicable et l'état de la procédure : enlevé, en attente de mainlevée, restituable, remis au service des domaines.

Un second service permet aux fourrières agréées de publier les changements d'état d'un dossier.

## Présentation pour les décideurs

Chaque année, des milliers d'usagers appellent commissariats et mairies pour retrouver un véhicule enlevé. L'API permet d'apporter cette réponse directement dans les services numériques qui les accompagnent déjà : application d'assurance, service d'assistance, portail municipal.

Moins d'appels entrants, des frais de garde réduits pour l'usager qui récupère son véhicule plus tôt, et des fourrières qui libèrent de la place plus vite.

## Cas d'usage

- Un assureur affiche dans son application l'emplacement du véhicule de son assuré et les pièces à apporter.
- Une commune intègre la recherche sur son site pour répondre aux usagers sans passer par l'accueil téléphonique.
- Une fourrière agréée met à jour l'état des dossiers depuis son logiciel de gestion.

## Modalités d'accès

Accès avec **clé d'API** transmise dans l'en-tête `X-API-Key`. La clé est délivrée après signature des conditions générales d'utilisation, sur demande auprès du producteur. Quotas : 20 requêtes par seconde et 50 000 requêtes par jour par clé.

```bash
curl -H "X-API-Key: $CLE" https://api.exemple.gouv.fr/fourriere/v1/vehicules/AB-123-CD
```

## Évolutions du produit

| Version | Date | Évolutions |
| --- | --- | --- |
| 1.3 | juin 2026 | Horaires d'ouverture des fourrières et catégories de frais |
| 1.2 | janv. 2026 | Publication des changements d'état par les fourrières agréées |
| 1.0 | sept. 2025 | Ouverture du service de consultation |
