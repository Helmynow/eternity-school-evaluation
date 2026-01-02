# Component Documentation

This document provides an overview of all React components in the frontend application.

## Component Structure

```
src/components/
├── admin/          # Admin-only components
├── auth/           # Authentication components
├── common/         # Shared/reusable components
├── dashboard/      # Dashboard components
├── eom/            # Employee of the Month components
├── history/        # History components
├── layout/         # Layout components
├── mre/            # Multi-Rater Evaluation components
├── notifications/  # Notification components
├── reports/        # Report components
└── survey/          # Survey components
```

## Survey Components

### SurveyList
**Path:** `components/survey/SurveyList.jsx`
**Purpose:** Display list of available surveys with filtering
**Props:** None
**Features:**
- Filter by status (all, active, draft, closed)
- Create survey button (admin only)
- Start survey button
- View analytics button (admin only)
**Uses:** `useAuth`, `apiClient.survey.getAll`

### SurveySession
**Path:** `components/survey/SurveySession.jsx`
**Purpose:** Initialize and manage survey session with identity mode selection
**Props:** None (uses route params)
**Features:**
- Identity mode selection
- Survey session initialization
- Question filtering by identity mode
- Response submission
**Uses:** `useAuth`, `useSurvey`, `apiClient.hybridIdentity`

### SurveyForm
**Path:** `components/survey/SurveyForm.jsx`
**Purpose:** Multi-step survey form for answering questions
**Props:**
- `survey`: Survey object
- `questions`: Array of questions
- `identityMode`: Current identity mode
- `onSubmit`: Callback for submission
- `onBack`: Callback for going back
**Features:**
- Progress tracking
- Question validation
- Multiple question types (text, multiple choice, rating, yes/no)
- Required field validation
**Uses:** None (pure presentation)

### SurveyCreate
**Path:** `components/survey/SurveyCreate.jsx`
**Purpose:** Create new survey (admin only)
**Props:** None
**Features:**
- Survey creation form
- Template loading option
- Date range selection
- Survey type selection
**Uses:** `useAuth`, `useSurveyTemplates`, `apiClient.survey.create`

### SurveyEdit
**Path:** `components/survey/SurveyEdit.jsx`
**Purpose:** Edit existing survey (admin only)
**Props:** None (uses route params)
**Features:**
- Survey editing form
- Status management
- Date updates
**Uses:** `useAuth`, `useSurvey`, `apiClient.survey.update`

### SurveyQuestions
**Path:** `components/survey/SurveyQuestions.jsx`
**Purpose:** Manage survey questions (admin only)
**Props:** None (uses route params)
**Features:**
- Add/edit/delete questions
- Question ordering
- Question type selection
- Category assignment
**Uses:** `useAuth`, `useSurvey`, `apiClient.survey.getQuestions`

### SurveyAnalytics
**Path:** `components/survey/SurveyAnalytics.jsx`
**Purpose:** Display survey analytics and insights (admin only)
**Props:** None (uses route params)
**Features:**
- Response statistics
- Identity mode distribution charts
- Response trends
- Category breakdown
**Uses:** `useAuth`, `apiClient.survey.getAnalytics`, Recharts

### IdentityModeSelector
**Path:** `components/survey/IdentityModeSelector.jsx`
**Purpose:** Select privacy/identity mode for survey
**Props:**
- `onSelect`: Callback when mode is selected
- `initialMode`: Pre-selected mode
**Features:**
- Three mode options (anonymous, conditional, identified)
- Privacy level indicators
- Visual mode cards
**Uses:** None (pure presentation)

### IdentityReveal
**Path:** `components/survey/IdentityReveal.jsx`
**Purpose:** Process identity reveal requests
**Props:**
- `surveyId`: Optional survey ID
- `onRevealComplete`: Callback after reveal
**Features:**
- Multiple reveal methods
- Conditional reveal setup
- Consent-based reveal
**Uses:** `useAuth`, `apiClient.hybridIdentity.processReveal`

### IdentityModeTest
**Path:** `components/survey/IdentityModeTest.jsx`
**Purpose:** Test identity mode transitions and reveal functionality
**Props:** `surveyId` (optional)
**Features:**
- Mode selection testing
- Mode switching testing
- Identity reveal testing
- Test result logging
**Uses:** `useAuth`, `apiClient.hybridIdentity`

## Admin Components

