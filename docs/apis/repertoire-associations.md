---
title: API Répertoire des associations
resume: Retrouver une association, son objet, son siège et ses dirigeants déclarés à partir de son numéro RNA ou de son nom.
theme: entreprises-associations
acces: [ouverte]
statut: production
version: "3.0"
url_base: https://api.exemple.gouv.fr/associations/v3
openapi: openapi/repertoire-associations.yaml
mots_cles: [associations, RNA, loi 1901, siège, objet social, SIREN]
demonstration: true
quota:
  requetes: 7
  periode: seconde
  portee: par adresse IP
producteur:
  nom: Direction des libertés publiques (exemple)
  equipe: Équipe produit Associations
  contact: api-associations@exemple.gouv.fr
---

# API Répertoire des associations

## Description fonctionnelle

L'API expose les informations publiques des associations déclarées : numéro RNA, SIREN le cas échéant, titre, objet social, adresse du siège, date de création, dernière déclaration et état (active ou dissoute). Elle propose une recherche plein texte et une recherche par identifiant.

## Présentation pour les décideurs

Les associations remplissent sans cesse les mêmes informations dans leurs demandes de subvention, d'agrément ou de partenariat. En interrogeant l'API, les services instructeurs préremplissent ces formulaires et vérifient l'existence de l'association : moins de pièces justificatives, moins d'erreurs, des dossiers traités plus vite.

## Cas d'usage

- 📋 **Préremplir une demande de subvention**
    - Acteur : service instructeur, association
    - Description : l'association saisit son numéro RNA ; le portail récupère son titre, son objet et son siège.
    - Bénéfice : moins de saisie et moins d'erreurs dans les dossiers
- ✅ **Vérifier qu'une association est active**
    - Acteur : collectivité qui prête une salle ou un équipement
    - Description : avant de signer une convention, l'agent contrôle que l'association est bien déclarée et n'a pas été dissoute.
    - Bénéfice : sécurisation juridique des conventions
- 🙋 **Afficher des fiches associations vérifiées**
    - Acteur : plateforme de bénévolat
    - Description : chaque association présente sur la plateforme est rattachée à sa fiche officielle, mise à jour automatiquement.
    - Bénéfice : confiance des bénévoles dans les structures présentées

## Modalités d'accès

**API ouverte**, sans authentification. Données publiées sous licence ouverte Etalab 2.0. Limite : 7 requêtes par seconde par adresse IP.

```bash
curl "https://api.exemple.gouv.fr/associations/v3/associations/W751234567"
```

## Évolutions du produit

| Version | Date | Évolutions |
| --- | --- | --- |
| 3.0 | mars 2026 | Recherche plein texte ; pagination par curseur (rupture de compatibilité) |
| 2.2 | sept. 2025 | Ajout du SIREN lorsqu'il existe |
| 2.0 | févr. 2025 | Historique des déclarations |
