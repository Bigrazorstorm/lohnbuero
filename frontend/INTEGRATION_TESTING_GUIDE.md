# Integration Testing Guide - Workflow System V2.0

## 🧪 Frontend Integration Test Scenarios

### Scenario 1: Create and Activate Global Event

**User Story:**
Admin creates a "Jahreswechsel 2026/2027" event that automatically adds year-end specific steps to all workflow templates.

**Test Steps:**
1. Navigate to `/admin/global-events`
2. Click "+ Neues Event"
3. Fill form:
   - Name: "Jahreswechsel 2026/2027"
   - Typ: "jahreswechsel"
   - Gültig von: 2026-12-01
   - Gültig bis: 2027-01-31
   - Priorität: 10
   - Check "Sofort aktivieren"
4. Add 3 Schritte:
   - "Jahresabschluss erstellen" (5 Tage, Pflicht, 2 Punkte)
   - "Steuererklärung vorbereiten" (10 Tage, Pflicht, 1 Punkt)
   - "Dokumentation archivieren" (15 Tage, Optional, 1 Punkt)
5. Click "Event erstellen"

**Expected Results:**
- Event appears in list with green "Aktiv" badge
- Event shows all 3 Schritte with positions
- Can immediately toggle status or delete

**API Calls Verified:**
- ✅ POST `/api/admin/global-events` successful
- ✅ Response includes `id`, `ist_aktiv`, `schritte[]`
- ✅ Database inserts event with tenant relationship

---

### Scenario 2: Configure Branch-Specific Steps

**User Story:**
Branche "Dienstleistungen" needs special compliance steps only during Q4 (Oct-Dec).

**Test Steps:**
1. Navigate to `/admin/branche-schritte`
2. Filter by Branche "Dienstleistungen"
3. Click "+ Neuer Schritt"
4. Fill form:
   - Branche: Dienstleistungen
   - Schritt-Typ: 42
   - Gültig von: 2026-10-01
   - Gültig bis: 2026-12-31
   - Check "Optional pro Mandant"
   - Punkte: 1.5
   - Beschreibung: "Q4 Compliance Check"
5. Click "Schritt erstellen"

**Expected Results:**
- Schritt appears under "Dienstleistungen" group
- Date range displayed correctly
- "Optional" badge visible
- Can delete individual steps

**API Calls Verified:**
- ✅ POST `/api/admin/branche-schritte` with `gueltig_von/gueltig_bis`
- ✅ GET filters by `branche_id` parameter
- ✅ Time-range stored correctly in database

---

### Scenario 3: Multi-Tenant Setup with Branding

**User Story:**
Create two tenants with different branding for multi-organization support.

**Test Steps:**
1. Navigate to `/admin/tenants`
2. Create Tenant 1:
   - Name: "Acme Corporation"
   - Code: "acme-corp"
   - Logo URL: "https://example.com/acme-logo.png"
   - Primary Color: #FF6B6B (using color picker)
   - Click "Tenant erstellen"
3. Create Abrechnungsfirma for Tenant 1:
   - Click "+ Neue Firma"
   - Name: "Acme Accounting"
   - Straße: "123 Main St"
   - PLZ: "12345"
   - Stadt: "New York"
   - Steuer-ID: "DE123456789"
   - IBAN: "DE89370400440532013000"
   - BIC: "COBADEFFXXX"
4. Repeat with Tenant 2

**Expected Results:**
- 2 Tenants displayed with branding colors
- Each tenant can have multiple Abrechnungsfirmen
- Company details persist and display correctly
- Color picker updates preview in real-time

**API Calls Verified:**
- ✅ POST `/api/admin/tenants` stores branding config
- ✅ GET returns all tenants with related companies
- ✅ POST `/api/admin/abrechnungsfirmen` links to tenant
- ✅ Address and banking info stored securely

---

### Scenario 4: Workflow Display with Herkunft Tracking

