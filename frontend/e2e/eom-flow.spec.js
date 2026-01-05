import { test, expect } from '@playwright/test'
import { seedSupabaseSession } from './utils/auth'

const getCredentials = () => ({
  email: process.env.E2E_TEST_EMAIL || '',
  password: process.env.E2E_TEST_PASSWORD || '',
})

const loginIfNeeded = async (page) => {
  const { email, password } = getCredentials()
  if (!email || !password) {
    await seedSupabaseSession(page, { email: 'head@eternity.edu', role: 'department_head' })
    return { loggedIn: true, reason: 'Using mocked session (no E2E_TEST_EMAIL/PASSWORD set)' }
  }

  await page.goto('/login')

  const signInHeading = page.getByRole('heading', { name: /sign in/i })
  if (!(await signInHeading.count())) {
    // Some builds render login at root
    await page.goto('/')
  }

  const signInStillVisible = (await signInHeading.count()) > 0
  if (!signInStillVisible) {
    return { loggedIn: true }
  }

  await page.getByLabel('Email Address').fill(email)
  await page.getByLabel('Password').fill(password)
  await page.getByRole('button', { name: /sign in/i }).click()

  // Give auth redirect a moment
  await page.waitForTimeout(1500)

  // Wait for auth token to land in storage (supabase session)
  const hasToken = await page
    .waitForFunction(
      () => Object.keys(localStorage).some((k) => k.includes('auth-token')),
      null,
      { timeout: 5000 }
    )
    .then(() => true)
    .catch(() => false)

  if (await page.getByRole('heading', { name: /sign in/i }).count()) {
    if (!hasToken) {
      return { loggedIn: false, reason: 'Login failed or requires different credentials' }
    }
    return { loggedIn: false, reason: 'Login failed or requires different credentials' }
  }

  return { loggedIn: true }
}

test.describe('EOM Nomination/Vote Flow (conditional)', () => {
  test('should exercise nomination, validation errors, voting, and load more if data is available', async ({ page }) => {
    const auth = await loginIfNeeded(page)
    if (!auth.loggedIn) {
      test.skip(true, auth.reason || 'Authentication required for EOM flows')
    }

    // Nomination flow
    await page.goto('/eom/nominate')
    const loginGate = await page.getByRole('heading', { name: /sign in/i }).count()
    const accessDenied = await page.locator('text=You do not have permission').count()
    if (loginGate || accessDenied) {
      test.skip(true, 'EOM nomination page requires authenticated leadership access')
    }

    await expect(page.locator('text=EOM Nomination')).toBeVisible()

    const categoryButton = page.locator('text=Select Category').locator('..').locator('button').first()
    if (await categoryButton.count()) {
      await categoryButton.click()
    }

    const nomineeInput = page.locator('input[placeholder*="Search by name"]')
    if (await nomineeInput.count()) {
      await nomineeInput.click()
    }

    const validateButton = page.getByRole('button', { name: /validate nomination/i })
    if (await validateButton.count()) {
      if (await validateButton.isEnabled()) {
        await validateButton.click()
        const validationResult = page.locator('text=Invalid').first()
        if (await validationResult.count()) {
          await expect(validationResult).toBeVisible()
        }
      }
    }

    // Voting flow
    await page.goto('/eom/vote')
    await expect(page.locator('text=EOM Voting')).toBeVisible()

    const voteButton = page.getByRole('button', { name: /^vote$/i }).first()
    if (await voteButton.count()) {
      await voteButton.click()
    }

    const loadMoreButton = page.getByRole('button', { name: /load more nominations/i })
    if (await loadMoreButton.count()) {
      await loadMoreButton.click()
    }
  })
})
