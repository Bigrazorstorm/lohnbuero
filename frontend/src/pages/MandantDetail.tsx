import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, Plus, Edit3, Phone, Mail, User } from 'lucide-react'
import { format } from 'date-fns'
import { de } from 'date-fns/locale'
import toast from 'react-hot-toast'
import { mandantenApi, workflowsApi, usersApi } from '../api/client'
import type { Mandant, WorkflowInstanzShort } from '../types'
import { KategorieBadge, WorkflowStatusBadge } from '../components/StatusBadge'
import Ampel from '../components/Ampel'

export default function MandantDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const qc = useQueryClient()
  const [showEdit, setShowEdit] = useState(false)

  const { data: mandant, isLoading } = useQuery<Mandant>({
    queryKey: ['mandant', id],
    queryFn: () => mandantenApi.get(Number(id)).then((r) => (r as { data: Mandant }).data),
  })

  const { data: workflows = [] } = useQuery<WorkflowInstanzShort[]>({
    queryKey: ['workflows', { mandant_id: id }],
    queryFn: () => workflowsApi.list({ mandant_id: id }).then((r) => (r as { data: WorkflowInstanzShort[] }).data),
  })

  const { data: users = [] } = useQuery({
    queryKey: ['users'],
    queryFn: () => usersApi.list().then((r) => (r as { data: any[] }).data),
  })

  const createWorkflowMutation = useMutation({
    mutationFn: () => {
      const now = new Date()
      return workflowsApi.create({
        mandant_id: Number(id),
        monat: now.getMonth() + 1,
        jahr: now.getFullYear(),
      })
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['workflows'] })
      toast.success('Workflow angelegt')
    },
    onError: (err: unknown) => {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      toast.error(msg ?? 'Fehler')
    },
  })

  const updateMutation = useMutation({
    mutationFn: (data: unknown) => mandantenApi.update(Number(id), data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['mandant', id] })
      qc.invalidateQueries({ queryKey: ['mandanten'] })
      toast.success('Mandant aktualisiert')
      setShowEdit(false)
    },
    onError: () => toast.error('Fehler beim Aktualisieren'),
  })

  if (isLoading) return <div className="text-gray-400 text-center py-12">Laden…</div>
  if (!mandant) return <div className="text-red-500 text-center py-12">Mandant nicht gefunden</div>

  const now = new Date()
  const monatLabel = format(now, 'MMMM yyyy', { locale: de })

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <button onClick={() => navigate('/mandanten')} className="btn-secondary px-2 py-2">
          <ArrowLeft size={18} />
        </button>
        <div className="flex-1">
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-gray-900">{mandant.name}</h1>
            <KategorieBadge kategorie={mandant.kategorie} />
            {!mandant.ist_aktiv && <span className="badge bg-red-100 text-red-700">Inaktiv</span>}
          </div>
          <p className="text-gray-400 text-sm mt-0.5">
            {mandant.nummer && `#${mandant.nummer} · `}{mandant.branche}
          </p>
        </div>
        <button className="btn-secondary" onClick={() => setShowEdit(true)}>
          <Edit3 size={16} />
          Bearbeiten
        </button>
      </div>

      <div className="grid grid-cols-3 gap-5">
        {/* Stammdaten */}
        <div className="col-span-2 space-y-5">
          <div className="card">
            <h2 className="text-base font-semibold text-gray-900 mb-4">Stammdaten</h2>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <InfoRow label="Ansprechpartner" value={mandant.ansprechpartner_name} icon={<User size={14} />} />
              <InfoRow label="E-Mail" value={mandant.ansprechpartner_email} icon={<Mail size={14} />} />
              <InfoRow label="Telefon" value={mandant.ansprechpartner_telefon} icon={<Phone size={14} />} />
              <InfoRow label="Mitarbeiter" value={mandant.mitarbeiteranzahl.toString()} />
              <InfoRow label="Abgabeweg" value={mandant.abgabeweg} />
              <InfoRow label="Lohnabschluss" value={`${mandant.lohnabschluss_tag}. des Monats`} />
              <InfoRow label="Sachbearbeiter" value={mandant.sachbearbeiter?.full_name} />
              <InfoRow label="Vertretung" value={mandant.vertretung?.full_name} />
              {mandant.monatspauschale && (
                <InfoRow label="Monatspauschale" value={`${mandant.monatspauschale.toFixed(2)} €`} />
              )}
              {mandant.service_level && (
                <InfoRow label="Service Level" value={mandant.service_level} />
              )}
            </div>
            {mandant.besonderheiten && (
              <div className="mt-4 p-3 bg-amber-50 rounded-lg border border-amber-100">
                <p className="text-xs font-medium text-amber-700 mb-1">Besonderheiten</p>
                <p className="text-sm text-amber-900">{mandant.besonderheiten}</p>
              </div>
            )}
          </div>

          {/* Geplante Änderungen */}
          {mandant.aenderungen && mandant.aenderungen.length > 0 && (
            <div className="card">
              <h2 className="text-base font-semibold text-gray-900 mb-4">Geplante Änderungen</h2>
              <div className="space-y-3">
                {mandant.aenderungen.map((aenderung) => (
                  <div key={aenderung.id} className="p-3 bg-blue-50 rounded-lg border border-blue-100">
                    <div className="flex items-center justify-between mb-2">
                      <span className={`badge ${
                        aenderung.status === 'geplant' ? 'bg-yellow-100 text-yellow-700' :
                        aenderung.status === 'aktiviert' ? 'bg-green-100 text-green-700' :
                        'bg-red-100 text-red-700'
                      }`}>
                        {aenderung.status}
                      </span>
                      {aenderung.aenderung_zum && (
                        <span className="text-sm text-gray-600">
                          Zum: {format(new Date(aenderung.aenderung_zum), 'dd.MM.yyyy', { locale: de })}
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-gray-700">
                      Erstellt von {aenderung.erstellt_von.full_name} am {format(new Date(aenderung.erstellt_am), 'dd.MM.yyyy', { locale: de })}
                    </p>
                    <details className="mt-2">
                      <summary className="text-sm font-medium text-blue-700 cursor-pointer">Änderungen anzeigen</summary>
                      <pre className="text-xs text-gray-600 mt-1 whitespace-pre-wrap">
                        {JSON.stringify(JSON.parse(aenderung.aenderungen), null, 2)}
                      </pre>
                    </details>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Workflow history */}
          <div className="card">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-base font-semibold text-gray-900">Monatliche Workflows</h2>
              <button
                className="btn-primary text-xs py-1.5"
                onClick={() => createWorkflowMutation.mutate()}
                disabled={createWorkflowMutation.isPending}
              >
                <Plus size={14} />
                {monatLabel} anlegen
              </button>
            </div>

            {workflows.length === 0 ? (
              <p className="text-sm text-gray-400 py-4 text-center">Noch keine Workflows</p>
            ) : (
              <div className="space-y-2">
                {workflows.map((wf) => (
                  <div
                    key={wf.id}
                    className="flex items-center justify-between p-3 rounded-lg border border-gray-100 hover:border-blue-200 hover:bg-blue-50/50 cursor-pointer transition-colors"
                    onClick={() => navigate(`/workflows/${wf.id}`)}
                  >
                    <div className="flex items-center gap-3">
                      <Ampel status={wf.ampelstatus} />
                      <span className="text-sm font-medium text-gray-800">
                        {format(new Date(wf.jahr, wf.monat - 1, 1), 'MMMM yyyy', { locale: de })}
                      </span>
                    </div>
                    <WorkflowStatusBadge status={wf.status} />
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Sidebar info */}
        <div className="space-y-4">
          <div className="card">
            <h3 className="text-sm font-semibold text-gray-700 mb-3">Schnellinfo</h3>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-500">Kategorie</span>
                <KategorieBadge kategorie={mandant.kategorie} />
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Workflows gesamt</span>
                <span className="font-medium">{workflows.length}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Angelegt</span>
                <span className="text-gray-600 text-xs">
                  {format(new Date(mandant.created_at), 'dd.MM.yyyy', { locale: de })}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Edit form modal */}
      {showEdit && (
        <MandantForm
          sachbearbeiterList={users.filter((u: any) => u.role === 'sachbearbeiter' || u.role === 'teamleitung')}
          onSubmit={(data) => updateMutation.mutate(data)}
          onClose={() => setShowEdit(false)}
          loading={updateMutation.isPending}
          initial={mandant}
          isEdit={true}
        />
      )}
    </div>
  )
}

function InfoRow({ label, value, icon }: { label: string; value?: string | null; icon?: React.ReactNode }) {
  return (
    <div>
      <p className="text-xs text-gray-400 font-medium mb-0.5">{label}</p>
      <p className="text-gray-800 flex items-center gap-1">
        {icon}
        {value ?? <span className="text-gray-300">–</span>}
      </p>
    </div>
  )
}
