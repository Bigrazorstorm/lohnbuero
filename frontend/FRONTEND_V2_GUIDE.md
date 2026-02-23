# Frontend Implementation - Workflow System V2.0

## Neue Admin-Komponenten

### 1. AdminGlobalEvents.tsx
Verwaltungsseite für globale Workflow-Events (Jahreswechsel, Mindestlohnerhöhung, etc.)

**Features:**
- Liste aller Global Events mit Filter
- Event-Status (Aktiv/Inaktiv, Abgeschlossen)
- Detailverwaltung von Workflow-Schritten pro Event
- Prioritätsmanagement
- Datum-Gültikeit (gueltig_von bis gueltig_bis)
- Mandanten-Filter (JSON-Konfiguration)

**API-Integration:**
- `adminApi.listGlobalEvents()` - Mit optional `include_inactive` Parameter
- `adminApi.createGlobalEvent()` - Mit Schritte-Array
- `adminApi.updateGlobalEvent()` - Inclusive Status ändern
- `adminApi.deleteGlobalEvent()`

---

### 2. AdminBranchenSchritte.tsx
Verwaltung von branchenspezifischen Workflow-Schritten

**Features:**
- Schritt-Management pro Branche
- Zeitliche Geltung (gueltig_von/gueltig_bis)
- Optional-pro-Mandant Flagging (kann pro Mandant deaktiviert werden)
- Punkte-Vergabe
- Gruppierte Anzeige nach Branche

**API-Integration:**
- `adminApi.listBranchenWorkflowSchritte()` - Mit optional `branche_id` Filter
- `adminApi.createBranchenWorkflowSchritt()`
- `adminApi.updateBranchenWorkflowSchritt()`
- `adminApi.deleteBranchenWorkflowSchritt()`

---

### 3. AdminTenants.tsx
Multi-Tenant Verwaltung - Verwaltung von Tenants und deren Abrechnungsfirmen

**Features:**
- Tenant-Verwaltung (Name, Code, Branding)
- Logo-URL und Primary-Farbe Branding
- Abrechnungsfirmen pro Tenant
- Address und Banking-Informationen (IBAN, BIC, Steuer-ID)
- Modal-Dialog für Abrechnungsfirma-Erstellung

**API-Integration:**
- `adminApi.listTenants()` - Alle Tenants
- `adminApi.createTenant()`
- `adminApi.updateTenant()`
- `adminApi.getTenant(id)`
- `adminApi.listAbrechnungsfirmen()`
- `adminApi.createAbrechnungsfirma()`
- `adminApi.updateAbrechnungsfirma()`

---

## Erweiterte WorkflowDetail.tsx

### Neue Features mit Herkunft-Tracking
Jeder Workflow-Schritt zeigt jetzt seine Quelle mit farbigen Badges:

```
Standard → 🔵 blau
Branche → 🟣 lila
Mandant → 🟢 grün
Global Event → 🟡 gelb
```

**Komponenten-Update:**
- Added `WorkflowItemMitHerkunft` Type-Import
- Herkunft-Badge Rendering mit Ebene + Source-Name
- Color-Coding basierend auf `ebene` Enum

---

## Typ-Definitionen (types/index.ts)

### Neue Enums
- `GlobalEventTyp`: jahreswechsel, mindestlohn_erhoehung, soka_beitragsaenderung, vierteljahressteuererklarung, jaehrliche_lohnsteuerererklaerung, monatliche_statistikabgabe, kurzarbeit_anmeldung, sommerzeitumstellung
- `WorkflowSchrittEbene`: 'standard' | 'branche' | 'mandant' | 'global_event'

### Neue Interfaces
- `Tenant` - Multi-Tenant Entity mit Branding
- `Abrechnungsfirma` - Accounting Company mit Banking Details
- `GlobalEvent` - Global Workflow Event
- `GlobalEventSchritt` - Steps innerhalb eines Events
- `BranchenWorkflowSchritt` - Branch-specific Steps
- `WorkflowItemHerkunft` - Source-Tracking für jeden Schritt
- `WorkflowItemMitHerkunft` - Extended WorkflowItem mit Herkunft

---

## API-Client Erweiterungen (api/client.ts)

### Global Events API Group
```typescript
adminApi.listGlobalEvents(params?: { include_inactive?: boolean })
adminApi.createGlobalEvent(data: GlobalEventCreate)
adminApi.updateGlobalEvent(id: number, data: GlobalEventUpdate)
adminApi.deleteGlobalEvent(id: number)
adminApi.getGlobalEventTypen() // Returns enum options
adminApi.listGlobalEventSchritte(eventId: number)
adminApi.addGlobalEventSchritt(eventId: number, data: GlobalEventSchrittCreate)
adminApi.updateGlobalEventSchritt(eventId: number, schrittId: number, data: GlobalEventSchrittUpdate)
adminApi.deleteGlobalEventSchritt(eventId: number, schrittId: number)
```

### Branche Schritte API Group
```typescript
adminApi.listBranchenWorkflowSchritte(params?: { branche_id?: number })
adminApi.createBranchenWorkflowSchritt(data: BranchenWorkflowSchrittCreate)
adminApi.updateBranchenWorkflowSchritt(id: number, data: BranchenWorkflowSchrittUpdate)
adminApi.deleteBranchenWorkflowSchritt(id: number)
```

