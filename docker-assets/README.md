# Configuration Docker pour le Catalogue des API

## Structure

```
docker-assets/
├── nginx.conf.template     # Template de configuration Nginx (avec variables)
├── security-headers.conf  # Headers de sécurité OWASP
└── README.md               # Ce fichier
```

## Fichiers générés

- `Dockerfile` : Dockerfile principal multi-stage
- `.dockerignore` : Liste des fichiers à exclure du build

## Utilisation

### Build de l'image

```bash
# Builder l'image
docker build -t catalogue-api .

# Builder avec cache séparé (recommandé)
docker build --no-cache -t catalogue-api .
```

### Exécution du container

#### Mode développement (port 8080)

```bash
# Exécuter avec le port 8080 exposé
docker run -d -p 8080:8080 --name catalogue-api catalogue-api

# Accéder au site : http://localhost:8080
```

#### Mode production (port 80)

```bash
# Exécuter avec le port 80 exposé (nécessite --cap-drop pour la sécurité)
docker run -d -p 80:8080 --name catalogue-api \
    --cap-drop ALL \
    --read-only \
    catalogue-api

# Accéder au site : http://localhost
```

### Avec Docker Compose

Créer un fichier `docker-compose.yml` :

```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "8080:8080"
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
    read_only: true
    tmpfs:
      - /tmp:size=10M,mode=777
    restart: unless-stopped
```

### Commandes utiles

```bash
# Voir les logs
docker logs catalogue-api

# Arrêter le container
docker stop catalogue-api

# Supprimer le container
docker rm catalogue-api

# Inspecter le container
docker inspect catalogue-api

# Exécuter une commande dans le container
docker exec -it catalogue-api sh
```

## Sécurité appliquée

### Rootless
- L'image utilise un utilisateur non-root (`appuser` UID 1000)
- Nginx tourne avec les droits de cet utilisateur
- Tous les fichiers ont les permissions minimales nécessaires

### OWASP Top 10
1. **Injection** : Fichiers statiques, pas de traitement côté serveur
2. **Broken Authentication** : Pas d'authentification gérée par Nginx
3. **Sensitive Data Exposure** : HTTPS recommandé, headers de sécurité
4. **XML External Entities** : Pas de parsing XML côté serveur
5. **Broken Access Control** : Accès en lecture seule
6. **Security Misconfiguration** : Headers CSP, HSTS, etc.
7. **Cross-Site Scripting (XSS)** : CSP strict, X-XSS-Protection
8. **Insecure Deserialization** : Pas de désérialisation
9. **Using Components with Known Vulnerabilities** : Images officielles, mises à jour
10. **Insufficient Logging & Monitoring** : Logging JSON structuré

### Headers de sécurité
- `X-Frame-Options: DENY` - Protection contre le clickjacking
- `X-Content-Type-Options: nosniff` - Protection contre le MIME sniffing
- `X-XSS-Protection: 1; mode=block` - Filtre XSS du navigateur
- `Referrer-Policy: strict-origin-when-cross-origin` - Contrôle du Referer
- `Permissions-Policy` - Limitation des API navigateur
- `Content-Security-Policy` - CSP strict

### Configuration Nginx
- `server_tokens off` - Masquage de la version
- Limitation des méthodes HTTP (GET, HEAD, OPTIONS uniquement)
- Limitation du taux de requêtes (10 req/s par IP)
- Limitation des connexions simultanées (20 par IP)
- Timeouts courts pour prévenir les DoS
- Buffer sizes limités
- Désactivation de TRACE et TRACK

## Personnalisation

### Adapter le CSP

Le Content Security Policy dans `security-headers.conf` peut être ajusté selon les besoins :

```nginx
add_header Content-Security-Policy \
    "default-src 'self'; \
     script-src 'self' 'unsafe-inline' https://cdn.example.com; \
     style-src 'self' 'unsafe-inline' https://cdn.example.com; \
     ..."
```

### Activer HSTS

Pour un site en production avec HTTPS, décommenter dans `security-headers.conf` :

```nginx
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
```

### Modifier le port

Le port est configurable via la variable d'environnement `NGINX_PORT` :

```bash
# Exécuter avec un port différent
docker run -d -p 9000:9000 -e NGINX_PORT=9000 --name catalogue-api catalogue-api
```

Ou modifier la valeur par défaut dans le Dockerfile :

```dockerfile
ENV NGINX_PORT=9000
```

Note : Nginx en mode rootless ne peut pas binder sur les ports < 1024 sans capabilities supplémentaires.

## Résolution des problèmes

### Erreur de permissions

Si Nginx ne peut pas accéder aux fichiers, vérifier :
```bash
# Dans le container
docker exec -it catalogue-api ls -la /var/www/html
docker exec -it catalogue-api ls -la /etc/nginx
```

### Erreur de port

Nginx en mode rootless ne peut pas binder sur les ports < 1024. Utiliser :
- Un port > 1024 (8080, 8000, etc.)
- Un reverse proxy devant Nginx
- La commande `setcap` sur l'hôte (non recommandé)

### Build échoue

Vérifier que tous les fichiers nécessaires sont présents :
- `mkdocs.yml`
- `requirements.txt`
- `docs/`
- `overrides/`
- `hooks/`
