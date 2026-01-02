import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import { useAuth } from '../../hooks/useAuth'
import { supabase } from '../../lib/supabase'

// Logo path - public assets are served at root
const logoPath = '/assets/media/logo-no-bound.png'

const ResetPassword = () => {
  const navigate = useNavigate()
  const { user, loading: authLoading, signOut } = useAuth()

  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [submitting, setSubmitting] = useState(false)

  // If user lands here already authenticated (or via recovery), keep them on this page.
  // If they are not authenticated, we still show the form but will error on submit.
  useEffect(() => {
    // no-op (placeholder for future URL handling)
  }, [])

  const handleSubmit = async (e) => {
    e.preventDefault()

    if (password.length < 8) {
      toast.error('Password must be at least 8 characters.')
      return
    }
    if (password !== confirmPassword) {
      toast.error('Passwords do not match.')
      return
    }

    setSubmitting(true)
    try {
      const { error } = await supabase.auth.updateUser({ password })
      if (error) {
        toast.error(error.message || 'Failed to update password.')
        return
      }

      toast.success('Password updated successfully. Please sign in again.')
      await signOut()
      navigate('/login', { replace: true })
    } catch (err) {
      toast.error('An unexpected error occurred. Please try again.')
    } finally {
      setSubmitting(false)
    }
  }

  if (authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-ese-ink-white">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-ese-lang-900 mx-auto"></div>
          <p className="mt-4 text-ese-ink-navy">Loading...</p>
        </div>
      </div>
    )
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
          <p className="text-ese-ink-blue">Create a new password</p>
        </div>

        <div className="ese-card">
          <h2 className="text-2xl font-heading font-semibold text-ese-ink-navy mb-2 text-center">
            Reset Password
          </h2>

          {!user && (
            <div className="mb-4 text-sm text-ese-ink-blue bg-ese-ink-offwhite rounded-lg p-3 border border-ese-accent-beige">
              Open this page using the reset link from your email. If you don’t have a link, go to{' '}
              <Link to="/forgot-password" className="text-ese-lang-900 hover:underline">
                Forgot Password
              </Link>
              .
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-ese-ink-navy mb-2">
                New Password
              </label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="w-full px-4 py-3 border border-ese-accent-beige rounded-lg focus:ring-2 focus:ring-ese-lang-500 focus:border-ese-lang-500 outline-none transition-all"
                placeholder="Enter a new password"
                disabled={submitting}
              />
            </div>

            <div>
              <label
                htmlFor="confirmPassword"
                className="block text-sm font-medium text-ese-ink-navy mb-2"
              >
                Confirm Password
              </label>
              <input
                id="confirmPassword"
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
                className="w-full px-4 py-3 border border-ese-accent-beige rounded-lg focus:ring-2 focus:ring-ese-lang-500 focus:border-ese-lang-500 outline-none transition-all"
                placeholder="Re-enter the new password"
                disabled={submitting}
              />
            </div>

            <button
              type="submit"
              disabled={submitting}
              className="w-full ese-button-primary disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {submitting ? (
                <span className="flex items-center justify-center">
                  <span className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></span>
                  Updating...
                </span>
              ) : (
                'Update Password'
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

export default ResetPassword

