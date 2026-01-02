import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { apiClient } from '../../lib/api'
import { useAuth } from '../../hooks/useAuth'
import { useSurvey } from '../../hooks/useSurvey'
import toast from 'react-hot-toast'
import ErrorBoundary from '../common/ErrorBoundary'
import LoadingSkeleton from '../common/LoadingSkeleton'

const SurveyEdit = () => {
  const { surveyId } = useParams()
  const navigate = useNavigate()
  const { user, isCEO, isPNC } = useAuth()
  const { survey, loading, fetchSurvey, updateSurvey } = useSurvey(surveyId)
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    status: 'draft',
    start_date: '',
    end_date: '',
  })
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    if (surveyId) {
      fetchSurvey(surveyId)
    }
  }, [surveyId, fetchSurvey])

  useEffect(() => {
    if (survey) {
      setFormData({
        title: survey.title || '',
        description: survey.description || '',
        status: survey.status || 'draft',
        start_date: survey.start_date || '',
        end_date: survey.end_date || '',
      })
    }
  }, [survey])

  const handleChange = (e) => {
    const { name, value } = e.target
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSubmitting(true)

    try {
      await updateSurvey.mutate({
        id: surveyId,
        data: formData,
      })
      toast.success('Survey updated successfully!')
      navigate(`/survey/${surveyId}`)
    } catch (error) {
      toast.error('Failed to update survey')
      console.error('Error updating survey:', error)
    } finally {
      setSubmitting(false)
    }
  }

  if (!isCEO && !isPNC) {
    return (
      <div className="p-6 text-center">
        <p className="text-ese-ink-medium text-lg">Access Denied</p>
        <p className="text-ese-ink-light mt-2">Admin access required</p>
      </div>
    )
  }

  if (loading) {
    return (
      <div className="p-6">
        <LoadingSkeleton type="form" count={5} />
      </div>
    )
  }

  return (
    <ErrorBoundary>
      <div className="p-6 max-w-4xl mx-auto">
        <div className="mb-6">
          <button
            onClick={() => navigate(`/survey/${surveyId}`)}
            className="text-ese-lang-900 hover:text-ese-lang-700 mb-4 flex items-center"
          >
            ← Back to Survey
          </button>
          <h1 className="text-3xl font-bold text-ese-ink-navy">Edit Survey</h1>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6 border border-ese-ink-light">
          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-ese-ink-navy mb-1">
                Survey Title *
              </label>
              <input
                type="text"
                name="title"
                value={formData.title}
                onChange={handleChange}
                required
                className="w-full px-4 py-2 border border-ese-ink-light rounded-lg focus:outline-none focus:ring-2 focus:ring-ese-lang-700"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-ese-ink-navy mb-1">
                Description
              </label>
              <textarea
                name="description"
                value={formData.description}
                onChange={handleChange}
                rows={4}
                className="w-full px-4 py-2 border border-ese-ink-light rounded-lg focus:outline-none focus:ring-2 focus:ring-ese-lang-700"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-ese-ink-navy mb-1">
                Status
              </label>
              <select
                name="status"
                value={formData.status}
                onChange={handleChange}
                className="w-full px-4 py-2 border border-ese-ink-light rounded-lg focus:outline-none focus:ring-2 focus:ring-ese-lang-700"
              >
                <option value="draft">Draft</option>
                <option value="active">Active</option>
                <option value="closed">Closed</option>
              </select>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-ese-ink-navy mb-1">
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
                <label className="block text-sm font-medium text-ese-ink-navy mb-1">
                  End Date
                </label>
                <input
                  type="date"
                  name="end_date"
                  value={formData.end_date}
                  onChange={handleChange}
                  className="w-full px-4 py-2 border border-ese-ink-light rounded-lg focus:outline-none focus:ring-2 focus:ring-ese-lang-700"
                />
              </div>
            </div>

            <div className="flex justify-end space-x-4">
              <button
                type="button"
                onClick={() => navigate(`/survey/${surveyId}`)}
                className="px-6 py-2 border border-ese-ink-light rounded-lg hover:bg-ese-lang-50"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={submitting}
                className="px-6 py-2 bg-ese-lang-900 text-white rounded-lg hover:bg-ese-lang-800 disabled:opacity-50"
              >
                {submitting ? 'Updating...' : 'Update Survey'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </ErrorBoundary>
  )
}

export default SurveyEdit
