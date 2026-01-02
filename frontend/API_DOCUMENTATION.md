# Frontend API Client Documentation

This document describes all available API client methods in the frontend application.

## Base Configuration

The API client is configured in `src/lib/api.js` and uses Axios with:
- Base URL: `VITE_API_URL` or `http://localhost:8000`
- Automatic authentication token injection
- Error handling with toast notifications
- Request/response interceptors

## API Client Methods

### Survey Endpoints

```javascript
apiClient.survey.getAll(params)
// GET /api/v2/surveys
// Returns: List of surveys
// Params: { status?: string, survey_type?: string }

apiClient.survey.getById(id)
// GET /api/v2/surveys/{id}
// Returns: Survey object

apiClient.survey.create(data)
// POST /api/v2/surveys
// Body: { title, description, survey_type, start_date?, end_date? }
// Returns: Created survey

apiClient.survey.update(id, data)
// PUT /api/v2/surveys/{id}
// Body: { title?, description?, status?, start_date?, end_date? }
// Returns: Updated survey

apiClient.survey.getQuestions(surveyId)
// GET /api/v2/surveys/{surveyId}/questions
// Returns: List of survey questions

apiClient.survey.getResponses(surveyId, params)
// GET /api/v2/surveys/{surveyId}/responses
// Returns: List of survey responses
// Params: { identity_mode?, respondent_email? }

apiClient.survey.submitResponse(data)
// POST /api/v2/surveys/responses
// Body: { survey_id, question_id, respondent_email?, anonymous_id?, session_id?, identity_mode?, response_text?, response_value? }
// Returns: Response confirmation

apiClient.survey.getAnalytics(surveyId)
// GET /api/v2/surveys/{surveyId}/analytics
// Returns: Survey analytics data
```

### Survey Templates

```javascript
apiClient.surveyTemplates.getComprehensive()
// GET /api/v2/survey-templates/comprehensive
// Returns: Comprehensive survey template

apiClient.surveyTemplates.getSection(category)
// GET /api/v2/survey-templates/section/{category}
// Returns: Section template for category
```

### Identity Preferences

```javascript
apiClient.identityPreferences.setPreference(data)
// POST /api/v2/survey/identity/preference
// Body: { user_email, survey_id?, identity_mode, privacy_level?, retention_days? }
// Returns: Saved preference

apiClient.identityPreferences.getPreference(userEmail, surveyId)
// GET /api/v2/survey/identity/status/{userEmail}
// Params: { survey_id?: number }
// Returns: User's identity preference/status
```

### Hybrid Identity

```javascript
apiClient.hybridIdentity.initializeSession(data)
// POST /api/v2/hybrid-identity/initialize-session
// Body: { user_email, identity_mode, survey_id? }
// Returns: { session_token, ... }

apiClient.hybridIdentity.createSurveySession(params)
// POST /api/v2/hybrid-identity/create-survey-session
// Params: { user_email, survey_type, session_token? }
// Returns: Survey session data

apiClient.hybridIdentity.submitResponse(data)
// POST /api/v2/hybrid-identity/submit-response
// Body: { session_token, survey_id, responses }
// Returns: Submission confirmation

apiClient.hybridIdentity.switchMode(data)
// POST /api/v2/hybrid-identity/switch-mode
// Body: { session_token, new_mode }
// Returns: Updated session

apiClient.hybridIdentity.processReveal(userEmail, revealType, conditions)
// POST /api/v2/hybrid-identity/process-reveal-request
// Params: { user_email, reveal_type, conditions? }
// Returns: Reveal result

apiClient.hybridIdentity.analyzeData(params)
// GET /api/v2/hybrid-identity/analyze-survey-data
// Params: { survey_id? }
// Returns: Analysis results
```

### Admin Dashboard

