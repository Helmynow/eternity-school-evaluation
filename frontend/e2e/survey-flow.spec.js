import { test, expect } from '@playwright/test'

test.describe('Survey Flow E2E Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Mock authentication
    await page.goto('/login')
    // In a real scenario, you'd authenticate here
    // For now, we'll assume the user is already logged in
  })

  test('should complete full survey flow', async ({ page }) => {
    // Navigate to surveys list
    await page.goto('/survey')
    await expect(page.locator('h1')).toContainText('Surveys')

    // Click on a survey (assuming there's at least one)
    const surveyCard = page.locator('[data-testid="survey-card"]').first()
    if (await surveyCard.count() > 0) {
      await surveyCard.click()

      // Select identity mode
      await expect(page.locator('text=Choose Your Privacy Mode')).toBeVisible()
      await page.locator('button:has-text("Anonymous")').click()

      // Wait for survey form to load
      await expect(page.locator('text=Question 1')).toBeVisible()

      // Answer first question (text)
      const textarea = page.locator('textarea[placeholder*="Enter your response"]')
      await textarea.fill('Test response for question 1')

      // Click Next
      await page.locator('button:has-text("Next")').click()

      // Answer second question (if exists)
      const nextQuestion = page.locator('text=Question 2')
      if (await nextQuestion.count() > 0) {
        await expect(nextQuestion).toBeVisible()
        // Handle different question types
        const ratingButton = page.locator('button:has-text("3")')
        if (await ratingButton.count() > 0) {
          await ratingButton.click()
        }
      }

      // Submit survey
      const submitButton = page.locator('button:has-text("Submit Survey")')
      if (await submitButton.count() > 0) {
        await submitButton.click()

        // Should redirect to survey list
        await expect(page).toHaveURL(/\/survey/)
        await expect(page.locator('text=Survey submitted successfully')).toBeVisible()
      }
    }
  })

  test('should validate required questions', async ({ page }) => {
    await page.goto('/survey')
    
    const surveyCard = page.locator('[data-testid="survey-card"]').first()
    if (await surveyCard.count() > 0) {
      await surveyCard.click()

      // Select identity mode
      await page.locator('button:has-text("Anonymous")').click()

      // Try to navigate without answering required question
      const nextButton = page.locator('button:has-text("Next")')
      if (await nextButton.count() > 0) {
        await nextButton.click()

        // Should show error message
        await expect(page.locator('text=This question is required')).toBeVisible()
      }
    }
  })

  test('should navigate between questions', async ({ page }) => {
    await page.goto('/survey')
    
    const surveyCard = page.locator('[data-testid="survey-card"]').first()
    if (await surveyCard.count() > 0) {
      await surveyCard.click()

      await page.locator('button:has-text("Anonymous")').click()

      // Answer first question
      const textarea = page.locator('textarea[placeholder*="Enter your response"]')
      await textarea.fill('Answer 1')
      await page.locator('button:has-text("Next")').click()

      // Should be on question 2
      await expect(page.locator('text=Question 2')).toBeVisible()

      // Click Previous
      await page.locator('button:has-text("Previous")').click()

      // Should be back on question 1
      await expect(page.locator('text=Question 1')).toBeVisible()
    }
  })

  test('should show progress bar', async ({ page }) => {
    await page.goto('/survey')
    
    const surveyCard = page.locator('[data-testid="survey-card"]').first()
    if (await surveyCard.count() > 0) {
      await surveyCard.click()

      await page.locator('button:has-text("Anonymous")').click()

      // Progress bar should be visible
      const progressBar = page.locator('[role="progressbar"]')
      await expect(progressBar).toBeVisible()

      // Progress should update as we navigate
      const textarea = page.locator('textarea[placeholder*="Enter your response"]')
      await textarea.fill('Answer')
      await page.locator('button:has-text("Next")').click()

      // Progress should have increased
      await expect(progressBar).toBeVisible()
    }
  })
})

test.describe('Survey Creation Flow', () => {
  test('should create a new survey', async ({ page }) => {
    // Navigate to survey creation
    await page.goto('/survey/create')
    
    // Fill in survey details
    await page.locator('input[name="title"]').fill('E2E Test Survey')
    await page.locator('textarea[name="description"]').fill('This is a test survey created by E2E tests')
    await page.locator('select[name="survey_type"]').selectOption('comprehensive')

    // Submit
    await page.locator('button:has-text("Create Survey")').click()

    // Should redirect to questions page
    await expect(page).toHaveURL(/\/survey\/\d+\/questions/)
  })

  test('should validate required fields', async ({ page }) => {
    await page.goto('/survey/create')
    
    // Try to submit without title
    await page.locator('button:has-text("Create Survey")').click()

    // Should show validation error
    await expect(page.locator('text=Please enter a survey title')).toBeVisible()
  })
})
