import { useState, useEffect, useRef } from 'react'
import { useIdentityPreferences } from '../../hooks/useIdentityPreferences'
import ErrorBoundary from '../common/ErrorBoundary'

const IDENTITY_MODES = [
  {
    id: 'anonymous',
    name: 'Anonymous',
    description: 'Your responses will be completely anonymous. No identifying information will be stored.',
    icon: '/assets/icons/anonymous.png',
    privacyLevel: 'maximum',
  },
  {
    id: 'conditional',
    name: 'Conditional',
    description: 'Your identity can be revealed under specific conditions (e.g., if you request it, or after a certain period).',
    icon: '/assets/icons/conditional.png',
    privacyLevel: 'high',
  },
  {
    id: 'identified',
    name: 'Identified',
    description: 'Your responses will be linked to your identity. This allows for follow-up and personalized feedback.',
    icon: '/assets/icons/identified.png',
    privacyLevel: 'low',
  },
]

const normalizeMode = (mode) => (
  IDENTITY_MODES.some((option) => option.id === mode) ? mode : null
)

const IdentityModeSelector = ({ onSelect, initialMode = null, surveyId = null }) => {
  const normalizedInitialMode = normalizeMode(initialMode)
  const { preference, fetchPreference } = useIdentityPreferences(surveyId)
  const [selectedMode, setSelectedMode] = useState(normalizedInitialMode)
  const modeRefs = useRef({})
  const modeIds = IDENTITY_MODES.map((mode) => mode.id)

  // Load saved preference if available
  useEffect(() => {
    if (surveyId && !normalizedInitialMode) {
      fetchPreference()
    }
  }, [surveyId, fetchPreference, normalizedInitialMode])

  useEffect(() => {
    const nextMode = normalizedInitialMode || normalizeMode(preference?.current_mode)
    if (nextMode) {
      setSelectedMode((prev) => (prev === nextMode ? prev : nextMode))
    }
  }, [normalizedInitialMode, preference?.current_mode])

  const handleSelect = (mode) => {
    if (mode === selectedMode) return
    setSelectedMode(mode)
    onSelect?.(mode)
  }

  const handleKeyDown = (event, index) => {
    const { key } = event
    if (!['ArrowRight', 'ArrowDown', 'ArrowLeft', 'ArrowUp', 'Home', 'End'].includes(key)) {
      return
    }

    event.preventDefault()
    const lastIndex = modeIds.length - 1
    let nextIndex = index

    if (key === 'ArrowRight' || key === 'ArrowDown') {
      nextIndex = index === lastIndex ? 0 : index + 1
    } else if (key === 'ArrowLeft' || key === 'ArrowUp') {
      nextIndex = index === 0 ? lastIndex : index - 1
    } else if (key === 'Home') {
      nextIndex = 0
    } else if (key === 'End') {
      nextIndex = lastIndex
    }

    const nextMode = modeIds[nextIndex]
    handleSelect(nextMode)
    requestAnimationFrame(() => modeRefs.current[nextMode]?.focus())
  }

  return (
    <ErrorBoundary>
      <div className="space-y-4">
        <div className="mb-6">
          <h2 className="text-2xl font-bold text-ese-ink-navy mb-2">Choose Your Privacy Mode</h2>
          <p id="identity-mode-help" className="text-ese-ink-medium">
            Select how you want your responses to be handled. You can change this later.
          </p>
        </div>

        <div
          className="grid grid-cols-1 md:grid-cols-3 gap-4"
          role="radiogroup"
          aria-describedby="identity-mode-help"
        >
          {IDENTITY_MODES.map((mode, index) => {
            const descriptionId = `identity-mode-${mode.id}-desc`
            const badgeId = `identity-mode-${mode.id}-badge`

            return (
              <button
                key={mode.id}
                type="button"
                ref={(el) => {
                  modeRefs.current[mode.id] = el
                }}
                onClick={() => handleSelect(mode.id)}
                onKeyDown={(event) => handleKeyDown(event, index)}
                role="radio"
                aria-checked={selectedMode === mode.id}
                aria-describedby={`${descriptionId} ${badgeId}`}
                tabIndex={
                  selectedMode
                    ? (selectedMode === mode.id ? 0 : -1)
                    : (index === 0 ? 0 : -1)
                }
                className={`p-6 rounded-lg border-2 transition-all text-left focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ese-lang-700 focus-visible:ring-offset-2 focus-visible:ring-offset-white ${
                  selectedMode === mode.id
                    ? 'border-ese-lang-900 bg-ese-lang-50'
                    : 'border-ese-ink-light hover:border-ese-lang-700 hover:bg-ese-lang-50'
                }`}
              >
                <div className="flex items-center mb-3">
                  <img src={mode.icon} alt={mode.name} className="w-8 h-8 mr-3" onError={(e) => { e.target.style.display = 'none'; e.target.parentElement.insertAdjacentHTML('afterbegin', '<span className="text-3xl mr-3">🔒</span>') }} />
                  <h3 className="text-xl font-semibold text-ese-ink-navy">{mode.name}</h3>
                </div>
                <p id={descriptionId} className="text-ese-ink-medium text-sm">{mode.description}</p>
                <div className="mt-3">
                  <span
                    id={badgeId}
                    className={`text-xs px-2 py-1 rounded ${
                      mode.privacyLevel === 'maximum'
                        ? 'bg-green-100 text-green-800'
                        : mode.privacyLevel === 'high'
                        ? 'bg-blue-100 text-blue-800'
                        : 'bg-yellow-100 text-yellow-800'
                    }`}
                  >
                    {mode.privacyLevel} privacy
                  </span>
                </div>
              </button>
            )
          })}
        </div>

        {selectedMode && (
          <div className="mt-6 p-4 bg-ese-lang-50 rounded-lg border border-ese-lang-200" role="status" aria-live="polite">
            <p className="text-sm text-ese-ink-navy">
              <strong>Selected:</strong> {IDENTITY_MODES.find((m) => m.id === selectedMode)?.name}
            </p>
            <p className="text-xs text-ese-ink-medium mt-1">
              You can proceed with the survey using this privacy mode.
            </p>
          </div>
        )}
      </div>
    </ErrorBoundary>
  )
}

export default IdentityModeSelector
