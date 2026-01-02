/**
 * Sentry Error Tracking Configuration
 * 
 * Initialize Sentry for error tracking and performance monitoring.
 * Set VITE_SENTRY_DSN in your .env file to enable Sentry.
 */

import * as Sentry from '@sentry/react'
import { BrowserTracing } from '@sentry/tracing'

// Do not hardcode DSNs in source. Configure via VITE_SENTRY_DSN at build time.
const SENTRY_DSN = import.meta.env.VITE_SENTRY_DSN || ''
const ENVIRONMENT = import.meta.env.MODE || 'development'

export const initSentry = () => {
  if (!SENTRY_DSN) {
    console.log('Sentry DSN not configured. Error tracking disabled.')
    return
  }

  Sentry.init({
    dsn: SENTRY_DSN,
    environment: ENVIRONMENT,
    integrations: [
      new BrowserTracing({
        // Set tracing origins
        tracingOrigins: ['localhost', /^\//],
      }),
    ],
    // Performance Monitoring
    tracesSampleRate: ENVIRONMENT === 'production' ? 0.1 : 1.0, // 10% in prod, 100% in dev
    // Session Replay (optional)
    replaysSessionSampleRate: ENVIRONMENT === 'production' ? 0.1 : 1.0,
    replaysOnErrorSampleRate: 1.0,
    // Release tracking
    release: import.meta.env.VITE_APP_VERSION || '1.0.0',
    // Filter out common non-critical errors
    beforeSend(event, hint) {
      // Filter out network errors that are expected
      if (event.exception) {
        const error = hint.originalException
        if (error?.message?.includes('Network Error') && error?.config?.url?.includes('/cycles')) {
          return null // Don't send expected 404s
        }
      }
      return event
    },
    // Ignore specific errors
    ignoreErrors: [
      'ResizeObserver loop limit exceeded',
      'Non-Error promise rejection captured',
      'Network request failed',
    ],
  })

  console.log('Sentry initialized for error tracking')
}

// Export Sentry components for use in ErrorBoundary
export { Sentry }
export const SentryErrorBoundary = Sentry.withErrorBoundary
