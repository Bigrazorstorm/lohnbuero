import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { workflowsApi } from '../api/client'
import { WorkflowVorlage } from '../types'

export default function AdminWorkflowVorlagen() {
  const navigate = useNavigate()
  const [vorlagen, setVorlagen] = useState<WorkflowVorlage[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [newVorlageForm, setNewVorlageForm] = useState({ name: '', beschreibung: '' })

  useEffect(() => {
    loadVorlagen()
  }, [])

  const loadVorlagen = async () => {
    try {
      setLoading(true)
      const response = await workflowsApi.listVorlagen()
      setVorlagen(response.data)
      setError(null)
    } catch (err) {
      setError('Fehler beim Laden der Vorlagen')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const createVorlage = async () => {
    if (!newVorlageForm.name) {
      setError('Vorlagen-Name erforderlich')
      return
    }

    try {
      const response = await workflowsApi.createVorlage(newVorlageForm)
      setVorlagen([...vorlagen, response.data])
      setNewVorlageForm({ name: '', beschreibung: '' })
      setError(null)
    } catch (err) {
      setError('Fehler beim Erstellen der Vorlage')
      console.error(err)
    }
  }

  if (loading) {
    return <div className="flex items-center justify-center h-screen">Lädt...</div>
  }

  return (
    <div className="p-8 max-w-6xl mx-auto">
      <h1 className="text-3xl font-bold mb-8">Workflow-Vorlagen verwalten</h1>

      {error && (
        <div className="mb-4 p-4 bg-red-100 text-red-700 rounded border border-red-300">{error}</div>
      )}

      {/* Create New Vorlage */}
      <div className="bg-white p-6 rounded-lg border border-gray-200 mb-8">
        <h2 className="text-xl font-bold mb-4">Neue Vorlage erstellen</h2>
        <div className="space-y-4">
          <input
            type="text"
            placeholder="Vorlagen-Name (z.B. 'Standard Lohnabrechnung')"
            value={newVorlageForm.name}
            onChange={(e) => setNewVorlageForm({ ...newVorlageForm, name: e.target.value })}
            className="w-full px-4 py-2 border border-gray-300 rounded"
          />
          <textarea
            placeholder="Beschreibung (optional)"
            value={newVorlageForm.beschreibung}
            onChange={(e) => setNewVorlageForm({ ...newVorlageForm, beschreibung: e.target.value })}
            rows={3}
            className="w-full px-4 py-2 border border-gray-300 rounded"
          />
          <button
            onClick={createVorlage}
            className="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700 font-semibold"
          >
            Vorlage erstellen
          </button>
        </div>
      </div>

      {/* Vorlagen List */}
      <div className="space-y-4">
        <h2 className="text-2xl font-bold mb-4">Vorhandene Vorlagen ({vorlagen.length})</h2>
        {vorlagen.length === 0 ? (
          <div className="bg-gray-50 p-8 rounded-lg text-center text-gray-600">
            Keine Vorlagen vorhanden
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {vorlagen.map((vorlage) => (
              <div
                key={vorlage.id}
                className="bg-white p-6 rounded-lg border border-gray-200 hover:shadow-lg transition-shadow"
              >
                <h3 className="font-bold text-lg mb-2">{vorlage.name}</h3>
                <p className="text-sm text-gray-600 mb-4">{vorlage.beschreibung}</p>

                <div className="space-y-2 mb-4 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Items:</span>
                    <span className="font-semibold">{vorlage.items?.length || 0}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Phasen:</span>
                    <span className="font-semibold">{vorlage.phasen?.length || 0}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Abhängigkeiten:</span>
                    <span className="font-semibold">{vorlage.item_dependencies?.length || 0}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Typ:</span>
                    <span className="font-semibold">
                      {vorlage.ist_standard ? '⭐ Standard' : vorlage.ist_onboarding ? '🎯 Onboarding' : '📋 Custom'}
                    </span>
                  </div>
                </div>

                <div className="pt-4 border-t border-gray-200 flex gap-2">
                  <button
                    onClick={() => navigate(`/admin/workflows/vorlagen/${vorlage.id}/edit`)}
                    className="flex-1 bg-blue-600 text-white py-2 rounded hover:bg-blue-700 text-sm font-semibold"
                  >
                    Bearbeiten
                  </button>
                  <button
                    onClick={() => navigate(`/admin/workflows/vorlagen/${vorlage.id}`)}
                    className="flex-1 bg-gray-500 text-white py-2 rounded hover:bg-gray-600 text-sm font-semibold"
                  >
                    Ansicht
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
