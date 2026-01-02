import axios from 'axios'
import toast from 'react-hot-toast'
import { supabase } from './supabase'

// Track recent errors to prevent spam
const recentErrors = new Map()
const ERROR_COOLDOWN = 5000 // 5 seconds

// Helper to show error only if not recently shown
const showErrorOnce = (message, key) => {
  const now = Date.now()
  const lastShown = recentErrors.get(key)
  
  if (!lastShown || (now - lastShown) > ERROR_COOLDOWN) {
    recentErrors.set(key, now)
    toast.error(message)
  }
}

// Create axios instance with base configuration
// IMPORTANT:
// - In production, we must NOT default to localhost, otherwise the deployed app will try to call
//   `http://localhost:8000` from users' browsers and fail with ERR_CONNECTION_REFUSED.
// - In dev, we still want a sensible default to the local FastAPI server.
const apiBaseURL = (() => {
  const envUrl = (import.meta.env.VITE_API_URL || '').trim()
  if (envUrl) {
    // Guard against accidentally setting a localhost URL in production builds.
    if (import.meta.env.PROD && /(?:^|\/\/)(?:localhost|127\.0\.0\.1)(?::\d+)?/.test(envUrl)) {
      return ''
    }
    return envUrl
  }

  // Default to local backend for development only.
  if (import.meta.env.DEV) return 'http://localhost:8000'

  // Production: use same-origin relative paths.
  return ''
})()

const api = axios.create({
  baseURL: apiBaseURL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000, // 10 seconds - reduced to fail faster
})

// Performance tracking is handled in interceptors below

