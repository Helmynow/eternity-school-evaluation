import { useState, useCallback } from 'react'
import { apiClient } from '../lib/api'
import { useMutation } from './useAPI'
import toast from 'react-hot-toast'

export const useIntegration = () => {
  const [evaluationBridge, setEvaluationBridge] = useState(null)
  const [loading, setLoading] = useState(false)

  // Fetch evaluation bridge
  const fetchEvaluationBridge = useCallback(async () => {
    setLoading(true)
    try {
      const response = await apiClient.integration.getEvaluationBridge()
      setEvaluationBridge(response.data)
      return response.data
    } catch (error) {
      toast.error('Failed to load evaluation bridge')
      throw error
    } finally {
      setLoading(false)
    }
  }, [])

  // Setup HR integration
  const setupHR = useMutation(async (config) => {
    const response = await apiClient.integration.setupHR(config)
    toast.success('HR integration setup successfully')
    return response.data
  })

  // Sync staff
  const syncStaff = useMutation(async (staffData = []) => {
    const response = await apiClient.integration.syncStaff(staffData)
    toast.success('Staff sync completed')
    return response.data
  })

  // Sync evaluation
  const syncEvaluation = useMutation(async (evaluationData = {}) => {
    const response = await apiClient.integration.syncEvaluation(evaluationData)
    toast.success('Evaluation sync completed')
    return response.data
  })

  return {
    evaluationBridge,
    loading,
    fetchEvaluationBridge,
    setupHR,
    syncStaff,
    syncEvaluation,
  }
}
