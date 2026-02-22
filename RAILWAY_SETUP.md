# Railway Deployment Guide für AOM (2 Services)

Railway braucht für diese Anwendung **2 separate Services**: Backend + Frontend.

---

## 🚀 Schritt 1: Railway Projekt erstellen

1. Gehe zu https://railway.app
2. Klicke "Create New Project"
3. Wähle "Deploy from GitHub repo"
4. Authentifiziere und wähle `lohnbuero` Repository

---

## 📦 Schritt 2: Backend Service hinzufügen

### 2.1 Service erstellen
```
Click "+ Add Service" → "GitHub Repo"
```

### 2.2 Konfigurieren
1. **Repo auswählen**: `lohnbuero`
2. **Root Directory**: `backend`
3. **Dockerfile**: `backend/Dockerfile` (Railway findet es automatisch)
4. **Service Name**: `backend`

### 2.3 Umgebungsvariablen setzen

Im Railway Dashboard für Backend Service:
```
Variables → "Raw Editor"
```

Füge diese Variablen ein:
```ini
SECRET_KEY=your-super-secure-secret-key-must-be-32-chars-long-change-this-now
DATABASE_URL=sqlite:///./aom.db
CORS_ORIGINS=https://your-frontend-domain.railway.app
LOG_LEVEL=info
```

### 2.4 Domain
- Railway generiert automatisch: `backend-xxx.railway.app`
- Notiere diese URL für später!

---

## 🎨 Schritt 3: Frontend Service hinzufügen

### 3.1 Service erstellen
```
Click "+ Add Service" → "GitHub Repo"
```

### 3.2 Konfigurieren
1. **Repo auswählen**: `lohnbuero`
2. **Root Directory**: `frontend`
3. **Dockerfile**: `frontend/Dockerfile` (Railway findet es automatisch)
4. **Service Name**: `frontend`

### 3.3 Umgebungsvariablen setzen

Im Railway Dashboard für Frontend Service:
```
Variables → "Raw Editor"
```

Füge diese Variablen ein:
```ini
VITE_API_URL=https://backend-xxx.railway.app
```

**Wichtig**: Ersetze `backend-xxx.railway.app` mit deiner echten Backend-URL aus Schritt 2.4!

### 3.4 Domain
- Railway generiert automatisch: `frontend-xxx.railway.app`
- Das ist deine Hauptanwendungs-URL!

---

## 🔗 Schritt 4: Services verbinden

Railway sollte automatisch die Abhängigkeit erkennen (Frontend braucht Backend). Falls nicht:

1. **Frontend Service** → Variables
2. Füge hinzu:
   ```
   RAILWAY_BACKEND_URL=http://backend:8000
   ```

---

## ✅ Schritt 5: Deployment testen

1. Gehe zu https://your-frontend-xxx.railway.app
2. Du solltest die AOM-Anwendung sehen
3. Teste mit Demo-Zugängen:
   ```
   Email: admin@kanzlei.de
   Passwort: admin123
   ```

---

## 🛠️ Troubleshooting

### Problem: "Cannot connect to Backend"
**Lösung:**
1. Stelle sicher, dass Backend-URL in Frontend-Variablen richtig gesetzt ist
2. Überprüfe Backend Logs: Dashboard → backend Service → Logs
3. Überprüfe CORS_ORIGINS in Backend - sollte Frontend-Domain enthalten

### Problem: "Port not available"
Railway setzt `$PORT` automatisch. Unsere Dockerfiles verwenden `${PORT:-8000}` - sollte funktionieren.

Überprüfe Logs:
```bash
railway logs --service backend
```

### Problem: Database ist leer
Beim ersten Start wird `seed.py` nicht automatisch ausgeführt. Optionen:

**Option A: Manuell via SSH**
```bash
railway shell
cd backend
python seed.py
```

**Option B: Docker-Befehl anpassen**
Ändere Backend Dockerfile CMD zu:
```dockerfile
CMD ["sh", "-c", "python seed.py && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
```

---

## 📊 Custom Domains (Optional)

### Domain hinzufügen
1. Railway Dashboard → Service (z.B. frontend)
2. "Settings" → "Custom Domains"
3. Gib deine Domain ein: `aom.yourdomain.com`
4. Folge DNS-Setup-Anleitung

### DNS Record setzen (bei deinem Domain-Provider)
```
CNAME: aom.yourdomain.com → your-service-xxx.railway.app
```

---

## 📈 Scaling & Performance

Railway skaliert automatisch basierend auf Verbrauch.

Wenn du bessere Performance brauchst:
1. Dashboard → Service → Settings
2. "Instance Size" erhöhen
3. "Replicas" auf 2+ setzen

---

## 💾 Produktions-Datenbank

SQLite ist für Entwicklung ok, für Produktion besser PostgreSQL:

### PostgreSQL in Railway hinzufügen
1. "+ Add Service" → "Marketplace"
2. Suche "PostgreSQL"
3. Klicke "Create"

Railway generiert automatisch `DATABASE_URL` - diese wird in Backend-Service verfügbar!

Backend DATABASE_URL ändert sich automatisch zu PostgreSQL-URL.

---

## 🔐 Sicherheit Checkliste

- [ ] SECRET_KEY auf min. 32 zufällige Zeichen setzen
- [ ] CORS_ORIGINS auf deine Domain setzen (nicht `*`)
- [ ] DATABASE_URL ist PostgreSQL (für Produktion)
- [ ] HTTPS ist aktiv (Railway macht das automatisch)
- [ ] Demo-Accounts nach Deployment löschen oder passwort ändern
- [ ] Logs regelmäßig überprüfen

---

## 📞 Hilfreiche Links

- [Railway Docs](https://docs.railway.app/)
- [Railway GitHub Integration](https://docs.railway.app/deploy/deployments#github-integration)
- [Environment Variables in Railway](https://docs.railway.app/develop/variables)

---

**Stand**: 2026-02-22 | **AOM v1.0**
