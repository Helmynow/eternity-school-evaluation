import { useState, useEffect } from 'react'
import { apiClient } from '../../lib/api'
import { useAuth } from '../../hooks/useAuth'
import toast from 'react-hot-toast'

const Announcements = () => {
  const { user, isCEO, isPNC } = useAuth()
  const [announcements, setAnnouncements] = useState([])
  const [loading, setLoading] = useState(true)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [editingAnnouncement, setEditingAnnouncement] = useState(null)
  
  const [formData, setFormData] = useState({
    title: '',
    content: '',
    priority: 'normal',
    target_audience: 'all',
    expires_at: ''
  })

  useEffect(() => {
    loadAnnouncements()
  }, [])

  const loadAnnouncements = async () => {
    try {
      setLoading(true)
      const response = await apiClient.announcements.getAll({
        user_email: user?.email
      })
      setAnnouncements(response.data?.data || [])
    } catch (error) {
      console.error('Failed to load announcements:', error)
      toast.error('Failed to load announcements')
    } finally {
      setLoading(false)
    }
  }

  const handleCreate = async () => {
    if (!formData.title || !formData.content) {
      toast.error('Title and content are required')
      return
    }

    try {
      const data = {
        ...formData,
        author_email: user?.email,
        expires_at: formData.expires_at || null
      }
      
      await apiClient.announcements.create(data)
      toast.success('Announcement created successfully')
      setShowCreateModal(false)
      resetForm()
      loadAnnouncements()
    } catch (error) {
      console.error('Failed to create announcement:', error)
      toast.error(error.response?.data?.detail || 'Failed to create announcement')
    }
  }

  const handleUpdate = async () => {
    if (!formData.title || !formData.content) {
      toast.error('Title and content are required')
      return
    }

    try {
      await apiClient.announcements.update(editingAnnouncement.id, formData)
      toast.success('Announcement updated successfully')
      setShowCreateModal(false)
      resetForm()
      loadAnnouncements()
    } catch (error) {
      console.error('Failed to update announcement:', error)
      toast.error(error.response?.data?.detail || 'Failed to update announcement')
    }
  }

  const handleDelete = async (id) => {
    if (!confirm('Are you sure you want to delete this announcement?')) return

    try {
      await apiClient.announcements.delete(id)
      toast.success('Announcement deleted successfully')
      loadAnnouncements()
    } catch (error) {
      console.error('Failed to delete announcement:', error)
      toast.error('Failed to delete announcement')
    }
  }

  const resetForm = () => {
    setFormData({
      title: '',
      content: '',
      priority: 'normal',
      target_audience: 'all',
      expires_at: ''
    })
    setEditingAnnouncement(null)
  }

  const openEditModal = (announcement) => {
    setEditingAnnouncement(announcement)
    setFormData({
      title: announcement.title,
      content: announcement.content,
      priority: announcement.priority,
      target_audience: announcement.target_audience,
      expires_at: announcement.expires_at ? announcement.expires_at.split('T')[0] : ''
    })
    setShowCreateModal(true)
  }

  const getPriorityColor = (priority) => {
    const colors = {
      low: 'bg-gray-100 text-gray-800',
      normal: 'bg-blue-100 text-blue-800',
      high: 'bg-orange-100 text-orange-800',
      urgent: 'bg-red-100 text-red-800'
    }
    return colors[priority] || colors.normal
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
          <h1 className="text-3xl font-heading font-bold text-ese-lang-900">Announcements</h1>
          <p className="text-ese-ink-blue mt-1">Create and manage system announcements</p>
        </div>
        <button
          onClick={() => {
            resetForm()
            setShowCreateModal(true)
          }}
          className="ese-button-primary"
        >
          + Create Announcement
        </button>
      </div>

      {/* Announcements List */}
      <div className="ese-card">
        <div className="space-y-4">
          {announcements.length === 0 ? (
            <div className="text-center py-12 text-ese-ink-blue">
              No announcements found. Create your first announcement to get started.
            </div>
          ) : (
            announcements.map((announcement) => (
              <div
                key={announcement.id}
                className={`p-4 rounded-lg border-2 ${
                  announcement.is_active
                    ? 'border-ese-lang-900 bg-white'
                    : 'border-ese-accent-beige bg-gray-50'
                }`}
              >
                <div className="flex justify-between items-start mb-2">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <h3 className="text-lg font-semibold text-ese-ink-navy">
                        {announcement.title}
                      </h3>
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${getPriorityColor(announcement.priority)}`}>
                        {announcement.priority}
                      </span>
                      <span className="px-2 py-1 rounded-full text-xs bg-ese-accent-beige text-ese-ink-navy">
                        {announcement.target_audience}
                      </span>
                      {!announcement.is_active && (
                        <span className="px-2 py-1 rounded-full text-xs bg-gray-200 text-gray-600">
                          Inactive
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-ese-ink-blue whitespace-pre-wrap mb-2">
                      {announcement.content}
                    </p>
                    <div className="flex items-center gap-4 text-xs text-ese-ink-medium">
                      <span>By: {announcement.author_name || announcement.author_email}</span>
                      <span>Created: {new Date(announcement.created_at).toLocaleDateString()}</span>
                      {announcement.expires_at && (
                        <span>Expires: {new Date(announcement.expires_at).toLocaleDateString()}</span>
                      )}
                    </div>
                  </div>
                  <div className="flex gap-2 ml-4">
                    <button
                      onClick={() => openEditModal(announcement)}
                      className="text-ese-lang-900 hover:text-ese-lang-800 text-sm font-medium"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => handleDelete(announcement.id)}
                      className="text-ese-accent-terracotta hover:text-red-600 text-sm font-medium"
                    >
                      Delete
                    </button>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Create/Edit Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg p-6 max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <h2 className="text-2xl font-heading font-bold text-ese-ink-navy mb-4">
              {editingAnnouncement ? 'Edit Announcement' : 'Create Announcement'}
            </h2>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-ese-ink-navy mb-1">
                  Title *
                </label>
                <input
                  type="text"
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  className="w-full px-4 py-2 border border-ese-accent-beige rounded-lg focus:outline-none focus:ring-2 focus:ring-ese-lang-900"
                  placeholder="Announcement title"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-ese-ink-navy mb-1">
                  Content *
                </label>
                <textarea
                  value={formData.content}
                  onChange={(e) => setFormData({ ...formData, content: e.target.value })}
                  rows={6}
                  className="w-full px-4 py-2 border border-ese-accent-beige rounded-lg focus:outline-none focus:ring-2 focus:ring-ese-lang-900"
                  placeholder="Announcement content"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-ese-ink-navy mb-1">
                    Priority
                  </label>
                  <select
                    value={formData.priority}
                    onChange={(e) => setFormData({ ...formData, priority: e.target.value })}
                    className="w-full px-4 py-2 border border-ese-accent-beige rounded-lg focus:outline-none focus:ring-2 focus:ring-ese-lang-900"
                  >
                    <option value="low">Low</option>
                    <option value="normal">Normal</option>
                    <option value="high">High</option>
                    <option value="urgent">Urgent</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-ese-ink-navy mb-1">
                    Target Audience
                  </label>
                  <select
                    value={formData.target_audience}
                    onChange={(e) => setFormData({ ...formData, target_audience: e.target.value })}
                    className="w-full px-4 py-2 border border-ese-accent-beige rounded-lg focus:outline-none focus:ring-2 focus:ring-ese-lang-900"
                  >
                    <option value="all">All Staff</option>
                    <option value="ceo">CEO/Director</option>
                    <option value="pnc">People & Culture</option>
                    <option value="department_head">Department Heads</option>
                    <option value="staff">Staff</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-ese-ink-navy mb-1">
                  Expires At (Optional)
                </label>
                <input
                  type="datetime-local"
                  value={formData.expires_at}
                  onChange={(e) => setFormData({ ...formData, expires_at: e.target.value })}
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
                onClick={editingAnnouncement ? handleUpdate : handleCreate}
                disabled={!formData.title || !formData.content}
                className="flex-1 ese-button-primary disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {editingAnnouncement ? 'Update' : 'Create'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default Announcements
