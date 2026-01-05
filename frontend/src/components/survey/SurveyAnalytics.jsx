import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { apiClient } from '../../lib/api'
import { useAuth } from '../../hooks/useAuth'
import toast from 'react-hot-toast'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  PieChart,
  Pie,
  Cell,
  AreaChart,
  Area,
  ResponsiveContainer,
} from 'recharts'
import ErrorBoundary from '../common/ErrorBoundary'
import LoadingSkeleton from '../common/LoadingSkeleton'

const SurveyAnalytics = () => {
  const { surveyId } = useParams()
  const navigate = useNavigate()
  const { isCEO, isPNC } = useAuth()
  const [survey, setSurvey] = useState(null)
  const [analytics, setAnalytics] = useState(null)
  const [abandonment, setAbandonment] = useState(null)
  const [loading, setLoading] = useState(true)
  const [dateRange, setDateRange] = useState('30d')

  useEffect(() => {
    if (!isCEO && !isPNC) {
      toast.error('Access denied. Admin access required.')
      navigate('/survey')
      return
    }

    if (surveyId) {
      loadData()
    }
  }, [surveyId, isCEO, isPNC, navigate, dateRange])

  const loadData = async () => {
    setLoading(true)
    try {
      const [surveyRes, analyticsRes, abandonmentRes] = await Promise.all([
        apiClient.survey.getById(surveyId),
        apiClient.survey.getAnalytics(surveyId),
        apiClient.survey.getAbandonmentAnalytics({ survey_id: surveyId, date_range: dateRange }),
      ])
      setSurvey(surveyRes.data)
      setAnalytics(analyticsRes.data)
      setAbandonment(abandonmentRes.data)
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

  if (!analytics && !abandonment) {
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

  const funnelStages = abandonment?.charts?.completion_funnel?.stages || []
  const identityImpact = abandonment?.charts?.identity_mode_impact?.categories || []
  const heatmap = abandonment?.charts?.dropout_heatmap?.matrix || []
  const timeline = abandonment?.charts?.abandonment_timeline?.series || []
  const completionStatus = abandonment?.charts?.response_completion_status?.categories || []
  const departmentRates = abandonment?.charts?.department_completion_rates?.categories || []
  const durationBins = abandonment?.charts?.session_duration_distribution?.bins || []
  const dataConfidence = abandonment?.data_confidence || null
  const timeToAbandonStats = abandonment?.charts?.time_to_abandon?.statistics || null

  const binHistogram = (samples, bucketSizeMinutes = 5, maxMinutes = 120) => {
    const safe = Array.isArray(samples) ? samples.filter((n) => typeof n === 'number' && Number.isFinite(n) && n >= 0) : []
    const bins = []
    for (let start = 0; start < maxMinutes; start += bucketSizeMinutes) {
      bins.push({
        name: `${start}-${start + bucketSizeMinutes}m`,
        count: 0,
        start,
        end: start + bucketSizeMinutes,
      })
    }
    safe.forEach((value) => {
      const idx = Math.min(Math.floor(value / bucketSizeMinutes), bins.length - 1)
      if (idx >= 0) bins[idx].count += 1
    })
    return bins
  }

  const timeToAbandonSamples = abandonment?.charts?.time_to_abandon?.samples_minutes || []
  const timeToAbandonHistogram = binHistogram(timeToAbandonSamples, 5, 120)

  const timelineData = (() => {
    const active = timeline.find((s) => s.name === 'Active Respondents')?.data || []
    const abandoned = timeline.find((s) => s.name === 'Abandoned Sessions')?.data || []
    const map = new Map()
    active.forEach((p) => {
      map.set(p.minutes, { minutes: p.minutes, active: p.count, abandoned: 0 })
    })
    abandoned.forEach((p) => {
      const existing = map.get(p.minutes) || { minutes: p.minutes, active: 0, abandoned: 0 }
      existing.abandoned = p.count
      map.set(p.minutes, existing)
    })
    return Array.from(map.values()).sort((a, b) => a.minutes - b.minutes)
  })()

  const heatmapRowClass = (rate) => {
    if (rate >= 0.5) return 'bg-red-100'
    if (rate >= 0.3) return 'bg-red-50'
    if (rate >= 0.15) return 'bg-ese-mustard/10'
    return ''
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
            {survey?.title} - Analytics
          </h1>
        </div>

        <div className="flex items-center gap-2">
          <label className="text-sm text-ese-ink-medium" htmlFor="survey-analytics-date-range">
            Date range
          </label>
          <select
            id="survey-analytics-date-range"
            className="border border-ese-ink-light rounded-lg px-3 py-2 text-sm bg-white"
            value={dateRange}
            onChange={(e) => setDateRange(e.target.value)}
          >
            <option value="7d">Last 7 days</option>
            <option value="30d">Last 30 days</option>
            <option value="90d">Last 90 days</option>
            <option value="all">All time</option>
          </select>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg shadow-md p-6 border border-ese-ink-light">
          <h3 className="text-sm font-medium text-ese-ink-medium mb-1">Started Sessions</h3>
          <p className="text-3xl font-bold text-ese-lang-900">
            {abandonment?.summary?.started_sessions ?? analytics?.total_responses ?? 0}
          </p>
        </div>
        <div className="bg-white rounded-lg shadow-md p-6 border border-ese-ink-light">
          <h3 className="text-sm font-medium text-ese-ink-medium mb-1">Completion Rate</h3>
          <p className="text-3xl font-bold text-ese-int-700">
            {abandonment?.summary?.completion_rate != null
              ? `${(abandonment.summary.completion_rate * 100).toFixed(1)}%`
              : 'N/A'}
          </p>
        </div>
        <div className="bg-white rounded-lg shadow-md p-6 border border-ese-ink-light">
          <h3 className="text-sm font-medium text-ese-ink-medium mb-1">Abandonment Rate</h3>
          <p className="text-3xl font-bold text-ese-mustard">
            {abandonment?.summary?.abandonment_rate != null
              ? `${(abandonment.summary.abandonment_rate * 100).toFixed(1)}%`
              : 'N/A'}
          </p>
        </div>
        <div className="bg-white rounded-lg shadow-md p-6 border border-ese-ink-light">
          <h3 className="text-sm font-medium text-ese-ink-medium mb-1">Median Time to Abandon</h3>
          <p className="text-3xl font-bold text-ese-terracotta">
            {abandonment?.summary?.median_time_to_abandon_minutes != null
              ? `${abandonment.summary.median_time_to_abandon_minutes.toFixed(1)}m`
              : 'N/A'}
          </p>
        </div>
      </div>

      {dataConfidence?.level && (
        <div className="bg-white rounded-lg shadow-md p-4 border border-ese-ink-light">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-2">
            <div className="text-sm">
              <span className="font-semibold text-ese-ink-navy">Data confidence:</span>{' '}
              <span className="text-ese-ink-medium">{dataConfidence.level}</span>
            </div>
            {dataConfidence.notes && Array.isArray(dataConfidence.notes) && dataConfidence.notes.length > 0 && (
              <div className="text-xs text-ese-ink-medium">
                {dataConfidence.notes.join(' • ')}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Abandonment Analytics */}
      {abandonment && (
        <>
          {/* Completion Funnel */}
          {funnelStages.length > 0 && (
            <div className="bg-white rounded-lg shadow-md p-6 border border-ese-ink-light">
              <h2 className="text-xl font-semibold text-ese-ink-navy mb-4">Survey Completion Funnel</h2>
              <div className="w-full h-[320px]">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={funnelStages} margin={{ top: 10, right: 24, left: 8, bottom: 24 }}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" interval={0} />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="count" fill="#094773" name="Sessions" />
                    <Bar dataKey="dropout" fill="#C88167" name="Dropouts" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
              <div className="mt-4 text-sm text-ese-ink-medium">
                Idle timeout assumption: {abandonment.summary?.timeout_minutes ?? 30} minutes
              </div>
            </div>
          )}

          {/* Identity Mode Impact */}
          {identityImpact.length > 0 && (
            <div className="bg-white rounded-lg shadow-md p-6 border border-ese-ink-light">
              <h2 className="text-xl font-semibold text-ese-ink-navy mb-4">Completion by Identity Mode</h2>
              <div className="w-full h-[320px]">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={identityImpact} margin={{ top: 10, right: 24, left: 8, bottom: 24 }}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="mode" interval={0} />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="completed" stackId="a" fill="#2C5B4C" name="Completed" />
                    <Bar dataKey="abandoned" stackId="a" fill="#C88167" name="Abandoned (timeout)" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}

          {/* Dropout Heatmap */}
          {Array.isArray(heatmap) && heatmap.length > 0 && (
            <div className="bg-white rounded-lg shadow-md p-6 border border-ese-ink-light">
              <h2 className="text-xl font-semibold text-ese-ink-navy mb-4">Dropout Heatmap (by Question)</h2>
              <div className="overflow-x-auto">
                <table className="min-w-full text-sm">
                  <thead>
                    <tr className="bg-ese-lang-50">
                      <th className="text-left px-4 py-2">#</th>
                      <th className="text-left px-4 py-2">Question</th>
                      <th className="text-right px-4 py-2">Reached</th>
                      <th className="text-right px-4 py-2">Dropouts</th>
                      <th className="text-right px-4 py-2">Dropout Rate</th>
                    </tr>
                  </thead>
                  <tbody>
                    {heatmap.map((row) => (
                      <tr key={row.order_index} className={`${heatmapRowClass(row.dropout_rate)} border-t border-ese-ink-light`}>
                        <td className="px-4 py-2 text-ese-ink-medium">{row.order_index + 1}</td>
                        <td className="px-4 py-2">{row.question_text || '—'}</td>
                        <td className="px-4 py-2 text-right">{row.completions ?? 0}</td>
                        <td className="px-4 py-2 text-right">{row.dropouts ?? 0}</td>
                        <td className="px-4 py-2 text-right">
                          {row.dropout_rate != null ? `${(row.dropout_rate * 100).toFixed(1)}%` : '—'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Time to Abandon */}
          {Array.isArray(timeToAbandonSamples) && timeToAbandonSamples.length > 0 && (
            <div className="bg-white rounded-lg shadow-md p-6 border border-ese-ink-light">
              <h2 className="text-xl font-semibold text-ese-ink-navy mb-4">Time to Abandon (minutes)</h2>
              <div className="w-full h-[320px]">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={timeToAbandonHistogram} margin={{ top: 10, right: 24, left: 8, bottom: 24 }}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" interval={0} />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="count" fill="#E4A740" name="Sessions" />
                  </BarChart>
                </ResponsiveContainer>
              </div>

              {timeToAbandonStats && (
                <div className="mt-3 text-sm text-ese-ink-medium flex flex-wrap gap-x-6 gap-y-2">
                  {timeToAbandonStats.median_minutes != null && (
                    <div>
                      <span className="font-semibold text-ese-ink-navy">Median:</span> {timeToAbandonStats.median_minutes}m
                    </div>
                  )}
                  {timeToAbandonStats.mean_minutes != null && (
                    <div>
                      <span className="font-semibold text-ese-ink-navy">Mean:</span> {timeToAbandonStats.mean_minutes.toFixed(1)}m
                    </div>
                  )}
                  {timeToAbandonStats.min_minutes != null && (
                    <div>
                      <span className="font-semibold text-ese-ink-navy">Min:</span> {timeToAbandonStats.min_minutes}m
                    </div>
                  )}
                  {timeToAbandonStats.max_minutes != null && (
                    <div>
                      <span className="font-semibold text-ese-ink-navy">Max:</span> {timeToAbandonStats.max_minutes}m
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {/* Abandonment Timeline */}
          {Array.isArray(timelineData) && timelineData.length > 0 && (
            <div className="bg-white rounded-lg shadow-md p-6 border border-ese-ink-light">
              <h2 className="text-xl font-semibold text-ese-ink-navy mb-4">Survey Abandonment Over Time</h2>
              <div className="w-full h-[320px]">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={timelineData} margin={{ top: 10, right: 24, left: 8, bottom: 24 }}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="minutes" label={{ value: 'Minutes', position: 'insideBottom', offset: -5 }} />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Area type="monotone" dataKey="active" stroke="#2C5B4C" fill="#2C5B4C" fillOpacity={0.15} name="Active" />
                    <Area type="monotone" dataKey="abandoned" stroke="#C88167" fill="#C88167" fillOpacity={0.15} name="Abandoned" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}

          {/* Completion Status */}
          {Array.isArray(completionStatus) && completionStatus.length > 0 && (
            <div className="bg-white rounded-lg shadow-md p-6 border border-ese-ink-light">
              <h2 className="text-xl font-semibold text-ese-ink-navy mb-4">Response Completion Status</h2>
              <div className="w-full h-[320px] max-w-[520px]">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={completionStatus}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                      outerRadius="70%"
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {completionStatus.map((entry, index) => (
                        <Cell key={`status-cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}

          {/* Department Completion Rates */}
          {Array.isArray(departmentRates) && departmentRates.length > 0 && (
            <div className="bg-white rounded-lg shadow-md p-6 border border-ese-ink-light">
              <h2 className="text-xl font-semibold text-ese-ink-navy mb-4">Completion Rate by Department</h2>
              <div className="w-full h-[360px]">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={departmentRates} margin={{ top: 10, right: 24, left: 8, bottom: 48 }}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="department" interval={0} angle={-20} textAnchor="end" height={70} />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="completed" stackId="a" fill="#2C5B4C" name="Completed" />
                    <Bar dataKey="abandoned" stackId="a" fill="#C88167" name="Abandoned" />
                    <Bar dataKey="active" stackId="a" fill="#2D7EA1" name="Active" />
                  </BarChart>
                </ResponsiveContainer>
              </div>

              <div className="mt-3 text-xs text-ese-ink-medium">
                Tip: completion rate is calculated as completed / total started (per department).
              </div>
            </div>
          )}

          {/* Session Duration Distribution */}
          {Array.isArray(durationBins) && durationBins.length > 0 && (
            <div className="bg-white rounded-lg shadow-md p-6 border border-ese-ink-light">
              <h2 className="text-xl font-semibold text-ese-ink-navy mb-4">Session Duration Distribution</h2>
              <div className="w-full h-[320px]">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={durationBins} margin={{ top: 10, right: 24, left: 8, bottom: 36 }}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="range" interval={0} angle={-15} textAnchor="end" height={60} />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="count" fill="#094773" name="Sessions" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}
        </>
      )}

      {/* Identity Mode Distribution */}
      {analytics?.identity_mode_distribution && (
        <div className="bg-white rounded-lg shadow-md p-6 border border-ese-ink-light">
          <h2 className="text-xl font-semibold text-ese-ink-navy mb-4">Identity Mode Distribution</h2>
          <div className="w-full h-[320px] max-w-[520px]">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={analytics.identity_mode_distribution}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                  outerRadius="70%"
                  fill="#8884d8"
                  dataKey="value"
                >
                  {analytics.identity_mode_distribution.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Response Trends */}
      {analytics?.response_trends && (
        <div className="bg-white rounded-lg shadow-md p-6 border border-ese-ink-light">
          <h2 className="text-xl font-semibold text-ese-ink-navy mb-4">Response Trends</h2>
          <div className="w-full h-[320px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={analytics.response_trends} margin={{ top: 10, right: 24, left: 8, bottom: 24 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="count" fill="#094773" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Category Breakdown */}
      {analytics?.category_breakdown && (
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
