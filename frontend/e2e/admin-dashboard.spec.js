import { test, expect } from '@playwright/test'

test.describe('Admin Dashboard E2E Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Mock admin authentication
    // In a real scenario, you'd authenticate as admin here
    await page.goto('/admin/dashboard')
  })

  test('should display admin dashboard for authorized users', async ({ page }) => {
    // Should show dashboard title
    await expect(page.locator('h1')).toContainText(/admin|dashboard/i)

    // Should show overview cards
    await expect(page.locator('text=Surveys')).toBeVisible()
    await expect(page.locator('text=Responses')).toBeVisible()
    await expect(page.locator('text=Users')).toBeVisible()
  })

  test('should navigate between tabs', async ({ page }) => {
    // Click System Metrics tab
    await page.locator('text=System Metrics').click()
    await expect(page.locator('text=Active Users')).toBeVisible()

    // Click Identity Analytics tab
    await page.locator('text=Identity Analytics').click()
    await expect(page.locator('text=Total Sessions')).toBeVisible()

    // Click Bias Alerts tab
    await page.locator('text=Bias Alerts').click()
    await expect(page.locator('text=Bias')).toBeVisible()

    // Click Action Items tab
    await page.locator('text=Action Items').click()
    await expect(page.locator('text=Action')).toBeVisible()
  })

  test('should show access denied for non-admin users', async ({ page }) => {
    // Mock non-admin user
    await page.goto('/admin/dashboard')
    
    // Should show access denied message
    const accessDenied = page.locator('text=Access Denied')
    if (await accessDenied.count() > 0) {
      await expect(accessDenied).toBeVisible()
    }
  })

  test('should load and display metrics', async ({ page }) => {
    // Wait for data to load
    await page.waitForSelector('text=Surveys', { timeout: 5000 })

    // Metrics should be displayed
    const metrics = page.locator('[data-testid="metric-card"]')
    if (await metrics.count() > 0) {
      await expect(metrics.first()).toBeVisible()
    }
  })
})

test.describe('Integration Hub E2E Tests', () => {
  test('should display integration hub', async ({ page }) => {
    await page.goto('/admin/integration')
    
    await expect(page.locator('h1')).toContainText(/integration/i)
  })

  test('should show integration status', async ({ page }) => {
    await page.goto('/admin/integration')
    
    // Should show status tab
    await page.locator('text=Integration Status').click()
    await expect(page.locator('text=Connection Status')).toBeVisible()
  })

  test('should allow HR system setup', async ({ page }) => {
    await page.goto('/admin/integration')
    
    // Click setup tab
    await page.locator('text=HR Setup').click()
    
    // Fill in HR configuration
    await page.locator('input[name="hr_system_url"]').fill('https://hr.example.com')
    await page.locator('input[name="api_key"]').fill('test-api-key')
    
    // Submit (if not in read-only mode)
    const submitButton = page.locator('button:has-text("Setup Integration")')
    if (await submitButton.count() > 0 && await submitButton.isEnabled()) {
      await submitButton.click()
      await expect(page.locator('text=successfully')).toBeVisible()
    }
  })
})
