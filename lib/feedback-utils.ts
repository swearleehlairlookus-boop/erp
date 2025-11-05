/**
 * Feedback and Validation Utilities
 * Provides common feedback patterns and validation helpers
 */

export interface FeedbackMessage {
  type: 'success' | 'error' | 'warning' | 'info'
  title?: string
  message: string
  duration?: number
}

export interface ValidationResult {
  isValid: boolean
  errors: string[]
  warnings: string[]
}

/**
 * Creates a standardized feedback message
 */
export function createFeedback(
  type: FeedbackMessage['type'],
  message: string,
  title?: string,
  duration = 5000
): FeedbackMessage {
  return {
    type,
    title,
    message,
    duration
  }
}

/**
 * Creates a success feedback message
 */
export function createSuccessFeedback(message: string, title = 'Success'): FeedbackMessage {
  return createFeedback('success', message, title)
}

/**
 * Creates an error feedback message
 */
export function createErrorFeedback(message: string, title = 'Error'): FeedbackMessage {
  return createFeedback('error', message, title, 8000)
}

/**
 * Creates a warning feedback message
 */
export function createWarningFeedback(message: string, title = 'Warning'): FeedbackMessage {
  return createFeedback('warning', message, title, 6000)
}

/**
 * Creates an info feedback message
 */
export function createInfoFeedback(message: string, title = 'Information'): FeedbackMessage {
  return createFeedback('info', message, title)
}

/**
 * Validates patient data and returns validation result
 */
export function validatePatientData(data: Record<string, any>): ValidationResult {
  const errors: string[] = []
  const warnings: string[] = []

  // Required field validation
  const requiredFields = ['firstName', 'lastName', 'dateOfBirth', 'phoneNumber']
  
  requiredFields.forEach(field => {
    if (!data[field] || data[field].toString().trim() === '') {
      errors.push(`${field.replace(/([A-Z])/g, ' $1').toLowerCase()} is required`)
    }
  })

  // Email validation
  if (data.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(data.email)) {
    errors.push('Please enter a valid email address')
  }

  // Phone number validation (basic)
  if (data.phoneNumber && !/^[\d\s\+\-\(\)]+$/.test(data.phoneNumber)) {
    errors.push('Please enter a valid phone number')
  }

  // Date of birth validation
  if (data.dateOfBirth) {
    const dob = new Date(data.dateOfBirth)
    const today = new Date()
    const age = today.getFullYear() - dob.getFullYear()
    
    if (isNaN(dob.getTime())) {
      errors.push('Please enter a valid date of birth')
    } else if (dob > today) {
      errors.push('Date of birth cannot be in the future')
    } else if (age > 120) {
      warnings.push('Please verify the date of birth - age appears unusually high')
    }
  }

  return {
    isValid: errors.length === 0,
    errors,
    warnings
  }
}

/**
 * Formats validation errors for display
 */
export function formatValidationErrors(errors: string[]): string {
  if (errors.length === 0) return ''
  if (errors.length === 1) return errors[0]
  
  return `Please fix the following issues:\n• ${errors.join('\n• ')}`
}

/**
 * Debounce utility for form validation
 */
export function debounce<T extends (...args: any[]) => any>(
  func: T,
  delay: number
): (...args: Parameters<T>) => void {
  let timeoutId: NodeJS.Timeout
  
  return (...args: Parameters<T>) => {
    clearTimeout(timeoutId)
    timeoutId = setTimeout(() => func(...args), delay)
  }
}

/**
 * Creates a standardized loading state message
 */
export function createLoadingFeedback(action: string): FeedbackMessage {
  return createFeedback('info', `${action}...`, 'Please wait')
}

/**
 * Form submission feedback helper
 */
export function handleFormSubmissionFeedback(
  success: boolean,
  successMessage: string,
  errorMessage: string
): FeedbackMessage {
  return success 
    ? createSuccessFeedback(successMessage)
    : createErrorFeedback(errorMessage)
}