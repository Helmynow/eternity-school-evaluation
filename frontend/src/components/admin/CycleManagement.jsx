import { useState, useEffect } from 'react'
import { useAPI, useMutation } from '../../hooks/useAPI'
import { apiClient } from '../../lib/api'
import { useAuth } from '../../hooks/useAuth'
import toast from 'react-hot-toast'

const CycleManagement = () => {
  const { isCEO, isPNC } = useAuth()
  const [cycles, setCycles] = useState([])
  const [loading, setLoading] = useState(true)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [editingCycle, setEditingCycle] = useState(null)
  
  const [formData, setFormData] = useState({
    code: '',
    name: '',
    start_date: '',
    end_date: '',
    status: 'draft'
  })

  // Fetch cycles
  const { data: cyclesData, refetch: refetchCycles } = useAPI(
    () => apiClient.cycles.getAll(),
    { autoFetch: true }
  )

  useEffect(() => {
    if (cyclesData) {
      setCycles(cyclesData)
      setLoading(false)
    }
  }, [cyclesData])

  const { mutate: createCycle, loading: creating } = useMutation(
    async (data) => {
      return apiClient.cycles.create(data)
    }
  )

  const { mutate: updateCycle, loading: updating } = useMutation(
    async ({ id, data }) => {
      return apiClient.cycles.update(id, data)
    }
  )

  const handleCreate = async () => {
    try {
      await createCycle(formData, {
        onSuccess: () => {
          toast.success('Cycle created successfully')
          setShowCreateModal(false)
          resetForm()
          refetchCycles()
        },
        onError: (err) => {
          toast.error(err.message || 'Failed to create cycle')
        }
      })
    } catch (error) {
      toast.error('Failed to create cycle')
    }
  }

  const handleUpdate = async (id) => {
    try {
      await updateCycle({ id, data: formData }, {
        onSuccess: () => {
          toast.success('Cycle updated successfully')
          setEditingCycle(null)
          resetForm()
          refetchCycles()
        },
        onError: (err) => {
          toast.error(err.message || 'Failed to update cycle')
        }
      })
    } catch (error) {
      toast.error('Failed to update cycle')
    }
  }

  const handleActivate = async (cycle) => {
    try {
      // Deactivate all other cycles first
      const otherCycles = cycles.filter(c => c.id !== cycle.id && c.status === 'active')
      for (const c of otherCycles) {
        await apiClient.cycles.update(c.id, { status: 'draft' })
      }
      
      // Activate this cycle
      await updateCycle({ id: cycle.id, data: { status: 'active' } }, {
        onSuccess: () => {
          toast.success(`Cycle "${cycle.name}" activated`)
          refetchCycles()
        }
      })
    } catch (error) {
      toast.error('Failed to activate cycle')
    }
  }

  const resetForm = () => {
    setFormData({
      code: '',
      name: '',
      start_date: '',
      end_date: '',
      status: 'draft'
    })
  }

  const openEditModal = (cycle) => {
    setEditingCycle(cycle)
    setFormData({
      code: cycle.code,
      name: cycle.name,
      start_date: cycle.start_date || '',
      end_date: cycle.end_date || '',
      status: cycle.status
    })
    setShowCreateModal(true)
  }

  if (!isCEO && !isPNC) {
    return (
      <div className="ese-card text-center py-12">
        <p className="text-ese-ink-blue">You don't have permission to access this page.</p>
      </div>
    )
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-ese-lang-900"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-heading font-bold text-ese-lang-900">Cycle Management</h1>
          <p className="text-ese-ink-blue mt-1">Create and manage evaluation cycles</p>
        </div>
        <button
          onClick={() => {
            resetForm()
            setEditingCycle(null)
            setShowCreateModal(true)
          }}
          className="ese-button-primary"
        >
          + Create New Cycle
        </button>
      </div>

      {/* Cycles List */}
      <div className="ese-card">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-ese-accent-beige">
                <th className="text-left py-3 px-4 font-semibold text-ese-ink-navy">Code</th>
                <th className="text-left py-3 px-4 font-semibold text-ese-ink-navy">Name</th>
                <th className="text-left py-3 px-4 font-semibold text-ese-ink-navy">Start Date</th>
                <th className="text-left py-3 px-4 font-semibold text-ese-ink-navy">End Date</th>
                <th className="text-left py-3 px-4 font-semibold text-ese-ink-navy">Status</th>
                <th className="text-left py-3 px-4 font-semibold text-ese-ink-navy">Actions</th>
              </tr>
            </thead>
            <tbody>
              {cycles.map((cycle) => (
                <tr key={cycle.id} className="border-b border-ese-accent-beige hover:bg-ese-ink-offwhite">
                  <td className="py-3 px-4">{cycle.code}</td>
                  <td className="py-3 px-4">{cycle.name}</td>
                  <td className="py-3 px-4">{cycle.start_date || 'N/A'}</td>
                  <td className="py-3 px-4">{cycle.end_date || 'N/A'}</td>
                  <td className="py-3 px-4">
                    <span className={`
                      px-3 py-1 rounded-full text-xs font-medium
                      ${cycle.status === 'active' 
                        ? 'bg-ese-int-500 text-white' 
                        : cycle.status === 'closed'
                        ? 'bg-ese-ink-blue text-white'
                        : 'bg-ese-accent-beige text-ese-ink-navy'
                      }
                    `}>
                      {cycle.status}
                    </span>
                  </td>
                  <td className="py-3 px-4">
                    <div className="flex gap-2">
                      {cycle.status !== 'active' && (
                        <button
                          onClick={() => handleActivate(cycle)}
                          className="text-ese-int-500 hover:text-ese-int-600 text-sm font-medium"
                        >
                          Activate
                        </button>
                      )}
                      <button
                        onClick={() => openEditModal(cycle)}
                        className="text-ese-lang-900 hover:text-ese-lang-800 text-sm font-medium"
                      >
                        Edit
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {cycles.length === 0 && (
            <div className="text-center py-12 text-ese-ink-blue">
              No cycles found. Create your first cycle to get started.
            </div>
          )}
        </div>
      </div>

      {/* Create/Edit Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h2 className="text-2xl font-heading font-bold text-ese-ink-navy mb-4">
              {editingCycle ? 'Edit Cycle' : 'Create New Cycle'}
            </h2>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-ese-ink-navy mb-1">
                  Cycle Code *
                </label>
                <input
                  type="text"
                  value={formData.code}
                  onChange={(e) => setFormData({ ...formData, code: e.target.value })}
                  className="w-full px-4 py-2 border border-ese-accent-beige rounded-lg focus:outline-none focus:ring-2 focus:ring-ese-lang-900"
                  placeholder="e.g., Q1-2025"
                  disabled={!!editingCycle}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-ese-ink-navy mb-1">
                  Cycle Name *
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full px-4 py-2 border border-ese-accent-beige rounded-lg focus:outline-none focus:ring-2 focus:ring-ese-lang-900"
                  placeholder="e.g., Q1 2025 Evaluation"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-ese-ink-navy mb-1">
                    Start Date
                  </label>
                  <input
                    type="date"
                    value={formData.start_date}
                    onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
                    className="w-full px-4 py-2 border border-ese-accent-beige rounded-lg focus:outline-none focus:ring-2 focus:ring-ese-lang-900"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-ese-ink-navy mb-1">
                    End Date
                  </label>
                  <input
                    type="date"
                    value={formData.end_date}
                    onChange={(e) => setFormData({ ...formData, end_date: e.target.value })}
                    className="w-full px-4 py-2 border border-ese-accent-beige rounded-lg focus:outline-none focus:ring-2 focus:ring-ese-lang-900"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-ese-ink-navy mb-1">
                  Status
                </label>
                <select
                  value={formData.status}
                  onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                  className="w-full px-4 py-2 border border-ese-accent-beige rounded-lg focus:outline-none focus:ring-2 focus:ring-ese-lang-900"
                >
                  <option value="draft">Draft</option>
                  <option value="active">Active</option>
                  <option value="closed">Closed</option>
                </select>
              </div>
            </div>

            <div className="flex gap-3 mt-6">
              <button
                onClick={() => {
                  setShowCreateModal(false)
                  resetForm()
                  setEditingCycle(null)
                }}
                className="flex-1 px-4 py-2 border border-ese-accent-beige rounded-lg text-ese-ink-navy hover:bg-ese-ink-offwhite"
              >
                Cancel
              </button>
              <button
                onClick={() => editingCycle ? handleUpdate(editingCycle.id) : handleCreate()}
                disabled={!formData.code || !formData.name || creating || updating}
                className="flex-1 ese-button-primary disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {creating || updating ? 'Saving...' : editingCycle ? 'Update' : 'Create'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default CycleManagement
