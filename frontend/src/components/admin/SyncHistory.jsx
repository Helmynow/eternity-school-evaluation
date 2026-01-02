import { useState, useEffect } from 'react'
import { apiClient } from '../../lib/api'
import ErrorBoundary from '../common/ErrorBoundary'
import LoadingSkeleton from '../common/LoadingSkeleton'

const SyncHistory = () => {
  const [syncHistory, setSyncHistory] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadSyncHistory()
  }, [])

  const loadSyncHistory = async () => {
    setLoading(true)
    try {
      // In a real implementation, this would fetch from a sync history endpoint
      // For now, we'll use a placeholder
      const history = [
        {
          id: 1,
          type: 'staff',
          status: 'success',
          records_synced: 150,
          timestamp: new Date().toISOString(),
        },
        {
          id: 2,
          type: 'evaluation',
          status: 'success',
          records_synced: 45,
          timestamp: new Date(Date.now() - 3600000).toISOString(),
        },
      ]
      setSyncHistory(history)
    } catch (error) {
      console.error('Error loading sync history:', error)
      setSyncHistory([])
    } finally {
      setLoading(false)
    }
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'success':
        return 'bg-green-100 text-green-800'
      case 'failed':
        return 'bg-red-100 text-red-800'
      case 'pending':
        return 'bg-yellow-100 text-yellow-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  if (loading) {
    return <LoadingSkeleton type="list" count={3} />
  }

  return (
    <ErrorBoundary>
      <div className="bg-white rounded-lg shadow-md p-6 border border-ese-ink-light">
      <h2 className="text-xl font-semibold text-ese-ink-navy mb-4">Sync History</h2>
      {syncHistory.length === 0 ? (
        <p className="text-ese-ink-medium">No sync history available</p>
      ) : (
        <div className="space-y-3">
          {syncHistory.map((sync) => (
            <div
              key={sync.id}
              className="flex justify-between items-center p-4 border border-ese-ink-light rounded-lg"
            >
              <div className="flex-1">
                <div className="flex items-center space-x-3 mb-2">
                  <span className="font-semibold text-ese-ink-navy capitalize">
                    {sync.type} Sync
                  </span>
                  <span
                    className={`px-2 py-1 text-xs rounded-full ${getStatusColor(sync.status)}`}
                  >
                    {sync.status}
                  </span>
                </div>
                <p className="text-sm text-ese-ink-medium">
                  {sync.records_synced} records synced
                </p>
                <p className="text-xs text-ese-ink-light mt-1">
                  {new Date(sync.timestamp).toLocaleString()}
                </p>
              </div>
            </div>
          ))}
        </div>
      )}
      </div>
    </ErrorBoundary>
  )
}

export default SyncHistory
