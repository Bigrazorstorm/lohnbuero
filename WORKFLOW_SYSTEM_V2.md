# Workflow-System - Verbesserungen v2.0

## 🎯 Übersicht

Das erweiterte Workflow-System v2.0 bietet eine flexible, mehrschichtige Architektur für Lohnabrechnung mit:

1. **Multi-Tenancy-Unterstützung** - Mehrere Tenants mit jeweils mehreren Abrechnungsfirmen
2. **Standard Workflows** - Basis-Workflows als Vorlagen
3. **Branchenspezifische Schritte** - Automatisch hinzugefügte Schritte pro Branche
4. **Mandantenspezifische Schritte** - Individuell konfigurierte Schritte pro Mandant
5. **Globale Events** - Große Themen wie Jahreswechsel oder Mindestlohnerhöhung

---

## 📦 Architektur - Datenbankmodelle

### 1. Multi-Tenancy

#### `Tenant`
- **Zweck**: Repräsentiert eine Organisation/Kanzlei
- **Felder**:
  - `name`, `code`: Eindeutige Identifikation
  - `konfiguration`: JSON für Features, Max-Mandanten, etc.
  - `logo_url`, `primaerfarbe`: Branding
- **Beziehungen**: 1:N zu `Abrechnungsfirma`, 1:N zu `User`

```python
# Beispiel
tenant = Tenant(
    name="Steuerberater Müller GmbH",
    code="mueller_sb",
    konfiguration=json.dumps({
        "features": ["multi_abrechnungsfirma", "global_events", "branche_spezifisch"],
        "max_mandanten": 500,
        "sla_default_tage": 10,
    })
)
```

#### `Abrechnungsfirma`
- **Zweck**: Lohnabrechnung innerhalb eines Tenants
- **Felder**:
  - `name`, `code`: Eindeutig pro Tenant
  - `strasse`, `plz`, `ort`: Adressdaten
  - `steuernummer`, `ustid`: Steuerliche Daten
  - `iban`, `bic`: Bankverbindung
  - `workflow_konfiguration`: JSON mit Standard-Vorlage pro Abrechnungsfirma
- **Beziehungen**: N:1 zu `Tenant`, 1:N zu `Mandant`

```python
# Beispiel: Eine Kanzlei mit mehreren Standorten
tenant = Tenant(name="InterGen GmbH", code="intergen")
# Abrechnungsfirma 1: Berlin-Büro
firma_berlin = Abrechnungsfirma(
    tenant_id=tenant.id,
    name="InterGen Lohnbüro Berlin",
    code="berlin",
    ort="Berlin",
)
# Abrechnungsfirma 2: München-Büro
firma_muenchen = Abrechnungsfirma(
    tenant_id=tenant.id,
    name="InterGen Lohnbüro München",
    code="muenchen",
    ort="München",
)
```

### 2. Workflow-Schritte auf mehreren Ebenen

```
┌─────────────────────────────────────────────────────┐
│           Workflow Instance (Mandant + Monat)       │
└──────────────────┬──────────────────────────────────┘
                   │
        ┌──────────┼──────────┬─────────────┐
        │          │          │             │
        ▼          ▼          ▼             ▼
    STANDARD   BRANCHE    MANDANT    GLOBAL_EVENT
    Schritte   Schritte   Schritte   Schritte
    (aus       (z.B.      (z.B.      (z.B.
    Vorlage)   Gastronomie Mandanten- Jahreswechsel
               Besonder.) spezifisch) MindestlohnErhöhung)
```

#### `WorkflowVorlageItem` - STANDARD Ebene
- **Zweck**: Kernschritte aus der Workflow-Vorlage
- **Eigenschaften**: Ist, Deadline, Dokumentation, etc.
- **Automatisch eingebunden**: Immer für passende Mandanten

