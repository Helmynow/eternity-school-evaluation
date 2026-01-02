/**
 * API Response Validation Utilities
 * 
 * Provides validation functions for API responses to ensure data integrity
 * before using responses in components.
 */

/**
 * Validate survey response structure
 */
export const validateSurvey = (survey) => {
  if (!survey) return { valid: false, error: 'Survey is null or undefined' }
  
  const errors = []
  
  if (!survey.id && survey.id !== 0) {
    errors.push('Survey missing id')
  }
  
  if (!survey.title || typeof survey.title !== 'string') {
    errors.push('Survey missing or invalid title')
  }
  
  if (survey.status && !['draft', 'active', 'closed'].includes(survey.status)) {
    errors.push(`Invalid survey status: ${survey.status}`)
  }
  
  return {
    valid: errors.length === 0,
    errors,
    data: survey,
  }
}

/**
 * Validate survey question structure
 */
export const validateSurveyQuestion = (question) => {
  if (!question) return { valid: false, error: 'Question is null or undefined' }
  
  const errors = []
  
  if (!question.id && question.id !== 0) {
    errors.push('Question missing id')
  }
  
  if (!question.question_text || typeof question.question_text !== 'string') {
    errors.push('Question missing or invalid question_text')
  }
  
  if (!question.question_type || typeof question.question_type !== 'string') {
    errors.push('Question missing or invalid question_type')
  }
  
  if (question.required !== undefined && typeof question.required !== 'boolean') {
    errors.push('Question required field must be boolean')
  }
  
  return {
    valid: errors.length === 0,
    errors,
    data: question,
  }
}

/**
 * Validate survey response structure
 */
export const validateSurveyResponse = (response) => {
  if (!response) return { valid: false, error: 'Response is null or undefined' }
  
  const errors = []
  
  if (!response.survey_id && response.survey_id !== 0) {
    errors.push('Response missing survey_id')
  }
  
  if (!response.question_id && response.question_id !== 0) {
    errors.push('Response missing question_id')
  }
  
  if (!response.response_text && !response.response_value) {
    errors.push('Response missing both response_text and response_value')
  }
  
  return {
    valid: errors.length === 0,
    errors,
    data: response,
  }
}

/**
 * Validate array of surveys
 */
export const validateSurveys = (surveys) => {
  if (!Array.isArray(surveys)) {
    return { valid: false, error: 'Surveys must be an array' }
  }
  
  const validated = surveys.map(validateSurvey)
  const invalid = validated.filter(v => !v.valid)
  
  return {
    valid: invalid.length === 0,
    errors: invalid.flatMap(v => v.errors),
    data: surveys,
    invalidCount: invalid.length,
  }
}

/**
 * Validate array of questions
 */
export const validateQuestions = (questions) => {
  if (!Array.isArray(questions)) {
    return { valid: false, error: 'Questions must be an array' }
  }
  
  const validated = questions.map(validateSurveyQuestion)
  const invalid = validated.filter(v => !v.valid)
  
  return {
    valid: invalid.length === 0,
    errors: invalid.flatMap(v => v.errors),
    data: questions,
    invalidCount: invalid.length,
  }
}

/**
 * Validate API response wrapper
 * Ensures response has expected structure
 */
export const validateAPIResponse = (response, expectedStructure = {}) => {
  if (!response) {
    return { valid: false, error: 'Response is null or undefined' }
  }
  
  const errors = []
  
  // Check if response has data property (common in axios responses)
  const data = response.data !== undefined ? response.data : response
  
  // Validate expected structure
  for (const [key, validator] of Object.entries(expectedStructure)) {
    if (!(key in data)) {
      errors.push(`Missing required field: ${key}`)
    } else if (validator && typeof validator === 'function') {
      const validation = validator(data[key])
      if (!validation.valid) {
        errors.push(...validation.errors)
      }
    }
  }
  
  return {
    valid: errors.length === 0,
    errors,
    data,
  }
}

/**
 * Safe data extraction with validation
 */
export const safeExtract = (response, fallback = null) => {
  try {
    const data = response?.data !== undefined ? response.data : response
    return data || fallback
  } catch (error) {
    console.error('Error extracting data:', error)
    return fallback
  }
}

/**
 * Validate and extract array from response
 */
export const safeExtractArray = (response, fallback = []) => {
  try {
    const data = response?.data !== undefined ? response.data : response
    if (Array.isArray(data)) {
      return data
    }
    if (data && Array.isArray(data.items)) {
      return data.items
    }
    return fallback
  } catch (error) {
    console.error('Error extracting array:', error)
    return fallback
  }
}

/**
 * Validate and extract object from response
 */
export const safeExtractObject = (response, fallback = {}) => {
  try {
    const data = response?.data !== undefined ? response.data : response
    if (data && typeof data === 'object' && !Array.isArray(data)) {
      return data
    }
    return fallback
  } catch (error) {
    console.error('Error extracting object:', error)
    return fallback
  }
}

export default {
  validateSurvey,
  validateSurveyQuestion,
  validateSurveyResponse,
  validateSurveys,
  validateQuestions,
  validateAPIResponse,
  safeExtract,
  safeExtractArray,
  safeExtractObject,
}
