import { useState, useEffect } from 'react'
import { apiClient } from '../../lib/api'
import toast from 'react-hot-toast'
import ErrorBoundary from '../common/ErrorBoundary'
import LoadingSkeleton from '../common/LoadingSkeleton'

const BiasAlerts = () => {
  const [alerts, setAlerts] = useState([])
  const [loading, setLoading] = useState(true)
  const [selectedCycle, setSelectedCycle] = useState(null)
  const [cycles, setCycles] = useState([])

  useEffect(() => {
    loadCycles()
  }, [])

  useEffect(() => {
    if (selectedCycle) {
      loadBiasAlerts()
    }
  }, [selectedCycle])

  const loadCycles = async () => {
    try {
      const response = await apiClient.cycles.getAll()
      setCycles(response.data || [])
      if (response.data && response.data.length > 0) {
        setSelectedCycle(response.data[0].id)
      }
    } catch (error) {
      console.error('Error loading cycles:', error)
    }
  }

  const loadBiasAlerts = async () => {
    setLoading(true)
    try {
      const response = await apiClient.bias.getReport(selectedCycle)
      // Extract alerts from bias report
      const biasAlerts = response.data?.alerts || []
      setAlerts(biasAlerts)
    } catch (error) {
      console.error('Error loading bias alerts:', error)
      setAlerts([])
    } finally {
      setLoading(false)
    }
  }

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'critical':
        return 'bg-red-100 text-red-800 border-red-300'
      case 'high':
        return 'bg-orange-100 text-orange-800 border-orange-300'
      case 'medium':
        return 'bg-yellow-100 text-yellow-800 border-yellow-300'
      case 'low':
        return 'bg-blue-100 text-blue-800 border-blue-300'
      default:
        return 'bg-gray-100 text-gray-800 border-gray-300'
    }
  }

  if (loading) {
    return (
      <ErrorBoundary>
        <div className="flex items-center justify-center min-h-[200px]">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-ese-lang-900 mx-auto"></div>
            <p className="mt-2 text-ese-ink-navy">Loading bias alerts...</p>
          </div>
        </div>
      </ErrorBoundary>
    )
  }

  return (
    <ErrorBoundary>
      <div className="space-y-6">
        {/* Cycle Selector */}
      <div className="bg-white rounded-lg shadow-md p-4 border border-ese-ink-light">
        <label className="block text-sm font-medium text-ese-ink-navy mb-2">
          Select Cycle
        </label>
        <select
          value={selectedCycle || ''}
          onChange={(e) => setSelectedCycle(parseInt(e.target.value))}
          className="w-full md:w-auto px-4 py-2 border border-ese-ink-light rounded-lg focus:outline-none focus:ring-2 focus:ring-ese-lang-700"
        >
          {cycles.map((cycle) => (
            <option key={cycle.id} value={cycle.id}>
              {cycle.name || cycle.code}
            </option>
          ))}
        </select>
      </div>

      {/* Alerts List */}
      {alerts.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-lg shadow-md border border-ese-ink-light">
          <p className="text-ese-ink-medium">No bias alerts found for this cycle</p>
        </div>
      ) : (
        <div className="space-y-4">
          {alerts.map((alert, index) => (
            <div
              key={index}
              className={`p-6 rounded-lg border-2 ${getSeverityColor(alert.severity)}`}
            >
              <div className="flex justify-between items-start mb-2">
                <h3 className="text-lg font-semibold">{alert.title || 'Bias Alert'}</h3>
                <span className="px-2 py-1 text-xs rounded-full bg-white">
                  {alert.severity}
                </span>
              </div>
              <p className="text-sm mb-3">{alert.description || alert.message}</p>
              {alert.details && (
                <div className="mt-3 text-xs">
                  <strong>Details:</strong>
                  <pre className="mt-1 bg-white p-2 rounded overflow-auto">
                    {JSON.stringify(alert.details, null, 2)}
                  </pre>
                </div>
              )}
              {alert.target_email && (
                <p className="text-xs mt-2">
                  <strong>Target:</strong> {alert.target_email}
                </p>
              )}
            </div>
          ))}
        </div>
      )}
      </div>
    </ErrorBoundary>
  )
}

export default BiasAlerts
