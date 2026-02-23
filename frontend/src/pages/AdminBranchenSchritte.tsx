import { useEffect, useState } from 'react'
import { adminApi } from '../api/client'
import { BranchenWorkflowSchritt, Branche } from '../types'

export function AdminBranchenSchritte() {
  const [branchenSchritte, setBranchenSchritte] = useState<BranchenWorkflowSchritt[]>([])
  const [branches, setBranches] = useState<Branche[]>([])
  const [loading, setLoading] = useState(false)
  const [showForm, setShowForm] = useState(false)
  const [selectedBranche, setSelectedBranche] = useState<number | null>(null)
  const [filterBranche, setFilterBranche] = useState<number | null>(null)

  // Form state
  const [formData, setFormData] = useState({
    branche_id: 0,
    schritt_typ_id: 0,
    position: 1,
    gueltig_von: '',
    gueltig_bis: '',
    ist_optional_pro_mandant: false,
    standard_punkte: 1,
    beschreibung: '',
  })

  useEffect(() => {
    loadData()
  }, [filterBranche])

  const loadData = async () => {
    setLoading(true)
    try {
      const [scritte, branches] = await Promise.all([
        adminApi.listBranchenWorkflowSchritte(filterBranche || 0, false),
        adminApi.listBranchen?.() || Promise.resolve({ data: [] }),
      ])
      setBranchenSchritte(scritte.data)
      setBranches(branches.data)
    } catch (error) {
      console.error('Fehler beim Laden der Daten:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleCreate = async () => {
    if (!formData.branche_id || !formData.schritt_typ_id) {
      alert('Bitte Branche und Schritt-Typ auswählen')
      return
    }

    try {
      await adminApi.createBranchenWorkflowSchritt(formData)
      setShowForm(false)
      setFormData({
        branche_id: 0,
        schritt_typ_id: 0,
        position: 1,
        gueltig_von: '',
        gueltig_bis: '',
        ist_optional_pro_mandant: false,
        standard_punkte: 1,
        beschreibung: '',
      })
      loadData()
    } catch (error) {
      console.error('Fehler beim Erstellen des Schritts:', error)
    }
  }

  const handleUpdate = async (
    id: number,
    updates: Partial<typeof formData>
  ) => {
    try {
      await adminApi.updateBranchenWorkflowSchritt(id, updates)
      loadData()
    } catch (error) {
      console.error('Fehler beim Aktualisieren:', error)
    }
  }

  const handleDelete = async (id: number) => {
    if (!confirm('Schritt wirklich löschen?')) return
    try {
      await adminApi.deleteBranchenWorkflowSchritt(id)
      loadData()
    } catch (error) {
      console.error('Fehler beim Löschen:', error)
    }
  }

  const getBrancheName = (id: number) => {
    return branches.find((b) => b.id === id)?.name || `Branche ${id}`
  }

  const groupedSchritte = branchenSchritte.reduce(
    (acc, schritt) => {
      const key = schritt.branche_id
      if (!acc[key]) acc[key] = []
      acc[key].push(schritt)
      return acc
    },
    {} as Record<number, BranchenWorkflowSchritt[]>
  )

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">Branchenspezifische Schritte</h1>
        <button
          onClick={() => setShowForm(!showForm)}
          className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
        >
          {showForm ? 'Abbrechen' : '+ Neuer Schritt'}
        </button>
      </div>

      {/* Filter */}
      <div className="mb-6">
        <label className="block text-sm font-medium mb-2">Nach Branche filtern:</label>
        <select
          value={filterBranche || ''}
          onChange={(e) => setFilterBranche(e.target.value ? parseInt(e.target.value) : null)}
          className="border rounded px-3 py-2"
        >
          <option value="">Alle Branchen</option>
          {branches.map((b) => (
            <option key={b.id} value={b.id}>
              {b.name}
            </option>
          ))}
        </select>
      </div>

      {/* Form */}
      {showForm && (
        <div className="bg-white p-6 rounded-lg shadow mb-6 border border-gray-200">
          <h2 className="text-xl font-semibold mb-4">Neuer branchenspezifischer Schritt</h2>

          <div className="grid grid-cols-2 gap-4 mb-4">
            <div>
              <label className="block text-sm font-medium mb-1">Branche *</label>
              <select
                value={formData.branche_id}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    branche_id: parseInt(e.target.value),
                  })
                }
                className="w-full border rounded px-3 py-2"
              >
                <option value={0}>-- Wählen --</option>
                {branches.map((b) => (
                  <option key={b.id} value={b.id}>
                    {b.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">Schritt-Typ *</label>
              <input
                type="number"
                value={formData.schritt_typ_id}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    schritt_typ_id: parseInt(e.target.value),
                  })
                }
                placeholder="Schritt-Typ ID"
                className="w-full border rounded px-3 py-2"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">Position</label>
              <input
                type="number"
                value={formData.position}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    position: parseInt(e.target.value),
                  })
                }
                className="w-full border rounded px-3 py-2"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">Punkte</label>
              <input
                type="number"
                step="0.5"
                value={formData.standard_punkte}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    standard_punkte: parseFloat(e.target.value),
                  })
                }
                className="w-full border rounded px-3 py-2"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">Gültig von</label>
              <input
                type="date"
                value={formData.gueltig_von}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    gueltig_von: e.target.value,
                  })
                }
                className="w-full border rounded px-3 py-2"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">Gültig bis</label>
              <input
                type="date"
                value={formData.gueltig_bis}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    gueltig_bis: e.target.value,
                  })
                }
                className="w-full border rounded px-3 py-2"
              />
            </div>
          </div>

          <div className="mb-4">
            <label className="flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={formData.ist_optional_pro_mandant}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    ist_optional_pro_mandant: e.target.checked,
                  })
                }
                className="mr-2"
              />
              <span className="text-sm">
                Optional pro Mandant (kann pro Mandant deaktiviert werden)
              </span>
            </label>
          </div>

          <div className="mb-4">
            <label className="block text-sm font-medium mb-1">Beschreibung</label>
            <textarea
              value={formData.beschreibung}
              onChange={(e) =>
                setFormData({
                  ...formData,
                  beschreibung: e.target.value,
                })
              }
              className="w-full border rounded px-3 py-2"
              rows={3}
            />
          </div>

          <button
            onClick={handleCreate}
            className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
          >
            Schritt erstellen
          </button>
        </div>
      )}

      {/* Grouped List */}
      {loading ? (
        <div className="text-gray-500">Laden...</div>
      ) : Object.keys(groupedSchritte).length === 0 ? (
        <div className="bg-gray-50 p-6 rounded text-center text-gray-500">
          Keine branchenspezifischen Schritte vorhanden
        </div>
      ) : (
        <div className="space-y-6">
          {Object.entries(groupedSchritte).map(([brancheId, schritte]) => (
            <div key={brancheId} className="bg-white rounded-lg shadow border border-gray-200">
              <div className="bg-gray-50 px-4 py-3 border-b border-gray-200">
                <h3 className="font-semibold text-lg">
                  {getBrancheName(parseInt(brancheId))}
                </h3>
              </div>

              <div className="divide-y divide-gray-200">
                {schritte.map((schritt) => (
                  <div
                    key={schritt.id}
                    className="p-4 hover:bg-blue-50 transition flex justify-between items-start"
                  >
                    <div className="flex-1">
                      <p className="font-medium">
                        {schritt.position}. Schritt {schritt.schritttyp}
                      </p>
                      {schritt.beschreibung && (
                        <p className="text-sm text-gray-600 mt-1">
                          {schritt.beschreibung}
                        </p>
                      )}
                      <div className="flex gap-4 mt-2 text-xs text-gray-500">
                        <span>{schritt.standard_punkte} Punkte</span>
                        {schritt.ist_optional_pro_mandant && (
                          <span className="bg-yellow-100 text-yellow-800 px-2 py-0.5 rounded">
                            Optional
                          </span>
                        )}
                        {schritt.gueltig_von && (
                          <span>
                            Gültig ab:{' '}
                            {new Date(schritt.gueltig_von).toLocaleDateString('de-DE')}
                          </span>
                        )}
                        {schritt.gueltig_bis && (
                          <span>
                            bis:{' '}
                            {new Date(schritt.gueltig_bis).toLocaleDateString('de-DE')}
                          </span>
                        )}
                      </div>
                    </div>

                    <div className="flex gap-2 ml-4">
                      <button
                        onClick={() => handleDelete(schritt.id)}
                        className="px-3 py-1 rounded text-sm bg-red-600 text-white hover:bg-red-700"
                      >
                        Löschen
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
