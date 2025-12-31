import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { useState, useEffect } from 'react'
import { createClient } from '@supabase/supabase-js'
import Dashboard from './components/dashboard/Dashboard'
import EOMNomination from './components/eom/EOMNomination'
import MREEvaluation from './components/mre/MREEvaluation'
import Login from './components/auth/Login'
import Layout from './components/layout/Layout'

// Initialize Supabase client
const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || 'https://ywcfqlyhesnikclesgpr.supabase.co'
const supabaseKey = import.meta.env.VITE_SUPABASE_ANON_KEY || ''

const supabase = createClient(supabaseUrl, supabaseKey)

function App() {
  const [session, setSession] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Check for existing session
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session)
      setLoading(false)
    })

    // Listen for auth changes
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session)
    })

    return () => subscription.unsubscribe()
  }, [])

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-ese-ink-white">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-ese-lang-900 mx-auto"></div>
          <p className="mt-4 text-ese-ink-navy">Loading...</p>
        </div>
      </div>
    )
  }

  if (!session) {
    return <Login supabase={supabase} />
  }

  return (
    <Router>
      <Layout supabase={supabase} session={session}>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/eom/nominate" element={<EOMNomination />} />
          <Route path="/eom/vote" element={<EOMNomination mode="vote" />} />
          <Route path="/mre/evaluate" element={<MREEvaluation />} />
        </Routes>
      </Layout>
    </Router>
  )
}

export default App