#### `BranchenWorkflowSchritt` - BRANCHE Ebene
- **Zweck**: Branchenspezifische Zusatzschritte
- **Beispiele**:
  - **Baugewerbe**: SOKA-Meldung, Berufsgenossenschaft
  - **Gastronomie**: Trinkgeld-Abrechnung, Minijobs
  - **Gesundheit**: Schichtarbeitszuschläge, Plfegezuschlag
- **Gültigkeit**: `gueltig_von`, `gueltig_bis` für zeitliche Befristung
- **Optional pro Mandant**: `ist_optional_pro_mandant` kann pro Mandant deaktiviert werden

```python
branche = Branche.query.filter_by(name="Baugewerbe").first()

# SOKA-Meldung hinzufügen
soka_schritt = BranchenWorkflowSchritt(
    branche_id=branche.id,
    position=1,
    titel="SOKA-Beitragsmeldung",
    beschreibung="Verpflichtend für alle Bauunternehmen",
    ist_pflicht=True,
    ist_optional_pro_mandant=False,
    faellig_offset_tage=10,  # 10. des Monats
    standard_punkte=1.0,
    gueltig_von=datetime(2024, 1, 1),  # Ab 1.1.2024
)
```

#### `MandantWorkflowSchritt` - MANDANT Ebene
- **Zweck**: Mandantenspezifische Zusatzschritte
- **Beispiele**:
  - Spezielle Auswertungen
  - Eigene Dokumentationspflichten
  - Klientenindividuelle Berechnungen
- **Aktiviert pro Mandant**: Via `WorkflowSchrittTypConfig`
- **Gültigkeit**: `aenderung_zum` für planbare Änderungen

```python
# Spezifischer Schritt für einen Mandanten
mandant_schritt = MandantWorkflowSchritt(
    mandant_id=123,
    schritt_typ_id=workflow_schritt_typ_id,  # Referenz zu konfiguriertem Schritttyp
    ist_aktiv=True,
    aenderung_zum=None,  # Sofort wirksam
)
```

#### `GlobalEventSchritt` - GLOBAL_EVENT Ebene
- **Zweck**: Zusätzliche Schritte für unternehmensweite Events
- **Ereignisse**:
  - `JAHRESWECHSEL` - z.B. Steuertarif-Updates, SV-Wert-Änderungen
  - `MINDESTLOHN_ERHOEHUNG` - z.B. Mindestlohn nach oben anpassen
  - `GESETZESAENDERUNG` - z.B. neue Steuerregelungen
  - `SV_WERTE_AENDERUNG` - z.B. Beitragssätze anpassen
  - `STEUERAENDERUNG` - z.B. Freibeträge aktualisieren
  - `KURZARBEIT` - Kurzarbeitermaßnahmen
  - `CORONA_MASSNAHME` - Pandemie-Maßnahmen (historisch)
  - `SONSTIG` - Sonstige Events
- **Filter**: Kann auf Branchen, Mandant-Kategorien, etc. begrenzt werden

```python
# Beispiel: Jahreswechsel 2026/2027
event = GlobalEvent(
    tenant_id=default_tenant.id,
    typ=GlobalEventTyp.JAHRESWECHSEL,
    name="Jahreswechsel 2026/2027",
    gueltig_von=datetime(2026, 12, 1),
    gueltig_bis=datetime(2027, 2, 28),
    betroffene_monate=json.dumps([
        {"monat": 12, "jahr": 2026},
        {"monat": 1, "jahr": 2027},
    ]),
    # Filter: Alle Mandanten (Jahreswechsel betrifft alle)
    mandanten_filter=json.dumps({"alle": True}),
    prioritaet=10,
    ist_aktiv=False,  # Noch nicht aktiviert
)

# Hinzufügen von Schritten
script1 = GlobalEventSchritt(
    event_id=event.id,
    position=1,
    titel="Jahreswechsel-Checkliste",
    beschreibung="...",
    faellig_offset_tage=5,
    standard_punkte=2.0,
)

# Schritt nur für SOKA-relevante Branchen
event2 = GlobalEvent(
    typ=GlobalEventTyp.MINDESTLOHN_ERHOEHUNG,
    name="Mindestlohn 2027",
    mandanten_filter=json.dumps({
        "branchen": ["Baugewerbe", "Gastronomie"],  # Nur diese Branchen
        "kategorien": ["A", "B"]  # Nur große und mittlere Unternehmen
    }),
)
```

