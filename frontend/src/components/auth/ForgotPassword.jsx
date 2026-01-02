import { useState } from 'react'
import { Link } from 'react-router-dom'
import toast from 'react-hot-toast'
import { useAuth } from '../../hooks/useAuth'

// Logo path - public assets are served at root
const logoPath = '/assets/media/logo-no-bound.png'

const ForgotPassword = () => {
  const { resetPassword } = useAuth()
  const [email, setEmail] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)

    try {
      const { error } = await resetPassword(email)

      if (error) {
        toast.error(error.message || 'Failed to send reset email. Please try again.')
        return
      }

      // Supabase intentionally does not reveal whether an email exists in the system.
      // So this can succeed even if no email is delivered (unknown email / spam / SMTP issues).
      toast.success("If an account exists for that email, you'll receive a reset link shortly. Please check spam/junk.")
    } catch (err) {
      toast.error('An unexpected error occurred. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-ese-lang-200 via-ese-ink-white to-ese-int-50 flex items-center justify-center p-4">
      <div className="max-w-md w-full">
        <div className="text-center mb-8">
          <img
            src={logoPath}
            alt="Eternity School Logo"
            className="h-16 w-auto mx-auto mb-4"
            onError={(e) => {
              e.target.style.display = 'none'
            }}
          />
          <h1 className="text-3xl font-heading font-bold text-ese-lang-900 mb-2">EVALVision</h1>
          <p className="text-ese-ink-blue">Reset your password</p>
        </div>

        <div className="ese-card">
          <h2 className="text-2xl font-heading font-semibold text-ese-ink-navy mb-2 text-center">
            Forgot Password
          </h2>
          <p className="text-sm text-ese-ink-blue text-center mb-6">
            Enter your email and we’ll send you a password reset link.
          </p>
          <div className="mb-4 text-xs text-ese-ink-blue bg-ese-ink-offwhite rounded-lg p-3 border border-ese-accent-beige">
            If you don’t receive an email within a few minutes, check your spam/junk folder. For security reasons, we
            can’t confirm whether an email address is registered.
          </div>

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

            <button
              type="submit"
              disabled={loading}
              className="w-full ese-button-primary disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <span className="flex items-center justify-center">
                  <span className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></span>
                  Sending...
                </span>
              ) : (
                'Send Reset Link'
              )}
            </button>
          </form>

          <div className="mt-6 text-center">
            <Link to="/login" className="text-sm text-ese-lang-900 hover:underline">
              Back to Sign In
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ForgotPassword