### Tenant API Group
```typescript
adminApi.listTenants()
adminApi.createTenant(data: TenantCreate)
adminApi.updateTenant(id: number, data: TenantUpdate)
adminApi.getTenant(id: number)
adminApi.listAbrechnungsfirmen()
adminApi.createAbrechnungsfirma(data: AbrechnungsfirmaCreate)
adminApi.updateAbrechnungsfirma(id: number, data: AbrechnungsfirmaUpdate)
```

### Erweiterte Admin APIs
```typescript
fristenApi.listProfiles()
fristenApi.createProfile(data: AusgabewegFristenCreate)
fristenApi.updateProfile(id: number, data: AusgabewegFristenUpdate)

schrittTypenApi.listMandantSchritte(mandantId: number)
schrittTypenApi.addMandantSchritt(mandantId: number, data: MandantWorkflowSchrittCreate)
schrittTypenApi.removeMandantSchritt(mandantId: number, schrittTypId: number)

reportingApi.mitarbeiterPunkte(params: { start_date: string; end_date: string })
reportingApi.mandantenPunkte(params: { start_date: string; end_date: string })
reportingApi.exportCsv(data: unknown, filename: string)
reportingApi.exportExcel(data: unknown, filename: string)
```

---

## Sidebar Routing Updates

Neue Navigation-Einträge für Admin-Benutzer:
- `/admin/global-events` → AdminGlobalEvents (🔌 Zap Icon)
- `/admin/branche-schritte` → AdminBranchenSchritte (✓ CheckSquare Icon)
- `/admin/tenants` → AdminTenants (🏢 Building2 Icon)

---

## Komponenten-Struktur

```
frontend/src/
├── pages/
│   ├── AdminGlobalEvents.tsx      ← NEW
│   ├── AdminBranchenSchritte.tsx  ← NEW
│   ├── AdminTenants.tsx           ← NEW
│   └── WorkflowDetail.tsx         ← UPDATED (Herkunft-Badges hinzugefügt)
├── api/
│   └── client.ts                  ← EXTENDED (~50+ neue Methoden)
├── types/
│   └── index.ts                   ← EXTENDED (~150 Zeilen neue Types)
├── components/
│   └── Sidebar.tsx                ← UPDATED (Neue Admin-Links)
└── App.tsx                        ← UPDATED (Neue Routes)
```

---

## Verwendungsbeispiele

### Global Event erstellen
```typescript
await adminApi.createGlobalEvent({
  name: 'Jahreswechsel 2026/2027',
  typ: 'jahreswechsel',
  beschreibung: 'Automatische Anpassung für neues Steuerjahr',
  gueltig_von: '2026-12-01',
  gueltig_bis: '2027-01-15',
  mandanten_filter: JSON.stringify({ alle: true }),
  prioritaet: 10,
  ist_aktiv: true,
  schritte: [
    {
      position: 1,
      titel: 'Finale Lohnabrechnung 2026',
      faellig_offset_tage: 5,
      ist_pflicht: true,
      standard_punkte: 2,
    },
    {
      position: 2,
      titel: 'Steuererklärung einreichen',
      faellig_offset_tage: 30,
      ist_pflicht: true,
      standard_punkte: 1,
    },
  ],
})
```

### Branchenschritt mit zeitlicher Geltung
```typescript
await adminApi.createBranchenWorkflowSchritt({
  branche_id: 5,
  schritt_typ_id: 12,
  position: 3,
  gueltig_von: '2026-01-01',
  gueltig_bis: '2026-12-31',
  ist_optional_pro_mandant: true,
  standard_punkte: 1.5,
  beschreibung: 'Nur für 2026 erforderlich - spezielle SOKA-Anforderung',
})
```

### Tenant mit Branding erstellen
```typescript
await adminApi.createTenant({
  name: 'Acme Corporation',
  code: 'acme-corp',
  branding_logo_url: 'https://example.com/logo.png',
  branding_primary_color: '#FF6B6B',
})
```

---

## Deployment Hinweise

1. **Database Migration**: Backend migrations erwarten die neuen Tabellen (Tenant, Abrechnungsfirma, GlobalEvent, etc.)
2. **Environment Variables**: Keine neuen Env-Variablen erforderlich - alles läuft über bestehende API-Client
3. **Backend-Abhängigkeiten**: Stellen Sie sicher, dass globalevents-Router in backend/main.py registriert ist
4. **Type Compatibility**: Alle TS-Types sind im types/index.ts definiert und voll kompatibel mit Backend-Schemas

---

## Nächste Schritte

- [ ] UI/UX-Tests für Admin-Interfaces
- [ ] E2E-Tests für Workflow-Erhaltung mit Global Events
- [ ] Reporting Dashboard für Event-Impact
- [ ] Mandanten-Filter UI für Global Events (statt JSON)
- [ ] Batch-Operationen für Branche-Steps
- [ ] Advanced Search für Global Events
- [ ] Email-Benachrichtigungen bei Event-Aktivierung
