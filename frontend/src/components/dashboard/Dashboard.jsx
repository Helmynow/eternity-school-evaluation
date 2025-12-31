import { useState, useEffect } from 'react'
import { useAPI } from '../../hooks/useAPI'
import { apiClient } from '../../lib/api'
import { useAuth } from '../../hooks/useAuth'
import toast from 'react-hot-toast'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, PieChart, Pie, Cell } from 'recharts'

const Dashboard = () => {
  const { role, isCEO, isPNC } = useAuth()
  const [selectedCycle, setSelectedCycle] = useState(null)
  const [cycles, setCycles] = useState([])
  const [participation, setParticipation] = useState(null)
  const [biasReport, setBiasReport] = useState(null)
  const [loading, setLoading] = useState(true)

  // Fetch cycles
  const { data: cyclesData, loading: cyclesLoading } = useAPI(
    () => apiClient.cycles.getAll(),
    { autoFetch: true }
  )

  useEffect(() => {
    if (cyclesData) {
      setCycles(cyclesData)
      if (cyclesData.length > 0 && !selectedCycle) {
        setSelectedCycle(cyclesData[0].id)
      }
    }
  }, [cyclesData, selectedCycle])

  // Fetch participation and bias data when cycle is selected
  useEffect(() => {
    if (selectedCycle) {
      loadCycleData(selectedCycle)
    }
  }, [selectedCycle])

  const loadCycleData = async (cycleId) => {
    setLoading(true)
    try {
      // Load participation stats
      const participationRes = await apiClient.dashboard.getParticipation(cycleId)
      setParticipation(participationRes.data)

      // Load bias report if available
      try {
        const biasRes = await apiClient.bias.getReport(cycleId)
        setBiasReport(biasRes.data)
      } catch (err) {
        // Bias report might not exist yet
        console.log('Bias report not available')
      }
    } catch (error) {
      toast.error('Failed to load cycle data')
    } finally {
      setLoading(false)
    }
  }

  const COLORS = {
    lang: '#094773',
    int: '#2C5B4C',
    mustard: '#E4A740',
    terracotta: '#C88167',
  }

  const participationChartData = participation ? [
    { name: 'EOM Nominations', value: participation.eom_nominations || 0, color: COLORS.mustard },
    { name: 'EOM Votes', value: participation.eom_votes || 0, color: COLORS.terracotta },
    { name: 'MRE Evaluations', value: participation.mre_evaluations || 0, color: COLORS.lang },
    { name: 'Completed', value: participation.completed || 0, color: COLORS.int },
  ] : []

  if (cyclesLoading || loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-ese-lang-900 mx-auto"></div>
          <p className="mt-4 text-ese-ink-navy">Loading dashboard...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-heading font-bold text-ese-lang-900">Dashboard</h1>
          <p className="text-ese-ink-blue mt-1">Evaluation & Recognition Overview</p>
        </div>
        <button
          onClick={() => selectedCycle && loadCycleData(selectedCycle)}
          className="ese-button-secondary"
        >
          Refresh
        </button>
      </div>

      {/* Cycle Selector */}
      {cycles.length > 0 && (
        <div className="ese-card">
          <h2 className="text-xl font-heading font-semibold text-ese-ink-navy mb-4">
            Select Cycle
          </h2>
          <div className="flex flex-wrap gap-2">
            {cycles.map((cycle) => (
              <button
                key={cycle.id}
                onClick={() => setSelectedCycle(cycle.id)}
                className={`
                  px-4 py-2 rounded-lg font-medium transition-all
                  ${selectedCycle === cycle.id
                    ? 'bg-ese-lang-900 text-white shadow-lg'
                    : 'bg-ese-accent-beige text-ese-ink-navy hover:bg-ese-accent-olive'
                  }
                `}
              >
                {cycle.code} - {cycle.name}
              </button>
            ))}
          </div>
        </div>
      )}

      {selectedCycle && (
        <>
          {/* Participation Overview */}
          {participation && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="ese-card">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-ese-ink-blue">EOM Nominations</p>
                    <p className="text-2xl font-bold text-ese-ink-navy mt-1">
                      {participation.eom_nominations || 0}
                    </p>
                  </div>
                  <div className="w-12 h-12 rounded-full bg-ese-accent-mustard/20 flex items-center justify-center">
                    <span className="text-2xl">⭐</span>
                  </div>
                </div>
              </div>

              <div className="ese-card">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-ese-ink-blue">EOM Votes</p>
                    <p className="text-2xl font-bold text-ese-ink-navy mt-1">
                      {participation.eom_votes || 0}
                    </p>
                  </div>
                  <div className="w-12 h-12 rounded-full bg-ese-accent-terracotta/20 flex items-center justify-center">
                    <span className="text-2xl">🗳️</span>
                  </div>
                </div>
              </div>

              <div className="ese-card">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-ese-ink-blue">MRE Evaluations</p>
                    <p className="text-2xl font-bold text-ese-ink-navy mt-1">
                      {participation.mre_evaluations || 0}
                    </p>
                  </div>
                  <div className="w-12 h-12 rounded-full bg-ese-lang-200 flex items-center justify-center">
                    <span className="text-2xl">📝</span>
                  </div>
                </div>
              </div>

              <div className="ese-card">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-ese-ink-blue">Completion Rate</p>
                    <p className="text-2xl font-bold text-ese-ink-navy mt-1">
                      {participation.completion_rate ? `${(participation.completion_rate * 100).toFixed(1)}%` : 'N/A'}
                    </p>
                  </div>
                  <div className="w-12 h-12 rounded-full bg-ese-int-300 flex items-center justify-center">
                    <span className="text-2xl">✓</span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Participation Chart */}
          {participationChartData.length > 0 && (
            <div className="ese-card">
              <h2 className="text-xl font-heading font-semibold text-ese-ink-navy mb-4">
                Participation Overview
              </h2>
              <div className="h-64">
                <BarChart width={600} height={250} data={participationChartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="value" fill={COLORS.lang} />
                </BarChart>
              </div>
            </div>
          )}

          {/* Bias Report */}
          {biasReport && (
            <div className="ese-card">
              <h2 className="text-xl font-heading font-semibold text-ese-ink-navy mb-4">
                Bias Detection Report
              </h2>
              <div className="space-y-4">
                <div className="flex items-center justify-between p-4 bg-ese-accent-beige rounded-lg">
                  <span className="font-medium text-ese-ink-navy">Overall Bias Score</span>
                  <span className={`
                    text-2xl font-bold
                    ${biasReport.overall_bias_score > 0.7 ? 'text-ese-accent-terracotta' : 
                      biasReport.overall_bias_score > 0.4 ? 'text-ese-accent-mustard' : 
                      'text-ese-int-900'}
                  `}>
                    {(biasReport.overall_bias_score * 100).toFixed(1)}%
                  </span>
                </div>

                {biasReport.findings && biasReport.findings.length > 0 && (
                  <div className="space-y-2">
                    <h3 className="font-semibold text-ese-ink-navy">Key Findings</h3>
                    {biasReport.findings.slice(0, 5).map((finding, idx) => (
                      <div key={idx} className="p-3 bg-ese-ink-offwhite rounded-lg">
                        <div className="flex items-center justify-between">
                          <span className="font-medium text-ese-ink-navy">{finding.bias_type}</span>
                          <span className={`
                            text-xs px-2 py-1 rounded-full
                            ${finding.severity === 'high' ? 'bg-ese-accent-terracotta text-white' :
                              finding.severity === 'medium' ? 'bg-ese-accent-mustard text-ese-ink-navy' :
                              'bg-ese-int-300 text-ese-int-900'}
                          `}>
                            {finding.severity}
                          </span>
                        </div>
                        <p className="text-sm text-ese-ink-blue mt-1">{finding.description}</p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Admin Only Sections */}
          {(isCEO || isPNC) && (
            <div className="ese-card">
              <h2 className="text-xl font-heading font-semibold text-ese-ink-navy mb-4">
                Admin Actions
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <button
                  onClick={() => {
                    apiClient.bias.generateReport(selectedCycle)
                      .then(() => toast.success('Bias report generated'))
                      .catch(() => toast.error('Failed to generate report'))
                  }}
                  className="ese-button-primary"
                >
                  Generate Bias Report
                </button>
                <button
                  onClick={() => {
                    // Export functionality
                    toast.info('Export feature coming soon')
                  }}
                  className="ese-button-secondary"
                >
                  Export Report
                </button>
                <button
                  onClick={() => {
                    // Analytics view
                    toast.info('Analytics view coming soon')
                  }}
                  className="bg-ese-accent-mustard text-ese-ink-navy px-6 py-3 rounded-ese-pill font-medium hover:opacity-90"
                >
                  View Analytics
                </button>
              </div>
            </div>
          )}
        </>
      )}

      {!selectedCycle && cycles.length === 0 && (
        <div className="ese-card text-center py-12">
          <p className="text-ese-ink-blue">No cycles available. Please create a cycle first.</p>
        </div>
      )}
    </div>
  )
}

export default Dashboard

