import { useState } from 'react'

/**
 * Unified error handling hook
 * Processes backend error responses and converts them to user-friendly messages
 */
export const useErrorHandler = () => {
  const [error, setError] = useState('')

  /**
   * Handle API error responses
   * @param err - Axios error object
   * @param setErrorCallback - Optional callback to set error (uses internal state if not provided)
   */
  const handleError = (err: any, setErrorCallback?: (msg: string) => void) => {
    const setErrorFn = setErrorCallback || setError
    const errorDetail = err.response?.data?.detail

    // Handle array type error details
    if (Array.isArray(errorDetail)) {
      // Find first error that is not "Field required"
      const meaningfulError = errorDetail.find((e: any) => e.msg !== 'Field required')

      if (meaningfulError) {
        const errorMsg = meaningfulError.msg || meaningfulError.type || JSON.stringify(meaningfulError)
        setErrorFn(errorMsg.replace('Value error, ', ''))
      } else if (errorDetail.length > 0) {
        // If all are "Field required", check if cookie is missing
        const lastError = errorDetail[errorDetail.length - 1]
        if (lastError.loc?.includes('cookie') && lastError.loc?.includes('refresh_token')) {
          setErrorFn('认证失败，请重新登录')
        } else {
          const errorMsg = lastError.msg || lastError.type || JSON.stringify(lastError)
          setErrorFn(errorMsg.replace('Value error, ', '') || '操作失败')
        }
      } else {
        setErrorFn('操作失败')
      }
    }
    // Handle object type error details
    else if (typeof errorDetail === 'object' && errorDetail.msg) {
      setErrorFn(errorDetail.msg.replace('Value error, ', ''))
    }
    // Handle string type error details
    else if (typeof errorDetail === 'string') {
      setErrorFn(errorDetail.replace('Value error, ', ''))
    }
    // Default error message
    else {
      setErrorFn('操作失败')
    }
  }

  const clearError = () => {
    setError('')
  }

  return { error, handleError, clearError }
}