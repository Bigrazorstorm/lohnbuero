# Hosting-Anleitung: Addison Operations Manager (AOM)

**Dokument**: Deployment-Guide für AOM v1.0
**Datum**: Februar 2026

---

## 📋 Inhaltsverzeichnis

1. [Voraussetzungen](#voraussetzungen)
2. [Hosting-Optionen im Überblick](#hosting-optionen-im-überblick)
3. [Option 1: Railway.app (Empfohlen - sehr einfach)](#option-1-railwayapp-empfohlen)
4. [Option 2: Heroku (Cloud, einfach)](#option-2-heroku)
5. [Option 3: DigitalOcean App Platform](#option-3-digitalocean-app-platform)
6. [Option 4: AWS EC2 (VPS + Docker)](#option-4-aws-ec2)
7. [Option 5: Selbstgehostetes VPS](#option-5-selbstgehostetes-vps)
8. [Datenbank-Upgrade für Produktion](#datenbank-upgrade-für-produktion)
9. [Sicherheit & Best Practices](#sicherheit--best-practices)
10. [Troubleshooting](#troubleshooting)

---

## Voraussetzungen

- Git-Repository hochgeladen
- Docker installiert (für lokales Testen)
- GitHub Account (für die meisten Cloud-Optionen)
- Basis-Verständnis von Umgebungsvariablen

**Stack überblick:**
- **Frontend**: React 18 + TypeScript + Vite
- **Backend**: Python 3.x + FastAPI + SQLite
- **Container**: Docker Compose

---

## Hosting-Optionen im Überblick

| Option | Schwierigkeit | Kosten | Skalierbarkeit | Setup-Zeit | Best für |
|--------|---|---|---|---|---|
| **Railway** | ⭐ Sehr einfach | €5-50/Monat | Gut | 10 Min | Schnelles Deployment |
| **Heroku** | ⭐ Sehr einfach | €7-50/Monat | Gut | 15 Min | Einfache Apps |
| **DigitalOcean** | ⭐⭐ Leicht | €5-12/Monat | Sehr gut | 20 Min | Gutes Preis-Leistungs- |
| **AWS EC2** | ⭐⭐⭐ Mittel | €3-20/Monat | Exzellent | 45 Min | Enterprise-Grade |
| **VPS manuell** | ⭐⭐⭐ Mittel | €3-10/Monat | Sehr gut | 60 Min | Vollständige Kontrolle |

---

## Option 1: Railway.app (Empfohlen)

Railway ist der **schnellste Weg** zu einem Production-Deployment. Nur 3 Schritte!

### Schritt 1: Railway Account erstellen
1. Gehe auf https://railway.app
2. Melde dich mit GitHub an
3. Autorisiere die App

### Schritt 2: Projekt erstellen
1. Klicke auf „New Project"
2. Wähle „Deploy from GitHub"
3. Wähle das Repository `lohnbuero`

### Schritt 3: Automatische Erkennung

Railway erkennt automatisch:
- `docker-compose.yml` → Docker-Setup wird übernommen
- Environment-Variablen können direkt im Dashboard gesetzt werden

### Umgebungsvariablen setzen

Im Railway-Dashboard:
1. Gehe zu „Variables"
2. Setze folgende Variablen:

```ini
# Backend
DATABASE_URL=sqlite:///./aom.db
SECRET_KEY=your-super-secret-key-min-32-chars-hier-ändern
CORS_ORIGINS=https://your-domain.railway.app

# Frontend
VITE_API_URL=https://your-backend-url.railway.app
```

### Custom Domain hinzufügen
1. Im Railway-Dashboard → Settings
2. „Domains" → „Add Custom Domain"
3. Deine Domain konfigurieren (z.B. `aom.yourdomain.com`)

### ✅ Fertig!
- Frontend: `https://your-project.railway.app`
- Backend API: `https://your-project.railway.app:8000`

**Kosten**: Ca. €5-20/Monat (Pay-as-you-go)

---

## Option 2: Heroku

### Voraussetzung: Heroku CLI installieren
```bash
# macOS
brew tap heroku/brew && brew install heroku

# oder von https://devcenter.heroku.com/articles/heroku-cli
```

### Schritt 1: Heroku App erstellen
```bash
heroku login
heroku create aom-app-name
```

### Schritt 2: Procfile für Backend erstellen
Erstelle `Procfile` im Root-Verzeichnis:

```
release: cd backend && python seed.py
web: cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

### Schritt 3: Buildpack setzen
```bash
# Python Buildpack für Backend
heroku buildpacks:add heroku/python
heroku buildpacks:add heroku/nodejs
```

### Schritt 4: Umgebungsvariablen
```bash
heroku config:set SECRET_KEY="your-secret-key"
heroku config:set DATABASE_URL="sqlite:///./aom.db"
heroku config:set CORS_ORIGINS="https://aom-app-name.herokuapp.com"
```

### Schritt 5: Deploy
```bash
git push heroku main
```

**Achtung**: Heroku kostenlos ist seit Nov 2022 nicht mehr verfügbar.

---

## Option 3: DigitalOcean App Platform

DigitalOcean ist günstiger als Heroku und zuverlässiger.

### Schritt 1: App erstellen
1. Gehe zu https://cloud.digitalocean.com/apps
2. Klicke „Create Apps"
3. Wähle „GitHub" und authentifiziere
4. Wähle Repository `lohnbuero`

### Schritt 2: Konfiguration
DigitalOcean liest automatisch:
- `Dockerfile` (falls vorhanden)
- `docker-compose.yml`

### Schritt 3: Services konfigurieren

**Backend Service:**
```yaml
name: backend
github:
  repo: your-username/lohnbuero
  branch: main
build_command: pip install -r requirements.txt
run_command: uvicorn app.main:app --host 0.0.0.0 --port 8080
http_port: 8080
envs:
  - key: DATABASE_URL
    value: sqlite:///./aom.db
  - key: SECRET_KEY
    value: your-secret-key
```

**Frontend Service:**
```yaml
name: frontend
github:
  repo: your-username/lohnbuero
  branch: main
build_command: npm install && npm run build
http_port: 80
envs:
  - key: VITE_API_URL
    value: https://your-app-backend.ondigitalocean.app
```

### Schritt 4: Deploy
Klicke „Create" → Deployment startet automatisch

**Kosten**: €5-12/Monat (sehr fair!)

---

## Option 4: AWS EC2

Für Enterprise-Deployments oder maximale Skalierbarkeit.

### Schritt 1: EC2-Instance starten
1. Gehe zu https://console.aws.amazon.com/ec2
2. Launch Instance:
   - Image: Ubuntu 22.04 LTS (Free Tier)
   - Instance Type: t2.micro (kostenlos erste 12 Monate)
   - Security Group: öffne Ports 22 (SSH), 80 (HTTP), 443 (HTTPS)

### Schritt 2: SSH-Verbindung
```bash
ssh -i your-key.pem ubuntu@your-ec2-ip
```

### Schritt 3: Docker installieren
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
```

### Schritt 4: Repository clonen
```bash
git clone https://github.com/your-username/lohnbuero.git
cd lohnbuero
```

### Schritt 5: Docker Compose starten
```bash
docker-compose up -d
```

### Schritt 6: Nginx als Reverse Proxy (optional)
```bash
sudo apt install nginx
```

Erstelle `/etc/nginx/sites-available/aom`:
```nginx
upstream backend {
    server localhost:8000;
}

upstream frontend {
    server localhost:5173;
}

server {
    listen 80;
    server_name your-domain.com;

    location /api {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location / {
        proxy_pass http://frontend;
        proxy_set_header Host $host;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/aom /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Schritt 7: SSL mit Let's Encrypt
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

**Kosten**: €3-20/Monat (abhängig von Instance-Type)

---

## Option 5: Selbstgehostetes VPS

Für maximale Kontrolle (z.B. Hetzner, Linode, Vultr).

### Schritt 1: VPS mieten
Empfohlene Provider:
- **Hetzner** (€3-5/Monat, beste Performance/Preis)
- **Linode** (€5/Monat, sehr zuverlässig)
- **Vultr** (€2.50/Monat, High Performance)

### Schritt 2: Linux-Server Setup
```bash
# Root-Login
ssh root@your-vps-ip

# Updates
apt update && apt upgrade -y

# Docker installieren
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Docker Compose installieren
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### Schritt 3: Repository auf VPS
```bash
cd /opt
git clone https://github.com/your-username/lohnbuero.git
cd lohnbuero
```

### Schritt 4: Produktions-docker-compose.yml
Erstelle `docker-compose.prod.yml`:

```yaml
version: "3.9"

services:
  backend:
    build: ./backend
    restart: always
    volumes:
      - uploads:/app/uploads
      - ./db:/app/db
    environment:
      DATABASE_URL: postgresql://aom_user:password@db:5432/aom_db
      SECRET_KEY: ${SECRET_KEY}
      CORS_ORIGINS: ${CORS_ORIGINS}
    ports:
      - "8000:8000"

  frontend:
    build: ./frontend
    restart: always
    ports:
      - "3000:80"
    environment:
      VITE_API_URL: ${VITE_API_URL}

  db:
    image: postgres:15-alpine
    restart: always
    environment:
      POSTGRES_USER: aom_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: aom_db
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  uploads:
  postgres_data:
```

### Schritt 5: Environment-Datei
Erstelle `.env.prod`:
```bash
SECRET_KEY=your-very-secure-key-min-32-chars
DB_PASSWORD=your-db-password-min-16-chars
CORS_ORIGINS=https://aom.yourdomain.com
VITE_API_URL=https://aom.yourdomain.com/api
```

### Schritt 6: Starten
```bash
docker-compose -f docker-compose.prod.yml up -d
```

### Schritt 7: SSL mit Let's Encrypt
```bash
apt install certbot python3-certbot-nginx
certbot certonly --standalone -d aom.yourdomain.com
```

---

## Datenbank-Upgrade für Produktion

SQLite ist für **Entwicklung** ok, für **Produktion** solltest du auf PostgreSQL upgraden.

### Why PostgreSQL?
- ✅ Bessere Concurrency
- ✅ Zuverlässiger unter Last
- ✅ Automatische Backups möglich
- ✅ Clustering-ready

### Backend umstellen

**1. requirements.txt erweitern:**
```
psycopg2-binary==2.9.9  # PostgreSQL Adapter
```

**2. DATABASE_URL ändern:**
```ini
# Entwicklung (SQLite)
DATABASE_URL=sqlite:///./aom.db

# Produktion (PostgreSQL)
DATABASE_URL=postgresql://user:password@localhost/aom_db
```

**3. SQLAlchemy verträgt beide** - keine Code-Änderungen nötig!

---

## Sicherheit & Best Practices

### 🔐 Umgebungsvariablen

**NIEMALS** in Git committen:
```bash
# Erstelle .gitignore Eintrag
echo ".env" >> .gitignore
echo ".env.prod" >> .gitignore
```

Nutze stattdessen:
- Railway/Heroku/DO Dashboard
- `.env` lokal nur auf dem Server
- Secrets Manager (AWS Secrets Manager, HashiCorp Vault)

### 🔒 HTTPS erzwingen

In `backend/app/main.py`:
```python
from fastapi.middleware.trustedhost import TrustedHostMiddleware

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["aom.yourdomain.com", "www.aom.yourdomain.com"]
)
```

### 📊 Monitoring & Logging

```bash
# Docker Logs anschauen
docker-compose logs -f backend
docker-compose logs -f frontend
```

### 🔄 Auto-Restart bei Crash
In `docker-compose.yml`:
```yaml
services:
  backend:
    restart: always
```

### 💾 Backups

**PostgreSQL Backup:**
```bash
pg_dump -U aom_user -d aom_db > aom_backup_$(date +%Y-%m-%d).sql
```

**Automatisiertes Backup (Cron):**
```bash
0 2 * * * /usr/local/bin/backup.sh  # täglich um 2 Uhr
```

### 🚀 Deployment-Checklist

- [ ] `.env` und Secrets nicht in Git
- [ ] HTTPS aktiviert
- [ ] Database-Backups konfiguriert
- [ ] CORS korrekt gesetzt (keine `*`)
- [ ] SECRET_KEY lang und zufällig
- [ ] Nginx/Reverse Proxy konfiguriert
- [ ] Health-Check Endpoint konfiguriert
- [ ] Monitoring/Alerting aktiv

---

## Troubleshooting

### Problem: "Cannot connect to Backend"
```bash
# Logs checken
docker-compose logs backend

# Backend läuft?
docker ps | grep backend

# Port freigegeben?
netstat -tulpn | grep 8000
```

### Problem: "CORS Error"
Sicherstellen in `backend/app/main.py`:
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Problem: Database ist weg
Docker-Volume verloren?
```bash
# Neues Volume erstellen
docker volume create uploads
docker-compose up -d
```

### Problem: "502 Bad Gateway" (Nginx)
```bash
# Nginx Config testen
sudo nginx -t

# Logs checken
sudo tail -f /var/log/nginx/error.log
```

### Problem: Out of Memory
```bash
# Docker Container Limits setzen
services:
  backend:
    mem_limit: 512m
    mem_reservation: 256m
```

---

## 📞 Support & Ressourcen

- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **React Docs**: https://react.dev/
- **Docker Compose**: https://docs.docker.com/compose/
- **Railway Docs**: https://docs.railway.app/
- **DigitalOcean**: https://docs.digitalocean.com/

---

## Nächste Schritte

1. **Wähle eine Hosting-Option** (Railway empfohlen zum Start)
2. **Erstelle einen Account** bei deinem Provider
3. **Setze Umgebungsvariablen**
4. **Deploy** - und voilà! 🚀
5. **Testen** unter `https://your-domain.com`

---

**Stand**: 2026-02-22 | **AOM Version**: 1.0