**User Story:**
When viewing a workflow created after Global Event activation, user sees badge indicating if step came from standard template, branch config, or global event.

**Test Steps:**
1. Navigate to `/workflows`
2. Select workflow created after Global Event was active
3. Click to view workflow detail: `/workflows/{id}`
4. Inspect each step for Herkunft badges

**Expected Results:**
- Standard steps show **🔵 Standard**
- Branche-specific steps show **🟣 Branche · [Branche Name]**
- Mandant-specific steps show **🟢 Mandant-spezifisch**
- Global Event steps show **🟡 Global Event · [Event Name]**
- Badges maintain proper color-coding
- Source names are readable and contextual

**Backend Verification:**
- ✅ `workflow_items.herkunft_id` foreign key exists
- ✅ `workflow_item_herkunft` table has ebene enum
- ✅ Workflow creation populates herkunft metadata
- ✅ Query joins herkunft table for source name

---

## 🔗 Frontend-Backend Integration Checklist

### API Endpoints Used

#### Global Events
- [ ] GET `/api/admin/global-events` - List with filter
- [ ] POST `/api/admin/global-events` - Create
- [ ] PUT `/api/admin/global-events/{id}` - Update
- [ ] DELETE `/api/admin/global-events/{id}` - Delete
- [ ] GET `/api/admin/global-events/typen` - Enum values
- [ ] POST `/api/admin/global-events/{id}/schritte` - Add step
- [ ] PUT `/api/admin/global-events/{event_id}/schritte/{schritt_id}` - Update step
- [ ] DELETE `/api/admin/global-events/{event_id}/schritte/{schritt_id}` - Delete step

#### Branche Schritte
- [ ] GET `/api/admin/branche-schritte` - List with optional filter
- [ ] POST `/api/admin/branche-schritte` - Create
- [ ] PUT `/api/admin/branche-schritte/{id}` - Update
- [ ] DELETE `/api/admin/branche-schritte/{id}` - Delete

#### Tenants
- [ ] GET `/api/admin/tenants` - List all
- [ ] POST `/api/admin/tenants` - Create
- [ ] PUT `/api/admin/tenants/{id}` - Update
- [ ] GET `/api/admin/abrechnungsfirmen` - List companies
- [ ] POST `/api/admin/abrechnungsfirmen` - Create company
- [ ] PUT `/api/admin/abrechnungsfirmen/{id}` - Update company

#### Workflow Enhancement
- [ ] GET `/api/workflows/{id}` - Returns workflow with herkunft data
- [ ] GET `/api/workflows/{id}/items` - Items include herkunft relationship

---

## 🧪 Component State Management Tests

### AdminGlobalEvents State Lifecycle
```typescript
// Initial state
events = []
loading = false
showForm = false
selectedEvent = null

// After loadEvents()
events = [{ id: 1, name: '...', ... }, ...]
loading = false

// Form interaction
showForm = true
formData.name = "New Event"
formData.schritte = [{ ... }, { ... }]

// After submit
showForm = false
events = [..., newEvent]
formData = reset
```

### AdminTenants Modal Management
```typescript
// Initial state
tenants = []
abrechnungsfirmen = []
showAbrechForm = false
selectedTenant = null

// Show modal
showAbrechForm = true
selectedTenant = tenant_5
abrechData.tenant_id = 5

// Submit
showAbrechForm = false
abrechnungsfirmen = [..., newFirma]
```

---

## 📊 Data Flow Validation

### Global Event → Workflow Items Creation Flow
```
Global Event Created (Backend)
  ↓
WorkflowInstanz.global_events = [event_id, ...]
  ↓
workflow_service._add_global_event_schritte()
  ↓
For each GlobalEventSchritt:
  - Create WorkflowItem
  - Create WorkflowItemHerkunft (ebene='global_event', global_event_id=...)
  ↓
Frontend GET /api/workflows/{id}
  ↓
Display with 🟡 Global Event badges
```

