import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import Dashboard from './components/dashboard/Dashboard'
import EOMNomination from './components/eom/EOMNomination'
import MREEvaluation from './components/mre/MREEvaluation'
import Login from './components/auth/Login'
import Layout from './components/layout/Layout'
import { useAuth } from './hooks/useAuth'
import { supabase } from './lib/supabase'

function App() {
  const { user, loading } = useAuth()

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

  return (
    <Router>
      <Toaster position="top-right" />
      {!user ? (
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      ) : (
        <Layout>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/eom/nominate" element={<EOMNomination />} />
            <Route path="/eom/vote" element={<EOMNomination mode="vote" />} />
            <Route path="/mre/evaluate" element={<MREEvaluation />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Layout>
      )}
    </Router>
  )
}

export default App

