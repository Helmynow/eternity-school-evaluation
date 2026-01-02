import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { apiClient } from '../../lib/api'
import { useAuth } from '../../hooks/useAuth'
import toast from 'react-hot-toast'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, PieChart, Pie, Cell } from 'recharts'
import ErrorBoundary from '../common/ErrorBoundary'
import LoadingSkeleton from '../common/LoadingSkeleton'

const SurveyAnalytics = () => {
  const { surveyId } = useParams()
  const navigate = useNavigate()
  const { isCEO, isPNC } = useAuth()
  const [survey, setSurvey] = useState(null)
  const [analytics, setAnalytics] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!isCEO && !isPNC) {
      toast.error('Access denied. Admin access required.')
      navigate('/survey')
      return
    }

    if (surveyId) {
      loadData()
    }
  }, [surveyId, isCEO, isPNC, navigate])

  const loadData = async () => {
    setLoading(true)
    try {
      const [surveyRes, analyticsRes] = await Promise.all([
        apiClient.survey.getById(surveyId),
        apiClient.survey.getAnalytics(surveyId),
      ])
      setSurvey(surveyRes.data)
      setAnalytics(analyticsRes.data)
    } catch (error) {
      toast.error('Failed to load analytics')
      console.error('Error loading analytics:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="p-6 space-y-6">
        <div className="h-8 bg-ese-ink-light rounded w-1/3 animate-pulse"></div>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <LoadingSkeleton type="card" count={4} />
        </div>
        <LoadingSkeleton type="card" count={2} />
      </div>
    )
  }

  if (!analytics) {
    return (
      <div className="p-6 text-center">
        <p className="text-ese-ink-medium">No analytics data available</p>
        <button
          onClick={() => navigate('/survey')}
          className="mt-4 px-4 py-2 bg-ese-lang-900 text-white rounded-lg hover:bg-ese-lang-800"
        >
          Back to Surveys
        </button>
      </div>
    )
  }

  const COLORS = ['#094773', '#2C5B4C', '#E4A740', '#C88167', '#2D7EA1']

  return (
    <ErrorBoundary>
      <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <button
            onClick={() => navigate('/survey')}
            className="text-ese-lang-900 hover:text-ese-lang-700 mb-2 flex items-center"
          >
            ← Back to Surveys
          </button>
          <h1 className="text-3xl font-bold text-ese-ink-navy">
            {survey?.title} - Analytics
          </h1>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg shadow-md p-6 border border-ese-ink-light">
          <h3 className="text-sm font-medium text-ese-ink-medium mb-1">Total Responses</h3>
          <p className="text-3xl font-bold text-ese-lang-900">
            {analytics.total_responses || 0}
          </p>
        </div>
        <div className="bg-white rounded-lg shadow-md p-6 border border-ese-ink-light">
          <h3 className="text-sm font-medium text-ese-ink-medium mb-1">Completion Rate</h3>
          <p className="text-3xl font-bold text-ese-int-700">
            {analytics.completion_rate ? `${(analytics.completion_rate * 100).toFixed(1)}%` : '0%'}
          </p>
        </div>
        <div className="bg-white rounded-lg shadow-md p-6 border border-ese-ink-light">
          <h3 className="text-sm font-medium text-ese-ink-medium mb-1">Average Rating</h3>
          <p className="text-3xl font-bold text-ese-mustard">
            {analytics.average_rating ? analytics.average_rating.toFixed(1) : 'N/A'}
          </p>
        </div>
        <div className="bg-white rounded-lg shadow-md p-6 border border-ese-ink-light">
          <h3 className="text-sm font-medium text-ese-ink-medium mb-1">Identity Modes</h3>
          <p className="text-3xl font-bold text-ese-terracotta">
            {analytics.identity_modes?.length || 0}
          </p>
        </div>
      </div>

      {/* Identity Mode Distribution */}
      {analytics.identity_mode_distribution && (
        <div className="bg-white rounded-lg shadow-md p-6 border border-ese-ink-light">
          <h2 className="text-xl font-semibold text-ese-ink-navy mb-4">Identity Mode Distribution</h2>
          <PieChart width={400} height={300}>
            <Pie
              data={analytics.identity_mode_distribution}
              cx={200}
              cy={150}
              labelLine={false}
              label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
              outerRadius={80}
              fill="#8884d8"
              dataKey="value"
            >
              {analytics.identity_mode_distribution.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip />
          </PieChart>
        </div>
      )}

      {/* Response Trends */}
      {analytics.response_trends && (
        <div className="bg-white rounded-lg shadow-md p-6 border border-ese-ink-light">
          <h2 className="text-xl font-semibold text-ese-ink-navy mb-4">Response Trends</h2>
          <BarChart width={600} height={300} data={analytics.response_trends}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Bar dataKey="count" fill="#094773" />
          </BarChart>
        </div>
      )}

      {/* Category Breakdown */}
      {analytics.category_breakdown && (
        <div className="bg-white rounded-lg shadow-md p-6 border border-ese-ink-light">
          <h2 className="text-xl font-semibold text-ese-ink-navy mb-4">Category Breakdown</h2>
          <div className="space-y-4">
            {Object.entries(analytics.category_breakdown).map(([category, data]) => (
              <div key={category} className="border-b border-ese-ink-light pb-4">
                <h3 className="font-semibold text-ese-ink-navy mb-2 capitalize">{category}</h3>
                <div className="grid grid-cols-3 gap-4 text-sm">
                  <div>
                    <span className="text-ese-ink-medium">Responses: </span>
                    <span className="font-medium">{data.count || 0}</span>
                  </div>
                  <div>
                    <span className="text-ese-ink-medium">Average: </span>
                    <span className="font-medium">
                      {data.average ? data.average.toFixed(1) : 'N/A'}
                    </span>
                  </div>
                  <div>
                    <span className="text-ese-ink-medium">Sentiment: </span>
                    <span className="font-medium capitalize">{data.sentiment || 'N/A'}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
      </div>
    </ErrorBoundary>
  )
}

export default SurveyAnalytics
