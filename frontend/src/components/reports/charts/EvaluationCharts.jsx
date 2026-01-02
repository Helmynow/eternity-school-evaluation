import { useState, useEffect } from 'react'
import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar
} from 'recharts'
import { apiClient } from '../../../lib/api'
import { useAPI } from '../../../hooks/useAPI'
import LoadingSkeleton from '../../common/LoadingSkeleton'

const COLORS = ['#1E3A8A', '#3B82F6', '#60A5FA', '#93C5FD', '#DBEAFE']

/**
 * Evaluation Score Distribution Chart
 * Shows distribution of evaluation scores
 */
export const EvaluationScoreDistribution = ({ cycleId }) => {
  const { data, loading } = useAPI(
    () => apiClient.mre.getWeightedScores(cycleId),
    { autoFetch: !!cycleId }
  )

  if (loading) return <LoadingSkeleton type="chart" />

  if (!data || !data.scores) {
    return <div className="text-ese-ink-blue text-center p-4">No score data available</div>
  }

  // Create score ranges
  const scoreRanges = {
    '90-100': 0,
    '80-89': 0,
    '70-79': 0,
    '60-69': 0,
    'Below 60': 0
  }

  data.scores.forEach(score => {
    const weightedScore = score.weighted_score || score.overall_score || 0
    if (weightedScore >= 90) scoreRanges['90-100']++
    else if (weightedScore >= 80) scoreRanges['80-89']++
    else if (weightedScore >= 70) scoreRanges['70-79']++
    else if (weightedScore >= 60) scoreRanges['60-69']++
    else scoreRanges['Below 60']++
  })

  const chartData = Object.entries(scoreRanges).map(([name, value]) => ({
    name,
    value
  }))

  return (
    <div className="ese-card">
      <h3 className="text-lg font-heading font-semibold text-ese-ink-navy mb-4">
        Score Distribution
      </h3>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
          <XAxis dataKey="name" stroke="#6B7280" />
          <YAxis stroke="#6B7280" />
          <Tooltip />
          <Bar dataKey="value" fill="#3B82F6" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

/**
 * Evaluation Participation Chart
 * Shows participation rates for evaluations
 */
export const EvaluationParticipation = ({ cycleId }) => {
  const { data, loading } = useAPI(
    () => apiClient.analytics.getParticipation(cycleId),
    { autoFetch: !!cycleId }
  )

  if (loading) return <LoadingSkeleton type="chart" />

  if (!data) {
    return <div className="text-ese-ink-blue text-center p-4">No participation data available</div>
  }

  const participationData = [
    { name: 'Completed', value: data.completed || 0, fill: '#10B981' },
    { name: 'Pending', value: (data.total || 0) - (data.completed || 0), fill: '#F59E0B' },
    { name: 'Overdue', value: data.overdue || 0, fill: '#EF4444' }
  ]

  const participationRate = data.total > 0 
    ? ((data.completed / data.total) * 100).toFixed(1)
    : 0

  return (
    <div className="ese-card">
      <h3 className="text-lg font-heading font-semibold text-ese-ink-navy mb-4">
        Evaluation Participation
      </h3>
      <div className="mb-4">
        <div className="text-2xl font-bold text-ese-lang-900">{participationRate}%</div>
        <div className="text-sm text-ese-ink-blue">Completion Rate</div>
      </div>
      <ResponsiveContainer width="100%" height={250}>
        <PieChart>
          <Pie
            data={participationData}
            cx="50%"
            cy="50%"
            labelLine={false}
            label={({ name, value }) => `${name}: ${value}`}
            outerRadius={80}
            fill="#8884d8"
            dataKey="value"
          >
            {participationData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.fill} />
            ))}
          </Pie>
          <Tooltip />
        </PieChart>
      </ResponsiveContainer>
    </div>
  )
}

/**
 * Domain Score Breakdown Chart
 * Shows average scores by domain
 */
