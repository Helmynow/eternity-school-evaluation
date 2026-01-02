import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import SurveySession from '../SurveySession'
import { apiClient } from '../../../lib/api'
import { useAuth } from '../../../hooks/useAuth'
import toast from 'react-hot-toast'

// Mock dependencies
jest.mock('../../../lib/api')
jest.mock('../../../hooks/useAuth')
jest.mock('react-hot-toast', () => ({
  default: {
    success: jest.fn(),
    error: jest.fn(),
  },
}))

// Mock localStorage
const localStorageMock = (() => {
  let store = {}
  return {
    getItem: jest.fn((key) => store[key] || null),
    setItem: jest.fn((key, value) => { store[key] = value.toString() }),
    removeItem: jest.fn((key) => { delete store[key] }),
    clear: jest.fn(() => { store = {} }),
  }
})()
Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
})

const mockNavigate = jest.fn()
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
  useParams: () => ({ surveyId: '1' }),
}))

const renderWithRouter = (component) => {
  return render(<BrowserRouter>{component}</BrowserRouter>)
}

describe('SurveySession', () => {
  const mockUser = {
    email: 'test@example.com',
    id: '123',
  }

  const mockSurvey = {
    id: 1,
    title: 'Test Survey',
    description: 'Test Description',
    survey_type: 'comprehensive',
    status: 'active',
  }

  const mockQuestions = [
    {
      id: 1,
      question_text: 'Question 1',
      question_type: 'text',
      required: true,
      identity_modes: ['anonymous', 'conditional', 'identified'],
    },
    {
      id: 2,
      question_text: 'Question 2',
      question_type: 'multiple_choice',
      required: false,
      options: ['Option A', 'Option B'],
      identity_modes: ['anonymous', 'conditional', 'identified'],
    },
  ]

  beforeEach(() => {
    jest.clearAllMocks()
    localStorageMock.getItem.mockReturnValue(null)
    useAuth.mockReturnValue({
      user: mockUser,
      isCEO: false,
      isPNC: false,
    })
  })

  describe('Initial Load', () => {
    it('should load survey and questions on mount', async () => {
      apiClient.survey.getById.mockResolvedValue({ data: mockSurvey })
      apiClient.survey.getQuestions.mockResolvedValue({ data: mockQuestions })

      renderWithRouter(<SurveySession />)

      await waitFor(() => {
        expect(apiClient.survey.getById).toHaveBeenCalledWith('1')
        expect(apiClient.survey.getQuestions).toHaveBeenCalledWith('1')
      })
    })

    it('should restore session from localStorage if available', async () => {
      localStorageMock.getItem.mockImplementation((key) => {
        if (key === 'survey_session_token') return 'saved-token'
        if (key === 'survey_identity_mode') return 'anonymous'
        return null
      })

      apiClient.survey.getById.mockResolvedValue({ data: mockSurvey })
      apiClient.survey.getQuestions.mockResolvedValue({ data: mockQuestions })

      renderWithRouter(<SurveySession />)

      await waitFor(() => {
        expect(screen.queryByText('Choose Your Privacy Mode')).not.toBeInTheDocument()
      })
    })

    it('should show error message if survey fails to load', async () => {
      apiClient.survey.getById.mockRejectedValue(new Error('Not found'))
      apiClient.survey.getQuestions.mockResolvedValue({ data: [] })

      renderWithRouter(<SurveySession />)

      await waitFor(() => {
        expect(toast.error).toHaveBeenCalledWith('Failed to load survey')
      })
    })
  })

  describe('Identity Mode Selection', () => {
    beforeEach(async () => {
      apiClient.survey.getById.mockResolvedValue({ data: mockSurvey })
      apiClient.survey.getQuestions.mockResolvedValue({ data: mockQuestions })
    })

    it('should show identity mode selector initially', async () => {
      renderWithRouter(<SurveySession />)

      await waitFor(() => {
        expect(screen.getByText('Choose Your Privacy Mode')).toBeInTheDocument()
      })
    })

    it('should initialize session when mode is selected', async () => {
      const mockSessionResponse = {
        data: {
          session_token: 'test-token',
          sessionToken: 'test-token',
        },
      }

      apiClient.hybridIdentity.initializeSession.mockResolvedValue(mockSessionResponse)
      apiClient.hybridIdentity.createSurveySession.mockResolvedValue({ data: {} })

      renderWithRouter(<SurveySession />)

      await waitFor(() => {
        expect(screen.getByText('Choose Your Privacy Mode')).toBeInTheDocument()
      })

      // Find and click anonymous mode button
      const anonymousButton = screen.getByText('Anonymous').closest('button')
      fireEvent.click(anonymousButton)

      await waitFor(() => {
        expect(apiClient.hybridIdentity.initializeSession).toHaveBeenCalledWith({
          user_email: mockUser.email,
          preferred_mode: 'anonymous',
          survey_id: 1,
        })
      })
    })

    it('should save preference when mode is selected', async () => {
      const mockSessionResponse = {
        data: {
          session_token: 'test-token',
        },
      }

      apiClient.hybridIdentity.initializeSession.mockResolvedValue(mockSessionResponse)
      apiClient.hybridIdentity.createSurveySession.mockResolvedValue({ data: {} })
      apiClient.surveyIdentity.setPreference.mockResolvedValue({ data: {} })

      renderWithRouter(<SurveySession />)

      await waitFor(() => {
        expect(screen.getByText('Choose Your Privacy Mode')).toBeInTheDocument()
      })

      const anonymousButton = screen.getByText('Anonymous').closest('button')
      fireEvent.click(anonymousButton)

      await waitFor(() => {
        expect(apiClient.surveyIdentity.setPreference).toHaveBeenCalled()
      })
    })

    it('should handle session initialization error', async () => {
      apiClient.hybridIdentity.initializeSession.mockRejectedValue(new Error('Failed'))

      renderWithRouter(<SurveySession />)

      await waitFor(() => {
        expect(screen.getByText('Choose Your Privacy Mode')).toBeInTheDocument()
      })

      const anonymousButton = screen.getByText('Anonymous').closest('button')
      fireEvent.click(anonymousButton)

      await waitFor(() => {
        expect(toast.error).toHaveBeenCalledWith('Failed to initialize survey session')
      })
    })
  })

  describe('Survey Form', () => {
    beforeEach(async () => {
      apiClient.survey.getById.mockResolvedValue({ data: mockSurvey })
      apiClient.survey.getQuestions.mockResolvedValue({ data: mockQuestions })
      apiClient.hybridIdentity.initializeSession.mockResolvedValue({
        data: { session_token: 'test-token' },
      })
      apiClient.hybridIdentity.createSurveySession.mockResolvedValue({ data: {} })
    })

    it('should show survey form after mode selection', async () => {
      renderWithRouter(<SurveySession />)

      await waitFor(() => {
        expect(screen.getByText('Choose Your Privacy Mode')).toBeInTheDocument()
      })

      const anonymousButton = screen.getByText('Anonymous').closest('button')
      fireEvent.click(anonymousButton)

      await waitFor(() => {
        expect(screen.getByText('Test Survey')).toBeInTheDocument()
        expect(screen.getByText('Question 1')).toBeInTheDocument()
      })
    })

    it('should filter questions based on identity mode', async () => {
      const filteredQuestions = [
        {
          ...mockQuestions[0],
          identity_modes: ['anonymous'],
        },
        {
          ...mockQuestions[1],
          identity_modes: ['identified'],
        },
      ]

      apiClient.survey.getQuestions.mockResolvedValue({ data: filteredQuestions })

      renderWithRouter(<SurveySession />)

      await waitFor(() => {
        expect(screen.getByText('Choose Your Privacy Mode')).toBeInTheDocument()
      })

      const anonymousButton = screen.getByText('Anonymous').closest('button')
      fireEvent.click(anonymousButton)

      await waitFor(() => {
        // Should only show question 1 (anonymous mode)
        expect(screen.getByText('Question 1')).toBeInTheDocument()
      })
    })
  })

  describe('Response Submission', () => {
    beforeEach(async () => {
      apiClient.survey.getById.mockResolvedValue({ data: mockSurvey })
      apiClient.survey.getQuestions.mockResolvedValue({ data: mockQuestions })
      apiClient.hybridIdentity.initializeSession.mockResolvedValue({
        data: { session_token: 'test-token' },
      })
      apiClient.hybridIdentity.createSurveySession.mockResolvedValue({ data: {} })
      apiClient.hybridIdentity.submitResponse.mockResolvedValue({ data: {} })
    })

    it('should submit responses via hybrid identity flow', async () => {
      renderWithRouter(<SurveySession />)

      // Select mode
      await waitFor(() => {
        expect(screen.getByText('Choose Your Privacy Mode')).toBeInTheDocument()
      })

      const anonymousButton = screen.getByText('Anonymous').closest('button')
      fireEvent.click(anonymousButton)

      // Wait for form to appear
      await waitFor(() => {
        expect(screen.getByText('Question 1')).toBeInTheDocument()
      })

      // Fill response
      const textarea = screen.getByPlaceholderText('Enter your response...')
      fireEvent.change(textarea, { target: { value: 'Test response' } })

      // Submit
      const submitButton = screen.getByText('Submit Survey')
      fireEvent.click(submitButton)

      await waitFor(() => {
        expect(apiClient.hybridIdentity.submitResponse).toHaveBeenCalled()
      })
    })

    it('should handle submission errors gracefully', async () => {
      apiClient.hybridIdentity.submitResponse.mockRejectedValue({
        response: {
          status: 500,
          data: { detail: 'Server error' },
        },
      })

      renderWithRouter(<SurveySession />)

      await waitFor(() => {
        expect(screen.getByText('Choose Your Privacy Mode')).toBeInTheDocument()
      })

      const anonymousButton = screen.getByText('Anonymous').closest('button')
      fireEvent.click(anonymousButton)

      await waitFor(() => {
        expect(screen.getByText('Question 1')).toBeInTheDocument()
      })

      const textarea = screen.getByPlaceholderText('Enter your response...')
      fireEvent.change(textarea, { target: { value: 'Test response' } })

      const submitButton = screen.getByText('Submit Survey')
      fireEvent.click(submitButton)

      await waitFor(() => {
        expect(toast.error).toHaveBeenCalled()
      })
    })

    it('should clear localStorage after successful submission', async () => {
      renderWithRouter(<SurveySession />)

      await waitFor(() => {
        expect(screen.getByText('Choose Your Privacy Mode')).toBeInTheDocument()
      })

      const anonymousButton = screen.getByText('Anonymous').closest('button')
      fireEvent.click(anonymousButton)

      await waitFor(() => {
        expect(screen.getByText('Question 1')).toBeInTheDocument()
      })

      const textarea = screen.getByPlaceholderText('Enter your response...')
      fireEvent.change(textarea, { target: { value: 'Test response' } })

      const submitButton = screen.getByText('Submit Survey')
      fireEvent.click(submitButton)

      await waitFor(() => {
        expect(localStorageMock.removeItem).toHaveBeenCalledWith('survey_session_token')
        expect(localStorageMock.removeItem).toHaveBeenCalledWith('survey_identity_mode')
        expect(mockNavigate).toHaveBeenCalledWith('/survey')
      })
    })
  })

  describe('Loading States', () => {
    it('should show loading skeleton while loading survey', () => {
      apiClient.survey.getById.mockImplementation(
        () => new Promise(() => {}) // Never resolves
      )
      apiClient.survey.getQuestions.mockResolvedValue({ data: [] })

      renderWithRouter(<SurveySession />)

      // Should show loading state
      expect(screen.getByText(/loading/i)).toBeInTheDocument()
    })
  })
})
