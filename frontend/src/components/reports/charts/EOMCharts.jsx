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
 * EOM Winners Timeline Chart
 * Shows winners over time by category
 */
export const EOMWinnersTimeline = ({ cycleId }) => {
  const { data, loading } = useAPI(
    () => apiClient.eom.getHallOfFame({ cycle_id: cycleId }),
    { autoFetch: !!cycleId }
  )

  if (loading) return <LoadingSkeleton type="chart" />

  if (!data || !data.winners) {
    return <div className="text-ese-ink-blue text-center p-4">No winners data available</div>
  }

  // Group winners by month and category
  const timelineData = data.winners.reduce((acc, winner) => {
    const month = new Date(winner.won_date).toLocaleDateString('en-US', { month: 'short', year: 'numeric' })
    if (!acc[month]) acc[month] = {}
    acc[month][winner.category] = (acc[month][winner.category] || 0) + 1
    return acc
  }, {})

  const chartData = Object.entries(timelineData).map(([month, categories]) => ({
    month,
    ...categories
  }))

  return (
    <div className="ese-card">
      <h3 className="text-lg font-heading font-semibold text-ese-ink-navy mb-4">
        EOM Winners Timeline
      </h3>
      <ResponsiveContainer width="100%" height={300}>
        <AreaChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
          <XAxis dataKey="month" stroke="#6B7280" />
          <YAxis stroke="#6B7280" />
          <Tooltip />
          <Legend />
          <Area type="monotone" dataKey="outstanding_leadership" stackId="1" stroke="#1E3A8A" fill="#3B82F6" />
          <Area type="monotone" dataKey="team_spirit" stackId="1" stroke="#059669" fill="#10B981" />
          <Area type="monotone" dataKey="innovation" stackId="1" stroke="#DC2626" fill="#EF4444" />
          <Area type="monotone" dataKey="rising_star" stackId="1" stroke="#D97706" fill="#F59E0B" />
          <Area type="monotone" dataKey="service_excellence" stackId="1" stroke="#7C3AED" fill="#8B5CF6" />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}

/**
 * EOM Category Distribution Chart
 * Shows distribution of nominations/winners by category
 */
export const EOMCategoryDistribution = ({ cycleId, type = 'winners' }) => {
  const { data, loading } = useAPI(
    () => type === 'winners' 
      ? apiClient.eom.getHallOfFame({ cycle_id: cycleId })
      : apiClient.eom.getNominations(cycleId, { limit: 1000 }),
    { autoFetch: !!cycleId }
  )

  if (loading) return <LoadingSkeleton type="chart" />

  if (!data) {
    return <div className="text-ese-ink-blue text-center p-4">No data available</div>
  }

  const items = type === 'winners' ? data.winners : (data.nominations || data.items || data)
  if (!items || items.length === 0) {
    return <div className="text-ese-ink-blue text-center p-4">No {type} data available</div>
  }

  // Count by category
  const categoryCounts = items.reduce((acc, item) => {
    const category = item.category || 'unknown'
    acc[category] = (acc[category] || 0) + 1
    return acc
  }, {})

  const chartData = Object.entries(categoryCounts).map(([name, value]) => ({
    name: name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
    value
  }))

  return (
    <div className="ese-card">
      <h3 className="text-lg font-heading font-semibold text-ese-ink-navy mb-4">
        {type === 'winners' ? 'Winners' : 'Nominations'} by Category
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
 * EOM Diversity Metrics Chart
 * Shows diversity breakdown by gender, department, role
 */
export const EOMDiversityMetrics = ({ cycleId }) => {
  const { data, loading } = useAPI(
    () => apiClient.eom.getDiversityTracking({ cycle_id: cycleId }),
    { autoFetch: !!cycleId }
  )

  if (loading) return <LoadingSkeleton type="chart" />

  if (!data) {
    return <div className="text-ese-ink-blue text-center p-4">No diversity data available</div>
  }

  const genderData = data.gender_breakdown ? Object.entries(data.gender_breakdown).map(([name, value]) => ({
    name: name.charAt(0).toUpperCase() + name.slice(1),
    value
  })) : []

  const departmentData = data.department_breakdown ? Object.entries(data.department_breakdown).map(([name, value]) => ({
    name,
    value
  })) : []

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {genderData.length > 0 && (
        <div className="ese-card">
          <h3 className="text-lg font-heading font-semibold text-ese-ink-navy mb-4">
            Gender Distribution
          </h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={genderData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
              <XAxis dataKey="name" stroke="#6B7280" />
              <YAxis stroke="#6B7280" />
              <Tooltip />
              <Bar dataKey="value" fill="#3B82F6" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {departmentData.length > 0 && (
        <div className="ese-card">
          <h3 className="text-lg font-heading font-semibold text-ese-ink-navy mb-4">
            Department Distribution
          </h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={departmentData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
              <XAxis dataKey="name" stroke="#6B7280" angle={-45} textAnchor="end" height={100} />
              <YAxis stroke="#6B7280" />
              <Tooltip />
              <Bar dataKey="value" fill="#10B981" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  )
}

/**
 * EOM Voting Participation Chart
 * Shows voting participation over time
 */
export const EOMVotingParticipation = ({ cycleId }) => {
  const { data, loading } = useAPI(
    () => apiClient.analytics.getEOM(cycleId),
    { autoFetch: !!cycleId }
  )

  if (loading) return <LoadingSkeleton type="chart" />

  if (!data) {
    return <div className="text-ese-ink-blue text-center p-4">No participation data available</div>
  }

  const participationRate = data.total_voters > 0 
    ? ((data.total_voters / (data.total_voters + 10)) * 100).toFixed(1) // Approximate calculation
    : 0

  const chartData = [
    { name: 'Voted', value: data.total_voters || 0, fill: '#10B981' },
    { name: 'Not Voted', value: Math.max(0, 20 - (data.total_voters || 0)), fill: '#EF4444' }
  ]

  return (
    <div className="ese-card">
      <h3 className="text-lg font-heading font-semibold text-ese-ink-navy mb-4">
        Voting Participation
      </h3>
      <div className="mb-4">
        <div className="text-2xl font-bold text-ese-lang-900">{participationRate}%</div>
        <div className="text-sm text-ese-ink-blue">Participation Rate</div>
      </div>
      <ResponsiveContainer width="100%" height={200}>
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
