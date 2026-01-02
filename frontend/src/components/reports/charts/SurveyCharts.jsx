import { useState, useEffect } from 'react'
import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  AreaChart, Area
} from 'recharts'
import { apiClient } from '../../../lib/api'
import { useAPI } from '../../../hooks/useAPI'
import LoadingSkeleton from '../../common/LoadingSkeleton'

const COLORS = ['#1E3A8A', '#3B82F6', '#60A5FA', '#93C5FD', '#DBEAFE']

/**
 * Survey Response Rate Chart
 * Shows response rates for surveys
 */
export const SurveyResponseRate = ({ surveyId }) => {
  const { data, loading } = useAPI(
    () => apiClient.survey.getAnalytics(surveyId),
    { autoFetch: !!surveyId }
  )

  if (loading) return <LoadingSkeleton type="chart" />

  if (!data) {
    return <div className="text-ese-ink-blue text-center p-4">No response data available</div>
  }

  const totalInvited = data.total_invited || data.total_respondents || 100
  const totalResponses = data.total_responses || data.total_respondents || 0
  const responseRate = totalInvited > 0 ? ((totalResponses / totalInvited) * 100).toFixed(1) : 0

  const chartData = [
    { name: 'Responded', value: totalResponses, fill: '#10B981' },
    { name: 'Not Responded', value: totalInvited - totalResponses, fill: '#EF4444' }
  ]

  return (
    <div className="ese-card">
      <h3 className="text-lg font-heading font-semibold text-ese-ink-navy mb-4">
        Response Rate
      </h3>
      <div className="mb-4">
        <div className="text-2xl font-bold text-ese-lang-900">{responseRate}%</div>
        <div className="text-sm text-ese-ink-blue">
          {totalResponses} of {totalInvited} responses
        </div>
      </div>
      <ResponsiveContainer width="100%" height={250}>
        <PieChart>
          <Pie
            data={chartData}
            cx="50%"
            cy="50%"
            labelLine={false}
            label={({ name, value }) => `${name}: ${value}`}
            outerRadius={80}
            fill="#8884d8"
            dataKey="value"
          >
            {chartData.map((entry, index) => (
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
 * Identity Mode Distribution Chart
 * Shows distribution of responses by identity mode
 */
export const IdentityModeDistribution = ({ surveyId }) => {
  const { data, loading } = useAPI(
    () => apiClient.survey.getAnalytics(surveyId),
    { autoFetch: !!surveyId }
  )

  if (loading) return <LoadingSkeleton type="chart" />

  if (!data || !data.identity_breakdown) {
    return <div className="text-ese-ink-blue text-center p-4">No identity mode data available</div>
  }

  const chartData = Object.entries(data.identity_breakdown).map(([mode, count]) => ({
    name: mode.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
    value: count
  }))

  return (
    <div className="ese-card">
      <h3 className="text-lg font-heading font-semibold text-ese-ink-navy mb-4">
        Identity Mode Distribution
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
 * Survey Sentiment Analysis Chart
 * Shows sentiment distribution of responses
 */
export const SurveySentiment = ({ surveyId }) => {
  const { data, loading } = useAPI(
    () => apiClient.survey.getAnalytics(surveyId),
    { autoFetch: !!surveyId }
  )

  if (loading) return <LoadingSkeleton type="chart" />

  if (!data || !data.sentiment_analysis) {
    return <div className="text-ese-ink-blue text-center p-4">No sentiment data available</div>
  }

  const sentiment = data.sentiment_analysis
  const chartData = [
    { name: 'Positive', value: sentiment.positive || 0, fill: '#10B981' },
    { name: 'Neutral', value: sentiment.neutral || 0, fill: '#F59E0B' },
    { name: 'Negative', value: sentiment.negative || 0, fill: '#EF4444' }
  ]

  return (
    <div className="ese-card">
      <h3 className="text-lg font-heading font-semibold text-ese-ink-navy mb-4">
        Sentiment Analysis
      </h3>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
          <XAxis dataKey="name" stroke="#6B7280" />
          <YAxis stroke="#6B7280" />
          <Tooltip />
          <Bar dataKey="value" fill="#8884d8">
            {chartData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.fill} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

/**
 * Question Response Patterns Chart
 * Shows response patterns for key questions
 */
export const QuestionResponsePatterns = ({ surveyId }) => {
  const { data, loading } = useAPI(
    () => apiClient.survey.getAnalytics(surveyId),
    { autoFetch: !!surveyId }
  )

  if (loading) return <LoadingSkeleton type="chart" />

  if (!data || !data.question_analytics) {
    return <div className="text-ese-ink-blue text-center p-4">No question data available</div>
  }

  const questions = data.question_analytics.slice(0, 10) // Top 10 questions
  const chartData = questions.map((q, index) => ({
    question: `Q${index + 1}`,
    responses: q.response_count || 0,
    avgRating: q.average_rating || 0
  }))

  return (
    <div className="ese-card">
      <h3 className="text-lg font-heading font-semibold text-ese-ink-navy mb-4">
        Question Response Patterns
      </h3>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
          <XAxis dataKey="question" stroke="#6B7280" />
          <YAxis stroke="#6B7280" />
          <Tooltip />
          <Legend />
          <Bar dataKey="responses" fill="#3B82F6" name="Response Count" />
          <Bar dataKey="avgRating" fill="#10B981" name="Avg Rating" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

/**
 * Survey Completion Over Time
 * Shows survey completion timeline
 */
export const SurveyCompletionTimeline = ({ surveyId }) => {
  const { data, loading } = useAPI(
    () => apiClient.survey.getAnalytics(surveyId),
    { autoFetch: !!surveyId }
  )

  if (loading) return <LoadingSkeleton type="chart" />

  if (!data || !data.completion_timeline) {
    return <div className="text-ese-ink-blue text-center p-4">No timeline data available</div>
  }

  const chartData = data.completion_timeline.map(entry => ({
    date: new Date(entry.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
    completed: entry.completed || 0,
    cumulative: entry.cumulative || 0
  }))

  return (
    <div className="ese-card">
      <h3 className="text-lg font-heading font-semibold text-ese-ink-navy mb-4">
        Completion Timeline
      </h3>
      <ResponsiveContainer width="100%" height={300}>
        <AreaChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
          <XAxis dataKey="date" stroke="#6B7280" />
          <YAxis stroke="#6B7280" />
          <Tooltip />
          <Legend />
          <Area type="monotone" dataKey="completed" stackId="1" stroke="#3B82F6" fill="#3B82F6" />
          <Area type="monotone" dataKey="cumulative" stackId="2" stroke="#10B981" fill="#10B981" />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}
