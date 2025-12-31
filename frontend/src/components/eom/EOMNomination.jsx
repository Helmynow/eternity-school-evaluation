import { useState, useEffect } from 'react'
import { useAPI, useMutation } from '../../hooks/useAPI'
import { apiClient } from '../../lib/api'
import { useAuth } from '../../hooks/useAuth'
import toast from 'react-hot-toast'

const EOM_CATEGORIES = [
  {
    id: 'outstanding_leadership',
    name: 'Outstanding Leadership',
    description: 'Leads projects successfully, models professionalism and ethics, volunteers for high-stakes responsibilities',
    example: 'Led digital attendance reform, trained peers on new process',
    icon: '👑',
  },
  {
    id: 'team_spirit',
    name: 'Team Spirit',
    description: 'Uplifts team morale, resolves conflict through positive action, consistently helps peers beyond duty',
    example: 'Organised peer tutoring among teachers and eased inter-department tension',
    icon: '🤝',
  },
  {
    id: 'innovation',
    name: 'Innovation',
    description: 'Suggests or implements solutions with impact, creates or improves systems/processes, shares tools or strategies',
    example: 'Developed a student feedback dashboard for the lesson plan',
    icon: '💡',
  },
  {
    id: 'rising_star',
    name: 'Rising Star',
    description: 'New to the school (first 6 months), quickly adapts and exceeds expectations, shows eagerness and initiative',
    example: 'Reworked an entire classroom setup within two weeks of hire',
    icon: '⭐',
  },
  {
    id: 'service_excellence',
    name: 'Service Excellence',
    description: 'Punctual, dependable, consistent output, maintains high standard across months, manages responsibilities with minimal supervision',
    example: 'Zero late marks, submits reports early, no task reminders needed',
    icon: '🏆',
  },
]

