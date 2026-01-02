import { useState, useEffect } from 'react'
import { apiClient } from '../../lib/api'
import { useAuth } from '../../hooks/useAuth'
import toast from 'react-hot-toast'
import IdentityModeSelector from './IdentityModeSelector'
import IdentityReveal from './IdentityReveal'

/**
 * Test component for identity mode transitions and reveal functionality
 * This component tests:
 * 1. Identity mode selection
 * 2. Session initialization
 * 3. Mode switching
 * 4. Identity reveal functionality
 */
const IdentityModeTest = ({ surveyId = null }) => {
  const { user } = useAuth()
  const [currentMode, setCurrentMode] = useState(null)
  const [sessionToken, setSessionToken] = useState(null)
  const [testResults, setTestResults] = useState([])
  const [loading, setLoading] = useState(false)

  const addTestResult = (test, status, message, data = null) => {
    setTestResults((prev) => [
      ...prev,
      {
        id: Date.now(),
        test,
        status, // 'success', 'error', 'warning'
        message,
        data,
        timestamp: new Date().toISOString(),
      },
    ])
  }

  const testModeSelection = async (mode) => {
    setLoading(true)
    try {
      addTestResult('Mode Selection', 'info', `Testing mode selection: ${mode}`)

      const sessionRes = await apiClient.hybridIdentity.initializeSession({
        user_email: user?.email,
        identity_mode: mode,
        survey_id: surveyId ? parseInt(surveyId) : null,
      })

      if (sessionRes.data?.session_token) {
        setSessionToken(sessionRes.data.session_token)
        setCurrentMode(mode)
        addTestResult(
          'Mode Selection',
          'success',
          `Successfully initialized ${mode} mode session`,
          { session_token: sessionRes.data.session_token }
        )
        return true
      } else {
        addTestResult('Mode Selection', 'error', 'Session token not received')
        return false
      }
    } catch (error) {
      addTestResult(
        'Mode Selection',
        'error',
        `Failed to initialize session: ${error.message}`,
        error
      )
      return false
    } finally {
      setLoading(false)
    }
  }

  const testModeSwitch = async (newMode) => {
    if (!sessionToken) {
      addTestResult('Mode Switch', 'warning', 'No active session to switch')
      return false
    }

    setLoading(true)
    try {
      addTestResult('Mode Switch', 'info', `Switching from ${currentMode} to ${newMode}`)

      const switchRes = await apiClient.hybridIdentity.switchMode({
        session_token: sessionToken,
        new_mode: newMode,
      })

      if (switchRes.data) {
        setCurrentMode(newMode)
        addTestResult(
          'Mode Switch',
          'success',
          `Successfully switched to ${newMode} mode`,
          switchRes.data
        )
        return true
      } else {
        addTestResult('Mode Switch', 'error', 'Mode switch failed')
        return false
      }
    } catch (error) {
      addTestResult(
        'Mode Switch',
        'error',
        `Failed to switch mode: ${error.message}`,
        error
      )
      return false
    } finally {
      setLoading(false)
    }
  }

  const testIdentityReveal = async (revealType, conditions = {}) => {
    if (!sessionToken) {
      addTestResult('Identity Reveal', 'warning', 'No active session for reveal')
      return false
    }

    setLoading(true)
    try {
      addTestResult('Identity Reveal', 'info', `Testing reveal type: ${revealType}`)

      const revealRes = await apiClient.hybridIdentity.processReveal(
        user?.email,
        revealType,
        Object.keys(conditions).length > 0 ? conditions : null
      )

      if (revealRes.data) {
        addTestResult(
          'Identity Reveal',
          'success',
          `Successfully processed ${revealType} reveal`,
          revealRes.data
        )
        return true
      } else {
        addTestResult('Identity Reveal', 'error', 'Reveal processing failed')
        return false
      }
    } catch (error) {
      addTestResult(
        'Identity Reveal',
        'error',
        `Failed to process reveal: ${error.message}`,
        error
      )
      return false
    } finally {
      setLoading(false)
    }
  }

  const runAllTests = async () => {
    setTestResults([])
    addTestResult('Test Suite', 'info', 'Starting identity mode tests...')

    // Test 1: Initialize anonymous mode
    const anonymousSuccess = await testModeSelection('anonymous')
    if (!anonymousSuccess) return

    // Test 2: Switch to conditional mode
    await new Promise((resolve) => setTimeout(resolve, 1000))
    await testModeSwitch('conditional')

    // Test 3: Switch to identified mode
    await new Promise((resolve) => setTimeout(resolve, 1000))
    await testModeSwitch('identified')

    // Test 4: Test identity reveal
    await new Promise((resolve) => setTimeout(resolve, 1000))
    await testIdentityReveal('full')

    addTestResult('Test Suite', 'success', 'All tests completed')
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'success':
        return 'bg-green-100 text-green-800 border-green-300'
      case 'error':
        return 'bg-red-100 text-red-800 border-red-300'
      case 'warning':
        return 'bg-yellow-100 text-yellow-800 border-yellow-300'
      case 'info':
        return 'bg-blue-100 text-blue-800 border-blue-300'
      default:
        return 'bg-gray-100 text-gray-800 border-gray-300'
    }
  }

  return (
    <div className="p-6 space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-ese-ink-navy mb-2">
          Identity Mode Testing
        </h2>
        <p className="text-ese-ink-medium">
          Test identity mode transitions and reveal functionality
        </p>
      </div>

      {/* Current Status */}
      <div className="bg-white rounded-lg shadow-md p-6 border border-ese-ink-light">
        <h3 className="text-lg font-semibold text-ese-ink-navy mb-4">Current Status</h3>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-sm text-ese-ink-medium">Current Mode:</p>
            <p className="text-lg font-medium text-ese-ink-navy">
              {currentMode || 'None'}
            </p>
          </div>
          <div>
            <p className="text-sm text-ese-ink-medium">Session Token:</p>
            <p className="text-xs font-mono text-ese-ink-medium truncate">
              {sessionToken || 'Not initialized'}
            </p>
          </div>
        </div>
      </div>

      {/* Mode Selection */}
      <div className="bg-white rounded-lg shadow-md p-6 border border-ese-ink-light">
        <h3 className="text-lg font-semibold text-ese-ink-navy mb-4">
          Test Mode Selection
        </h3>
        <IdentityModeSelector
          onSelect={testModeSelection}
          initialMode={currentMode}
        />
      </div>

      {/* Mode Switching */}
      {sessionToken && (
        <div className="bg-white rounded-lg shadow-md p-6 border border-ese-ink-light">
          <h3 className="text-lg font-semibold text-ese-ink-navy mb-4">
            Test Mode Switching
          </h3>
          <div className="flex space-x-2">
            {['anonymous', 'conditional', 'identified'].map((mode) => (
              <button
                key={mode}
                onClick={() => testModeSwitch(mode)}
                disabled={loading || currentMode === mode}
                className="px-4 py-2 bg-ese-lang-900 text-white rounded-lg hover:bg-ese-lang-800 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Switch to {mode}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Identity Reveal */}
      {sessionToken && (
        <div className="bg-white rounded-lg shadow-md p-6 border border-ese-ink-light">
          <h3 className="text-lg font-semibold text-ese-ink-navy mb-4">
            Test Identity Reveal
          </h3>
          <IdentityReveal
            surveyId={surveyId}
            onRevealComplete={(data) => {
              addTestResult('Identity Reveal', 'success', 'Reveal completed', data)
            }}
          />
        </div>
      )}

      {/* Test Controls */}
      <div className="bg-white rounded-lg shadow-md p-6 border border-ese-ink-light">
        <h3 className="text-lg font-semibold text-ese-ink-navy mb-4">Test Controls</h3>
        <button
          onClick={runAllTests}
          disabled={loading}
          className="px-6 py-2 bg-ese-int-700 text-white rounded-lg hover:bg-ese-int-800 disabled:opacity-50"
        >
          {loading ? 'Running Tests...' : 'Run All Tests'}
        </button>
        <button
          onClick={() => setTestResults([])}
          className="ml-4 px-6 py-2 bg-ese-ink-light text-ese-ink-navy rounded-lg hover:bg-ese-ink-medium"
        >
          Clear Results
        </button>
      </div>

      {/* Test Results */}
      {testResults.length > 0 && (
        <div className="bg-white rounded-lg shadow-md p-6 border border-ese-ink-light">
          <h3 className="text-lg font-semibold text-ese-ink-navy mb-4">Test Results</h3>
          <div className="space-y-2 max-h-96 overflow-y-auto">
            {testResults.map((result) => (
              <div
                key={result.id}
                className={`p-4 rounded-lg border-2 ${getStatusColor(result.status)}`}
              >
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <p className="font-semibold">{result.test}</p>
                    <p className="text-sm mt-1">{result.message}</p>
                    <p className="text-xs mt-1 opacity-75">
                      {new Date(result.timestamp).toLocaleTimeString()}
                    </p>
                    {result.data && (
                      <details className="mt-2">
                        <summary className="cursor-pointer text-xs">View Data</summary>
                        <pre className="text-xs mt-2 bg-white p-2 rounded overflow-auto">
                          {JSON.stringify(result.data, null, 2)}
                        </pre>
                      </details>
                    )}
                  </div>
                  <span className="text-xs px-2 py-1 rounded-full bg-white">
                    {result.status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default IdentityModeTest
