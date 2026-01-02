import { useState, useEffect, useCallback } from 'react'
import { useAPI, useMutation } from '../../hooks/useAPI'
import { apiClient } from '../../lib/api'
import { useAuth } from '../../hooks/useAuth'
import toast from 'react-hot-toast'

// Domain definitions based on target group
const ADMIN_DOMAINS = [
  { code: 'task_management', label: 'Task Management', description: 'Performs assigned tasks effectively', weight: 10 },
  { code: 'policy_adherence', label: 'Policy Adherence', description: 'Follows policies and regulations', weight: 10 },
  { code: 'problem_solving', label: 'Problem-Solving', description: 'Handles challenges and issues proactively', weight: 10 },
  { code: 'teamwork', label: 'Teamwork', description: 'Collaborates effectively with colleagues', weight: 10 },
  { code: 'attendance', label: 'Attendance & Absenteeism', description: 'Meets attendance expectations', weight: 20 },
  { code: 'peer_review', label: 'Peer Review', description: 'Provides feedback on peer performance', weight: 10 },
  { code: 'qa_policies', label: 'QA Policies', description: 'Follows quality assurance policies', weight: 10 },
  { code: 'innovation', label: 'Innovation/Reputation/Discipline', description: 'Demonstrates innovation, upholds reputation, observes discipline', weight: 15 },
  { code: 'self_evaluation', label: 'Self-Evaluation', description: 'Compares personal performance to the average', weight: 5 },
]

const ACADEMIC_DOMAINS = [
  { code: 'parent_feedback', label: 'Parent Feedback', description: 'Reflects parents\' satisfaction', weight: 10 },
  { code: 'team_collaboration', label: 'Team Collaboration', description: 'Collaborates with colleagues', weight: 10 },
  { code: 'student_engagement', label: 'Student Engagement', description: 'Engages students in learning', weight: 5 },
  { code: 'teaching_effectiveness', label: 'Teaching Effectiveness', description: 'Demonstrates effective teaching practices', weight: 10 },
  { code: 'attendance', label: 'Attendance & Absenteeism', description: 'Meets attendance expectations', weight: 20 },
  { code: 'classroom_management', label: 'Classroom Management', description: 'Manages the classroom environment', weight: 15 },
  { code: 'curriculum_implementation', label: 'Curriculum Implementation', description: 'Implements the curriculum effectively', weight: 10 },
  { code: 'innovation', label: 'Innovation, Reputation, Discipline & Resource Utilisation', description: 'Shows innovation, upholds reputation, respects discipline and uses resources efficiently', weight: 20 },
  { code: 'self_evaluation', label: 'Goals, Improvements & Challenges', description: 'Reflects on personal growth and identifies improvements and challenges', weight: 5 },
]

