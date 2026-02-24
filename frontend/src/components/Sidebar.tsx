import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard, Users, Briefcase, CheckSquare, MessageSquare,
  FileText, Building2, Shield, Mail, Database, Server, Zap, GitBranch
} from 'lucide-react'
import { useAuthStore } from '../store/auth'

const navItems = [
  { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard, roles: ['admin', 'teamleitung', 'sachbearbeiter', 'pruefer'] },
  { to: '/mandanten', label: 'Mandanten', icon: Building2, roles: ['admin', 'teamleitung', 'sachbearbeiter', 'pruefer', 'mandant'] },
  { to: '/workflows', label: 'Workflows', icon: CheckSquare, roles: ['admin', 'teamleitung', 'sachbearbeiter', 'pruefer', 'mandant'] },
  { to: '/tickets', label: 'Rückfragen', icon: MessageSquare, roles: ['admin', 'teamleitung', 'sachbearbeiter', 'pruefer', 'mandant'] },
  { to: '/users', label: 'Benutzer', icon: Users, roles: ['admin'] },
  { to: '/vorlagen', label: 'Vorlagen', icon: FileText, roles: ['admin', 'teamleitung'] },
  { to: '/email-templates', label: 'E-Mail-Templates', icon: Mail, roles: ['admin', 'teamleitung'] },
  { to: '/admin/stammdaten', label: 'Stammdaten', icon: Database, roles: ['admin'] },
  { to: '/admin/global-events', label: 'Global Events', icon: Zap, roles: ['admin'] },
  { to: '/admin/branche-schritte', label: 'Branche Schritte', icon: CheckSquare, roles: ['admin'] },
  { to: '/admin/prozess-designer', label: 'Prozessdesigner', icon: GitBranch, roles: ['admin'] },
  { to: '/admin/tenants', label: 'Tenants', icon: Building2, roles: ['admin'] },
  { to: '/admin/mail', label: 'Mail-Konfiguration', icon: Server, roles: ['admin'] },
  { to: '/audit', label: 'Audit-Log', icon: Shield, roles: ['admin', 'teamleitung'] },
]

export default function Sidebar() {
  const { user } = useAuthStore()

  const visible = navItems.filter(
    (item) => !user?.role || item.roles.includes(user.role)
  )

  return (
    <aside className="w-64 bg-gray-900 text-white flex flex-col">
      {/* Logo */}
      <div className="px-6 py-5 border-b border-gray-700">
        <div className="flex items-center gap-2">
          <Briefcase className="text-blue-400" size={22} />
          <div>
            <div className="text-sm font-bold text-white leading-tight">Addison Operations</div>
            <div className="text-xs text-gray-400">Manager</div>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-1">
        {visible.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                isActive
                  ? 'bg-blue-600 text-white'
                  : 'text-gray-300 hover:bg-gray-800 hover:text-white'
              }`
            }
          >
            <item.icon size={18} />
            {item.label}
          </NavLink>
        ))}
      </nav>

      <div className="px-4 py-3 border-t border-gray-700 text-xs text-gray-500">
        AOM v1.0 · 2026
      </div>
    </aside>
  )
}
