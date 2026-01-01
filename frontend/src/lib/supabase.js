import { createClient } from '@supabase/supabase-js'

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || 'https://ywcfqlyhesnikclesgpr.supabase.co'
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inl3Y2ZxbHloZXNuaWtjbGVzZ3ByIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzI5MDc1NjgsImV4cCI6MjA0ODQ4MzU2OH0.RaXN7ggZ8Ypm7O5xJZ8yvRkoiEFLrNNg6yj5lGmBfFw'

if (!supabaseUrl || !supabaseAnonKey) {
  console.error('CRITICAL: Supabase configuration is missing!')
}

export const supabase = createClient(supabaseUrl, supabaseAnonKey, {
  auth: {
    persistSession: true,
    autoRefreshToken: true,
    detectSessionInUrl: true,
  },
})

// Helper to get user role from metadata
export const getUserRole = async () => {
  const { data: { user } } = await supabase.auth.getUser()
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

