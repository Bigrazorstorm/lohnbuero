import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { Plus, FileText, ChevronDown, ChevronUp, Trash2, Star } from 'lucide-react'
import toast from 'react-hot-toast'
import { workflowsApi } from '../api/client'
import type { WorkflowVorlage, WorkflowVorlageItem } from '../types'

export default function Vorlagen() {
  const qc = useQueryClient()
  const [expanded, setExpanded] = useState<number | null>(null)
  const [showCreate, setShowCreate] = useState(false)
  const [newVorlage, setNewVorlage] = useState({
    name: '',
    beschreibung: '',
    branche: '',
    ist_standard: false,
  })
  const [items, setItems] = useState([
    { position: 1, titel: '', beschreibung: '', faellig_offset_tage: 0, ist_kernprozess: false, ist_pflicht: true, ist_optional_pro_mandant: false, erfordert_dokument: false, erfordert_pruefung: false }
  ])

  const { data: vorlagen = [], isLoading } = useQuery<WorkflowVorlage[]>({
    queryKey: ['vorlagen'],
    queryFn: () => workflowsApi.listVorlagen().then((r) => (r as { data: WorkflowVorlage[] }).data),
  })

  const createMutation = useMutation({
    mutationFn: (data: unknown) => workflowsApi.createVorlage(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['vorlagen'] })
      toast.success('Vorlage angelegt')
      setShowCreate(false)
    },
    onError: () => toast.error('Fehler'),
  })

  const updateItemMutation = useMutation({
    mutationFn: ({ vorlageId, itemId, data }: { vorlageId: number; itemId: number; data: unknown }) =>
      workflowsApi.updateVorlageItem(vorlageId, itemId, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['vorlagen'] })
      toast.success('Schritt aktualisiert')
    },
    onError: () => toast.error('Fehler beim Aktualisieren'),
  })

  const toggleKernprozess = (vorlageId: number, item: WorkflowVorlageItem) => {
    updateItemMutation.mutate({
      vorlageId,
      itemId: item.id,
      data: { ist_kernprozess: !item.ist_kernprozess },
    })
  }

  const addItem = () => setItems(prev => [
    ...prev,
    { position: prev.length + 1, titel: '', beschreibung: '', faellig_offset_tage: prev.length * 3, ist_kernprozess: false, ist_pflicht: true, ist_optional_pro_mandant: false, erfordert_dokument: false, erfordert_pruefung: false }
  ])

  const removeItem = (idx: number) => setItems(prev => prev.filter((_, i) => i !== idx).map((it, i) => ({ ...it, position: i + 1 })))

  const updateItem = (idx: number, key: string, value: unknown) =>
    setItems(prev => prev.map((it, i) => i === idx ? { ...it, [key]: value } : it))

  const handleCreate = () => {
    if (!newVorlage.name || items.some(i => !i.titel)) {
      toast.error('Bitte alle Pflichtfelder ausfüllen')
      return
    }
    createMutation.mutate({ ...newVorlage, items })
  }

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Workflow-Vorlagen</h1>
        <button className="btn-primary" onClick={() => setShowCreate(!showCreate)}>
          <Plus size={16} />
          Neue Vorlage
        </button>
      </div>

      {/* Create form */}
      {showCreate && (
        <div className="card space-y-4">
          <h2 className="text-base font-semibold">Neue Vorlage erstellen</h2>
          <div className="grid grid-cols-3 gap-4">
            <div className="col-span-2">
              <label className="label">Name *</label>
              <input className="input" value={newVorlage.name}
                onChange={e => setNewVorlage(v => ({ ...v, name: e.target.value }))} />
            </div>
            <div>
              <label className="label">Branche</label>
              <input className="input" value={newVorlage.branche}
                onChange={e => setNewVorlage(v => ({ ...v, branche: e.target.value }))} />
            </div>
            <div className="col-span-3">
              <label className="label">Beschreibung</label>
              <input className="input" value={newVorlage.beschreibung}
                onChange={e => setNewVorlage(v => ({ ...v, beschreibung: e.target.value }))} />
            </div>
            <div className="col-span-3">
              <label className="flex items-center gap-2 cursor-pointer">
                <input type="checkbox" checked={newVorlage.ist_standard}
                  onChange={e => setNewVorlage(v => ({ ...v, ist_standard: e.target.checked }))} />
                <span className="text-sm text-gray-700">Als Standard-Vorlage verwenden</span>
              </label>
            </div>
          </div>

          {/* Items */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-semibold text-gray-700">Checklisten-Schritte</h3>
              <button className="btn-secondary text-xs py-1" onClick={addItem}>
                <Plus size={12} /> Schritt hinzufügen
              </button>
            </div>
            {/* Column headers */}
            <div className="grid grid-cols-13 gap-2 px-3 pb-2 text-[10px] text-gray-500 font-medium">
              <div className="col-span-1 text-center">Nr.</div>
              <div className="col-span-3">Titel</div>
              <div className="col-span-2">Beschreibung</div>
              <div className="col-span-2">Fällig</div>
              <div className="col-span-1 text-center">Kern</div>
              <div className="col-span-1 text-center">Mand.</div>
              <div className="col-span-1 text-center">Pflicht</div>
              <div className="col-span-1"></div>
            </div>
            <div className="space-y-2">
              {items.map((item, idx) => (
                <div key={idx} className="grid grid-cols-13 gap-2 items-center p-3 bg-gray-50 rounded-lg">
                  <div className="col-span-1 text-center text-xs text-gray-400 font-mono">{item.position}</div>
                  <div className="col-span-3">
                    <input className="input text-xs" placeholder="Titel *" value={item.titel}
                      onChange={e => updateItem(idx, 'titel', e.target.value)} />
                  </div>
                  <div className="col-span-2">
                    <input className="input text-xs" placeholder="Beschreibung" value={item.beschreibung}
                      onChange={e => updateItem(idx, 'beschreibung', e.target.value)} />
                  </div>
                  <div className="col-span-2">
                    <div className="flex items-center gap-1">
                      <input type="number" min="0" className="input text-xs w-14" value={item.faellig_offset_tage}
                        onChange={e => updateItem(idx, 'faellig_offset_tage', Number(e.target.value))} />
                      <span className="text-xs text-gray-400">Tage</span>
                    </div>
                  </div>
                  <div className="col-span-1 flex flex-col items-center">
                    <input type="checkbox" checked={item.ist_kernprozess} onChange={e => updateItem(idx, 'ist_kernprozess', e.target.checked)} id={`kern-${idx}`} />
                    <label htmlFor={`kern-${idx}`} className="text-[10px] text-amber-600 cursor-pointer">Kern</label>
                  </div>
                  <div className="col-span-1 flex flex-col items-center">
                    <input type="checkbox" checked={item.ist_optional_pro_mandant} onChange={e => updateItem(idx, 'ist_optional_pro_mandant', e.target.checked)} id={`opt-${idx}`} />
                    <label htmlFor={`opt-${idx}`} className="text-[10px] text-gray-500 cursor-pointer">Mand.</label>
                  </div>
                  <div className="col-span-1 flex flex-col items-center">
                    <input type="checkbox" checked={item.ist_pflicht} onChange={e => updateItem(idx, 'ist_pflicht', e.target.checked)} id={`pfl-${idx}`} />
                    <label htmlFor={`pfl-${idx}`} className="text-[10px] text-gray-500 cursor-pointer">Pflicht</label>
                  </div>
                  <div className="col-span-1 text-right">
                    <button onClick={() => removeItem(idx)} className="text-red-400 hover:text-red-600">
                      <Trash2 size={14} />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="flex gap-3">
            <button className="btn-primary" onClick={handleCreate} disabled={createMutation.isPending}>
              Vorlage anlegen
            </button>
            <button className="btn-secondary" onClick={() => setShowCreate(false)}>Abbrechen</button>
          </div>
        </div>
      )}

      {/* List */}
      {isLoading ? (
        <div className="card text-center py-12 text-gray-400">Laden…</div>
      ) : vorlagen.length === 0 ? (
        <div className="card text-center py-12">
          <FileText size={40} className="mx-auto text-gray-300 mb-3" />
          <p className="text-gray-400">Noch keine Vorlagen vorhanden</p>
        </div>
      ) : (
        <div className="space-y-3">
          {vorlagen.map((v) => (
            <div key={v.id} className="card">
              <div
                className="flex items-center justify-between cursor-pointer"
                onClick={() => setExpanded(expanded === v.id ? null : v.id)}
              >
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-gray-900">{v.name}</span>
                    {v.ist_standard && <span className="badge bg-green-100 text-green-700">Standard</span>}
                    {v.branche && <span className="badge bg-gray-100 text-gray-600">{v.branche}</span>}
                  </div>
                  {v.beschreibung && <p className="text-xs text-gray-400 mt-0.5">{v.beschreibung}</p>}
                  <p className="text-xs text-gray-400 mt-1">{v.items.length} Schritte</p>
                </div>
                {expanded === v.id ? <ChevronUp size={18} className="text-gray-400" /> : <ChevronDown size={18} className="text-gray-400" />}
              </div>

              {expanded === v.id && (
                <div className="mt-4 border-t pt-4">
                  <div className="flex items-center justify-between mb-2">
                    <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Prozessschritte</p>
                    <p className="text-xs text-gray-400">Auf <Star size={10} className="inline" /> klicken zum Setzen als Kernprozess</p>
                  </div>
                  <div className="space-y-1">
                  {v.items.map((item) => (
                    <div key={item.id} className={`flex items-center gap-3 text-sm py-1.5 rounded-lg px-2 ${item.ist_kernprozess ? 'bg-amber-50 border border-amber-100' : ''}`}>
                      <span className="w-6 h-6 rounded-full bg-gray-100 text-gray-600 text-xs font-mono flex items-center justify-center flex-shrink-0">
                        {item.position}
                      </span>
                      <span className="flex-1 text-gray-800">{item.titel}</span>
                      <span className="text-xs text-gray-400">+{item.faellig_offset_tage} Tage</span>
                      {item.ist_optional_pro_mandant && <span className="badge bg-blue-100 text-blue-700 text-xs">Mandanten-Option</span>}
                      {!item.ist_pflicht && <span className="badge bg-gray-100 text-gray-500 text-xs">Optional</span>}
                      {item.erfordert_pruefung && <span className="badge bg-purple-100 text-purple-600 text-xs">4-Augen</span>}
                      <button
                        onClick={(e) => { e.stopPropagation(); toggleKernprozess(v.id, item) }}
                        disabled={updateItemMutation.isPending}
                        title={item.ist_kernprozess ? 'Als Kernprozess entfernen' : 'Als Kernprozess markieren'}
                        className={`flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium transition-colors ${
                          item.ist_kernprozess
                            ? 'bg-amber-500 text-white hover:bg-amber-600'
                            : 'bg-gray-100 text-gray-500 hover:bg-amber-100 hover:text-amber-700'
                        }`}
                      >
                        <Star size={11} className={item.ist_kernprozess ? 'fill-current' : ''} />
                        {item.ist_kernprozess ? 'Kernprozess' : 'Kern?'}
                      </button>
                    </div>
                  ))}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
