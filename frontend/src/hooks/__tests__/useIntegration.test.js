import { renderHook, waitFor } from '@testing-library/react'
import { useIntegration } from '../useIntegration'
import { apiClient } from '../../lib/api'
import toast from 'react-hot-toast'

// Mock dependencies
jest.mock('../../lib/api', () => ({
  apiClient: {
    integration: {
      setupHR: jest.fn(),
      getEvaluationBridge: jest.fn(),
      syncStaff: jest.fn(),
      syncEvaluation: jest.fn(),
    },
  },
}))

describe('useIntegration', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('fetchEvaluationBridge', () => {
    it('should fetch evaluation bridge successfully', async () => {
      const mockBridge = {
        connected: true,
        hr_system_url: 'https://hr.example.com',
        last_sync: '2024-01-01T00:00:00Z',
        field_mappings: {
          email: 'email',
          name: 'full_name',
        },
      }
      apiClient.integration.getEvaluationBridge.mockResolvedValue({ data: mockBridge })

      const { result } = renderHook(() => useIntegration())

      await waitFor(async () => {
        await result.current.fetchEvaluationBridge()
      })

      expect(result.current.evaluationBridge).toEqual(mockBridge)
      expect(apiClient.integration.getEvaluationBridge).toHaveBeenCalled()
    })

    it('should handle fetch errors', async () => {
      const error = new Error('Connection failed')
      apiClient.integration.getEvaluationBridge.mockRejectedValue(error)

      const { result } = renderHook(() => useIntegration())

      await expect(result.current.fetchEvaluationBridge()).rejects.toThrow('Connection failed')
      expect(toast.error).toHaveBeenCalledWith('Failed to load evaluation bridge')
    })

    it('should handle disconnected state', async () => {
      const mockBridge = {
        connected: false,
        hr_system_url: null,
        last_sync: null,
      }
      apiClient.integration.getEvaluationBridge.mockResolvedValue({ data: mockBridge })

      const { result } = renderHook(() => useIntegration())

      await waitFor(async () => {
        await result.current.fetchEvaluationBridge()
      })

      expect(result.current.evaluationBridge.connected).toBe(false)
    })
  })

  describe('setupHR', () => {
    it('should setup HR integration successfully', async () => {
      const config = {
        hr_system_url: 'https://hr.example.com',
        api_key: 'test-key',
        real_time_sync: true,
      }
      const mockResponse = {
        connected: true,
        hr_system_url: config.hr_system_url,
        message: 'Integration setup successfully',
      }
      apiClient.integration.setupHR.mockResolvedValue({ data: mockResponse })

      const { result } = renderHook(() => useIntegration())

      await waitFor(async () => {
        await result.current.setupHR.mutate(config)
      })

      expect(apiClient.integration.setupHR).toHaveBeenCalledWith(config)
      expect(toast.success).toHaveBeenCalledWith('HR integration setup successfully')
    })

    it('should handle setup errors', async () => {
      const config = { hr_system_url: 'invalid-url' }
      const error = new Error('Invalid configuration')
      apiClient.integration.setupHR.mockRejectedValue(error)

      const { result } = renderHook(() => useIntegration())

      await expect(result.current.setupHR.mutate(config)).rejects.toThrow('Invalid configuration')
    })
  })

  describe('syncStaff', () => {
    it('should sync staff successfully', async () => {
      const mockResponse = {
        synced_count: 50,
        updated_count: 10,
        new_count: 5,
        message: 'Staff sync completed',
      }
      apiClient.integration.syncStaff.mockResolvedValue({ data: mockResponse })

      const { result } = renderHook(() => useIntegration())

      await waitFor(async () => {
        await result.current.syncStaff.mutate()
      })

      expect(apiClient.integration.syncStaff).toHaveBeenCalled()
      expect(toast.success).toHaveBeenCalledWith('Staff sync completed')
    })

    it('should handle sync errors', async () => {
      const error = new Error('Sync failed')
      apiClient.integration.syncStaff.mockRejectedValue(error)

      const { result } = renderHook(() => useIntegration())

      await expect(result.current.syncStaff.mutate()).rejects.toThrow('Sync failed')
    })
  })

  describe('syncEvaluation', () => {
    it('should sync evaluation successfully', async () => {
      const mockResponse = {
        synced_count: 20,
        updated_count: 5,
        new_count: 2,
        message: 'Evaluation sync completed',
      }
      apiClient.integration.syncEvaluation.mockResolvedValue({ data: mockResponse })

      const { result } = renderHook(() => useIntegration())

      await waitFor(async () => {
        await result.current.syncEvaluation.mutate()
      })

      expect(apiClient.integration.syncEvaluation).toHaveBeenCalled()
      expect(toast.success).toHaveBeenCalledWith('Evaluation sync completed')
    })

    it('should handle sync errors', async () => {
      const error = new Error('Evaluation sync failed')
      apiClient.integration.syncEvaluation.mockRejectedValue(error)

      const { result } = renderHook(() => useIntegration())

      await expect(result.current.syncEvaluation.mutate()).rejects.toThrow('Evaluation sync failed')
    })
  })

  describe('loading state', () => {
    it('should set loading to true during fetch', async () => {
      let resolvePromise
      const promise = new Promise((resolve) => {
        resolvePromise = resolve
      })
      apiClient.integration.getEvaluationBridge.mockReturnValue(promise)

      const { result } = renderHook(() => useIntegration())

      const fetchPromise = result.current.fetchEvaluationBridge()

      // Loading should be true during fetch
      await waitFor(() => {
        expect(result.current.loading).toBe(true)
      })

      resolvePromise({ data: {} })
      await fetchPromise

      // Loading should be false after fetch
      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })
    })

    it('should reset loading state on error', async () => {
      const error = new Error('Failed')
      apiClient.integration.getEvaluationBridge.mockRejectedValue(error)

      const { result } = renderHook(() => useIntegration())

      try {
        await result.current.fetchEvaluationBridge()
      } catch (e) {
        // Expected error
      }

      // Loading should be false after error
      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })
    })
  })

  describe('initial state', () => {
    it('should initialize with null evaluation bridge', () => {
      const { result } = renderHook(() => useIntegration())

      expect(result.current.evaluationBridge).toBeNull()
      expect(result.current.loading).toBe(false)
    })
  })
})
