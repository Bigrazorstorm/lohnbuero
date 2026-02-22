# ── Stage 1: React-App bauen ─────────────────────────────────
FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

# ── Stage 2: Production-Server mit nginx ──────────────────────
FROM nginx:alpine
# Statische Dateien aus Build-Stage kopieren
COPY --from=build /app/dist /usr/share/nginx/html
# nginx-Template; wird beim Start via envsubst befuellt
# (offizielles nginx-Image unterstuetzt /etc/nginx/templates/ nativ)
COPY nginx.conf.template /etc/nginx/templates/default.conf.template
EXPOSE 80
