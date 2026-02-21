import { Outlet, useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store/auth'
import Sidebar from './Sidebar'

export default function Layout() {
  const { user, logout } = useAuthStore()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <div className="flex h-screen bg-gray-50">
      <Sidebar />
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top bar */}
        <header className="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between">
          <div />
          <div className="flex items-center gap-3">
            <span className="text-sm text-gray-600">
              {user?.full_name}
            </span>
            <span className="badge bg-blue-100 text-blue-800">{roleLabel(user?.role)}</span>
            <button onClick={handleLogout} className="btn-secondary text-xs px-3 py-1.5">
              Abmelden
            </button>
          </div>
        </header>

        {/* Main content */}
        <main className="flex-1 overflow-y-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}

function roleLabel(role?: string) {
  const map: Record<string, string> = {
    admin: 'Admin',
    teamleitung: 'Teamleitung',
    sachbearbeiter: 'Sachbearbeiter',
    pruefer: 'Prüfer',
    mandant: 'Mandant',
  }
  return map[role ?? ''] ?? role
}
