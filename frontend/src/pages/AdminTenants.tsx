import { useEffect, useState } from 'react'
import { adminApi } from '../api/client'
import { Tenant, Abrechnungsfirma } from '../types'

export function AdminTenants() {
  const [tenants, setTenants] = useState<Tenant[]>([])
  const [abrechnungsfirmen, setAbrechnungsfirmen] = useState<Abrechnungsfirma[]>([])
  const [loading, setLoading] = useState(false)
  const [showTenantForm, setShowTenantForm] = useState(false)
  const [showAbrechForm, setShowAbrechForm] = useState(false)
  const [selectedTenant, setSelectedTenant] = useState<Tenant | null>(null)

  // Form states
  const [tenantData, setTenantData] = useState({
    name: '',
    code: '',
    branding_logo_url: '',
    branding_primary_color: '#3b82f6',
  })

  const [abrechData, setAbrechData] = useState({
    tenant_id: 0,
    name: '',
    strasse: '',
    plz: '',
    stadt: '',
    land: '',
    steuer_id: '',
    hrb_nummer: '',
    iban: '',
    bic: '',
  })

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    setLoading(true)
    try {
      const tenants = await adminApi.listTenants?.(false) || Promise.resolve({ data: [] })
      setTenants(tenants.data)
      
      // Load abrechnungsfirmen for each tenant
      const allAbrech: any[] = []
      for (const tenant of tenants.data) {
        try {
          const abrech = await adminApi.listAbrechnungsfirmen?.(tenant.id, false)
          if (abrech?.data) {
            allAbrech.push(...abrech.data)
          }
        } catch (error) {
          console.error(`Fehler beim Laden von Abrechnungsfirmen für Tenant ${tenant.id}:`, error)
        }
      }
      setAbrechnungsfirmen(allAbrech)
    } catch (error) {
      console.error('Fehler beim Laden der Daten:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleCreateTenant = async () => {
    if (!tenantData.name || !tenantData.code) {
      alert('Name und Code sind erforderlich')
      return
    }

    try {
      await adminApi.createTenant?.(tenantData)
      setShowTenantForm(false)
      setTenantData({
        name: '',
        code: '',
        branding_logo_url: '',
        branding_primary_color: '#3b82f6',
      })
      loadData()
    } catch (error) {
      console.error('Fehler beim Erstellen des Tenants:', error)
    }
  }

  const handleCreateAbrechnungsfirma = async () => {
    if (!abrechData.tenant_id || !abrechData.name) {
      alert('Tenant und Name sind erforderlich')
      return
    }

    try {
      await adminApi.createAbrechnungsfirma?.(abrechData)
      setShowAbrechForm(false)
      setAbrechData({
        tenant_id: 0,
        name: '',
        strasse: '',
        plz: '',
        stadt: '',
        land: '',
        steuer_id: '',
        hrb_nummer: '',
        iban: '',
        bic: '',
      })
      loadData()
    } catch (error) {
      console.error('Fehler beim Erstellen der Abrechnungsfirma:', error)
    }
  }

  const getAbrechFirmen = (tenantId: number) => {
    return abrechnungsfirmen.filter((a) => a.tenant_id === tenantId)
  }

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">Multi-Tenant Verwaltung</h1>
        <button
          onClick={() => setShowTenantForm(!showTenantForm)}
          className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
        >
          {showTenantForm ? 'Abbrechen' : '+ Neuer Tenant'}
        </button>
      </div>

      {/* Create Tenant Form */}
      {showTenantForm && (
        <div className="bg-white p-6 rounded-lg shadow mb-6 border border-gray-200">
          <h2 className="text-xl font-semibold mb-4">Neuer Tenant</h2>

          <div className="grid grid-cols-2 gap-4 mb-4">
            <div>
              <label className="block text-sm font-medium mb-1">Name *</label>
              <input
                type="text"
                value={tenantData.name}
                onChange={(e) =>
                  setTenantData({ ...tenantData, name: e.target.value })
                }
                className="w-full border rounded px-3 py-2"
                placeholder="z.B. Mandanten AG"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">Code *</label>
              <input
                type="text"
                value={tenantData.code}
                onChange={(e) =>
                  setTenantData({ ...tenantData, code: e.target.value })
                }
                className="w-full border rounded px-3 py-2"
                placeholder="z.B. mandanten-ag"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">Logo URL</label>
              <input
                type="url"
                value={tenantData.branding_logo_url}
                onChange={(e) =>
                  setTenantData({
                    ...tenantData,
                    branding_logo_url: e.target.value,
                  })
                }
                className="w-full border rounded px-3 py-2"
                placeholder="https://..."
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">
                Primärfarbe
              </label>
              <div className="flex gap-2">
                <input
                  type="color"
                  value={tenantData.branding_primary_color}
                  onChange={(e) =>
                    setTenantData({
                      ...tenantData,
                      branding_primary_color: e.target.value,
                    })
                  }
                  className="h-10 w-20 border rounded cursor-pointer"
                />
                <input
                  type="text"
                  value={tenantData.branding_primary_color}
                  onChange={(e) =>
                    setTenantData({
                      ...tenantData,
                      branding_primary_color: e.target.value,
                    })
                  }
                  className="flex-1 border rounded px-3 py-2 font-mono text-sm"
                />
              </div>
            </div>
          </div>

          <button
            onClick={handleCreateTenant}
            className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
          >
            Tenant erstellen
          </button>
        </div>
      )}

      {/* Tenants List */}
      {loading ? (
        <div className="text-gray-500">Laden...</div>
      ) : tenants.length === 0 ? (
        <div className="bg-gray-50 p-6 rounded text-center text-gray-500">
          Keine Tenants vorhanden
        </div>
      ) : (
        <div className="space-y-6">
          {tenants.map((tenant) => {
            const firmen = getAbrechFirmen(tenant.id)
            return (
              <div
                key={tenant.id}
                className="bg-white rounded-lg shadow border border-gray-200 overflow-hidden"
              >
                {/* Tenant Header */}
                <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-start">
                  <div className="flex-1">
                    <h3 className="text-lg font-semibold">{tenant.name}</h3>
                    <p className="text-sm text-gray-600">
                      Code: <span className="font-mono">{tenant.code}</span>
                    </p>
                    {tenant.branding_logo_url && (
                      <img
                        src={tenant.branding_logo_url}
                        alt={tenant.name}
                        className="h-8 mt-2"
                      />
                    )}
                  </div>

                  <div
                    className="w-16 h-16 rounded border-2"
                    style={{
                      backgroundColor: tenant.branding_primary_color,
                    }}
                  />
                </div>

                {/* Abrechnungsfirmen */}
                <div className="px-6 py-4">
                  <div className="flex justify-between items-center mb-3">
                    <h4 className="font-semibold">Abrechnungsfirmen ({firmen.length})</h4>
                    <button
                      onClick={() => {
                        setSelectedTenant(tenant)
                        setShowAbrechForm(true)
                        setAbrechData({
                          ...abrechData,
                          tenant_id: tenant.id,
                        })
                      }}
                      className="bg-green-600 text-white px-3 py-1 rounded text-sm hover:bg-green-700"
                    >
                      + Neue Firma
                    </button>
                  </div>

                  {firmen.length === 0 ? (
                    <p className="text-sm text-gray-500 italic">
                      Keine Abrechnungsfirmen zugeordnet
                    </p>
                  ) : (
                    <div className="space-y-2">
                      {firmen.map((firma) => (
                        <div
                          key={firma.id}
                          className="bg-gray-50 p-3 rounded border border-gray-200"
                        >
                          <p className="font-medium">{firma.name}</p>
                          <div className="text-xs text-gray-600 mt-1">
                            {firma.strasse && (
                              <p>
                                {firma.strasse}, {firma.plz} {firma.stadt}
                              </p>
                            )}
                            {firma.steuer_id && (
                              <p>Steuer-ID: {firma.steuer_id}</p>
                            )}
                            {firma.iban && (
                              <p>IBAN: {firma.iban.slice(-4).padStart(firma.iban.length, '*')}</p>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      )}

      {/* Create Abrechnungsfirma Form */}
      {showAbrechForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full p-6">
            <h2 className="text-xl font-semibold mb-4">
              Neue Abrechnungsfirma für {selectedTenant?.name}
            </h2>

            <div className="grid grid-cols-2 gap-4 mb-4">
              <div>
                <label className="block text-sm font-medium mb-1">Name *</label>
                <input
                  type="text"
                  value={abrechData.name}
                  onChange={(e) =>
                    setAbrechData({ ...abrechData, name: e.target.value })
                  }
                  className="w-full border rounded px-3 py-2"
                  placeholder="Unternehmensname"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Steuer-ID</label>
                <input
                  type="text"
                  value={abrechData.steuer_id}
                  onChange={(e) =>
                    setAbrechData({
                      ...abrechData,
                      steuer_id: e.target.value,
                    })
                  }
                  className="w-full border rounded px-3 py-2"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Straße</label>
                <input
                  type="text"
                  value={abrechData.strasse}
                  onChange={(e) =>
                    setAbrechData({ ...abrechData, strasse: e.target.value })
                  }
                  className="w-full border rounded px-3 py-2"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">PLZ</label>
                <input
                  type="text"
                  value={abrechData.plz}
                  onChange={(e) =>
                    setAbrechData({ ...abrechData, plz: e.target.value })
                  }
                  className="w-full border rounded px-3 py-2"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Stadt</label>
                <input
                  type="text"
                  value={abrechData.stadt}
                  onChange={(e) =>
                    setAbrechData({ ...abrechData, stadt: e.target.value })
                  }
                  className="w-full border rounded px-3 py-2"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Land</label>
                <input
                  type="text"
                  value={abrechData.land}
                  onChange={(e) =>
                    setAbrechData({ ...abrechData, land: e.target.value })
                  }
                  className="w-full border rounded px-3 py-2"
                  defaultValue="Deutschland"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">IBAN</label>
                <input
                  type="text"
                  value={abrechData.iban}
                  onChange={(e) =>
                    setAbrechData({ ...abrechData, iban: e.target.value })
                  }
                  className="w-full border rounded px-3 py-2"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">BIC</label>
                <input
                  type="text"
                  value={abrechData.bic}
                  onChange={(e) =>
                    setAbrechData({ ...abrechData, bic: e.target.value })
                  }
                  className="w-full border rounded px-3 py-2"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">HRB-Nummer</label>
                <input
                  type="text"
                  value={abrechData.hrb_nummer}
                  onChange={(e) =>
                    setAbrechData({
                      ...abrechData,
                      hrb_nummer: e.target.value,
                    })
                  }
                  className="w-full border rounded px-3 py-2"
                />
              </div>
            </div>

            <div className="flex gap-3 justify-end">
              <button
                onClick={() => setShowAbrechForm(false)}
                className="px-4 py-2 rounded border border-gray-300 hover:bg-gray-50"
              >
                Abbrechen
              </button>
              <button
                onClick={handleCreateAbrechnungsfirma}
                className="px-4 py-2 rounded bg-blue-600 text-white hover:bg-blue-700"
              >
                Erstellen
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
