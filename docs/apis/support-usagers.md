---
title: API Support usagers
resume: Créer et suivre des demandes d'assistance depuis n'importe quel service numérique, avec un seul outil de traitement côté administration.
theme: support
acces: [api-key]
statut: production
version: "1.1"
url_base: https://api.exemple.gouv.fr/support/v1
openapi: openapi/support-usagers.yaml
mots_cles: [support, ticket, assistance, helpdesk, réclamation]
demonstration: true
quota:
  requetes: 60
  periode: minute
  portee: par clé d'API
producteur:
  nom: Direction du numérique (exemple)
  equipe: Équipe Support mutualisé
  contact: support-mutualise@exemple.gouv.fr
---

# API Support usagers

## Description fonctionnelle

L'API permet à un service numérique de créer une demande d'assistance au nom d'un usager ou d'un agent, d'y joindre des pièces, de suivre son état et de recevoir les réponses. Les demandes arrivent dans l'outil de traitement mutualisé, classées par service et par catégorie.

Un mécanisme de notification (webhook) informe le service appelant de chaque changement d'état.

## Présentation pour les décideurs

Chaque service numérique développait son propre formulaire de contact et sa propre boîte de réception. L'API mutualise le traitement : un seul outil pour les équipes de support, des indicateurs consolidés, et une expérience homogène pour l'usager quel que soit le service utilisé.

## Cas d'usage

- 🆘 **Signaler un problème depuis un téléservice**
    - Acteur : usager d'un service en ligne
    - Description : un bouton « Signaler un problème » crée une demande avec le contexte technique (page, navigateur, étape). L'usager n'a rien à réexpliquer.
    - Bénéfice : diagnostic plus rapide, usager rassuré
- 🧑‍💼 **Suivre ses demandes depuis l'intranet**
    - Acteur : agent
    - Description : l'agent retrouve dans son intranet toutes ses demandes au support informatique et leur état d'avancement.
    - Bénéfice : moins de relances auprès du support
- 🤖 **Passer le relais d'un robot conversationnel à un humain**
    - Acteur : service qui utilise un assistant conversationnel
    - Description : quand l'assistant ne sait pas répondre, il crée une demande qui reprend la conversation, traitée par un agent.
    - Bénéfice : aucune question sans réponse

## Modalités d'accès

Accès avec **clé d'API** transmise dans l'en-tête `X-API-Key`, une clé par service consommateur. Demande de clé auprès de l'équipe Support mutualisé, en précisant le service et les catégories de demandes souhaitées.

## Évolutions du produit

| Version | Date | Évolutions |
| --- | --- | --- |
| 1.1 | juil. 2026 | Notifications par webhook signées |
| 1.0 | févr. 2026 | Création, suivi et pièces jointes |
