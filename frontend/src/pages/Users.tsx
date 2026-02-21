import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { Plus, Users as UsersIcon } from 'lucide-react'
import toast from 'react-hot-toast'
import { usersApi } from '../api/client'
import type { User, UserRole } from '../types'

const ROLE_LABELS: Record<UserRole, string> = {
  admin: 'Admin',
  teamleitung: 'Teamleitung',
  sachbearbeiter: 'Sachbearbeiter',
  pruefer: 'Prüfer',
  mandant: 'Mandant-Portal',
}

export default function Users() {
  const qc = useQueryClient()
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({ email: '', full_name: '', role: 'sachbearbeiter', password: '' })

  const { data: users = [], isLoading } = useQuery<User[]>({
    queryKey: ['users'],
    queryFn: () => usersApi.list().then((r) => (r as { data: User[] }).data),
  })

  const createMutation = useMutation({
    mutationFn: (data: unknown) => usersApi.create(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['users'] })
      toast.success('Benutzer angelegt')
      setShowForm(false)
      setForm({ email: '', full_name: '', role: 'sachbearbeiter', password: '' })
    },
    onError: () => toast.error('Fehler beim Anlegen'),
  })

  const toggleMutation = useMutation({
    mutationFn: ({ id, is_active }: { id: number; is_active: boolean }) =>
      usersApi.update(id, { is_active }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['users'] }),
  })

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Benutzerverwaltung</h1>
        <button className="btn-primary" onClick={() => setShowForm(!showForm)}>
          <Plus size={16} />
          Neuer Benutzer
        </button>
      </div>

      {/* Create form */}
      {showForm && (
        <div className="card">
          <h2 className="text-base font-semibold mb-4">Neuer Benutzer</h2>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">Name *</label>
              <input className="input" required value={form.full_name}
                onChange={e => setForm(f => ({ ...f, full_name: e.target.value }))} />
            </div>
            <div>
              <label className="label">E-Mail *</label>
              <input type="email" className="input" required value={form.email}
                onChange={e => setForm(f => ({ ...f, email: e.target.value }))} />
            </div>
            <div>
              <label className="label">Rolle *</label>
              <select className="input" value={form.role}
                onChange={e => setForm(f => ({ ...f, role: e.target.value }))}>
                <option value="sachbearbeiter">Sachbearbeiter</option>
                <option value="teamleitung">Teamleitung</option>
                <option value="pruefer">Prüfer</option>
                <option value="admin">Admin</option>
                <option value="mandant">Mandant-Portal</option>
              </select>
            </div>
            <div>
              <label className="label">Passwort *</label>
              <input type="password" className="input" required value={form.password}
                onChange={e => setForm(f => ({ ...f, password: e.target.value }))} />
            </div>
          </div>
          <div className="flex gap-3 mt-4">
            <button
              className="btn-primary"
              disabled={createMutation.isPending}
              onClick={() => createMutation.mutate(form)}
            >
              Anlegen
            </button>
            <button className="btn-secondary" onClick={() => setShowForm(false)}>Abbrechen</button>
          </div>
        </div>
      )}

      {/* Table */}
      {isLoading ? (
        <div className="card text-center py-12 text-gray-400">Laden…</div>
      ) : (
        <div className="card p-0 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Name</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">E-Mail</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Rolle</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Status</th>
                <th className="px-4 py-3"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {users.map((u) => (
                <tr key={u.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 font-medium text-gray-900">{u.full_name}</td>
                  <td className="px-4 py-3 text-gray-600">{u.email}</td>
                  <td className="px-4 py-3">
                    <span className="badge bg-blue-100 text-blue-700">{ROLE_LABELS[u.role]}</span>
                  </td>
                  <td className="px-4 py-3">
                    <span className={`badge ${u.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
                      {u.is_active ? 'Aktiv' : 'Inaktiv'}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <button
                      className="text-xs text-gray-400 hover:text-gray-700"
                      onClick={() => toggleMutation.mutate({ id: u.id, is_active: !u.is_active })}
                    >
                      {u.is_active ? 'Deaktivieren' : 'Aktivieren'}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
