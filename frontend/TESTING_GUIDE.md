# Component Testing Guide

This guide covers testing the new components with the backend API, error handling, and identity mode functionality.

## Error Boundaries

All major components are now wrapped with `ErrorBoundary` components that:
- Catch React errors during rendering
- Display user-friendly error messages
- Provide options to retry or refresh
- Log errors to console for debugging

### Components with Error Boundaries:
- `App.jsx` - Global error boundary
- `SurveyList.jsx`
- `SurveySession.jsx`
- `AdminDashboard.jsx`
- `ActionItems.jsx`

## Loading Skeletons

Loading states have been improved with skeleton components that provide better UX:

### Available Skeleton Types:
- `card` - For card-based layouts
- `list` - For list items
- `table` - For table layouts
- `dashboard` - For dashboard views
- `form` - For form inputs

### Components with Loading Skeletons:
- `SurveyList.jsx` - Uses `card` skeleton
- `SurveySession.jsx` - Uses `form` skeleton
- `AdminDashboard.jsx` - Uses `dashboard` skeleton
- `ActionItems.jsx` - Uses `list` skeleton

## API Integration Testing

### Survey Components

1. **SurveyList** (`/survey`)
   - Tests: `GET /api/v2/surveys`
   - Filters: status (all, active, draft, closed)
   - Expected: List of surveys with status badges

2. **SurveySession** (`/survey/:surveyId`)
   - Tests:
     - `GET /api/v2/surveys/{surveyId}` - Load survey
     - `GET /api/v2/surveys/{surveyId}/questions` - Load questions
     - `POST /api/v2/hybrid-identity/initialize-session` - Initialize session
     - `POST /api/v2/hybrid-identity/create-survey-session` - Create session
     - `POST /api/v2/hybrid-identity/submit-response` - Submit response

3. **SurveyAnalytics** (`/survey/:surveyId/analytics`)
   - Tests: `GET /api/v2/surveys/{surveyId}/analytics`
   - Requires: CEO or PNC role
   - Expected: Analytics data with charts

### Admin Components

1. **AdminDashboard** (`/admin/dashboard`)
   - Tests:
     - `GET /api/v2/admin/dashboard` - Dashboard data
     - `GET /api/v2/admin/dashboard/overview-cards` - Overview cards
     - `GET /api/v2/admin/dashboard/real-time-metrics` - Real-time metrics
     - `GET /api/v2/admin/dashboard/identity-analytics` - Identity analytics

2. **IntegrationHub** (`/admin/integration`)
   - Tests:
     - `GET /api/v2/integration/evaluation-bridge` - Bridge status
     - `POST /api/v2/integration/hr/setup` - Setup HR integration
     - `POST /api/v2/integration/sync/staff` - Sync staff
     - `POST /api/v2/integration/sync/evaluation` - Sync evaluation

## Identity Mode Testing

### Test Component

Use the `IdentityModeTest` component at `/survey/test/:surveyId?` to test:

1. **Mode Selection**
   - Anonymous mode
   - Conditional mode
   - Identified mode

2. **Mode Switching**
   - Switch between modes during active session
   - Verify session token persistence

3. **Identity Reveal**
   - Full reveal
   - Partial reveal (role, department)
   - Gradual reveal
   - Consent-based reveal

### Testing Steps

1. Navigate to `/survey/test` or `/survey/test/{surveyId}`
2. Select an identity mode
3. Verify session initialization
4. Test mode switching
5. Test identity reveal functionality
6. Review test results

### Expected API Calls

```javascript
// Initialize session
POST /api/v2/hybrid-identity/initialize-session
{
  "user_email": "user@example.com",
  "identity_mode": "anonymous",
  "survey_id": 1
}

// Switch mode
POST /api/v2/hybrid-identity/switch-mode
{
  "session_token": "...",
  "new_mode": "conditional"
}

// Process reveal
POST /api/v2/hybrid-identity/process-reveal-request
?user_email=user@example.com
&reveal_type=full
```

## Error Handling

### Common Errors and Solutions

1. **401 Unauthorized**
   - Check authentication token
   - Verify user is logged in
   - Check token expiration

2. **403 Forbidden**
   - Verify user role permissions
   - Check if user has required access level

3. **404 Not Found**
   - Verify resource exists
   - Check URL parameters
   - Verify database records

4. **422 Validation Error**
   - Check request payload
   - Verify required fields
   - Check data types

5. **500 Server Error**
   - Check server logs
   - Verify database connection
   - Check API endpoint implementation

## Testing Checklist

### Survey System
- [ ] Load survey list
- [ ] Filter surveys by status
- [ ] Start survey session
- [ ] Select identity mode
- [ ] Answer survey questions
- [ ] Submit survey response
- [ ] View survey analytics (admin)

### Admin Dashboard
- [ ] Load dashboard overview
- [ ] View system metrics
- [ ] Check identity analytics
- [ ] Review bias alerts
- [ ] Manage action items

### Integration Hub
- [ ] View integration status
- [ ] Setup HR integration
- [ ] Sync staff data
- [ ] Sync evaluation data
- [ ] View sync history

### Identity Mode
- [ ] Initialize anonymous session
- [ ] Initialize conditional session
- [ ] Initialize identified session
- [ ] Switch between modes
- [ ] Test identity reveal
- [ ] Verify reveal conditions

## Debugging Tips

1. **Check Browser Console**
   - Look for API errors
   - Check network requests
   - Verify response data

2. **Check Network Tab**
   - Verify request URLs
   - Check request payloads
   - Review response status codes

3. **Use Test Component**
   - Run identity mode tests
   - Review test results
   - Check API responses

4. **Check Backend Logs**
   - Verify API endpoint execution
   - Check database queries
   - Review error messages

## Next Steps

1. Test all components with real backend data
2. Verify error handling for edge cases
3. Test identity mode transitions thoroughly
4. Verify loading states work correctly
5. Test error boundaries with intentional errors
