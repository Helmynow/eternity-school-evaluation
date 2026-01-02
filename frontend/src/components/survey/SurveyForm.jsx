import { useState } from 'react'
import toast from 'react-hot-toast'
import ErrorBoundary from '../common/ErrorBoundary'
import LoadingSkeleton from '../common/LoadingSkeleton'
import PropTypes from 'prop-types'

const SurveyForm = ({ survey, questions, identityMode, onSubmit, onBack, loading = false }) => {
  const [responses, setResponses] = useState({})
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0)
  const [submitting, setSubmitting] = useState(false)

  const currentQuestion = questions?.[currentQuestionIndex]

  const handleResponseChange = (questionId, value) => {
    setResponses((prev) => ({
      ...prev,
      [questionId]: value,
    }))
  }

  const handleNext = () => {
    if (currentQuestion.required && !responses[currentQuestion.id]) {
      toast.error('This question is required')
      return
    }
    if (currentQuestionIndex < questions.length - 1) {
      setCurrentQuestionIndex(currentQuestionIndex + 1)
    }
  }

  const handlePrevious = () => {
    if (currentQuestionIndex > 0) {
      setCurrentQuestionIndex(currentQuestionIndex - 1)
    }
  }

  const handleSubmit = async () => {
    // Validate required questions
    const missingRequired = questions.filter(
      (q) => q.required && !responses[q.id]
    )
    if (missingRequired.length > 0) {
      toast.error(`Please answer all required questions (${missingRequired.length} remaining)`)
      return
    }

    setSubmitting(true)
    try {
      await onSubmit(responses)
    } catch (error) {
      console.error('Error submitting:', error)
    } finally {
      setSubmitting(false)
    }
  }

  const renderQuestionInput = (question) => {
    const value = responses[question.id] || ''

    switch (question.question_type) {
      case 'multiple_choice':
        return (
          <div className="space-y-2">
            {question.options?.map((option, idx) => (
              <label
                key={idx}
                className="flex items-center p-3 border border-ese-ink-light rounded-lg hover:bg-ese-lang-50 cursor-pointer"
              >
                <input
                  type="radio"
                  name={`question-${question.id}`}
                  value={option}
                  checked={value === option}
                  onChange={(e) => handleResponseChange(question.id, e.target.value)}
                  className="mr-3"
                />
                <span className="text-ese-ink-navy">{option}</span>
              </label>
            ))}
          </div>
        )

      case 'rating':
        return (
          <div className="flex space-x-2">
            {[1, 2, 3, 4, 5].map((rating) => (
              <button
                key={rating}
                onClick={() => handleResponseChange(question.id, rating)}
                className={`w-12 h-12 rounded-lg border-2 transition-colors ${
                  value === rating
                    ? 'bg-ese-lang-900 text-white border-ese-lang-900'
                    : 'border-ese-ink-light hover:border-ese-lang-700'
                }`}
              >
                {rating}
              </button>
            ))}
          </div>
        )

      case 'yes_no':
        return (
          <div className="flex space-x-4">
            {['Yes', 'No'].map((option) => (
              <button
                key={option}
                onClick={() => handleResponseChange(question.id, option.toLowerCase())}
                className={`px-6 py-3 rounded-lg border-2 transition-colors ${
                  value === option.toLowerCase()
                    ? 'bg-ese-lang-900 text-white border-ese-lang-900'
                    : 'border-ese-ink-light hover:border-ese-lang-700'
                }`}
              >
                {option}
              </button>
            ))}
          </div>
        )

      case 'text':
      default:
        return (
          <textarea
            value={value}
            onChange={(e) => handleResponseChange(question.id, e.target.value)}
            rows={6}
            className="w-full p-3 border border-ese-ink-light rounded-lg focus:outline-none focus:ring-2 focus:ring-ese-lang-700"
            placeholder="Enter your response..."
          />
        )
    }
  }

  const progress = questions?.length > 0 ? ((currentQuestionIndex + 1) / questions.length) * 100 : 0

  // Show loading state
  if (loading || !questions || questions.length === 0) {
    return (
      <ErrorBoundary>
        <div className="space-y-6">
          <span className="sr-only">Loading...</span>
          <LoadingSkeleton type="form" count={3} />
        </div>
      </ErrorBoundary>
    )
  }

  return (
    <ErrorBoundary>
      <div className="space-y-6">
      {/* Header */}
      <div>
        <button
          onClick={onBack}
          className="text-ese-lang-900 hover:text-ese-lang-700 mb-4 flex items-center"
        >
          ← Back to mode selection
        </button>
        <h1 className="text-3xl font-bold text-ese-ink-navy mb-2">{survey.title}</h1>
        {survey.description && (
          <p className="text-ese-ink-medium mb-2">{survey.description}</p>
        )}
        <div className="flex items-center space-x-4 text-sm text-ese-ink-medium">
          <span>Mode: {identityMode}</span>
          <span>•</span>
          <span>
            Question {currentQuestionIndex + 1} of {questions.length}
          </span>
        </div>
      </div>

      {/* Progress Bar */}
      <div
        className="w-full bg-ese-ink-light rounded-full h-2"
        role="progressbar"
        aria-label="Survey progress"
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={Math.round(progress)}
      >
        <div
          className="bg-ese-lang-900 h-2 rounded-full transition-all"
          style={{ width: `${progress}%` }}
        />
      </div>

      {/* Current Question */}
      {currentQuestion && (
        <div className="bg-white rounded-lg shadow-md p-6 border border-ese-ink-light">
          <div className="mb-4">
            {currentQuestion.category && (
              <span className="text-xs px-2 py-1 bg-ese-lang-100 text-ese-lang-900 rounded">
                {currentQuestion.category}
              </span>
            )}
            {currentQuestion.required && (
              <span className="text-red-500 ml-2">*</span>
            )}
          </div>

          <h2 className="text-xl font-semibold text-ese-ink-navy mb-4">
            {currentQuestion.question_text}
          </h2>

          {currentQuestion.section && (
            <p className="text-sm text-ese-ink-medium mb-4">{currentQuestion.section}</p>
          )}

          <div className="mt-6">{renderQuestionInput(currentQuestion)}</div>
        </div>
      )}

      {/* Navigation */}
      <div className="flex justify-between">
        <button
          onClick={handlePrevious}
          disabled={currentQuestionIndex === 0}
          className="px-6 py-2 border border-ese-ink-light rounded-lg hover:bg-ese-lang-50 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Previous
        </button>

        {currentQuestionIndex < questions.length - 1 ? (
          <button
            onClick={handleNext}
            className="px-6 py-2 bg-ese-lang-900 text-white rounded-lg hover:bg-ese-lang-800"
          >
            Next
          </button>
        ) : (
          <button
            onClick={handleSubmit}
            disabled={submitting}
            className="px-6 py-2 bg-ese-int-700 text-white rounded-lg hover:bg-ese-int-800 disabled:opacity-50"
          >
            {submitting ? 'Submitting...' : 'Submit Survey'}
          </button>
        )}
      </div>
      </div>
    </ErrorBoundary>
  )
}

SurveyForm.propTypes = {
  survey: PropTypes.shape({
    id: PropTypes.oneOfType([PropTypes.string, PropTypes.number]).isRequired,
    title: PropTypes.string.isRequired,
    description: PropTypes.string,
    status: PropTypes.oneOf(['draft', 'active', 'closed']),
  }).isRequired,
  questions: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.oneOfType([PropTypes.string, PropTypes.number]).isRequired,
      question_text: PropTypes.string.isRequired,
      question_type: PropTypes.oneOf(['text', 'multiple_choice', 'rating', 'yes_no']).isRequired,
      required: PropTypes.bool,
      category: PropTypes.string,
      section: PropTypes.string,
      options: PropTypes.arrayOf(PropTypes.string),
    })
  ).isRequired,
  identityMode: PropTypes.oneOf(['anonymous', 'conditional', 'identified']).isRequired,
  onSubmit: PropTypes.func.isRequired,
  onBack: PropTypes.func.isRequired,
  loading: PropTypes.bool,
}

export default SurveyForm
