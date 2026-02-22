# Workflow System Überarbeitung - Lohnbüro Excellence

## Überblick

Die Workflow-Logik wurde vollständig überarbeitet, um ein robustes und flexibles System für Lohnabrechnungsbüros mit verschiedenen Branchen und Stichtagen zu schaffen.

## Neue Funktionen

### 1. **Branche-spezifische Konfiguration**

Jede Branche kann jetzt ihre eigenen Regeln definieren:

```
Branche (z.B. "Industriebetrieb")
  ├── Lohnabschluss-Standardtag: 10. des Monats
  ├── SLA-Warnung: 2 Tage vorher
  └── BrancheFristenprofil
      └── BrancheFrist (z.B. "SV-Zahlung")
          ├── Regeltyp: RELATIV_BANKARBEITSTAGE
          ├── Regel-Config: { "bankarbeitstage_nach_zahlungsgruppe3": 1 }
          └── Automatische Deadline-Berechnung
```

### 2. **Intelligente Fristenberechnung**

WorkflowItems erhalten automatisch Deadlines basierend auf:
- **Vorlagen-Offset**: `faellig_offset_tage` (Tage ab Monatsbeginn)
- **Fristart-Referenz**: Externe Deadlines aus BrancheFrist-Profilen
- **Mandant-Konfiguration**: Spezifische Anpassungen pro Kunde

```python
service = WorkflowService(db)
deadline = service.calculate_item_deadline(vorlage_item, instanz, mandant)
# → automatically resolved from branch rules
```

### 3. **SLA-Management**

Jeder Workflow hat einen berechneten SLA-Deadline:
- Konfigurierbar über `WorkflowVorlage.sla_konfiguration`
- Automatische Ampel-Status-Berechnung
- Warnung vor Deadline

```json
{
  "gesamtdauer_tage": 30,
  "warnung_tage": 5
}
```

### 4. **Ampel-Status (Traffic Light)**

Automatische Berechnung basierend auf:
1. Kritische Tickets (ROT)
2. Überfällige Pflicht-Schritte (ROT)
3. Warnung (2-3 Tage vor Deadline) (GELB)
4. Keine Probleme (GRUEN)

```python
service.update_ampel_status_with_log(instanz_id)
# → Automatisch bei jedem Update
```

### 5. **Abhängigkeitsmanagement**

Workflow-Items können voneinander abhängig sein:

```json
{
  "abhaengig_von_items": ["item_id_1", "item_id_2"]
}
```

- Automatische Blockierung
- Automatisches Entsperren nach Abschluss
- Dependency-Auflösung

### 6. **Arbeitszeiterfassung**

Bessere Zeitmessung für Reporting:
- `started_at`: Wann wurde tatsächlich angefangen?
- `actual_duration_minuten`: Wie lange dauerte es?
- `durchlaufzeit_stunden`: Gesamtdauer nach Abschluss
- `verzoegerung_tage`: Wie viele Tage über SLA?

### 7. **Flexible Schritttypen**

Statt hartcodierter Kernprozesse:

```python
class WorkflowSchrittTyp(str, enum.Enum):
    DATENERFASSUNG = "datenerfassung"
    PRUEFER_PFLICHT = "pruefer_pflicht"
    ABSCHLUSSFRIST = "abschlussfrist"
    UPLOAD = "upload"
    GENEHMIGUNG = "genehmigung"
    # ... etc
```

### 8. **Validierung vor Abschluss**

Umfassende Prüfung beim Monatsabschluss:

```python
can_close, errors = service.validate_can_close(instanz)
# Returns list of blocking issues
```

Validiert:
- Alle Pflicht-Schritte erledigt
- 4-Augen-Prüfung durchgeführt (wenn nötig)
- Keine blockierten Items
- Keine kritischen offenen Tickets

## Architektur

### WorkflowService (`app/workflow_service.py`)

Zentrale Service-Klasse mit Kern-Logik:

```python
service = WorkflowService(db)

# Deadline-Berechnung
deadline = service.calculate_item_deadline(item, instanz, mandant)

# Ampel-Status
service.update_ampel_status_with_log(instanz_id)

# Abhängigkeiten
is_unblocked, blocking = service.check_dependencies(item)
unblocked_ids = service.auto_unblock_items(instanz_id)

# Workflow-Erstellung
instanz = service.create_workflow_from_template(mandant_id, vorlage_id, monat, jahr)

# Validierung
can_close, errors = service.validate_can_close(instanz)

# Reporting
metrics = service.calculate_metrics(instanz)
```

### Router-Integration (`app/routers/workflows.py`)

Router nutzt Service für:
- `POST /api/workflows/` - Neue Workflows mit Smart-Deadlines
- `PATCH /api/workflows/{id}` - Updates mit Auto-Ampel
- `POST /api/workflows/bulk-create-monthly` - Massen-Erstellung
- `PATCH /api/workflows/{id}/items/{item_id}` - Item-Updates mit Dependency-Check

## Datenmodell

### Neue Tabellen

- `branchen` - Branch-Master
- `branche_fristenprofile` - Branch-spezifische Deadline-Profile
- `branche_fristen` - Einzelne Deadline-Regeln

### Erweiterte Spalten

**WorkflowVorlage:**
- `branche_typ` - Target branch type enum
- `branche_id` - Link to specific branch
- `sla_konfiguration` - JSON SLA config

