import { useEffect, useRef, useState, useCallback } from 'react'
import { prozessDesignerApi } from '../api/client'
import {
  ProzessDesignerGraph,
  ProzessDesignerNode,
  ProzessDesignerEdge,
  ProzessSchrittChecklistItem,
} from '../types'
import {
  ChevronDown,
  ChevronUp,
  Plus,
  Trash2,
  Move,
  GitBranch,
  CheckSquare,
  Layers,
  X,
} from 'lucide-react'

// ── Constants ─────────────────────────────────
const CARD_WIDTH = 220
const CARD_HEIGHT_COLLAPSED = 80
const CARD_HEIGHT_EXPANDED = 260

const STEP_TYPE_COLORS: Record<string, string> = {
  datenerfassung: 'bg-blue-100 border-blue-400 text-blue-800',
  pruefer_pflicht: 'bg-purple-100 border-purple-400 text-purple-800',
  abschlussfrist: 'bg-red-100 border-red-400 text-red-800',
  upload: 'bg-yellow-100 border-yellow-400 text-yellow-800',
  genehmigung: 'bg-green-100 border-green-400 text-green-800',
  berechnung: 'bg-indigo-100 border-indigo-400 text-indigo-800',
  versand: 'bg-teal-100 border-teal-400 text-teal-800',
  verarbeitung: 'bg-gray-100 border-gray-400 text-gray-800',
}

const EDGE_COLORS: Record<string, string> = {
  blockiert_von: '#ef4444',
  muss_vor: '#f97316',
  parallel_ok: '#22c55e',
  optional_nach: '#94a3b8',
}

type VorlageListItem = { id: number; name: string; beschreibung?: string; ist_standard: boolean }

