import fs from 'fs'
import path from 'path'

const parseProjectRef = () => {
  if (process.env.SUPABASE_PROJECT_REF) {
    return process.env.SUPABASE_PROJECT_REF.trim()
  }
  if (process.env.VITE_SUPABASE_URL) {
    const match = process.env.VITE_SUPABASE_URL.match(/https?:\/\/([^.]+)\.supabase\.co/i)
    if (match) return match[1]
  }

  try {
    const envPath = path.resolve(process.cwd(), '.env')
    if (fs.existsSync(envPath)) {
      const raw = fs.readFileSync(envPath, 'utf-8')
      const lines = raw.split('\n')
      for (const line of lines) {
        const trimmed = line.trim()
        if (!trimmed || trimmed.startsWith('#')) continue
        const [key, ...rest] = trimmed.split('=')
        const value = rest.join('=').trim()
        if (key === 'SUPABASE_PROJECT_REF' && value) return value
        if (key === 'VITE_SUPABASE_URL' && value) {
          const match = value.match(/https?:\/\/([^.]+)\.supabase\.co/i)
          if (match) return match[1]
        }
      }
    }
  } catch {
    // ignore
  }

  return null
}

export const buildSupabaseSession = ({
  email = 'ceo@eternity.edu',
  role = 'ceo',
} = {}) => {
  const now = Math.floor(Date.now() / 1000)
  return {
    access_token: 'test-access-token',
    refresh_token: 'test-refresh-token',
    token_type: 'bearer',
    expires_at: now + 60 * 60,
    user: {
      id: 'test-user',
      email,
      user_metadata: { role },
      app_metadata: { role },
    },
  }
}

export const seedSupabaseSession = async (page, options = {}) => {
  const session = buildSupabaseSession(options)
  const projectRef = parseProjectRef()
  await page.addInitScript(
    (sessionValue, ref) => {
      const keys = new Set(['sb-e2e-auth-token'])
      if (ref) {
        keys.add(`sb-${ref}-auth-token`)
      }
      keys.forEach((key) => {
        localStorage.setItem(key, JSON.stringify(sessionValue))
      })
    },
    session,
    projectRef
  )
  return session
}
