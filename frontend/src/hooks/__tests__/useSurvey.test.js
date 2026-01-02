import { renderHook, waitFor } from '@testing-library/react'
import { useSurvey } from '../useSurvey'
import { apiClient } from '../../lib/api'
import toast from 'react-hot-toast'

// Mock dependencies
jest.mock('../../lib/api', () => ({
  apiClient: {
    survey: {
      getAll: jest.fn(),
      getById: jest.fn(),
      create: jest.fn(),
      update: jest.fn(),
      getQuestions: jest.fn(),
      getResponses: jest.fn(),
      submitResponse: jest.fn(),
      getAnalytics: jest.fn(),
    },
    hybridIdentity: {
      initializeSession: jest.fn(),
      createSurveySession: jest.fn(),
      submitResponse: jest.fn(),
      switchMode: jest.fn(),
      processReveal: jest.fn(),
      analyzeData: jest.fn(),
    },
  },
}))

describe('useSurvey', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('fetchSurveys', () => {
    it('should fetch surveys successfully', async () => {
      const mockSurveys = [
        { id: 1, title: 'Survey 1', status: 'active' },
        { id: 2, title: 'Survey 2', status: 'draft' },
      ]

      apiClient.survey.getAll.mockResolvedValue({ data: mockSurveys })

      const { result } = renderHook(() => useSurvey())

      expect(result.current.loading).toBe(false)
      expect(result.current.surveys).toEqual([])

      await result.current.fetchSurveys()

      await waitFor(() => {
        expect(result.current.surveys).toEqual(mockSurveys)
      })
      expect(apiClient.survey.getAll).toHaveBeenCalledWith({})
    })

    it('should handle fetch errors', async () => {
      const error = new Error('Failed to fetch')
      apiClient.survey.getAll.mockRejectedValue(error)

      const { result } = renderHook(() => useSurvey())

      await expect(result.current.fetchSurveys()).rejects.toThrow('Failed to fetch')
      expect(toast.error).toHaveBeenCalledWith('Failed to load surveys')
    })

    it('should pass filters to API', async () => {
      const mockSurveys = [{ id: 1, title: 'Survey 1', status: 'active' }]
      apiClient.survey.getAll.mockResolvedValue({ data: mockSurveys })

      const { result } = renderHook(() => useSurvey())

      await waitFor(async () => {
        await result.current.fetchSurveys({ status: 'active' })
      })

      expect(apiClient.survey.getAll).toHaveBeenCalledWith({ status: 'active' })
    })
  })

  describe('fetchSurvey', () => {
    it('should fetch a single survey', async () => {
      const mockSurvey = { id: 1, title: 'Survey 1', status: 'active' }
      apiClient.survey.getById.mockResolvedValue({ data: mockSurvey })

      const { result } = renderHook(() => useSurvey())

      await waitFor(async () => {
        await result.current.fetchSurvey(1)
      })

      expect(result.current.survey).toEqual(mockSurvey)
      expect(apiClient.survey.getById).toHaveBeenCalledWith(1)
    })

    it('should handle fetch errors', async () => {
      const error = new Error('Not found')
      apiClient.survey.getById.mockRejectedValue(error)

      const { result } = renderHook(() => useSurvey())

      await expect(result.current.fetchSurvey(1)).rejects.toThrow('Not found')
      expect(toast.error).toHaveBeenCalledWith('Failed to load survey')
    })
  })

  describe('fetchQuestions', () => {
    it('should fetch survey questions', async () => {
      const mockQuestions = [
        { id: 1, question_text: 'Question 1', question_type: 'text' },
        { id: 2, question_text: 'Question 2', question_type: 'multiple_choice' },
      ]
      apiClient.survey.getQuestions.mockResolvedValue({ data: mockQuestions })

      const { result } = renderHook(() => useSurvey())

      await waitFor(async () => {
        await result.current.fetchQuestions(1)
      })

      expect(result.current.questions).toEqual(mockQuestions)
      expect(apiClient.survey.getQuestions).toHaveBeenCalledWith(1)
    })

    it('should handle empty questions array', async () => {
      apiClient.survey.getQuestions.mockResolvedValue({ data: [] })

      const { result } = renderHook(() => useSurvey())

      await waitFor(async () => {
        await result.current.fetchQuestions(1)
      })

      expect(result.current.questions).toEqual([])
    })
  })

  describe('fetchAnalytics', () => {
    it('should fetch survey analytics', async () => {
      const mockAnalytics = {
        total_responses: 100,
        completion_rate: 0.85,
        average_rating: 4.2,
      }
      apiClient.survey.getAnalytics.mockResolvedValue({ data: mockAnalytics })

      const { result } = renderHook(() => useSurvey())

      await waitFor(async () => {
        await result.current.fetchAnalytics(1)
      })

      expect(result.current.analytics).toEqual(mockAnalytics)
      expect(apiClient.survey.getAnalytics).toHaveBeenCalledWith(1)
    })
  })

  describe('createSurvey', () => {
    it('should create a survey successfully', async () => {
      const newSurvey = { title: 'New Survey', survey_type: 'comprehensive' }
      const createdSurvey = { id: 1, ...newSurvey }
      apiClient.survey.create.mockResolvedValue({ data: createdSurvey })

      const { result } = renderHook(() => useSurvey())

      await waitFor(async () => {
        await result.current.createSurvey.mutate(newSurvey)
      })

      expect(apiClient.survey.create).toHaveBeenCalledWith(newSurvey)
      expect(toast.success).toHaveBeenCalledWith('Survey created successfully')
    })
  })

  describe('updateSurvey', () => {
    it('should update a survey successfully', async () => {
      const updateData = { title: 'Updated Survey' }
      const updatedSurvey = { id: 1, ...updateData }
      apiClient.survey.update.mockResolvedValue({ data: updatedSurvey })

      const { result } = renderHook(() => useSurvey())

      await waitFor(async () => {
        await result.current.updateSurvey.mutate({ id: 1, data: updateData })
      })

      expect(apiClient.survey.update).toHaveBeenCalledWith(1, updateData)
      expect(toast.success).toHaveBeenCalledWith('Survey updated successfully')
    })
  })

  describe('loading state', () => {
    it('should set loading to true during fetch', async () => {
      let resolvePromise
      const promise = new Promise((resolve) => {
        resolvePromise = resolve
      })
      apiClient.survey.getAll.mockReturnValue(promise)

      const { result } = renderHook(() => useSurvey())

      const fetchPromise = result.current.fetchSurveys()

      // Loading should be true during fetch
      await waitFor(() => {
        expect(result.current.loading).toBe(true)
      })

      resolvePromise({ data: [] })
      await fetchPromise

      // Loading should be false after fetch
      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })
    })
  })
})
