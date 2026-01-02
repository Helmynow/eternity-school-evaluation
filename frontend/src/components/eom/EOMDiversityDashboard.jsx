import { useState, useEffect } from 'react'
import { useAPI } from '../../hooks/useAPI'
import { apiClient } from '../../lib/api'
import toast from 'react-hot-toast'

const EOMDiversityDashboard = () => {
  const [diversityData, setDiversityData] = useState([])
  const [loading, setLoading] = useState(true)
  const [selectedCycle, setSelectedCycle] = useState(null)

  useEffect(() => {
    loadDiversityData()
  }, [selectedCycle])

  const loadDiversityData = async () => {
    try {
      setLoading(true)
      const response = await apiClient.get('/api/v2/eom/diversity-tracking', {
        params: selectedCycle ? { cycle_id: selectedCycle } : {}
      })
      setDiversityData(response.data || [])
    } catch (error) {
      console.error('Failed to load diversity data:', error)
      toast.error('Failed to load diversity tracking data')
    } finally {
      setLoading(false)
    }
  }

  // Aggregate data for charts
  const segmentStats = diversityData.reduce((acc, item) => {
    if (!acc[item.segment]) {
      acc[item.segment] = { winners: 0, nominees: 0 }
    }
    acc[item.segment].winners += item.winners_count || 0
    acc[item.segment].nominees += item.nominees_count || 0
    return acc
  }, {})

  const categoryStats = diversityData.reduce((acc, item) => {
    if (!acc[item.category]) {
      acc[item.category] = { winners: 0, nominees: 0 }
    }
    acc[item.category].winners += item.winners_count || 0
    acc[item.category].nominees += item.nominees_count || 0
    return acc
  }, {})

  const departmentStats = diversityData.reduce((acc, item) => {
    if (!acc[item.department]) {
      acc[item.department] = { winners: 0, nominees: 0 }
    }
    acc[item.department].winners += item.winners_count || 0
    acc[item.department].nominees += item.nominees_count || 0
    return acc
  }, {})

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-ese-lang-900"></div>
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-heading font-bold text-ese-ink-navy mb-2">
          <span className="flex items-center gap-2">
            <img src="/assets/icons/Analytics.png" alt="Analytics" className="w-8 h-8" onError={(e) => { e.target.style.display = 'none' }} />
            Diversity Monitoring Dashboard
          </span>
        </h1>
        <p className="text-ese-ink-navy/70">
          Track EOM recognition across segments, departments, and roles
        </p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-sm font-medium text-ese-ink-navy/70 mb-2">Total Winners</h3>
          <p className="text-3xl font-bold text-ese-lang-900">
            {Object.values(segmentStats).reduce((sum, stat) => sum + stat.winners, 0)}
          </p>
        </div>
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-sm font-medium text-ese-ink-navy/70 mb-2">Total Nominees</h3>
          <p className="text-3xl font-bold text-ese-int-900">
            {Object.values(segmentStats).reduce((sum, stat) => sum + stat.nominees, 0)}
          </p>
        </div>
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-sm font-medium text-ese-ink-navy/70 mb-2">Categories</h3>
          <p className="text-3xl font-bold text-ese-accent-terracotta">
            {Object.keys(categoryStats).length}
          </p>
        </div>
      </div>

      {/* Segment Distribution */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <h2 className="text-xl font-heading font-semibold text-ese-ink-navy mb-4">
          Recognition by Segment
        </h2>
        <div className="space-y-4">
          {Object.entries(segmentStats).map(([segment, stats]) => {
            const totalWinners = Object.values(segmentStats).reduce((sum, s) => sum + s.winners, 0)
            const percentage = totalWinners > 0 ? (stats.winners / totalWinners * 100).toFixed(1) : 0
            return (
              <div key={segment}>
                <div className="flex justify-between mb-1">
                  <span className="text-sm font-medium text-ese-ink-navy capitalize">
                    {segment.replace('_', ' ')}
                  </span>
                  <span className="text-sm text-ese-ink-navy/70">
                    {stats.winners} winners ({percentage}%)
                  </span>
                </div>
                <div className="w-full bg-ese-accent-beige rounded-full h-2">
                  <div
                    className="bg-ese-lang-900 h-2 rounded-full transition-all"
                    style={{ width: `${percentage}%` }}
                  ></div>
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* Category Distribution */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <h2 className="text-xl font-heading font-semibold text-ese-ink-navy mb-4">
          Recognition by Category
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {Object.entries(categoryStats).map(([category, stats]) => (
            <div key={category} className="border border-ese-accent-beige rounded-lg p-4">
              <h3 className="font-medium text-ese-ink-navy mb-2 capitalize">
                {category.replace('_', ' ')}
              </h3>
              <div className="flex justify-between text-sm">
                <span className="text-ese-ink-navy/70">Winners:</span>
                <span className="font-medium">{stats.winners}</span>
              </div>
              <div className="flex justify-between text-sm mt-1">
                <span className="text-ese-ink-navy/70">Nominees:</span>
                <span className="font-medium">{stats.nominees}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Department Distribution */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-heading font-semibold text-ese-ink-navy mb-4">
          Recognition by Department
        </h2>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-ese-accent-beige">
            <thead className="bg-ese-lang-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-ese-ink-navy uppercase tracking-wider">
                  Department
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-ese-ink-navy uppercase tracking-wider">
                  Winners
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-ese-ink-navy uppercase tracking-wider">
                  Nominees
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-ese-accent-beige">
              {Object.entries(departmentStats).map(([department, stats]) => (
                <tr key={department}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-ese-ink-navy">
                    {department || 'N/A'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-ese-ink-navy">
                    {stats.winners}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-ese-ink-navy">
                    {stats.nominees}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

export default EOMDiversityDashboard
