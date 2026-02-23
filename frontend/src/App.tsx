import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './store/auth'
import Layout from './components/Layout'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Mandanten from './pages/Mandanten'
import MandantDetail from './pages/MandantDetail'
import Workflows from './pages/Workflows'
import WorkflowDetail from './pages/WorkflowDetail'
import Tickets from './pages/Tickets'
import Users from './pages/Users'
import Vorlagen from './pages/Vorlagen'
import Audit from './pages/Audit'
import EmailTemplates from './pages/EmailTemplates'
import AdminStammdaten from './pages/AdminStammdaten'
import AdminMailConfig from './pages/AdminMailConfig'
import { AdminGlobalEvents } from './pages/AdminGlobalEvents'
import { AdminBranchenSchritte } from './pages/AdminBranchenSchritte'
import { AdminTenants } from './pages/AdminTenants'

function RequireAuth({ children }: { children: React.ReactNode }) {
  const { token } = useAuthStore()
  if (!token) return <Navigate to="/login" replace />
  return <>{children}</>
}

function RequireAdmin({ children }: { children: React.ReactNode }) {
  const { user } = useAuthStore()
  if (user?.role !== 'admin') return <Navigate to="/dashboard" replace />
  return <>{children}</>
}

export default function App() {
  const { token, user } = useAuthStore()

  return (
    <Routes>
      <Route path="/login" element={token ? <Navigate to="/dashboard" replace /> : <Login />} />

      <Route
        path="/"
        element={
          <RequireAuth>
            <Layout />
          </RequireAuth>
        }
      >
        <Route index element={<Navigate to="/dashboard" replace />} />

        {/* Dashboard - staff only, mandant gets redirected to their workflows */}
        <Route
          path="dashboard"
          element={user?.role === 'mandant' ? <Navigate to="/workflows" replace /> : <Dashboard />}
        />

        <Route path="mandanten" element={<Mandanten />} />
        <Route path="mandanten/:id" element={<MandantDetail />} />
        <Route path="workflows" element={<Workflows />} />
        <Route path="workflows/:id" element={<WorkflowDetail />} />
        <Route path="tickets" element={<Tickets />} />

        <Route
          path="users"
          element={
            <RequireAdmin>
              <Users />
            </RequireAdmin>
          }
        />
        <Route path="vorlagen" element={<Vorlagen />} />
        <Route path="email-templates" element={<EmailTemplates />} />
        <Route
          path="admin/stammdaten"
          element={
            <RequireAdmin>
              <AdminStammdaten />
            </RequireAdmin>
          }
        />
        <Route
          path="admin/mail"
          element={
            <RequireAdmin>
              <AdminMailConfig />
            </RequireAdmin>
          }
        />
        <Route
          path="admin/global-events"
          element={
            <RequireAdmin>
              <AdminGlobalEvents />
            </RequireAdmin>
          }
        />
        <Route
          path="admin/branche-schritte"
          element={
            <RequireAdmin>
              <AdminBranchenSchritte />
            </RequireAdmin>
          }
        />
        <Route
          path="admin/tenants"
          element={
            <RequireAdmin>
              <AdminTenants />
            </RequireAdmin>
          }
        />
        <Route path="audit" element={<Audit />} />
      </Route>

      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  )
}
