import ErrorBoundary from '../common/ErrorBoundary'
import LoadingSkeleton from '../common/LoadingSkeleton'

const IntegrationStatus = ({ evaluationBridge, loading }) => {
  if (loading) {
    return (
      <div className="space-y-4">
        <LoadingSkeleton type="card" count={3} />
      </div>
    )
  }

  if (!evaluationBridge) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6 border border-ese-ink-light">
        <p className="text-ese-ink-medium">No integration configured</p>
        <p className="text-sm text-ese-ink-light mt-2">
          Set up HR integration to enable data synchronization
        </p>
      </div>
    )
  }

  return (
    <ErrorBoundary>
      <div className="space-y-4">
      {/* Connection Status */}
      <div className="bg-white rounded-lg shadow-md p-6 border border-ese-ink-light">
        <h2 className="text-xl font-semibold text-ese-ink-navy mb-4">Connection Status</h2>
        <div className="flex items-center space-x-3">
          <div
            className={`w-3 h-3 rounded-full ${
              evaluationBridge.connected
                ? 'bg-green-500'
                : 'bg-red-500'
            }`}
          />
          <span className="text-ese-ink-navy">
            {evaluationBridge.connected ? 'Connected' : 'Disconnected'}
          </span>
        </div>
        {evaluationBridge.last_sync && (
          <p className="text-sm text-ese-ink-medium mt-2">
            Last sync: {new Date(evaluationBridge.last_sync).toLocaleString()}
          </p>
        )}
      </div>

      {/* Bridge Configuration */}
      <div className="bg-white rounded-lg shadow-md p-6 border border-ese-ink-light">
        <h2 className="text-xl font-semibold text-ese-ink-navy mb-4">Evaluation Bridge</h2>
        <div className="space-y-3">
          {evaluationBridge.config && (
            <div>
              <h3 className="font-medium text-ese-ink-navy mb-2">Configuration</h3>
              <div className="bg-ese-lang-50 p-4 rounded-lg">
                <pre className="text-sm overflow-auto">
                  {JSON.stringify(evaluationBridge.config, null, 2)}
                </pre>
              </div>
            </div>
          )}
          {evaluationBridge.mappings && (
            <div>
              <h3 className="font-medium text-ese-ink-navy mb-2">Field Mappings</h3>
              <div className="space-y-2">
                {Object.entries(evaluationBridge.mappings).map(([key, value]) => (
                  <div key={key} className="flex justify-between text-sm">
                    <span className="text-ese-ink-medium">{key}:</span>
                    <span className="text-ese-ink-navy font-medium">{value}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Sync Statistics */}
      {evaluationBridge.stats && (
        <div className="bg-white rounded-lg shadow-md p-6 border border-ese-ink-light">
          <h2 className="text-xl font-semibold text-ese-ink-navy mb-4">Sync Statistics</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <h3 className="text-sm font-medium text-ese-ink-medium mb-1">Staff Synced</h3>
              <p className="text-2xl font-bold text-ese-lang-900">
                {evaluationBridge.stats.staff_synced || 0}
              </p>
            </div>
            <div>
              <h3 className="text-sm font-medium text-ese-ink-medium mb-1">Evaluations Synced</h3>
              <p className="text-2xl font-bold text-ese-int-700">
                {evaluationBridge.stats.evaluations_synced || 0}
              </p>
            </div>
            <div>
              <h3 className="text-sm font-medium text-ese-ink-medium mb-1">Last Sync</h3>
              <p className="text-sm font-medium text-ese-mustard">
                {evaluationBridge.stats.last_sync
                  ? new Date(evaluationBridge.stats.last_sync).toLocaleString()
                  : 'Never'}
              </p>
            </div>
          </div>
        </div>
      )}
      </div>
    </ErrorBoundary>
  )
}

export default IntegrationStatus
