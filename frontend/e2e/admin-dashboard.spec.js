import { test, expect } from '@playwright/test'
import { seedSupabaseSession } from './utils/auth'
import { mockAdminApi, mockIntegrationApi } from './utils/mockApi'

test.describe('Admin Dashboard E2E Tests (authorized)', () => {
  test.beforeEach(async ({ page }) => {
    await seedSupabaseSession(page, { email: 'pnc@eternity.edu', role: 'pnc' })
    await mockAdminApi(page)
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
    await page.getByRole('button', { name: /System Metrics/i }).click()
    await expect(page.getByRole('heading', { name: 'Active Users' })).toBeVisible()

    // Click Identity Analytics tab
    await page.getByRole('button', { name: /Identity Analytics/i }).click()
    await expect(page.getByRole('heading', { name: 'Total Sessions' })).toBeVisible()

    // Click Bias Alerts tab
    await page.getByRole('button', { name: /Bias Alerts/i }).click()
    await expect(page.locator('text=Bias').first()).toBeVisible()

    // Click Action Items tab
    await page.getByRole('button', { name: /Action Items/i }).click()
    await expect(page.locator('text=Action').first()).toBeVisible()
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

test.describe('Admin Dashboard E2E Tests (unauthorized)', () => {
  test('should show access denied for non-admin users', async ({ page }) => {
    await seedSupabaseSession(page, { email: 'staff@eternity.edu', role: 'staff' })
    await page.goto('/admin/dashboard')

    // Should show access denied message
    await expect(page.locator('text=Access Denied')).toBeVisible()
  })
})

test.describe('Integration Hub E2E Tests (CEO)', () => {
  test.beforeEach(async ({ page }) => {
    await seedSupabaseSession(page, { email: 'ceo@eternity.edu', role: 'ceo' })
    await mockIntegrationApi(page)
  })

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
    await page.getByRole('button', { name: /HR Setup/i }).click()
    await expect(page.getByText('HR System Setup')).toBeVisible()
    
    // Fill in HR configuration
    await page.locator('input[type="url"]').first().fill('https://hr.example.com')
    await page.locator('input[type="password"]').first().fill('test-api-key')
    
    // Submit (if not in read-only mode)
    const submitButton = page.locator('button:has-text("Setup Integration")')
    if (await submitButton.count() > 0 && await submitButton.isEnabled()) {
      await submitButton.click()
      await expect(page.getByText(/HR integration .* successfully/i).first()).toBeVisible()
    }
  })
})
