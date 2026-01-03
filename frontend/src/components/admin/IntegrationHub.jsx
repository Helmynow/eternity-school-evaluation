import { useState, useEffect } from 'react'
import { useAuth } from '../../hooks/useAuth'
import { useIntegration } from '../../hooks/useIntegration'
import IntegrationStatus from './IntegrationStatus'
import SyncHistory from './SyncHistory'
import toast from 'react-hot-toast'
import ErrorBoundary from '../common/ErrorBoundary'

const IntegrationHub = () => {
  const { isCEO } = useAuth()
  const {
    evaluationBridge,
    loading,
    fetchEvaluationBridge,
    setupHR,
    syncStaff,
    syncEvaluation,
  } = useIntegration()
  const [activeTab, setActiveTab] = useState('status')
  const [hrConfig, setHrConfig] = useState({
    hr_system_url: '',
    api_key: '',
    real_time_sync: false,
    webhook_url: '',
    ip_whitelist: [],
  })

  useEffect(() => {
    if (isCEO) {
      loadIntegrationData()
    }
  }, [isCEO])

  const loadIntegrationData = async () => {
    try {
      await fetchEvaluationBridge()
    } catch (error) {
      console.error('Error loading integration data:', error)
    }
  }

  const handleSetupHR = async (e) => {
    e.preventDefault()
    try {
      await setupHR.mutate(hrConfig)
      toast.success('HR integration configured successfully')
      setHrConfig({
        hr_system_url: '',
        api_key: '',
        real_time_sync: false,
        webhook_url: '',
        ip_whitelist: [],
      })
      await fetchEvaluationBridge()
    } catch (error) {
      toast.error('Failed to setup HR integration')
      console.error('Error setting up HR integration:', error)
    }
  }

  const handleSyncStaff = async () => {
    try {
      await syncStaff.mutate()
      toast.success('Staff sync completed')
    } catch (error) {
      toast.error('Failed to sync staff')
      console.error('Error syncing staff:', error)
    }
  }

  const handleSyncEvaluation = async () => {
    try {
      await syncEvaluation.mutate()
      toast.success('Evaluation sync completed')
    } catch (error) {
      toast.error('Failed to sync evaluation')
      console.error('Error syncing evaluation:', error)
    }
  }

  if (!isCEO) {
    return (
      <div className="p-6 text-center">
        <p className="text-ese-ink-medium text-lg">Access Denied</p>
        <p className="text-ese-ink-light mt-2">CEO access required</p>
      </div>
    )
  }

  const tabs = [
    { id: 'status', label: 'Integration Status', icon: '/assets/icons/analytics.svg' },
    { id: 'setup', label: 'HR Setup', icon: '/assets/icons/refresh.svg' },
    { id: 'sync', label: 'Sync History', icon: '/assets/icons/refresh.svg' },
  ]

  return (
    <ErrorBoundary>
      <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-ese-ink-navy">Integration Hub</h1>
        <p className="text-ese-ink-medium mt-1">HR system integration and data synchronization</p>
      </div>

      {/* Tab Navigation */}
      <div className="flex space-x-2 border-b border-ese-ink-light overflow-x-auto whitespace-nowrap">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`shrink-0 px-4 py-2 font-medium transition-colors flex items-center space-x-2 ${
              activeTab === tab.id
                ? 'border-b-2 border-ese-lang-900 text-ese-lang-900'
                : 'text-ese-ink-medium hover:text-ese-lang-900'
            }`}
          >
            <img src={tab.icon} alt={tab.label} className="w-5 h-5" onError={(e) => { e.target.style.display = 'none'; e.target.parentElement.insertAdjacentHTML('afterbegin', '<span>📊</span>') }} />
            <span>{tab.label}</span>
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div>
        {activeTab === 'status' && (
          <IntegrationStatus evaluationBridge={evaluationBridge} loading={loading} />
        )}

        {activeTab === 'setup' && (
          <div className="bg-white rounded-lg shadow-md p-6 border border-ese-ink-light">
            <h2 className="text-xl font-semibold text-ese-ink-navy mb-4">HR System Setup</h2>
            <form onSubmit={handleSetupHR} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-ese-ink-navy mb-1">
                  HR System URL
                </label>
                <input
                  type="url"
                  value={hrConfig.hr_system_url}
                  onChange={(e) =>
                    setHrConfig({ ...hrConfig, hr_system_url: e.target.value })
                  }
                  className="w-full px-4 py-2 border border-ese-ink-light rounded-lg focus:outline-none focus:ring-2 focus:ring-ese-lang-700"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-ese-ink-navy mb-1">
                  API Key
                </label>
                <input
                  type="password"
                  value={hrConfig.api_key}
                  onChange={(e) =>
                    setHrConfig({ ...hrConfig, api_key: e.target.value })
                  }
                  className="w-full px-4 py-2 border border-ese-ink-light rounded-lg focus:outline-none focus:ring-2 focus:ring-ese-lang-700"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-ese-ink-navy mb-1">
                  Webhook URL
                </label>
                <input
                  type="url"
                  value={hrConfig.webhook_url}
                  onChange={(e) =>
                    setHrConfig({ ...hrConfig, webhook_url: e.target.value })
                  }
                  className="w-full px-4 py-2 border border-ese-ink-light rounded-lg focus:outline-none focus:ring-2 focus:ring-ese-lang-700"
                />
              </div>

              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="real_time_sync"
                  checked={hrConfig.real_time_sync}
                  onChange={(e) =>
                    setHrConfig({ ...hrConfig, real_time_sync: e.target.checked })
                  }
                  className="mr-2"
                />
                <label htmlFor="real_time_sync" className="text-sm text-ese-ink-navy">
                  Enable Real-Time Sync
                </label>
              </div>

              <div className="flex space-x-4">
                <button
                  type="submit"
                  disabled={setupHR.loading}
                  className="px-6 py-2 bg-ese-lang-900 text-white rounded-lg hover:bg-ese-lang-800 disabled:opacity-50"
                >
                  {setupHR.loading ? 'Setting up...' : 'Setup Integration'}
                </button>
              </div>
            </form>
          </div>
        )}

        {activeTab === 'sync' && (
          <div className="space-y-4">
            <div className="bg-white rounded-lg shadow-md p-6 border border-ese-ink-light">
              <h2 className="text-xl font-semibold text-ese-ink-navy mb-4">Manual Sync</h2>
              <div className="flex space-x-4">
                <button
                  onClick={handleSyncStaff}
                  disabled={syncStaff.loading}
                  className="px-6 py-2 bg-ese-lang-900 text-white rounded-lg hover:bg-ese-lang-800 disabled:opacity-50"
                >
                  {syncStaff.loading ? 'Syncing...' : 'Sync Staff'}
                </button>
                <button
                  onClick={handleSyncEvaluation}
                  disabled={syncEvaluation.loading}
                  className="px-6 py-2 bg-ese-int-700 text-white rounded-lg hover:bg-ese-int-800 disabled:opacity-50"
                >
                  {syncEvaluation.loading ? 'Syncing...' : 'Sync Evaluation'}
                </button>
              </div>
            </div>
            <SyncHistory />
          </div>
        )}
      </div>
      </div>
    </ErrorBoundary>
  )
}

export default IntegrationHub
