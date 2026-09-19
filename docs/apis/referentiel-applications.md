---
title: API Référentiel des applications
resume: Point de vérité unique sur les applications du ministère de l'Intérieur, leurs acteurs, leur conformité, leur hébergement et leur dette technique.
theme: referentiel
acces: [oauth2, api-key]
statut: production
version: "2.0"
url_base: https://<instance-refapp>/api/v2
openapi: https://raw.githubusercontent.com/dnum-mi/referentiel-applications/main/frontend/openapi/swagger.yaml
openapi_local: openapi/referentiel-applications.yaml
picto: digital/application
mots_cles: [refapp, canel, cartographie, applications, conformité, dette technique, indice de qualité, homologation]
quota: non communiqué
producteur:
  nom: DNUM, ministère de l'Intérieur
  equipe: Équipe produit RefApp
  contact: https://github.com/dnum-mi/referentiel-applications/issues
  support: https://github.com/dnum-mi/referentiel-applications
---

# API Référentiel des applications

## Description fonctionnelle

Le Référentiel des applications (RefApp) catalogue les applications numériques du ministère de l'Intérieur et en consolide les métadonnées. Il succède au service historique CANEL. Son API REST, exposée sous le préfixe `/api/v2`, donne accès à l'ensemble des fonctions du référentiel.

Pour chaque application, l'API permet de lire et de mettre à jour :

- le **statut** dans le cycle de vie, de la construction au décommissionnement ;
- les **acteurs** et leurs responsabilités : maîtrise d'ouvrage, maîtrise d'œuvre, exploitation, sécurité ;
- la **conformité** sur plusieurs axes : continuité, sécurité, protection des données, design, accessibilité, sobriété numérique ;
- l'**hébergement**, décrit de manière générique ;
- les **données** exposées ou consommées par l'application ;
- la **dette technique**, la maturité et les technologies utilisées, avec le suivi de leur fin de vie.

L'API calcule un **indice de qualité (IQ)** qui mesure la complétude de chaque fiche. Elle expose aussi les signalements, les abonnements, l'historique des modifications, les statistiques et la revue des corrélations entre applications.