### 3. Workflow-Item Herkunft Tracking

#### `WorkflowItemHerkunft`
- **Zweck**: Speichert die Quelle jedes Workflow-Items
- **Ebenen**: `STANDARD`, `BRANCHE`, `MANDANT`, `GLOBAL_EVENT`
- **Referenzen**: Je nach Ebene verweist auf die entsprechende Quelle

```python
# In jedem WorkflowItem nach Erstellung hinzugefügt:
herkunft = WorkflowItemHerkunft(
    workflow_item_id=item.id,
    ebene=WorkflowSchrittEbene.BRANCHE,
    branchen_schritt_id=schritt.id,
)
```

---

## 🔄 Workflow-Erstellung - Ablauf

Wenn ein Workflow für einen Mandanten und Monat erstellt wird:

1. **Template Schritte laden** (STANDARD)
   ```
   Vorlage: "Monatsabrechnung Baugewerbe"
   → Items: Unterlagen, Erfassung, Probe, Prüfung, Versand, Abschluss
   ```

2. **Branche-spezifische Schritte hinzufügen** (BRANCHE)
   ```
   Mandant.branche = "Baugewerbe"
   → BranchenWorkflowSchnitte filtern
   → Items hinzufügen: SOKA-Meldung, BG-Abrechnung, ...
   ```

3. **Mandant-spezifische Schritte hinzufügen** (MANDANT)
   ```
   Mandant.workflow_schritte filtern
   → MandantWorkflowSchritt aktiviert
   → Items hinzufügen: Z.B. spezielle Auswertung
   ```

4. **Globale Event-Schritte hinzufügen** (GLOBAL_EVENT)
   ```
   GlobalEvent.betroffene_monate enthält: {monat: 1, jahr: 2027}
   GlobalEvent.mandanten_filter passt: Alle oder bestimmte Branchen
   → GlobalEventSchritt hinzufügen: Jahreswechsel-Aktivitäten
   ```

5. **Positionen neu berechnen** & **SLA setzen**

### Code-Beispiel

```python
from app.workflow_service import WorkflowService

service = WorkflowService(db)

# Workflow erstellen
instanz = service.create_workflow_from_template(
    mandant_id=123,
    vorlage_id=5,   # "Monatsabrechnung Standard"
    monat=1,
    jahr=2027,
    sachbearbeiter_id=10,
)

# Result:
# - 8 Standard-Schritte (aus Vorlage)
# - 2 Branche-Schritte (Baugewerbe-spezifisch)
# - 1 Mandant-Schritt (Mandanten-spezifisch)
# - 3 Jahreswechsel-Schritte (Global Event)
# = 14 Schritte insgesamt
```

---

## 🌍 Admin-API - Endpoints

### Global Events

```bash
# Alle Events auflisten
GET /api/admin/global-events
  ?include_inactive=false
  &include_abgeschlossen=false
  &typ=jahreswechsel

# Event erstellen
POST /api/admin/global-events
{
  "name": "Jahreswechsel 2026/2027",
  "typ": "jahreswechsel",
  "gueltig_von": "2026-12-01",
  "gueltig_bis": "2027-02-28",
  "betroffene_monate": [
    {"monat": 12, "jahr": 2026},
    {"monat": 1, "jahr": 2027}
  ],
  "mandanten_filter": {"alle": true},
  "schritte": [
    {
      "position": 1,
      "titel": "Jahreswechsel-Checkliste",
      "faellig_offset_tage": 5,
      "ist_pflicht": true,
      "standard_punkte": 2.0
    }
  ]
}

# Event aktualisieren
PATCH /api/admin/global-events/{event_id}
{
  "ist_aktiv": true,  # Aktivieren
  "ist_abgeschlossen": false
}

# Event deaktivieren
DELETE /api/admin/global-events/{event_id}
```

