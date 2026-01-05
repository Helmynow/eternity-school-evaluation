import { createClient } from '@supabase/supabase-js'

const supabaseUrl = (import.meta.env.VITE_SUPABASE_URL || '').trim()
// Avoid hardcoding keys in the client bundle. Configure via VITE_SUPABASE_ANON_KEY at build time.
const supabaseAnonKey = (import.meta.env.VITE_SUPABASE_ANON_KEY || '').trim()

if (!supabaseUrl || !supabaseAnonKey) {
  // In production we should never run with missing Supabase config.
  if (import.meta.env.PROD) {
    throw new Error('CRITICAL: Supabase configuration is missing (VITE_SUPABASE_URL / VITE_SUPABASE_ANON_KEY).')
  }
  console.error('CRITICAL: Supabase configuration is missing (dev).')
}

export const supabase = createClient(supabaseUrl, supabaseAnonKey, {
  auth: {
    persistSession: true,
    autoRefreshToken: true,
    detectSessionInUrl: true,
  },
})

// Helper to get user role from metadata
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

export const getUserRole = async () => {
  let user = null
  const isE2E = import.meta.env.VITE_E2E_MOCK_AUTH === 'true'

  // Prefer cached session user to avoid blocking on network.
  try {
    if (!isE2E) {
      const { data: { session } } = await withTimeout(supabase.auth.getSession(), 2000)
      user = session?.user ?? null
    }
  } catch (error) {
    // Ignore session retrieval failures.
  }

  if (!user) {
    const cached = getSessionFromStorage()
    user = cached?.user ?? null
  }

  // Best-effort fetch of the authoritative user record (may fail offline).
  try {
    if (!isE2E) {
      const { data } = await withTimeout(supabase.auth.getUser(), 2000)
      if (data?.user) user = data.user
    }
  } catch (error) {
    // Fall back to session user if the network call fails.
  }

  if (!user) return null
  
  // Check user metadata for role
  const role = user.user_metadata?.role || user.app_metadata?.role
  
  // If no role in metadata, check email domain/pattern
  if (!role) {
    const email = user.email?.toLowerCase() || ''
    if (email.includes('ahelmy@eternity') || email.includes('ceo')) {
      return 'ceo'
    } else if (email.includes('p.c@eternity') || email.includes('people') || email.includes('culture')) {
      return 'pnc'
    } else if (email.includes('principal') || email.includes('head') || email.includes('coordinator')) {
      return 'department_head'
    }
  }
  
  return role || 'staff'
}

// Helper to check if user has permission
export const hasPermission = async (requiredRole) => {
  const userRole = await getUserRole()
  
  const roleHierarchy = {
    ceo: 4,
    pnc: 3,
    department_head: 2,
    staff: 1,
  }
  
  const userLevel = roleHierarchy[userRole] || 0
  const requiredLevel = roleHierarchy[requiredRole] || 0
  
  return userLevel >= requiredLevel
}

export default supabase
