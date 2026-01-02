import { useState, useEffect } from 'react'
import { apiClient } from '../../lib/api'
import { useAuth } from '../../hooks/useAuth'
import toast from 'react-hot-toast'
import ErrorBoundary from '../common/ErrorBoundary'
import LoadingSkeleton from '../common/LoadingSkeleton'
import PropTypes from 'prop-types'

const ActionItems = ({ items }) => {
  const { user } = useAuth()
  const [actionItems, setActionItems] = useState(() => (Array.isArray(items) ? items : []))
  const [loading, setLoading] = useState(() => !Array.isArray(items))

  useEffect(() => {
    // If items are provided (e.g., already fetched by parent), use them and skip refetch.
    if (Array.isArray(items)) {
      setActionItems(items)
      setLoading(false)
      return
    }

    loadActionItems()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user, items])

  const loadActionItems = async () => {
    setLoading(true)
    try {
      // Try to get action items from admin dashboard first
      let items = []
      try {
        const dashboardRes = await apiClient.admin.getDashboard()
        if (dashboardRes.data?.action_items) {
          items = dashboardRes.data.action_items
        }
      } catch (err) {
        // Fallback to manual aggregation if dashboard fails
        console.log('Dashboard action items not available, using fallback')
      }

      // If no items from dashboard, fallback to manual aggregation
      if (items.length === 0) {
        // Get pending objections as action items
        const objectionsRes = await apiClient.objections.getAll()
        const pendingObjections = (objectionsRes.data || []).filter(
          (o) => o.status === 'pending'
        )

        // Get unread notifications as action items
        const notificationsRes = await apiClient.notifications.getAll()
        const unreadNotifications = (notificationsRes.data || []).filter((n) => !n.read)

        // Combine into action items
        items = [
          ...pendingObjections.map((o) => ({
            id: `objection-${o.id}`,
            type: 'objection',
            title: `Objection: ${o.title || o.reason?.substring(0, 50)}`,
            description: o.description || o.reason,
            priority: 'high',
            dueDate: null,
            link: `/admin/objections`,
          })),
          ...unreadNotifications
            .slice(0, 5)
            .map((n) => ({
              id: `notification-${n.id}`,
              type: 'notification',
              title: n.title,
              description: n.message,
              priority: n.priority || 'normal',
              dueDate: null,
              link: n.link || '/notifications',
            })),
        ]
      }

      setActionItems(items)
    } catch (error) {
      console.error('Error loading action items:', error)
      setActionItems([])
    } finally {
      setLoading(false)
    }
  }

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'urgent':
      case 'high':
        return 'bg-red-100 text-red-800 border-red-300'
      case 'normal':
        return 'bg-blue-100 text-blue-800 border-blue-300'
      case 'low':
        return 'bg-gray-100 text-gray-800 border-gray-300'
      default:
        return 'bg-gray-100 text-gray-800 border-gray-300'
    }
  }

  const handleComplete = async (item) => {
    try {
      if (item.type === 'notification') {
        const notificationId = item.id.replace('notification-', '')
        await apiClient.notifications.markRead(parseInt(notificationId, 10))
      } else if (item.type === 'objection') {
        // Objections are handled separately, just remove from view
      }
      // Remove from list
      setActionItems((prev) => prev.filter((i) => i.id !== item.id))
      toast.success('Action item completed')
    } catch (error) {
      toast.error('Failed to complete action item')
      console.error('Error completing action item:', error)
    }
  }

  if (loading) {
    return <LoadingSkeleton type="list" count={3} />
  }

  return (
    <ErrorBoundary>
      <div className="space-y-4">
      {actionItems.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-lg shadow-md border border-ese-ink-light">
          <p className="text-ese-ink-medium">No action items at this time</p>
        </div>
      ) : (
        actionItems.map((item) => (
          <div
            key={item.id}
            className={`p-6 rounded-lg border-2 ${getPriorityColor(item.priority)}`}
          >
            <div className="flex justify-between items-start">
              <div className="flex-1">
                <div className="flex items-center space-x-2 mb-2">
                  <span className="text-xs px-2 py-1 rounded-full bg-white">
                    {item.type}
                  </span>
                  <span className="text-xs px-2 py-1 rounded-full bg-white">
                    {item.priority}
                  </span>
                </div>
                <h3 className="text-lg font-semibold mb-2">{item.title}</h3>
                <p className="text-sm mb-3">{item.description}</p>
                {item.link && (
                  <a
                    href={item.link}
                    className="text-sm text-ese-lang-900 hover:underline"
                  >
                    View Details →
                  </a>
                )}
              </div>
              <button
                onClick={() => handleComplete(item)}
                className="ml-4 px-4 py-2 bg-white rounded-lg hover:bg-gray-50 transition-colors"
              >
                Complete
              </button>
            </div>
          </div>
        ))
      )}
      </div>
    </ErrorBoundary>
  )
}

ActionItems.propTypes = {
  items: PropTypes.array,
}

ActionItems.defaultProps = {
  items: undefined,
}

export default ActionItems
