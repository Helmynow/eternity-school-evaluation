import { useState, useCallback, useEffect } from 'react'
import { apiClient } from '../lib/api'
import { useAuth } from './useAuth'
import toast from 'react-hot-toast'

export const useNotifications = (autoFetch = true) => {
  const { user } = useAuth()
  const [notifications, setNotifications] = useState([])
  const [unreadCount, setUnreadCount] = useState(0)
  const [loading, setLoading] = useState(false)

  // Fetch all notifications
  const fetchNotifications = useCallback(async () => {
    if (!user?.email) return []
    setLoading(true)
    try {
      const response = await apiClient.notifications.getAll({
        user_email: user.email
      })
      setNotifications(response.data || [])
      return response.data
    } catch (error) {
      console.error('Failed to load notifications:', error)
      // Don't show toast for notifications - they might not exist
      return []
    } finally {
      setLoading(false)
    }
  }, [user])

  // Fetch unread count
  const fetchUnreadCount = useCallback(async () => {
    if (!user?.email) return 0
    try {
      const response = await apiClient.notifications.getUnreadCount({
        user_email: user.email
      })
      const count = response.data?.unread_count || 0
      setUnreadCount(count)
      return count
    } catch (error) {
      console.error('Failed to load unread count:', error)
      return 0
    }
  }, [user])

  // Mark notification as read
  const markAsRead = useCallback(async (id) => {
    if (!user?.email) return
    try {
      await apiClient.notifications.markRead(id, {
        user_email: user.email
      })
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, read: true } : n))
      )
      setUnreadCount((prev) => Math.max(0, prev - 1))
    } catch (error) {
      toast.error('Failed to mark notification as read')
    }
  }, [user])

  // Mark all as read
  const markAllAsRead = useCallback(async () => {
    if (!user?.email) return
    try {
      await apiClient.notifications.markAllRead({
        user_email: user.email
      })
      setNotifications((prev) => prev.map((n) => ({ ...n, read: true })))
      setUnreadCount(0)
      toast.success('All notifications marked as read')
    } catch (error) {
      toast.error('Failed to mark all notifications as read')
    }
  }, [user])

  // Mark multiple as read
  const markMultipleAsRead = useCallback(async (ids) => {
    if (!user?.email) return
    try {
      await apiClient.notifications.markMultipleRead(ids, {
        user_email: user.email
      })
      setNotifications((prev) =>
        prev.map((n) => (ids.includes(n.id) ? { ...n, read: true } : n))
      )
      setUnreadCount((prev) => Math.max(0, prev - ids.length))
    } catch (error) {
      toast.error('Failed to mark notifications as read')
    }
  }, [user])

  // Auto-fetch on mount
  useEffect(() => {
    if (autoFetch && user?.email) {
      fetchNotifications()
      fetchUnreadCount()
    }
  }, [autoFetch, user, fetchNotifications, fetchUnreadCount])

  return {
    notifications,
    unreadCount,
    loading,
    fetchNotifications,
    fetchUnreadCount,
    markAsRead,
    markAllAsRead,
    markMultipleAsRead,
  }
}
