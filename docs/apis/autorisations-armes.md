---
title: API Vérification des autorisations d'armes
resume: Permettre aux armuriers de vérifier en temps réel qu'un client détient une autorisation valide avant une vente.
theme: armes
acces: [habilitation, oauth2]
statut: production
version: "2.1"
url_base: https://api.exemple.gouv.fr/armes/v2
openapi: openapi/autorisations-armes.yaml
picto: document/document-signature
mots_cles: [armes, armurier, autorisation, détention, vente, permis de chasser]
demonstration: true
quota:
  requetes: 300
  periode: minute
  portee: par établissement habilité
producteur:
  nom: Service central des armes (exemple)
  equipe: Équipe produit Armes
  contact: api-armes@exemple.gouv.fr
---

# API Vérification des autorisations d'armes

## Description fonctionnelle

L'API vérifie qu'une personne est autorisée à acquérir une arme d'une catégorie donnée. À partir de l'identifiant du détenteur et de la catégorie visée, elle renvoie une réponse simple : autorisé, non autorisé, ou vérification manuelle requise. Elle ne transmet aucune donnée personnelle au-delà de ce qui est nécessaire à la décision.

L'armurier peut ensuite déclarer la transaction afin que le registre de détention soit mis à jour sans ressaisie.

## Présentation pour les décideurs

La vente d'une arme à une personne non autorisée est un risque de sécurité publique majeur. Une vérification systématique et instantanée, intégrée au logiciel de caisse de l'armurier, supprime les contrôles papier et trace chaque consultation.

L'API réduit le délai de déclaration des ventes et fiabilise le registre national de détention.

## Cas d'usage

- 🏪 **Contrôler l'autorisation au moment de la vente**
    - Acteur : armurier
    - Description : au passage en caisse, le logiciel de l'armurier interroge l'API et affiche « autorisé », « non autorisé » ou « vérification manuelle requise ». Aucune pièce papier à contrôler.
    - Bénéfice : aucune vente à une personne non autorisée, contrôle tracé
- 💻 **Intégrer la vérification dans un logiciel métier**
    - Acteur : éditeur de logiciel pour armuriers
    - Description : l'éditeur intègre la vérification et la déclaration de vente dans son produit, pour tous ses clients habilités.
    - Bénéfice : un seul développement pour l'ensemble de la profession
- 🎯 **Vérifier les licences des tireurs sportifs**
    - Acteur : fédération sportive
    - Description : la fédération s'assure que les licenciés disposant d'une autorisation de détention la conservent en cours de validité.
    - Bénéfice : un suivi continu au lieu d'un contrôle annuel

## Modalités d'accès

L'accès nécessite une **habilitation préalable** : le demandeur justifie de son agrément de professionnel des armes. Une fois habilité, il obtient des identifiants client **OAuth2** (flux `client_credentials`) et un certificat pour l'authentification mutuelle TLS.

Chaque appel est journalisé avec l'identifiant de l'établissement.

## Évolutions du produit

| Version | Date | Évolutions |
| --- | --- | --- |
| 2.1 | mai 2026 | Réponse « vérification manuelle requise » avec motif codifié |
| 2.0 | nov. 2025 | Passage à OAuth2 et mTLS ; déclaration de vente |
| 1.0 | mars 2025 | Vérification simple par identifiant de détenteur |
