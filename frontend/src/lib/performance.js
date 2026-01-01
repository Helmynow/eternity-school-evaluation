/**
 * Performance Monitoring Utilities
 * 
 * Tracks Web Vitals and custom performance metrics
 */

import { onCLS, onFCP, onLCP, onTTFB, onINP } from 'web-vitals'

/**
 * Send performance metrics to analytics endpoint
 */
const sendToAnalytics = (metric) => {
  // Send to your analytics endpoint
  const endpoint = '/api/v2/analytics/performance'
  
  // In production, send to your backend
  if (import.meta.env.PROD) {
    fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name: metric.name,
        value: metric.value,
        id: metric.id,
        delta: metric.delta,
        rating: metric.rating,
        navigationType: metric.navigationType,
        url: window.location.href,
        timestamp: Date.now(),
      }),
      keepalive: true, // Send even if page is unloading
    }).catch(console.error)
  } else {
    // Log in development
    console.log('Performance Metric:', {
      name: metric.name,
      value: metric.value,
      rating: metric.rating,
    })
  }

  // Also send to Sentry if available
  if (window.Sentry) {
    window.Sentry.addBreadcrumb({
      category: 'performance',
      message: `${metric.name}: ${metric.value}ms (${metric.rating})`,
      level: metric.rating === 'good' ? 'info' : 'warning',
      data: {
        value: metric.value,
        delta: metric.delta,
        id: metric.id,
      },
    })
  }
}

/**
 * Initialize Web Vitals monitoring
 */
export const initWebVitals = () => {
  // Core Web Vitals
  onCLS(sendToAnalytics) // Cumulative Layout Shift
  onFCP(sendToAnalytics) // First Contentful Paint
  onLCP(sendToAnalytics) // Largest Contentful Paint
  onTTFB(sendToAnalytics) // Time to First Byte
  onINP(sendToAnalytics) // Interaction to Next Paint (replaces FID)

  console.log('Web Vitals monitoring initialized')
}

/**
 * Measure custom performance metric
 */
export const measurePerformance = (name, fn) => {
  if (typeof window !== 'undefined' && window.performance && window.performance.mark) {
    const startMark = `${name}-start`
    const endMark = `${name}-end`
    const measureName = name

    window.performance.mark(startMark)
    const result = fn()
    
    // Handle async functions
    if (result instanceof Promise) {
      return result.then((value) => {
        window.performance.mark(endMark)
        window.performance.measure(measureName, startMark, endMark)
        const measure = window.performance.getEntriesByName(measureName)[0]
        sendToAnalytics({
          name: measureName,
          value: measure.duration,
          rating: measure.duration < 100 ? 'good' : measure.duration < 300 ? 'needs-improvement' : 'poor',
        })
        return value
      })
    } else {
      window.performance.mark(endMark)
      window.performance.measure(measureName, startMark, endMark)
      const measure = window.performance.getEntriesByName(measureName)[0]
      sendToAnalytics({
        name: measureName,
        value: measure.duration,
        rating: measure.duration < 100 ? 'good' : measure.duration < 300 ? 'needs-improvement' : 'poor',
      })
      return result
    }
  }
  
  return fn()
}

/**
 * Track API request performance
 */
export const trackAPIRequest = (url, duration, status) => {
  sendToAnalytics({
    name: 'api-request',
    value: duration,
    rating: duration < 200 ? 'good' : duration < 500 ? 'needs-improvement' : 'poor',
    url,
    status,
  })
}

/**
 * Track route navigation duration
 */
export const trackNavigation = (path, duration) => {
  sendToAnalytics({
    name: 'navigation',
    value: duration,
    rating: duration < 300 ? 'good' : duration < 1000 ? 'needs-improvement' : 'poor',
    path,
  })
}

// Make trackAPIRequest available globally for API interceptor
if (typeof window !== 'undefined') {
  window.trackAPIRequest = trackAPIRequest
}

/**
 * Track component render time
 */
export const trackComponentRender = (componentName, renderTime) => {
  sendToAnalytics({
    name: 'component-render',
    value: renderTime,
    rating: renderTime < 16 ? 'good' : renderTime < 50 ? 'needs-improvement' : 'poor',
    component: componentName,
  })
}

/**
 * Get performance summary
 */
export const getPerformanceSummary = () => {
  if (typeof window === 'undefined' || !window.performance) {
    return null
  }

  const navigation = window.performance.getEntriesByType('navigation')[0]
  const paint = window.performance.getEntriesByType('paint')
  
  return {
    dns: navigation?.domainLookupEnd - navigation?.domainLookupStart,
    tcp: navigation?.connectEnd - navigation?.connectStart,
    request: navigation?.responseStart - navigation?.requestStart,
    response: navigation?.responseEnd - navigation?.responseStart,
    dom: navigation?.domContentLoadedEventEnd - navigation?.domContentLoadedEventStart,
    load: navigation?.loadEventEnd - navigation?.loadEventStart,
    fcp: paint?.find(p => p.name === 'first-contentful-paint')?.startTime,
  }
}

export default {
  initWebVitals,
  measurePerformance,
  trackAPIRequest,
  trackNavigation,
  trackComponentRender,
  getPerformanceSummary,
}