### AdminDashboard
**Path:** `components/admin/AdminDashboard.jsx`
**Purpose:** Main admin dashboard with multiple tabs
**Props:** None
**Features:**
- Overview cards
- System metrics tab
- Identity analytics tab
- Bias alerts tab
- Action items tab
**Uses:** `useAuth`, `useAdmin`, multiple admin sub-components

### SystemMetrics
**Path:** `components/admin/SystemMetrics.jsx`
**Purpose:** Display real-time system metrics
**Props:**
- `metrics`: Metrics data object
- `loading`: Loading state
**Features:**
- Active users count
- API request statistics
- Response time metrics
- Usage trends charts
- Feature usage charts
**Uses:** Recharts

### IdentityAnalytics
**Path:** `components/admin/IdentityAnalytics.jsx`
**Purpose:** Display identity mode analytics
**Props:**
- `analytics`: Analytics data object
- `loading`: Loading state
**Features:**
- Total sessions count
- Mode distribution pie chart
- Reveal methods bar chart
**Uses:** Recharts

### BiasAlerts
**Path:** `components/admin/BiasAlerts.jsx`
**Purpose:** Display bias detection alerts
**Props:** None
**Features:**
- Cycle selector
- Alert severity indicators
- Alert details display
**Uses:** `apiClient.bias.getReport`, `apiClient.cycles.getAll`

### ActionItems
**Path:** `components/admin/ActionItems.jsx`
**Purpose:** Display admin action items from objections and notifications
**Props:** None
**Features:**
- Pending objections
- Unread notifications
- Priority indicators
- Action completion
**Uses:** `useAuth`, `apiClient.objections`, `apiClient.notifications`

### IntegrationHub
**Path:** `components/admin/IntegrationHub.jsx`
**Purpose:** HR system integration management (CEO only)
**Props:** None
**Features:**
- Integration status tab
- HR setup tab
- Sync history tab
- Manual sync controls
**Uses:** `useAuth`, `useIntegration`

### IntegrationStatus
**Path:** `components/admin/IntegrationStatus.jsx`
**Purpose:** Display integration connection status
**Props:**
- `evaluationBridge`: Bridge data object
- `loading`: Loading state
**Features:**
- Connection status indicator
- Bridge configuration
- Field mappings
- Sync statistics
**Uses:** None (pure presentation)

### SyncHistory
**Path:** `components/admin/SyncHistory.jsx`
**Purpose:** Display sync operation history
**Props:** None
**Features:**
- Sync type and status
- Records synced count
- Timestamp display
**Uses:** `apiClient` (placeholder implementation)

## Common Components

### ErrorBoundary
**Path:** `components/common/ErrorBoundary.jsx`
**Purpose:** Catch and handle React errors gracefully
**Props:**
- `children`: Child components
- `fallback`: Optional custom error UI
- `showDetails`: Show error details (default: false)
**Features:**
- Error catching
- User-friendly error messages
- Retry functionality
- Error logging

### LoadingSkeleton
**Path:** `components/common/LoadingSkeleton.jsx`
**Purpose:** Display loading placeholders
**Props:**
- `type`: Skeleton type (card, list, table, dashboard, form, default)
- `count`: Number of skeletons to display
**Exports:**
- `LoadingSkeleton`: Main component
- `LoadingSpinner`: Spinner component
- `LoadingOverlay`: Full-screen overlay

## Component Patterns

### Error Handling
All components should be wrapped with `ErrorBoundary`:
```jsx
<ErrorBoundary>
  <YourComponent />
</ErrorBoundary>
```

### Loading States
Use `LoadingSkeleton` instead of basic spinners:
```jsx
if (loading) {
  return <LoadingSkeleton type="card" count={3} />
}
```

### API Calls
Use custom hooks when available:
```jsx
const { surveys, loading, fetchSurveys } = useSurvey()
```

### Authentication
Check user roles before rendering:
```jsx
const { isCEO, isPNC } = useAuth()
if (!isCEO && !isPNC) {
  return <AccessDenied />
}
```

## Component Dependencies

### Required Packages
- `react` - React library
- `react-router-dom` - Routing
- `react-hot-toast` - Toast notifications
- `recharts` - Chart components
- `axios` - HTTP client

### Internal Dependencies
- `hooks/useAuth` - Authentication
- `hooks/useAPI` - API data fetching
- `lib/api` - API client
- `lib/supabase` - Supabase client
