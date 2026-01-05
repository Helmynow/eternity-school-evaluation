import fs from 'node:fs'
import path from 'node:path'

function parseDotEnv(contents) {
  const env = {}
  for (const rawLine of contents.split(/\r?\n/)) {
    const line = rawLine.trim()
    if (!line || line.startsWith('#')) continue
    const eq = line.indexOf('=')
    if (eq === -1) continue
    const key = line.slice(0, eq).trim()
    let value = line.slice(eq + 1).trim()
    if ((value.startsWith('"') && value.endsWith('"')) || (value.startsWith("'") && value.endsWith("'"))) {
      value = value.slice(1, -1)
    }
    env[key] = value
  }
  return env
}

function loadEnvFiles() {
  // Mimic Vite env loading for production mode (subset).
  const cwd = process.cwd()
  const candidates = ['.env', '.env.local', '.env.production', '.env.production.local']
  for (const filename of candidates) {
    const filePath = path.join(cwd, filename)
    if (!fs.existsSync(filePath)) continue
    const parsed = parseDotEnv(fs.readFileSync(filePath, 'utf8'))
    for (const [k, v] of Object.entries(parsed)) {
      if (process.env[k] == null) process.env[k] = v
    }
  }
}

loadEnvFiles()

const required = [
  { key: 'VITE_SUPABASE_URL', hint: 'https://<project-ref>.supabase.co' },
  { key: 'VITE_SUPABASE_ANON_KEY', hint: 'your Supabase anon key' },
]

const errors = []

for (const { key, hint } of required) {
  const value = (process.env[key] || '').trim()
  if (!value) {
    errors.push(`${key} is required for a production build (${hint}).`)
    continue
  }
  if (value.includes('YOUR_PROJECT') || value.includes('YOUR_SUPABASE')) {
    errors.push(`${key} looks like a placeholder value.`)
  }
}

// API base URL
// - If VITE_API_URL is unset, the frontend defaults to same-origin relative paths (see `frontend/src/lib/api.js`).
// - This works well when deploying the FastAPI backend in the same Vercel project under `/api/*`.
// - If you're hosting the backend elsewhere, set VITE_API_URL to that origin (e.g. https://api.example.com).
const apiUrl = (process.env.VITE_API_URL || '').trim()
if (apiUrl && /(?:^|\/\/)(?:localhost|127\.0\.0\.1)(?::\d+)?/.test(apiUrl)) {
  errors.push('VITE_API_URL must not point to localhost/127.0.0.1 for production builds.')
}

if (errors.length) {
  console.error('\n[env-check] Production env validation failed:\n')
  for (const err of errors) {
    console.error(`- ${err}`)
  }
  console.error('\nSet these in your CI/Vercel Environment Variables (and/or frontend/.env.production.local).\n')
  process.exit(1)
}

console.log('[env-check] OK')
