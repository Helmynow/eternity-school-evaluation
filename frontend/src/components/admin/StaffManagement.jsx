import { useState, useEffect, useRef } from 'react'
import { useAPI, useMutation } from '../../hooks/useAPI'
import { apiClient } from '../../lib/api'
import { useAuth } from '../../hooks/useAuth'
import toast from 'react-hot-toast'
import EvaluatorManagement from './EvaluatorManagement'

const StaffManagement = () => {
  const { isCEO, isPNC } = useAuth()
  const [staff, setStaff] = useState([])
  const [loading, setLoading] = useState(true)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showBulkUpload, setShowBulkUpload] = useState(false)
  const [editingStaff, setEditingStaff] = useState(null)
  const [evaluatorManagement, setEvaluatorManagement] = useState(null)
  const fileInputRef = useRef(null)
  
  const [formData, setFormData] = useState({
    email: '',
    full_name: '',
    role_title: '',
    department: '',
    segment: 'whole_school',
    hire_date: ''
  })

  // Fetch staff
  const fetchStaff = async () => {
    try {
      const response = await apiClient.people.getAll()
      setStaff(response.data || [])
    } catch (error) {
      toast.error('Failed to load staff')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchStaff()
  }, [])

  const handleCreate = async () => {
    try {
      if (editingStaff) {
        await apiClient.people.update(editingStaff.email, formData)
        toast.success('Staff member updated successfully')
      } else {
        await apiClient.people.create(formData)
        toast.success('Staff member added successfully')
      }
      setShowCreateModal(false)
      resetForm()
      fetchStaff()
      
      // Auto-create evaluator assignments only for newly created staff
      if (!editingStaff) {
        try {
          const currentCycle = await apiClient.cycles.getCurrent()
          if (currentCycle.data) {
            await apiClient.staff.assignEvaluators(formData.email, {
              target_email: formData.email,
              cycle_id: currentCycle.data.id
            })
            toast.success('Evaluator assignments created automatically')
          }
        } catch (evalError) {
          console.warn('Could not auto-create assignments:', evalError)
          // Don't fail the whole operation if assignment creation fails
        }
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to save staff member')
    }
  }

  const handleDelete = async (email) => {
    if (!confirm(`Are you sure you want to remove ${email}?`)) return
    
    try {
      // Soft delete by setting active to false
      await apiClient.people.update(email, { active: false })
      toast.success('Staff member removed')
      fetchStaff()
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to remove staff member')
    }
  }

  const handleBulkUpload = async (event) => {
    const file = event.target.files[0]
    if (!file) return

    if (!file.name.endsWith('.xlsx')) {
      toast.error('Please upload an Excel (.xlsx) file')
      return
    }

    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await apiClient.import.staff(formData)
      const result = response.data
      toast.success(`Successfully imported ${result.count || 0} staff members`)
      setShowBulkUpload(false)
      fetchStaff()
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to upload staff file')
    }
  }

  const resetForm = () => {
    setFormData({
      email: '',
      full_name: '',
      role_title: '',
      department: '',
      segment: 'whole_school',
      hire_date: ''
    })
    setEditingStaff(null)
  }

  const openEditModal = (member) => {
    setEditingStaff(member)
    setFormData({
      email: member.email,
      full_name: member.full_name,
      role_title: member.role_title || '',
      department: member.department || '',
      segment: member.segment || 'whole_school',
      hire_date: member.hire_date || ''
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
          <h1 className="text-3xl font-heading font-bold text-ese-lang-900">Staff Management</h1>
          <p className="text-ese-ink-blue mt-1">Add, edit, and manage staff members</p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={() => setShowBulkUpload(true)}
            className="ese-button-secondary"
          >
            <img src="/assets/icons/upload.png" alt="Upload" className="w-5 h-5 inline mr-2" />
            Bulk Upload
          </button>
          <button
            onClick={() => {
              resetForm()
              setShowCreateModal(true)
            }}
            className="ese-button-primary"
          >
            + Add Staff Member
          </button>
        </div>
      </div>

      {/* Staff List */}
      <div className="ese-card">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-ese-accent-beige">
                <th className="text-left py-3 px-4 font-semibold text-ese-ink-navy">ID</th>
                <th className="text-left py-3 px-4 font-semibold text-ese-ink-navy">Full Name</th>
                <th className="text-left py-3 px-4 font-semibold text-ese-ink-navy">Email</th>
                <th className="text-left py-3 px-4 font-semibold text-ese-ink-navy">Position</th>
                <th className="text-left py-3 px-4 font-semibold text-ese-ink-navy">Division</th>
                <th className="text-left py-3 px-4 font-semibold text-ese-ink-navy">Segment</th>
                <th className="text-left py-3 px-4 font-semibold text-ese-ink-navy">Status</th>
                <th className="text-left py-3 px-4 font-semibold text-ese-ink-navy">Actions</th>
              </tr>
            </thead>
            <tbody>
              {staff.map((member) => (
                <tr key={member.email} className="border-b border-ese-accent-beige hover:bg-ese-ink-offwhite">
                  <td className="py-3 px-4">
                    <span className="font-mono text-sm text-ese-ink-navy">
                      {member.email.split('@')[0]}
                    </span>
                  </td>
                  <td className="py-3 px-4 font-medium text-ese-ink-navy">{member.full_name}</td>
                  <td className="py-3 px-4">
                    <span className="text-sm text-ese-ink-blue">{member.email}</span>
                  </td>
                  <td className="py-3 px-4">
                    <span className="text-sm">{member.role_title || 'N/A'}</span>
                  </td>
                  <td className="py-3 px-4">
                    <span className="text-sm">{member.department || 'N/A'}</span>
                  </td>
                  <td className="py-3 px-4">
                    <span className="px-2 py-1 rounded-full text-xs bg-ese-accent-beige text-ese-ink-navy capitalize">
                      {member.segment ? member.segment.replace('_', ' ') : 'whole_school'}
                    </span>
                  </td>
                  <td className="py-3 px-4">
                    {member.active !== false ? (
                      <span className="px-2 py-1 rounded-full text-xs bg-green-100 text-green-800">
                        Active
                      </span>
                    ) : (
                      <span className="px-2 py-1 rounded-full text-xs bg-gray-100 text-gray-600">
                        Inactive
                      </span>
                    )}
                  </td>
                  <td className="py-3 px-4">
                    <div className="flex gap-2">
                      <button
                        onClick={() => openEditModal(member)}
                        className="text-ese-lang-900 hover:text-ese-lang-800 text-sm font-medium"
                      >
                        Edit
                      </button>
                      <button
                        onClick={() => setEvaluatorManagement({
                          email: member.email,
                          name: member.full_name
                        })}
                        className="text-ese-lang-700 hover:text-ese-lang-900 text-sm font-medium"
                        title="Manage Evaluators"
                      >
                        Evaluators
                      </button>
                      <button
                        onClick={() => handleDelete(member.email)}
                        className="text-ese-accent-terracotta hover:text-red-600 text-sm font-medium"
                      >
                        Remove
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {staff.length === 0 && (
            <div className="text-center py-12 text-ese-ink-blue">
              No staff members found. Add your first staff member to get started.
            </div>
          )}
        </div>
      </div>

      {/* Create/Edit Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h2 className="text-2xl font-heading font-bold text-ese-ink-navy mb-4">
              {editingStaff ? 'Edit Staff Member' : 'Add Staff Member'}
            </h2>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-ese-ink-navy mb-1">
                  Email *
                </label>
                <input
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  className="w-full px-4 py-2 border border-ese-accent-beige rounded-lg focus:outline-none focus:ring-2 focus:ring-ese-lang-900"
                  placeholder="staff@eternity.edu"
                  disabled={!!editingStaff}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-ese-ink-navy mb-1">
                  Full Name *
                </label>
                <input
                  type="text"
                  value={formData.full_name}
                  onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                  className="w-full px-4 py-2 border border-ese-accent-beige rounded-lg focus:outline-none focus:ring-2 focus:ring-ese-lang-900"
                  placeholder="John Doe"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-ese-ink-navy mb-1">
                    Role Title
                  </label>
                  <input
                    type="text"
                    value={formData.role_title}
                    onChange={(e) => setFormData({ ...formData, role_title: e.target.value })}
                    className="w-full px-4 py-2 border border-ese-accent-beige rounded-lg focus:outline-none focus:ring-2 focus:ring-ese-lang-900"
                    placeholder="Teacher"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-ese-ink-navy mb-1">
                    Department
                  </label>
                  <input
                    type="text"
                    value={formData.department}
                    onChange={(e) => setFormData({ ...formData, department: e.target.value })}
                    className="w-full px-4 py-2 border border-ese-accent-beige rounded-lg focus:outline-none focus:ring-2 focus:ring-ese-lang-900"
                    placeholder="Academics"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-ese-ink-navy mb-1">
                  Segment
                </label>
                <select
                  value={formData.segment}
                  onChange={(e) => setFormData({ ...formData, segment: e.target.value })}
                  className="w-full px-4 py-2 border border-ese-accent-beige rounded-lg focus:outline-none focus:ring-2 focus:ring-ese-lang-900"
                >
                  <option value="national">National</option>
                  <option value="international">International</option>
                  <option value="whole_school">Whole School</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-ese-ink-navy mb-1">
                  Hire Date
                </label>
                <input
                  type="date"
                  value={formData.hire_date}
                  onChange={(e) => setFormData({ ...formData, hire_date: e.target.value })}
                  className="w-full px-4 py-2 border border-ese-accent-beige rounded-lg focus:outline-none focus:ring-2 focus:ring-ese-lang-900"
                />
              </div>
            </div>

            <div className="flex gap-3 mt-6">
              <button
                onClick={() => {
                  setShowCreateModal(false)
                  resetForm()
                }}
                className="flex-1 px-4 py-2 border border-ese-accent-beige rounded-lg text-ese-ink-navy hover:bg-ese-ink-offwhite"
              >
                Cancel
              </button>
              <button
                onClick={handleCreate}
                disabled={!formData.email || !formData.full_name}
                className="flex-1 ese-button-primary disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {editingStaff ? 'Update' : 'Add'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Bulk Upload Modal */}
      {showBulkUpload && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h2 className="text-2xl font-heading font-bold text-ese-ink-navy mb-4">
              Bulk Upload Staff
            </h2>
            
            <div className="space-y-4">
              <p className="text-ese-ink-blue text-sm">
                Upload a CSV or Excel file with columns: email, full_name, role_title, department, segment, hire_date
              </p>
              
              <input
                ref={fileInputRef}
                type="file"
                accept=".csv,.xlsx,.xls"
                onChange={handleBulkUpload}
                className="hidden"
              />
              
              <button
                onClick={() => fileInputRef.current?.click()}
                className="w-full ese-button-secondary"
              >
                Choose File
              </button>
            </div>

            <button
              onClick={() => setShowBulkUpload(false)}
              className="w-full mt-4 px-4 py-2 border border-ese-accent-beige rounded-lg text-ese-ink-navy hover:bg-ese-ink-offwhite"
            >
              Close
            </button>
          </div>
        </div>
      )}

      {/* Evaluator Management Modal */}
      {evaluatorManagement && (
        <EvaluatorManagement
          staffEmail={evaluatorManagement.email}
          staffName={evaluatorManagement.name}
          onClose={() => setEvaluatorManagement(null)}
        />
      )}
    </div>
  )
}

export default StaffManagement