**WorkflowVorlageItem:**
- `schritttyp` - Step type enum (replaces hardcoded types)
- `fristart_offset_tage` - Offset from external deadline
- `abhaengig_von_items` - JSON dependency list
- `blockier_konfiguration` - Blocking rules

**WorkflowInstanz:**
- `sla_deadline` - Calculated overall deadline
- `sla_status` - SLA status (gruen/gelb/rot)
- `started_at` - When actually started
- `durchlaufzeit_stunden` - Total duration
- `verzoegerung_tage` - Delay after SLA

**WorkflowItem:**
- `schritttyp` - Workflow step type
- `sla_warnung_ab` - Warning deadline
- `started_at` - Work start time
- `actual_duration_minuten` - Time spent
- `abhaengig_von_items` - JSON dependencies
- `blockierung_seit` - When blocked
- `ist_ueberfaellig` - Overdue flag

## Schnellstart

### 1. Branch-Profile erstellen

```python
branche = Branche(
    name="Industriebetrieb",
    typ=BrancheTyp.INDUSTRIE,
    lohnabschluss_standardtag=10,
    sla_warnung_tage=2
)

profil = BrancheFristenprofil(
    branche_id=branche.id,
    name="Standard Industrie",
    ist_standard=True
)

frist = BrancheFrist(
    profil_id=profil.id,
    position=1,
    bezeichnung="SV-Zahlung",
    regeltyp=FristenRegeltyp.RELATIV_BANKARBEITSTAGE,
    regelkonfiguration='{"bankarbeitstage_nach_zahlungsgruppe3": 1}',
    interne_vorfrist_tage=2
)
```

### 2. Workflow-Template erstellen

```python
vorlage = WorkflowVorlage(
    name="Industriebetrieb - Monatlich",
    branche_typ=BrancheTyp.INDUSTRIE,
    ist_standard=True,
    sla_konfiguration='{"gesamtdauer_tage": 30, "warnung_tage": 5}'
)

items = [
    WorkflowVorlageItem(
        vorlage_id=vorlage.id,
        position=1,
        titel="Unterlagen eingegangen",
        schritttyp=WorkflowSchrittTyp.DATENERFASSUNG,
        faellig_offset_tage=0,
        ist_pflicht=True,
    ),
    WorkflowVorlageItem(
        vorlage_id=vorlage.id,
        position=2,
        titel="Probe-Abrechnung",
        schritttyp=WorkflowSchrittTyp.BERECHNUNG,
        faellig_offset_tage=5,
        ist_pflicht=True,
        abhaengig_von_items='[1]',  # depends on item 1
    ),
    # ... etc
]
```

### 3. Workflow für Mandant erstellen

```python
service = WorkflowService(db)
instanz = service.create_workflow_from_template(
    mandant_id=123,
    vorlage_id=456,
    monat=2,
    jahr=2026
)
# → Deadlines automatically calculated from branch rules
```

## Best Practices

### ✅ DO

- Nutze `WorkflowService` für alle komplexen Operationen
- Definiere Fristen auf Branch-Level, nicht hardcoded
- Nutze Abhängigkeiten für logische Sequenzen
- Berechne SLA-Deadlines zentral
- Tracke Arbeitszeiten für Reporting

### ❌ DON'T

- Direktes Update von Deadlines in Items
- Ignorieren von Blockierungen
- Hardcodierte Stichtage pro Mandant
- Manuelles Ampel-Status-Setting
- Abschließen ohne Validierung

## Migration Bestehender Daten

Bestehende Workflows mit hartcodierten Kernprozess-Schritten bleiben funktional. Sie wechseln schrittweise zu flexiblen Template-Items:

1. Export: `unterlagen_eingegangen_am` → WorkflowItem mit `schritttyp=DATENERFASSUNG`
2. Mapping: Kernprozess-Felder → entsprechende Items
3. Testing: Neue und alte Items parallel laufen lassen
4. Cutover: Nach Validierung auf neue Items umschalten

## Monitoring & Alerts

### SLA-Metriken

```python
metrics = service.calculate_metrics(instanz)
# Returns:
# {
#   "items_gesamt": 10,
#   "items_erledigt": 7,
#   "items_offen": 3,
#   "prozent_fertig": 70.0,
#   "durchlaufzeit_stunden": 28.5,
#   "verzoegerung_tage": 2,
#   "punkte": 15.5,
#   "ampel": "gelb"
# }
```

### Auto-Eskalation (zukünftig)

Geplant: Automatische Eskalation bei:
- ROT Ampel > 3 Tage
- SLA überschritten > 5 Tage
- Kritische Tickets > X Stunden offen

## Performance-Optimierungen

Die neue Logik ist optimiert für:
- **Masse**: Bulk-Create für 1000+ Workflows/Monat
- **Fristen**: Einmalige Berechnung bei Erstellung
- **Abfragen**: Indexed workflows by (mandant, monat, jahr)
- **Updates**: Lazy ampel status update

## Nächste Schritte

1. ✅ Models und Service erweitert
2. ✅ Router modernisiert
3. ⏳ Frontend Dashboard für SLA-Tracking
4. ⏳ Template-Builder UI
5. ⏳ Migration bestehender Workflows
6. ⏳ Auto-Eskalation implementieren
7. ⏳ Reporting-Dashboard

---

**Version**: 2.0  
**Stand**: 2026-02-23  
**Autor**: AI Assistant
