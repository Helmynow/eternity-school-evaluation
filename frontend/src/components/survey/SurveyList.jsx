import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { apiClient } from '../../lib/api'
import { useAuth } from '../../hooks/useAuth'
import { getSurveyErrorMessage, safeExtractArray } from '../../lib/errorMessages'
import { validateSurveys } from '../../lib/apiValidation'
import toast from 'react-hot-toast'
import PropTypes from 'prop-types'
import ErrorBoundary from '../common/ErrorBoundary'
import LoadingSkeleton from '../common/LoadingSkeleton'

const SurveyList = () => {
  const { user, isCEO, isPNC } = useAuth()
  const navigate = useNavigate()
  const [surveys, setSurveys] = useState([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('active') // 'all', 'active', 'draft', 'closed'

  useEffect(() => {
    loadSurveys()
  }, [filter])

  const loadSurveys = async () => {
    setLoading(true)
    try {
      const params = filter !== 'all' ? { status: filter } : {}
      const response = await apiClient.survey.getAll(params)
      
      // Validate and extract surveys
      const surveysData = safeExtractArray(response, [])
      const validation = validateSurveys(surveysData)
      
      if (validation.valid) {
        setSurveys(validation.data)
      } else {
        console.warn('Survey validation warnings:', validation.errors)
        // Still use data if available, but log warnings
        setSurveys(surveysData)
        if (validation.invalidCount > 0) {
          toast.error(`Some surveys have invalid data (${validation.invalidCount} items)`)
        }
      }
    } catch (error) {
      const errorMessage = getSurveyErrorMessage(error, 'load')
      toast.error(errorMessage)
      console.error('Error loading surveys:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleStartSurvey = (surveyId) => {
    navigate(`/survey/${surveyId}`)
  }

  const handleViewAnalytics = (surveyId) => {
    navigate(`/survey/${surveyId}/analytics`)
  }

  if (loading) {
    return (
      <div className="p-6 space-y-6">
        <div className="h-8 bg-ese-ink-light rounded w-1/3 animate-pulse"></div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <LoadingSkeleton type="card" count={3} />
        </div>
      </div>
    )
  }

  return (
    <ErrorBoundary>
      <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-ese-ink-navy">Surveys</h1>
        {(isCEO || isPNC) && (
          <button
            onClick={() => navigate('/survey/create')}
            className="px-4 py-2 bg-ese-lang-900 text-white rounded-lg hover:bg-ese-lang-800 transition-colors"
          >
            Create Survey
          </button>
        )}
      </div>

      {/* Filter Tabs */}
      <div className="flex space-x-2 border-b border-ese-ink-light">
        {['all', 'active', 'draft', 'closed'].map((status) => (
          <button
            key={status}
            onClick={() => setFilter(status)}
            className={`px-4 py-2 font-medium capitalize transition-colors ${
              filter === status
                ? 'border-b-2 border-ese-lang-900 text-ese-lang-900'
                : 'text-ese-ink-medium hover:text-ese-lang-900'
            }`}
          >
            {status}
          </button>
        ))}
      </div>

      {/* Survey Cards */}
      {surveys.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-ese-ink-medium text-lg">No surveys found</p>
          <p className="text-ese-ink-light mt-2">
            {filter === 'active' ? 'No active surveys at this time' : `No ${filter} surveys`}
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {surveys.map((survey) => (
            <div
              key={survey.id}
              className="bg-white rounded-lg shadow-md p-6 border border-ese-ink-light hover:shadow-lg transition-shadow"
            >
              <div className="flex justify-between items-start mb-4">
                <h3 className="text-xl font-semibold text-ese-ink-navy">{survey.title}</h3>
                <span
                  className={`px-2 py-1 text-xs rounded-full ${
                    survey.status === 'active'
                      ? 'bg-green-100 text-green-800'
                      : survey.status === 'draft'
                      ? 'bg-gray-100 text-gray-800'
                      : 'bg-red-100 text-red-800'
                  }`}
                >
                  {survey.status}
                </span>
              </div>

              {survey.description && (
                <p className="text-ese-ink-medium text-sm mb-4 line-clamp-2">{survey.description}</p>
              )}

              <div className="space-y-2 mb-4 text-sm text-ese-ink-medium">
                <div className="flex items-center">
                  <span className="font-medium">Type:</span>
                  <span className="ml-2 capitalize">{survey.survey_type || 'comprehensive'}</span>
                </div>
                {survey.start_date && (
                  <div className="flex items-center">
                    <span className="font-medium">Start:</span>
                    <span className="ml-2">{new Date(survey.start_date).toLocaleDateString()}</span>
                  </div>
                )}
                {survey.end_date && (
                  <div className="flex items-center">
                    <span className="font-medium">End:</span>
                    <span className="ml-2">{new Date(survey.end_date).toLocaleDateString()}</span>
                  </div>
                )}
              </div>

              <div className="flex space-x-2">
                {survey.status === 'active' && (
                  <button
                    onClick={() => handleStartSurvey(survey.id)}
                    className="flex-1 px-4 py-2 bg-ese-lang-900 text-white rounded-lg hover:bg-ese-lang-800 transition-colors"
                  >
                    Start Survey
                  </button>
                )}
                {(isCEO || isPNC) && (
                  <>
                    <button
                      onClick={() => navigate(`/survey/${survey.id}/responses`)}
                      className="px-4 py-2 bg-ese-lang-700 text-white rounded-lg hover:bg-ese-lang-800 transition-colors"
                    >
                      View Responses
                    </button>
                    <button
                      onClick={() => handleViewAnalytics(survey.id)}
                      className="px-4 py-2 bg-ese-int-700 text-white rounded-lg hover:bg-ese-int-800 transition-colors"
                    >
                      Analytics
                    </button>
                  </>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
      </div>
    </ErrorBoundary>
  )
}

export default SurveyList
