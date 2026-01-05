import { test } from '@playwright/test'
import { seedSupabaseSession } from './utils/auth'

test('eom headings dump', async ({ page }) => {
  await seedSupabaseSession(page, { email: 'head@eternity.edu', role: 'department_head' })
  await page.goto('/eom/nominate')
  await page.waitForTimeout(1000)
  const headings = await page.$$eval('h1, h2, h3', els => els.map(e => e.textContent?.trim()).filter(Boolean))
  const title = await page.title()
  console.log(JSON.stringify({ title, headings }))
})
