import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { apiClient } from '../../lib/api'
import { useAuth } from '../../hooks/useAuth'
import { useSurveyTemplates } from '../../hooks/useSurveyTemplates'
import toast from 'react-hot-toast'
import ErrorBoundary from '../common/ErrorBoundary'
import LoadingSkeleton from '../common/LoadingSkeleton'

const SurveyCreate = () => {
  const navigate = useNavigate()
  const { user, isCEO, isPNC } = useAuth()
  const { comprehensiveTemplate, fetchComprehensive, loading: templateLoading } = useSurveyTemplates()
  const [loading, setLoading] = useState(false)
  const [useTemplate, setUseTemplate] = useState(false)
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    survey_type: 'comprehensive',
    start_date: '',
    end_date: '',
  })

  const handleLoadTemplate = async () => {
    try {
      await fetchComprehensive()
      setUseTemplate(true)
      toast.success('Template loaded')
    } catch (error) {
      toast.error('Failed to load template')
    }
  }

  const handleChange = (e) => {
    const { name, value } = e.target
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    if (!formData.title.trim()) {
      toast.error('Please enter a survey title')
      return
    }

    setLoading(true)
    try {
      const response = await apiClient.survey.create(formData, {
        user_email: user?.email,
      })
      
      toast.success('Survey created successfully!')
      
      // If using template, navigate to question management
      if (useTemplate && comprehensiveTemplate) {
        navigate(`/survey/${response.data.id}/questions?template=true`)
      } else {
        navigate(`/survey/${response.data.id}/questions`)
      }
    } catch (error) {
      let errorMessage = 'Failed to create survey'
      if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail
      }
      toast.error(errorMessage)
      console.error('Error creating survey:', error)
    } finally {
      setLoading(false)
    }
  }

  if (!isCEO && !isPNC) {
    return (
      <div className="p-6 text-center">
        <p className="text-ese-ink-medium text-lg">Access Denied</p>
        <p className="text-ese-ink-light mt-2">Admin access required to create surveys</p>
      </div>
    )
  }

  return (
    <ErrorBoundary>
      <div className="p-6 max-w-3xl mx-auto">
        <div className="mb-6">
          <button
            onClick={() => navigate('/survey')}
            className="text-ese-lang-900 hover:text-ese-lang-700 mb-4 flex items-center"
          >
            ← Back to Surveys
          </button>
          <h1 className="text-3xl font-bold text-ese-ink-navy">Create New Survey</h1>
        </div>

        {/* Template Option */}
        <div className="bg-white rounded-lg shadow-md p-6 border border-ese-ink-light mb-6">
          <h2 className="text-xl font-semibold text-ese-ink-navy mb-4">Survey Templates</h2>
          <div className="flex items-center space-x-4">
            <button
              onClick={handleLoadTemplate}
              disabled={templateLoading || useTemplate}
              className="px-4 py-2 bg-ese-int-700 text-white rounded-lg hover:bg-ese-int-800 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {templateLoading ? 'Loading...' : useTemplate ? 'Template Loaded' : 'Use Comprehensive Template'}
            </button>
            {useTemplate && comprehensiveTemplate && (
              <p className="text-sm text-ese-ink-medium">
                Template loaded: {comprehensiveTemplate.title || 'Comprehensive Survey Template'}
              </p>
            )}
          </div>
        </div>

        {/* Survey Form */}
        <form onSubmit={handleSubmit} className="bg-white rounded-lg shadow-md p-6 border border-ese-ink-light space-y-6">
          <div>
            <label className="block text-sm font-medium text-ese-ink-navy mb-2">
              Survey Title *
            </label>
            <input
              type="text"
              name="title"
              value={formData.title}
              onChange={handleChange}
              required
              className="w-full px-4 py-2 border border-ese-ink-light rounded-lg focus:outline-none focus:ring-2 focus:ring-ese-lang-700"
              placeholder="Enter survey title"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-ese-ink-navy mb-2">
              Description
            </label>
            <textarea
              name="description"
              value={formData.description}
              onChange={handleChange}
              rows={4}
              className="w-full px-4 py-2 border border-ese-ink-light rounded-lg focus:outline-none focus:ring-2 focus:ring-ese-lang-700"
              placeholder="Enter survey description"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-ese-ink-navy mb-2">
              Survey Type
            </label>
            <select
              name="survey_type"
              value={formData.survey_type}
              onChange={handleChange}
              className="w-full px-4 py-2 border border-ese-ink-light rounded-lg focus:outline-none focus:ring-2 focus:ring-ese-lang-700"
            >
              <option value="comprehensive">Comprehensive</option>
              <option value="climate">Climate Survey</option>
              <option value="feedback">Feedback Survey</option>
              <option value="evaluation">Evaluation Survey</option>
            </select>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-ese-ink-navy mb-2">
                Start Date
              </label>
              <input
                type="date"
                name="start_date"
                value={formData.start_date}
                onChange={handleChange}
                className="w-full px-4 py-2 border border-ese-ink-light rounded-lg focus:outline-none focus:ring-2 focus:ring-ese-lang-700"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-ese-ink-navy mb-2">
                End Date
              </label>
              <input
                type="date"
                name="end_date"
                value={formData.end_date}
                onChange={handleChange}
                min={formData.start_date}
                className="w-full px-4 py-2 border border-ese-ink-light rounded-lg focus:outline-none focus:ring-2 focus:ring-ese-lang-700"
              />
            </div>
          </div>

          <div className="flex justify-end space-x-4">
            <button
              type="button"
              onClick={() => navigate('/survey')}
              className="px-6 py-2 border border-ese-ink-light rounded-lg hover:bg-ese-lang-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-6 py-2 bg-ese-lang-900 text-white rounded-lg hover:bg-ese-lang-800 disabled:opacity-50"
            >
              {loading ? 'Creating...' : 'Create Survey'}
            </button>
          </div>
        </form>
      </div>
    </ErrorBoundary>
  )
}

export default SurveyCreate
