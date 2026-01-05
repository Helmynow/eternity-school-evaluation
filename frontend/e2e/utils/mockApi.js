const jsonResponse = (data, status = 200) => ({
  status,
  contentType: 'application/json',
  body: JSON.stringify(data),
})

export const mockAdminApi = async (page) => {
  await page.route('**/api/v2/admin/dashboard', async (route) => {
    await route.fulfill(
      jsonResponse({
        system_status: 'Operational',
        last_updated: new Date().toISOString(),
        action_items: [{ id: 1, title: 'Review survey anomalies' }],
      })
    )
  })

  await page.route('**/api/v2/admin/dashboard/overview-cards', async (route) => {
    await route.fulfill(
      jsonResponse([
        { title: 'Surveys', value: 12, change: 5 },
        { title: 'Responses', value: 348, change: 3 },
        { title: 'Users', value: 128, change: 1 },
        { title: 'Cycles', value: 4, change: 0 },
      ])
    )
  })

  await page.route('**/api/v2/admin/dashboard/real-time-metrics', async (route) => {
    await route.fulfill(
      jsonResponse({
        active_users: 42,
        api_requests: 1337,
        avg_response_time: 120,
        usage_trends: [
          { date: '2026-01-01', users: 10, requests: 100 },
          { date: '2026-01-02', users: 20, requests: 200 },
        ],
        feature_usage: [
          { feature: 'Surveys', count: 50 },
          { feature: 'EOM', count: 25 },
        ],
      })
    )
  })

  await page.route('**/api/v2/admin/dashboard/identity-analytics', async (route) => {
    await route.fulfill(
      jsonResponse({
        total_sessions: 120,
        mode_count: 3,
        reveals_processed: 7,
        mode_distribution: [
          { name: 'Anonymous', value: 60 },
          { name: 'Identified', value: 40 },
        ],
        reveal_methods: [
          { method: 'Auto', count: 4 },
          { method: 'Manual', count: 3 },
        ],
      })
    )
  })
}

export const mockIntegrationApi = async (page) => {
  await page.route('**/api/v2/integration/evaluation-bridge', async (route) => {
    await route.fulfill(
      jsonResponse({
        status: 'connected',
        last_sync: new Date().toISOString(),
      })
    )
  })

  await page.route('**/api/v2/integration/hr/setup', async (route) => {
    await route.fulfill(jsonResponse({ status: 'ok' }))
  })
}

export const mockSurveyApi = async (page) => {
  await page.route('**/api/v2/survey-templates/standardized**', async (route) => {
    await route.fulfill(jsonResponse({ surveys: [] }))
  })

  await page.route('**/api/v2/surveys**', async (route) => {
    if (route.request().method().toUpperCase() === 'POST') {
      await route.fulfill(jsonResponse({ id: 123 }))
      return
    }
    await route.fulfill(jsonResponse([]))
  })
}
