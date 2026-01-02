import React from 'react'
import { useNavigate } from 'react-router-dom'

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false, error: null, errorInfo: null }
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error }
  }

  componentDidCatch(error, errorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo)
    this.setState({
      error,
      errorInfo,
    })
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null, errorInfo: null })
  }

  render() {
    if (this.state.hasError) {
      const { fallback, showDetails = false } = this.props

      if (fallback) {
        return fallback(this.state.error, this.handleReset)
      }

      return (
        <div className="min-h-[400px] flex items-center justify-center p-6">
          <div className="max-w-2xl w-full bg-white rounded-lg shadow-md p-8 border border-red-200">
            <div className="text-center">
              <div className="mb-4">
                <img src="/assets/icons/warning.png" alt="Error" className="w-16 h-16 mx-auto" onError={(e) => { e.target.style.display = 'none'; e.target.parentElement.innerHTML = '<div className="text-6xl mb-4">⚠️</div>' }} />
              </div>
              <h2 className="text-2xl font-bold text-ese-ink-navy mb-2">
                Something went wrong
              </h2>
              <p className="text-ese-ink-medium mb-6">
                We encountered an unexpected error. Please try refreshing the page.
              </p>

              {showDetails && this.state.error && (
                <details className="mt-4 text-left bg-ese-ink-offwhite p-4 rounded-lg">
                  <summary className="cursor-pointer font-medium text-ese-ink-navy mb-2">
                    Error Details
                  </summary>
                  <pre className="text-xs text-ese-ink-medium overflow-auto">
                    {this.state.error.toString()}
                    {this.state.errorInfo?.componentStack}
                  </pre>
                </details>
              )}

              <div className="flex justify-center space-x-4 mt-6">
                <button
                  onClick={this.handleReset}
                  className="px-6 py-2 bg-ese-lang-900 text-white rounded-lg hover:bg-ese-lang-800 transition-colors"
                >
                  Try Again
                </button>
                <button
                  onClick={() => window.location.reload()}
                  className="px-6 py-2 bg-ese-ink-light text-ese-ink-navy rounded-lg hover:bg-ese-ink-medium transition-colors"
                >
                  Refresh Page
                </button>
              </div>
            </div>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}

// Hook-based error boundary wrapper for functional components
export const withErrorBoundary = (Component, errorBoundaryProps = {}) => {
  return (props) => (
    <ErrorBoundary {...errorBoundaryProps}>
      <Component {...props} />
    </ErrorBoundary>
  )
}

export default ErrorBoundary