const EOMNomination = ({ mode = 'nominate' }) => {
  const { role, isCEO, isPNC, isDepartmentHead } = useAuth()
  const [selectedCategory, setSelectedCategory] = useState(null)
  const [nomineeEmail, setNomineeEmail] = useState('')
  const [reason, setReason] = useState('')
  const [eligibleNominees, setEligibleNominees] = useState([])
  const [currentCycle, setCurrentCycle] = useState(null)
  const [validationResult, setValidationResult] = useState(null)

  // Get current cycle
  const { data: currentCycleData } = useAPI(
    () => apiClient.cycles.getCurrent(),
    { autoFetch: true }
  )

  useEffect(() => {
    if (currentCycleData) {
      setCurrentCycle(currentCycleData)
      loadEligibleNominees(currentCycleData.id)
    }
  }, [currentCycleData])

  const loadEligibleNominees = async (cycleId) => {
    try {
      const response = await apiClient.eom.getEligibleNominees(cycleId)
      setEligibleNominees(response.data || [])
    } catch (error) {
      console.error('Failed to load eligible nominees:', error)
    }
  }

  const { mutate: validateNomination, loading: validating } = useMutation(
    apiClient.eom.validateNomination
  )

  const { mutate: submitNomination, loading: submitting } = useMutation(
    apiClient.eom.submitNomination
  )

  const handleValidate = async () => {
    if (!selectedCategory || !nomineeEmail || !reason.trim()) {
      toast.error('Please fill in all fields')
      return
    }

    try {
      const result = await validateNomination({
        eom_cycle_id: currentCycle?.id,
        nominee_email: nomineeEmail,
        category: selectedCategory,
        reason: reason,
        nominated_by: 'current_user', // Will be set from auth
      })
      setValidationResult(result)
      
      if (result.is_valid) {
        toast.success('Nomination is valid!')
      } else {
        toast.error(`Validation failed: ${result.errors?.join(', ') || 'Unknown error'}`)
      }
    } catch (error) {
      toast.error('Validation failed')
    }
  }

  const handleSubmit = async () => {
    if (!selectedCategory || !nomineeEmail || !reason.trim()) {
      toast.error('Please fill in all fields')
      return
    }

    if (!validationResult?.is_valid) {
      toast.error('Please validate nomination first')
      return
    }

    try {
      await submitNomination({
        eom_cycle_id: currentCycle?.id,
        nominee_email: nomineeEmail,
        category: selectedCategory,
        reason: reason,
        nominated_by: 'current_user',
      })
      toast.success('Nomination submitted successfully!')
      
      // Reset form
      setSelectedCategory(null)
      setNomineeEmail('')
      setReason('')
      setValidationResult(null)
    } catch (error) {
      toast.error('Failed to submit nomination')
    }
  }

  // Voting mode
  if (mode === 'vote') {
    return (
      <div className="space-y-6">
        <h1 className="text-3xl font-heading font-bold text-ese-lang-900">EOM Voting</h1>
        <div className="ese-card">
          <p className="text-ese-ink-blue">Voting interface coming soon...</p>
        </div>
      </div>
    )
  }

  // Check permissions
  if (!isCEO && !isPNC && !isDepartmentHead) {
    return (
      <div className="ese-card">
        <p className="text-ese-ink-blue">You do not have permission to nominate. Only Department Heads, P&C, and CEO can nominate.</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-heading font-bold text-ese-lang-900">EOM Nomination</h1>
        <p className="text-ese-ink-blue mt-1">Nominate an employee for Employee of the Month</p>
      </div>

      {!currentCycle && (
        <div className="ese-card">
          <p className="text-ese-ink-blue">No active EOM cycle. Please wait for the next cycle to open.</p>
        </div>
      )}

      {currentCycle && (
        <>
          {/* Category Selection */}
          <div className="ese-card">
            <h2 className="text-xl font-heading font-semibold text-ese-ink-navy mb-4">
              Select Category
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {EOM_CATEGORIES.map((category) => (
                <button
                  key={category.id}
                  onClick={() => setSelectedCategory(category.id)}
                  className={`
                    p-4 rounded-lg border-2 transition-all text-left
                    ${selectedCategory === category.id
                      ? 'border-ese-accent-mustard bg-ese-accent-mustard/10'
                      : 'border-ese-accent-beige hover:border-ese-accent-olive'
                    }
                  `}
                >
                  <div className="flex items-center gap-3 mb-2">
                    <span className="text-3xl">{category.icon}</span>
                    <span className="font-semibold text-ese-ink-navy">{category.name}</span>
                  </div>
                  <p className="text-sm text-ese-ink-blue">{category.description}</p>
                  <p className="text-xs text-ese-ink-blue mt-2 italic">
                    Example: {category.example}
                  </p>
                </button>
              ))}
            </div>
          </div>

          {/* Nomination Form */}
          {selectedCategory && (
            <div className="ese-card">
              <h2 className="text-xl font-heading font-semibold text-ese-ink-navy mb-4">
                Nomination Details
              </h2>

              <div className="space-y-4">
                {/* Nominee Selection */}
                <div>
                  <label className="block text-sm font-medium text-ese-ink-navy mb-2">
                    Nominee
                  </label>
                  <select
                    value={nomineeEmail}
                    onChange={(e) => setNomineeEmail(e.target.value)}
                    className="w-full px-4 py-3 border border-ese-accent-beige rounded-lg focus:ring-2 focus:ring-ese-lang-500 focus:border-ese-lang-500 outline-none"
                  >
                    <option value="">Select a nominee...</option>
                    {eligibleNominees.map((nominee) => (
                      <option key={nominee.email} value={nominee.email}>
                        {nominee.name} ({nominee.email}) - {nominee.title}
                      </option>
                    ))}
                  </select>
                  {eligibleNominees.length === 0 && (
                    <p className="text-sm text-ese-ink-blue mt-1">
                      Loading eligible nominees...
                    </p>
                  )}
                </div>

                {/* Reason */}
                <div>
                  <label className="block text-sm font-medium text-ese-ink-navy mb-2">
                    Reason for Nomination
                  </label>
                  <textarea
                    value={reason}
                    onChange={(e) => setReason(e.target.value)}
                    rows={6}
                    className="w-full px-4 py-3 border border-ese-accent-beige rounded-lg focus:ring-2 focus:ring-ese-lang-500 focus:border-ese-lang-500 outline-none"
                    placeholder="Describe why this employee deserves recognition in this category. Include specific examples and evidence..."
                  />
                  <p className="text-xs text-ese-ink-blue mt-1">
                    {reason.length} characters (minimum 50 recommended)
                  </p>
                </div>

                {/* Validation Result */}
                {validationResult && (
                  <div className={`
                    p-4 rounded-lg
                    ${validationResult.is_valid
                      ? 'bg-ese-int-50 border border-ese-int-300'
                      : 'bg-ese-accent-terracotta/10 border border-ese-accent-terracotta'
                    }
                  `}>
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-xl">
                        {validationResult.is_valid ? '✓' : '✗'}
                      </span>
                      <span className="font-semibold text-ese-ink-navy">
                        {validationResult.is_valid ? 'Valid' : 'Invalid'}
                      </span>
                    </div>
                    {validationResult.errors && validationResult.errors.length > 0 && (
                      <ul className="list-disc list-inside text-sm text-ese-ink-blue mt-2">
                        {validationResult.errors.map((error, idx) => (
                          <li key={idx}>{error}</li>
                        ))}
                      </ul>
                    )}
                  </div>
                )}

                {/* Actions */}
                <div className="flex gap-4">
                  <button
                    onClick={handleValidate}
                    disabled={validating || !nomineeEmail || !reason.trim()}
                    className="ese-button-secondary disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {validating ? 'Validating...' : 'Validate Nomination'}
                  </button>
                  <button
                    onClick={handleSubmit}
                    disabled={submitting || !validationResult?.is_valid}
                    className="ese-button-primary disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {submitting ? 'Submitting...' : 'Submit Nomination'}
                  </button>
                </div>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}

export default EOMNomination

