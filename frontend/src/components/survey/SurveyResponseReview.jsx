import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { apiClient } from '../../lib/api'
import { useAuth } from '../../hooks/useAuth'
import toast from 'react-hot-toast'
import ErrorBoundary from '../common/ErrorBoundary'
import LoadingSkeleton from '../common/LoadingSkeleton'

const SurveyResponseReview = () => {
  const { surveyId } = useParams()
  const navigate = useNavigate()
  const { isCEO, isPNC } = useAuth()
  const [survey, setSurvey] = useState(null)
  const [responses, setResponses] = useState([])
  const [questions, setQuestions] = useState([])
  const [loading, setLoading] = useState(true)
  const [loadingResponses, setLoadingResponses] = useState(false)
  const [selectedResponseId, setSelectedResponseId] = useState(null)
  const [pageMeta, setPageMeta] = useState({
    skip: 0,
    limit: 200,
    total: 0,
    has_more: false,
  })
  const [filter, setFilter] = useState({
    identity_mode: 'all',
    date_from: '',
    date_to: '',
  })

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

  useEffect(() => {
    if (!surveyId) return
    // When filters change, reload from the first page using server-side filters.
    loadResponsesPage(0, pageMeta.limit, filter)
  }, [filter, surveyId])

  const loadData = async () => {
    setLoading(true)
    try {
      const [surveyRes, questionsRes] = await Promise.all([
        apiClient.survey.getById(surveyId),
        apiClient.survey.getQuestions(surveyId),
      ])
      setSurvey(surveyRes.data)
      setQuestions(questionsRes.data || [])
      await loadResponsesPage(0, pageMeta.limit, filter)
    } catch (error) {
      toast.error('Failed to load survey responses')
      console.error('Error loading responses:', error)
    } finally {
      setLoading(false)
    }
  }

  const loadResponsesPage = async (skip, limit, currentFilter) => {
    setLoadingResponses(true)
    try {
      const params = { skip, limit }
      const fm = currentFilter?.identity_mode
      if (fm && fm !== 'all') params.identity_mode = fm
      if (currentFilter?.date_from) params.date_from = currentFilter.date_from
      if (currentFilter?.date_to) params.date_to = currentFilter.date_to

      const responsesRes = await apiClient.survey.getResponses(surveyId, params)
      const payload = responsesRes.data || {}
      setResponses(payload.responses || [])
      setPageMeta({
        skip: payload.skip ?? skip,
        limit: payload.limit ?? limit,
        total: payload.total ?? 0,
        has_more: Boolean(payload.has_more),
      })
      setSelectedResponseId(null)
    } catch (error) {
      toast.error('Failed to load responses')
      console.error('Error loading responses page:', error)
    } finally {
      setLoadingResponses(false)
    }
  }

  const fetchAllResponsesForExport = async (currentFilter) => {
    const all = []
    let skip = 0
    const limit = 1000

    // Hard safety cap to avoid accidental infinite loops
    const maxPages = 200
    for (let i = 0; i < maxPages; i++) {
      const params = { skip, limit }
      const fm = currentFilter?.identity_mode
      if (fm && fm !== 'all') params.identity_mode = fm
      if (currentFilter?.date_from) params.date_from = currentFilter.date_from
      if (currentFilter?.date_to) params.date_to = currentFilter.date_to

      const res = await apiClient.survey.getResponses(surveyId, params)
      const payload = res.data || {}
      const batch = payload.responses || []
      all.push(...batch)
      if (!payload.has_more) break
      skip += limit
    }
    return all
  }

  const handleExport = async () => {
    try {
      const filteredResponses = await fetchAllResponsesForExport(filter)

      const exportData = {
        survey: {
          id: survey.id,
          title: survey.title,
          description: survey.description,
        },
        exported_at: new Date().toISOString(),
        total_responses: filteredResponses.length,
        responses: filteredResponses.map((r) => {
          const question = questions.find((q) => q.id === r.question_id)
          return {
            response_id: r.id,
            question_text: question?.question_text || 'Unknown',
            question_type: question?.question_type || 'text',
            response_text: r.response_text,
            response_value: r.response_value,
            identity_mode: r.identity_mode,
            submitted_at: r.submitted_at,
            respondent_email: r.respondent_email || 'Anonymous',
          }
        }),
      }

      const blob = new Blob([JSON.stringify(exportData, null, 2)], {
        type: 'application/json',
      })
      const downloadUrl = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = downloadUrl
      a.download = `survey_${surveyId}_responses_${new Date().toISOString().split('T')[0]}.json`
      a.click()
      window.URL.revokeObjectURL(downloadUrl)
      toast.success('Responses exported successfully')
    } catch (error) {
      toast.error('Failed to export responses')
      console.error('Error exporting:', error)
    }
  }

  const getQuestionText = (questionId) => {
    const question = questions.find((q) => q.id === questionId)
    return question?.question_text || 'Unknown Question'
  }

  const formatResponseValue = (value, questionType) => {
    if (!value) return 'N/A'
    if (typeof value === 'string') return value
    if (typeof value === 'object') {
      if (questionType === 'rating' && value.score) return value.score
      if (questionType === 'multiple_choice' && value.value) return value.value
      return JSON.stringify(value)
    }
    return String(value)
  }

  const filteredResponses = responses

  const showingFrom = pageMeta.total > 0 ? pageMeta.skip + 1 : 0
  const showingTo = Math.min(pageMeta.skip + responses.length, pageMeta.total)

  if (loading) {
    return (
      <div className="p-6">
        <LoadingSkeleton type="table" count={10} />
      </div>
    )
  }

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
              {survey?.title} - Response Review
            </h1>
            <p className="text-ese-ink-medium mt-1">
              Showing {showingFrom}-{showingTo} of {pageMeta.total} responses
            </p>
          </div>
          <button
            onClick={handleExport}
            className="px-6 py-2 bg-ese-int-700 text-white rounded-lg hover:bg-ese-int-800"
          >
            Export Responses
          </button>
        </div>

        {/* Filters */}
        <div className="bg-white rounded-lg shadow-md p-6 border border-ese-ink-light">
          <h2 className="text-xl font-semibold text-ese-ink-navy mb-4">Filters</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-ese-ink-navy mb-2">
                Identity Mode
              </label>
              <select
                value={filter.identity_mode}
                onChange={(e) =>
                  setFilter({ ...filter, identity_mode: e.target.value })
                }
                className="w-full px-4 py-2 border border-ese-ink-light rounded-lg focus:outline-none focus:ring-2 focus:ring-ese-lang-700"
              >
                <option value="all">All Modes</option>
                <option value="anonymous">Anonymous</option>
                <option value="conditional">Conditional</option>
                <option value="identified">Identified</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-ese-ink-navy mb-2">
                From Date
              </label>
              <input
                type="date"
                value={filter.date_from}
                onChange={(e) =>
                  setFilter({ ...filter, date_from: e.target.value })
                }
                className="w-full px-4 py-2 border border-ese-ink-light rounded-lg focus:outline-none focus:ring-2 focus:ring-ese-lang-700"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-ese-ink-navy mb-2">
                To Date
              </label>
              <input
                type="date"
                value={filter.date_to}
                onChange={(e) =>
                  setFilter({ ...filter, date_to: e.target.value })
                }
                className="w-full px-4 py-2 border border-ese-ink-light rounded-lg focus:outline-none focus:ring-2 focus:ring-ese-lang-700"
              />
            </div>
          </div>
        </div>

        {/* Responses List */}
        <div className="bg-white rounded-lg shadow-md border border-ese-ink-light">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-ese-lang-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-ese-ink-navy uppercase tracking-wider">
                    Question
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-ese-ink-navy uppercase tracking-wider">
                    Response
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-ese-ink-navy uppercase tracking-wider">
                    Identity Mode
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-ese-ink-navy uppercase tracking-wider">
                    Respondent
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-ese-ink-navy uppercase tracking-wider">
                    Submitted
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-ese-ink-light">
                {filteredResponses.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="px-6 py-12 text-center text-ese-ink-medium">
                      No responses found
                    </td>
                  </tr>
                ) : (
                  filteredResponses.map((response) => {
                    const question = questions.find((q) => q.id === response.question_id)
                    return (
                      <tr
                        key={response.id}
                        className="hover:bg-ese-lang-50 cursor-pointer"
                        onClick={() => setSelectedResponseId(response.id)}
                      >
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-ese-ink-navy">
                          {getQuestionText(response.question_id)}
                        </td>
                        <td className="px-6 py-4 text-sm text-ese-ink-medium">
                          {formatResponseValue(
                            response.response_value || response.response_text,
                            question?.question_type
                          )}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span
                            className={`px-2 py-1 text-xs rounded-full ${
                              response.identity_mode === 'anonymous'
                                ? 'bg-green-100 text-green-800'
                                : response.identity_mode === 'conditional'
                                ? 'bg-blue-100 text-blue-800'
                                : 'bg-yellow-100 text-yellow-800'
                            }`}
                          >
                            {response.identity_mode || 'N/A'}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-ese-ink-medium">
                          {response.respondent_email || 'Anonymous'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-ese-ink-medium">
                          {new Date(response.submitted_at).toLocaleString()}
                        </td>
                      </tr>
                    )
                  })
                )}
              </tbody>
            </table>
          </div>

          {/* Pagination Controls */}
          <div className="flex items-center justify-between px-6 py-4 border-t border-ese-ink-light">
            <div className="text-sm text-ese-ink-medium">
              Page size: {pageMeta.limit}
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => loadResponsesPage(Math.max(0, pageMeta.skip - pageMeta.limit), pageMeta.limit, filter)}
                disabled={loadingResponses || pageMeta.skip === 0}
                className="px-4 py-2 rounded-lg border border-ese-ink-light text-ese-ink-navy disabled:opacity-50 disabled:cursor-not-allowed hover:bg-ese-lang-50"
              >
                Previous
              </button>
              <button
                onClick={() => loadResponsesPage(pageMeta.skip + pageMeta.limit, pageMeta.limit, filter)}
                disabled={loadingResponses || !pageMeta.has_more}
                className="px-4 py-2 rounded-lg bg-ese-lang-900 text-white disabled:opacity-50 disabled:cursor-not-allowed hover:bg-ese-lang-800"
              >
                Next
              </button>
            </div>
          </div>
        </div>
      </div>
    </ErrorBoundary>
  )
}

export default SurveyResponseReview