### Branche Schritt → Workflow Items Flow
```
BranchenWorkflowSchritt Created
  ↓
Workflow Instantiation for matching branche
  ↓
workflow_service._add_branchen_schritte()
  ↓
Create WorkflowItem + WorkflowItemHerkunft
  ↓
Frontend displays 🟣 Branche badge
```

---

## 🔍 Frontend Type Safety Tests

### TypeScript Compilation
```bash
# Should have zero errors
tsc --noEmit

# Check type definitions
npm run type-check
```

### Type Definition Coverage
- [ ] GlobalEvent type matches backend GlobalEventBase schema
- [ ] BranchenWorkflowSchritt type has all backend fields
- [ ] WorkflowItemHerkunft type correctly unions source fields
- [ ] AdminGlobalEvents uses GlobalEvent type correctly
- [ ] API client returns correctly typed responses

---

## 🌐 API Response Validation

### Expected Response Structures

**GET /admin/global-events**
```json
[
  {
    "id": 1,
    "name": "Jahreswechsel 2026/2027",
    "typ": "jahreswechsel",
    "gueltig_von": "2026-12-01T00:00:00",
    "gueltig_bis": "2027-01-31T23:59:59",
    "ist_aktiv": true,
    "ist_abgeschlossen": false,
    "schritte": [
      {
        "id": 1,
        "position": 1,
        "titel": "...",
        "faellig_offset_tage": 5
      }
    ]
  }
]
```

**POST /admin/branche-schritte**
```json
{
  "id": 42,
  "branche_id": 5,
  "schritt_typ_id": 12,
  "gueltig_von": "2026-10-01",
  "gueltig_bis": "2026-12-31",
  "ist_optional_pro_mandant": true,
  "standard_punkte": 1.5
}
```

**GET /workflows/{id}**
```json
{
  "id": 1,
  "items": [
    {
      "id": 100,
      "position": 1,
      "herkunft": {
        "ebene": "standard",
        "source_name": "Template Standard"
      }
    },
    {
      "id": 101,
      "position": 2,
      "herkunft": {
        "ebene": "global_event",
        "source_name": "Jahreswechsel 2026/2027"
      }
    }
  ]
}
```

---

## 🚨 Error Handling Tests

### Scenario A: Duplicate Event Name
1. Create event "Jahreswechsel 2026"
2. Attempt to create another with same name
3. Expected: Backend validation error, frontend shows alert

### Scenario B: Invalid Date Range
1. Try to create event with gueltig_bis before gueltig_von
2. Expected: Frontend validation prevents submission

### Scenario C: Missing Required Field
1. Try to create event without name
2. Expected: Form validation error, alert displayed

### Scenario D: Unauthorized Access
1. Non-admin user tries to access `/admin/tenants`
2. Expected: RequireAdmin wrapper redirects to dashboard

---

## ✅ Acceptance Criteria

- [ ] All three admin pages load without errors
- [ ] CRUD operations work for events, steps, and tenants
- [ ] Herkunft badges display correctly in workflows
- [ ] Form validation prevents invalid submissions
- [ ] API responses match expected structures
- [ ] Error handling graceful with user feedback
- [ ] Navigation works between admin pages
- [ ] Sidebar shows admin-only routes correctly
- [ ] Types compile without errors
- [ ] Performance acceptable (< 2s page load)

---

## 🚀 Pre-Production Checklist

- [ ] All integration tests pass
- [ ] Console has no JavaScript errors
- [ ] Network tab shows expected API calls
- [ ] Database contains correct relationships
- [ ] Herkunft tracking works end-to-end
- [ ] Multi-tenant isolation verified
- [ ] Global Events affect correct workflows
- [ ] Branch steps respect time ranges
- [ ] Backup/restore procedures tested
- [ ] Load testing completed
- [ ] Security audit passed
- [ ] Documentation reviewed
