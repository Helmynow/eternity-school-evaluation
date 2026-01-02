import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import AdminDashboard from '../AdminDashboard'
import { useAuth } from '../../../hooks/useAuth'
import { useAdmin } from '../../../hooks/useAdmin'
import toast from 'react-hot-toast'

jest.mock('../../../hooks/useAuth')
jest.mock('../../../hooks/useAdmin')
jest.mock('../BiasAlerts', () => ({
  __esModule: true,
  default: () => <div>Bias Alerts Component</div>,
}))
jest.mock('react-hot-toast', () => ({
  __esModule: true,
  default: {
    success: jest.fn(),
    error: jest.fn(),
    loading: jest.fn(),
  },
}))

const renderWithRouter = (component) => {
  return render(<BrowserRouter>{component}</BrowserRouter>)
}

describe('AdminDashboard', () => {
  const mockUser = {
    email: 'admin@example.com',
    id: '123',
  }

  const mockDashboard = {
    total_surveys: 10,
    active_surveys: 5,
    total_responses: 100,
    action_items: [
      { id: 1, type: 'objection', title: 'Pending Objection', priority: 'high' },
      { id: 2, type: 'notification', title: 'Unread Notification', priority: 'medium' },
    ],
  }

  const mockOverviewCards = [
    { title: 'Surveys', value: 10, change: 2 },
    { title: 'Responses', value: 100, change: 15 },
    { title: 'Users', value: 50, change: 0 },
  ]

  const mockRealTimeMetrics = {
    active_users: 25,
    api_requests: 120,
    avg_response_time: 150,
    usage_trends: [
      { date: '2024-01-01', users: 20, requests: 100 },
      { date: '2024-01-02', users: 25, requests: 120 },
    ],
    feature_usage: [
      { feature: 'surveys', count: 80 },
      { feature: 'evaluations', count: 60 },
    ],
  }

  const mockIdentityAnalytics = {
    total_sessions: 500,
    mode_count: 3,
    reveals_processed: 50,
    mode_distribution: [
      { name: 'anonymous', value: 200 },
      { name: 'conditional', value: 150 },
      { name: 'identified', value: 150 },
    ],
    reveal_methods: [
      { method: 'full', count: 30 },
      { method: 'partial', count: 20 },
    ],
  }

  beforeEach(() => {
    jest.clearAllMocks()
    useAuth.mockReturnValue({
      user: mockUser,
      isCEO: true,
      isPNC: false,
    })
    useAdmin.mockReturnValue({
      dashboard: null,
      overviewCards: null,
      realTimeMetrics: null,
      identityAnalytics: null,
      loading: false,
      fetchDashboard: jest.fn(),
      fetchOverviewCards: jest.fn(),
      fetchRealTimeMetrics: jest.fn(),
      fetchIdentityAnalytics: jest.fn(),
    })
  })

  describe('Access Control', () => {
    it('should show access denied for non-admin users', () => {
      useAuth.mockReturnValue({
        user: mockUser,
        isCEO: false,
        isPNC: false,
      })

      renderWithRouter(<AdminDashboard />)

      expect(screen.getByText('Access Denied')).toBeInTheDocument()
      expect(screen.getByText('Admin access required')).toBeInTheDocument()
    })

    it('should allow access for CEO', () => {
      useAuth.mockReturnValue({
        user: mockUser,
        isCEO: true,
        isPNC: false,
      })

      renderWithRouter(<AdminDashboard />)

      expect(screen.queryByText('Access Denied')).not.toBeInTheDocument()
    })

    it('should allow access for PNC', () => {
      useAuth.mockReturnValue({
        user: mockUser,
        isCEO: false,
        isPNC: true,
      })

      renderWithRouter(<AdminDashboard />)

      expect(screen.queryByText('Access Denied')).not.toBeInTheDocument()
    })
  })

  describe('Data Loading', () => {
    it('should fetch dashboard data on mount', () => {
      const mockFetchDashboard = jest.fn()
      const mockFetchOverviewCards = jest.fn()
      const mockFetchRealTimeMetrics = jest.fn()
      const mockFetchIdentityAnalytics = jest.fn()

      useAdmin.mockReturnValue({
        dashboard: null,
        overviewCards: null,
        realTimeMetrics: null,
        identityAnalytics: null,
        loading: false,
        fetchDashboard: mockFetchDashboard,
        fetchOverviewCards: mockFetchOverviewCards,
        fetchRealTimeMetrics: mockFetchRealTimeMetrics,
        fetchIdentityAnalytics: mockFetchIdentityAnalytics,
      })

      renderWithRouter(<AdminDashboard />)

      expect(mockFetchDashboard).toHaveBeenCalledWith(mockUser.email)
      expect(mockFetchOverviewCards).toHaveBeenCalled()
      expect(mockFetchRealTimeMetrics).toHaveBeenCalled()
      expect(mockFetchIdentityAnalytics).toHaveBeenCalled()
    })

    it('should show loading skeleton while loading', () => {
      useAdmin.mockReturnValue({
        dashboard: null,
        overviewCards: null,
        realTimeMetrics: null,
        identityAnalytics: null,
        loading: true,
        fetchDashboard: jest.fn(),
        fetchOverviewCards: jest.fn(),
        fetchRealTimeMetrics: jest.fn(),
        fetchIdentityAnalytics: jest.fn(),
      })

      renderWithRouter(<AdminDashboard />)

      expect(screen.getByText(/loading/i)).toBeInTheDocument()
    })
  })

  describe('Tab Navigation', () => {
    beforeEach(() => {
      useAdmin.mockReturnValue({
        dashboard: mockDashboard,
        overviewCards: mockOverviewCards,
        realTimeMetrics: mockRealTimeMetrics,
        identityAnalytics: mockIdentityAnalytics,
        loading: false,
        fetchDashboard: jest.fn(),
        fetchOverviewCards: jest.fn(),
        fetchRealTimeMetrics: jest.fn(),
        fetchIdentityAnalytics: jest.fn(),
      })
    })

    it('should show overview tab by default', () => {
      renderWithRouter(<AdminDashboard />)

      expect(screen.getByText('Overview')).toBeInTheDocument()
      expect(screen.getByText('System Metrics')).toBeInTheDocument()
    })

    it('should switch to System Metrics tab', async () => {
      renderWithRouter(<AdminDashboard />)

      const metricsTab = screen.getByText('System Metrics')
      fireEvent.click(metricsTab)

      await waitFor(() => {
        expect(screen.getByText('Active Users')).toBeInTheDocument()
        expect(screen.getByText('25')).toBeInTheDocument()
      })
    })

    it('should switch to Identity Analytics tab', async () => {
      renderWithRouter(<AdminDashboard />)

      const analyticsTab = screen.getByText('Identity Analytics')
      fireEvent.click(analyticsTab)

      await waitFor(() => {
        expect(screen.getByText('Total Sessions')).toBeInTheDocument()
        expect(screen.getByText('500')).toBeInTheDocument()
      })
    })

    it('should switch to Bias Alerts tab', async () => {
      renderWithRouter(<AdminDashboard />)

      const biasTab = screen.getByText('Bias Alerts')
      fireEvent.click(biasTab)

      await waitFor(() => {
        expect(screen.getByText('Bias Alerts Component')).toBeInTheDocument()
      })
    })

    it('should switch to Action Items tab', async () => {
      renderWithRouter(<AdminDashboard />)

      const actionTab = screen.getByText('Action Items')
      fireEvent.click(actionTab)

      await waitFor(() => {
        expect(screen.getByText('Pending Objection')).toBeInTheDocument()
        expect(screen.getByText('Unread Notification')).toBeInTheDocument()
      })
    })
  })

  describe('Overview Cards', () => {
    beforeEach(() => {
      useAdmin.mockReturnValue({
        dashboard: mockDashboard,
        overviewCards: mockOverviewCards,
        realTimeMetrics: null,
        identityAnalytics: null,
        loading: false,
        fetchDashboard: jest.fn(),
        fetchOverviewCards: jest.fn(),
        fetchRealTimeMetrics: jest.fn(),
        fetchIdentityAnalytics: jest.fn(),
      })
    })

    it('should display overview cards', () => {
      renderWithRouter(<AdminDashboard />)

      expect(screen.getByText('10')).toBeInTheDocument() // Surveys count
      expect(screen.getByText('100')).toBeInTheDocument() // Responses count
      expect(screen.getByText('50')).toBeInTheDocument() // Users count
    })

    it('should show trends for each card', () => {
      renderWithRouter(<AdminDashboard />)

      // Should show change text for cards with change data
      expect(screen.getByText('+2% from last period')).toBeInTheDocument()
      expect(screen.getByText('+15% from last period')).toBeInTheDocument()
    })
  })

  describe('Error Handling', () => {
    it('should handle fetch errors gracefully', () => {
      const mockFetchDashboard = jest.fn().mockRejectedValue(new Error('Failed'))
      const mockFetchOverviewCards = jest.fn()
      const mockFetchRealTimeMetrics = jest.fn()
      const mockFetchIdentityAnalytics = jest.fn()

      useAdmin.mockReturnValue({
        dashboard: null,
        overviewCards: null,
        realTimeMetrics: null,
        identityAnalytics: null,
        loading: false,
        fetchDashboard: mockFetchDashboard,
        fetchOverviewCards: mockFetchOverviewCards,
        fetchRealTimeMetrics: mockFetchRealTimeMetrics,
        fetchIdentityAnalytics: mockFetchIdentityAnalytics,
      })

      renderWithRouter(<AdminDashboard />)

      // Should not crash, just log error
      expect(mockFetchDashboard).toHaveBeenCalled()
    })
  })

  describe('Component Integration', () => {
    beforeEach(() => {
      useAdmin.mockReturnValue({
        dashboard: mockDashboard,
        overviewCards: mockOverviewCards,
        realTimeMetrics: mockRealTimeMetrics,
        identityAnalytics: mockIdentityAnalytics,
        loading: false,
        fetchDashboard: jest.fn(),
        fetchOverviewCards: jest.fn(),
        fetchRealTimeMetrics: jest.fn(),
        fetchIdentityAnalytics: jest.fn(),
      })
    })

    it('should render SystemMetrics component with correct props', async () => {
      renderWithRouter(<AdminDashboard />)

      const metricsTab = screen.getByText('System Metrics')
      fireEvent.click(metricsTab)

      await waitFor(() => {
        expect(screen.getByText('Active Users')).toBeInTheDocument()
        expect(screen.getByText('API Requests')).toBeInTheDocument()
      })
    })

    it('should render IdentityAnalytics component with correct props', async () => {
      renderWithRouter(<AdminDashboard />)

      const analyticsTab = screen.getByText('Identity Analytics')
      fireEvent.click(analyticsTab)

      await waitFor(() => {
        expect(screen.getByText('Total Sessions')).toBeInTheDocument()
        expect(screen.getByText('Mode Distribution')).toBeInTheDocument()
      })
    })

    it('should render BiasAlerts component', async () => {
      renderWithRouter(<AdminDashboard />)

      const biasTab = screen.getByText('Bias Alerts')
      fireEvent.click(biasTab)

      await waitFor(() => {
        expect(screen.getByText('Bias Alerts Component')).toBeInTheDocument()
      })
    })

    it('should render ActionItems component with dashboard data', async () => {
      renderWithRouter(<AdminDashboard />)

      const actionTab = screen.getByText('Action Items')
      fireEvent.click(actionTab)

      await waitFor(() => {
        expect(screen.getByText('Pending Objection')).toBeInTheDocument()
      })
    })
  })
})
