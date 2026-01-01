import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'

// Initialize error tracking (Sentry) - wrapped in try/catch
try {
  import('./lib/sentry').then(({ initSentry }) => initSentry()).catch(err => console.log('Sentry init skipped'))
} catch (e) {
  console.log('Sentry not available')
}

// Initialize performance monitoring - wrapped in try/catch
try {
  import('./lib/performance').then(({ initWebVitals }) => initWebVitals()).catch(err => console.log('WebVitals skipped'))
} catch (e) {
  console.log('Performance monitoring not available')
}

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)

