import { useEffect } from 'react'
import { useLocation } from 'react-router-dom'
import { getPerformanceSummary, trackNavigation } from '../../lib/performance'

/**
 * Performance Monitor Component
 * 
 * Tracks page load performance and component render times
 */
const PerformanceMonitor = () => {
  const location = useLocation()

  useEffect(() => {
    if (typeof performance === 'undefined') return undefined

    // Track route view duration
    const startTime = performance.now()

    return () => {
      const duration = performance.now() - startTime

      // Send to analytics
      trackNavigation(location.pathname, duration)
    }
  }, [location.pathname])

  useEffect(() => {
    // Get and log performance summary on mount
    const summary = getPerformanceSummary()
    if (summary) {
      console.log('Performance Summary:', summary)
    }
  }, [])

  return null // This component doesn't render anything
}

export default PerformanceMonitor
