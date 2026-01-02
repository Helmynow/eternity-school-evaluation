import { useState, useEffect } from 'react'
import { useAuth } from '../../hooks/useAuth'
import { apiClient } from '../../lib/api'
import toast from 'react-hot-toast'
import LoadingSkeleton from '../common/LoadingSkeleton'

const Settings = () => {
  const { isCEO } = useAuth()
  const [settings, setSettings] = useState({
    emailNotifications: true,
    autoActivateCycles: false,
    requireApproval: true,
    defaultRotationPeriod: 'term',
    maxNominationsPerPerson: 1,
    evaluationDeadlineDays: 30
  })
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (isCEO) {
      loadSettings()
    }
  }, [isCEO])

  const loadSettings = async () => {
    try {
      setLoading(true)
      const response = await apiClient.settings.get()
      if (response.data) {
        setSettings({
          emailNotifications: response.data.email_notifications ?? true,
          autoActivateCycles: response.data.auto_activate_cycles ?? false,
          requireApproval: response.data.require_approval ?? true,
          defaultRotationPeriod: response.data.default_rotation_period ?? 'term',
          maxNominationsPerPerson: response.data.max_nominations_per_person ?? 1,
          evaluationDeadlineDays: response.data.evaluation_deadline_days ?? 30
        })
      }
    } catch (error) {
      // If settings don't exist yet, use defaults (that's OK)
      if (error.response?.status !== 404) {
        console.error('Error loading settings:', error)
        toast.error('Failed to load settings')
      }
    } finally {
      setLoading(false)
    }
  }

  const handleSave = async () => {
    try {
      setSaving(true)
      const settingsData = {
        email_notifications: settings.emailNotifications,
        auto_activate_cycles: settings.autoActivateCycles,
        require_approval: settings.requireApproval,
        default_rotation_period: settings.defaultRotationPeriod,
        max_nominations_per_person: settings.maxNominationsPerPerson,
        evaluation_deadline_days: settings.evaluationDeadlineDays
      }
      
      // Try update first, then create if it doesn't exist
      try {
        await apiClient.settings.update(settingsData)
      } catch (updateError) {
        if (updateError.response?.status === 404) {
          // Settings don't exist, create them
          await apiClient.settings.save(settingsData)
        } else {
          throw updateError
        }
      }
      
      toast.success('Settings saved successfully')
    } catch (error) {
      console.error('Error saving settings:', error)
      toast.error(error.response?.data?.detail || 'Failed to save settings')
    } finally {
      setSaving(false)
    }
  }

  if (!isCEO) {
    return (
      <div className="ese-card text-center py-12">
        <p className="text-ese-ink-blue">Only CEO can access settings.</p>
      </div>
    )
  }

  if (loading) {
    return <LoadingSkeleton type="dashboard" count={1} />
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-heading font-bold text-ese-lang-900">Settings</h1>
        <p className="text-ese-ink-blue mt-1">Configure system settings and preferences</p>
      </div>

      {/* Email Notifications */}
      <div className="ese-card">
        <h2 className="text-xl font-heading font-semibold text-ese-ink-navy mb-4">
          Email Notifications
        </h2>
        <div className="space-y-4">
          <label className="flex items-center justify-between cursor-pointer">
            <div>
              <span className="font-medium text-ese-ink-navy">Enable Email Notifications</span>
              <p className="text-sm text-ese-ink-blue">Send emails to winners, voters, and evaluators</p>
            </div>
            <input
              type="checkbox"
              checked={settings.emailNotifications}
              onChange={(e) => setSettings({ ...settings, emailNotifications: e.target.checked })}
              className="w-5 h-5 text-ese-lang-900 rounded focus:ring-ese-lang-900"
            />
          </label>
        </div>
      </div>

      {/* Cycle Management */}
      <div className="ese-card">
        <h2 className="text-xl font-heading font-semibold text-ese-ink-navy mb-4">
          Cycle Management
        </h2>
        <div className="space-y-4">
          <label className="flex items-center justify-between cursor-pointer">
            <div>
              <span className="font-medium text-ese-ink-navy">Auto-Activate New Cycles</span>
              <p className="text-sm text-ese-ink-blue">Automatically activate cycles when created</p>
            </div>
            <input
              type="checkbox"
              checked={settings.autoActivateCycles}
              onChange={(e) => setSettings({ ...settings, autoActivateCycles: e.target.checked })}
              className="w-5 h-5 text-ese-lang-900 rounded focus:ring-ese-lang-900"
            />
          </label>
        </div>
      </div>

      {/* Approval Workflow */}
      <div className="ese-card">
        <h2 className="text-xl font-heading font-semibold text-ese-ink-navy mb-4">
          Approval Workflow
        </h2>
        <div className="space-y-4">
          <label className="flex items-center justify-between cursor-pointer">
            <div>
              <span className="font-medium text-ese-ink-navy">Require Approval</span>
              <p className="text-sm text-ese-ink-blue">Require approval before nominations/evaluations are finalized</p>
            </div>
            <input
              type="checkbox"
              checked={settings.requireApproval}
              onChange={(e) => setSettings({ ...settings, requireApproval: e.target.checked })}
              className="w-5 h-5 text-ese-lang-900 rounded focus:ring-ese-lang-900"
            />
          </label>
        </div>
      </div>

      {/* EOM Settings */}
      <div className="ese-card">
        <h2 className="text-xl font-heading font-semibold text-ese-ink-navy mb-4">
          Employee of the Month
        </h2>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-ese-ink-navy mb-1">
              Default Rotation Period
            </label>
            <select
              value={settings.defaultRotationPeriod}
              onChange={(e) => setSettings({ ...settings, defaultRotationPeriod: e.target.value })}
              className="w-full px-4 py-2 border border-ese-accent-beige rounded-lg focus:outline-none focus:ring-2 focus:ring-ese-lang-900"
            >
              <option value="term">Term</option>
              <option value="quarter">Quarter</option>
              <option value="month">Month</option>
              <option value="year">Year</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-ese-ink-navy mb-1">
              Max Nominations Per Person
            </label>
            <input
              type="number"
              value={settings.maxNominationsPerPerson}
              onChange={(e) => setSettings({ ...settings, maxNominationsPerPerson: parseInt(e.target.value) })}
              className="w-full px-4 py-2 border border-ese-accent-beige rounded-lg focus:outline-none focus:ring-2 focus:ring-ese-lang-900"
              min="1"
              max="10"
            />
          </div>
        </div>
      </div>

      {/* Evaluation Settings */}
      <div className="ese-card">
        <h2 className="text-xl font-heading font-semibold text-ese-ink-navy mb-4">
          Evaluation Settings
        </h2>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-ese-ink-navy mb-1">
              Evaluation Deadline (Days)
            </label>
            <input
              type="number"
              value={settings.evaluationDeadlineDays}
              onChange={(e) => setSettings({ ...settings, evaluationDeadlineDays: parseInt(e.target.value) })}
              className="w-full px-4 py-2 border border-ese-accent-beige rounded-lg focus:outline-none focus:ring-2 focus:ring-ese-lang-900"
              min="1"
              max="365"
            />
            <p className="text-sm text-ese-ink-blue mt-1">Number of days after cycle start to complete evaluations</p>
          </div>
        </div>
      </div>

      <div className="flex justify-end">
        <button
          onClick={handleSave}
          disabled={saving}
          className="ese-button-primary disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {saving ? 'Saving...' : 'Save Settings'}
        </button>
      </div>
    </div>
  )
}

export default Settings
