/**
 * Centralized Error Message Utilities
 * 
 * Provides consistent, user-friendly error messages throughout the application
 */

/**
 * Get user-friendly error message from API error
 */
export const getErrorMessage = (error, context = '') => {
  if (!error) return 'An unexpected error occurred'

  // Handle axios errors
  if (error.response) {
    const { status, data } = error.response
    const detail = data?.detail || data?.message || data?.error

    switch (status) {
      case 400:
        return detail || `Invalid request${context ? ` for ${context}` : ''}. Please check your input and try again.`
      
      case 401:
        return 'Your session has expired. Please log in again.'
      
      case 403:
        return `You don't have permission to ${context || 'perform this action'}. Please contact an administrator if you believe this is an error.`
      
      case 404:
        return detail || `${context || 'Resource'} not found. It may have been deleted or you may not have access.`
      
      case 422:
        return detail || `Validation error${context ? ` for ${context}` : ''}. Please check your input and try again.`
      
      case 429:
        return 'Too many requests. Please wait a moment and try again.'
      
      case 500:
        return 'Server error. Our team has been notified. Please try again later.'
      
      case 502:
      case 503:
      case 504:
        return 'Service temporarily unavailable. Please try again in a few moments.'
      
      default:
        return detail || `Error ${status}: ${error.message || 'An error occurred'}`
    }
  }

  // Handle network errors
  if (error.request) {
    if (error.code === 'ECONNABORTED') {
      return 'Request timed out. Please check your connection and try again.'
    }
    if (error.code === 'ERR_NETWORK') {
      return 'Network error. Please check your internet connection and try again.'
    }
    return 'Unable to connect to server. Please check your connection and try again.'
  }

  // Handle other errors
  if (error.message) {
    // Provide context-aware messages for common errors
    if (error.message.includes('timeout')) {
      return 'Request timed out. Please try again.'
    }
    if (error.message.includes('network')) {
      return 'Network error. Please check your connection.'
    }
    return error.message
  }

  return 'An unexpected error occurred. Please try again.'
}

/**
 * Get specific error message for survey operations
 */
export const getSurveyErrorMessage = (error, operation = '') => {
  const baseMessage = getErrorMessage(error, `survey ${operation}`)
  
  // Handle common "not found" cases even when error isn't an axios error
  const messageText = typeof error?.message === 'string' ? error.message.toLowerCase() : ''
  if (messageText.includes('not found')) {
    if (operation.includes('submit')) {
      return 'Survey or question not found. The survey may have been closed or removed.'
    }
    if (operation.includes('load')) {
      return 'Survey not found. It may have been deleted or you may not have access.'
    }
  }

  if (error.response?.status === 404) {
    if (operation.includes('submit')) {
      return 'Survey or question not found. The survey may have been closed or removed.'
    }
    if (operation.includes('load')) {
      return 'Survey not found. It may have been deleted or you may not have access.'
    }
  }
  
  if (error.response?.status === 422 && operation.includes('submit')) {
    return 'Some required questions are missing or invalid. Please review your answers and try again.'
  }
  
  return baseMessage
}

/**
 * Get specific error message for authentication operations
 */
export const getAuthErrorMessage = (error) => {
  if (error.response?.status === 401) {
    return 'Invalid email or password. Please try again.'
  }
  
  if (error.response?.status === 403) {
    return 'Your account does not have access to this resource.'
  }
  
  return getErrorMessage(error, 'authentication')
}

/**
 * Get specific error message for admin operations
 */
export const getAdminErrorMessage = (error, operation = '') => {
  if (error.response?.status === 403) {
    return `Admin access required to ${operation || 'perform this action'}. Please contact your administrator.`
  }
  
  return getErrorMessage(error, `admin ${operation}`)
}

/**
 * Get specific error message for API operations
 */
export const getAPIErrorMessage = (error, endpoint = '') => {
  const context = endpoint ? `API endpoint (${endpoint})` : 'API request'
  return getErrorMessage(error, context)
}

/**
 * Format validation errors for display
 */
export const formatValidationErrors = (errors) => {
  if (!errors || errors.length === 0) {
    return 'Validation failed'
  }
  
  if (errors.length === 1) {
    return errors[0]
  }
  
  return `Multiple errors: ${errors.join('; ')}`
}

/**
 * Get user-friendly success message
 */
export const getSuccessMessage = (operation, resource = '') => {
  const messages = {
    create: `${resource || 'Item'} created successfully`,
    update: `${resource || 'Item'} updated successfully`,
    delete: `${resource || 'Item'} deleted successfully`,
    submit: `${resource || 'Response'} submitted successfully`,
    save: `${resource || 'Changes'} saved successfully`,
    load: `${resource || 'Data'} loaded successfully`,
  }
  
  return messages[operation] || `${operation} completed successfully`
}

/**
 * Safely extract a value from API response, with fallback
 */
export const safeExtract = (response, fallback = null) => {
  if (!response) return fallback
  if (typeof response === 'object' && 'data' in response) {
    return response.data || fallback
  }
  return response || fallback
}

/**
 * Safely extract an array from API response, with fallback
 */
export const safeExtractArray = (response, fallback = []) => {
  if (!response) return fallback
  if (Array.isArray(response)) return response
  if (typeof response === 'object' && 'data' in response) {
    return Array.isArray(response.data) ? response.data : fallback
  }
  return fallback
}

export default {
  getErrorMessage,
  getSurveyErrorMessage,
  getAuthErrorMessage,
  getAdminErrorMessage,
  getAPIErrorMessage,
  formatValidationErrors,
  getSuccessMessage,
  safeExtract,
  safeExtractArray,
}
