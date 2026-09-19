# =============================================================================
# Dockerfile pour le Catalogue des API
# - Génération du site statique via MkDocs
# - Exposition via Nginx
# - Conforme aux bonnes pratiques OWASP
# - Mode rootless (utilisateur non-root)
# =============================================================================

# -----------------------------------------------------------------------------
# Stage 1 : Build du site statique avec MkDocs
# -----------------------------------------------------------------------------
FROM python:3.12-slim-bookworm AS builder

# Définir un utilisateur non-root pour le build
RUN groupadd -r appuser && useradd -r -g appuser -u 1000 appuser

# Configurer l'environnement de build
ENV PYTHONFAULTHANDLER=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=randomized \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Installer les dépendances système nécessaires
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copier les fichiers de dépendances Python
WORKDIR /app
COPY requirements.txt .

# Installer les dépendances Python dans un virtualenv isolé
RUN python -m venv /opt/venv && \
    . /opt/venv/bin/activate && \
    pip install --no-cache-dir -r requirements.txt

# Copier le code source
COPY . .

# Builder le site statique
RUN . /opt/venv/bin/activate && \
    mkdocs build --strict --site-dir /static-site

# -----------------------------------------------------------------------------
# Stage 2 : Image finale avec Nginx rootless
# -----------------------------------------------------------------------------
FROM nginx:stable-alpine AS final

# Installer envsubst pour le templating de la configuration
RUN apk add --no-cache gettext && \
    rm -rf /var/cache/apk/*

# =============================================================================
# Configuration Rootless
# =============================================================================

# Créer un utilisateur non-root (même UID que le stage builder pour cohérence)
RUN addgroup -g 1000 appuser && \
    adduser -D -u 1000 -G appuser appuser

# Créer les répertoires nécessaires avec les bonnes permissions
RUN mkdir -p /var/www/html && \
    mkdir -p /var/cache/nginx && \
    mkdir -p /var/log/nginx && \
    mkdir -p /etc/nginx/conf.d && \
    mkdir -p /etc/nginx/snippets && \
    mkdir -p /run

# Copier la configuration Nginx sécurisée (template avec variables)
COPY docker-assets/nginx.conf.template /etc/nginx/nginx.conf.template
COPY docker-assets/security-headers.conf /etc/nginx/snippets/security-headers.conf

# Copier le site statique depuis le stage builder
COPY --from=builder --chown=appuser:appuser /static-site /var/www/html

# Changer le propriétaire de tous les répertoires nécessaires
RUN chown -R appuser:appuser /var/www/html && \
    chown -R appuser:appuser /var/cache/nginx && \
    chown -R appuser:appuser /var/log/nginx && \
    chown -R appuser:appuser /etc/nginx/conf.d && \
    chown -R appuser:appuser /etc/nginx/snippets && \
    chown appuser:appuser /etc/nginx/nginx.conf.template && \
    chown appuser:appuser /run

# Supprimer les permissions inutiles (sécurité OWASP)
RUN find /var/www/html -type f -exec chmod 644 {} \; && \
    find /var/www/html -type d -exec chmod 755 {} \; && \
    find /etc/nginx -type f -exec chmod 644 {} \; && \
    find /etc/nginx -type d -exec chmod 755 {} \;

# Basculer vers l'utilisateur non-root
USER appuser

# =============================================================================
# Configuration Nginx sécurisée
# =============================================================================

# Désactiver la gestion des processus par Nginx (rootless)
# Nginx en mode rootless ne peut pas bind sur des ports < 1024,
# donc on expose sur le port 8080 et on utilise un reverse proxy ou
# on mappe le port 8080:80 dans docker run
ENV NGINX_PORT=8080

# Désactiver les capabilities inutiles
# (sera géré par docker run --cap-drop)

# Exposer le port
EXPOSE 8080

# Healthcheck
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:8080/ || exit 1

# Commande d'exécution : utiliser envsubst pour remplacer ${NGINX_PORT} dans nginx.conf
CMD ["/bin/sh", "-c", "envsubst < /etc/nginx/nginx.conf.template > /etc/nginx/nginx.conf && nginx -g 'daemon off;' -c /etc/nginx/nginx.conf"]
