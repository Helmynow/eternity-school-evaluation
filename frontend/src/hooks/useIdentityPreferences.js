import { useState, useCallback, useEffect } from 'react'
import { apiClient } from '../lib/api'
import { useAuth } from './useAuth'
import { useMutation } from './useAPI'
import toast from 'react-hot-toast'

export const useIdentityPreferences = (surveyId = null) => {
  const { user } = useAuth()
  const [preference, setPreference] = useState(null)
  const [loading, setLoading] = useState(false)

  // Fetch user's identity preference/status
  const fetchPreference = useCallback(async () => {
    if (!user?.email) return null

    setLoading(true)
    try {
      const params = surveyId ? { survey_id: surveyId } : {}
      const response = await apiClient.surveyIdentity.getStatus(user.email, params)
      setPreference(response.data)
      return response.data
    } catch (error) {
      // Preference might not exist yet, that's OK
      console.log('No preference found, using default')
      return null
    } finally {
      setLoading(false)
    }
  }, [user?.email, surveyId])

  // Set identity preference
  const setPreferenceMutation = useMutation(async (preferenceData) => {
    const response = await apiClient.surveyIdentity.setPreference({
      user_email: user?.email,
      survey_id: surveyId,
      ...preferenceData,
    })
    setPreference(response.data)
    toast.success('Identity preference saved')
    return response.data
  })

  // Auto-fetch on mount
  useEffect(() => {
    if (user?.email) {
      fetchPreference()
    }
  }, [user?.email, surveyId, fetchPreference])

  return {
    preference,
    loading,
    fetchPreference,
    setPreference: setPreferenceMutation.mutate,
    setPreferenceLoading: setPreferenceMutation.loading,
  }
}

export default useIdentityPreferences
