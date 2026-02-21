# Addison Operations Manager (AOM)

**Version:** 1.0 | **Datum:** 2026-02-21

Webbasierte Lösung zur operativen Steuerung von Lohnbüros – koordiniert Prozesse rund um Addison Lohn & Gehalt, **ohne** die Lohnabrechnung selbst zu ersetzen.

---

## Funktionsumfang (MVP nach Pflichtenheft)

| Modul | Beschreibung |
|-------|-------------|
| **Mandantenverwaltung** | Anlage, Kategorisierung (A/B/C), Zuordnung Sachbearbeiter + Vertretung |
| **Workflow-Engine** | Monatliche Checklisten aus Vorlagen, automatische Erstellung per Bulk-API |
| **Ampelsystem** | Fristenüberwachung pro Mandant (Grün/Gelb/Rot) |
| **Rückfragen-Tickets** | Ticket-System mit Kommentarverlauf und Prioritäten |
| **Dokument-Tracking** | Upload und Verknüpfung mit Mandanten/Workflows |
| **4-Augen-Prüfung** | Prüfer-Rolle, Probeabrechnungs-Freigabe-Schritt |
| **Mandanten-Portal** | Eigener Login für Mandanten (Upload, Rückfragen, Statusanzeige) |
| **Dashboard** | KPIs, Ampel-Übersicht aller aktiven Mandanten |
| **Benutzerverwaltung** | Rollen: Admin, Teamleitung, Sachbearbeiter, Prüfer, Mandant |

---

## Schnellstart

### Mit Docker Compose (empfohlen)

```bash
docker-compose up
```

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Manuell

**Backend:**
```bash
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python seed.py                     # Datenbank befüllen
uvicorn app.main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

---

## Demo-Zugänge

| E-Mail | Passwort | Rolle |
|--------|----------|-------|
| `admin@kanzlei.de` | `admin123` | Admin (Kanzleileitung) |
| `teamleitung@kanzlei.de` | `team123` | Teamleitung |
| `anna.schmidt@kanzlei.de` | `sb123` | Sachbearbeiterin |
| `pruefer@kanzlei.de` | `pruef123` | Prüfer (4-Augen) |
| `buchhaltung@baufirma.de` | `mandant123` | Mandant-Portal |

---

## Architektur

```
lohnbuero/
├── backend/             # Python · FastAPI · SQLAlchemy · SQLite
│   ├── app/
│   │   ├── main.py      # FastAPI App, CORS, Router-Einbindung
│   │   ├── models.py    # SQLAlchemy ORM-Modelle
│   │   ├── schemas.py   # Pydantic-Schemas (Request/Response)
│   │   ├── auth.py      # JWT-Authentifizierung
│   │   └── routers/     # API-Endpunkte je Modul
│   └── seed.py          # Demo-Daten
└── frontend/            # React · TypeScript · Vite · Tailwind CSS
    └── src/
        ├── pages/       # Seiten-Komponenten
        ├── components/  # Wiederverwendbare UI-Elemente
        ├── api/         # Axios-Client
        ├── store/       # Zustand (Auth)
        └── types/       # TypeScript-Typdefinitionen
```

## Prozessmodell (implementiert)

```
Monatsstart
    │
    ▼
[1] Automatische Workflow-Erstellung (bulk-create-monthly API)
    │
    ▼
[2] Unterlagen anfordern → Ticket / Erinnerung
    │
    ▼
[3] Vollständigkeitscheck → Ampel Grün/Gelb/Rot
    │
    ▼
[4] Rückfragen als Tickets führen
    │
    ▼
[5] Erfassung in Addison (extern) → Schritt abhaken
    │
    ▼
[6] Probeabrechnung + 4-Augen-Prüfung
    │
    ▼
[7] Mandantenfreigabe (Portal oder intern)
    │
    ▼
[8] Endabrechnung + Versand
    │
    ▼
[9] Monatsabschluss → Workflow "Abgeschlossen"
```

## Eskalation

- Rote Ampel = Pflicht-Items überfällig
- Gelbe Ampel = Fälligkeiten innerhalb 2 Tage
- Eskalation über Ticket-Priorität "Dringend" + Workflow-Status "Eskaliert"
- Bulk-Create-API für automatische Monatserstellung per Cronjob aufrufbar

---

## API-Dokumentation

Nach Start verfügbar unter: **http://localhost:8000/docs** (Swagger UI)
