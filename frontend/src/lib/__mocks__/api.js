// Mock API client for testing
export const apiClient = {
  survey: {
    getAll: jest.fn(),
    getById: jest.fn(),
    create: jest.fn(),
    update: jest.fn(),
    getQuestions: jest.fn(),
    getResponses: jest.fn(),
    submitResponse: jest.fn(),
    getAnalytics: jest.fn(),
  },
  admin: {
    getDashboard: jest.fn(),
    getOverviewCards: jest.fn(),
    getRealTimeMetrics: jest.fn(),
    getIdentityAnalytics: jest.fn(),
  },
  integration: {
    setupHR: jest.fn(),
    getEvaluationBridge: jest.fn(),
    syncStaff: jest.fn(),
    syncEvaluation: jest.fn(),
  },
  hybridIdentity: {
    initializeSession: jest.fn(),
    createSurveySession: jest.fn(),
    submitResponse: jest.fn(),
    switchMode: jest.fn(),
    processReveal: jest.fn(),
    analyzeData: jest.fn(),
  },
}
