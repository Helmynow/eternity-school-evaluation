import { useState, useEffect, useCallback, useRef } from 'react'
import { apiClient } from '../lib/api'

export const useAPI = (endpoint, options = {}) => {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const hasFetched = useRef(false)
  const isFetching = useRef(false)

  const fetchData = useCallback(async () => {
    if (!endpoint || isFetching.current) return
    
    isFetching.current = true
    setLoading(true)
    setError(null)
    
    try {
      const response = await endpoint()
      setData(response.data)
      setError(null)
      hasFetched.current = true
    } catch (err) {
      // Only set error if it's a real error (not just null/empty response)
      if (err?.response?.status !== 404 && err?.response?.status !== 200) {
        setError(err)
      } else {
        // 404 or empty response is OK - just set data to null
        setData(null)
        setError(null)
      }
      hasFetched.current = true
    } finally {
      setLoading(false)
      isFetching.current = false
    }
  }, [endpoint])

  useEffect(() => {
    if (options.autoFetch !== false && !hasFetched.current && !isFetching.current) {
      fetchData()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []) // Only run once on mount - endpoint function reference is stable

  const refetch = useCallback(() => {
    hasFetched.current = false
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

