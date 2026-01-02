# Performance and Monitoring Guide

This guide covers the performance optimizations, error tracking, and monitoring setup for the Eternity School Evaluation System.

## 🚀 Performance Optimizations

### Code Splitting

All route components are lazy-loaded using React's `lazy()` and `Suspense`:

```jsx
const Dashboard = lazy(() => import('./components/dashboard/Dashboard'))
```

**Benefits:**
- Smaller initial bundle size
- Faster initial page load
- Better caching (chunks update independently)

### Bundle Optimization

**Vite Configuration:**
- Manual chunk splitting for vendor libraries
- Terser minification with console removal in production
- Source maps in development only

**Chunk Strategy:**
- `react-vendor`: React, React DOM, React Router
- `chart-vendor`: Recharts
- `ui-vendor`: Toast notifications, Icons

### Build Analysis

Analyze your bundle size:

```bash
ANALYZE=true npm run build
```

This generates `dist/stats.html` showing:
- Bundle sizes
- Gzip sizes
- Brotli sizes
- Dependency tree

## 📊 Performance Monitoring

### Web Vitals

The app automatically tracks Core Web Vitals:

- **CLS** (Cumulative Layout Shift) - Visual stability
- **FID** (First Input Delay) - Interactivity
- **FCP** (First Contentful Paint) - Initial render
- **LCP** (Largest Contentful Paint) - Loading performance
- **TTFB** (Time to First Byte) - Server response
- **INP** (Interaction to Next Paint) - Responsiveness

### Custom Metrics

Track custom performance metrics:

```javascript
import { measurePerformance } from './lib/performance'

// Measure async operation
const result = await measurePerformance('data-fetch', async () => {
  return await fetchData()
})

// Measure sync operation
const result = measurePerformance('calculation', () => {
  return heavyCalculation()
})
```

### API Request Tracking

API requests are automatically tracked for:
- Request duration
- Response status
- Slow requests (>500ms logged as warnings)

## 🐛 Error Tracking (Sentry)

### Setup

1. Create a Sentry account at https://sentry.io
2. Create a new project (React)
3. Copy your DSN
4. Add to `.env`:

```env
VITE_SENTRY_DSN=[YOUR-VITE_SENTRY_DSN]
```

### Features

- **Automatic Error Capture**: All unhandled errors
- **Performance Monitoring**: Transaction tracing
- **Session Replay**: 10% of sessions, 100% of errors
- **Release Tracking**: Track errors by app version
- **Error Filtering**: Ignores expected errors (404s, network errors)

### Manual Error Reporting

```javascript
import * as Sentry from '@sentry/react'

// Capture exception
Sentry.captureException(new Error('Something went wrong'))

// Capture message
Sentry.captureMessage('User action completed', 'info')

// Add context
Sentry.setUser({ email: 'user@example.com' })
Sentry.setContext('survey', { surveyId: 123 })
```

## 📈 Monitoring Dashboard

### Performance Metrics

Access performance summary:

```javascript
import { getPerformanceSummary } from './lib/performance'

const summary = getPerformanceSummary()
// Returns: { dns, tcp, request, response, dom, load, fcp }
```

### Backend Integration

Performance metrics are sent to:

```
POST /api/v2/analytics/performance
```

**Payload:**
```json
{
  "name": "LCP",
  "value": 1200,
  "rating": "good",
  "url": "/survey/123",
  "timestamp": 1234567890
}
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `VITE_SENTRY_DSN` | Sentry DSN for error tracking | No |
| `VITE_APP_VERSION` | App version for release tracking | No |
| `VITE_API_URL` | Backend API URL | Yes |

### Production Settings

**Sentry:**
- Traces sample rate: 10% (reduces overhead)
- Session replay: 10% of sessions
- Error replay: 100% of errors

**Performance:**
- Console logs removed in production
- Source maps disabled in production
- Aggressive minification enabled

## 📊 Performance Targets

### Web Vitals Targets

| Metric | Good | Needs Improvement | Poor |
|--------|------|-------------------|------|
| LCP | < 2.5s | 2.5s - 4s | > 4s |
| FID | < 100ms | 100ms - 300ms | > 300ms |
| CLS | < 0.1 | 0.1 - 0.25 | > 0.25 |
| FCP | < 1.8s | 1.8s - 3s | > 3s |
| TTFB | < 800ms | 800ms - 1.8s | > 1.8s |

### API Performance Targets

| Duration | Rating |
|----------|--------|
| < 200ms | Good |
| 200ms - 500ms | Needs Improvement |
| > 500ms | Poor |

## 🛠️ Troubleshooting

### High Bundle Size

1. Run bundle analyzer: `ANALYZE=true npm run build`
2. Check for large dependencies
3. Consider code splitting for large components
4. Use dynamic imports for heavy libraries

### Slow API Requests

1. Check network tab in DevTools
2. Review API endpoint performance
3. Consider request caching
4. Implement request debouncing

### Sentry Not Working

1. Verify `VITE_SENTRY_DSN` is set
2. Check browser console for Sentry errors
3. Verify network requests to Sentry
4. Check Sentry project settings

## 📚 Resources

- [Web Vitals](https://web.dev/vitals/)
- [Sentry React Docs](https://docs.sentry.io/platforms/javascript/guides/react/)
- [Vite Performance](https://vitejs.dev/guide/performance.html)
- [React Code Splitting](https://react.dev/reference/react/lazy)
