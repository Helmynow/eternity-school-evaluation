import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import ErrorBoundary from '../common/ErrorBoundary'
import LoadingSkeleton from '../common/LoadingSkeleton'

const SystemMetrics = ({ metrics, loading = false }) => {
  if (loading) {
    return (
      <ErrorBoundary>
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <LoadingSkeleton type="card" count={3} />
          </div>
          <LoadingSkeleton type="card" count={2} />
        </div>
      </ErrorBoundary>
    )
  }

  if (!metrics) {
    return (
      <ErrorBoundary>
        <div className="text-center py-12">
          <p className="text-ese-ink-medium">No metrics data available</p>
        </div>
      </ErrorBoundary>
    )
  }

  const COLORS = {
    lang: '#094773',
    int: '#2C5B4C',
    mustard: '#E4A740',
    terracotta: '#C88167',
  }

  return (
    <ErrorBoundary>
      <div className="space-y-6">
      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white rounded-lg shadow-md p-6 border border-ese-ink-light">
          <h3 className="text-sm font-medium text-ese-ink-medium mb-1">Active Users</h3>
          <p className="text-3xl font-bold text-ese-lang-900">
            {metrics.active_users || 0}
          </p>
        </div>
        <div className="bg-white rounded-lg shadow-md p-6 border border-ese-ink-light">
          <h3 className="text-sm font-medium text-ese-ink-medium mb-1">API Requests</h3>
          <p className="text-3xl font-bold text-ese-int-700">
            {metrics.api_requests || 0}
          </p>
        </div>
        <div className="bg-white rounded-lg shadow-md p-6 border border-ese-ink-light">
          <h3 className="text-sm font-medium text-ese-ink-medium mb-1">Response Time</h3>
          <p className="text-3xl font-bold text-ese-mustard">
            {metrics.avg_response_time ? `${metrics.avg_response_time}ms` : 'N/A'}
          </p>
        </div>
      </div>

      {/* Charts */}
      {metrics.usage_trends && (
        <div className="bg-white rounded-lg shadow-md p-6 border border-ese-ink-light">
          <h2 className="text-xl font-semibold text-ese-ink-navy mb-4">Usage Trends</h2>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={metrics.usage_trends}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line
                type="monotone"
                dataKey="users"
                stroke={COLORS.lang}
                name="Active Users"
              />
              <Line
                type="monotone"
                dataKey="requests"
                stroke={COLORS.int}
                name="API Requests"
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {metrics.feature_usage && (
        <div className="bg-white rounded-lg shadow-md p-6 border border-ese-ink-light">
          <h2 className="text-xl font-semibold text-ese-ink-navy mb-4">Feature Usage</h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={metrics.feature_usage}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="feature" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="count" fill={COLORS.mustard} name="Usage Count" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
      </div>
    </ErrorBoundary>
  )
}

SystemMetrics.propTypes = {
  metrics: PropTypes.shape({
    active_users: PropTypes.number,
    api_requests_per_minute: PropTypes.number,
    average_response_time: PropTypes.number,
    usage_trends: PropTypes.object,
    feature_usage: PropTypes.object,
  }),
  loading: PropTypes.bool,
}

SystemMetrics.defaultProps = {
  metrics: null,
  loading: false,
}

export default SystemMetrics
