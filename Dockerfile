 # 1. Construction du site
FROM python:3.12-slim AS build
WORKDIR /src
COPY . .
RUN pip install --no-cache-dir -r requirements.txt \
 && mkdocs build --site-dir /site

# 2. Service par nginx non privilégié (utilisateur nginx, UID 101, port 8080)
FROM nginxinc/nginx-unprivileged:1.27-alpine
COPY --from=build /site /usr/share/nginx/html
USER 101
EXPOSE 8080