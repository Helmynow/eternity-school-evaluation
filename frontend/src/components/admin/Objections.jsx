import { useState, useEffect } from 'react'
import { useAuth } from '../../hooks/useAuth'
import { apiClient } from '../../lib/api'
import toast from 'react-hot-toast'

const Objections = () => {
  const { isCEO, isPNC, user } = useAuth()
  const [objections, setObjections] = useState([])
  const [loading, setLoading] = useState(true)
  const [selectedObjection, setSelectedObjection] = useState(null)
  const [resolutionNotes, setResolutionNotes] = useState('')

  useEffect(() => {
    fetchObjections()
  }, [])

  const fetchObjections = async () => {
    try {
      setLoading(true)
      const response = await apiClient.objections.getAll()
      setObjections(response.data || [])
    } catch (error) {
      toast.error('Failed to load objections')
      console.error(error)
    } finally {
      setLoading(false)
    }
  }

  const handleResolve = async (objectionId, status) => {
    try {
      await apiClient.objections.resolve(objectionId, {
        status,
        resolution_notes: resolutionNotes,
        reviewed_by: user?.email
      })
      toast.success(`Objection ${status}`)
      setSelectedObjection(null)
      setResolutionNotes('')
      fetchObjections()
    } catch (error) {
      toast.error('Failed to resolve objection')
      console.error(error)
    }
  }

  if (!isCEO && !isPNC) {
    return (
      <div className="ese-card text-center py-12">
        <p className="text-ese-ink-blue">Only CEO and P&C can view objections.</p>
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
      <div>
        <h1 className="text-3xl font-heading font-bold text-ese-lang-900">Objections & Disputes</h1>
        <p className="text-ese-ink-blue mt-1">Review and resolve objections to EOM nominations</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="ese-card">
          <div className="text-2xl font-bold text-ese-accent-terracotta">
            {objections.filter(o => o.status === 'pending').length}
          </div>
          <div className="text-sm text-ese-ink-blue mt-1">Pending</div>
        </div>
        <div className="ese-card">
          <div className="text-2xl font-bold text-ese-int-500">
            {objections.filter(o => o.status === 'resolved').length}
          </div>
          <div className="text-sm text-ese-ink-blue mt-1">Resolved</div>
        </div>
        <div className="ese-card">
          <div className="text-2xl font-bold text-ese-ink-blue">
            {objections.length}
          </div>
          <div className="text-sm text-ese-ink-blue mt-1">Total</div>
        </div>
      </div>

      <div className="ese-card">
        <div className="space-y-4">
          {objections.length === 0 ? (
            <div className="text-center py-12 text-ese-ink-blue">
              No objections submitted yet.
            </div>
          ) : (
            objections.map((objection) => (
              <div
                key={objection.id}
                className={`p-4 rounded-lg border-2 ${
                  objection.status === 'pending'
                    ? 'border-ese-accent-terracotta bg-ese-accent-terracotta/5'
                    : 'border-ese-accent-beige'
                }`}
              >
                <div className="flex justify-between items-start mb-3">
                  <div>
                    <h3 className="font-semibold text-ese-ink-navy">
                      Objection to: {objection.nominee_name}
                    </h3>
                    <p className="text-sm text-ese-ink-blue">
                      By: {objection.objector_name} ({objection.objector_email})
                    </p>
                    <p className="text-xs text-ese-ink-blue mt-1">
                      {new Date(objection.created_at).toLocaleDateString()}
                    </p>
                  </div>
                  <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                    objection.status === 'pending'
                      ? 'bg-ese-accent-terracotta text-white'
                      : objection.status === 'resolved'
                      ? 'bg-ese-int-500 text-white'
                      : 'bg-ese-accent-beige text-ese-ink-navy'
                  }`}>
                    {objection.status}
                  </span>
                </div>

                <div className="bg-white p-3 rounded border-l-4 border-ese-accent-terracotta mb-3">
                  <p className="text-ese-ink-navy">{objection.reason}</p>
                </div>

                {objection.status === 'pending' && (
                  <div className="flex gap-2">
                    <button
                      onClick={() => {
                        setSelectedObjection(objection)
                        setResolutionNotes('')
                      }}
                      className="ese-button-primary text-sm"
                    >
                      Review
                    </button>
                  </div>
                )}

                {objection.resolution_notes && (
                  <div className="mt-3 p-3 bg-ese-int-100 rounded">
                    <p className="text-sm font-medium text-ese-ink-navy mb-1">Resolution:</p>
                    <p className="text-sm text-ese-ink-blue">{objection.resolution_notes}</p>
                    {objection.reviewed_by && (
                      <p className="text-xs text-ese-ink-blue mt-2">
                        Reviewed by {objection.reviewed_by} on {new Date(objection.reviewed_at).toLocaleDateString()}
                      </p>
                    )}
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      </div>

      {/* Resolution Modal */}
      {selectedObjection && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <h2 className="text-2xl font-heading font-bold text-ese-ink-navy mb-4">
              Review Objection
            </h2>

            <div className="space-y-4 mb-6">
              <div>
                <label className="block text-sm font-medium text-ese-ink-navy mb-1">
                  Nominee
                </label>
                <p className="text-ese-ink-blue">{selectedObjection.nominee_name}</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-ese-ink-navy mb-1">
                  Objector
                </label>
                <p className="text-ese-ink-blue">
                  {selectedObjection.objector_name} ({selectedObjection.objector_email})
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-ese-ink-navy mb-1">
                  Reason for Objection
                </label>
                <div className="bg-ese-ink-offwhite p-3 rounded border-l-4 border-ese-accent-terracotta">
                  <p className="text-ese-ink-navy">{selectedObjection.reason}</p>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-ese-ink-navy mb-1">
                  Resolution Notes
                </label>
                <textarea
                  value={resolutionNotes}
                  onChange={(e) => setResolutionNotes(e.target.value)}
                  className="w-full px-4 py-2 border border-ese-accent-beige rounded-lg focus:outline-none focus:ring-2 focus:ring-ese-lang-900"
                  rows="4"
                  placeholder="Add your resolution notes..."
                />
              </div>
            </div>

            <div className="flex gap-3">
              <button
                onClick={() => {
                  setSelectedObjection(null)
                  setResolutionNotes('')
                }}
                className="flex-1 px-4 py-2 border border-ese-accent-beige rounded-lg text-ese-ink-navy hover:bg-ese-ink-offwhite"
              >
                Cancel
              </button>
              <button
                onClick={() => handleResolve(selectedObjection.id, 'dismissed')}
                className="flex-1 ese-button-secondary"
              >
                Dismiss
              </button>
              <button
                onClick={() => handleResolve(selectedObjection.id, 'resolved')}
                className="flex-1 ese-button-primary"
              >
                Resolve
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default Objections
