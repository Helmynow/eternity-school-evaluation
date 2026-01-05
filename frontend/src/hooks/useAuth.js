import { useState, useEffect } from 'react'
import { supabase, getUserRole } from '../lib/supabase'

export const useAuth = () => {
  const [user, setUser] = useState(null)
  const [role, setRole] = useState(null)
  const [loading, setLoading] = useState(true)
  const [session, setSession] = useState(null)
  const isE2E = import.meta.env.VITE_E2E_MOCK_AUTH === 'true'

  const withTimeout = (promise, ms) =>
    Promise.race([
      promise,
      new Promise((_, reject) => setTimeout(() => reject(new Error('timeout')), ms)),
    ])

  const getSessionFromStorage = () => {
    if (typeof window === 'undefined') return null
    try {
      const key = Object.keys(window.localStorage).find((k) => k.includes('auth-token'))
      if (!key) return null
      const raw = window.localStorage.getItem(key)
      return raw ? JSON.parse(raw) : null
    } catch (error) {
      return null
    }
  }

  useEffect(() => {
    // Fast path: use cached session immediately to avoid blocking UI.
    const cachedSession = getSessionFromStorage()
    if (cachedSession?.user) {
      setSession(cachedSession)
      setUser(cachedSession.user)
      if (isE2E) {
        const cachedRole = cachedSession.user?.user_metadata?.role || cachedSession.user?.app_metadata?.role || null
        setRole(cachedRole)
      } else {
        getUserRole().then(setRole).catch(() => setRole(null))
      }
      setLoading(false)
    } else {
      setLoading(false)
    }

    if (isE2E) {
      return
    }

    // Get initial session
    withTimeout(supabase.auth.getSession(), 2000)
      .then(async ({ data: { session } }) => {
        setSession(session)
        setUser(session?.user ?? null)
        if (session?.user) {
          try {
            const userRole = await getUserRole()
            setRole(userRole)
          } catch (error) {
            setRole(null)
          }
        }
        setLoading(false)
      })
      .catch(async () => {
        const fallbackSession = getSessionFromStorage()
        setSession(fallbackSession)
        setUser(fallbackSession?.user ?? null)
        if (fallbackSession?.user) {
          try {
            const userRole = await getUserRole()
            setRole(userRole)
          } catch (error) {
            setRole(null)
          }
        }
        setLoading(false)
      })

    // Listen for auth changes
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange(async (_event, session) => {
      setSession(session)
      setUser(session?.user ?? null)
      try {
        if (session?.user) {
          const userRole = await getUserRole()
          setRole(userRole)
        } else {
          setRole(null)
        }
      } catch (error) {
        setRole(null)
      } finally {
        setLoading(false)
      }
    })

    return () => subscription.unsubscribe()
  }, [])

  const signIn = async (email, password) => {
    const { data, error } = await supabase.auth.signInWithPassword({
      email,
      password,
    })
    return { data, error }
  }

  const signOut = async () => {
    const { error } = await supabase.auth.signOut()
    return { error }
  }

  const signUp = async (email, password, metadata = {}) => {
    const { data, error } = await supabase.auth.signUp({
      email,
      password,
      options: {
        data: metadata,
      },
    })
    return { data, error }
  }

  const resetPassword = async (email) => {
    // Prefer backend-driven recovery so we can use reliable SMTP delivery when configured.
    // Backend also falls back to Supabase's built-in /recover flow if SMTP isn't configured.
    try {
      const envUrl = (import.meta.env.VITE_API_URL || '').trim()
      const apiBase =
        envUrl && !(import.meta.env.PROD && /(?:^|\/\/)(?:localhost|127\.0\.0\.1)(?::\d+)?/.test(envUrl))
          ? envUrl
          : window.location.origin
      const res = await fetch(`${apiBase}/api/v2/auth/password-recovery`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email }),
      })

      if (res.ok) {
        const payload = await res.json().catch(() => null)
        // If backend reports it couldn't perform recovery (misconfigured), fall back to client-side Supabase.
        if (payload?.provider && payload.provider !== 'none') {
          return { data: payload, error: null }
        }
      }
    } catch (e) {
      // Ignore and fall back to Supabase client recovery.
    }

    const { data, error } = await supabase.auth.resetPasswordForEmail(email, {
      redirectTo: `${window.location.origin}/reset-password`,
    })
    return { data, error }
  }

  return {
    user,
    role,
    session,
    loading,
    signIn,
    signOut,
    signUp,
    resetPassword,
    isAuthenticated: !!user,
    isCEO: (role || (user?.email?.toLowerCase().includes('ahelmy@eternity') || user?.email?.toLowerCase().includes('ceo') ? 'ceo' : null)) === 'ceo',
    isPNC: (role || (user?.email?.toLowerCase().includes('p.c@eternity') || user?.email?.toLowerCase().includes('people') || user?.email?.toLowerCase().includes('culture') ? 'pnc' : null)) === 'pnc',
    isDepartmentHead: (role || (user?.email?.toLowerCase().includes('principal') || user?.email?.toLowerCase().includes('head') || user?.email?.toLowerCase().includes('coordinator') ? 'department_head' : null)) === 'department_head',
    isStaff: (role || 'staff') === 'staff',
  }
}
