import { useState, useEffect } from 'react'
import { useAuth } from '../../hooks/useAuth'
import { apiClient } from '../../lib/api'
import toast from 'react-hot-toast'

const History = () => {
  const { user, isCEO, isPNC } = useAuth()
  const [auditLogs, setAuditLogs] = useState([])
  const [loading, setLoading] = useState(true)
  const [filters, setFilters] = useState({
    action_type: '',
    entity_type: '',
    user_email: '',
    date_from: '',
    date_to: ''
  })

  useEffect(() => {
    fetchAuditLogs()
  }, [filters])

  const fetchAuditLogs = async () => {
    try {
      const params = {}
      if (filters.action_type) params.action_type = filters.action_type
      if (filters.entity_type) params.entity_type = filters.entity_type
      if (filters.user_email) params.user_email = filters.user_email
      if (filters.date_from) params.date_from = filters.date_from
      if (filters.date_to) params.date_to = filters.date_to

      // Limit to user's own actions unless CEO/PNC
      if (!isCEO && !isPNC) {
        params.user_email = user?.email
      }

      const response = await apiClient.auditLogs.getAll(params)
      setAuditLogs(response.data || [])
    } catch (error) {
      toast.error('Failed to load history')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-ese-lang-900"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-heading font-bold text-ese-lang-900">History & Audit Log</h1>
        <p className="text-ese-ink-blue mt-1">View system activity and audit trail</p>
      </div>

      {/* Filters */}
      <div className="ese-card">
        <h2 className="text-xl font-heading font-semibold text-ese-ink-navy mb-4">Filters</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-ese-ink-navy mb-1">Action Type</label>
            <select
              value={filters.action_type}
              onChange={(e) => setFilters({ ...filters, action_type: e.target.value })}
              className="w-full px-4 py-2 border border-ese-accent-beige rounded-lg focus:outline-none focus:ring-2 focus:ring-ese-lang-900"
            >
              <option value="">All</option>
              <option value="create">Create</option>
              <option value="update">Update</option>
              <option value="delete">Delete</option>
              <option value="submit">Submit</option>
              <option value="approve">Approve</option>
              <option value="reject">Reject</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-ese-ink-navy mb-1">Entity Type</label>
            <select
              value={filters.entity_type}
              onChange={(e) => setFilters({ ...filters, entity_type: e.target.value })}
              className="w-full px-4 py-2 border border-ese-accent-beige rounded-lg focus:outline-none focus:ring-2 focus:ring-ese-lang-900"
            >
              <option value="">All</option>
              <option value="person">Person</option>
              <option value="evaluation">Evaluation</option>
              <option value="eom_nominee">EOM Nominee</option>
              <option value="cycle">Cycle</option>
            </select>
          </div>

          {(isCEO || isPNC) && (
            <div>
              <label className="block text-sm font-medium text-ese-ink-navy mb-1">User Email</label>
              <input
                type="email"
                value={filters.user_email}
                onChange={(e) => setFilters({ ...filters, user_email: e.target.value })}
                className="w-full px-4 py-2 border border-ese-accent-beige rounded-lg focus:outline-none focus:ring-2 focus:ring-ese-lang-900"
                placeholder="Filter by user..."
              />
            </div>
          )}
        </div>

        <div className="grid grid-cols-2 gap-4 mt-4">
          <div>
            <label className="block text-sm font-medium text-ese-ink-navy mb-1">From Date</label>
            <input
              type="date"
              value={filters.date_from}
              onChange={(e) => setFilters({ ...filters, date_from: e.target.value })}
              className="w-full px-4 py-2 border border-ese-accent-beige rounded-lg focus:outline-none focus:ring-2 focus:ring-ese-lang-900"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-ese-ink-navy mb-1">To Date</label>
            <input
              type="date"
              value={filters.date_to}
              onChange={(e) => setFilters({ ...filters, date_to: e.target.value })}
              className="w-full px-4 py-2 border border-ese-accent-beige rounded-lg focus:outline-none focus:ring-2 focus:ring-ese-lang-900"
            />
          </div>
        </div>
      </div>

      {/* Audit Logs */}
      <div className="ese-card">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-ese-accent-beige">
                <th className="text-left py-3 px-4 font-semibold text-ese-ink-navy">Date</th>
                <th className="text-left py-3 px-4 font-semibold text-ese-ink-navy">Action</th>
                <th className="text-left py-3 px-4 font-semibold text-ese-ink-navy">Entity</th>
                <th className="text-left py-3 px-4 font-semibold text-ese-ink-navy">User</th>
                <th className="text-left py-3 px-4 font-semibold text-ese-ink-navy">Description</th>
              </tr>
            </thead>
            <tbody>
              {auditLogs.map((log) => (
                <tr key={log.id} className="border-b border-ese-accent-beige hover:bg-ese-ink-offwhite">
                  <td className="py-3 px-4 text-sm">
                    {new Date(log.created_at).toLocaleString()}
                  </td>
                  <td className="py-3 px-4">
                    <span className="px-2 py-1 rounded-full text-xs bg-ese-accent-beige text-ese-ink-navy">
                      {log.action_type}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-sm">{log.entity_type}</td>
                  <td className="py-3 px-4 text-sm">{log.user_email}</td>
                  <td className="py-3 px-4 text-sm text-ese-ink-blue">{log.description || 'N/A'}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {auditLogs.length === 0 && (
            <div className="text-center py-12 text-ese-ink-blue">
              No audit logs found.
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default History