### Branchenspezifische Schritte

```bash
# Schritte einer Branche auflisten
GET /api/admin/branchen/{branche_id}/workflow-schritte

# Neuen Schritt erstellen
POST /api/admin/branchen-workflow-schritte
{
  "branche_id": 2,  # Baugewerbe
  "position": 1,
  "titel": "SOKA-Beitragsmeldung",
  "ist_pflicht": true,
  "ist_optional_pro_mandant": true,
  "faellig_offset_tage": 10,
  "standard_punkte": 1.0,
  "gueltig_von": "2024-01-01",
  "gueltig_bis": null  # Unbegrenzt
}

# Schritt aktualisieren
PATCH /api/admin/branchen-workflow-schritte/{schritt_id}
{
  "ist_optional_pro_mandant": false  # Fortan nicht optional
}

# Schritt deaktivieren
DELETE /api/admin/branchen-workflow-schritte/{schritt_id}
```

### Tenants & Abrechnungsfirmen

```bash
# Tenants auflisten
GET /api/admin/tenants

# Abrechnungsfirmen eines Tenants
GET /api/admin/tenants/{tenant_id}/abrechnungsfirmen

# Neue Abrechnungsfirma
POST /api/admin/abrechnungsfirmen
{
  "tenant_id": 1,
  "name": "InterGen Berlin",
  "code": "berlin",
  "strasse": "Hauptstr. 1",
  "plz": "10115",
  "ort": "Berlin",
  "steuernummer": "...",
  "iban": "DE...",
  "workflow_konfiguration": {
    "standard_vorlage_id": 5,
    "default_sachbearbeiter_gruppe": "team_berlin"
  }
}
```

---

## 🎓 Praktische Szenarien

### Szenario 1: Jahreswechsel 2026/2027

**Problem**: Alle Mandanten brauchen zusätzliche Aktivitäten zum Jahreswechsel.

**Lösung**:
1. Admin erstellt Global Event "Jahreswechsel 2026/2027" mit Schritten
2. Event wird für Dezember/Januar aktiviert
3. Bei Workflow-Erstellung automatisch eingespielt
4. Mandanten sehen zusätzliche Items in ihrem Workflow
5. Nach Event-Abschluss: `ist_abgeschlossen = true`

### Szenario 2: Neue SOKA-Regelung für Bauunternehmen

**Problem**: SOKA-Regelungen ändern sich → nur Baugewerbe betroffen.

**Lösung**:
1. Admin erstellt/aktualisiert `BranchenWorkflowSchritt` für Baugewerbe
2. `gueltig_von` = neues Gültigkeitsdatum
3. Alle Bauunternehmen erhalten neuen Schritt in Workflows ab Gültigkeitsdatum
4. Optional: `ist_optional_pro_mandant = true` für Ausnahmen

### Szenario 3: Spezialfall Mandant ABC SE

**Problem**: Mandant ABC hat sehr spezialisierte Anforderungen.

**Lösung**:
1. Admin erstellt `WorkflowSchrittTypConfig` "ABC-Spezialauswertung"
2. Admin aktiviert über `MandantWorkflowSchritt` (nur für Mandant ABC)
3. Alle Workflows von ABC haben zusätzlichen Schritt
4. Änderung via `aenderung_zum` = effektives Datum

### Szenario 4: Mandant deaktiviert optionalen Branche-Schritt

**Problem**: Mandant in Baugewerbe braucht 1 von 2 optionalen Schritten nicht.

