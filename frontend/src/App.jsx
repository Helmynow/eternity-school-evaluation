import { lazy, Suspense } from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import { useAuth } from './hooks/useAuth'
import ErrorBoundary from './components/common/ErrorBoundary'
import LoadingSkeleton from './components/common/LoadingSkeleton'
import PerformanceMonitor from './components/common/PerformanceMonitor'

// Lazy load components for code splitting
const Dashboard = lazy(() => import('./components/dashboard/Dashboard'))
const EOMNomination = lazy(() => import('./components/eom/EOMNomination'))
const EOMHallOfFame = lazy(() => import('./components/eom/EOMHallOfFame'))
const EOMDiversityDashboard = lazy(() => import('./components/eom/EOMDiversityDashboard'))
const EOMFeedbackForm = lazy(() => import('./components/eom/EOMFeedbackForm'))
const MREEvaluation = lazy(() => import('./components/mre/MREEvaluation'))
const Login = lazy(() => import('./components/auth/Login'))
const ForgotPassword = lazy(() => import('./components/auth/ForgotPassword'))
const ResetPassword = lazy(() => import('./components/auth/ResetPassword'))
const Layout = lazy(() => import('./components/layout/Layout'))
const CycleManagement = lazy(() => import('./components/admin/CycleManagement'))
const StaffManagement = lazy(() => import('./components/admin/StaffManagement'))
const Settings = lazy(() => import('./components/admin/Settings'))
const Objections = lazy(() => import('./components/admin/Objections'))
const Announcements = lazy(() => import('./components/admin/Announcements'))
const BulkImport = lazy(() => import('./components/admin/BulkImport'))
const Reports = lazy(() => import('./components/reports/Reports'))
const History = lazy(() => import('./components/history/History'))
const NotificationsCenter = lazy(() => import('./components/notifications/NotificationsCenter'))
const SurveyList = lazy(() => import('./components/survey/SurveyList'))
const SurveySession = lazy(() => import('./components/survey/SurveySession'))
const SurveyAnalytics = lazy(() => import('./components/survey/SurveyAnalytics'))
const SurveyCreate = lazy(() => import('./components/survey/SurveyCreate'))
const SurveyEdit = lazy(() => import('./components/survey/SurveyEdit'))
const SurveyQuestions = lazy(() => import('./components/survey/SurveyQuestions'))
const SurveyResponseReview = lazy(() => import('./components/survey/SurveyResponseReview'))
const IdentityModeTest = lazy(() => import('./components/survey/IdentityModeTest'))
const AdminDashboard = lazy(() => import('./components/admin/AdminDashboard'))
const IntegrationHub = lazy(() => import('./components/admin/IntegrationHub'))

function App() {
  const { user, loading } = useAuth()
  // If a user lands via Supabase password recovery (type=recovery), force them onto the reset page.
  // Supabase can redirect to the site root depending on template/config, so we handle it client-side.
  const isRecoveryFlow =
    typeof window !== 'undefined' && window.location.hash && window.location.hash.includes('type=recovery')

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
      <PerformanceMonitor />
      <Toaster position="top-right" />
      {!user ? (
        <Suspense fallback={<LoadingSkeleton type="dashboard" count={1} />}>
          <Routes>
            <Route
              path="/"
              element={<Navigate to={isRecoveryFlow ? '/reset-password' : '/login'} replace />}
            />
            <Route path="/login" element={<Login />} />
            <Route path="/forgot-password" element={<ForgotPassword />} />
            <Route path="/reset-password" element={<ResetPassword />} />
            <Route path="*" element={<Navigate to="/login" replace />} />
          </Routes>
        </Suspense>
      ) : (
        <ErrorBoundary>
          <Suspense fallback={<LoadingSkeleton type="dashboard" count={1} />}>
            <Layout>
              <Routes>
            <Route path="/" element={isRecoveryFlow ? <ResetPassword /> : <Dashboard />} />
            <Route path="/reset-password" element={<ResetPassword />} />
            <Route path="/eom/nominate" element={<EOMNomination />} />
            <Route path="/eom/vote" element={<EOMNomination mode="vote" />} />
            <Route path="/eom/hall-of-fame" element={<EOMHallOfFame />} />
            <Route path="/eom/diversity" element={<EOMDiversityDashboard />} />
            <Route path="/eom/feedback" element={<EOMFeedbackForm />} />
            <Route path="/mre/evaluate" element={<MREEvaluation />} />
            <Route path="/admin/cycles" element={<CycleManagement />} />
            <Route path="/admin/staff" element={<StaffManagement />} />
            <Route path="/admin/settings" element={<Settings />} />
            <Route path="/admin/objections" element={<Objections />} />
            <Route path="/admin/announcements" element={<Announcements />} />
            <Route path="/admin/import" element={<BulkImport />} />
            <Route path="/admin/dashboard" element={<AdminDashboard />} />
            <Route path="/admin/integration" element={<IntegrationHub />} />
            <Route path="/reports" element={<Reports />} />
            <Route path="/history" element={<History />} />
            <Route path="/notifications" element={<NotificationsCenter />} />
            <Route path="/survey" element={<SurveyList />} />
            <Route path="/survey/create" element={<SurveyCreate />} />
            <Route path="/survey/:surveyId" element={<SurveySession />} />
            <Route path="/survey/:surveyId/edit" element={<SurveyEdit />} />
            <Route path="/survey/:surveyId/questions" element={<SurveyQuestions />} />
            <Route path="/survey/:surveyId/responses" element={<SurveyResponseReview />} />
            <Route path="/survey/:surveyId/analytics" element={<SurveyAnalytics />} />
            <Route path="/survey/test/:surveyId?" element={<IdentityModeTest />} />
            <Route path="*" element={<Navigate to="/" replace />} />
              </Routes>
            </Layout>
          </Suspense>
        </ErrorBoundary>
      )}
    </Router>
  )
}

export default App
