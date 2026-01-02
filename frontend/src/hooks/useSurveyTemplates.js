import { useState, useCallback } from 'react'
import { apiClient } from '../lib/api'
import { useAPI, useMutation } from './useAPI'
import toast from 'react-hot-toast'

export const useSurveyTemplates = () => {
  const [comprehensiveTemplate, setComprehensiveTemplate] = useState(null)
  const [sectionTemplate, setSectionTemplate] = useState(null)
  const [loading, setLoading] = useState(false)

  // Fetch comprehensive template
  const fetchComprehensive = useCallback(async () => {
    setLoading(true)
    try {
      const response = await apiClient.surveyTemplates.getComprehensive()
      setComprehensiveTemplate(response.data)
      return response.data
    } catch (error) {
      toast.error('Failed to load comprehensive template')
      throw error
    } finally {
      setLoading(false)
    }
  }, [])

  // Fetch section template
  const fetchSection = useCallback(async (category) => {
    setLoading(true)
    try {
      const response = await apiClient.surveyTemplates.getSection(category)
      setSectionTemplate(response.data)
      return response.data
    } catch (error) {
      toast.error(`Failed to load template for category: ${category}`)
      throw error
    } finally {
      setLoading(false)
    }
  }, [])

  return {
    comprehensiveTemplate,
    sectionTemplate,
    loading,
    fetchComprehensive,
    fetchSection,
  }
}

export default useSurveyTemplates
