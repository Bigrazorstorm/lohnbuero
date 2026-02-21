import { useState, FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { Briefcase } from 'lucide-react'
import toast from 'react-hot-toast'
import { authApi } from '../api/client'
import { useAuthStore } from '../store/auth'

export default function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const { setAuth } = useAuthStore()
  const navigate = useNavigate()

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      const tokenRes = await authApi.login(email, password)
      const meRes = await authApi.me()
      // axios response has .data
      const token = (tokenRes as { data: { access_token: string } }).data.access_token
      const user = (meRes as { data: unknown }).data
      setAuth(token, user as Parameters<typeof setAuth>[1])
      navigate('/dashboard')
    } catch {
      toast.error('E-Mail oder Passwort falsch')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-900 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-blue-600 mb-4">
            <Briefcase className="text-white" size={32} />
          </div>
          <h1 className="text-2xl font-bold text-white">Addison Operations Manager</h1>
          <p className="text-gray-400 mt-1 text-sm">Operative Steuerung für Lohnbüros</p>
        </div>

        {/* Form */}
        <div className="bg-white rounded-2xl shadow-xl p-8">
          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="label">E-Mail</label>
              <input
                type="email"
                className="input"
                placeholder="name@kanzlei.de"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                autoFocus
              />
            </div>
            <div>
              <label className="label">Passwort</label>
              <input
                type="password"
                className="input"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>
            <button type="submit" className="btn-primary w-full justify-center py-2.5" disabled={loading}>
              {loading ? 'Anmelden...' : 'Anmelden'}
            </button>
          </form>

          {/* Demo hints */}
          <div className="mt-6 pt-5 border-t border-gray-100">
            <p className="text-xs text-gray-500 font-medium mb-2">Demo-Zugänge:</p>
            <div className="space-y-1 text-xs text-gray-500">
              <div><code className="bg-gray-100 px-1 rounded">admin@kanzlei.de</code> / admin123</div>
              <div><code className="bg-gray-100 px-1 rounded">anna.schmidt@kanzlei.de</code> / sb123</div>
              <div><code className="bg-gray-100 px-1 rounded">buchhaltung@baufirma.de</code> / mandant123</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
