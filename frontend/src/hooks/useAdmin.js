import { useState, useCallback } from 'react'
import { apiClient } from '../lib/api'
import { useAPI } from './useAPI'
import toast from 'react-hot-toast'

export const useAdmin = (adminId = null) => {
  const [dashboard, setDashboard] = useState(null)
  const [overviewCards, setOverviewCards] = useState(null)
  const [realTimeMetrics, setRealTimeMetrics] = useState(null)
  const [identityAnalytics, setIdentityAnalytics] = useState(null)
  const [loading, setLoading] = useState(false)

  // Fetch admin dashboard
  const fetchDashboard = useCallback(async (id) => {
    setLoading(true)
    try {
      const response = await apiClient.admin.getDashboard(id)
      setDashboard(response.data)
      return response.data
    } catch (error) {
      toast.error('Failed to load admin dashboard')
      throw error
    } finally {
      setLoading(false)
    }
  }, [])

  // Fetch overview cards
  const fetchOverviewCards = useCallback(async () => {
    setLoading(true)
    try {
      const response = await apiClient.admin.getOverviewCards()
      setOverviewCards(response.data)
      return response.data
    } catch (error) {
      toast.error('Failed to load overview cards')
      throw error
    } finally {
      setLoading(false)
    }
  }, [])

  // Fetch real-time metrics
  const fetchRealTimeMetrics = useCallback(async () => {
    setLoading(true)
    try {
      const response = await apiClient.admin.getRealTimeMetrics()
      setRealTimeMetrics(response.data)
      return response.data
    } catch (error) {
      toast.error('Failed to load real-time metrics')
      throw error
    } finally {
      setLoading(false)
    }
  }, [])

  // Fetch identity analytics
  const fetchIdentityAnalytics = useCallback(async () => {
    setLoading(true)
    try {
      const response = await apiClient.admin.getIdentityAnalytics()
      setIdentityAnalytics(response.data)
      return response.data
    } catch (error) {
      toast.error('Failed to load identity analytics')
      throw error
    } finally {
      setLoading(false)
    }
  }, [])

  return {
    dashboard,
    overviewCards,
    realTimeMetrics,
    identityAnalytics,
    loading,
    fetchDashboard,
    fetchOverviewCards,
    fetchRealTimeMetrics,
    fetchIdentityAnalytics,
  }
}
