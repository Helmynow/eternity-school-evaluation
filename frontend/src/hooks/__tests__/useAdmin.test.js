import { renderHook, waitFor } from '@testing-library/react'
import { useAdmin } from '../useAdmin'
import { apiClient } from '../../lib/api'
import toast from 'react-hot-toast'

// Mock dependencies
jest.mock('../../lib/api', () => ({
  apiClient: {
    admin: {
      getDashboard: jest.fn(),
      getOverviewCards: jest.fn(),
      getRealTimeMetrics: jest.fn(),
      getIdentityAnalytics: jest.fn(),
    },
  },
}))

describe('useAdmin', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('fetchDashboard', () => {
    it('should fetch admin dashboard successfully', async () => {
      const mockDashboard = {
        total_surveys: 10,
        active_surveys: 5,
        total_responses: 100,
        action_items: [],
      }
      apiClient.admin.getDashboard.mockResolvedValue({ data: mockDashboard })

      const { result } = renderHook(() => useAdmin())

      await waitFor(async () => {
        await result.current.fetchDashboard('admin@example.com')
      })

      expect(result.current.dashboard).toEqual(mockDashboard)
      expect(apiClient.admin.getDashboard).toHaveBeenCalledWith('admin@example.com')
    })

    it('should handle fetch errors', async () => {
      const error = new Error('Unauthorized')
      apiClient.admin.getDashboard.mockRejectedValue(error)

      const { result } = renderHook(() => useAdmin())

      await expect(result.current.fetchDashboard('admin@example.com')).rejects.toThrow('Unauthorized')
      expect(toast.error).toHaveBeenCalledWith('Failed to load admin dashboard')
    })
  })

  describe('fetchOverviewCards', () => {
    it('should fetch overview cards successfully', async () => {
      const mockCards = {
        surveys: { count: 10, trend: 'up' },
        responses: { count: 100, trend: 'up' },
        users: { count: 50, trend: 'stable' },
      }
      apiClient.admin.getOverviewCards.mockResolvedValue({ data: mockCards })

      const { result } = renderHook(() => useAdmin())

      await waitFor(async () => {
        await result.current.fetchOverviewCards()
      })

      expect(result.current.overviewCards).toEqual(mockCards)
      expect(apiClient.admin.getOverviewCards).toHaveBeenCalled()
    })

    it('should handle fetch errors', async () => {
      const error = new Error('Network error')
      apiClient.admin.getOverviewCards.mockRejectedValue(error)

      const { result } = renderHook(() => useAdmin())

      await expect(result.current.fetchOverviewCards()).rejects.toThrow('Network error')
      expect(toast.error).toHaveBeenCalledWith('Failed to load overview cards')
    })
  })

  describe('fetchRealTimeMetrics', () => {
    it('should fetch real-time metrics successfully', async () => {
      const mockMetrics = {
        active_users: 25,
        api_requests_per_minute: 120,
        average_response_time: 150,
        feature_usage: {
          surveys: 80,
          evaluations: 60,
          reports: 40,
        },
      }
      apiClient.admin.getRealTimeMetrics.mockResolvedValue({ data: mockMetrics })

      const { result } = renderHook(() => useAdmin())

      await waitFor(async () => {
        await result.current.fetchRealTimeMetrics()
      })

      expect(result.current.realTimeMetrics).toEqual(mockMetrics)
      expect(apiClient.admin.getRealTimeMetrics).toHaveBeenCalled()
    })

    it('should handle fetch errors', async () => {
      const error = new Error('Service unavailable')
      apiClient.admin.getRealTimeMetrics.mockRejectedValue(error)

      const { result } = renderHook(() => useAdmin())

      await expect(result.current.fetchRealTimeMetrics()).rejects.toThrow('Service unavailable')
      expect(toast.error).toHaveBeenCalledWith('Failed to load real-time metrics')
    })
  })

  describe('fetchIdentityAnalytics', () => {
    it('should fetch identity analytics successfully', async () => {
      const mockAnalytics = {
        total_sessions: 500,
        mode_distribution: {
          anonymous: 200,
          conditional: 150,
          identified: 150,
        },
        reveal_methods: {
          full: 50,
          partial: 30,
          conditional: 20,
        },
      }
      apiClient.admin.getIdentityAnalytics.mockResolvedValue({ data: mockAnalytics })

      const { result } = renderHook(() => useAdmin())

      await waitFor(async () => {
        await result.current.fetchIdentityAnalytics()
      })

      expect(result.current.identityAnalytics).toEqual(mockAnalytics)
      expect(apiClient.admin.getIdentityAnalytics).toHaveBeenCalled()
    })

    it('should handle fetch errors', async () => {
      const error = new Error('Data unavailable')
      apiClient.admin.getIdentityAnalytics.mockRejectedValue(error)

      const { result } = renderHook(() => useAdmin())

      await expect(result.current.fetchIdentityAnalytics()).rejects.toThrow('Data unavailable')
      expect(toast.error).toHaveBeenCalledWith('Failed to load identity analytics')
    })
  })

  describe('loading state', () => {
    it('should set loading to true during fetch', async () => {
      let resolvePromise
      const promise = new Promise((resolve) => {
        resolvePromise = resolve
      })
      apiClient.admin.getDashboard.mockReturnValue(promise)

      const { result } = renderHook(() => useAdmin())

      const fetchPromise = result.current.fetchDashboard('admin@example.com')

      // Loading should be true during fetch
      expect(result.current.loading).toBe(true)

      resolvePromise({ data: {} })
      await fetchPromise

      // Loading should be false after fetch
      expect(result.current.loading).toBe(false)
    })

    it('should reset loading state on error', async () => {
      const error = new Error('Failed')
      apiClient.admin.getDashboard.mockRejectedValue(error)

      const { result } = renderHook(() => useAdmin())

      try {
        await result.current.fetchDashboard('admin@example.com')
      } catch (e) {
        // Expected error
      }

      // Loading should be false after error
      expect(result.current.loading).toBe(false)
    })
  })

  describe('initial state', () => {
    it('should initialize with null values', () => {
      const { result } = renderHook(() => useAdmin())

      expect(result.current.dashboard).toBeNull()
      expect(result.current.overviewCards).toBeNull()
      expect(result.current.realTimeMetrics).toBeNull()
      expect(result.current.identityAnalytics).toBeNull()
      expect(result.current.loading).toBe(false)
    })
  })
})