// ── Main Component ────────────────────────────
export function ProzessDesigner() {
  const [vorlagen, setVorlagen] = useState<VorlageListItem[]>([])
  const [selectedVorlageId, setSelectedVorlageId] = useState<number | null>(null)
  const [graph, setGraph] = useState<ProzessDesignerGraph | null>(null)
  const [loading, setLoading] = useState(false)
  const [expandedNodes, setExpandedNodes] = useState<Set<number>>(new Set())
  const [selectedNode, setSelectedNode] = useState<ProzessDesignerNode | null>(null)

  // Pan state
  const [pan, setPan] = useState({ x: 40, y: 40 })
  const [isPanning, setIsPanning] = useState(false)
  const panStart = useRef({ x: 0, y: 0, panX: 0, panY: 0 })

  // Drag state for nodes
  const [draggingNode, setDraggingNode] = useState<{
    id: number
    startMouseX: number
    startMouseY: number
    startPosX: number
    startPosY: number
  } | null>(null)

  // Connection drawing state
  const [connectingFrom, setConnectingFrom] = useState<number | null>(null)

  // Checklist management
  const [checklistForm, setChecklistForm] = useState<{
    itemId: number
    titel: string
    beschreibung: string
    ist_pflicht: boolean
  } | null>(null)

  const canvasRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    loadVorlagen()
  }, [])

  useEffect(() => {
    if (selectedVorlageId) loadGraph(selectedVorlageId)
  }, [selectedVorlageId])

  const loadVorlagen = async () => {
    try {
      const res = await prozessDesignerApi.listVorlagen()
      setVorlagen(res.data)
      if (res.data.length > 0 && !selectedVorlageId) {
        setSelectedVorlageId(res.data[0].id)
      }
    } catch (err) {
      console.error('Fehler beim Laden der Vorlagen:', err)
    }
  }

  const loadGraph = async (vorlageId: number) => {
    setLoading(true)
    try {
      const res = await prozessDesignerApi.getGraph(vorlageId)
      setGraph(res.data)
      setExpandedNodes(new Set())
      setSelectedNode(null)
    } catch (err) {
      console.error('Fehler beim Laden des Prozessgraphs:', err)
    } finally {
      setLoading(false)
    }
  }

  // ── Canvas Pan ────────────────────────────────
  const onCanvasMouseDown = (e: React.MouseEvent) => {
    if ((e.target as HTMLElement).closest('[data-node]')) return
    setIsPanning(true)
    panStart.current = { x: e.clientX, y: e.clientY, panX: pan.x, panY: pan.y }
  }

  const onCanvasMouseMove = useCallback(
    (e: React.MouseEvent) => {
      if (draggingNode) {
        const dx = e.clientX - draggingNode.startMouseX
        const dy = e.clientY - draggingNode.startMouseY
        setGraph((prev) => {
          if (!prev) return prev
          return {
            ...prev,
            nodes: prev.nodes.map((n) =>
              n.id === draggingNode.id
                ? { ...n, pos_x: draggingNode.startPosX + dx, pos_y: draggingNode.startPosY + dy }
                : n
            ),
          }
        })
        return
      }
      if (!isPanning) return
      const dx = e.clientX - panStart.current.x
      const dy = e.clientY - panStart.current.y
      setPan({ x: panStart.current.panX + dx, y: panStart.current.panY + dy })
    },
    [isPanning, draggingNode]
  )

  const onCanvasMouseUp = useCallback(
    async (e: React.MouseEvent) => {
      if (draggingNode) {
        const node = graph?.nodes.find((n) => n.id === draggingNode.id)
        if (node) {
          try {
            await prozessDesignerApi.updateItemPosition(node.id, node.pos_x, node.pos_y)
          } catch (err) {
            console.error('Fehler beim Speichern der Position:', err)
          }
        }
        setDraggingNode(null)
      }
      setIsPanning(false)
    },
    [draggingNode, graph]
  )

  // ── Node drag ────────────────────────────────
  const onNodeMouseDown = (e: React.MouseEvent, node: ProzessDesignerNode) => {
    e.stopPropagation()
    if (connectingFrom !== null) {
      // Complete connection
      handleConnect(connectingFrom, node.id)
      return
    }
    setDraggingNode({
      id: node.id,
      startMouseX: e.clientX,
      startMouseY: e.clientY,
      startPosX: node.pos_x,
      startPosY: node.pos_y,
    })
  }

  const toggleExpand = (e: React.MouseEvent, nodeId: number) => {
    e.stopPropagation()
    setExpandedNodes((prev) => {
      const next = new Set(prev)
      if (next.has(nodeId)) next.delete(nodeId)
      else next.add(nodeId)
      return next
    })
  }

  const openNodeDetail = (e: React.MouseEvent, node: ProzessDesignerNode) => {
    e.stopPropagation()
    setSelectedNode(node)
  }

  // ── Edge management ───────────────────────────
  const startConnect = (e: React.MouseEvent, nodeId: number) => {
    e.stopPropagation()
    setConnectingFrom(nodeId)
  }

  const cancelConnect = () => setConnectingFrom(null)

  const handleConnect = async (sourceId: number, targetId: number) => {
    setConnectingFrom(null)
    if (sourceId === targetId || !graph) return
    try {
      await prozessDesignerApi.createEdge(graph.vorlage_id, sourceId, targetId)
      loadGraph(graph.vorlage_id)
    } catch (err) {
      console.error('Fehler beim Erstellen der Verbindung:', err)
    }
  }

  const handleDeleteEdge = async (edgeId: number) => {
    if (!graph) return
    if (!confirm('Verbindung löschen?')) return
    try {
      await prozessDesignerApi.deleteEdge(edgeId)
      loadGraph(graph.vorlage_id)
    } catch (err) {
      console.error('Fehler beim Löschen der Verbindung:', err)
    }
  }

  // ── Checklist management ──────────────────────
  const openChecklistForm = (nodeId: number) => {
    setChecklistForm({ itemId: nodeId, titel: '', beschreibung: '', ist_pflicht: true })
  }

  const submitChecklistItem = async () => {
    if (!checklistForm || !graph) return
    try {
      await prozessDesignerApi.createChecklistItem(checklistForm.itemId, {
        titel: checklistForm.titel,
        beschreibung: checklistForm.beschreibung || undefined,
        ist_pflicht: checklistForm.ist_pflicht,
        position: 1,
      })
      setChecklistForm(null)
      loadGraph(graph.vorlage_id)
      if (selectedNode?.id === checklistForm.itemId) {
        const res = await prozessDesignerApi.getGraph(graph.vorlage_id)
        const updated = res.data.nodes.find((n: ProzessDesignerNode) => n.id === checklistForm.itemId)
        if (updated) setSelectedNode(updated)
      }
    } catch (err) {
      console.error('Fehler beim Erstellen des Checklisten-Eintrags:', err)
    }
  }

  const deleteChecklistItem = async (checklistId: number) => {
    if (!graph || !confirm('Checklisten-Eintrag löschen?')) return
    try {
      await prozessDesignerApi.deleteChecklistItem(checklistId)
      loadGraph(graph.vorlage_id)
      if (selectedNode) {
        const res = await prozessDesignerApi.getGraph(graph.vorlage_id)
        const updated = res.data.nodes.find((n: ProzessDesignerNode) => n.id === selectedNode.id)
        if (updated) setSelectedNode(updated)
      }
    } catch (err) {
      console.error('Fehler beim Löschen des Checklisten-Eintrags:', err)
    }
  }

  // ── SVG Arrow helpers ─────────────────────────
  const getNodeCenter = (node: ProzessDesignerNode) => ({
    x: node.pos_x + CARD_WIDTH / 2,
    y: node.pos_y + CARD_HEIGHT_COLLAPSED / 2,
  })

  const getEdgePath = (edge: ProzessDesignerEdge, nodes: ProzessDesignerNode[]) => {
    const source = nodes.find((n) => n.id === edge.source_item_id)
    const target = nodes.find((n) => n.id === edge.target_item_id)
    if (!source || !target) return null

    const s = { x: source.pos_x + CARD_WIDTH, y: source.pos_y + 40 }
    const t = { x: target.pos_x, y: target.pos_y + 40 }
    const cp1 = { x: s.x + 60, y: s.y }
    const cp2 = { x: t.x - 60, y: t.y }
    return `M ${s.x} ${s.y} C ${cp1.x} ${cp1.y}, ${cp2.x} ${cp2.y}, ${t.x} ${t.y}`
  }

  // Compute canvas bounds for SVG size
  const canvasWidth = graph
    ? Math.max(1200, ...graph.nodes.map((n) => n.pos_x + CARD_WIDTH + 200))
    : 1200
  const canvasHeight = graph
    ? Math.max(800, ...graph.nodes.map((n) => n.pos_y + CARD_HEIGHT_EXPANDED + 100))
    : 800

  return (
    <div className="flex flex-col h-screen">
      {/* Top Bar */}
      <div className="flex items-center gap-4 px-6 py-3 bg-white border-b border-gray-200 shadow-sm flex-shrink-0">
        <div className="flex items-center gap-2">
          <GitBranch className="text-blue-600" size={22} />
          <h1 className="text-xl font-bold text-gray-900">Prozessdesigner</h1>
        </div>

        <div className="flex items-center gap-2 ml-4">
          <label className="text-sm font-medium text-gray-600">Vorlage:</label>
          <select
            value={selectedVorlageId || ''}
            onChange={(e) => setSelectedVorlageId(parseInt(e.target.value))}
            className="border border-gray-300 rounded px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">-- Vorlage wählen --</option>
            {vorlagen.map((v) => (
              <option key={v.id} value={v.id}>
                {v.name} {v.ist_standard ? '(Standard)' : ''}
              </option>
            ))}
          </select>
        </div>

        {graph && (
          <div className="ml-auto flex items-center gap-3 text-sm text-gray-500">
            <span className="flex items-center gap-1">
              <Layers size={14} />
              {graph.phasen.length} Phasen
            </span>
            <span className="flex items-center gap-1">
              <CheckSquare size={14} />
              {graph.nodes.length} Schritte
            </span>
            <span className="flex items-center gap-1">
              <GitBranch size={14} />
              {graph.edges.length} Verbindungen
            </span>
          </div>
        )}
      </div>

      {/* Legend */}
      {graph && (
        <div className="flex items-center gap-4 px-6 py-2 bg-gray-50 border-b border-gray-200 text-xs flex-shrink-0">
          <span className="font-medium text-gray-600">Verbindungstypen:</span>
          {Object.entries(EDGE_COLORS).map(([typ, color]) => (
            <span key={typ} className="flex items-center gap-1">
              <span className="inline-block w-6 h-0.5" style={{ backgroundColor: color }} />
              {typ.replace('_', ' ')}
            </span>
          ))}
          <span className="ml-4 text-gray-400">
            Schritt ziehen = verschieben · Verbinden-Knopf = Pfeil zeichnen
          </span>
          {connectingFrom !== null && (
            <button
              onClick={cancelConnect}
              className="ml-auto flex items-center gap-1 px-2 py-1 bg-orange-100 text-orange-700 rounded text-xs"
            >
              <X size={12} /> Verbinden abbrechen
            </button>
          )}
        </div>
      )}

      <div className="flex flex-1 overflow-hidden">
        {/* Canvas */}
        <div
          ref={canvasRef}
          className={`flex-1 overflow-hidden relative bg-gray-100 ${
            isPanning ? 'cursor-grabbing' : connectingFrom !== null ? 'cursor-crosshair' : 'cursor-grab'
          }`}
          style={{
            backgroundImage:
              'radial-gradient(circle, #c7c7c7 1px, transparent 1px)',
            backgroundSize: '24px 24px',
          }}
          onMouseDown={onCanvasMouseDown}
          onMouseMove={onCanvasMouseMove}
          onMouseUp={onCanvasMouseUp}
          onMouseLeave={onCanvasMouseUp}
        >
          {loading && (
            <div className="absolute inset-0 flex items-center justify-center bg-white/60 z-50">
              <div className="text-gray-500 text-lg">Lade Prozessgraph...</div>
            </div>
          )}

          {graph && (
            <div
              style={{
                transform: `translate(${pan.x}px, ${pan.y}px)`,
                position: 'absolute',
                width: canvasWidth,
                height: canvasHeight,
              }}
            >
              {/* SVG layer for edges */}
              <svg
                width={canvasWidth}
                height={canvasHeight}
                style={{ position: 'absolute', top: 0, left: 0, pointerEvents: 'none' }}
              >
                <defs>
                  {Object.entries(EDGE_COLORS).map(([typ, color]) => (
                    <marker
                      key={typ}
                      id={`arrow-${typ}`}
                      markerWidth="10"
                      markerHeight="7"
                      refX="9"
                      refY="3.5"
                      orient="auto"
                    >
                      <polygon points="0 0, 10 3.5, 0 7" fill={color} />
                    </marker>
                  ))}
                </defs>
                {graph.edges.map((edge) => {
                  const path = getEdgePath(edge, graph.nodes)
                  if (!path) return null
                  const color = EDGE_COLORS[edge.typ] || '#94a3b8'
                  return (
                    <g key={edge.id}>
                      <path
                        d={path}
                        stroke={color}
                        strokeWidth={2}
                        fill="none"
                        markerEnd={`url(#arrow-${edge.typ})`}
                        opacity={0.8}
                      />
                    </g>
                  )
                })}
              </svg>

              {/* Nodes */}
              {graph.nodes.map((node) => {
                const isExpanded = expandedNodes.has(node.id)
                const colorClass =
                  STEP_TYPE_COLORS[node.schritttyp ?? 'verarbeitung'] ||
                  STEP_TYPE_COLORS.verarbeitung
                const isConnecting = connectingFrom === node.id

                return (
                  <div
                    key={node.id}
                    data-node={node.id}
                    style={{
                      position: 'absolute',
                      left: node.pos_x,
                      top: node.pos_y,
                      width: CARD_WIDTH,
                      zIndex: isExpanded ? 20 : 10,
                      userSelect: 'none',
                    }}
                    className={`rounded-lg border-2 shadow-md bg-white transition-shadow ${
                      isConnecting ? 'ring-2 ring-orange-400' : ''
                    } ${selectedNode?.id === node.id ? 'ring-2 ring-blue-500' : ''}`}
                    onMouseDown={(e) => onNodeMouseDown(e, node)}
                  >
                    {/* Card Header */}
                    <div
                      className={`px-3 py-2 rounded-t-md border-b ${colorClass} cursor-pointer flex items-center gap-2`}
                      onClick={(e) => openNodeDetail(e, node)}
                    >
                      <Move size={12} className="opacity-50 flex-shrink-0" />
                      <span className="text-xs font-bold flex-1 truncate">{node.titel}</span>
                      <span className="text-xs opacity-70">#{node.position}</span>
                    </div>

                    {/* Card Body (collapsed) */}
                    <div className="px-3 py-2 text-xs text-gray-600">
                      <div className="flex items-center justify-between gap-1 flex-wrap">
                        <span className="bg-gray-100 rounded px-1">{node.schritttyp ?? '—'}</span>
                        {node.ist_pflicht && (
                          <span className="bg-red-100 text-red-700 rounded px-1">Pflicht</span>
                        )}
                        {node.erfordert_pruefung && (
                          <span className="bg-purple-100 text-purple-700 rounded px-1">4-Augen</span>
                        )}
                        {node.checklisten.length > 0 && (
                          <span className="bg-blue-100 text-blue-700 rounded px-1 flex items-center gap-0.5">
                            <CheckSquare size={10} />
                            {node.checklisten.length}
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Expanded section */}
                    {isExpanded && (
                      <div className="px-3 py-2 border-t border-gray-100 text-xs text-gray-700 space-y-1">
                        {node.beschreibung && (
                          <p className="text-gray-600 italic">{node.beschreibung}</p>
                        )}
                        <div className="flex gap-3 flex-wrap text-gray-500">
                          {node.faellig_offset_tage !== 0 && (
                            <span>Fällig: +{node.faellig_offset_tage}d</span>
                          )}
                          {node.standard_punkte !== 1 && (
                            <span>{node.standard_punkte} Punkte</span>
                          )}
                          {node.verantwortlich_rolle && (
                            <span>Rolle: {node.verantwortlich_rolle}</span>
                          )}
                        </div>
                        {node.checklisten.length > 0 && (
                          <div className="mt-2">
                            <div className="font-semibold text-gray-600 mb-1">Checkliste:</div>
                            <ul className="space-y-0.5">
                              {node.checklisten.map((cl) => (
                                <li key={cl.id} className="flex items-center gap-1">
                                  <CheckSquare size={10} className="text-blue-500 flex-shrink-0" />
                                  <span className="truncate">{cl.titel}</span>
                                  {cl.ist_pflicht && (
                                    <span className="text-red-500 text-xs">*</span>
                                  )}
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    )}

                    {/* Card Footer */}
                    <div className="px-2 py-1 border-t border-gray-100 flex items-center justify-between gap-1">
                      <button
                        onMouseDown={(e) => e.stopPropagation()}
                        onClick={(e) => toggleExpand(e, node.id)}
                        className="text-gray-400 hover:text-gray-600 p-0.5"
                        title={isExpanded ? 'Einklappen' : 'Ausklappen'}
                      >
                        {isExpanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                      </button>
                      <button
                        onMouseDown={(e) => e.stopPropagation()}
                        onClick={(e) => {
                          e.stopPropagation()
                          startConnect(e, node.id)
                        }}
                        className={`text-xs px-1.5 py-0.5 rounded ${
                          connectingFrom === node.id
                            ? 'bg-orange-200 text-orange-700'
                            : 'bg-gray-100 text-gray-500 hover:bg-gray-200'
                        }`}
                        title="Verbindung zeichnen"
                      >
                        <GitBranch size={12} />
                      </button>
                      <button
                        onMouseDown={(e) => e.stopPropagation()}
                        onClick={(e) => {
                          e.stopPropagation()
                          openNodeDetail(e, node)
                        }}
                        className="text-xs px-1.5 py-0.5 bg-blue-50 text-blue-600 rounded hover:bg-blue-100"
                        title="Details / Checkliste bearbeiten"
                      >
                        <CheckSquare size={12} />
                      </button>
                    </div>
                  </div>
                )
              })}
            </div>
          )}

          {!graph && !loading && (
            <div className="absolute inset-0 flex flex-col items-center justify-center text-gray-400">
              <GitBranch size={64} className="mb-4 opacity-20" />
              <p className="text-lg">Bitte eine Workflow-Vorlage auswählen</p>
            </div>
          )}
        </div>

        {/* Detail Panel */}
        {selectedNode && (
          <DetailPanel
            node={selectedNode}
            edges={graph?.edges ?? []}
            allNodes={graph?.nodes ?? []}
            onClose={() => setSelectedNode(null)}
            onDeleteEdge={handleDeleteEdge}
            onOpenChecklistForm={() => openChecklistForm(selectedNode.id)}
            onDeleteChecklist={deleteChecklistItem}
          />
        )}
      </div>

      {/* Checklist Form Modal */}
      {checklistForm && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl p-6 w-96">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">Checklisten-Eintrag hinzufügen</h3>
              <button onClick={() => setChecklistForm(null)} className="text-gray-400 hover:text-gray-600">
                <X size={20} />
              </button>
            </div>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">Titel *</label>
                <input
                  type="text"
                  value={checklistForm.titel}
                  onChange={(e) => setChecklistForm({ ...checklistForm, titel: e.target.value })}
                  className="w-full border rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="z.B. Lohnsteuer-Anmeldung prüfen"
                  autoFocus
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Beschreibung</label>
                <textarea
                  value={checklistForm.beschreibung}
                  onChange={(e) => setChecklistForm({ ...checklistForm, beschreibung: e.target.value })}
                  className="w-full border rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  rows={3}
                  placeholder="Optionale Details..."
                />
              </div>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={checklistForm.ist_pflicht}
                  onChange={(e) => setChecklistForm({ ...checklistForm, ist_pflicht: e.target.checked })}
                  className="rounded"
                />
                <span className="text-sm">Pflicht-Eintrag (muss abgehakt werden)</span>
              </label>
            </div>
            <div className="flex gap-3 mt-6 justify-end">
              <button
                onClick={() => setChecklistForm(null)}
                className="px-4 py-2 text-sm border rounded text-gray-600 hover:bg-gray-50"
              >
                Abbrechen
              </button>
              <button
                onClick={submitChecklistItem}
                disabled={!checklistForm.titel.trim()}
                className="px-4 py-2 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
              >
                Hinzufügen
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

// ── Detail Panel ──────────────────────────────
interface DetailPanelProps {
  node: ProzessDesignerNode
  edges: ProzessDesignerEdge[]
  allNodes: ProzessDesignerNode[]
  onClose: () => void
  onDeleteEdge: (id: number) => void
  onOpenChecklistForm: () => void
  onDeleteChecklist: (id: number) => void
}

function DetailPanel({
  node,
  edges,
  allNodes,
  onClose,
  onDeleteEdge,
  onOpenChecklistForm,
  onDeleteChecklist,
}: DetailPanelProps) {
  const incomingEdges = edges.filter((e) => e.target_item_id === node.id)
  const outgoingEdges = edges.filter((e) => e.source_item_id === node.id)

  const getNodeName = (id: number) => allNodes.find((n) => n.id === id)?.titel ?? `Schritt #${id}`

  return (
    <div className="w-80 bg-white border-l border-gray-200 flex flex-col overflow-hidden shadow-lg">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200 bg-gray-50">
        <h3 className="font-semibold text-gray-800 truncate">{node.titel}</h3>
        <button onClick={onClose} className="text-gray-400 hover:text-gray-600 flex-shrink-0">
          <X size={18} />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-5">
        {/* Basic Info */}
        <section>
          <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Schritt-Details</h4>
          <div className="space-y-1 text-sm">
            <DetailRow label="Position" value={String(node.position)} />
            <DetailRow label="Typ" value={node.schritttyp ?? '—'} />
            <DetailRow label="Pflicht" value={node.ist_pflicht ? 'Ja' : 'Nein'} />
            <DetailRow label="Optional pro Mandant" value={node.ist_optional_pro_mandant ? 'Ja' : 'Nein'} />
            <DetailRow label="Dokument erforderlich" value={node.erfordert_dokument ? 'Ja' : 'Nein'} />
            <DetailRow label="4-Augen-Prüfung" value={node.erfordert_pruefung ? 'Ja' : 'Nein'} />
            <DetailRow label="Punkte" value={String(node.standard_punkte)} />
            {node.faellig_offset_tage !== 0 && (
              <DetailRow label="Fällig nach" value={`${node.faellig_offset_tage} Tage`} />
            )}
            {node.verantwortlich_rolle && (
              <DetailRow label="Rolle" value={node.verantwortlich_rolle} />
            )}
          </div>
          {node.beschreibung && (
            <p className="mt-2 text-sm text-gray-600 bg-gray-50 rounded p-2">{node.beschreibung}</p>
          )}
        </section>

        {/* Incoming connections */}
        {incomingEdges.length > 0 && (
          <section>
            <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Voraussetzungen</h4>
            <div className="space-y-1">
              {incomingEdges.map((edge) => (
                <div key={edge.id} className="flex items-center justify-between bg-gray-50 rounded px-2 py-1 text-xs">
                  <span className="truncate">{getNodeName(edge.source_item_id)}</span>
                  <div className="flex items-center gap-1 flex-shrink-0 ml-2">
                    <span
                      className="rounded px-1"
                      style={{ backgroundColor: EDGE_COLORS[edge.typ] + '22', color: EDGE_COLORS[edge.typ] }}
                    >
                      {edge.typ.replace('_', ' ')}
                    </span>
                    <button
                      onClick={() => onDeleteEdge(edge.id)}
                      className="text-red-400 hover:text-red-600"
                      title="Verbindung löschen"
                    >
                      <Trash2 size={12} />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Outgoing connections */}
        {outgoingEdges.length > 0 && (
          <section>
            <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Nachfolger</h4>
            <div className="space-y-1">
              {outgoingEdges.map((edge) => (
                <div key={edge.id} className="flex items-center justify-between bg-gray-50 rounded px-2 py-1 text-xs">
                  <span className="truncate">{getNodeName(edge.target_item_id)}</span>
                  <div className="flex items-center gap-1 flex-shrink-0 ml-2">
                    <span
                      className="rounded px-1"
                      style={{ backgroundColor: EDGE_COLORS[edge.typ] + '22', color: EDGE_COLORS[edge.typ] }}
                    >
                      {edge.typ.replace('_', ' ')}
                    </span>
                    <button
                      onClick={() => onDeleteEdge(edge.id)}
                      className="text-red-400 hover:text-red-600"
                      title="Verbindung löschen"
                    >
                      <Trash2 size={12} />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Checklist */}
        <section>
          <div className="flex items-center justify-between mb-2">
            <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wide">
              Monatliche Checkliste
            </h4>
            <button
              onClick={onOpenChecklistForm}
              className="flex items-center gap-1 text-xs bg-blue-50 text-blue-600 px-2 py-1 rounded hover:bg-blue-100"
            >
              <Plus size={12} /> Eintrag
            </button>
          </div>
          {node.checklisten.length === 0 ? (
            <p className="text-xs text-gray-400 italic">Keine Checklisten-Einträge vorhanden</p>
          ) : (
            <div className="space-y-1">
              {node.checklisten
                .filter((cl) => cl.ist_aktiv)
                .map((cl) => (
                  <div
                    key={cl.id}
                    className="flex items-start gap-2 bg-gray-50 rounded px-2 py-1.5 text-xs"
                  >
                    <CheckSquare size={12} className="text-blue-500 flex-shrink-0 mt-0.5" />
                    <div className="flex-1 min-w-0">
                      <span className="font-medium truncate block">{cl.titel}</span>
                      {cl.beschreibung && (
                        <span className="text-gray-500 text-xs">{cl.beschreibung}</span>
                      )}
                    </div>
                    <div className="flex items-center gap-1 flex-shrink-0">
                      {cl.ist_pflicht && (
                        <span className="text-red-500 font-bold" title="Pflicht">*</span>
                      )}
                      <button
                        onClick={() => onDeleteChecklist(cl.id)}
                        className="text-red-400 hover:text-red-600"
                        title="Löschen"
                      >
                        <Trash2 size={11} />
                      </button>
                    </div>
                  </div>
                ))}
            </div>
          )}
        </section>
      </div>
    </div>
  )
}

function DetailRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-gray-500">{label}</span>
      <span className="font-medium">{value}</span>
    </div>
  )
}