Les listes sont paginées (`page`, `pageSize` jusqu'à 100) et renvoient la forme `{ "results": [...], "total": n }`. La recherche d'applications accepte des filtres riches : texte libre, étiquette, type ou courriel d'acteur, organisation, site d'hébergement, fiches incomplètes (sans MOA, sans MOE, sans hébergement), statut, bornes de dates.

## Présentation pour les décideurs

**Le problème.** Environ 2 700 applications composent le système d'information du ministère. Sans source unique, chaque direction tient ses propres inventaires, souvent incomplets et contradictoires. Préparer une homologation, un plan de continuité ou un arbitrage budgétaire demande alors des semaines de collecte.

**La réponse.** RefApp devient la référence partagée : une fiche par application, tenue à jour par les équipes qui la connaissent, et un indice de qualité qui rend visible l'effort de documentation restant. L'API permet aux autres outils du ministère de s'appuyer sur cette référence au lieu de recréer leurs propres listes.

**La valeur.**

- Moins de ressaisies : les outils de supervision, de support ou d'homologation lisent le référentiel au lieu de le dupliquer.
- Un pilotage objectivé : dette technique, conformité et fins de vie technologiques sont consolidées à l'échelle du ministère.
- Une trajectoire de plateforme : l'équipe prévoit des synchronisations avec d'autres systèmes du ministère et un accès en langage naturel (voir la [feuille de route](../feuille-de-route.md)).

**Pour qui.** Agents du ministère, équipes MOA et MOE, RSSI, exploitants, responsables de programmes et décideurs, avec des droits différenciés selon le rôle.

## Cas d'usage

- 🖥️ **Superviser les applications en production**
    - Acteur : équipe d'exploitation
    - Description : l'outil de supervision récupère chaque nuit la liste des applications en production, avec leurs exploitants et leur hébergement. Les alertes sont routées vers la bonne équipe sans maintenir de liste en double.
    - Bénéfice : incidents attribués plus vite, inventaire toujours à jour
    - Opérations : `GET /applications` filtré par statut
- 🛡️ **Préparer un dossier d'homologation**
    - Acteur : RSSI, responsable de la sécurité
    - Description : le RSSI rassemble en une requête les acteurs, l'hébergement, les données traitées et l'état de conformité d'une application. Le dossier d'homologation part d'une base fiable au lieu d'un questionnaire à remplir.
    - Bénéfice : plusieurs jours de collecte évités par dossier
    - Opérations : `GET /applications/{id}` et sous-ressources
- 📉 **Piloter la dette technique d'un portefeuille**
    - Acteur : responsable de programme, direction du numérique
    - Description : les statistiques consolidées montrent les applications exposées à une fin de vie technologique et leur niveau de maturité. Les arbitrages budgétaires s'appuient sur des données partagées.
    - Bénéfice : priorisation objectivée des chantiers de modernisation
    - Opérations : statistiques, suivi des fins de vie
- 📝 **Lancer une campagne de mise à jour des fiches**
    - Acteur : administrateur fonctionnel
    - Description : les filtres « sans MOA », « sans MOE » ou « sans hébergement » et l'indice de qualité identifient les fiches incomplètes. L'administrateur relance les bonnes équipes.
    - Bénéfice : un référentiel plus complet, donc plus utile à tous
    - Opérations : filtres `missingMoa`, `missingMoe`, `missingHosting`, indice de qualité
- 🔄 **Synchroniser les acteurs depuis un annuaire**
    - Acteur : intégrateur du système d'information
    - Description : un traitement automatique met à jour les responsables d'une application quand l'annuaire change. Plus de fiches pointant vers des agents partis.
    - Bénéfice : des contacts fiables sans saisie manuelle
    - Opérations : endpoints acteurs, jeton de service

## Modalités d'accès

L'API n'est pas ouverte : toutes les routes métier exigent une authentification. Deux mécanismes sont déclarés dans la spécification.

**OAuth2 / OpenID Connect (flux C2B, utilisateur humain).** Le client obtient un jeton auprès du fournisseur d'identité de l'organisation (Authorization Code Flow avec PKCE, scopes `openid` et `profile`) et le transmet dans l'en-tête `Authorization`. Le backend vérifie la signature du jeton ; l'adresse électronique sert d'identifiant. Depuis la version 1.91, une **authentification forte** est exigée : une session de niveau insuffisant reçoit une réponse `403` avec `strongAuthRequired: true`.

```bash
curl -H "Authorization: Bearer $JETON_OIDC" \
  "https://<instance-refapp>/api/v2/applications?page=0&pageSize=20"
```

**Clé d'API (flux B2B, machine à machine).** Un jeton de service ou un jeton personnel est transmis dans l'en-tête `x-refapp-token`. Le jeton est rattaché à un utilisateur et hérite de ses permissions.

```bash
curl -H "x-refapp-token: $JETON_SERVICE" \
  "https://<instance-refapp>/api/v2/applications?search=messagerie"
```

**Obtenir un accès.** Les jetons sont délivrés par les administrateurs du référentiel. Les droits reposent sur une matrice de permissions par rôle et par périmètre ; l'endpoint `GET /applications/{id}/my-perms` indique les droits effectifs sur une application.

## Évolutions du produit

| Version | Date | Évolutions notables |
| --- | --- | --- |
| 1.91.0 | 14 sept. 2026 | Authentification forte exigée pour tous les accès ; alerte lorsque l'utilisateur ne peut pas lire toutes les données d'une fiche |
| 1.90.0 | 3 sept. 2026 | Refonte du panneau d'administration ; saisie manuelle de la fin de vie d'une technologie ; campagnes IQ enrichies |
| 1.89.0 | 31 août 2026 | Filtres sauvegardés ; traçabilité de l'impersonation ; corrections de cloisonnement entre fiches |
| 1.88.0 | 26 août 2026 | Moteur de détection de corrélations entre applications (suggestions à accepter ou rejeter) ; campagnes d'indice de qualité |
| 1.87.0 | 17 août 2026 | Mode maintenance en lecture seule ; historique des envois de courriels et des changements de permissions |
| 1.85.0 | 24 juil. 2026 | Rattachement à plusieurs directions métier ; fréquence de mise à jour « jamais » dans le catalogue de données |

Prochaines étapes annoncées par l'équipe : gestion fine des droits par périmètre, import et export Excel en masse, serveur MCP et recherche assistée, intégrations avec d'autres systèmes du ministère. Historique complet : [CHANGELOG du dépôt](https://github.com/dnum-mi/referentiel-applications/blob/main/CHANGELOG.md).
