import { useState, useEffect } from 'react'
import { apiClient } from '../../lib/api'
import { useAuth } from '../../hooks/useAuth'
import toast from 'react-hot-toast'
import LoadingSkeleton from '../common/LoadingSkeleton'

const EvaluatorManagement = ({ staffEmail, staffName, onClose, cycleId }) => {
  const { user } = useAuth()
  const [loading, setLoading] = useState(true)
  const [evaluationStatus, setEvaluationStatus] = useState(null)
  const [allStaff, setAllStaff] = useState([])
  const [editingAssignment, setEditingAssignment] = useState(null)
  const [showAddEvaluator, setShowAddEvaluator] = useState(false)
  const [currentCycle, setCurrentCycle] = useState(cycleId)

  useEffect(() => {
    if (staffEmail) {
      loadEvaluationStatus()
      loadAllStaff()
      loadCurrentCycle()
    }
  }, [staffEmail])  // Only depend on staffEmail to avoid infinite loop

  const loadCurrentCycle = async () => {
    try {
      const response = await apiClient.cycles.getCurrent()
      if (response.data && response.data.id !== currentCycle) {
        setCurrentCycle(response.data.id)
      }
    } catch (error) {
      console.error('Error loading current cycle:', error)
    }
  }

  const loadEvaluationStatus = async () => {
    try {
      setLoading(true)
      const response = await apiClient.staff.getEvaluationStatus(staffEmail, { cycle_id: currentCycle })
      setEvaluationStatus(response.data)
    } catch (error) {
      console.error('Error loading evaluation status:', error)
      toast.error('Failed to load evaluation status')
    } finally {
      setLoading(false)
    }
  }

  const loadAllStaff = async () => {
    try {
      const response = await apiClient.people.getAll()
      setAllStaff(response.data || [])
    } catch (error) {
      console.error('Error loading staff:', error)
    }
  }

  const handleCreateAssignments = async () => {
    try {
      setLoading(true)
      await apiClient.staff.assignEvaluators(staffEmail, {
        target_email: staffEmail,
        cycle_id: currentCycle
      })
      toast.success('Evaluator assignments created successfully')
      loadEvaluationStatus()
    } catch (error) {
      console.error('Error creating assignments:', error)
      toast.error(error.response?.data?.detail || 'Failed to create evaluator assignments')
    } finally {
      setLoading(false)
    }
  }

  const handleUpdateAssignment = async (assignmentId, updates) => {
    try {
      setLoading(true)
      const assignments = evaluationStatus.evaluated_by.map(a => {
        if (a.assignment_id === assignmentId) {
          return {
            id: assignmentId,
            action: 'update',
            ...updates
          }
        }
        return {
          id: a.assignment_id,
          action: 'update',
          rater_email: a.rater_email,
          rater_context: a.rater_context,
          weight: a.weight
        }
      })

      await apiClient.staff.updateEvaluators(staffEmail, {
        target_email: staffEmail,
        cycle_id: currentCycle,
        assignments
      })
      toast.success('Evaluator assignment updated')
      loadEvaluationStatus()
      setEditingAssignment(null)
    } catch (error) {
      console.error('Error updating assignment:', error)
      toast.error(error.response?.data?.detail || 'Failed to update assignment')
    } finally {
      setLoading(false)
    }
  }

  const handleDeleteAssignment = async (assignmentId) => {
    if (!confirm('Are you sure you want to remove this evaluator assignment?')) return

    try {
      setLoading(true)
      const assignments = [
        {
          id: assignmentId,
          action: 'delete'
        }
      ]

      await apiClient.staff.updateEvaluators(staffEmail, {
        target_email: staffEmail,
        cycle_id: currentCycle,
        assignments
      })
      toast.success('Evaluator assignment removed')
      loadEvaluationStatus()
    } catch (error) {
      console.error('Error deleting assignment:', error)
      toast.error(error.response?.data?.detail || 'Failed to remove assignment')
    } finally {
      setLoading(false)
    }
  }

  const handleAddEvaluator = async (raterEmail, raterContext, weight) => {
    try {
      setLoading(true)
      const existingAssignments = evaluationStatus.evaluated_by.map(a => ({
        id: a.assignment_id,
        action: 'update',
        rater_email: a.rater_email,
        rater_context: a.rater_context,
        weight: a.weight
      }))

      existingAssignments.push({
        action: 'create',
        rater_email: raterEmail,
        rater_context: raterContext,
        weight: weight
      })

      await apiClient.staff.updateEvaluators(staffEmail, {
        target_email: staffEmail,
        cycle_id: currentCycle,
        assignments: existingAssignments
      })
      toast.success('Evaluator added')
      loadEvaluationStatus()
      setShowAddEvaluator(false)
    } catch (error) {
      console.error('Error adding evaluator:', error)
      toast.error(error.response?.data?.detail || 'Failed to add evaluator')
    } finally {
      setLoading(false)
    }
  }

  if (loading && !evaluationStatus) {
    return <LoadingSkeleton type="dashboard" count={1} />
  }

  const raterContextOptions = [
    { value: 'CEO', label: 'CEO/Director (15%)', weight: 0.15 },
    { value: 'P&C', label: 'People & Culture (25%)', weight: 0.25 },
    { value: 'manager_review', label: 'Manager/Principal (30-40%)', weight: 0.35 },
    { value: 'coordinator_hod', label: 'Coordinator/HOD (25%)', weight: 0.25 },
    { value: 'QA', label: 'Quality Assurance (10%)', weight: 0.10 },
    { value: 'peer_review', label: 'Peer Review (10%)', weight: 0.10 },
    { value: 'self_review', label: 'Self Evaluation (5%)', weight: 0.05 }
  ]

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg p-6 max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-6">
          <div>
            <h2 className="text-2xl font-heading font-bold text-ese-ink-navy">
              Evaluator Management
            </h2>
            <p className="text-ese-ink-blue mt-1">
              {staffName} ({staffEmail})
            </p>
            <p className="text-sm text-ese-ink-medium mt-1">
              Staff Type: {evaluationStatus?.staff_type || 'Unknown'} | 
              Cycle: {currentCycle || 'Current'}
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-ese-ink-medium hover:text-ese-ink-navy text-2xl"
          >
            ×
          </button>
        </div>

        {/* Summary */}
        {evaluationStatus && (
          <div className="mb-6 p-4 bg-ese-lang-50 rounded-lg">
            <div className="grid grid-cols-3 gap-4">
              <div>
                <p className="text-sm text-ese-ink-blue">Total Evaluators</p>
                <p className="text-2xl font-bold text-ese-ink-navy">
                  {evaluationStatus.summary?.total_evaluators || 0}
                </p>
              </div>
              <div>
                <p className="text-sm text-ese-ink-blue">Required</p>
                <p className="text-2xl font-bold text-ese-ink-navy">
                  {evaluationStatus.summary?.required_count || 0}
                </p>
              </div>
              <div>
                <p className="text-sm text-ese-ink-blue">Evaluating Others</p>
                <p className="text-2xl font-bold text-ese-ink-navy">
                  {evaluationStatus.summary?.total_evaluating || 0}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Actions */}
        <div className="flex gap-3 mb-6">
          {(!evaluationStatus?.evaluated_by || evaluationStatus.evaluated_by.length === 0) && (
            <button
              onClick={handleCreateAssignments}
              className="ese-button-primary"
            >
              Auto-Assign Evaluators
            </button>
          )}
          <button
            onClick={() => setShowAddEvaluator(true)}
            className="ese-button-secondary"
          >
            + Add Evaluator
          </button>
        </div>

        {/* Evaluators List */}
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-ese-ink-navy">
            Who Evaluates {staffName}
          </h3>
          
          {evaluationStatus?.evaluated_by && evaluationStatus.evaluated_by.length > 0 ? (
            <div className="space-y-2">
              {evaluationStatus.evaluated_by.map((assignment) => (
                <div
                  key={assignment.assignment_id}
                  className="p-4 border border-ese-accent-beige rounded-lg hover:bg-ese-ink-offwhite"
                >
                  {editingAssignment === assignment.assignment_id ? (
                    <EditAssignmentForm
                      assignment={assignment}
                      allStaff={allStaff}
                      raterContextOptions={raterContextOptions}
                      onSave={(updates) => handleUpdateAssignment(assignment.assignment_id, updates)}
                      onCancel={() => setEditingAssignment(null)}
                    />
                  ) : (
                    <div className="flex justify-between items-center">
                      <div className="flex-1">
                        <p className="font-medium text-ese-ink-navy">
                          {assignment.rater_name}
                        </p>
                        <p className="text-sm text-ese-ink-blue">
                          <span className="font-mono">{assignment.rater_email.split('@')[0]}</span> • {assignment.rater_email}
                        </p>
                        {assignment.rater_position && (
                          <p className="text-xs text-ese-ink-medium mt-1">
                            Position: {assignment.rater_position}
                            {assignment.rater_department && ` • Division: ${assignment.rater_department}`}
                          </p>
                        )}
                        <p className="text-sm text-ese-ink-blue mt-1">
                          {assignment.rater_context} • Weight: {(assignment.weight * 100).toFixed(0)}%
                        </p>
                      </div>
                      <div className="flex gap-2">
                        <button
                          onClick={() => setEditingAssignment(assignment.assignment_id)}
                          className="text-ese-lang-900 hover:text-ese-lang-800 text-sm font-medium"
                        >
                          Edit
                        </button>
                        <button
                          onClick={() => handleDeleteAssignment(assignment.assignment_id)}
                          className="text-ese-accent-terracotta hover:text-red-600 text-sm font-medium"
                        >
                          Remove
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-ese-ink-blue">
              No evaluators assigned. Click "Auto-Assign Evaluators" to create assignments.
            </div>
          )}
        </div>

        {/* Who They Evaluate */}
        {evaluationStatus?.evaluating && evaluationStatus.evaluating.length > 0 && (
          <div className="mt-6 space-y-4">
            <h3 className="text-lg font-semibold text-ese-ink-navy">
              Who {staffName} Evaluates
            </h3>
            <div className="space-y-2">
              {evaluationStatus.evaluating.map((assignment) => (
                <div
                  key={assignment.assignment_id}
                  className="p-4 border border-ese-accent-beige rounded-lg"
                >
                  <p className="font-medium text-ese-ink-navy">
                    {assignment.target_name}
                  </p>
                  <p className="text-sm text-ese-ink-blue">
                    <span className="font-mono">{assignment.target_email.split('@')[0]}</span> • {assignment.target_email}
                  </p>
                  {assignment.target_position && (
                    <p className="text-xs text-ese-ink-medium mt-1">
                      Position: {assignment.target_position}
                      {assignment.target_department && ` • Division: ${assignment.target_department}`}
                    </p>
                  )}
                  <p className="text-sm text-ese-ink-blue mt-1">
                    {assignment.rater_context} • Weight: {(assignment.weight * 100).toFixed(0)}%
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Add Evaluator Modal */}
        {showAddEvaluator && (
          <AddEvaluatorForm
            allStaff={allStaff}
            raterContextOptions={raterContextOptions}
            onSave={handleAddEvaluator}
            onCancel={() => setShowAddEvaluator(false)}
          />
        )}
      </div>
    </div>
  )
}

const EditAssignmentForm = ({ assignment, allStaff, raterContextOptions, onSave, onCancel }) => {
  // Keep selects controlled from the first render (avoid uncontrolled->controlled warnings)
  const [raterEmail, setRaterEmail] = useState(assignment?.rater_email ?? '')
  const [raterContext, setRaterContext] = useState(assignment?.rater_context ?? '')
  const [weight, setWeight] = useState(
    Number.isFinite(Number(assignment?.weight)) ? Number(assignment.weight) : 0.0
  )

  const handleSubmit = (e) => {
    e.preventDefault()
    onSave({ rater_email: raterEmail, rater_context: raterContext, weight })
  }

  const handleContextChange = (newContext) => {
    setRaterContext(newContext)
    const selectedContext = raterContextOptions.find(opt => opt.value === newContext)
    if (selectedContext) {
      setWeight(selectedContext.weight)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-ese-ink-navy mb-1">
          Evaluator
        </label>
        <select
          value={raterEmail || ''}
          onChange={(e) => setRaterEmail(e.target.value)}
          className="w-full px-4 py-2 border border-ese-accent-beige rounded-lg"
          required
        >
          <option value="">Select evaluator...</option>
          {allStaff.map((staff) => (
            <option key={staff.email} value={staff.email}>
              {staff.full_name} | {staff.email.split('@')[0]} | {staff.role_title || 'N/A'} | {staff.department || 'N/A'}
            </option>
          ))}
        </select>
      </div>

      <div>
        <label className="block text-sm font-medium text-ese-ink-navy mb-1">
          Evaluator Type
        </label>
        <select
          value={raterContext || ''}
          onChange={(e) => handleContextChange(e.target.value)}
          className="w-full px-4 py-2 border border-ese-accent-beige rounded-lg"
          required
        >
          {raterContextOptions.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      </div>

      <div>
        <label className="block text-sm font-medium text-ese-ink-navy mb-1">
          Weight (0.0 - 1.0)
        </label>
        <input
          type="number"
          min="0"
          max="1"
          step="0.01"
          value={weight}
          onChange={(e) => setWeight(parseFloat(e.target.value))}
          className="w-full px-4 py-2 border border-ese-accent-beige rounded-lg"
          required
        />
      </div>

      <div className="flex gap-3">
        <button type="button" onClick={onCancel} className="flex-1 ese-button-secondary">
          Cancel
        </button>
        <button type="submit" className="flex-1 ese-button-primary">
          Save
        </button>
      </div>
    </form>
  )
}

const AddEvaluatorForm = ({ allStaff, raterContextOptions, onSave, onCancel }) => {
  const [raterEmail, setRaterEmail] = useState('')
  const [raterContext, setRaterContext] = useState('')
  const [weight, setWeight] = useState(0.0)

  const handleSubmit = (e) => {
    e.preventDefault()
    onSave(raterEmail, raterContext, weight)
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
        <h3 className="text-xl font-heading font-bold text-ese-ink-navy mb-4">
          Add Evaluator
        </h3>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-ese-ink-navy mb-1">
              Evaluator
            </label>
            <select
              value={raterEmail}
              onChange={(e) => setRaterEmail(e.target.value)}
              className="w-full px-4 py-2 border border-ese-accent-beige rounded-lg"
              required
            >
              <option value="">Select evaluator...</option>
              {allStaff.map((staff) => (
                <option key={staff.email} value={staff.email}>
                  {staff.full_name} | {staff.email.split('@')[0]} | {staff.role_title || 'N/A'} | {staff.department || 'N/A'}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-ese-ink-navy mb-1">
              Evaluator Type
            </label>
            <select
              value={raterContext}
              onChange={(e) => {
                setRaterContext(e.target.value)
                const context = raterContextOptions.find(opt => opt.value === e.target.value)
                if (context) setWeight(context.weight)
              }}
              className="w-full px-4 py-2 border border-ese-accent-beige rounded-lg"
              required
            >
              <option value="">Select type...</option>
              {raterContextOptions.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-ese-ink-navy mb-1">
              Weight (0.0 - 1.0)
            </label>
            <input
              type="number"
              min="0"
              max="1"
              step="0.01"
              value={weight}
              onChange={(e) => setWeight(parseFloat(e.target.value))}
              className="w-full px-4 py-2 border border-ese-accent-beige rounded-lg"
              required
            />
          </div>

          <div className="flex gap-3">
            <button type="button" onClick={onCancel} className="flex-1 ese-button-secondary">
              Cancel
            </button>
            <button type="submit" className="flex-1 ese-button-primary">
              Add
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default EvaluatorManagement
