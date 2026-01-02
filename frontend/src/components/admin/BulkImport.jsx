import { useState } from 'react'
import { useAuth } from '../../hooks/useAuth'
import { apiClient } from '../../lib/api'
import toast from 'react-hot-toast'

const BulkImport = () => {
  const { isCEO, isPNC } = useAuth()
  const [importType, setImportType] = useState('staff')
  const [file, setFile] = useState(null)
  const [loading, setLoading] = useState(false)
  const [importParams, setImportParams] = useState({
    cycle_id: '',
    month: new Date().getMonth() + 1,
    year: new Date().getFullYear()
  })

  const handleFileSelect = (e) => {
    const selectedFile = e.target.files[0]
    if (selectedFile) {
      setFile(selectedFile)
    }
  }

  const handleImport = async () => {
    if (!file) {
      toast.error('Please select a file')
      return
    }

    setLoading(true)
    try {
      const formData = new FormData()
      formData.append('file', file)

      let response

      switch (importType) {
        case 'staff':
          response = await apiClient.import.staff(formData)
          break
        case 'eom-voters':
          response = await apiClient.import.eomVoters(formData, {
            cycle_id: importParams.cycle_id,
            month: importParams.month,
            year: importParams.year,
          })
          break
        case 'eom-candidates':
          response = await apiClient.import.eomCandidates(formData)
          break
        case 'weight-matrix':
          response = await apiClient.import.weightMatrix(formData, {
            cycle_id: importParams.cycle_id,
          })
          break
      }

      const result = response?.data
      if (result?.error) {
        toast.error(result.error)
        return
      }

      toast.success(`Successfully imported ${result?.imported || result?.count || 0} items`)
      if (result?.errors && result.errors.length > 0) {
        console.warn('Import errors:', result.errors)
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to import file')
      console.error(error)
    } finally {
      setLoading(false)
    }
  }

  if (!isCEO && !isPNC) {
    return (
      <div className="ese-card text-center py-12">
        <p className="text-ese-ink-blue">Only CEO and P&C can access bulk import.</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-heading font-bold text-ese-lang-900">Bulk Import</h1>
        <p className="text-ese-ink-blue mt-1">Import data from Excel files</p>
      </div>

      <div className="ese-card">
        <h2 className="text-xl font-heading font-semibold text-ese-ink-navy mb-4">
          Select Import Type
        </h2>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-ese-ink-navy mb-2">
              Import Type
            </label>
            <select
              value={importType}
              onChange={(e) => setImportType(e.target.value)}
              className="w-full px-4 py-2 border border-ese-accent-beige rounded-lg focus:outline-none focus:ring-2 focus:ring-ese-lang-900"
            >
              <option value="staff">Staff Database</option>
              <option value="eom-voters">EOM Voters</option>
              <option value="eom-candidates">EOM Candidates</option>
              <option value="weight-matrix">Weight Matrix</option>
            </select>
          </div>

          {(importType === 'eom-voters' || importType === 'weight-matrix') && (
            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-ese-ink-navy mb-1">
                  Cycle ID
                </label>
                <input
                  type="number"
                  value={importParams.cycle_id}
                  onChange={(e) => setImportParams({ ...importParams, cycle_id: e.target.value })}
                  className="w-full px-4 py-2 border border-ese-accent-beige rounded-lg focus:outline-none focus:ring-2 focus:ring-ese-lang-900"
                  placeholder="Cycle ID"
                />
              </div>
              {importType === 'eom-voters' && (
                <>
                  <div>
                    <label className="block text-sm font-medium text-ese-ink-navy mb-1">
                      Month
                    </label>
                    <input
                      type="number"
                      value={importParams.month}
                      onChange={(e) => setImportParams({ ...importParams, month: parseInt(e.target.value) })}
                      className="w-full px-4 py-2 border border-ese-accent-beige rounded-lg focus:outline-none focus:ring-2 focus:ring-ese-lang-900"
                      min="1"
                      max="12"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-ese-ink-navy mb-1">
                      Year
                    </label>
                    <input
                      type="number"
                      value={importParams.year}
                      onChange={(e) => setImportParams({ ...importParams, year: parseInt(e.target.value) })}
                      className="w-full px-4 py-2 border border-ese-accent-beige rounded-lg focus:outline-none focus:ring-2 focus:ring-ese-lang-900"
                    />
                  </div>
                </>
              )}
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-ese-ink-navy mb-2">
              Excel File
            </label>
            <input
              type="file"
              accept=".xlsx,.xls"
              onChange={handleFileSelect}
              className="w-full px-4 py-2 border border-ese-accent-beige rounded-lg focus:outline-none focus:ring-2 focus:ring-ese-lang-900"
            />
            {file && (
              <p className="text-sm text-ese-ink-blue mt-2">
                Selected: {file.name} ({(file.size / 1024).toFixed(2)} KB)
              </p>
            )}
          </div>

          <div className="bg-ese-ink-offwhite p-4 rounded-lg">
            <p className="text-sm font-medium text-ese-ink-navy mb-2">Expected File Format:</p>
            <ul className="text-sm text-ese-ink-blue list-disc list-inside space-y-1">
              {importType === 'staff' && (
                <>
                  <li>Sheet name: "Staff_Database"</li>
                  <li>Columns: Staff ID, Segment, Name, Emails, Title</li>
                </>
              )}
              {importType === 'eom-voters' && (
                <>
                  <li>Sheet name: "Sheet1" or "EOM_ Nominators-Voters"</li>
                  <li>Columns: Staff ID, Segment, Name, Emails, Title</li>
                </>
              )}
              {importType === 'eom-candidates' && (
                <>
                  <li>Sheet name: "EOM_candidates" or "Sheet1"</li>
                  <li>Columns: Staff ID, Segment, Name, Emails, Title, Sub Title, Sub Department</li>
                </>
              )}
              {importType === 'weight-matrix' && (
                <>
                  <li>Sheet name: "Weight_Matrix"</li>
                  <li>Columns: target_group, evaluator_email, rater_context, weight, required, min_count, max_count</li>
                </>
              )}
            </ul>
          </div>

          <button
            onClick={handleImport}
            disabled={!file || loading}
            className="w-full ese-button-primary disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Importing...' : 'Import Data'}
          </button>
        </div>
      </div>
    </div>
  )
}

export default BulkImport
