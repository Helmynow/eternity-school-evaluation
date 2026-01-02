import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import SurveyForm from '../SurveyForm'
import toast from 'react-hot-toast'

jest.mock('react-hot-toast', () => ({
  __esModule: true,
  default: {
    success: jest.fn(),
    error: jest.fn(),
    loading: jest.fn(),
  },
}))

const mockSurvey = {
  id: 1,
  title: 'Test Survey',
  description: 'Test Description',
  status: 'active',
}

const mockQuestions = [
  {
    id: 1,
    question_text: 'What is your name?',
    question_type: 'text',
    required: true,
    category: 'Personal',
  },
  {
    id: 2,
    question_text: 'Rate your experience',
    question_type: 'rating',
    required: false,
    category: 'Rating',
  },
  {
    id: 3,
    question_text: 'Choose an option',
    question_type: 'multiple_choice',
    required: true,
    options: ['Option A', 'Option B', 'Option C'],
    category: 'Choice',
  },
  {
    id: 4,
    question_text: 'Do you agree?',
    question_type: 'yes_no',
    required: false,
    category: 'Agreement',
  },
]

describe('SurveyForm', () => {
  const mockOnSubmit = jest.fn()
  const mockOnBack = jest.fn()

  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('Rendering', () => {
    it('should render survey title and description', () => {
      render(
        <SurveyForm
          survey={mockSurvey}
          questions={mockQuestions}
          identityMode="anonymous"
          onSubmit={mockOnSubmit}
          onBack={mockOnBack}
        />
      )

      expect(screen.getByText('Test Survey')).toBeInTheDocument()
      expect(screen.getByText('Test Description')).toBeInTheDocument()
    })

    it('should render first question by default', () => {
      render(
        <SurveyForm
          survey={mockSurvey}
          questions={mockQuestions}
          identityMode="anonymous"
          onSubmit={mockOnSubmit}
          onBack={mockOnBack}
        />
      )

      expect(screen.getByText('What is your name?')).toBeInTheDocument()
      expect(screen.getByText('Question 1 of 4')).toBeInTheDocument()
    })

    it('should show progress bar', () => {
      render(
        <SurveyForm
          survey={mockSurvey}
          questions={mockQuestions}
          identityMode="anonymous"
          onSubmit={mockOnSubmit}
          onBack={mockOnBack}
        />
      )

      const progressBar = screen.getByRole('progressbar', { hidden: true })
      expect(progressBar).toBeInTheDocument()
    })

    it('should show loading skeleton when loading', () => {
      render(
        <SurveyForm
          survey={mockSurvey}
          questions={mockQuestions}
          identityMode="anonymous"
          onSubmit={mockOnSubmit}
          onBack={mockOnBack}
          loading={true}
        />
      )

      // Loading skeleton should be visible
      expect(screen.getByText(/loading/i)).toBeInTheDocument()
    })
  })

  describe('Question Navigation', () => {
    it('should navigate to next question', async () => {
      const user = userEvent.setup()
      render(
        <SurveyForm
          survey={mockSurvey}
          questions={mockQuestions}
          identityMode="anonymous"
          onSubmit={mockOnSubmit}
          onBack={mockOnBack}
        />
      )

      // Fill first question
      const textarea = screen.getByPlaceholderText('Enter your response...')
      await user.type(textarea, 'John Doe')

      // Click Next
      const nextButton = screen.getByText('Next')
      await user.click(nextButton)

      // Should show second question
      await waitFor(() => {
        expect(screen.getByText('Rate your experience')).toBeInTheDocument()
        expect(screen.getByText('Question 2 of 4')).toBeInTheDocument()
      })
    })

    it('should navigate to previous question', async () => {
      const user = userEvent.setup()
      render(
        <SurveyForm
          survey={mockSurvey}
          questions={mockQuestions}
          identityMode="anonymous"
          onSubmit={mockOnSubmit}
          onBack={mockOnBack}
        />
      )

      // Fill first question and go to second
      const textarea = screen.getByPlaceholderText('Enter your response...')
      await user.type(textarea, 'John Doe')
      await user.click(screen.getByText('Next'))

      await waitFor(() => {
        expect(screen.getByText('Rate your experience')).toBeInTheDocument()
      })

      // Click Previous
      const previousButton = screen.getByText('Previous')
      await user.click(previousButton)

      // Should show first question again
      await waitFor(() => {
        expect(screen.getByText('What is your name?')).toBeInTheDocument()
      })
    })

    it('should disable Previous button on first question', () => {
      render(
        <SurveyForm
          survey={mockSurvey}
          questions={mockQuestions}
          identityMode="anonymous"
          onSubmit={mockOnSubmit}
          onBack={mockOnBack}
        />
      )

      const previousButton = screen.getByText('Previous')
      expect(previousButton).toBeDisabled()
    })

    it('should show Submit button on last question', async () => {
      const user = userEvent.setup()
      render(
        <SurveyForm
          survey={mockSurvey}
          questions={mockQuestions}
          identityMode="anonymous"
          onSubmit={mockOnSubmit}
          onBack={mockOnBack}
        />
      )

      // Navigate to last question
      const textarea = screen.getByPlaceholderText('Enter your response...')
      await user.type(textarea, 'Answer')
      await user.click(screen.getByText('Next'))
      await user.click(screen.getByText('Next'))

      // Question 3 is required (multiple choice) - select an option
      await waitFor(() => {
        expect(screen.getByText('Choose an option')).toBeInTheDocument()
      })
      await user.click(screen.getByText('Option A'))

      await user.click(screen.getByText('Next'))

      await waitFor(() => {
        expect(screen.getByText('Submit Survey')).toBeInTheDocument()
        expect(screen.queryByText('Next')).not.toBeInTheDocument()
      })
    })
  })

  describe('Question Types', () => {
    it('should render text input for text questions', () => {
      render(
        <SurveyForm
          survey={mockSurvey}
          questions={[mockQuestions[0]]}
          identityMode="anonymous"
          onSubmit={mockOnSubmit}
          onBack={mockOnBack}
        />
      )

      expect(screen.getByPlaceholderText('Enter your response...')).toBeInTheDocument()
    })

    it('should render rating buttons for rating questions', async () => {
      const user = userEvent.setup()
      render(
        <SurveyForm
          survey={mockSurvey}
          questions={mockQuestions}
          identityMode="anonymous"
          onSubmit={mockOnSubmit}
          onBack={mockOnBack}
        />
      )

      // Navigate to rating question
      const textarea = screen.getByPlaceholderText('Enter your response...')
      await user.type(textarea, 'Answer')
      await user.click(screen.getByText('Next'))

      await waitFor(() => {
        expect(screen.getByText('Rate your experience')).toBeInTheDocument()
        // Should have rating buttons 1-5
        expect(screen.getByText('1')).toBeInTheDocument()
        expect(screen.getByText('5')).toBeInTheDocument()
      })
    })

    it('should render radio buttons for multiple choice questions', async () => {
      const user = userEvent.setup()
      render(
        <SurveyForm
          survey={mockSurvey}
          questions={mockQuestions}
          identityMode="anonymous"
          onSubmit={mockOnSubmit}
          onBack={mockOnBack}
        />
      )

      // Navigate to multiple choice question
      const textarea = screen.getByPlaceholderText('Enter your response...')
      await user.type(textarea, 'Answer')
      await user.click(screen.getByText('Next'))
      await user.click(screen.getByText('Next'))

      await waitFor(() => {
        expect(screen.getByText('Choose an option')).toBeInTheDocument()
        expect(screen.getByText('Option A')).toBeInTheDocument()
        expect(screen.getByText('Option B')).toBeInTheDocument()
        expect(screen.getByText('Option C')).toBeInTheDocument()
      })
    })

    it('should render Yes/No buttons for yes_no questions', async () => {
      const user = userEvent.setup()
      render(
        <SurveyForm
          survey={mockSurvey}
          questions={mockQuestions}
          identityMode="anonymous"
          onSubmit={mockOnSubmit}
          onBack={mockOnBack}
        />
      )

      // Navigate to yes_no question
      const textarea = screen.getByPlaceholderText('Enter your response...')
      await user.type(textarea, 'Answer')
      await user.click(screen.getByText('Next'))
      await user.click(screen.getByText('Next'))

      // Question 3 is required (multiple choice) - select an option
      await waitFor(() => {
        expect(screen.getByText('Choose an option')).toBeInTheDocument()
      })
      await user.click(screen.getByText('Option A'))

      await user.click(screen.getByText('Next'))

      await waitFor(() => {
        expect(screen.getByText('Do you agree?')).toBeInTheDocument()
        expect(screen.getByText('Yes')).toBeInTheDocument()
        expect(screen.getByText('No')).toBeInTheDocument()
      })
    })
  })

  describe('Validation', () => {
    it('should prevent navigation if required question is not answered', async () => {
      const user = userEvent.setup()
      render(
        <SurveyForm
          survey={mockSurvey}
          questions={mockQuestions}
          identityMode="anonymous"
          onSubmit={mockOnSubmit}
          onBack={mockOnBack}
        />
      )

      // Try to navigate without answering required question
      const nextButton = screen.getByText('Next')
      await user.click(nextButton)

      await waitFor(() => {
        expect(toast.error).toHaveBeenCalledWith('This question is required')
        expect(screen.getByText('What is your name?')).toBeInTheDocument()
      })
    })

    it('should validate all required questions before submission', async () => {
      const user = userEvent.setup()
      render(
        <SurveyForm
          survey={mockSurvey}
          questions={mockQuestions}
          identityMode="anonymous"
          onSubmit={mockOnSubmit}
          onBack={mockOnBack}
        />
      )

      // Answer first question
      const textarea = screen.getByPlaceholderText('Enter your response...')
      await user.type(textarea, 'Answer')
      await user.click(screen.getByText('Next'))

      // Navigate to required question 3 without answering it
      await waitFor(() => {
        expect(screen.getByText('Rate your experience')).toBeInTheDocument()
      })
      await user.click(screen.getByText('Next'))
      await waitFor(() => {
        expect(screen.getByText('Choose an option')).toBeInTheDocument()
      })

      // Attempt to continue without answering required question 3
      await user.click(screen.getByText('Next'))

      await waitFor(() => {
        expect(toast.error).toHaveBeenCalledWith('This question is required')
        expect(screen.queryByText('Do you agree?')).not.toBeInTheDocument()
      })
    })
  })

  describe('Submission', () => {
    it('should call onSubmit with responses when submitted', async () => {
      const user = userEvent.setup()
      render(
        <SurveyForm
          survey={mockSurvey}
          questions={mockQuestions.slice(0, 2)} // Only 2 questions for simplicity
          identityMode="anonymous"
          onSubmit={mockOnSubmit}
          onBack={mockOnBack}
        />
      )

      // Answer first question
      const textarea = screen.getByPlaceholderText('Enter your response...')
      await user.type(textarea, 'John Doe')
      await user.click(screen.getByText('Next'))

      // Answer second question
      await waitFor(() => {
        expect(screen.getByText('Rate your experience')).toBeInTheDocument()
      })
      const ratingButton = screen.getByText('3')
      await user.click(ratingButton)

      // Submit
      const submitButton = screen.getByText('Submit Survey')
      await user.click(submitButton)

      await waitFor(() => {
        expect(mockOnSubmit).toHaveBeenCalledWith({
          1: 'John Doe',
          2: 3,
        })
      })
    })

    it('should show submitting state during submission', async () => {
      const user = userEvent.setup()
      let resolveSubmit
      const submitPromise = new Promise((resolve) => {
        resolveSubmit = resolve
      })
      mockOnSubmit.mockReturnValue(submitPromise)

      render(
        <SurveyForm
          survey={mockSurvey}
          questions={mockQuestions.slice(0, 1)}
          identityMode="anonymous"
          onSubmit={mockOnSubmit}
          onBack={mockOnBack}
        />
      )

      const textarea = screen.getByPlaceholderText('Enter your response...')
      await user.type(textarea, 'Answer')
      const submitButton = screen.getByText('Submit Survey')
      await user.click(submitButton)

      // Should show submitting state
      await waitFor(() => {
        expect(screen.getByText('Submitting...')).toBeInTheDocument()
        expect(submitButton).toBeDisabled()
      })

      resolveSubmit()
      await submitPromise
    })

    it('should handle submission errors', async () => {
      const user = userEvent.setup()
      mockOnSubmit.mockRejectedValue(new Error('Submission failed'))

      render(
        <SurveyForm
          survey={mockSurvey}
          questions={mockQuestions.slice(0, 1)}
          identityMode="anonymous"
          onSubmit={mockOnSubmit}
          onBack={mockOnBack}
        />
      )

      const textarea = screen.getByPlaceholderText('Enter your response...')
      await user.type(textarea, 'Answer')
      const submitButton = screen.getByText('Submit Survey')
      await user.click(submitButton)

      await waitFor(() => {
        expect(mockOnSubmit).toHaveBeenCalled()
      })
    })
  })

  describe('Back Navigation', () => {
    it('should call onBack when back button is clicked', async () => {
      const user = userEvent.setup()
      render(
        <SurveyForm
          survey={mockSurvey}
          questions={mockQuestions}
          identityMode="anonymous"
          onSubmit={mockOnSubmit}
          onBack={mockOnBack}
        />
      )

      const backButton = screen.getByText(/back to mode selection/i)
      await user.click(backButton)

      expect(mockOnBack).toHaveBeenCalled()
    })
  })

  describe('Progress Tracking', () => {
    it('should update progress bar as user navigates', async () => {
      const user = userEvent.setup()
      render(
        <SurveyForm
          survey={mockSurvey}
          questions={mockQuestions}
          identityMode="anonymous"
          onSubmit={mockOnSubmit}
          onBack={mockOnBack}
        />
      )

      // Initial progress should be 25% (1 of 4)
      const progressBar = screen.getByRole('progressbar', { hidden: true })
      expect(progressBar).toHaveAttribute('aria-valuenow', '25')
      const progressFill = progressBar.querySelector('div')
      expect(progressFill).toHaveStyle({ width: '25%' })

      // Navigate to second question
      const textarea = screen.getByPlaceholderText('Enter your response...')
      await user.type(textarea, 'Answer')
      await user.click(screen.getByText('Next'))

      await waitFor(() => {
        expect(progressBar).toHaveAttribute('aria-valuenow', '50')
        expect(progressFill).toHaveStyle({ width: '50%' })
      })
    })
  })
})