```javascript
apiClient.admin.getDashboard(adminId)
// GET /api/v2/admin/dashboard
// Params: { admin_id }
// Returns: Dashboard data

apiClient.admin.getOverviewCards()
// GET /api/v2/admin/dashboard/overview-cards
// Returns: Overview card data

apiClient.admin.getRealTimeMetrics()
// GET /api/v2/admin/dashboard/real-time-metrics
// Returns: Real-time system metrics

apiClient.admin.getIdentityAnalytics()
// GET /api/v2/admin/dashboard/identity-analytics
// Returns: Identity analytics data
```

### Integration Hub

```javascript
apiClient.integration.setupHR(config)
// POST /api/v2/integration/hr/setup
// Body: { hr_system_url, api_key?, real_time_sync?, webhook_url?, ip_whitelist? }
// Returns: Setup confirmation

apiClient.integration.getEvaluationBridge()
// GET /api/v2/integration/evaluation-bridge
// Returns: Bridge configuration and status

apiClient.integration.syncStaff()
// POST /api/v2/integration/sync/staff
// Returns: Sync result

apiClient.integration.syncEvaluation()
// POST /api/v2/integration/sync/evaluation
// Returns: Sync result
```

### EOM (Employee of the Month)

```javascript
apiClient.eom.submitNomination(data)
apiClient.eom.validateNomination(data)
apiClient.eom.getNominations(cycleId)
apiClient.eom.submitVote(data)
apiClient.eom.getWinners(cycleId)
apiClient.eom.getEligibleNominees(cycleId)
apiClient.eom.getRotationAnalytics(cycleId)
apiClient.eom.suggestCategory(achievementText, nomineeRole)
apiClient.eom.getHallOfFame(params)
apiClient.eom.getDiversityTracking(params)
apiClient.eom.submitFeedback(data)
apiClient.eom.getWindowStatus(cycleId)
```

### MRE (Multi-Rater Evaluation)

```javascript
apiClient.mre.getAssignments(cycleId)
apiClient.mre.submitEvaluation(data)
apiClient.mre.getWeightedScores(cycleId)
apiClient.mre.getDomains(targetGroup)
```

### Notifications

```javascript
apiClient.notifications.getAll(params)
apiClient.notifications.markRead(id, params)
apiClient.notifications.markAllRead(params)
apiClient.notifications.markMultipleRead(ids, params)
apiClient.notifications.getUnreadCount(params)
```

### Objections

```javascript
apiClient.objections.getAll(params)
apiClient.objections.getById(id)
apiClient.objections.submit(data)
apiClient.objections.resolve(id, data)
```

### Reports

```javascript
apiClient.reports.getCEO(cycleId)
apiClient.reports.exportCEO(cycleId, format)
apiClient.reports.getBias(cycleId)
apiClient.reports.getParticipation(cycleId)
```

### Analytics

```javascript
apiClient.analytics.getParticipation(cycleId)
apiClient.analytics.getBias(cycleId)
apiClient.analytics.getEOM(cycleId)
apiClient.analytics.getMRE(cycleId)
```

## Error Handling

All API calls automatically handle errors through interceptors:
- 401: Redirects to login
- 403: Shows permission error
- 404: Silently handled (expected for some endpoints)
- 422: Shows validation error
- 500: Shows server error
- Network errors: Logged but not shown as toast (to prevent spam)

## Usage Examples

```javascript
import { apiClient } from '../lib/api'

// Fetch surveys
const surveys = await apiClient.survey.getAll({ status: 'active' })

// Create survey
const newSurvey = await apiClient.survey.create({
  title: 'Employee Satisfaction Survey',
  survey_type: 'comprehensive',
})

// Submit survey response
await apiClient.survey.submitResponse({
  survey_id: 1,
  question_id: 5,
  response_text: 'Great experience',
  identity_mode: 'anonymous',
})
```

## Custom Hooks

For easier data management, use the custom hooks:

```javascript
import { useSurvey } from '../hooks/useSurvey'
import { useAdmin } from '../hooks/useAdmin'
import { useSurveyTemplates } from '../hooks/useSurveyTemplates'
import { useIdentityPreferences } from '../hooks/useIdentityPreferences'

// In component
const { surveys, loading, fetchSurveys } = useSurvey()
const { preference, setPreference } = useIdentityPreferences(surveyId)
```
