import { useState, useEffect } from 'react'
import { useAPI } from '../../hooks/useAPI'
import { apiClient } from '../../lib/api'
import toast from 'react-hot-toast'

const EOMHallOfFame = () => {
  const [winners, setWinners] = useState([])
  const [loading, setLoading] = useState(true)
  const [filters, setFilters] = useState({
    category: '',
    year: '',
    segment: ''
  })

  useEffect(() => {
    loadHallOfFame()
  }, [filters])

  const loadHallOfFame = async () => {
    try {
      setLoading(true)
      // Use the eom_hall_of_fame view
      const response = await apiClient.get('/api/v2/eom/hall-of-fame', {
        params: filters
      })
      setWinners(response.data || [])
    } catch (error) {
      console.error('Failed to load Hall of Fame:', error)
      toast.error('Failed to load Hall of Fame data')
    } finally {
      setLoading(false)
    }
  }

  const categoryColors = {
    outstanding_leadership: 'bg-purple-100 text-purple-800',
    team_spirit: 'bg-blue-100 text-blue-800',
    innovation: 'bg-green-100 text-green-800',
    rising_star: 'bg-yellow-100 text-yellow-800',
    service_excellence: 'bg-orange-100 text-orange-800'
  }

  const getCategoryName = (category) => {
    const names = {
      outstanding_leadership: 'Outstanding Leadership',
      team_spirit: 'Team Spirit',
      innovation: 'Innovation',
      rising_star: 'Rising Star',
      service_excellence: 'Service Excellence'
    }
    return names[category] || category
  }

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-ese-lang-900"></div>
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-heading font-bold text-ese-ink-navy mb-2">
          <span className="flex items-center gap-2">
            <img src="/assets/icons/trophy.png" alt="Trophy" className="w-8 h-8" onError={(e) => { e.target.style.display = 'none' }} />
            Hall of Fame
          </span>
        </h1>
        <p className="text-ese-ink-navy/70">
          Celebrating excellence and recognizing outstanding contributions
        </p>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow-sm p-4 mb-6 grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <label className="block text-sm font-medium text-ese-ink-navy mb-2">
            Category
          </label>
          <select
            value={filters.category}
            onChange={(e) => setFilters({ ...filters, category: e.target.value })}
            className="w-full px-3 py-2 border border-ese-accent-beige rounded-md focus:outline-none focus:ring-2 focus:ring-ese-accent-light-blue"
          >
            <option value="">All Categories</option>
            <option value="outstanding_leadership">Outstanding Leadership</option>
            <option value="team_spirit">Team Spirit</option>
            <option value="innovation">Innovation</option>
            <option value="rising_star">Rising Star</option>
            <option value="service_excellence">Service Excellence</option>
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium text-ese-ink-navy mb-2">
            Year
          </label>
          <select
            value={filters.year}
            onChange={(e) => setFilters({ ...filters, year: e.target.value })}
            className="w-full px-3 py-2 border border-ese-accent-beige rounded-md focus:outline-none focus:ring-2 focus:ring-ese-accent-light-blue"
          >
            <option value="">All Years</option>
            {Array.from({ length: 5 }, (_, i) => new Date().getFullYear() - i).map(year => (
              <option key={year} value={year}>{year}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium text-ese-ink-navy mb-2">
            Segment
          </label>
          <select
            value={filters.segment}
            onChange={(e) => setFilters({ ...filters, segment: e.target.value })}
            className="w-full px-3 py-2 border border-ese-accent-beige rounded-md focus:outline-none focus:ring-2 focus:ring-ese-accent-light-blue"
          >
            <option value="">All Segments</option>
            <option value="national">National</option>
            <option value="international">International</option>
            <option value="whole_school">Whole School</option>
          </select>
        </div>
      </div>

      {/* Winners Grid */}
      {winners.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-lg shadow-sm">
          <p className="text-ese-ink-navy/70">No winners found for the selected filters.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {winners.map((winner) => (
            <div
              key={winner.id}
              className="bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow p-6"
            >
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h3 className="text-xl font-heading font-semibold text-ese-ink-navy">
                    {winner.winner_name}
                  </h3>
                  <p className="text-sm text-ese-ink-navy/70">{winner.role_title}</p>
                  <p className="text-xs text-ese-ink-navy/60">{winner.department}</p>
                </div>
                <span className={`px-3 py-1 rounded-full text-xs font-medium ${categoryColors[winner.category] || 'bg-gray-100 text-gray-800'}`}>
                  {getCategoryName(winner.category)}
                </span>
              </div>

              {winner.nomination_reason && (
                <p className="text-sm text-ese-ink-navy/80 mb-4 italic">
                  "{winner.nomination_reason}"
                </p>
              )}

              <div className="border-t border-ese-accent-beige pt-4 mt-4">
                <div className="flex justify-between text-sm">
                  <span className="text-ese-ink-navy/70">Cycle:</span>
                  <span className="font-medium text-ese-ink-navy">{winner.cycle_name}</span>
                </div>
                <div className="flex justify-between text-sm mt-2">
                  <span className="text-ese-ink-navy/70">Votes:</span>
                  <span className="font-medium text-ese-ink-navy">
                    {winner.total_votes} ({winner.weighted_votes?.toFixed(1)} weighted)
                  </span>
                </div>
                <div className="flex justify-between text-sm mt-2">
                  <span className="text-ese-ink-navy/70">Date:</span>
                  <span className="font-medium text-ese-ink-navy">
                    {new Date(winner.won_at).toLocaleDateString()}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default EOMHallOfFame
