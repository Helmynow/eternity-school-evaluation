import { useState, useEffect, useCallback } from 'react'
import { apiClient } from '../lib/api'

export const useAPI = (endpoint, options = {}) => {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const fetchData = useCallback(async () => {
    if (!endpoint) return
    
    setLoading(true)
    setError(null)
    
    try {
      const response = await endpoint()
      setData(response.data)
      setError(null)
    } catch (err) {
      setError(err)
      setData(null)
    } finally {
      setLoading(false)
    }
  }, [endpoint])

  useEffect(() => {
    if (options.autoFetch !== false) {
      fetchData()
    }
  }, [fetchData, options.autoFetch])

  const refetch = useCallback(() => {
    fetchData()
  }, [fetchData])

  return { data, loading, error, refetch }
}

// Hook for mutations (POST, PUT, DELETE)
export const useMutation = (mutationFn) => {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [data, setData] = useState(null)

  const mutate = useCallback(async (variables, options = {}) => {
    setLoading(true)
    setError(null)
    
    try {
      const response = await mutationFn(variables)
      setData(response.data)
      
      if (options.onSuccess) {
        options.onSuccess(response.data)
      }
      
      return response.data
    } catch (err) {
      setError(err)
      
      if (options.onError) {
        options.onError(err)
      }
      
      throw err
    } finally {
      setLoading(false)
    }
  }, [mutationFn])

  return { mutate, loading, error, data }
}

