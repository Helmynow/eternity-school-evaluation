import { useState, useEffect, useCallback } from 'react'
import { useAPI, useMutation } from '../../hooks/useAPI'
import { apiClient } from '../../lib/api'
import { useAuth } from '../../hooks/useAuth'
import toast from 'react-hot-toast'
import SmartNomineeSearch from './SmartNomineeSearch'

const EOM_CATEGORIES = [
  {
    id: 'outstanding_leadership',
    name: 'Outstanding Leadership',
    description: 'Leads projects successfully, models professionalism and ethics, volunteers for high-stakes responsibilities',
    example: 'Led digital attendance reform, trained peers on new process',
    icon: '/assets/icons/leadership.png',
  },
  {
    id: 'team_spirit',
    name: 'Team Spirit',
    description: 'Uplifts team morale, resolves conflict through positive action, consistently helps peers beyond duty',
    example: 'Organised peer tutoring among teachers and eased inter-department tension',
    icon: '/assets/icons/team_spirit.png',
  },
  {
    id: 'innovation',
    name: 'Innovation',
    description: 'Suggests or implements solutions with impact, creates or improves systems/processes, shares tools or strategies',
    example: 'Developed a student feedback dashboard for the lesson plan',
    icon: '/assets/icons/innovation.png',
  },
  {
    id: 'rising_star',
    name: 'Rising Star',
    description: 'New to the school (first 6 months), quickly adapts and exceeds expectations, shows eagerness and initiative',
    example: 'Reworked an entire classroom setup within two weeks of hire',
    icon: '/assets/icons/rising_star.png',
  },
  {
    id: 'service_excellence',
    name: 'Service Excellence',
    description: 'Punctual, dependable, consistent output, maintains high standard across months, manages responsibilities with minimal supervision',
    example: 'Zero late marks, submits reports early, no task reminders needed',
    icon: '/assets/icons/trophy.png',
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
  const [suggestedCategory, setSuggestedCategory] = useState(null)
  const [suggestingCategory, setSuggestingCategory] = useState(false)

  // Get current cycle - use useCallback to stabilize the endpoint function
  const getCurrentCycle = useCallback(() => apiClient.cycles.getCurrent(), [])
  const { data: currentCycleData, loading: cycleLoading } = useAPI(
    getCurrentCycle,
    { autoFetch: true }
  )

  useEffect(() => {
    if (currentCycleData && currentCycleData.id) {
      setCurrentCycle(currentCycleData)
      loadEligibleNominees(currentCycleData.id)
    } else if (!cycleLoading && currentCycleData === null) {
      // No cycle available - handle gracefully
      setCurrentCycle(null)
    }
  }, [currentCycleData, cycleLoading])

  const loadEligibleNominees = async (cycleId) => {
    try {
      const response = await apiClient.eom.getEligibleNominees(cycleId)
      setEligibleNominees(response.data || [])
    } catch (error) {
      console.error('Failed to load eligible nominees:', error)
    }
  }

  // Debounced category suggestion
  useEffect(() => {
    if (!reason.trim() || reason.length < 20) {
      setSuggestedCategory(null)
      return
    }

    const timeoutId = setTimeout(async () => {
      setSuggestingCategory(true)
      try {
        // Get nominee role if available
        const nominee = eligibleNominees.find(n => n.email === nomineeEmail)
        const nomineeRole = nominee?.role_title || null

        const response = await apiClient.eom.suggestCategory(reason, nomineeRole)
        if (response.data && response.data) {
          setSuggestedCategory(response.data)
        }
      } catch (error) {
        console.error('Failed to suggest category:', error)
      } finally {
        setSuggestingCategory(false)
      }
    }, 1000) // Wait 1 second after user stops typing

    return () => clearTimeout(timeoutId)
  }, [reason, nomineeEmail, eligibleNominees])

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
  const [nominations, setNominations] = useState([])
  const [selectedNomination, setSelectedNomination] = useState(null)
  const [votingLoading, setVotingLoading] = useState(false)
  const [showObjectionModal, setShowObjectionModal] = useState(false)
  const [objectionReason, setObjectionReason] = useState('')
  const [objectingNomination, setObjectingNomination] = useState(null)
  const [voteSearchQuery, setVoteSearchQuery] = useState('')
  const [voteCategoryFilter, setVoteCategoryFilter] = useState('')

  useEffect(() => {
    if (mode === 'vote' && currentCycle) {
      loadNominations()
    }
  }, [mode, currentCycle])

  const loadNominations = async () => {
    if (!currentCycle) return
    try {
      const response = await apiClient.eom.getNominations(currentCycle.id)
      setNominations(response.data || [])
    } catch (error) {
      console.error('Failed to load nominations:', error)
    }
  }

  const handleVote = async (nominationId) => {
    if (!currentCycle || !user?.email) return
    
    setVotingLoading(true)
    try {
      await apiClient.eom.submitVote({
        eom_cycle_id: currentCycle.id,
        nominee_email: nominations.find(n => n.id === nominationId)?.nominee_email,
        voter_email: user.email
      })
      toast.success('Vote submitted successfully!')
      loadNominations()
    } catch (error) {
      toast.error('Failed to submit vote')
    } finally {
      setVotingLoading(false)
    }
  }

  const handleObject = (nomination) => {
    setObjectingNomination(nomination)
    setObjectionReason('')
    setShowObjectionModal(true)
  }

  const submitObjection = async () => {
    if (!objectionReason.trim()) {
      toast.error('Please provide a reason for your objection')
      return
    }

    try {
      const response = await fetch('http://localhost:8000/api/v2/objections', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          eom_nominee_id: objectingNomination.id,
          objector_email: user?.email,
          reason: objectionReason
        })
      })

      if (response.ok) {
        toast.success('Objection submitted successfully')
        setShowObjectionModal(false)
        setObjectionReason('')
        setObjectingNomination(null)
      } else {
        toast.error('Failed to submit objection')
      }
    } catch (error) {
      toast.error('Failed to submit objection')
    }
  }

  if (mode === 'vote') {
    // Filter nominations based on search query
    const filteredNominations = nominations.filter(nom => {
      // Search filter
      if (voteSearchQuery.trim()) {
        const query = voteSearchQuery.toLowerCase()
        const matchesSearch = 
          (nom.nominee_name || nom.nominee_email || '').toLowerCase().includes(query) ||
          (nom.nomination_reason || '').toLowerCase().includes(query) ||
          (nom.nominated_by || '').toLowerCase().includes(query) ||
          (nom.category || '').toLowerCase().includes(query)
        if (!matchesSearch) return false
      }
      
      // Category filter
      if (voteCategoryFilter && nom.category !== voteCategoryFilter) {
        return false
      }
      
      return true
    })

    // Group filtered nominations by category
    const nominationsByCategory = filteredNominations.reduce((acc, nom) => {
      const cat = nom.category || 'other'
      if (!acc[cat]) acc[cat] = []
      acc[cat].push(nom)
      return acc
    }, {})

    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-heading font-bold text-ese-lang-900">EOM Voting</h1>
          <p className="text-ese-ink-blue mt-1">Vote for your Employee of the Month</p>
        </div>

        {!currentCycle ? (
          <div className="ese-card">
            <p className="text-ese-ink-blue">No active EOM cycle. Please wait for the next cycle to open.</p>
          </div>
        ) : nominations.length === 0 ? (
          <div className="ese-card">
            <p className="text-ese-ink-blue">No nominations available for voting yet.</p>
          </div>
        ) : (
          <div className="space-y-6">
            {/* Smart Search and Filter Bar */}
            <div className="ese-card">
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-ese-ink-navy mb-2 flex items-center gap-2">
                    <img src="/assets/icons/search.png" alt="Search" className="w-5 h-5" />
                    Search Nominations
                  </label>
                  <div className="relative">
                    <input
                      type="text"
                      value={voteSearchQuery}
                      onChange={(e) => setVoteSearchQuery(e.target.value)}
                      placeholder="Search by nominee name, reason, category, or nominator..."
                      className="w-full px-4 py-3 pl-10 border border-ese-accent-beige rounded-lg focus:ring-2 focus:ring-ese-lang-500 focus:border-ese-lang-500 outline-none"
                    />
                    <div className="absolute left-3 top-1/2 transform -translate-y-1/2">
                      <svg className="w-5 h-5 text-ese-ink-blue" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                      </svg>
                    </div>
                    {voteSearchQuery && (
                      <button
                        onClick={() => setVoteSearchQuery('')}
                        className="absolute right-3 top-1/2 transform -translate-y-1/2 text-ese-ink-blue hover:text-ese-ink-navy"
                      >
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      </button>
                    )}
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-ese-ink-navy mb-2">
                    Filter by Category
                  </label>
                  <div className="flex flex-wrap gap-2">
                    <button
                      onClick={() => setVoteCategoryFilter('')}
                      className={`px-4 py-2 rounded-lg text-sm transition-colors ${
                        !voteCategoryFilter
                          ? 'bg-ese-accent-mustard text-white'
                          : 'bg-ese-ink-offwhite text-ese-ink-navy hover:bg-ese-accent-beige'
                      }`}
                    >
                      All Categories
                    </button>
                    {EOM_CATEGORIES.map((cat) => (
                      <button
                        key={cat.id}
                        onClick={() => setVoteCategoryFilter(cat.id)}
                        className={`px-4 py-2 rounded-lg text-sm transition-colors flex items-center gap-2 ${
                          voteCategoryFilter === cat.id
                            ? 'bg-ese-accent-mustard text-white'
                            : 'bg-ese-ink-offwhite text-ese-ink-navy hover:bg-ese-accent-beige'
                        }`}
                      >
                        <img src={cat.icon} alt={cat.name} className="w-5 h-5" onError={(e) => e.target.style.display = 'none'} />
                        {cat.name}
                      </button>
                    ))}
                  </div>
                </div>

                {(voteSearchQuery || voteCategoryFilter) && (
                  <div className="flex items-center justify-between p-3 bg-ese-lang-50 rounded-lg">
                    <p className="text-sm text-ese-ink-navy">
                      Showing {filteredNominations.length} of {nominations.length} nominations
                    </p>
                    <button
                      onClick={() => {
                        setVoteSearchQuery('')
                        setVoteCategoryFilter('')
                      }}
                      className="text-sm text-ese-ink-blue hover:text-ese-ink-navy underline"
                    >
                      Clear all filters
                    </button>
                  </div>
                )}
              </div>
            </div>

            {filteredNominations.length === 0 ? (
              <div className="ese-card">
                <p className="text-ese-ink-blue text-center py-8">
                  No nominations match your search criteria. Try adjusting your filters.
                </p>
              </div>
            ) : (
              <div className="space-y-6">
            {Object.entries(nominationsByCategory).map(([category, categoryNominations]) => (
              <div key={category} className="ese-card">
                <h2 className="text-xl font-heading font-semibold text-ese-ink-navy mb-4 capitalize">
                  {category.replace('_', ' ')} Category
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {categoryNominations.map((nomination) => (
                    <div
                      key={nomination.id}
                      className={`
                        p-4 rounded-lg border-2 transition-all
                        ${selectedNomination === nomination.id
                          ? 'border-ese-accent-mustard bg-ese-accent-mustard/10'
                          : 'border-ese-accent-beige hover:border-ese-accent-olive'
                        }
                      `}
                    >
                      <div className="flex justify-between items-start mb-3">
                        <div>
                          <h3 className="font-semibold text-ese-ink-navy">{nomination.nominee_name || nomination.nominee_email}</h3>
                          <p className="text-sm text-ese-ink-blue">Nominated by: {nomination.nominated_by}</p>
                        </div>
                        <span className="px-2 py-1 rounded-full text-xs bg-ese-int-300 text-ese-int-900">
                          {nomination.votes_received || 0} votes
                        </span>
                      </div>
                      
                      <p className="text-sm text-ese-ink-navy mb-4">{nomination.nomination_reason}</p>
                      
                      <div className="flex gap-2">
                        <button
                          onClick={() => handleVote(nomination.id)}
                          disabled={votingLoading}
                          className="flex-1 ese-button-primary disabled:opacity-50"
                        >
                          {votingLoading ? 'Submitting...' : 'Vote'}
                        </button>
                        <button
                          onClick={() => handleObject(nomination)}
                          className="px-4 py-2 bg-ese-accent-terracotta text-white rounded-lg hover:opacity-90 text-sm flex items-center justify-center"
                          title="Object to this nomination"
                        >
                          <img src="/assets/icons/warning_alert.png" alt="Object" className="w-5 h-5" onError={(e) => { e.target.src = "/assets/icons/waening_alert.png"; }} />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
              </div>
            )}
          </div>
        )}

        {/* Objection Modal */}
        {showObjectionModal && objectingNomination && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
              <h2 className="text-2xl font-heading font-bold text-ese-ink-navy mb-4">
                Submit Objection
              </h2>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-ese-ink-navy mb-1">
                    Nominee
                  </label>
                  <p className="text-ese-ink-blue">{objectingNomination.nominee_name || objectingNomination.nominee_email}</p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-ese-ink-navy mb-1">
                    Reason for Objection *
                  </label>
                  <textarea
                    value={objectionReason}
                    onChange={(e) => setObjectionReason(e.target.value)}
                    className="w-full px-4 py-2 border border-ese-accent-beige rounded-lg focus:outline-none focus:ring-2 focus:ring-ese-lang-900"
                    rows="5"
                    placeholder="Please provide a detailed reason for your objection..."
                  />
                </div>
              </div>

              <div className="flex gap-3 mt-6">
                <button
                  onClick={() => {
                    setShowObjectionModal(false)
                    setObjectionReason('')
                    setObjectingNomination(null)
                  }}
                  className="flex-1 px-4 py-2 border border-ese-accent-beige rounded-lg text-ese-ink-navy hover:bg-ese-ink-offwhite"
                >
                  Cancel
                </button>
                <button
                  onClick={submitObjection}
                  disabled={!objectionReason.trim()}
                  className="flex-1 ese-button-primary disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Submit Objection
                </button>
              </div>
            </div>
          </div>
        )}
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

  // Nomination window status
  const [windowStatus, setWindowStatus] = useState(null)
  
  useEffect(() => {
    if (currentCycle) {
      checkNominationWindow()
    }
  }, [currentCycle])

  const checkNominationWindow = async () => {
    try {
      const response = await apiClient.get(`/api/v2/eom/cycles/${currentCycle.id}/window-status`)
      setWindowStatus(response.data)
    } catch (error) {
      console.error('Failed to check nomination window:', error)
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-heading font-bold text-ese-lang-900">EOM Nomination</h1>
        <p className="text-ese-ink-blue mt-1">Nominate an employee for Employee of the Month</p>
      </div>

      {/* Nomination Window Indicator */}
      {currentCycle && windowStatus && (
        <div className={`ese-card ${
          windowStatus.is_within_window 
            ? 'bg-green-50 border-green-200' 
            : 'bg-yellow-50 border-yellow-200'
        }`}>
          <div className="flex items-center gap-3">
            <span className="text-2xl">
              {windowStatus.is_within_window ? (
                <img src="/assets/icons/success.png" alt="Open" className="w-6 h-6 inline" onError={(e) => { e.target.outerHTML = '✅' }} />
              ) : (
                <img src="/assets/icons/time_task.png" alt="Closed" className="w-6 h-6 inline" onError={(e) => { e.target.outerHTML = '⏰' }} />
              )}
            </span>
            <div className="flex-1">
              <h3 className="font-semibold text-ese-ink-navy mb-1">
                {windowStatus.is_within_window 
                  ? 'Nomination Window Open' 
                  : windowStatus.errors?.[0] || 'Nomination Window Status'}
              </h3>
              <p className="text-sm text-ese-ink-navy/70">
                Window: {new Date(windowStatus.window_start).toLocaleDateString()} - {new Date(windowStatus.window_end).toLocaleDateString()}
                {windowStatus.is_within_window && windowStatus.warnings?.[0] && (
                  <span className="ml-2 text-yellow-700">
                    ({windowStatus.warnings[0]})
                  </span>
                )}
              </p>
            </div>
          </div>
        </div>
      )}

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
                    <img src={category.icon} alt={category.name} className="w-8 h-8" onError={(e) => e.target.style.display = 'none'} />
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
                {/* Nominee Selection with Smart Search */}
                <div>
                  <label className="block text-sm font-medium text-ese-ink-navy mb-2">
                    Nominee
                  </label>
                  {eligibleNominees.length === 0 ? (
                    <div className="w-full px-4 py-3 border border-ese-accent-beige rounded-lg bg-ese-ink-offwhite">
                      <p className="text-sm text-ese-ink-blue">
                        Loading eligible nominees...
                      </p>
                    </div>
                  ) : (
                    <SmartNomineeSearch
                      nominees={eligibleNominees}
                      value={nomineeEmail}
                      onChange={setNomineeEmail}
                      placeholder="Search by name, email, department, or role..."
                    />
                  )}
                  {eligibleNominees.length > 0 && (
                    <p className="text-xs text-ese-ink-blue mt-2 flex items-center gap-1">
                      <img src="/assets/icons/innovation.png" alt="Tip" className="w-4 h-4" onError={(e) => e.target.style.display = 'none'} />
                      Tip: Type to search, or use filters to narrow down by department, role, or segment
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
                  
                  {/* AI Category Suggestion */}
                  {suggestedCategory && suggestedCategory.recommended_category && (
                    <div className="mt-3 p-3 bg-ese-int-100 rounded-lg border border-ese-int-500">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <p className="text-sm font-medium text-ese-ink-navy mb-1">
                            <img src="/assets/icons/innovation.png" alt="AI" className="w-4 h-4 inline mr-1" onError={(e) => e.target.style.display = 'none'} /> AI Suggestion: {suggestedCategory.recommended_category.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                          </p>
                          <p className="text-xs text-ese-ink-blue mb-2">
                            Confidence: {Math.round(suggestedCategory.confidence_score * 100)}%
                          </p>
                          {suggestedCategory.reasoning && (
                            <p className="text-xs text-ese-ink-blue italic">
                              {suggestedCategory.reasoning}
                            </p>
                          )}
                        </div>
                        <button
                          onClick={() => {
                            // Map backend category to frontend category ID
                            const categoryMap = {
                              'outstanding_leadership': 'outstanding_leadership',
                              'team_spirit': 'team_spirit',
                              'innovation': 'innovation',
                              'rising_star': 'rising_star',
                              'service_excellence': 'service_excellence'
                            }
                            const categoryLower = suggestedCategory.recommended_category.toLowerCase()
                            const mappedCategory = categoryMap[categoryLower] || categoryLower
                            if (mappedCategory) {
                              setSelectedCategory(mappedCategory)
                              toast.success('Category selected based on AI suggestion')
                            }
                          }}
                          className="ml-3 px-3 py-1 bg-ese-int-500 text-white rounded text-xs hover:bg-ese-int-600 transition-colors"
                        >
                          Use This
                        </button>
                      </div>
                    </div>
                  )}
                  
                  {suggestingCategory && (
                    <div className="mt-2 text-xs text-ese-ink-blue flex items-center gap-2">
                      <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-ese-lang-900"></div>
                      Analyzing achievement text...
                    </div>
                  )}
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

