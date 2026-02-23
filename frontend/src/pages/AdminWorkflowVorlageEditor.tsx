import React, { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { workflowsApi } from '../api/client'
import {
  WorkflowVorlage,
  WorkflowPhase,
  WorkflowVorlageItemDependency,
  DependencyGraph,
  WorkflowVorlageItem,
} from '../types'

type TabType = 'phases' | 'items' | 'dependencies'

interface DraggedPhase {
  id: number
  fromIndex: number
}

export default function AdminWorkflowVorlageEditor() {
  const { vorlageId } = useParams<{ vorlageId: string }>()
  const id = parseInt(vorlageId || '0', 10)

  const [vorlage, setVorlage] = useState<WorkflowVorlage | null>(null)
  const [phasen, setPhasen] = useState<WorkflowPhase[]>([])
  const [items, setItems] = useState<WorkflowVorlageItem[]>([])
  const [dependencies, setDependencies] = useState<WorkflowVorlageItemDependency[]>([])
  const [graph, setGraph] = useState<DependencyGraph | null>(null)
  const [activeTab, setActiveTab] = useState<TabType>('phases')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [draggedPhase, setDraggedPhase] = useState<DraggedPhase | null>(null)

  // Form states
  const [editingPhase, setEditingPhase] = useState<Partial<WorkflowPhase> | null>(null)
  const [newPhaseForm, setNewPhaseForm] = useState({
    position: 1,
    name: '',
    icon: '📋',
    standard_frist_tag: undefined as number | undefined,
    ist_kernprozess: false,
  })

  const [newDependencyForm, setNewDependencyForm] = useState({
    source_item_id: 0,
    target_item_id: 0,
    typ: 'blockiert_von' as 'blockiert_von' | 'muss_vor' | 'parallel_ok' | 'optional_nach',
    beschreibung: '',
  })

  useEffect(() => {
    loadData()
  }, [id])

  const loadData = async () => {
    try {
      setLoading(true)
      const [vRes, pRes, dRes, gRes] = await Promise.all([
        workflowsApi.listVorlagen(),
        workflowsApi.listPhasen(id),
        workflowsApi.listDependencies(id),
        workflowsApi.getDependencyGraph(id),
      ])

      const v = vRes.data.find((v: WorkflowVorlage) => v.id === id)
      setVorlage(v || null)
      setPhasen(pRes.data || [])
      setItems(v?.items || [])
      setDependencies(dRes.data || [])
      setGraph(gRes.data || null)
      setError(null)
    } catch (err) {
      setError('Fehler beim Laden der Daten')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const createPhase = async () => {
    if (!newPhaseForm.name) {
      setError('Phase-Name erforderlich')
      return
    }

    try {
      const response = await workflowsApi.createPhase(id, newPhaseForm)
      setPhasen([...phasen, response.data])
      setNewPhaseForm({
        position: phasen.length + 2,
        name: '',
        icon: '📋',
        standard_frist_tag: undefined,
        ist_kernprozess: false,
      })
      setError(null)
    } catch (err) {
      setError('Fehler beim Erstellen der Phase')
      console.error(err)
    }
  }

  const updatePhase = async () => {
    if (!editingPhase?.id || !editingPhase.name) {
      setError('Name erforderlich')
      return
    }

    try {
      const response = await workflowsApi.updatePhase(id, editingPhase.id, editingPhase)
      setPhasen(phasen.map((p) => (p.id === editingPhase.id ? response.data : p)))
      setEditingPhase(null)
      setError(null)
    } catch (err) {
      setError('Fehler beim Aktualisieren der Phase')
      console.error(err)
    }
  }

  const deletePhase = async (phaseId: number) => {
    if (!window.confirm('Phase wirklich löschen?')) return

    try {
      await workflowsApi.deletePhase(id, phaseId)
      setPhasen(phasen.filter((p) => p.id !== phaseId))
      setError(null)
    } catch (err) {
      setError('Fehler beim Löschen der Phase')
      console.error(err)
    }
  }

  const reorderPhasen = async (newOrder: number[]) => {
    try {
      const response = await workflowsApi.reorderPhasen(id, newOrder)
      setPhasen(response.data)
      setError(null)
    } catch (err) {
      setError('Fehler beim Neuordnen der Phasen')
      console.error(err)
    }
  }

  const createDependency = async () => {
    if (newDependencyForm.source_item_id === 0 || newDependencyForm.target_item_id === 0) {
      setError('Source und Target Item erforderlich')
      return
    }

    try {
      const response = await workflowsApi.createDependency(id, newDependencyForm)
      setDependencies([...dependencies, response.data])
      setNewDependencyForm({
        source_item_id: 0,
        target_item_id: 0,
        typ: 'blockiert_von',
        beschreibung: '',
      })
      setError(null)
    } catch (err) {
      setError('Fehler beim Erstellen der Abhängigkeit')
      console.error(err)
    }
  }

  const deleteDependency = async (depId: number) => {
    if (!window.confirm('Abhängigkeit wirklich löschen?')) return

    try {
      await workflowsApi.deleteDependency(id, depId)
      setDependencies(dependencies.filter((d) => d.id !== depId))
      setError(null)
    } catch (err) {
      setError('Fehler beim Löschen der Abhängigkeit')
      console.error(err)
    }
  }

  const handlePhasesDragStart = (index: number, phase: WorkflowPhase) => {
    setDraggedPhase({ id: phase.id, fromIndex: index })
  }

  const handlePhasesDragOver = (e: React.DragEvent) => {
    e.preventDefault()
  }

  const handlePhasesDrop = (toIndex: number) => {
    if (!draggedPhase) return

    const newPhasen = [...phasen]
    const [movedPhase] = newPhasen.splice(draggedPhase.fromIndex, 1)
    newPhasen.splice(toIndex, 0, movedPhase)

    const newOrder = newPhasen.map((p) => p.id)
    reorderPhasen(newOrder)
    setDraggedPhase(null)
  }

  if (loading) {
    return <div className="flex items-center justify-center h-screen">Lädt...</div>
  }

  if (!vorlage) {
    return <div className="flex items-center justify-center h-screen">Vorlage nicht gefunden</div>
  }

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">{vorlage.name}</h1>
        <p className="text-gray-600">{vorlage.beschreibung}</p>
      </div>

      {error && (
        <div className="mb-4 p-4 bg-red-100 text-red-700 rounded border border-red-300">{error}</div>
      )}

      {/* Tabs */}
      <div className="flex gap-2 mb-6 border-b">
        {(['phases', 'items', 'dependencies'] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 border-b-2 transition-colors ${
              activeTab === tab
                ? 'border-blue-500 text-blue-600 font-semibold'
                : 'border-transparent text-gray-600 hover:text-gray-800'
            }`}
          >
            {tab === 'phases' && '📋 Phasen'}
            {tab === 'items' && '✓ Items'}
            {tab === 'dependencies' && '🔗 Abhängigkeiten'}
          </button>
        ))}
      </div>

      {/* Phases Tab */}
      {activeTab === 'phases' && (
        <div className="space-y-6">
          {/* Create New Phase */}
          <div className="bg-white p-6 rounded-lg border border-gray-200">
            <h2 className="text-xl font-bold mb-4">Neue Phase erstellen</h2>
            <div className="space-y-4">
              <input
                type="text"
                placeholder="Phase-Name (z.B. 'Dateneingang')"
                value={newPhaseForm.name}
                onChange={(e) => setNewPhaseForm({ ...newPhaseForm, name: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded"
              />
              <input
                type="text"
                placeholder="Icon (z.B. '📋')"
                value={newPhaseForm.icon}
                onChange={(e) => setNewPhaseForm({ ...newPhaseForm, icon: e.target.value })}
                maxLength={2}
                className="w-full px-4 py-2 border border-gray-300 rounded"
              />
              <input
                type="number"
                placeholder="Standard-Frist (z.B. 5 = 5. des Monats)"
                value={newPhaseForm.standard_frist_tag ?? ''}
                onChange={(e) =>
                  setNewPhaseForm({
                    ...newPhaseForm,
                    standard_frist_tag: e.target.value ? parseInt(e.target.value, 10) : undefined,
                  })
                }
                className="w-full px-4 py-2 border border-gray-300 rounded"
              />
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={newPhaseForm.ist_kernprozess}
                  onChange={(e) =>
                    setNewPhaseForm({ ...newPhaseForm, ist_kernprozess: e.target.checked })
                  }
                />
                <span>Kernprozess</span>
              </label>
              <button
                onClick={createPhase}
                className="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700"
              >
                Phase erstellen
              </button>
            </div>
          </div>

          {/* Existing Phases */}
          <div className="space-y-3">
            <h2 className="text-xl font-bold">Vorhandene Phasen</h2>
            {phasen.map((phase, index) => (
              <div
                key={phase.id}
                draggable
                onDragStart={() => handlePhasesDragStart(index, phase)}
                onDragOver={handlePhasesDragOver}
                onDrop={() => handlePhasesDrop(index)}
                className="bg-white p-4 rounded-lg border border-gray-200 cursor-move hover:shadow-md transition-shadow"
              >
                {editingPhase?.id === phase.id ? (
                  // Edit Mode
                  <div className="space-y-3">
                    <input
                      type="text"
                      value={editingPhase.name || ''}
                      onChange={(e) => setEditingPhase({ ...editingPhase, name: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded"
                    />
                    <div className="flex gap-2">
                      <button
                        onClick={updatePhase}
                        className="flex-1 bg-green-600 text-white py-2 rounded hover:bg-green-700"
                      >
                        Speichern
                      </button>
                      <button
                        onClick={() => setEditingPhase(null)}
                        className="flex-1 bg-gray-400 text-white py-2 rounded hover:bg-gray-500"
                      >
                        Abbrechen
                      </button>
                    </div>
                  </div>
                ) : (
                  // Display Mode
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="text-lg font-semibold">
                        {phase.icon} {phase.name}
                      </div>
                      <div className="text-sm text-gray-600">
                        Position: {phase.position} | Frist: {phase.standard_frist_tag || '-'} |{' '}
                        {phase.ist_kernprozess ? '✓ Kernprozess' : ''}
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <button
                        onClick={() => setEditingPhase(phase)}
                        className="px-3 py-1 bg-blue-500 text-white rounded hover:bg-blue-600 text-sm"
                      >
                        Bearbeiten
                      </button>
                      <button
                        onClick={() => deletePhase(phase.id)}
                        className="px-3 py-1 bg-red-500 text-white rounded hover:bg-red-600 text-sm"
                      >
                        Löschen
                      </button>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Items Tab */}
      {activeTab === 'items' && (
        <div className="bg-white p-6 rounded-lg border border-gray-200">
          <h2 className="text-xl font-bold mb-4">Items in dieser Vorlage</h2>
          <div className="space-y-2">
            {items.map((item) => (
              <div key={item.id} className="p-3 bg-gray-50 rounded border border-gray-200">
                <div className="font-semibold">
                  {item.position}. {item.titel}
                </div>
                <div className="text-sm text-gray-600 mt-1">
                  Phase: {phasen.find((p) => p.id === item.phase_id)?.name || 'Unzugeordnet'}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Dependencies Tab */}
      {activeTab === 'dependencies' && (
        <div className="space-y-6">
          {/* Create New Dependency */}
          <div className="bg-white p-6 rounded-lg border border-gray-200">
            <h2 className="text-xl font-bold mb-4">Neue Abhängigkeit erstellen</h2>
            <div className="space-y-4">
              <select
                value={newDependencyForm.source_item_id || 0}
                onChange={(e) =>
                  setNewDependencyForm({
                    ...newDependencyForm,
                    source_item_id: parseInt(e.target.value, 10),
                  })
                }
                className="w-full px-4 py-2 border border-gray-300 rounded"
              >
                <option value={0}>Quell-Item wählen</option>
                {items.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.position}. {item.titel}
                  </option>
                ))}
              </select>

              <select
                value={newDependencyForm.target_item_id || 0}
                onChange={(e) =>
                  setNewDependencyForm({
                    ...newDependencyForm,
                    target_item_id: parseInt(e.target.value, 10),
                  })
                }
                className="w-full px-4 py-2 border border-gray-300 rounded"
              >
                <option value={0}>Ziel-Item wählen</option>
                {items.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.position}. {item.titel}
                  </option>
                ))}
              </select>

              <select
                value={newDependencyForm.typ}
                onChange={(e) =>
                  setNewDependencyForm({
                    ...newDependencyForm,
                    typ: e.target.value as typeof newDependencyForm.typ,
                  })
                }
                className="w-full px-4 py-2 border border-gray-300 rounded"
              >
                <option value="blockiert_von">Blockiert von</option>
                <option value="muss_vor">Muss vorher sein</option>
                <option value="parallel_ok">Parallel ok</option>
                <option value="optional_nach">Optional danach</option>
              </select>

              <input
                type="text"
                placeholder="Beschreibung (optional)"
                value={newDependencyForm.beschreibung}
                onChange={(e) =>
                  setNewDependencyForm({ ...newDependencyForm, beschreibung: e.target.value })
                }
                className="w-full px-4 py-2 border border-gray-300 rounded"
              />

              <button
                onClick={createDependency}
                className="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700"
              >
                Abhängigkeit erstellen
              </button>
            </div>
          </div>

          {/* Existing Dependencies */}
          <div className="space-y-3">
            <h2 className="text-xl font-bold">Vorhandene Abhängigkeiten</h2>
            {dependencies.map((dep) => {
              const sourceItem = items.find((i) => i.id === dep.source_item_id)
              const targetItem = items.find((i) => i.id === dep.target_item_id)
              return (
                <div key={dep.id} className="bg-white p-4 rounded-lg border border-gray-200">
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="font-semibold">
                        {sourceItem?.titel} → {targetItem?.titel}
                      </div>
                      <div className="text-sm text-gray-600 mt-1">
                        Typ: {dep.typ} | {dep.beschreibung || 'Keine Beschreibung'}
                      </div>
                    </div>
                    <button
                      onClick={() => deleteDependency(dep.id)}
                      className="px-3 py-1 bg-red-500 text-white rounded hover:bg-red-600 text-sm"
                    >
                      Löschen
                    </button>
                  </div>
                </div>
              )
            })}
          </div>

          {/* Graph Visualization Info */}
          {graph && (
            <div className="bg-white p-6 rounded-lg border border-gray-200">
              <h2 className="text-xl font-bold mb-4">Abhängigkeitsgraph</h2>
              <div className="text-sm text-gray-600">
                <p>Knoten: {graph.nodes.length} Items</p>
                <p>Kanten: {graph.edges.length} Abhängigkeiten</p>
                <p>Phasen: {graph.phases.length}</p>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