// Request interceptor for performance tracking and auth token
api.interceptors.request.use(
  async (config) => {
    // Track performance
    const startTime = performance.now()
    config.metadata = { startTime }
    
    // Get token from Supabase session (v2 compatible)
    try {
      const { data: { session } } = await supabase.auth.getSession()
      if (session?.access_token) {
        config.headers.Authorization = `Bearer ${session.access_token}`
      }
    } catch (error) {
      // If session retrieval fails, continue without auth token
      // The backend will handle unauthorized requests appropriately
      console.warn('Failed to retrieve auth session:', error)
    }

    // Optional API key for backend auth
    const apiKey = import.meta.env.VITE_API_KEY
    if (apiKey) {
      config.headers['x-api-key'] = apiKey
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor for performance tracking
api.interceptors.response.use(
  (response) => {
    const endTime = performance.now()
    const duration = endTime - (response.config.metadata?.startTime || endTime)
    
    // Track performance
    if (window.trackAPIRequest) {
      window.trackAPIRequest(response.config.url, duration, response.status)
    }
    
    return response
  },
  (error) => {
    if (error.config) {
      const endTime = performance.now()
      const duration = endTime - (error.config.metadata?.startTime || endTime)
      
      // Track performance even for errors
      if (window.trackAPIRequest) {
        window.trackAPIRequest(error.config.url, duration, error.response?.status || 'error')
      }
    }
    
    return Promise.reject(error)
  }
)

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Don't show errors for expected cases (like no cycles found)
    const isExpected404 = error.config?.url?.includes('/cycles/current') || 
                         error.config?.url?.includes('/cycles') && error.response?.status === 404
    
    if (error.response) {
      // Server responded with error status
      const { status, data } = error.response
      
      // Only show toast for unexpected errors
      if (!isExpected404) {
        const errorKey = `${status}-${error.config?.url}`
        switch (status) {
          case 401:
            showErrorOnce('Authentication required. Please log in.', errorKey)
            // Redirect to login
            window.location.href = '/login'
            break
          case 403:
            showErrorOnce('You do not have permission to perform this action.', errorKey)
            break
          case 404:
            // Don't show error for expected 404s (like no cycles)
            break
          case 422:
            // Validation errors
            const message = data?.detail || data?.message || 'Validation error'
            showErrorOnce(typeof message === 'string' ? message : JSON.stringify(message), errorKey)
            break
          case 500:
            showErrorOnce('Server error. Please try again later.', errorKey)
            break
          default:
            showErrorOnce(data?.message || `Error: ${status}`, errorKey)
        }
      }
    } else if (error.request) {
      // Request made but no response - only show toast once, not for every retry
      if (error.code === 'ECONNABORTED') {
        // Timeout - don't show error, let component handle it
        console.warn('Request timeout:', error.config?.url)
      } else if (error.code === 'ERR_NETWORK' || error.message?.includes('Network Error')) {
        // Network error - only log, don't spam toasts
        console.error('Network error:', error.config?.url)
        // Only show toast if it's a user-initiated action, not auto-fetch
        const errorKey = `network-${error.config?.url}`
        if (error.config?.metadata?.userInitiated) {
          showErrorOnce('Network error. Please check your connection.', errorKey)
        }
      }
    } else {
      // Something else happened - only log, don't spam
      console.error('API error:', error)
    }
    
    return Promise.reject(error)
  }
)

// API endpoints
export const apiClient = {
  // EOM Endpoints
  eom: {
    // Submit nomination
    submitNomination: (data) => api.post('/api/v2/eom/nominations/submit', data),
    
    // Validate nomination
    validateNomination: (data) => api.post('/api/v2/eom/nominations/validate', data),
    
    // Get nominations for cycle
    getNominations: (cycleId) => api.get(`/api/v2/eom/nominations/cycle/${cycleId}`),
    
    // Submit vote
    submitVote: (data) => api.post('/api/v2/eom/vote', data),
    
    // Get winners
    getWinners: (cycleId) => api.get(`/api/v2/eom/winners/${cycleId}`),
    
    // Get eligible nominees
    getEligibleNominees: (cycleId) => api.get(`/api/v2/eom/rotation-rules/eligible-nominees/${cycleId}`),
    
    // Get rotation analytics
    getRotationAnalytics: (cycleId) => api.get(`/api/v2/eom/rotation-rules/analytics/${cycleId}`),
    
    // Suggest category based on achievement text
    suggestCategory: (achievementText, nomineeRole) => 
      api.post('/api/v2/eom/nominations/suggest-category', null, {
        params: {
          achievement_text: achievementText,
          nominee_role: nomineeRole
        }
      }),
    
    // Get Hall of Fame
    getHallOfFame: (params) => api.get('/api/v2/eom/hall-of-fame', { params }),
    
    // Get Diversity Tracking
    getDiversityTracking: (params) => api.get('/api/v2/eom/diversity-tracking', { params }),
    
    // Submit Feedback
    submitFeedback: (data) => api.post('/api/v2/eom/feedback', data),
    
    // Get Nomination Window Status
    getWindowStatus: (cycleId) => api.get(`/api/v2/eom/cycles/${cycleId}/window-status`),
  },
  
  // MRE Endpoints
  mre: {
    // Get assignments for cycle
    getAssignments: (cycleId) => api.get(`/api/v2/mre/assignments/${cycleId}`),
    
    // Submit evaluation
    submitEvaluation: (data) => api.post('/api/v2/mre/evaluations/process', data),
    
    // Get weighted scores
    getWeightedScores: (cycleId) => api.get(`/api/v2/mre/evaluations/${cycleId}/weighted-scores`),
    
    // Get evaluation domains
    getDomains: (targetGroup) => api.get(`/api/v2/mre/domains/${targetGroup}`),
  },
  
  // Bias Detection
  bias: {
    // Generate bias report
    generateReport: (cycleId) => api.post(`/api/v2/bias/reports/generate`, { cycle_id: cycleId }),
    
    // Get bias report
    getReport: (cycleId) => api.get(`/api/v2/bias/reports/${cycleId}`),
    
    // Get target-specific analysis
    getTargetAnalysis: (cycleId, email) => api.get(`/api/v2/bias/reports/${cycleId}/target/${email}`),
    
    // Get context-aware report
    getContextAwareReport: (cycleId) => api.post(`/api/v2/bias/360/context-aware-report/${cycleId}`),
  },
  
  // Dashboard
  dashboard: {
    // Get participation stats
    getParticipation: (cycleId) => api.get(`/api/v2/dashboard/participation/${cycleId}`),
    
    // Get analytics
    getAnalytics: (cycleId) => api.get(`/api/v2/dashboard/analytics/${cycleId}`),
  },
  
  // Cycles
  cycles: {
    // Get all cycles
    getAll: () => api.get('/api/v2/cycles'),
    
    // Get cycle by ID
    getById: (id) => api.get(`/api/v2/cycles/${id}`),
    
    // Get current cycle
    getCurrent: () => api.get('/api/v2/cycles/current'),

    // Create cycle (admin only)
    create: (data) => api.post('/api/v2/cycles', data),

    // Update cycle (admin only)
    update: (id, data) => api.put(`/api/v2/cycles/${id}`, data),
  },
  
  // People/Staff
  people: {
    // Get all staff
    getAll: () => api.get('/api/v2/people'),
    
    // Get staff by email
    getByEmail: (email) => api.get(`/api/v2/people/${email}`),
    
    // Get staff by segment
    getBySegment: (segment) => api.get(`/api/v2/people/segment/${segment}`),

    // Create staff member (admin only)
    create: (data) => api.post('/api/v2/people', data),

    // Update staff member (admin only)
    update: (email, data) => api.put(`/api/v2/people/${encodeURIComponent(email)}`, data),
  },
  
  // Staff Evaluator Management
  staff: {
    // Get evaluation status (who evaluates them, who they evaluate)
    getEvaluationStatus: (email, params) => api.get(`/api/v2/staff/${email}/evaluation-status`, { params }),
    
    // Get evaluators for a staff member
    getEvaluators: (email, params) => api.get(`/api/v2/staff/${email}/evaluators`, { params }),
    
    // Create evaluator assignments
    assignEvaluators: (email, data) => api.post(`/api/v2/staff/${email}/assign-evaluators`, data),
    
    // Update evaluator assignments
    updateEvaluators: (email, data) => api.put(`/api/v2/staff/${email}/evaluators`, data),
  },
  
  // Evaluation Matrix
  evaluationMatrix: {
    // Get complete evaluation matrix
    getMatrix: (cycleId) => api.get(`/api/v2/evaluation-matrix/${cycleId}`),
  },
  
  // Survey Endpoints
  survey: {
    getAll: (params) => api.get('/api/v2/surveys', { params }),
    getById: (id) => api.get(`/api/v2/surveys/${id}`),
    create: (data, params) => api.post('/api/v2/surveys', data, { params }),
    update: (id, data) => api.put(`/api/v2/surveys/${id}`, data),
    getQuestions: (surveyId) => api.get(`/api/v2/surveys/${surveyId}/questions`),
    getResponses: (surveyId, params) => api.get(`/api/v2/surveys/${surveyId}/responses`, { params }),
    submitResponse: (data) => api.post('/api/v2/surveys/responses', data),
    getAnalytics: (surveyId) => api.get(`/api/v2/surveys/${surveyId}/analytics`),
  },
  
  // Survey Identity Endpoints
  surveyIdentity: {
    setPreference: (data) => api.post('/api/v2/survey/identity/preference', data),
    reveal: (data) => api.post('/api/v2/survey/identity/reveal', data),
    getStatus: (userEmail, params) => api.get(`/api/v2/survey/identity/status/${userEmail}`, { params }),
    revokeAnonymity: (data) => api.post('/api/v2/survey/identity/revoke-anonymity', data),
    conditionalReveal: (data) => api.post('/api/v2/survey/identity/conditional-reveal', data),
    checkTriggers: (userEmail) => api.get(`/api/v2/survey/identity/conditional-reveal/check-triggers/${userEmail}`),
    executeReveal: (userEmail, data) => api.post(`/api/v2/survey/identity/conditional-reveal/execute/${userEmail}`, data),
  },
  
  // Survey Templates
  surveyTemplates: {
    getComprehensive: (identityMode = 'identified') => api.get('/api/v2/survey-templates/comprehensive', {
      params: { identity_mode: identityMode }
    }),
    getSection: (category, identityMode = 'identified') => api.get(`/api/v2/survey-templates/section/${category}`, {
      params: { identity_mode: identityMode }
    }),
  },
  
  // Identity Preferences (alias for surveyIdentity for backward compatibility)
  identityPreferences: {
    setPreference: (data) => api.post('/api/v2/survey/identity/preference', data),
    getPreference: (userEmail, surveyId) => api.get(`/api/v2/survey/identity/status/${userEmail}`, {
      params: surveyId ? { survey_id: surveyId } : {}
    }),
  },
  
  // Hybrid Identity
  hybridIdentity: {
    initializeSession: (data) => api.post('/api/v2/hybrid-identity/initialize-session', data),
    createSurveySession: (params) => api.post('/api/v2/hybrid-identity/create-survey-session', null, { params }),
    submitResponse: (data) => api.post('/api/v2/hybrid-identity/submit-response', data),
    switchMode: (data) => api.post('/api/v2/hybrid-identity/switch-mode', data),
    processReveal: (userEmail, revealType, conditions) => {
      const params = {
        user_email: userEmail,
        reveal_type: revealType,
      }
      if (conditions) {
        params.conditions = JSON.stringify(conditions)
      }
      return api.post('/api/v2/hybrid-identity/process-reveal-request', null, { params })
    },
    analyzeData: (params) => api.get('/api/v2/hybrid-identity/analyze-survey-data', { params }),
  },
  
  // Admin Dashboard
  admin: {
    getDashboard: () => api.get('/api/v2/admin/dashboard'),
    getOverviewCards: () => api.get('/api/v2/admin/dashboard/overview-cards'),
    getRealTimeMetrics: () => api.get('/api/v2/admin/dashboard/real-time-metrics'),
    getIdentityAnalytics: () => api.get('/api/v2/admin/dashboard/identity-analytics'),
  },
  
  // Integration Hub
  integration: {
    setupHR: (config) => api.post('/api/v2/integration/hr/setup', config),
    getEvaluationBridge: () => api.get('/api/v2/integration/evaluation-bridge'),
    syncStaff: (staffData) => api.post('/api/v2/integration/sync/staff', staffData),
    syncEvaluation: (evaluationData) => api.post('/api/v2/integration/sync/evaluation', evaluationData),
  },
  
  // System Setup
  system: {
    setup: (config) => api.post('/api/v2/system/setup', config),
    getGoLiveChecklist: () => api.get('/api/v2/system/go-live-checklist'),
  },

  // Bulk Import
  import: {
    staff: (formData) => api.post('/api/v2/import/staff', formData, { headers: { 'Content-Type': 'multipart/form-data' } }),
    eomVoters: (formData, params) => api.post('/api/v2/import/eom-voters', formData, { params, headers: { 'Content-Type': 'multipart/form-data' } }),
    eomCandidates: (formData) => api.post('/api/v2/import/eom-candidates', formData, { headers: { 'Content-Type': 'multipart/form-data' } }),
    weightMatrix: (formData, params) => api.post('/api/v2/import/weight-matrix', formData, { params, headers: { 'Content-Type': 'multipart/form-data' } }),
  },
  
  // Analytics
  analytics: {
    getParticipation: (cycleId) => api.get(`/api/v2/analytics/participation/${cycleId}`),
    getBias: (cycleId) => api.get(`/api/v2/analytics/bias/${cycleId}`),
    getEOM: (cycleId) => api.get(`/api/v2/analytics/eom/${cycleId}`),
    getMRE: (cycleId) => api.get(`/api/v2/analytics/mre/${cycleId}`),
  },

  // Audit Logs
  auditLogs: {
    getAll: (params) => api.get('/api/v2/audit-logs', { params }),
  },
  
  // Notifications
  notifications: {
    getAll: (params) => api.get('/api/v2/notifications', { params }),
    markRead: (id, params) => api.post(`/api/v2/notifications/${id}/read`, null, { params }),
    markAllRead: (params) => api.post('/api/v2/notifications/read-all', null, { params }),
    markMultipleRead: (ids, params) => api.post('/api/v2/notifications/mark-read', ids, { params }),
    getUnreadCount: (params) => api.get('/api/v2/notifications/unread-count', { params }),
  },
  
  // Objections
  objections: {
    getAll: (params) => api.get('/api/v2/objections', { params }),
    getById: (id) => api.get(`/api/v2/objections/${id}`),
    submit: (data) => api.post('/api/v2/objections', data),
    resolve: (id, data) => api.post(`/api/v2/objections/${id}/resolve`, data),
  },
  
  // Announcements
  announcements: {
    getAll: (params) => api.get('/api/v2/announcements', { params }),
    getById: (id) => api.get(`/api/v2/announcements/${id}`),
    create: (data) => api.post('/api/v2/announcements', data),
    update: (id, data) => api.put(`/api/v2/announcements/${id}`, data),
    delete: (id) => api.delete(`/api/v2/announcements/${id}`),
  },
  
  // Reports
  reports: {
    getCEO: (cycleId) => api.get(`/api/v2/reports/ceo/${cycleId}`),
    exportCEO: (cycleId, format) => api.post(`/api/v2/reports/ceo/export`, { cycle_id: cycleId, format }),
    getBias: (cycleId) => api.get(`/api/v2/reports/bias/${cycleId}`),
    getParticipation: (cycleId) => api.get(`/api/v2/reports/participation/${cycleId}`),
  },
  
  // Admin Settings
  settings: {
    get: () => api.get('/api/v2/admin/settings'),
    update: (data) => api.put('/api/v2/admin/settings', data),
    save: (data) => api.post('/api/v2/admin/settings', data),
  },
}

export default api
