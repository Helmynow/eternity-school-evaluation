import { useState, useEffect } from 'react'
import { useAPI } from '../../hooks/useAPI'
import { apiClient } from '../../lib/api'
import { useAuth } from '../../hooks/useAuth'
import toast from 'react-hot-toast'

// Import chart components
import {
  EOMWinnersTimeline,
  EOMCategoryDistribution,
  EOMDiversityMetrics,
  EOMVotingParticipation
} from './charts/EOMCharts'
import {
  EvaluationScoreDistribution,
  EvaluationParticipation,
  DomainScoreBreakdown,
  RaterContextDistribution,
  EvaluationTrends
} from './charts/EvaluationCharts'
import {
  SurveyResponseRate,
  IdentityModeDistribution,
  SurveySentiment,
  QuestionResponsePatterns,
  SurveyCompletionTimeline
} from './charts/SurveyCharts'

const Reports = () => {
  const { isCEO, isPNC } = useAuth()
  const [selectedCycle, setSelectedCycle] = useState(null)
  const [selectedSurvey, setSelectedSurvey] = useState(null)
  const [reportType, setReportType] = useState('ceo')
  const [format, setFormat] = useState('json')
  const [activeTab, setActiveTab] = useState('export') // 'export', 'eom', 'evaluations', 'surveys'

  const { data: cyclesData } = useAPI(
    () => apiClient.cycles.getAll(),
    { autoFetch: true }
  )

  const { data: surveysData } = useAPI(
    () => apiClient.survey.getAll({ status: 'active' }),
    { autoFetch: true }
  )

  useEffect(() => {
    if (cyclesData && cyclesData.length > 0 && !selectedCycle) {
      setSelectedCycle(cyclesData[0].id)
    }
  }, [cyclesData, selectedCycle])

  const handleExport = async () => {
    if (!selectedCycle) {
      toast.error('Please select a cycle')
      return
    }

    try {
      if (format === 'json') {
        const response = await apiClient.reports.getCEO(selectedCycle)
        const data = response.data
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
        const downloadUrl = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = downloadUrl
        a.download = `ceo_report_${selectedCycle}_${new Date().toISOString().split('T')[0]}.json`
        a.click()
      } else {
        const response = await apiClient.reports.exportCEO(selectedCycle, format)
        const blob = new Blob([response.data], { type: format === 'csv' ? 'text/csv' : 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
        const downloadUrl = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = downloadUrl
        a.download = `ceo_report_${selectedCycle}_${new Date().toISOString().split('T')[0]}.${format === 'csv' ? 'csv' : 'xlsx'}`
        a.click()
      }
      toast.success('Report exported successfully')
    } catch (error) {
      toast.error('Failed to export report')
      console.error(error)
    }
  }

  const handleBiasReport = async () => {
    if (!selectedCycle) {
      toast.error('Please select a cycle')
      return
    }

    try {
      const response = await apiClient.reports.getBias(selectedCycle)
      const data = response.data
      
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
      const downloadUrl = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = downloadUrl
      a.download = `bias_report_${selectedCycle}_${new Date().toISOString().split('T')[0]}.json`
      a.click()
      toast.success('Bias report exported')
    } catch (error) {
      toast.error('Failed to export bias report')
      console.error(error)
    }
  }

  const handleParticipationReport = async () => {
    if (!selectedCycle) {
      toast.error('Please select a cycle')
      return
    }

    try {
      const response = await apiClient.reports.getParticipation(selectedCycle)
      const data = response.data
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
      const downloadUrl = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = downloadUrl
      a.download = `participation_report_${selectedCycle}_${new Date().toISOString().split('T')[0]}.json`
      a.click()
      toast.success('Participation report exported')
    } catch (error) {
      toast.error('Failed to export participation report')
      console.error(error)
    }
  }

  const handleSurveyReport = async (surveyId) => {
    if (!surveyId) {
      toast.error('Please select a survey')
      return
    }

    try {
      const response = await apiClient.survey.getAnalytics(surveyId)
      const data = response.data
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
      const downloadUrl = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = downloadUrl
      a.download = `survey_report_${surveyId}_${new Date().toISOString().split('T')[0]}.json`
      a.click()
      toast.success('Survey report exported')
    } catch (error) {
      toast.error('Failed to export survey report')
      console.error(error)
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-heading font-bold text-ese-lang-900">Reports</h1>
        <p className="text-ese-ink-blue mt-1">Generate and export evaluation reports</p>
      </div>

      <div className="ese-card">
        <h2 className="text-xl font-heading font-semibold text-ese-ink-navy mb-4">
          Select Cycle
        </h2>
        {cyclesData && cyclesData.length > 0 ? (
          <select
            value={selectedCycle || ''}
            onChange={(e) => setSelectedCycle(parseInt(e.target.value))}
            className="w-full px-4 py-2 border border-ese-accent-beige rounded-lg focus:outline-none focus:ring-2 focus:ring-ese-lang-900"
          >
            {cyclesData.map((cycle) => (
              <option key={cycle.id} value={cycle.id}>
                {cycle.code} - {cycle.name} ({cycle.status})
              </option>
            ))}
          </select>
        ) : (
          <p className="text-ese-ink-blue">No cycles available</p>
        )}
      </div>

      {selectedCycle && (
        <>
          <div className="ese-card">
            <h2 className="text-xl font-heading font-semibold text-ese-ink-navy mb-4">
              CEO Report
            </h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-ese-ink-navy mb-2">
                  Export Format
                </label>
                <div className="flex gap-4">
                  <label className="flex items-center">
                    <input
                      type="radio"
                      value="json"
                      checked={format === 'json'}
                      onChange={(e) => setFormat(e.target.value)}
                      className="mr-2"
                    />
                    JSON
                  </label>
                  <label className="flex items-center">
                    <input
                      type="radio"
                      value="csv"
                      checked={format === 'csv'}
                      onChange={(e) => setFormat(e.target.value)}
                      className="mr-2"
                    />
                    CSV
                  </label>
                  <label className="flex items-center">
                    <input
                      type="radio"
                      value="excel"
                      checked={format === 'excel'}
                      onChange={(e) => setFormat(e.target.value)}
                      className="mr-2"
                    />
                    Excel
                  </label>
                </div>
              </div>
              <button
                onClick={handleExport}
                className="ese-button-primary"
              >
                Export CEO Report
              </button>
            </div>
          </div>

          <div className="ese-card">
            <h2 className="text-xl font-heading font-semibold text-ese-ink-navy mb-4">
              Bias Detection Report
            </h2>
            <button
              onClick={handleBiasReport}
              className="ese-button-secondary"
            >
              Export Bias Report
            </button>
          </div>

          {(isCEO || isPNC) && (
            <div className="ese-card">
              <h2 className="text-xl font-heading font-semibold text-ese-ink-navy mb-4">
                Participation Report
              </h2>
              <button
                onClick={handleParticipationReport}
                className="ese-button-secondary"
              >
                Export Participation Report
              </button>
            </div>
          )}
        </>
      )}

      {/* Survey Reports Section */}
      <div className="ese-card">
        <h2 className="text-xl font-heading font-semibold text-ese-ink-navy mb-4">
          Survey Reports
        </h2>
        {surveysData && surveysData.length > 0 ? (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-ese-ink-navy mb-2">
                Select Survey
              </label>
              <select
                value={selectedSurvey || ''}
                onChange={(e) => setSelectedSurvey(parseInt(e.target.value))}
                className="w-full px-4 py-2 border border-ese-accent-beige rounded-lg focus:outline-none focus:ring-2 focus:ring-ese-lang-900"
              >
                <option value="">Select a survey...</option>
                {surveysData.map((survey) => (
                  <option key={survey.id} value={survey.id}>
                    {survey.title} ({survey.status})
                  </option>
                ))}
              </select>
            </div>
            {selectedSurvey && (
              <button
                onClick={() => handleSurveyReport(selectedSurvey)}
                className="ese-button-secondary"
              >
                Export Survey Report
              </button>
            )}
          </div>
        ) : (
          <p className="text-ese-ink-blue">No active surveys available</p>
        )}
      </div>

      {/* Charts Section */}
      <div className="ese-card">
        <h2 className="text-xl font-heading font-semibold text-ese-ink-navy mb-4">
          Visual Analytics
        </h2>
        
        {/* Tab Navigation */}
        <div className="flex space-x-2 mb-6 border-b border-ese-accent-beige overflow-x-auto whitespace-nowrap">
          <button
            onClick={() => setActiveTab('export')}
            className={`shrink-0 px-4 py-2 font-medium transition-colors ${
              activeTab === 'export'
                ? 'border-b-2 border-ese-lang-900 text-ese-lang-900'
                : 'text-ese-ink-blue hover:text-ese-lang-900'
            }`}
          >
            Export Reports
          </button>
          <button
            onClick={() => setActiveTab('eom')}
            className={`shrink-0 px-4 py-2 font-medium transition-colors ${
              activeTab === 'eom'
                ? 'border-b-2 border-ese-lang-900 text-ese-lang-900'
                : 'text-ese-ink-blue hover:text-ese-lang-900'
            }`}
          >
            EOM Charts
          </button>
          <button
            onClick={() => setActiveTab('evaluations')}
            className={`shrink-0 px-4 py-2 font-medium transition-colors ${
              activeTab === 'evaluations'
                ? 'border-b-2 border-ese-lang-900 text-ese-lang-900'
                : 'text-ese-ink-blue hover:text-ese-lang-900'
            }`}
          >
            Evaluation Charts
          </button>
          <button
            onClick={() => setActiveTab('surveys')}
            className={`shrink-0 px-4 py-2 font-medium transition-colors ${
              activeTab === 'surveys'
                ? 'border-b-2 border-ese-lang-900 text-ese-lang-900'
                : 'text-ese-ink-blue hover:text-ese-lang-900'
            }`}
          >
            Survey Charts
          </button>
        </div>

        {/* Tab Content */}
        {activeTab === 'export' && (
          <div className="text-ese-ink-blue">
            <p>Use the export buttons above to download reports in various formats.</p>
          </div>
        )}

        {activeTab === 'eom' && selectedCycle && (
          <div className="space-y-6">
            <EOMWinnersTimeline cycleId={selectedCycle} />
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <EOMCategoryDistribution cycleId={selectedCycle} type="winners" />
              <EOMCategoryDistribution cycleId={selectedCycle} type="nominations" />
            </div>
            <EOMDiversityMetrics cycleId={selectedCycle} />
            <EOMVotingParticipation cycleId={selectedCycle} />
          </div>
        )}

        {activeTab === 'evaluations' && selectedCycle && (
          <div className="space-y-6">
            <EvaluationScoreDistribution cycleId={selectedCycle} />
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <EvaluationParticipation cycleId={selectedCycle} />
              <DomainScoreBreakdown cycleId={selectedCycle} />
            </div>
            <RaterContextDistribution cycleId={selectedCycle} />
            {cyclesData && cyclesData.length > 0 && (
              <EvaluationTrends cycles={cyclesData.slice(0, 6)} />
            )}
          </div>
        )}

        {activeTab === 'surveys' && selectedSurvey && (
          <div className="space-y-6">
            <SurveyResponseRate surveyId={selectedSurvey} />
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <IdentityModeDistribution surveyId={selectedSurvey} />
              <SurveySentiment surveyId={selectedSurvey} />
            </div>
            <QuestionResponsePatterns surveyId={selectedSurvey} />
            <SurveyCompletionTimeline surveyId={selectedSurvey} />
          </div>
        )}

        {activeTab === 'eom' && !selectedCycle && (
          <div className="text-ese-ink-blue text-center p-4">
            Please select a cycle to view EOM charts
          </div>
        )}

        {activeTab === 'evaluations' && !selectedCycle && (
          <div className="text-ese-ink-blue text-center p-4">
            Please select a cycle to view evaluation charts
          </div>
        )}

        {activeTab === 'surveys' && !selectedSurvey && (
          <div className="text-ese-ink-blue text-center p-4">
            Please select a survey to view survey charts
          </div>
        )}
      </div>
    </div>
  )
}

export default Reports
