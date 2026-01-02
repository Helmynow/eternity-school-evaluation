import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { apiClient } from '../../lib/api'
import { useAuth } from '../../hooks/useAuth'
import { getSurveyErrorMessage, safeExtract, safeExtractArray } from '../../lib/errorMessages'
import { validateSurvey, validateQuestions } from '../../lib/apiValidation'
import toast from 'react-hot-toast'
import IdentityModeSelector from './IdentityModeSelector'
import SurveyForm from './SurveyForm'
import ErrorBoundary from '../common/ErrorBoundary'
import LoadingSkeleton, { LoadingSpinner } from '../common/LoadingSkeleton'

const SurveySession = () => {
  const { surveyId } = useParams()
  const navigate = useNavigate()
  const { user } = useAuth()
  const [survey, setSurvey] = useState(null)
  const [sessionToken, setSessionToken] = useState(null)
  const [identityMode, setIdentityMode] = useState(null)
  const [questions, setQuestions] = useState([])
  const [loading, setLoading] = useState(true)
  const [step, setStep] = useState('select-mode') // 'select-mode', 'survey'

  useEffect(() => {
    if (surveyId) {
      loadSurvey()
      // Try to restore session from localStorage
      const savedToken = localStorage.getItem('survey_session_token')
      const savedMode = localStorage.getItem('survey_identity_mode')
      if (savedToken && savedMode) {
        setSessionToken(savedToken)
        setIdentityMode(savedMode)
        setStep('survey')
      }
    }
  }, [surveyId])

  const loadSurvey = async () => {
    setLoading(true)
    try {
      const [surveyRes, questionsRes] = await Promise.all([
        apiClient.survey.getById(surveyId),
        apiClient.survey.getQuestions(surveyId),
      ])
      
      // Validate survey
      const surveyData = safeExtract(surveyRes)
      const surveyValidation = validateSurvey(surveyData)
      if (surveyValidation.valid) {
        setSurvey(surveyData)
      } else {
        throw new Error(`Invalid survey data: ${surveyValidation.errors.join(', ')}`)
      }
      
      // Validate questions
      const questionsData = safeExtractArray(questionsRes, [])
      const questionsValidation = validateQuestions(questionsData)
      if (questionsValidation.valid) {
        setQuestions(questionsData)
      } else {
        console.warn('Question validation warnings:', questionsValidation.errors)
        setQuestions(questionsData) // Use data anyway but log warnings
      }
    } catch (error) {
      const errorMessage = getSurveyErrorMessage(error, 'load')
      toast.error(errorMessage)
      console.error('Error loading survey:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleModeSelect = async (mode) => {
    try {
      setLoading(true)
      
      // Save preference to backend for persistence
      if (user?.email) {
        try {
          await apiClient.surveyIdentity.setPreference({
            user_email: user.email,
            survey_id: parseInt(surveyId),
            identity_mode: mode,
            privacy_level: mode === 'anonymous' ? 'maximum' : mode === 'conditional' ? 'high' : 'low',
          })
        } catch (prefError) {
          // Don't fail if preference save fails, just log it
          console.warn('Failed to save identity preference:', prefError)
        }
      }
      
      // Initialize hybrid identity session
      const sessionRes = await apiClient.hybridIdentity.initializeSession({
        user_email: user?.email,
        preferred_mode: mode,
        survey_id: parseInt(surveyId),
      })

      setSessionToken(sessionRes.data.session_token)
      setIdentityMode(mode)
      
      // Save to localStorage for session persistence
      localStorage.setItem('survey_session_token', sessionRes.data.session_token)
      localStorage.setItem('survey_identity_mode', mode)

      // Create survey session
      const surveySessionRes = await apiClient.hybridIdentity.createSurveySession({
        user_email: user?.email,
        survey_type: survey?.survey_type || 'comprehensive',
        session_token: sessionRes.data.session_token || sessionRes.data.sessionToken,
      })

      // Filter questions based on identity mode
      const modeQuestions = questions.filter((q) => {
        const modes = q.identity_modes || ['anonymous', 'conditional', 'identified']
        return modes.includes(mode)
      })

      setQuestions(modeQuestions)
      setStep('survey')
    } catch (error) {
      toast.error('Failed to initialize survey session')
      console.error('Error initializing session:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async (responses) => {
    try {
      setLoading(true)
      
      // Validate responses
      if (!responses || Object.keys(responses).length === 0) {
        toast.error('Please answer at least one question before submitting')
        return
      }
      
      // Check if we have a session token (hybrid flow) or need direct submission
      if (sessionToken) {
        // Hybrid Identity Flow - batch submission
        const formattedResponses = {}
        for (const [questionId, value] of Object.entries(responses)) {
          formattedResponses[questionId] = {
            question_id: parseInt(questionId),
            response_text: typeof value === 'string' ? value : null,
            response_value: typeof value === 'object' && value !== null 
              ? value 
              : (typeof value === 'number' ? { score: value } : { value })
          }
        }
        
        await apiClient.hybridIdentity.submitResponse({
          session_token: sessionToken,
          responses: formattedResponses,
        })
      } else {
        // Direct Submission Flow - submit each response individually
        // This is for cases where hybrid identity isn't used
        const submitPromises = Object.entries(responses).map(async ([questionId, value]) => {
          const responseData = {
            survey_id: parseInt(surveyId),
            question_id: parseInt(questionId),
            respondent_email: identityMode === 'identified' ? user?.email : null,
            anonymous_id: identityMode === 'anonymous' ? `anon_${Date.now()}_${Math.random().toString(36).substr(2, 9)}` : null,
            session_id: `direct_${Date.now()}`,
            identity_mode: identityMode || 'identified',
            response_text: typeof value === 'string' ? value : null,
            response_value: typeof value === 'object' && value !== null 
              ? value 
              : (typeof value === 'number' ? { score: value } : { value })
          }
          
          return apiClient.survey.submitResponse(responseData)
        })
        
        await Promise.all(submitPromises)
      }
      
      toast.success('Survey submitted successfully!')
      
      // Clear session data
      if (sessionToken) {
        localStorage.removeItem('survey_session_token')
        localStorage.removeItem('survey_identity_mode')
      }
      
      navigate('/survey')
    } catch (error) {
      // Use centralized error message utility
      const errorMessage = getSurveyErrorMessage(error, 'submit')
      toast.error(errorMessage)
      console.error('Error submitting survey:', {
        error,
        responses,
        sessionToken,
        identityMode,
        surveyId
      })
    } finally {
      setLoading(false)
    }
  }

  if (loading && !survey) {
    return (
      <div className="p-6">
        <span className="sr-only">Loading...</span>
        <LoadingSkeleton type="form" count={5} />
      </div>
    )
  }

  if (!survey) {
    return (
      <div className="p-6 text-center">
        <p className="text-ese-ink-medium">Survey not found</p>
        <button
          onClick={() => navigate('/survey')}
          className="mt-4 px-4 py-2 bg-ese-lang-900 text-white rounded-lg hover:bg-ese-lang-800"
        >
          Back to Surveys
        </button>
      </div>
    )
  }

  return (
    <ErrorBoundary>
      <div className="p-6 max-w-4xl mx-auto">
      {step === 'select-mode' ? (
        <div>
          <div className="mb-6">
            <h1 className="text-3xl font-bold text-ese-ink-navy mb-2">{survey.title}</h1>
            {survey.description && (
              <p className="text-ese-ink-medium">{survey.description}</p>
            )}
          </div>
          <IdentityModeSelector 
            onSelect={handleModeSelect} 
            surveyId={surveyId}
            initialMode={localStorage.getItem('survey_identity_mode')}
          />
        </div>
      ) : (
        <SurveyForm
          survey={survey}
          questions={questions}
          identityMode={identityMode}
          loading={loading}
          onSubmit={handleSubmit}
          onBack={() => setStep('select-mode')}
        />
      )}
      </div>
    </ErrorBoundary>
  )
}

export default SurveySession
