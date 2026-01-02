import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import PropTypes from 'prop-types'
import ErrorBoundary from '../common/ErrorBoundary'
import LoadingSkeleton from '../common/LoadingSkeleton'

const IdentityAnalytics = ({ analytics, loading = false }) => {
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

  if (!analytics) {
    return (
      <ErrorBoundary>
        <div className="text-center py-12">
          <p className="text-ese-ink-medium">No identity analytics data available</p>
        </div>
      </ErrorBoundary>
    )
  }

  const COLORS = ['#094773', '#2C5B4C', '#E4A740', '#C88167', '#2D7EA1']

  return (
    <ErrorBoundary>
      <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white rounded-lg shadow-md p-6 border border-ese-ink-light">
          <h3 className="text-sm font-medium text-ese-ink-medium mb-1">Total Sessions</h3>
          <p className="text-3xl font-bold text-ese-lang-900">
            {analytics.total_sessions || 0}
          </p>
        </div>
        <div className="bg-white rounded-lg shadow-md p-6 border border-ese-ink-light">
          <h3 className="text-sm font-medium text-ese-ink-medium mb-1">Mode Distribution</h3>
          <p className="text-3xl font-bold text-ese-int-700">
            {analytics.mode_count || 0}
          </p>
        </div>
        <div className="bg-white rounded-lg shadow-md p-6 border border-ese-ink-light">
          <h3 className="text-sm font-medium text-ese-ink-medium mb-1">Reveals Processed</h3>
          <p className="text-3xl font-bold text-ese-mustard">
            {analytics.reveals_processed || 0}
          </p>
        </div>
      </div>

      {/* Mode Distribution Chart */}
      {analytics.mode_distribution && (
        <div className="bg-white rounded-lg shadow-md p-6 border border-ese-ink-light">
          <h2 className="text-xl font-semibold text-ese-ink-navy mb-4">Identity Mode Distribution</h2>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={analytics.mode_distribution}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {analytics.mode_distribution.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Reveal Methods Chart */}
      {analytics.reveal_methods && (
        <div className="bg-white rounded-lg shadow-md p-6 border border-ese-ink-light">
          <h2 className="text-xl font-semibold text-ese-ink-navy mb-4">Reveal Methods</h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={analytics.reveal_methods}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="method" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="count" fill="#094773" name="Count" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
      </div>
    </ErrorBoundary>
  )
}

IdentityAnalytics.propTypes = {
  analytics: PropTypes.shape({
    total_sessions: PropTypes.number,
    mode_distribution: PropTypes.object,
    reveal_methods: PropTypes.object,
  }),
  loading: PropTypes.bool,
}

IdentityAnalytics.defaultProps = {
  analytics: null,
  loading: false,
}

export default IdentityAnalytics
