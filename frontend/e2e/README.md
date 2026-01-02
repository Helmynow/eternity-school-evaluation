# E2E Testing Guide

This directory contains end-to-end tests using Playwright.

## Setup

1. Install dependencies:
```bash
npm install
```

2. Install Playwright browsers:
```bash
npx playwright install
```

## Running Tests

### Run all E2E tests:
```bash
npm run test:e2e
```

### Run tests in UI mode:
```bash
npm run test:e2e:ui
```

### Run tests in debug mode:
```bash
npm run test:e2e:debug
```

### Run specific test file:
```bash
npx playwright test survey-flow.spec.js
```

## Test Structure

- `survey-flow.spec.js` - Tests for survey creation, submission, and navigation
- `admin-dashboard.spec.js` - Tests for admin dashboard and integration hub

## Writing Tests

Tests use Playwright's page object model. Example:

```javascript
import { test, expect } from '@playwright/test'

test('should do something', async ({ page }) => {
  await page.goto('/path')
  await expect(page.locator('h1')).toContainText('Expected Text')
})
```

## CI/CD

Tests run automatically in CI/CD pipelines. Make sure to set up environment variables:
- `CI=true` - Enables CI mode (retries, single worker)
- `BASE_URL` - Override base URL if needed
