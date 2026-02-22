# Docker Hosting Guide - AOM auf eigenem VPS/Server

Vollständige Anleitung zum Deployen der Addison Operations Manager (AOM) Anwendung auf einem VPS mit Docker und Git.

---

## 📋 Inhaltsverzeichnis

1. [VPS-Setup](#vps-setup)
2. [Docker Installation](#docker-installation)
3. [Repository klonen](#repository-klonen)
4. [Docker Compose starten](#docker-compose-starten)
5. [Produktions-Konfiguration](#produktions-konfiguration)
6. [SSL/HTTPS mit Let's Encrypt](#ssltlshttps-mit-lets-encrypt)
7. [Reverse Proxy (Nginx)](#reverse-proxy-nginx)
8. [Automatische Updates via Git](#automatische-updates-via-git)
9. [Monitoring & Logs](#monitoring--logs)
10. [Backup & Restore](#backup--restore)
11. [Troubleshooting](#troubleshooting)

---

## VPS-Setup

### Empfohlene Provider & Specs

| Provider | OS | RAM | CPU | Preis | Link |
|----------|----|----|-----|-------|------|
| **Hetzner** | Ubuntu 22.04 | 2GB | 2 vCPU | €3-5/Mo | hetzner.com |
| **Linode** | Ubuntu 22.04 | 2GB | 2 vCPU | €5/Mo | linode.com |
| **DigitalOcean** | Ubuntu 22.04 | 2GB | 2 vCPU | €5/Mo | digitalocean.com |
| **Vultr** | Ubuntu 22.04 | 2GB | 2 vCPU | €2.50/Mo | vultr.com |

**Minimum für AOM**: 2GB RAM, 2 CPU, 20GB SSD

### Initiales Setup (Root SSH)

```bash
# SSH verbinden
ssh root@your-vps-ip

# System updaten
apt update && apt upgrade -y

# Neue User erstellen (nicht als root arbeiten!)
adduser appuser
usermod -aG sudo appuser

# SSH-Key Setup für neue User
su - appuser
mkdir -p ~/.ssh
cat >> ~/.ssh/authorized_keys << EOF
your-public-ssh-key-here
EOF
chmod 600 ~/.ssh/authorized_keys
```

### Firewall konfigurieren (UFW)

```bash
# UFW aktivieren
sudo ufw enable

# SSH öffnen (WICHTIG - vor Enable!)
sudo ufw allow 22/tcp

# HTTP & HTTPS öffnen
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Optional: Backend-Port nur intern
sudo ufw allow from 127.0.0.1 to 127.0.0.1 port 8000

# Status prüfen
sudo ufw status
```

---

## Docker Installation

```bash
# Loggiere dich als appuser ein
su - appuser

# Docker installieren (offizielle Methode)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# appuser zu docker-group hinzufügen (sudo nicht immer nötig)
sudo usermod -aG docker $USER
newgrp docker

# Test
docker --version
docker run hello-world
```

### Docker Compose installieren

```bash
# Latest Version finden unter: github.com/docker/compose/releases
DOCKER_COMPOSE_VERSION=2.24.0

sudo curl -L "https://github.com/docker/compose/releases/download/v${DOCKER_COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Test
docker-compose --version
```

---

## Repository klonen

```bash
# Ins Home-Directory gehen
cd ~

# Repository klonen
git clone https://github.com/your-username/lohnbuero.git
cd lohnbuero

# Branch auschecken (optional)
git checkout main
```

### SSH-Key für Git setup (für Auto-Updates)

```bash
# SSH-Key generieren
ssh-keygen -t ed25519 -C "appuser@aom-server"
# → Speichern als ~/.ssh/github_deploy

# Public Key anzeigen
cat ~/.ssh/github_deploy.pub
# → In GitHub → Settings → Deploy Keys eintragen

# SSH Config eintragen
cat >> ~/.ssh/config << EOF
Host github.com
    IdentityFile ~/.ssh/github_deploy
    IdentitiesOnly yes
EOF
chmod 600 ~/.ssh/config

# Git remote auf SSH umstellen
git remote set-url origin git@github.com:your-username/lohnbuero.git

# Test
git fetch origin
```

---

## Docker Compose starten

### 1. Produktions-Konfiguration erstellen

Erstelle `.env` Datei im Projekt-Root:

```bash
cat > /home/appuser/lohnbuero/.env << 'EOF'
# === Backend ===
SECRET_KEY=your-super-secure-random-key-min-32-characters-change-this-now
DATABASE_URL=sqlite:///./db/aom.db
CORS_ORIGINS=https://aom.yourdomain.com,https://www.aom.yourdomain.com
LOG_LEVEL=info
ENVIRONMENT=production

# === Frontend ===
VITE_API_URL=https://aom.yourdomain.com/api

# === Database ===
POSTGRES_USER=aom_user
POSTGRES_PASSWORD=your-secure-db-password-min-16-chars
POSTGRES_DB=aom_db
EOF

# Permissions setzen
chmod 600 /home/appuser/lohnbuero/.env
```

**Wichtig**: Setze `SECRET_KEY` und `POSTGRES_PASSWORD` auf echte zufällige Werte!

```bash
# Zufällige Keys generieren
openssl rand -base64 32  # für SECRET_KEY
openssl rand -base64 16  # für POSTGRES_PASSWORD
```

### 2. Produktions-docker-compose.yml vorbereiten

Im Repository ist bereits `docker-compose.yml` vorhanden. Für Production erstelle `docker-compose.prod.yml`:

```bash
cat > /home/appuser/lohnbuero/docker-compose.prod.yml << 'EOF'
version: "3.9"

services:
  # ─── Backend ───────────────────────────────────────
  backend:
    build: ./backend
    container_name: aom-backend
    restart: always
    ports:
      - "127.0.0.1:8000:8000"  # Nur localhost
    volumes:
      - ./db:/app/db
      - ./uploads:/app/uploads
    environment:
      DATABASE_URL: ${DATABASE_URL}
      SECRET_KEY: ${SECRET_KEY}
      CORS_ORIGINS: ${CORS_ORIGINS}
      LOG_LEVEL: ${LOG_LEVEL}
      ENVIRONMENT: ${ENVIRONMENT}
    depends_on:
      - postgres
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/docs"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    networks:
      - aom-network

  # ─── Frontend ───────────────────────────────────────
  frontend:
    build:
      context: ./frontend
      args:
        VITE_API_URL: ${VITE_API_URL}
    container_name: aom-frontend
    restart: always
    ports:
      - "127.0.0.1:3000:80"  # Nur localhost
    depends_on:
      - backend
    healthcheck:
      test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://localhost/"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - aom-network

  # ─── PostgreSQL (Optional - für Production) ───────
  postgres:
    image: postgres:15-alpine
    container_name: aom-postgres
    restart: always
    ports:
      - "127.0.0.1:5432:5432"  # Nur localhost
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backups:/backups
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - aom-network

volumes:
  postgres_data:
    driver: local
  uploads:
    driver: local

networks:
  aom-network:
    driver: bridge
EOF
```

### 3. Docker Compose starten

```bash
cd /home/appuser/lohnbuero

# Images bauen
docker-compose -f docker-compose.prod.yml build

# Services starten
docker-compose -f docker-compose.prod.yml up -d

# Status prüfen
docker-compose -f docker-compose.prod.yml ps

# Logs anschauen
docker-compose -f docker-compose.prod.yml logs -f
```

---

## Produktions-Konfiguration

### Datenbank auf PostgreSQL upgraden

Backend unterstützt beide (SQLite + PostgreSQL). Um auf PostgreSQL zu wechseln:

1. Installiere PostgreSQL Adapter:

```bash
echo "psycopg2-binary==2.9.9" >> backend/requirements.txt
```

2. Docker Compose wird PostgreSQL automatisch starten (wenn `postgres` Service vorhanden)

3. Backend erkennt `DATABASE_URL` automatisch und nutzt PostgreSQL

### Env-Variablen pro Environment

```bash
# Development
docker-compose -f docker-compose.yml up -d

# Production
docker-compose -f docker-compose.prod.yml up -d
```

---

## SSL/TLS/HTTPS mit Let's Encrypt

### Certbot installieren

```bash
sudo apt install certbot python3-certbot-nginx -y
```

### Zertifikat erstellen

```bash
sudo certbot certonly --standalone \
  -d aom.yourdomain.com \
  -d www.aom.yourdomain.com \
  --email your-email@example.com \
  --agree-tos \
  --non-interactive
```

Zertifikat ist jetzt unter:
- `/etc/letsencrypt/live/aom.yourdomain.com/fullchain.pem`
- `/etc/letsencrypt/live/aom.yourdomain.com/privkey.pem`

### Auto-Renewal aktivieren

```bash
sudo certbot renew --dry-run  # Test
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer

# Status
sudo systemctl status certbot.timer
```

---

## Reverse Proxy (Nginx)

### Nginx installieren

```bash
sudo apt install nginx -y
```

### Nginx Config erstellen

```bash
sudo tee /etc/nginx/sites-available/aom > /dev/null << 'EOF'
upstream backend {
    server 127.0.0.1:8000;
}

upstream frontend {
    server 127.0.0.1:3000;
}

server {
    listen 80;
    server_name aom.yourdomain.com www.aom.yourdomain.com;

    # Redirect HTTP → HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name aom.yourdomain.com www.aom.yourdomain.com;

    # SSL Zertifikate
    ssl_certificate /etc/letsencrypt/live/aom.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/aom.yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Logging
    access_log /var/log/nginx/aom_access.log;
    error_log /var/log/nginx/aom_error.log;

    # Timeouts
    client_max_body_size 100M;
    proxy_connect_timeout 600s;
    proxy_send_timeout 600s;
    proxy_read_timeout 600s;

    # Frontend
    location / {
        proxy_pass http://frontend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Backend API
    location /api/ {
        proxy_pass http://backend/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Health Check
    location /health {
        return 200 "OK";
        add_header Content-Type text/plain;
    }
}
EOF
```

### Nginx aktivieren & starten

```bash
# Config prüfen
sudo nginx -t

# Enable
sudo ln -sf /etc/nginx/sites-available/aom /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Restart
sudo systemctl restart nginx
sudo systemctl enable nginx

# Status
sudo systemctl status nginx
```

---

## Automatische Updates via Git

### Auto-Update Script

Erstelle `/home/appuser/lohnbuero/deploy.sh`:

```bash
#!/bin/bash

# Logging
LOG_FILE="/home/appuser/lohnbuero/deploy.log"
exec > >(tee -a "$LOG_FILE")
exec 2>&1

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting deployment..."

cd /home/appuser/lohnbuero

# Git Pull
git fetch origin
git pull origin main

if [ $? -ne 0 ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Git pull failed!"
    exit 1
fi

# Docker rebuild
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d

# Cleanup old images
docker image prune -f

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Deployment finished!"
```

Executable machen:
```bash
chmod +x /home/appuser/lohnbuero/deploy.sh
```

### Cron Job für automatische Updates

```bash
# Crontab öffnen
crontab -e

# Folgende Zeile einfügen (täglich um 2 Uhr):
0 2 * * * /home/appuser/lohnbuero/deploy.sh >> /home/appuser/lohnbuero/cron.log 2>&1
```

### Manueller Deploy

```bash
/home/appuser/lohnbuero/deploy.sh
```

---

## Monitoring & Logs

### Docker Container Status

```bash
# Alle Container prüfen
docker ps -a

# Spezifischer Container
docker-compose -f docker-compose.prod.yml ps

# Container restarten
docker-compose -f docker-compose.prod.yml restart backend
```

### Logs anschauen

```bash
# Live Logs (alle Services)
docker-compose -f docker-compose.prod.yml logs -f

# Nur Backend
docker-compose -f docker-compose.prod.yml logs -f backend

# Nur Frontend
docker-compose -f docker-compose.prod.yml logs -f frontend

# Nur PostgreSQL
docker-compose -f docker-compose.prod.yml logs -f postgres

# Letzte 100 Zeilen
docker-compose -f docker-compose.prod.yml logs --tail=100 backend
```

### Nginx Logs

```bash
# Live Access Log
sudo tail -f /var/log/nginx/aom_access.log

# Errors
sudo tail -f /var/log/nginx/aom_error.log
```

### System Monitoring

```bash
# CPU & Memory
docker stats

# Disk Space
df -h

# PostgreSQL Backup
docker-compose -f docker-compose.prod.yml exec -T postgres \
  pg_dump -U aom_user aom_db > backup_$(date +%Y-%m-%d).sql
```

---

## Backup & Restore

### PostgreSQL Backup automatisieren

Erstelle `/home/appuser/lohnbuero/backup.sh`:

```bash
#!/bin/bash

BACKUP_DIR="/home/appuser/lohnbuero/backups"
TIMESTAMP=$(date +%Y-%m-%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/aom_backup_$TIMESTAMP.sql.gz"

mkdir -p "$BACKUP_DIR"

# Backup erstellen
docker-compose -f docker-compose.prod.yml exec -T postgres \
  pg_dump -U aom_user aom_db | gzip > "$BACKUP_FILE"

# Alte Backups (älter als 30 Tage) löschen
find "$BACKUP_DIR" -name "*.sql.gz" -mtime +30 -delete

echo "Backup erstellt: $BACKUP_FILE"
```

Executable machen:
```bash
chmod +x /home/appuser/lohnbuero/backup.sh
```

Cron Job für tägliche Backups:
```bash
# Crontab öffnen
crontab -e

# Um 3 Uhr morgens täglich
0 3 * * * /home/appuser/lohnbuero/backup.sh >> /home/appuser/lohnbuero/backup.log 2>&1
```

### Backup auf externen Storage (S3/Backblaze)

```bash
# awscli installieren
sudo apt install awscli -y

# Backup-Script mit S3 Upload
cat >> /home/appuser/lohnbuero/backup.sh << 'EOF'

# S3 Upload
aws s3 cp "$BACKUP_FILE" s3://your-bucket/aom-backups/ \
  --region your-region

echo "Backup uploaded to S3"
EOF
```

### Restore aus Backup

```bash
# Backup File auswählen
BACKUP_FILE="/home/appuser/lohnbuero/backups/aom_backup_2024-02-22_030000.sql.gz"

# Restore
gunzip < "$BACKUP_FILE" | docker-compose -f docker-compose.prod.yml exec -T postgres \
  psql -U aom_user aom_db
```

---

## Troubleshooting

### Problem: Container startet nicht

```bash
# Logs prüfen
docker-compose -f docker-compose.prod.yml logs backend

# Container einzeln prüfen
docker run -it --rm lohnbuero-backend python -c "import app"

# Container im Debug-Modus starten
docker-compose -f docker-compose.prod.yml up backend
```

### Problem: "Port already in use"

```bash
# Port 8000 nutzer finden
sudo lsof -i :8000

# Container mit Gewalt stoppen
docker-compose -f docker-compose.prod.yml down
docker system prune -f
```

### Problem: "Cannot connect to Docker daemon"

```bash
# Docker Status
sudo systemctl status docker

# Docker starten
sudo systemctl start docker

# appuser ist in docker-group?
groups $USER
# Falls nicht:
sudo usermod -aG docker $USER
newgrp docker
```

### Problem: Frontend zeigt keine Daten

```bash
# API URL in Frontend prüfen
docker-compose -f docker-compose.prod.yml exec frontend \
  grep -r "VITE_API_URL" .

# Backend erreichbar vom Container?
docker-compose -f docker-compose.prod.yml exec frontend \
  curl http://backend:8000/docs
```

### Problem: Out of Memory

```bash
# Speicher prüfen
free -h

# Docker Memory-Limits setzen
docker-compose -f docker-compose.prod.yml down

# In docker-compose.prod.yml:
# backend:
#   mem_limit: 512m
#   mem_reservation: 256m
```

### Problem: Disk Space voll

```bash
# Disk Nutzung prüfen
df -h

# Docker Cleanup
docker system prune -a --volumes  # Achtung: löscht viele Images!

# Logfiles rotieren
sudo logrotate -f /etc/logrotate.conf
```

---

## Sicherheit Checkliste

- [ ] SSH-Key-Auth aktiviert, Password-Auth deaktiviert
- [ ] UFW Firewall konfiguriert
- [ ] .env Datei mit `chmod 600` geschützt
- [ ] SECRET_KEY auf 32+ zufällige Zeichen setzen
- [ ] CORS_ORIGINS auf spezifische Domains (nicht `*`)
- [ ] PostgreSQL mit starkem Passwort
- [ ] HTTPS/SSL aktiviert
- [ ] Regelmäßige Backups (täglich!)
- [ ] Monitoring & Alerts konfiguriert
- [ ] Fail2ban für SSH-Brute-Force-Protection

---

## Performance-Tipps

### Nginx Caching

```nginx
# In nginx config hinzufügen:
location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
    expires 30d;
    add_header Cache-Control "public, immutable";
}
```

### Database Backups optimieren

```bash
# Nur incremental backup (mit pg_basebackup)
docker-compose -f docker-compose.prod.yml exec -T postgres \
  pg_basebackup -D /backups/latest -F tar -z
```

### Container Auto-Restart bei High Memory

```bash
# In docker-compose.prod.yml:
services:
  backend:
    mem_limit: 1g
    restart: unless-stopped
```

---

## Helpful Commands

```bash
# Schneller Überblick
docker-compose -f docker-compose.prod.yml ps

# Container in Shell betreten
docker-compose -f docker-compose.prod.yml exec backend bash

# Environment Variablen in Container prüfen
docker-compose -f docker-compose.prod.yml exec backend env

# Database in Container prüfen
docker-compose -f docker-compose.prod.yml exec postgres psql -U aom_user aom_db

# Volume Inhalte prüfen
docker volume ls
docker volume inspect lohnbuero_postgres_data

# Netzwerk Debugging
docker-compose -f docker-compose.prod.yml exec backend curl http://frontend/
```

---

## Weitere Ressourcen

- [Docker Docs](https://docs.docker.com/)
- [Docker Compose Docs](https://docs.docker.com/compose/)
- [Nginx Docs](https://nginx.org/en/docs/)
- [Let's Encrypt Docs](https://letsencrypt.org/docs/)
- [PostgreSQL Docs](https://www.postgresql.org/docs/)

---

**Stand**: 2026-02-22 | **AOM v1.0**