**Lösung**:
1. `BranchenWorkflowSchritt` mit `ist_optional_pro_mandant = true` erstellt
2. Mandant deaktiviert in seiner `workflow_konfiguration`: `{"disabled_branchen_schritte": [id]}`
3. Workflow-Erstellung berücksichtigt diese Liste und überspringt Schritt

---

## 📊 Reporting & Analysen

```bash
# Alle Schritte eines Workflows mit Quellen
GET /api/workflows/{instanz_id}
{
  "items": [
    {
      "id": 1,
      "titel": "Unterlagen",
      "status": "erledigt",
      "herkunft": {
        "ebene": "standard",
        "vorlage_item_id": 5
      }
    },
    {
      "id": 8,
      "titel": "SOKA-Meldung",
      "status": "offen",
      "herkunft": {
        "ebene": "branche",
        "branchen_schritt_id": 12
      }
    },
    {
      "id": 14,
      "titel": "Jahreswechsel-Checkliste",
      "status": "offen",
      "herkunft": {
        "ebene": "global_event",
        "global_event_schritt_id": 25
      }
    }
  ],
  "global_events": [
    {
      "name": "Jahreswechsel 2026/2027",
      "typ": "jahreswechsel"
    }
  ]
}

# Schritte pro Ebene auflisten
GET /api/admin/branchen-workflow-schritte?active=true&count=true
{
  "total_branchen_schritte": 87,
  "branchen": {
    "Baugewerbe": 12,
    "Gastronomie": 8,
    ...
  }
}
```

---

## 🚀 Migration & Deployment

### Database Migration

```sql
-- Neue Tabellen werden automatisch bei SQLAlchemy create_all() erstellt:
CREATE TABLE tenants (...)
CREATE TABLE abrechnungsfirmen (...)
CREATE TABLE global_events (...)
CREATE TABLE global_event_schritte (...)
CREATE TABLE branchen_workflow_schritte (...)
CREATE TABLE workflow_item_herkunft (...)

-- Neue Spalten zu bestehenden Tabellen (idempotent):
ALTER TABLE users ADD COLUMN tenant_id INTEGER;
ALTER TABLE mandanten ADD COLUMN tenant_id INTEGER;
ALTER TABLE mandanten ADD COLUMN abrechnungsfirma_id INTEGER;
```

### Seed Data

```python
# Beispielglobal Events werden automatisch geladen:
seed_defaults.EXAMPLE_GLOBAL_EVENTS
→ Jahreswechsel 2026/2027
→ Mindestlohn-Erhöhung 2027
```

---

## 🔒 Sicherheit & Best Practices

1. **Tenant-Isolation**: Queries filtern immer `tenant_id`
2. **Audit Logging**: Alle Admin-Änderungen protokolliert
3. **Permissions**: Nur `admin` kann Events/Branchen-Steps erstellen
4. **Soft Delete**: `ist_aktiv`, `ist_archiviert` statt physisches Löschen
5. **Gültigkeitsdaten**: Zeitlich begrenzte Konfigurationen

---

## 📝 Zusammenfassung

Das neue Workflow-System v2.0 bietet eine **flexible, skalierbare Architektur** mit:

✅ **Multi-Tenancy** für verschiedene Kanzleien
✅ **Standard Workflows** als Vorlagen
✅ **Branchenspezifische Anpassungen** (Baugewerbe, Gastronomie, ...)
✅ **Mandantenspezifische Optionen** (Individual-Anforderungen)
✅ **Globale Events** (Jahreswechsel, Gesetzes-Änderungen, ...)
✅ **Herkunft-Tracking** (Nachverfolgung von Schritt-Quellen)
✅ **Zeitbasierte Gültigkeitmit** (gültig_von/bis, aenderung_zum)

Ausblick: Zukünftig können **Community-basierte Workflows** hinzugefügt werden, die von anderen Kanzleien geteilt und wiederverwendet werden.
