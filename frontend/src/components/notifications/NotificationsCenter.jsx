import { useEffect } from 'react'
import { useNotifications } from '../../hooks/useNotifications'

const NotificationsCenter = () => {
  const {
    notifications,
    unreadCount,
    loading,
    markAsRead,
    markAllAsRead,
    fetchNotifications
  } = useNotifications()

  useEffect(() => {
    // Poll for new notifications every 30 seconds
    const interval = setInterval(() => {
      fetchNotifications()
    }, 30000)
    return () => clearInterval(interval)
  }, [fetchNotifications])

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-ese-lang-900"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-heading font-bold text-ese-lang-900">Notifications</h1>
          <p className="text-ese-ink-blue mt-1">
            {unreadCount > 0 ? `${unreadCount} unread notification${unreadCount > 1 ? 's' : ''}` : 'All caught up!'}
          </p>
        </div>
        {unreadCount > 0 && (
          <button
            onClick={markAllAsRead}
            className="ese-button-secondary"
          >
            Mark All as Read
          </button>
        )}
      </div>

      <div className="ese-card">
        <div className="space-y-3">
          {notifications.length === 0 ? (
            <div className="text-center py-12 text-ese-ink-blue">
              No notifications yet.
            </div>
          ) : (
            notifications.map((notification) => (
              <div
                key={notification.id}
                className={`p-4 rounded-lg border-2 transition-all cursor-pointer ${
                  notification.read
                    ? 'border-ese-accent-beige bg-white'
                    : 'border-ese-lang-900 bg-ese-lang-50'
                }`}
                onClick={() => {
                  if (!notification.read) markAsRead(notification.id)
                  if (notification.action_url) {
                    window.location.href = notification.action_url
                  }
                }}
              >
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <h3 className={`font-semibold ${notification.read ? 'text-ese-ink-navy' : 'text-ese-lang-900'}`}>
                        {notification.title}
                      </h3>
                      {!notification.read && (
                        <span className="w-2 h-2 bg-ese-lang-900 rounded-full"></span>
                      )}
                    </div>
                    <p className="text-sm text-ese-ink-blue">{notification.message}</p>
                    <p className="text-xs text-ese-ink-blue mt-2">
                      {new Date(notification.created_at).toLocaleString()}
                    </p>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  )
}

export default NotificationsCenter