const MREEvaluation = () => {
  const { user } = useAuth()
  const [assignments, setAssignments] = useState([])
  const [selectedAssignment, setSelectedAssignment] = useState(null)
  const [scores, setScores] = useState({})
  const [currentCycle, setCurrentCycle] = useState(null)
  const [targetGroup, setTargetGroup] = useState(null)

  // Get current cycle - use useMemo to stabilize the endpoint function
  const getCurrentCycle = useCallback(() => apiClient.cycles.getCurrent(), [])
  const { data: currentCycleData, loading: cycleLoading } = useAPI(
    getCurrentCycle,
    { autoFetch: true }
  )

  useEffect(() => {
    if (currentCycleData && currentCycleData.id) {
      setCurrentCycle(currentCycleData)
      loadAssignments(currentCycleData.id)
    } else if (!cycleLoading && currentCycleData === null) {
      // No cycle available - show message or handle gracefully
      setCurrentCycle(null)
    }
  }, [currentCycleData, cycleLoading])

  const loadAssignments = async (cycleId) => {
    try {
      const response = await apiClient.mre.getAssignments(cycleId)
      setAssignments(response.data || [])
    } catch (error) {
      toast.error('Failed to load assignments')
    }
  }

  const { mutate: submitEvaluation, loading: submitting } = useMutation(
    apiClient.mre.submitEvaluation
  )

  const handleScoreChange = (domainCode, value) => {
    setScores(prev => ({
      ...prev,
      [domainCode]: parseFloat(value) || 0,
    }))
  }

  const handleSubmit = async () => {
    if (!selectedAssignment) {
      toast.error('Please select an assignment')
      return
    }

    // Validate all required domains are scored
    const domains = targetGroup === 'admin' ? ADMIN_DOMAINS : ACADEMIC_DOMAINS
    const requiredDomains = domains.filter(d => d.code !== 'self_evaluation')
    const missingDomains = requiredDomains.filter(d => !scores[d.code] && scores[d.code] !== 0)

    if (missingDomains.length > 0) {
      toast.error(`Please score all required domains: ${missingDomains.map(d => d.label).join(', ')}`)
      return
    }

    try {
      await submitEvaluation({
        assignment_id: selectedAssignment.id,
        domain_scores: scores,
        status: 'submitted',
      })
      toast.success('Evaluation submitted successfully!')
      
      // Reset form
      setSelectedAssignment(null)
      setScores({})
      setTargetGroup(null)
      loadAssignments(currentCycle.id)
    } catch (error) {
      toast.error('Failed to submit evaluation')
    }
  }

  const handleAssignmentSelect = (assignment) => {
    setSelectedAssignment(assignment)
    setTargetGroup(assignment.target_group)
    setScores({}) // Reset scores
  }

  const domains = targetGroup === 'admin' ? ADMIN_DOMAINS : ACADEMIC_DOMAINS
  const pendingAssignments = assignments.filter(a => a.status === 'pending' || a.status === 'draft')
  const completedAssignments = assignments.filter(a => a.status === 'submitted')

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-heading font-bold text-ese-lang-900">MRE Evaluation</h1>
        <p className="text-ese-ink-blue mt-1">Complete your Multi-Rater Evaluations</p>
      </div>

      {!currentCycle && (
        <div className="ese-card">
          <p className="text-ese-ink-blue">No active evaluation cycle. Please wait for the next cycle to open.</p>
        </div>
      )}

      {currentCycle && (
        <>
          {/* Assignment List */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Pending Assignments */}
            <div className="ese-card">
              <h2 className="text-xl font-heading font-semibold text-ese-ink-navy mb-4">
                Pending Evaluations ({pendingAssignments.length})
              </h2>
              <div className="space-y-2 max-h-96 overflow-y-auto">
                {pendingAssignments.length === 0 ? (
                  <p className="text-ese-ink-blue">No pending evaluations</p>
                ) : (
                  pendingAssignments.map((assignment) => (
                    <button
                      key={assignment.id}
                      onClick={() => handleAssignmentSelect(assignment)}
                      className={`
                        w-full p-4 rounded-lg border-2 text-left transition-all
                        ${selectedAssignment?.id === assignment.id
                          ? 'border-ese-accent-mustard bg-ese-accent-mustard/10'
                          : 'border-ese-accent-beige hover:border-ese-accent-olive'
                        }
                      `}
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="font-semibold text-ese-ink-navy">{assignment.target_name}</p>
                          <p className="text-sm text-ese-ink-blue">{assignment.target_email}</p>
                          <p className="text-xs text-ese-ink-blue mt-1">
                            {assignment.target_group} • {assignment.rater_context}
                          </p>
                        </div>
                        <span className={`
                          text-xs px-2 py-1 rounded-full
                          ${assignment.required
                            ? 'bg-ese-accent-terracotta text-white'
                            : 'bg-ese-accent-beige text-ese-ink-navy'
                          }
                        `}>
                          {assignment.required ? 'Required' : 'Optional'}
                        </span>
                      </div>
                    </button>
                  ))
                )}
              </div>
            </div>

            {/* Completed Assignments */}
            <div className="ese-card">
              <h2 className="text-xl font-heading font-semibold text-ese-ink-navy mb-4">
                Completed Evaluations ({completedAssignments.length})
              </h2>
              <div className="space-y-2 max-h-96 overflow-y-auto">
                {completedAssignments.length === 0 ? (
                  <p className="text-ese-ink-blue">No completed evaluations</p>
                ) : (
                  completedAssignments.map((assignment) => (
                    <div
                      key={assignment.id}
                      className="w-full p-4 rounded-lg border-2 border-ese-int-300 bg-ese-int-50"
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="font-semibold text-ese-ink-navy">{assignment.target_name}</p>
                          <p className="text-sm text-ese-ink-blue">{assignment.target_email}</p>
                        </div>
                        <span className="text-xs px-2 py-1 rounded-full bg-ese-int-500 text-white">
                          ✓ Submitted
                        </span>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>

          {/* Evaluation Form */}
          {selectedAssignment && (
            <div className="ese-card">
              <h2 className="text-xl font-heading font-semibold text-ese-ink-navy mb-4">
                Evaluate: {selectedAssignment.target_name}
              </h2>
              <p className="text-sm text-ese-ink-blue mb-6">
                Target Group: <span className="font-medium capitalize">{targetGroup}</span> • 
                Rater Context: <span className="font-medium">{selectedAssignment.rater_context}</span>
              </p>

              <div className="space-y-6">
                {domains.map((domain) => {
                  const isSelfEval = domain.code === 'self_evaluation'
                  const isRequired = !isSelfEval
                  
                  return (
                    <div key={domain.code} className="p-4 bg-ese-ink-offwhite rounded-lg">
                      <div className="flex items-center justify-between mb-2">
                        <div>
                          <label className="font-semibold text-ese-ink-navy">
                            {domain.label}
                            {isRequired && <span className="text-ese-accent-terracotta ml-1">*</span>}
                          </label>
                          <p className="text-xs text-ese-ink-blue mt-1">{domain.description}</p>
                        </div>
                        <span className="text-xs px-2 py-1 rounded-full bg-ese-accent-mustard/20 text-ese-ink-navy">
                          {domain.weight}%
                        </span>
                      </div>
                      
                      {isSelfEval ? (
                        <textarea
                          value={scores[domain.code] || ''}
                          onChange={(e) => handleScoreChange(domain.code, e.target.value)}
                          rows={4}
                          className="w-full px-4 py-2 border border-ese-accent-beige rounded-lg focus:ring-2 focus:ring-ese-lang-500 focus:border-ese-lang-500 outline-none"
                          placeholder="Reflect on your performance, achievements, and areas for improvement..."
                        />
                      ) : (
                        <div className="flex items-center gap-4">
                          <input
                            type="number"
                            min="0"
                            max="100"
                            value={scores[domain.code] || ''}
                            onChange={(e) => handleScoreChange(domain.code, e.target.value)}
                            className="w-24 px-4 py-2 border border-ese-accent-beige rounded-lg focus:ring-2 focus:ring-ese-lang-500 focus:border-ese-lang-500 outline-none"
                            placeholder="0-100"
                          />
                          <div className="flex-1">
                            <input
                              type="range"
                              min="0"
                              max="100"
                              value={scores[domain.code] || 0}
                              onChange={(e) => handleScoreChange(domain.code, e.target.value)}
                              className="w-full"
                            />
                          </div>
                          <span className="text-ese-ink-navy font-medium w-12 text-right">
                            {scores[domain.code] || 0}%
                          </span>
                        </div>
                      )}
                    </div>
                  )
                })}

                <div className="flex gap-4 pt-4">
                  <button
                    onClick={handleSubmit}
                    disabled={submitting}
                    className="ese-button-primary disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {submitting ? 'Submitting...' : 'Submit Evaluation'}
                  </button>
                  <button
                    onClick={() => {
                      setSelectedAssignment(null)
                      setScores({})
                      setTargetGroup(null)
                    }}
                    className="bg-ese-accent-beige text-ese-ink-navy px-6 py-3 rounded-ese-pill font-medium hover:bg-ese-accent-olive"
                  >
                    Cancel
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

export default MREEvaluation

