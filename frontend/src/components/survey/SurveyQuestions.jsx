import { useState, useEffect, useMemo, useRef } from 'react'
import { useParams, useNavigate, useSearchParams } from 'react-router-dom'
import { apiClient } from '../../lib/api'
import { useAuth } from '../../hooks/useAuth'
import { useSurvey } from '../../hooks/useSurvey'
import toast from 'react-hot-toast'
import ErrorBoundary from '../common/ErrorBoundary'
import LoadingSkeleton from '../common/LoadingSkeleton'

const SurveyQuestions = () => {
  const { surveyId } = useParams()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const { user, isCEO, isPNC, isDepartmentHead, isStaff } = useAuth()
  const { survey, questions, loading, fetchSurvey, fetchQuestions } = useSurvey(surveyId)
  const [editingQuestion, setEditingQuestion] = useState(null)
  const [showAddForm, setShowAddForm] = useState(false)
  const [questionForm, setQuestionForm] = useState({
    question_text: '',
    question_type: 'text',
    category: '',
    section: '',
    order_index: '',
    required: true,
    identity_modes: ['anonymous', 'conditional', 'partial', 'identified'],
    sensitivity_level: 'medium',
    options: [],
    optionsText: '',
  })
  const [templateLoading, setTemplateLoading] = useState(false)
  const [templateSurveys, setTemplateSurveys] = useState([])
  const [templateFilter, setTemplateFilter] = useState({ audience: 'all', termType: 'all', search: '' })
  const [importingTemplate, setImportingTemplate] = useState(false)
  const autoImportRan = useRef(false)
  const [orderedQuestions, setOrderedQuestions] = useState([])
  const [draggingId, setDraggingId] = useState(null)
  const [dragOverId, setDragOverId] = useState(null)
  const [reordering, setReordering] = useState(false)

  useEffect(() => {
    if (surveyId) {
      fetchSurvey(surveyId)
      fetchQuestions(surveyId)
    }
  }, [surveyId, fetchSurvey, fetchQuestions])

  useEffect(() => {
    setOrderedQuestions(questions || [])
  }, [questions])

  const loadStandardizedTemplates = async () => {
    setTemplateLoading(true)
    try {
      const response = await apiClient.surveyTemplates.getStandardized()
      setTemplateSurveys(response.data?.surveys || [])
    } catch (error) {
      toast.error('Failed to load standardized templates')
    } finally {
      setTemplateLoading(false)
    }
  }

  useEffect(() => {
    loadStandardizedTemplates()
  }, [])

  const handleAddQuestion = async (e) => {
    e.preventDefault()
    try {
      const optionsArray = questionForm.question_type === 'multiple_choice'
        ? questionForm.optionsText
            .split(',')
            .map((option) => option.trim())
            .filter((option) => option.length > 0)
        : []

      const parsedOrder =
        questionForm.order_index === '' ? null : Number(questionForm.order_index)
      const payload = {
        question_text: questionForm.question_text,
        question_type: questionForm.question_type,
        category: questionForm.category || null,
        section: questionForm.section || null,
        order_index: Number.isFinite(parsedOrder) ? parsedOrder : null,
        required: questionForm.required,
        identity_modes: questionForm.identity_modes,
        sensitivity_level: questionForm.sensitivity_level,
        options: optionsArray,
      }

      if (editingQuestion) {
        await apiClient.survey.updateQuestion(surveyId, editingQuestion.id, payload)
        toast.success('Question updated')
      } else {
        await apiClient.survey.createQuestion(surveyId, payload)
        toast.success('Question added')
      }

      await fetchQuestions(surveyId)
      setShowAddForm(false)
      setEditingQuestion(null)
      setQuestionForm({
        question_text: '',
        question_type: 'text',
        category: '',
        section: '',
        order_index: '',
        required: true,
        identity_modes: ['anonymous', 'conditional', 'partial', 'identified'],
        sensitivity_level: 'medium',
        options: [],
        optionsText: '',
      })
    } catch (error) {
      toast.error('Failed to save question')
    }
  }

  const handleEditQuestion = (question) => {
    setEditingQuestion(question)
    setQuestionForm({
      question_text: question.question_text,
      question_type: question.question_type,
      category: question.category || '',
      section: question.section || '',
      order_index: question.order_index ?? '',
      required: question.required !== false,
      identity_modes: question.identity_modes || ['anonymous', 'conditional', 'partial', 'identified'],
      sensitivity_level: question.sensitivity_level || 'medium',
      options: question.options || [],
      optionsText: (question.options || []).join(', '),
    })
    setShowAddForm(true)
  }

  const handleDeleteQuestion = async (questionId) => {
    if (!window.confirm('Are you sure you want to delete this question?')) {
      return
    }
    try {
      await apiClient.survey.deleteQuestion(surveyId, questionId)
      toast.success('Question deleted')
      await fetchQuestions(surveyId)
    } catch (error) {
      toast.error('Failed to delete question')
    }
  }

  const handleDragStart = (questionId) => {
    setDraggingId(questionId)
  }

  const handleDragEnter = (questionId) => {
    if (questionId !== draggingId) {
      setDragOverId(questionId)
    }
  }

  const handleDrop = async (dropId) => {
    if (!draggingId || draggingId === dropId) {
      setDraggingId(null)
      setDragOverId(null)
      return
    }

    const currentOrder = [...orderedQuestions]
    const fromIndex = currentOrder.findIndex((q) => q.id === draggingId)
    const toIndex = currentOrder.findIndex((q) => q.id === dropId)
    if (fromIndex === -1 || toIndex === -1) {
      setDraggingId(null)
      setDragOverId(null)
      return
    }

    const [moved] = currentOrder.splice(fromIndex, 1)
    currentOrder.splice(toIndex, 0, moved)
    setOrderedQuestions(currentOrder)
    setDraggingId(null)
    setDragOverId(null)

    const orders = currentOrder.map((question, index) => ({
      question_id: question.id,
      order_index: index + 1,
    }))

    setReordering(true)
    try {
      await apiClient.survey.reorderQuestions(surveyId, { orders })
      toast.success('Question order updated')
      await fetchQuestions(surveyId)
    } catch (error) {
      toast.error('Failed to reorder questions')
      await fetchQuestions(surveyId)
    } finally {
      setReordering(false)
    }
  }

  const templateTypeMap = {
    likert: 'rating',
    categorical: 'multiple_choice',
    open: 'text',
  }

  const mapTemplateQuestions = (template, sections = null) => {
    const mapped = []
    template.sections.forEach((section) => {
      if (sections && !sections.includes(section.name)) {
        return
      }
      section.questions.forEach((question) => {
        const questionType = templateTypeMap[question.type] || 'text'
        mapped.push({
          question_text: question.text,
          question_type: questionType,
          category: question.domain || section.name,
          section: question.section || section.name,
          required: question.type !== 'open',
          identity_modes: ['anonymous', 'conditional', 'partial', 'identified'],
          sensitivity_level: 'low',
          options: questionType === 'multiple_choice' ? question.options || [] : [],
        })
      })
    })
    return mapped
  }

  const handleImportTemplate = async ({ template, sections = null }) => {
    if (!surveyId) return
    const questionsToImport = mapTemplateQuestions(template, sections)
    if (questionsToImport.length === 0) {
      toast.error('No questions to import')
      return
    }
    setImportingTemplate(true)
    try {
      await apiClient.survey.bulkCreateQuestions(surveyId, { questions: questionsToImport })
      await fetchQuestions(surveyId)
      toast.success(`Imported ${questionsToImport.length} questions`)
    } catch (error) {
      toast.error('Failed to import template questions')
    } finally {
      setImportingTemplate(false)
    }
  }

  const filteredTemplates = useMemo(() => {
    const search = templateFilter.search.trim().toLowerCase()
    return templateSurveys.filter((template) => {
      const matchesAudience =
        templateFilter.audience === 'all' ||
        template.audience?.toLowerCase() === templateFilter.audience
      const matchesTerm =
        templateFilter.termType === 'all' ||
        template.term_type?.toLowerCase() === templateFilter.termType
      const matchesSearch = !search || template.name?.toLowerCase().includes(search)
      return matchesAudience && matchesTerm && matchesSearch
    })
  }, [templateSurveys, templateFilter])

  useEffect(() => {
    const templateMode = searchParams.get('template')
    const templateName = searchParams.get('name')
    if (!templateMode || templateMode !== 'standardized' || !templateName) return
    if (autoImportRan.current) return
    if (loading) return
    if (templateSurveys.length === 0) return
    if (questions.length > 0) return

    const match = templateSurveys.find(
      (template) => template.name?.toLowerCase() === templateName.toLowerCase()
    )
    if (!match) return

    autoImportRan.current = true
    handleImportTemplate({ template: match })
  }, [searchParams, templateSurveys, questions.length, loading])

  if (!isCEO && !isPNC && !isDepartmentHead && !isStaff) {
    return (
      <div className="p-6 text-center">
        <p className="text-ese-ink-medium text-lg">Access Denied</p>
        <p className="text-ese-ink-light mt-2">Staff access required</p>
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

        {/* Template Library */}
        <div className="bg-white rounded-lg shadow-md p-6 border border-ese-ink-light">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <div>
              <h2 className="text-xl font-semibold text-ese-ink-navy">Template Library</h2>
              <p className="text-sm text-ese-ink-medium mt-1">
                Mix and match sections from standardized templates to build a custom survey.
              </p>
            </div>
            <button
              onClick={loadStandardizedTemplates}
              disabled={templateLoading}
              className="px-4 py-2 border border-ese-ink-light rounded-lg hover:bg-ese-lang-50 disabled:opacity-50"
            >
              {templateLoading ? 'Refreshing...' : 'Refresh'}
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
            <div>
              <label className="block text-sm font-medium text-ese-ink-navy mb-1">
                Audience
              </label>
              <select
                value={templateFilter.audience}
                onChange={(e) => setTemplateFilter((prev) => ({ ...prev, audience: e.target.value }))}
                className="w-full px-3 py-2 border border-ese-ink-light rounded-lg focus:outline-none focus:ring-2 focus:ring-ese-lang-700"
              >
                <option value="all">All</option>
                <option value="parent">Parent</option>
                <option value="staff">Staff</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-ese-ink-navy mb-1">
                Term Type
              </label>
              <select
                value={templateFilter.termType}
                onChange={(e) => setTemplateFilter((prev) => ({ ...prev, termType: e.target.value }))}
                className="w-full px-3 py-2 border border-ese-ink-light rounded-lg focus:outline-none focus:ring-2 focus:ring-ese-lang-700"
              >
                <option value="all">All</option>
                <option value="core">Core</option>
                <option value="rotating">Rotating</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-ese-ink-navy mb-1">
                Search
              </label>
              <input
                type="text"
                value={templateFilter.search}
                onChange={(e) => setTemplateFilter((prev) => ({ ...prev, search: e.target.value }))}
                className="w-full px-3 py-2 border border-ese-ink-light rounded-lg focus:outline-none focus:ring-2 focus:ring-ese-lang-700"
                placeholder="Search templates"
              />
            </div>
          </div>

          {filteredTemplates.length === 0 ? (
            <p className="text-ese-ink-medium text-center py-6">No templates found.</p>
          ) : (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mt-6">
              {filteredTemplates.map((template) => (
                <div
                  key={template.name}
                  className="border border-ese-ink-light rounded-lg p-4 bg-ese-lang-50/30"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <h3 className="text-lg font-semibold text-ese-ink-navy">{template.name}</h3>
                      <p className="text-sm text-ese-ink-medium">
                        {template.audience} • {template.term_type}
                      </p>
                    </div>
                    <button
                      onClick={() => handleImportTemplate({ template })}
                      disabled={importingTemplate}
                      className="px-3 py-2 bg-ese-int-700 text-white rounded-lg hover:bg-ese-int-800 disabled:opacity-50"
                    >
                      Add All
                    </button>
                  </div>
                  <div className="mt-4 space-y-3">
                    {template.sections.map((section) => (
                      <div
                        key={section.name}
                        className="flex items-center justify-between bg-white border border-ese-ink-light rounded-lg p-3"
                      >
                        <div>
                          <p className="text-sm font-medium text-ese-ink-navy">{section.name}</p>
                          <p className="text-xs text-ese-ink-medium">
                            {section.questions.length} questions
                          </p>
                        </div>
                        <button
                          onClick={() => handleImportTemplate({ template, sections: [section.name] })}
                          disabled={importingTemplate}
                          className="px-3 py-1 text-sm border border-ese-ink-light rounded-lg hover:bg-ese-lang-50 disabled:opacity-50"
                        >
                          Add Section
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
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

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-ese-ink-navy mb-1">
                    Section
                  </label>
                  <input
                    type="text"
                    value={questionForm.section}
                    onChange={(e) =>
                      setQuestionForm({ ...questionForm, section: e.target.value })
                    }
                    className="w-full px-4 py-2 border border-ese-ink-light rounded-lg focus:outline-none focus:ring-2 focus:ring-ese-lang-700"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-ese-ink-navy mb-1">
                    Order
                  </label>
                  <input
                    type="number"
                    min="0"
                    value={questionForm.order_index}
                    onChange={(e) =>
                      setQuestionForm({ ...questionForm, order_index: e.target.value })
                    }
                    className="w-full px-4 py-2 border border-ese-ink-light rounded-lg focus:outline-none focus:ring-2 focus:ring-ese-lang-700"
                  />
                </div>
              </div>

              {questionForm.question_type === 'multiple_choice' && (
                <div>
                  <label className="block text-sm font-medium text-ese-ink-navy mb-1">
                    Options (comma separated)
                  </label>
                  <input
                    type="text"
                    value={questionForm.optionsText}
                    onChange={(e) =>
                      setQuestionForm({ ...questionForm, optionsText: e.target.value })
                    }
                    className="w-full px-4 py-2 border border-ese-ink-light rounded-lg focus:outline-none focus:ring-2 focus:ring-ese-lang-700"
                    placeholder="e.g. Strongly Disagree, Disagree, Neutral, Agree, Strongly Agree"
                  />
                </div>
              )}

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
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-xl font-semibold text-ese-ink-navy">
                Questions ({orderedQuestions.length})
              </h2>
              <p className="text-xs text-ese-ink-medium mt-1">
                Drag and drop questions to reorder them.
              </p>
            </div>
            {reordering && (
              <span className="text-xs text-ese-ink-medium">Saving order...</span>
            )}
          </div>
          {orderedQuestions.length === 0 ? (
            <p className="text-ese-ink-medium text-center py-8">
              No questions yet. Add your first question above.
            </p>
          ) : (
            <div className="space-y-4">
              {orderedQuestions.map((question, index) => (
                <div
                  key={question.id}
                  className={`p-4 border border-ese-ink-light rounded-lg bg-white hover:bg-ese-lang-50 transition ${
                    draggingId === question.id ? 'opacity-60' : ''
                  } ${
                    dragOverId === question.id ? 'border-ese-int-500 ring-1 ring-ese-int-200' : ''
                  }`}
                  draggable
                  onDragStart={() => handleDragStart(question.id)}
                  onDragEnter={() => handleDragEnter(question.id)}
                  onDragOver={(e) => e.preventDefault()}
                  onDrop={() => handleDrop(question.id)}
                  onDragEnd={() => {
                    setDraggingId(null)
                    setDragOverId(null)
                  }}
                >
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <div className="flex items-center space-x-2 mb-2">
                        <span className="text-sm text-ese-ink-light cursor-grab">⋮⋮</span>
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
