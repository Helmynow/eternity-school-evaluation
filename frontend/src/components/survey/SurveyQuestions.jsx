import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { apiClient } from '../../lib/api'
import { useAuth } from '../../hooks/useAuth'
import { useSurvey } from '../../hooks/useSurvey'
import toast from 'react-hot-toast'
import ErrorBoundary from '../common/ErrorBoundary'
import LoadingSkeleton from '../common/LoadingSkeleton'

const SurveyQuestions = () => {
  const { surveyId } = useParams()
  const navigate = useNavigate()
  const { user, isCEO, isPNC } = useAuth()
  const { survey, questions, loading, fetchSurvey, fetchQuestions } = useSurvey(surveyId)
  const [editingQuestion, setEditingQuestion] = useState(null)
  const [showAddForm, setShowAddForm] = useState(false)
  const [questionForm, setQuestionForm] = useState({
    question_text: '',
    question_type: 'text',
    category: '',
    section: '',
    order_index: 0,
    required: true,
    identity_modes: ['anonymous', 'conditional', 'identified'],
    sensitivity_level: 'medium',
    options: [],
  })

  useEffect(() => {
    if (surveyId) {
      fetchSurvey(surveyId)
      fetchQuestions(surveyId)
    }
  }, [surveyId, fetchSurvey, fetchQuestions])

  const handleAddQuestion = async (e) => {
    e.preventDefault()
    try {
      // This would need a backend endpoint to add questions
      // For now, we'll show a message
      toast.success('Question management coming soon')
      setShowAddForm(false)
      setQuestionForm({
        question_text: '',
        question_type: 'text',
        category: '',
        section: '',
        order_index: 0,
        required: true,
        identity_modes: ['anonymous', 'conditional', 'identified'],
        sensitivity_level: 'medium',
        options: [],
      })
    } catch (error) {
      toast.error('Failed to add question')
    }
  }

  const handleEditQuestion = (question) => {
    setEditingQuestion(question)
    setQuestionForm({
      question_text: question.question_text,
      question_type: question.question_type,
      category: question.category || '',
      section: question.section || '',
      order_index: question.order_index || 0,
      required: question.required !== false,
      identity_modes: question.identity_modes || ['anonymous', 'conditional', 'identified'],
      sensitivity_level: question.sensitivity_level || 'medium',
      options: question.options || [],
    })
    setShowAddForm(true)
  }

  const handleDeleteQuestion = async (questionId) => {
    if (!window.confirm('Are you sure you want to delete this question?')) {
      return
    }
    try {
      // This would need a backend endpoint to delete questions
      toast.success('Question deletion coming soon')
    } catch (error) {
      toast.error('Failed to delete question')
    }
  }

  if (!isCEO && !isPNC) {
    return (
      <div className="p-6 text-center">
        <p className="text-ese-ink-medium text-lg">Access Denied</p>
        <p className="text-ese-ink-light mt-2">Admin access required</p>
      </div>
    )
  }

  if (loading) {
    return (
      <div className="p-6">
        <LoadingSkeleton type="list" count={5} />
      </div>
    )
  }

  return (
    <ErrorBoundary>
      <div className="p-6 max-w-6xl mx-auto space-y-6">
        <div className="flex justify-between items-center">
          <div>
            <button
              onClick={() => navigate(`/survey/${surveyId}`)}
              className="text-ese-lang-900 hover:text-ese-lang-700 mb-2 flex items-center"
            >
              ← Back to Survey
            </button>
            <h1 className="text-3xl font-bold text-ese-ink-navy">
              {survey?.title} - Questions
            </h1>
          </div>
          <button
            onClick={() => setShowAddForm(!showAddForm)}
            className="px-4 py-2 bg-ese-lang-900 text-white rounded-lg hover:bg-ese-lang-800"
          >
            {showAddForm ? 'Cancel' : '+ Add Question'}
          </button>
        </div>

        {/* Add/Edit Question Form */}
        {showAddForm && (
          <div className="bg-white rounded-lg shadow-md p-6 border border-ese-ink-light">
            <h2 className="text-xl font-semibold text-ese-ink-navy mb-4">
              {editingQuestion ? 'Edit Question' : 'Add Question'}
            </h2>
            <form onSubmit={handleAddQuestion} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-ese-ink-navy mb-1">
                  Question Text *
                </label>
                <textarea
                  value={questionForm.question_text}
                  onChange={(e) =>
                    setQuestionForm({ ...questionForm, question_text: e.target.value })
                  }
                  required
                  rows={3}
                  className="w-full px-4 py-2 border border-ese-ink-light rounded-lg focus:outline-none focus:ring-2 focus:ring-ese-lang-700"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-ese-ink-navy mb-1">
                    Question Type
                  </label>
                  <select
                    value={questionForm.question_type}
                    onChange={(e) =>
                      setQuestionForm({ ...questionForm, question_type: e.target.value })
                    }
                    className="w-full px-4 py-2 border border-ese-ink-light rounded-lg focus:outline-none focus:ring-2 focus:ring-ese-lang-700"
                  >
                    <option value="text">Text</option>
                    <option value="multiple_choice">Multiple Choice</option>
                    <option value="rating">Rating</option>
                    <option value="yes_no">Yes/No</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-ese-ink-navy mb-1">
                    Category
                  </label>
                  <input
                    type="text"
                    value={questionForm.category}
                    onChange={(e) =>
                      setQuestionForm({ ...questionForm, category: e.target.value })
                    }
                    className="w-full px-4 py-2 border border-ese-ink-light rounded-lg focus:outline-none focus:ring-2 focus:ring-ese-lang-700"
                  />
                </div>
              </div>

              <div className="flex items-center">
                <input
                  type="checkbox"
                  checked={questionForm.required}
                  onChange={(e) =>
                    setQuestionForm({ ...questionForm, required: e.target.checked })
                  }
                  className="mr-2"
                />
                <label className="text-sm text-ese-ink-navy">Required</label>
              </div>

              <div className="flex justify-end space-x-4">
                <button
                  type="button"
                  onClick={() => {
                    setShowAddForm(false)
                    setEditingQuestion(null)
                  }}
                  className="px-4 py-2 border border-ese-ink-light rounded-lg hover:bg-ese-lang-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-ese-lang-900 text-white rounded-lg hover:bg-ese-lang-800"
                >
                  {editingQuestion ? 'Update' : 'Add'} Question
                </button>
              </div>
            </form>
          </div>
        )}

        {/* Questions List */}
        <div className="bg-white rounded-lg shadow-md p-6 border border-ese-ink-light">
          <h2 className="text-xl font-semibold text-ese-ink-navy mb-4">
            Questions ({questions.length})
          </h2>
          {questions.length === 0 ? (
            <p className="text-ese-ink-medium text-center py-8">
              No questions yet. Add your first question above.
            </p>
          ) : (
            <div className="space-y-4">
              {questions.map((question, index) => (
                <div
                  key={question.id}
                  className="p-4 border border-ese-ink-light rounded-lg hover:bg-ese-lang-50"
                >
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <div className="flex items-center space-x-2 mb-2">
                        <span className="text-sm font-medium text-ese-ink-medium">
                          {index + 1}.
                        </span>
                        <span className="text-sm px-2 py-1 bg-ese-lang-100 text-ese-lang-900 rounded">
                          {question.question_type}
                        </span>
                        {question.required && (
                          <span className="text-xs text-red-500">*</span>
                        )}
                        {question.category && (
                          <span className="text-xs px-2 py-1 bg-ese-int-100 text-ese-int-900 rounded">
                            {question.category}
                          </span>
                        )}
                      </div>
                      <p className="text-ese-ink-navy font-medium">{question.question_text}</p>
                    </div>
                    <div className="flex space-x-2">
                      <button
                        onClick={() => handleEditQuestion(question)}
                        className="px-3 py-1 text-sm bg-ese-lang-900 text-white rounded hover:bg-ese-lang-800"
                      >
                        Edit
                      </button>
                      <button
                        onClick={() => handleDeleteQuestion(question.id)}
                        className="px-3 py-1 text-sm bg-red-600 text-white rounded hover:bg-red-700"
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </ErrorBoundary>
  )
}

export default SurveyQuestions
