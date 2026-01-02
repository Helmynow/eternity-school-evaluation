import { useState, useEffect } from 'react'
import { useAPI, useMutation } from '../../hooks/useAPI'
import { apiClient } from '../../lib/api'
import { useAuth } from '../../hooks/useAuth'
import toast from 'react-hot-toast'

const EOMFeedbackForm = ({ cycleId }) => {
  const { user } = useAuth()
  const [feedbackType, setFeedbackType] = useState('nominee')
  const [feedbackText, setFeedbackText] = useState('')
  const [rating, setRating] = useState(5)
  const [submitted, setSubmitted] = useState(false)

  const { mutate: submitFeedback, loading } = useMutation(
    (data) => apiClient.post('/api/v2/eom/feedback', data)
  )

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    if (!feedbackText.trim()) {
      toast.error('Please provide feedback text')
      return
    }

    try {
      await submitFeedback({
        eom_cycle_id: cycleId,
        feedback_type: feedbackType,
        person_email: user?.email,
        feedback_text: feedbackText,
        rating: rating
      })
      
      toast.success('Thank you for your feedback!')
      setSubmitted(true)
      setFeedbackText('')
      setRating(5)
    } catch (error) {
      toast.error('Failed to submit feedback')
    }
  }

  if (submitted) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-8">
        <div className="bg-green-50 border border-green-200 rounded-lg p-6 text-center">
          <div className="mb-4">
            <img src="/assets/icons/success.png" alt="Success" className="w-16 h-16 mx-auto" onError={(e) => { e.target.style.display = 'none'; e.target.parentElement.innerHTML = '<div className="text-4xl mb-4">✅</div>' }} />
          </div>
          <h3 className="text-xl font-heading font-semibold text-green-800 mb-2">
            Feedback Submitted Successfully
          </h3>
          <p className="text-green-700 mb-4">
            Thank you for taking the time to provide feedback. Your input helps us improve the EOM program.
          </p>
          <button
            onClick={() => setSubmitted(false)}
            className="ese-button-primary"
          >
            Submit Another Feedback
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-2xl mx-auto px-4 py-8">
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-2xl font-heading font-bold text-ese-ink-navy mb-4">
          EOM Feedback Form
        </h2>
        <p className="text-ese-ink-navy/70 mb-6">
          Help us improve the Employee of the Month program by sharing your experience.
        </p>

        <form onSubmit={handleSubmit}>
          <div className="mb-6">
            <label className="block text-sm font-medium text-ese-ink-navy mb-2">
              I am a:
            </label>
            <div className="grid grid-cols-3 gap-4">
              <button
                type="button"
                onClick={() => setFeedbackType('nominee')}
                className={`px-4 py-3 rounded-lg border-2 transition-all ${
                  feedbackType === 'nominee'
                    ? 'border-ese-lang-900 bg-ese-lang-50'
                    : 'border-ese-accent-beige bg-white hover:border-ese-lang-900'
                }`}
              >
                Nominee
              </button>
              <button
                type="button"
                onClick={() => setFeedbackType('nominator')}
                className={`px-4 py-3 rounded-lg border-2 transition-all ${
                  feedbackType === 'nominator'
                    ? 'border-ese-lang-900 bg-ese-lang-50'
                    : 'border-ese-accent-beige bg-white hover:border-ese-lang-900'
                }`}
              >
                Nominator
              </button>
              <button
                type="button"
                onClick={() => setFeedbackType('voter')}
                className={`px-4 py-3 rounded-lg border-2 transition-all ${
                  feedbackType === 'voter'
                    ? 'border-ese-lang-900 bg-ese-lang-50'
                    : 'border-ese-accent-beige bg-white hover:border-ese-lang-900'
                }`}
              >
                Voter
              </button>
            </div>
          </div>

          <div className="mb-6">
            <label className="block text-sm font-medium text-ese-ink-navy mb-2">
              Overall Rating (1-5)
            </label>
            <div className="flex items-center space-x-2">
              {[1, 2, 3, 4, 5].map((star) => (
                <button
                  key={star}
                  type="button"
                  onClick={() => setRating(star)}
                  className={`transition-all ${
                    star <= rating
                      ? 'opacity-100'
                      : 'opacity-30'
                  }`}
                >
                  <img src="/assets/icons/rising_star.png" alt={`${star} star`} className="w-8 h-8" onError={(e) => { e.target.outerHTML = '<span className="text-3xl">⭐</span>' }} />
                </button>
              ))}
              <span className="ml-4 text-sm text-ese-ink-navy/70">
                {rating} out of 5
              </span>
            </div>
          </div>

          <div className="mb-6">
            <label className="block text-sm font-medium text-ese-ink-navy mb-2">
              Your Feedback
            </label>
            <textarea
              value={feedbackText}
              onChange={(e) => setFeedbackText(e.target.value)}
              rows={6}
              className="w-full px-4 py-3 border border-ese-accent-beige rounded-lg focus:outline-none focus:ring-2 focus:ring-ese-accent-light-blue"
              placeholder="Please share your thoughts about the EOM process, what worked well, and what could be improved..."
            />
          </div>

          <div className="flex justify-end space-x-4">
            <button
              type="button"
              onClick={() => {
                setFeedbackText('')
                setRating(5)
              }}
              className="px-6 py-2 border border-ese-accent-beige rounded-lg text-ese-ink-navy hover:bg-ese-accent-beige transition-all"
            >
              Clear
            </button>
            <button
              type="submit"
              disabled={loading || !feedbackText.trim()}
              className="ese-button-primary disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Submitting...' : 'Submit Feedback'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default EOMFeedbackForm
