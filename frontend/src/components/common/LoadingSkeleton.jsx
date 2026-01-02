const LoadingSkeleton = ({ type = 'default', count = 1 }) => {
  const skeletons = Array.from({ length: count })

  if (type === 'card') {
    return (
      <>
        {skeletons.map((_, i) => (
          <div
            key={i}
            className="bg-white rounded-lg shadow-md p-6 border border-ese-ink-light animate-pulse"
          >
            <div className="h-6 bg-ese-ink-light rounded w-3/4 mb-4"></div>
            <div className="h-4 bg-ese-ink-light rounded w-full mb-2"></div>
            <div className="h-4 bg-ese-ink-light rounded w-5/6"></div>
          </div>
        ))}
      </>
    )
  }

  if (type === 'list') {
    return (
      <>
        {skeletons.map((_, i) => (
          <div
            key={i}
            className="flex items-center space-x-4 p-4 border-b border-ese-ink-light animate-pulse"
          >
            <div className="w-12 h-12 bg-ese-ink-light rounded-full"></div>
            <div className="flex-1">
              <div className="h-4 bg-ese-ink-light rounded w-1/4 mb-2"></div>
              <div className="h-3 bg-ese-ink-light rounded w-1/2"></div>
            </div>
          </div>
        ))}
      </>
    )
  }

  if (type === 'table') {
    return (
      <div className="animate-pulse">
        <div className="h-12 bg-ese-ink-light rounded mb-2"></div>
        {skeletons.map((_, i) => (
          <div key={i} className="h-16 bg-ese-ink-light rounded mb-2"></div>
        ))}
      </div>
    )
  }

  if (type === 'dashboard') {
    return (
      <div className="space-y-6 animate-pulse">
        <div className="h-8 bg-ese-ink-light rounded w-1/3"></div>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {skeletons.map((_, i) => (
            <div key={i} className="bg-white rounded-lg shadow-md p-6 border border-ese-ink-light">
              <div className="h-4 bg-ese-ink-light rounded w-1/2 mb-3"></div>
              <div className="h-8 bg-ese-ink-light rounded w-3/4"></div>
            </div>
          ))}
        </div>
        <div className="bg-white rounded-lg shadow-md p-6 border border-ese-ink-light">
          <div className="h-6 bg-ese-ink-light rounded w-1/4 mb-4"></div>
          <div className="h-64 bg-ese-ink-light rounded"></div>
        </div>
      </div>
    )
  }

  if (type === 'form') {
    return (
      <div className="space-y-6 animate-pulse">
        <div className="h-8 bg-ese-ink-light rounded w-1/2"></div>
        {skeletons.map((_, i) => (
          <div key={i} className="space-y-2">
            <div className="h-4 bg-ese-ink-light rounded w-1/4"></div>
            <div className="h-10 bg-ese-ink-light rounded w-full"></div>
          </div>
        ))}
      </div>
    )
  }

  // Default skeleton
  return (
    <>
      {skeletons.map((_, i) => (
        <div
          key={i}
          className="animate-pulse bg-ese-ink-light rounded h-4 w-full mb-2"
        ></div>
      ))}
    </>
  )
}

export const LoadingSpinner = ({ size = 'md', className = '' }) => {
  const sizeClasses = {
    sm: 'h-4 w-4',
    md: 'h-8 w-8',
    lg: 'h-12 w-12',
    xl: 'h-16 w-16',
  }

  return (
    <div className={`flex items-center justify-center ${className}`}>
      <div
        className={`animate-spin rounded-full border-b-2 border-ese-lang-900 ${sizeClasses[size]}`}
      ></div>
    </div>
  )
}

export const LoadingOverlay = ({ message = 'Loading...' }) => {
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-lg p-8 max-w-sm w-full mx-4">
        <LoadingSpinner size="lg" className="mx-auto mb-4" />
        <p className="text-center text-ese-ink-navy">{message}</p>
      </div>
    </div>
  )
}

export default LoadingSkeleton
