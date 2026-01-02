import { useState, useEffect } from 'react'
import { apiClient } from '../../lib/api'
import { useAuth } from '../../hooks/useAuth'

const AnnouncementBanner = () => {
  const { user } = useAuth()
  const [announcements, setAnnouncements] = useState([])
  const [dismissed, setDismissed] = useState(new Set())

  useEffect(() => {
    loadAnnouncements()
    // Reload announcements every 5 minutes
    const interval = setInterval(loadAnnouncements, 5 * 60 * 1000)
    return () => clearInterval(interval)
  }, [user])

  const loadAnnouncements = async () => {
    if (!user?.email) return

    try {
      const response = await apiClient.announcements.getAll({
        is_active: true,
      })
      
      const activeAnnouncements = (response.data?.data || []).filter(
        a => !dismissed.has(a.id)
      )
      setAnnouncements(activeAnnouncements)
    } catch (error) {
      console.error('Failed to load announcements:', error)
    }
  }

  const handleDismiss = (id) => {
    setDismissed(prev => new Set([...prev, id]))
    setAnnouncements(prev => prev.filter(a => a.id !== id))
  }

  const getPriorityStyles = (priority) => {
    const styles = {
      urgent: 'bg-red-50 border-red-300',
      high: 'bg-orange-50 border-orange-300',
      normal: 'bg-blue-50 border-blue-300',
      low: 'bg-gray-50 border-gray-300'
    }
    return styles[priority] || styles.normal
  }

  if (announcements.length === 0) return null

  return (
    <div className="space-y-2 mb-4">
      {announcements.map((announcement) => (
        <div
          key={announcement.id}
          className={`p-4 rounded-lg border-2 ${getPriorityStyles(announcement.priority)}`}
        >
          <div className="flex justify-between items-start">
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-1">
                <h4 className="font-semibold text-ese-ink-navy">
                  {announcement.title}
                </h4>
                {announcement.priority === 'urgent' && (
                  <span className="px-2 py-1 rounded-full text-xs bg-red-200 text-red-800 font-medium">
                    Urgent
                  </span>
                )}
              </div>
              <p className="text-sm text-ese-ink-blue whitespace-pre-wrap">
                {announcement.content}
              </p>
            </div>
            <button
              onClick={() => handleDismiss(announcement.id)}
              className="ml-4 text-ese-ink-medium hover:text-ese-ink-navy"
              aria-label="Dismiss announcement"
            >
              <img src="/assets/icons/close.png" alt="" className="w-5 h-5" />
            </button>
          </div>
        </div>
      ))}
    </div>
  )
}

export default AnnouncementBanner
