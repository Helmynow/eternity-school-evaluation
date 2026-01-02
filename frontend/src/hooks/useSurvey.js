import { useState, useCallback } from 'react'
import { apiClient } from '../lib/api'
import { useAPI, useMutation } from './useAPI'
import toast from 'react-hot-toast'

export const useSurvey = (surveyId = null) => {
  const [surveys, setSurveys] = useState([])
  const [survey, setSurvey] = useState(null)
  const [questions, setQuestions] = useState([])
  const [analytics, setAnalytics] = useState(null)
  const [loading, setLoading] = useState(false)

  // Fetch all surveys
  const fetchSurveys = useCallback(async (filters = {}) => {
    setLoading(true)
    try {
      const response = await apiClient.survey.getAll(filters)
      setSurveys(response.data || [])
      return response.data
    } catch (error) {
      toast.error('Failed to load surveys')
      throw error
    } finally {
      setLoading(false)
    }
  }, [])

  // Fetch single survey
  const fetchSurvey = useCallback(async (id) => {
    setLoading(true)
    try {
      const response = await apiClient.survey.getById(id)
      setSurvey(response.data)
      return response.data
    } catch (error) {
      toast.error('Failed to load survey')
      throw error
    } finally {
      setLoading(false)
    }
  }, [])

  // Fetch survey questions
  const fetchQuestions = useCallback(async (id) => {
    setLoading(true)
    try {
      const response = await apiClient.survey.getQuestions(id)
      setQuestions(response.data || [])
      return response.data
    } catch (error) {
      toast.error('Failed to load questions')
      throw error
    } finally {
      setLoading(false)
    }
  }, [])

  // Fetch survey analytics
  const fetchAnalytics = useCallback(async (id) => {
    setLoading(true)
    try {
      const response = await apiClient.survey.getAnalytics(id)
      setAnalytics(response.data)
      return response.data
    } catch (error) {
      toast.error('Failed to load analytics')
      throw error
    } finally {
      setLoading(false)
    }
  }, [])

  // Create survey
  const createSurvey = useMutation(async (data) => {
    const response = await apiClient.survey.create(data)
    toast.success('Survey created successfully')
    return response.data
  })

  // Update survey
  const updateSurvey = useMutation(async ({ id, data }) => {
    const response = await apiClient.survey.update(id, data)
    toast.success('Survey updated successfully')
    return response.data
  })

  // Initialize hybrid identity session
  const initializeSession = useMutation(async (data) => {
    const response = await apiClient.hybridIdentity.initializeSession(data)
    return response.data
  })

  // Create survey session
  const createSurveySession = useMutation(async (params) => {
    const response = await apiClient.hybridIdentity.createSurveySession(params)
    return response.data
  })

  // Submit survey response
  const submitResponse = useMutation(async (data) => {
    const response = await apiClient.hybridIdentity.submitResponse(data)
    toast.success('Survey response submitted successfully')
    return response.data
  })

  return {
    surveys,
    survey,
    questions,
    analytics,
    loading,
    fetchSurveys,
    fetchSurvey,
    fetchQuestions,
    fetchAnalytics,
    createSurvey,
    updateSurvey,
    initializeSession,
    createSurveySession,
    submitResponse,
  }
}