export const DomainScoreBreakdown = ({ cycleId }) => {
  const { data, loading } = useAPI(
    () => apiClient.mre.getWeightedScores(cycleId),
    { autoFetch: !!cycleId }
  )

  if (loading) return <LoadingSkeleton type="chart" />

  if (!data || !data.scores) {
    return <div className="text-ese-ink-blue text-center p-4">No domain data available</div>
  }

  // Calculate average scores by domain
  const domainScores = {}
  let domainCount = 0

  data.scores.forEach(score => {
    if (score.domain_scores) {
      Object.entries(score.domain_scores).forEach(([domain, domainScore]) => {
        if (!domainScores[domain]) {
          domainScores[domain] = { total: 0, count: 0 }
        }
        domainScores[domain].total += domainScore
        domainScores[domain].count++
      })
      domainCount++
    }
  })

  const chartData = Object.entries(domainScores).map(([domain, stats]) => ({
    domain: domain.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
    average: (stats.total / stats.count).toFixed(1),
    fullMark: 100
  }))

  if (chartData.length === 0) {
    return <div className="text-ese-ink-blue text-center p-4">No domain scores available</div>
  }

  return (
    <div className="ese-card">
      <h3 className="text-lg font-heading font-semibold text-ese-ink-navy mb-4">
        Average Domain Scores
      </h3>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
          <XAxis dataKey="domain" stroke="#6B7280" angle={-45} textAnchor="end" height={100} />
          <YAxis stroke="#6B7280" domain={[0, 100]} />
          <Tooltip />
          <Bar dataKey="average" fill="#3B82F6" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

/**
 * Rater Context Distribution Chart
 * Shows distribution of evaluations by rater context
 */
export const RaterContextDistribution = ({ cycleId }) => {
  const { data, loading } = useAPI(
    () => apiClient.analytics.getMRE(cycleId),
    { autoFetch: !!cycleId }
  )

  if (loading) return <LoadingSkeleton type="chart" />

  if (!data || !data.rater_contexts) {
    return <div className="text-ese-ink-blue text-center p-4">No rater context data available</div>
  }

  const chartData = Object.entries(data.rater_contexts || {}).map(([name, value]) => ({
    name: name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
    value
  }))

  return (
    <div className="ese-card">
      <h3 className="text-lg font-heading font-semibold text-ese-ink-navy mb-4">
        Rater Context Distribution
      </h3>
      <ResponsiveContainer width="100%" height={300}>
        <PieChart>
          <Pie
            data={chartData}
            cx="50%"
            cy="50%"
            labelLine={false}
            label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
            outerRadius={100}
            fill="#8884d8"
            dataKey="value"
          >
            {chartData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip />
        </PieChart>
      </ResponsiveContainer>
    </div>
  )
}

/**
 * Evaluation Trends Over Time
 * Shows evaluation scores trend across cycles
 */
export const EvaluationTrends = ({ cycles }) => {
  const [trendData, setTrendData] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!cycles || cycles.length === 0) {
      setLoading(false)
      return
    }

    const loadTrendData = async () => {
      setLoading(true)
      try {
        const scores = await Promise.all(
          cycles.map(async (cycle) => {
            try {
              const response = await apiClient.mre.getWeightedScores(cycle.id)
              const scores = response.data?.scores || []
              const avgScore = scores.length > 0
                ? scores.reduce((sum, s) => sum + (s.weighted_score || s.overall_score || 0), 0) / scores.length
                : 0
              return {
                cycle: cycle.code || cycle.name,
                averageScore: avgScore.toFixed(1)
              }
            } catch (error) {
              return { cycle: cycle.code || cycle.name, averageScore: 0 }
            }
          })
        )
        setTrendData(scores)
      } catch (error) {
        console.error('Error loading trend data:', error)
      } finally {
        setLoading(false)
      }
    }

    loadTrendData()
  }, [cycles])

  if (loading) return <LoadingSkeleton type="chart" />

  if (trendData.length === 0) {
    return <div className="text-ese-ink-blue text-center p-4">No trend data available</div>
  }

  return (
    <div className="ese-card">
      <h3 className="text-lg font-heading font-semibold text-ese-ink-navy mb-4">
        Evaluation Score Trends
      </h3>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={trendData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
          <XAxis dataKey="cycle" stroke="#6B7280" />
          <YAxis stroke="#6B7280" domain={[0, 100]} />
          <Tooltip />
          <Legend />
          <Line type="monotone" dataKey="averageScore" stroke="#3B82F6" strokeWidth={2} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
