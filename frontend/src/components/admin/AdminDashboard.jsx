import { useState, useEffect } from 'react'
import { useAuth } from '../../hooks/useAuth'
import { useAdmin } from '../../hooks/useAdmin'
import PropTypes from 'prop-types'
import SystemMetrics from './SystemMetrics'
import IdentityAnalytics from './IdentityAnalytics'
import BiasAlerts from './BiasAlerts'
import ActionItems from './ActionItems'
import toast from 'react-hot-toast'
import ErrorBoundary from '../common/ErrorBoundary'
import LoadingSkeleton, { LoadingSpinner } from '../common/LoadingSkeleton'

const AdminDashboard = () => {
  const { user, isCEO, isPNC } = useAuth()
  const {
    dashboard,
    overviewCards,
    realTimeMetrics,
    identityAnalytics,
    loading,
    fetchDashboard,
    fetchOverviewCards,
    fetchRealTimeMetrics,
    fetchIdentityAnalytics,
  } = useAdmin(user?.email)
  const [activeTab, setActiveTab] = useState('overview')

  useEffect(() => {
    if (isCEO || isPNC) {
      loadDashboardData()
    }
  }, [isCEO, isPNC, user])

  const loadDashboardData = async () => {
    try {
      await Promise.all([
        fetchDashboard(user?.email),
        fetchOverviewCards(),
        fetchRealTimeMetrics(),
        fetchIdentityAnalytics(),
      ])
    } catch (error) {
      console.error('Error loading dashboard data:', error)
    }
  }

  if (!isCEO && !isPNC) {
    return (
      <div className="p-6 text-center">
        <p className="text-ese-ink-medium text-lg">Access Denied</p>
        <p className="text-ese-ink-light mt-2">Admin access required</p>
      </div>
    )
  }

  const tabs = [
    { id: 'overview', label: 'Overview', icon: '/assets/icons/Analytics.png' },
    { id: 'metrics', label: 'System Metrics', icon: '/assets/icons/metrics.png' },
    { id: 'identity', label: 'Identity Analytics', icon: '/assets/icons/identity.png' },
    { id: 'bias', label: 'Bias Alerts', icon: '/assets/icons/warning_alert.png' },
    { id: 'actions', label: 'Action Items', icon: '/assets/icons/success.png' },
  ]

  if (loading && !dashboard) {
    return (
      <div className="p-6">
        <span className="sr-only">Loading...</span>
        <LoadingSkeleton type="dashboard" count={1} />
      </div>
    )
  }

  return (
    <ErrorBoundary>
      <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-ese-ink-navy">Admin Dashboard</h1>
        <p className="text-ese-ink-medium mt-1">System overview and management</p>
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
        {activeTab === 'overview' && (
          <div className="space-y-6">
            {/* Overview Cards */}
            {overviewCards && (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {overviewCards.map((card, index) => (
                  <div
                    key={index}
                    className="bg-white rounded-lg shadow-md p-6 border border-ese-ink-light"
                  >
                    <h3 className="text-sm font-medium text-ese-ink-medium mb-1">
                      {card.title}
                    </h3>
                    <p className="text-3xl font-bold text-ese-lang-900">{card.value}</p>
                    {card.change && (
                      <p
                        className={`text-sm mt-2 ${
                          card.change > 0 ? 'text-green-600' : 'text-red-600'
                        }`}
                      >
                        {card.change > 0 ? '+' : ''}
                        {card.change}% from last period
                      </p>
                    )}
                  </div>
                ))}
              </div>
            )}

            {/* Dashboard Summary */}
            {dashboard && (
              <div className="bg-white rounded-lg shadow-md p-6 border border-ese-ink-light">
                <h2 className="text-xl font-semibold text-ese-ink-navy mb-4">
                  Dashboard Summary
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <h3 className="font-medium text-ese-ink-navy mb-2">System Status</h3>
                    <p className="text-ese-ink-medium">
                      {dashboard.system_status || 'Operational'}
                    </p>
                  </div>
                  <div>
                    <h3 className="font-medium text-ese-ink-navy mb-2">Last Updated</h3>
                    <p className="text-ese-ink-medium">
                      {dashboard.last_updated
                        ? new Date(dashboard.last_updated).toLocaleString()
                        : 'N/A'}
                    </p>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'metrics' && <SystemMetrics metrics={realTimeMetrics} loading={loading} />}
        {activeTab === 'identity' && <IdentityAnalytics analytics={identityAnalytics} loading={loading} />}
        {activeTab === 'bias' && <BiasAlerts />}
        {activeTab === 'actions' && <ActionItems items={dashboard?.action_items} />}
      </div>
      </div>
    </ErrorBoundary>
  )
}

export default AdminDashboard
