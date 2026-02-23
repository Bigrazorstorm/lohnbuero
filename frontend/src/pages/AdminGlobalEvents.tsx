import { useEffect, useState } from 'react'
import { adminApi } from '../api/client'
import { GlobalEvent, GlobalEventTyp } from '../types'

export function AdminGlobalEvents() {
  const [events, setEvents] = useState<GlobalEvent[]>([])
  const [loading, setLoading] = useState(false)
  const [showForm, setShowForm] = useState(false)
  const [selectedEvent, setSelectedEvent] = useState<GlobalEvent | null>(null)
  const [eventTypen, setEventTypen] = useState<Array<{ value: string; label: string }>>([])

  // Form state
  const [formData, setFormData] = useState({
    name: '',
    typ: 'jahreswechsel' as GlobalEventTyp,
    beschreibung: '',
    gueltig_von: '',
    gueltig_bis: '',
    mandanten_filter: JSON.stringify({ alle: true }),
    prioritaet: 5,
    ist_aktiv: false,
    schritte: [] as Array<{
      position: number
      titel: string
      faellig_offset_tage: number
      ist_pflicht: boolean
      standard_punkte: number
    }>,
  })

  useEffect(() => {
    loadEvents()
    loadEventTypen()
  }, [])

  const loadEvents = async () => {
    setLoading(true)
    try {
      const response = await adminApi.listGlobalEvents({ include_inactive: true })
      setEvents(response.data)
    } catch (error) {
      console.error('Fehler beim Laden der Events:', error)
    } finally {
      setLoading(false)
    }
  }

  const loadEventTypen = async () => {
    try {
      const response = await adminApi.getGlobalEventTypen()
      setEventTypen(response.data)
    } catch (error) {
      console.error('Fehler beim Laden der Event-Typen:', error)
    }
  }

  const handleCreate = async () => {
    try {
      await adminApi.createGlobalEvent(formData)
      setShowForm(false)
      setFormData({
        name: '',
        typ: 'jahreswechsel',
        beschreibung: '',
        gueltig_von: '',
        gueltig_bis: '',
        mandanten_filter: JSON.stringify({ alle: true }),
        prioritaet: 5,
        ist_aktiv: false,
        schritte: [],
      })
      loadEvents()
    } catch (error) {
      console.error('Fehler beim Erstellen des Events:', error)
    }
  }

  const handleToggleActive = async (event: GlobalEvent) => {
    try {
      await adminApi.updateGlobalEvent(event.id, {
        ist_aktiv: !event.ist_aktiv,
      })
      loadEvents()
    } catch (error) {
      console.error('Fehler beim Aktualisieren des Events:', error)
    }
  }

  const handleDelete = async (eventId: number) => {
    if (!confirm('Event wirklich löschen?')) return
    try {
      await adminApi.deleteGlobalEvent(eventId)
      loadEvents()
    } catch (error) {
      console.error('Fehler beim Löschen des Events:', error)
    }
  }

  const addSchritt = () => {
    const newSchritte = [
      ...formData.schritte,
      {
        position: formData.schritte.length + 1,
        titel: '',
        faellig_offset_tage: 0,
        ist_pflicht: true,
        standard_punkte: 1,
      },
    ]
    setFormData({ ...formData, schritte: newSchritte })
  }

  const updateSchritt = (
    index: number,
    field: string,
    value: unknown
  ) => {
    const newSchritte = [...formData.schritte]
    newSchritte[index] = { ...newSchritte[index], [field]: value }
    setFormData({ ...formData, schritte: newSchritte })
  }

  const removeSchritt = (index: number) => {
    const newSchritte = formData.schritte.filter((_, i) => i !== index)
    setFormData({ ...formData, schritte: newSchritte })
  }

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">Globale Events</h1>
        <button
          onClick={() => setShowForm(!showForm)}
          className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
        >
          {showForm ? 'Abbrechen' : '+ Neues Event'}
        </button>
      </div>

      {/* Form */}
      {showForm && (
        <div className="bg-white p-6 rounded-lg shadow mb-6 border border-gray-200">
          <h2 className="text-xl font-semibold mb-4">Neues Global Event</h2>

          <div className="grid grid-cols-2 gap-4 mb-4">
            <div>
              <label className="block text-sm font-medium mb-1">Name *</label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full border rounded px-3 py-2"
                placeholder="z.B. Jahreswechsel 2026/2027"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">Typ *</label>
              <select
                value={formData.typ}
                onChange={(e) =>
                  setFormData({ ...formData, typ: e.target.value as GlobalEventTyp })
                }
                className="w-full border rounded px-3 py-2"
              >
                {eventTypen.map((t) => (
                  <option key={t.value} value={t.value}>
                    {t.label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">Gültig von *</label>
              <input
                type="date"
                value={formData.gueltig_von}
                onChange={(e) =>
                  setFormData({ ...formData, gueltig_von: e.target.value })
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
                  setFormData({ ...formData, gueltig_bis: e.target.value })
                }
                className="w-full border rounded px-3 py-2"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">Priorität</label>
              <input
                type="number"
                value={formData.prioritaet}
                onChange={(e) =>
                  setFormData({ ...formData, prioritaet: parseInt(e.target.value) })
                }
                className="w-full border rounded px-3 py-2"
              />
            </div>

            <div className="flex items-center justify-start pt-6">
              <label className="flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={formData.ist_aktiv}
                  onChange={(e) =>
                    setFormData({ ...formData, ist_aktiv: e.target.checked })
                  }
                  className="mr-2"
                />
                <span className="text-sm">Sofort aktivieren</span>
              </label>
            </div>
          </div>

          <div className="mb-4">
            <label className="block text-sm font-medium mb-1">Beschreibung</label>
            <textarea
              value={formData.beschreibung}
              onChange={(e) =>
                setFormData({ ...formData, beschreibung: e.target.value })
              }
              className="w-full border rounded px-3 py-2"
              rows={3}
              placeholder="Detaillierte Beschreibung des Events..."
            />
          </div>

          {/* Schritte */}
          <div className="mb-4">
            <div className="flex justify-between items-center mb-2">
              <h3 className="font-semibold">Workflow-Schritte</h3>
              <button
                onClick={addSchritt}
                className="bg-green-600 text-white px-3 py-1 rounded text-sm hover:bg-green-700"
              >
                + Schritt
              </button>
            </div>

            {formData.schritte.map((schritt, idx) => (
              <div
                key={idx}
                className="bg-gray-50 p-3 rounded mb-2 border border-gray-200"
              >
                <div className="grid grid-cols-3 gap-2 mb-2">
                  <input
                    type="text"
                    value={schritt.titel}
                    onChange={(e) =>
                      updateSchritt(idx, 'titel', e.target.value)
                    }
                    placeholder="Schritt-Titel"
                    className="border rounded px-2 py-1 text-sm"
                  />
                  <input
                    type="number"
                    value={schritt.faellig_offset_tage}
                    onChange={(e) =>
                      updateSchritt(idx, 'faellig_offset_tage', parseInt(e.target.value))
                    }
                    placeholder="Tage bis Fälligkeit"
                    className="border rounded px-2 py-1 text-sm"
                  />
                  <input
                    type="number"
                    value={schritt.standard_punkte}
                    onChange={(e) =>
                      updateSchritt(idx, 'standard_punkte', parseFloat(e.target.value))
                    }
                    placeholder="Punkte"
                    className="border rounded px-2 py-1 text-sm"
                  />
                </div>
                <div className="flex justify-between items-center">
                  <label className="flex items-center text-sm">
                    <input
                      type="checkbox"
                      checked={schritt.ist_pflicht}
                      onChange={(e) =>
                        updateSchritt(idx, 'ist_pflicht', e.target.checked)
                      }
                      className="mr-1"
                    />
                    Pflicht
                  </label>
                  <button
                    onClick={() => removeSchritt(idx)}
                    className="text-red-600 hover:text-red-800 text-sm"
                  >
                    Entfernen
                  </button>
                </div>
              </div>
            ))}
          </div>

          <button
            onClick={handleCreate}
            className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
          >
            Event erstellen
          </button>
        </div>
      )}

      {/* Events List */}
      {loading ? (
        <div className="text-gray-500">Laden...</div>
      ) : events.length === 0 ? (
        <div className="bg-gray-50 p-6 rounded text-center text-gray-500">
          Keine Global Events vorhanden
        </div>
      ) : (
        <div className="space-y-4">
          {events.map((event) => (
            <div
              key={event.id}
              className="bg-white p-4 rounded-lg shadow border border-gray-200 hover:shadow-md transition"
            >
              <div className="flex justify-between items-start mb-2">
                <div className="flex-1">
                  <h3 className="text-lg font-semibold">{event.name}</h3>
                  <p className="text-sm text-gray-600">
                    Typ: <span className="font-medium">{event.typ.replace('_', ' ')}</span>
                  </p>
                  {event.beschreibung && (
                    <p className="text-sm text-gray-600 mt-1">{event.beschreibung}</p>
                  )}
                  <div className="flex gap-4 mt-2 text-xs text-gray-500">
                    <span>
                      Gültig von:{' '}
                      {new Date(event.gueltig_von).toLocaleDateString('de-DE')}
                    </span>
                    {event.gueltig_bis && (
                      <span>
                        bis:{' '}
                        {new Date(event.gueltig_bis).toLocaleDateString('de-DE')}
                      </span>
                    )}
                    <span>Priorität: {event.prioritaet}</span>
                    <span>{event.schritte.length} Schritte</span>
                  </div>
                </div>

                <div className="flex gap-2">
                  <button
                    onClick={() => handleToggleActive(event)}
                    className={`px-3 py-1 rounded text-sm text-white ${
                      event.ist_aktiv ? 'bg-green-600' : 'bg-gray-600'
                    } hover:opacity-80`}
                  >
                    {event.ist_aktiv ? 'Aktiv' : 'Inaktiv'}
                  </button>
                  {event.ist_abgeschlossen && (
                    <span className="px-3 py-1 rounded text-sm bg-yellow-100 text-yellow-800">
                      Abgeschlossen
                    </span>
                  )}
                  <button
                    onClick={() => {
                      setSelectedEvent(event)
                      setShowForm(false)
                    }}
                    className="px-3 py-1 rounded text-sm bg-blue-600 text-white hover:bg-blue-700"
                  >
                    Bearbeiten
                  </button>
                  <button
                    onClick={() => handleDelete(event.id)}
                    className="px-3 py-1 rounded text-sm bg-red-600 text-white hover:bg-red-700"
                  >
                    Löschen
                  </button>
                </div>
              </div>

              {/* Schritte vorne */}
              {event.schritte.length > 0 && (
                <div className="mt-3 pt-3 border-t border-gray-200">
                  <p className="text-sm font-medium mb-2">Schritte:</p>
                  <ul className="space-y-1">
                    {event.schritte.map((schritt) => (
                      <li
                        key={schritt.id}
                        className="text-sm text-gray-700 ml-4 flex justify-between"
                      >
                        <span>
                          {schritt.position}. {schritt.titel}
                        </span>
                        <span className="text-gray-500">
                          {schritt.ist_pflicht ? '⭐ ' : ''}
                          {schritt.standard_punkte} Pkt
                        </span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
