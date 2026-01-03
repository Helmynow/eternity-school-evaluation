import { useState } from 'react'
import { apiClient } from '../../lib/api'
import { useAuth } from '../../hooks/useAuth'
import toast from 'react-hot-toast'
import ErrorBoundary from '../common/ErrorBoundary'

const REVEAL_METHODS = [
  {
    id: 'full',
    name: 'Full Reveal',
    description: 'Reveal complete identity information',
    icon: '/assets/icons/eye.svg',
  },
  {
    id: 'partial_role',
    name: 'Partial - Role Only',
    description: 'Reveal only your role/title',
    icon: '/assets/icons/user.svg',
  },
  {
    id: 'partial_department',
    name: 'Partial - Department Only',
    description: 'Reveal only your department',
    icon: '/assets/icons/users-group.svg',
  },
  {
    id: 'gradual',
    name: 'Gradual Reveal',
    description: 'Reveal information over time',
    icon: '/assets/icons/time.svg',
  },
  {
    id: 'consent_based',
    name: 'Consent-Based Reveal',
    description: 'Reveal only with explicit consent',
    icon: '/assets/icons/team.svg',
  },
]

const IdentityReveal = ({ surveyId, onRevealComplete }) => {
  const { user } = useAuth()
  const [selectedMethod, setSelectedMethod] = useState(null)
  const [conditions, setConditions] = useState({})
  const [processing, setProcessing] = useState(false)

  const handleReveal = async () => {
    if (!selectedMethod) {
      toast.error('Please select a reveal method')
      return
    }

    setProcessing(true)
    try {
      const result = await apiClient.hybridIdentity.processReveal(
        user?.email,
        selectedMethod,
        Object.keys(conditions).length > 0 ? conditions : null
      )

      toast.success('Identity reveal processed successfully')
      if (onRevealComplete) {
        onRevealComplete(result.data)
      }
    } catch (error) {
      toast.error('Failed to process identity reveal')
      console.error('Error processing reveal:', error)
    } finally {
      setProcessing(false)
    }
  }

  return (
    <ErrorBoundary>
      <div className="p-6 max-w-4xl mx-auto space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-ese-ink-navy mb-2">Identity Reveal</h2>
        <p className="text-ese-ink-medium">
          Choose how you want to reveal your identity for this survey.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {REVEAL_METHODS.map((method) => (
          <button
            key={method.id}
            onClick={() => setSelectedMethod(method.id)}
            className={`p-6 rounded-lg border-2 transition-all text-left ${
              selectedMethod === method.id
                ? 'border-ese-lang-900 bg-ese-lang-50'
                : 'border-ese-ink-light hover:border-ese-lang-700 hover:bg-ese-lang-50'
            }`}
          >
            <div className="flex items-center mb-3">
              <img src={method.icon} alt={method.name} className="w-8 h-8 mr-3" onError={(e) => { e.target.style.display = 'none'; e.target.parentElement.insertAdjacentHTML('afterbegin', '<span className="text-3xl mr-3">🔓</span>') }} />
              <h3 className="text-xl font-semibold text-ese-ink-navy">{method.name}</h3>
            </div>
            <p className="text-ese-ink-medium text-sm">{method.description}</p>
          </button>
        ))}
      </div>

      {selectedMethod === 'gradual' && (
        <div className="bg-ese-lang-50 p-4 rounded-lg border border-ese-lang-200">
          <label className="block text-sm font-medium text-ese-ink-navy mb-2">
            Reveal Date
          </label>
          <input
            type="date"
            value={conditions.reveal_date || ''}
            onChange={(e) =>
              setConditions({ ...conditions, reveal_date: e.target.value })
            }
            className="w-full p-2 border border-ese-ink-light rounded-lg"
          />
        </div>
      )}

      {selectedMethod === 'consent_based' && (
        <div className="bg-ese-lang-50 p-4 rounded-lg border border-ese-lang-200">
          <label className="flex items-center">
            <input
              type="checkbox"
              checked={conditions.consent_confirmed || false}
              onChange={(e) =>
                setConditions({
                  ...conditions,
                  consent_confirmed: e.target.checked,
                })
              }
              className="mr-2"
            />
            <span className="text-sm text-ese-ink-navy">
              I consent to revealing my identity
            </span>
          </label>
        </div>
      )}

      <div className="flex justify-end space-x-4">
        <button
          onClick={handleReveal}
          disabled={!selectedMethod || processing}
          className="px-6 py-2 bg-ese-lang-900 text-white rounded-lg hover:bg-ese-lang-800 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {processing ? 'Processing...' : 'Process Reveal'}
        </button>
      </div>
      </div>
    </ErrorBoundary>
  )
}

export default IdentityReveal
