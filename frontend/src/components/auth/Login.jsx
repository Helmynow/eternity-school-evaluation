import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../../hooks/useAuth'
import toast from 'react-hot-toast'
// Logo path - public assets are served at root
const logoPath = '/assets/media/logo-no-bound.png'

const Login = ({ supabase: supabaseClient }) => {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const { signIn } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)

    try {
      const { data, error } = await signIn(email, password)
      
      if (error) {
        toast.error(error.message || 'Login failed. Please check your credentials.')
        return
      }

      if (data?.user) {
        toast.success('Welcome back!')
        navigate('/')
      }
    } catch (error) {
      toast.error('An unexpected error occurred. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-ese-lang-200 via-ese-ink-white to-ese-int-50 flex items-center justify-center p-4">
      <div className="max-w-md w-full">
        {/* Logo and Header */}
        <div className="text-center mb-8">
          <img 
            src={logoPath} 
            alt="Eternity School Logo" 
            className="h-16 w-auto mx-auto mb-4"
            onError={(e) => {
              e.target.style.display = 'none'
            }}
          />
          <h1 className="text-3xl font-heading font-bold text-ese-lang-900 mb-2">
            EVALVision
          </h1>
          <p className="text-ese-ink-blue">
            Eternity School Evaluation & Recognition System
          </p>
          <p className="text-sm text-ese-ink-blue mt-1 italic">
            "Developing lifelong learners"
          </p>
        </div>

        {/* Login Card */}
        <div className="ese-card">
          <h2 className="text-2xl font-heading font-semibold text-ese-ink-navy mb-6 text-center">
            Sign In
          </h2>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-ese-ink-navy mb-2">
                Email Address
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="w-full px-4 py-3 border border-ese-accent-beige rounded-lg focus:ring-2 focus:ring-ese-lang-500 focus:border-ese-lang-500 outline-none transition-all"
                placeholder="your.email@eternityschooegypt.com"
                disabled={loading}
              />
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-ese-ink-navy mb-2">
                Password
              </label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="w-full px-4 py-3 border border-ese-accent-beige rounded-lg focus:ring-2 focus:ring-ese-lang-500 focus:border-ese-lang-500 outline-none transition-all"
                placeholder="Enter your password"
                disabled={loading}
              />
              <div className="mt-2 flex justify-end">
                <Link
                  to="/forgot-password"
                  className="text-sm text-ese-lang-900 hover:underline"
                >
                  Forgot password?
                </Link>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full ese-button-primary disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <span className="flex items-center justify-center">
                  <span className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></span>
                  Signing in...
                </span>
              ) : (
                'Sign In'
              )}
            </button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-sm text-ese-ink-blue">
              Need help? Contact{' '}
              <a href="mailto:p.c@eternityschooegypt.com" className="text-ese-lang-900 hover:underline">
                People & Culture
              </a>
            </p>
          </div>
        </div>

        {/* Brand Colors Display */}
        <div className="mt-8 flex justify-center gap-2">
          <div className="w-12 h-12 rounded-lg bg-ese-lang-900" title="Language Division"></div>
          <div className="w-12 h-12 rounded-lg bg-ese-int-900" title="International Division"></div>
          <div className="w-12 h-12 rounded-lg bg-ese-accent-mustard" title="Accent"></div>
        </div>
      </div>
    </div>
  )
}

export default Login

