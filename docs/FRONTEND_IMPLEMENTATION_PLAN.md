# Frontend Implementation Plan - EVALVision

Based on the comprehensive ESE specification document, this outlines the frontend implementation plan.

## ✅ Completed Setup

1. **Frontend Foundation**
   - Vite + React 18 setup
   - React Router for navigation
   - Tailwind CSS with ESE brand colors
   - Supabase Auth integration
   - Project structure with organized components

2. **ESE Brand Integration**
   - Color palettes (Language Blues & International Greens)
   - Font system (Plus Jakarta Sans, Fraunces, Noto Sans Arabic)
   - Theme CSS variables matching brand guidelines
   - Directory structure for mascots and icons

## 📋 Implementation Roadmap

### Phase 1: Core Components (Week 1-2)

#### 1.1 Layout & Navigation
- [ ] **GlobalHeader**: Top navigation with ESE logo and user menu
- [ ] **NavigationBar**: Card-based nav with green band (per brand guidelines)
- [ ] **Layout Component**: Shell structure with header, nav, and content areas
- [ ] **Sidebar**: Role-based navigation (CEO, P&C, Department Heads, Staff)

#### 1.2 Authentication
- [ ] **Login Page**: Supabase Auth integration
- [ ] **Role Detection**: Identify user role (CEO, P&C, Department Head, Staff)
- [ ] **Protected Routes**: Role-based route protection
- [ ] **Session Management**: Handle auth state and refresh

#### 1.3 Dashboard
- [ ] **Admin Dashboard**: Real-time participation monitoring
- [ ] **EOM Dashboard**: Nomination counts, voting progress, category distribution
- [ ] **MRE Dashboard**: Evaluation completion rates, rater assignments
- [ ] **Bias Report Visualization**: Charts and graphs for bias detection results

### Phase 2: EOM Module (Week 2-3)

#### 2.1 Nomination Interface
- [ ] **Nomination Form**: 
  - Category selection (5 categories with descriptions)
  - Nominee selection from eligible staff list
  - Reason/evidence text area with character limit
  - Example prompts per category
  - Validation (rotation rules, attendance, duplicates)
  
- [ ] **Nomination List**: 
  - View all nominations (with anonymized nominators)
  - Filter by category
  - Search functionality
  - Status indicators (pending, verified, rejected)

#### 2.2 Voting Interface
- [ ] **Voting Dashboard**: Overview of all categories
- [ ] **Category Voting Cards**: One vote per category
- [ ] **Nominee Profiles**: Display nomination reasons and evidence
- [ ] **Vote Submission**: Confirmation and audit trail

#### 2.3 EOM Management (Admin)
- [ ] **Rotation Rules UI**: View and manage rotation rules
- [ ] **Eligibility Checker**: Verify nominees against rules
- [ ] **Winner Announcement**: Public announcement interface
- [ ] **Certificate Generation**: Digital certificates for winners

### Phase 3: MRE Module (Week 3-4)

#### 3.1 Evaluation Assignment
- [ ] **Assignment List**: View assigned evaluations
- [ ] **Required vs Optional**: Clear indicators
- [ ] **Deadline Tracking**: Countdown timers and reminders
- [ ] **Bulk Assignment View**: See all assignments at once

#### 3.2 Evaluation Form
- [ ] **Role-based Form**: Different domains based on target group (academic/admin)
- [ ] **Domain Scoring**: 
  - Admin: Task management, Policy adherence, Problem-solving, Teamwork, etc.
  - Academic: Parent feedback, Team collaboration, Student engagement, etc.
- [ ] **Weight Display**: Show weight percentages per domain
- [ ] **Self-Evaluation Section**: Separate 5% self-evaluation form
- [ ] **Draft Saving**: Auto-save drafts
- [ ] **Submission Confirmation**: Final review before submit

#### 3.3 Weight Matrix Visualization
- [ ] **Matrix Display**: Visual representation of rater weights
- [ ] **Calibration Dashboard**: See how weights contribute to final scores
- [ ] **Inconsistency Alerts**: Highlight outliers or calibration issues

### Phase 4: Advanced Features (Week 4-5)

#### 4.1 Bias Detection UI
- [ ] **Bias Report Dashboard**: 
  - Overall bias score
  - Findings by type (role bias, recency, centrality, etc.)
  - Severity indicators
  - Recommendations
  
- [ ] **Bias Visualization**:
  - Charts for distribution analysis
  - Heatmaps for rater patterns
  - Timeline views for temporal bias
  - Context comparison graphs

#### 4.2 Analytics & Reporting
- [ ] **Participation Analytics**: 
  - Completion rates by department
  - Rater participation tracking
  - Deadline adherence metrics
  
- [ ] **Trend Analysis**:
  - Historical comparisons
  - Performance improvements over time
  - Recognition patterns
  
- [ ] **Export Functionality**:
  - CSV export for reports
  - PDF generation for CEO reports
  - Excel exports with charts

#### 4.3 Notifications & Reminders
- [ ] **In-app Notifications**: 
  - Nomination windows opening/closing
  - Voting deadlines
  - Evaluation assignments
  - Reminders for incomplete tasks
  
- [ ] **Email Integration**: 
  - Automated reminder emails
  - Deadline warnings
  - Winner announcements

### Phase 5: Mobile & Polish (Week 5-6)

#### 5.1 Mobile Responsiveness
- [ ] **Responsive Design**: Mobile-first approach
- [ ] **Touch Optimization**: Large tap targets, swipe gestures
- [ ] **Mobile Navigation**: Collapsible menu, bottom nav option

#### 5.2 Accessibility
- [ ] **WCAG AA Compliance**: Color contrast, keyboard navigation
- [ ] **Screen Reader Support**: ARIA labels, semantic HTML
- [ ] **Reduced Motion**: Respect prefers-reduced-motion

#### 5.3 Performance
- [ ] **Code Splitting**: Lazy load routes
- [ ] **Image Optimization**: Optimize mascots and icons
- [ ] **Caching Strategy**: Cache API responses
- [ ] **Bundle Optimization**: Tree shaking, minification

## 🎨 Design System Components

### UI Components to Build

1. **Cards & Surfaces**
   - `ESECard`: Embossed card with brand shadows
   - `ESETile`: Square tiles for navigation
   - `ESEStatCard`: Dashboard stat cards

2. **Forms**
   - `ESEInput`: Text inputs with brand styling
   - `ESESelect`: Dropdown selects
   - `ESETextarea`: Multi-line inputs
   - `ESERadio`: Radio buttons for categories
   - `ESECheckbox`: Checkboxes

3. **Buttons & Actions**
   - `ESEButton`: Primary, secondary, tertiary variants
   - `ESEIconButton`: Icon-only buttons
   - `ESEBadge`: Status badges (mustard, terracotta, etc.)

4. **Navigation**
   - `ESENavCard`: Card-based navigation items
   - `ESETab`: Tab navigation with active states
   - `ESEBreadcrumb`: Breadcrumb navigation

5. **Feedback**
   - `ESEToast`: Notification toasts
   - `ESEModal`: Modal dialogs
   - `ESELoading`: Loading states
   - `ESEEmptyState`: Empty state illustrations

6. **Data Display**
   - `ESETable`: Data tables
   - `ESECalendar`: Calendar component
   - `ESEChart`: Chart wrapper (Recharts)
   - `ESETimeline`: Timeline for evaluation cycles

## 📐 Brand Implementation Details

### Colors Usage
- **Language Division Pages**: Blue palette (#094773 primary, #9DC6E1 backgrounds)
- **International Division Pages**: Green palette (#2C5B4C primary, #E5F6DF backgrounds)
- **Whole School Pages**: 60/40 split of blue/green
- **Accents**: Mustard (#E4A740) for CTAs, Terracotta (#C88167) for warnings

### Typography
- **Headings**: Fraunces (serif) - for hero sections, page titles
- **Body**: Plus Jakarta Sans (sans-serif) - for all body text
- **Arabic**: Noto Sans Arabic - for Arabic content support

### Mascots
- **Language Division**: Blue-tinted mascots (BLUE 1.png, BLUE 2.png, BLUE 3.png)
- **International Division**: Green-tinted mascots (GREEN 1.png, GREEN 2.png, GREEN 3.png)
- **Usage**: Supporting elements, never replace logo, maintain clear space

### Icons
- **Location**: `/public/assets/icons/`
- **Style**: Handmade colorful icons
- **Usage**: Add, edit, delete, search, notifications, announcements

## 🔐 Role-Based Features

### CEO (Super Admin)
- Full system access
- Modify any variable (weights, rules, schedules)
- Detailed reports and analytics
- Override any validation
- Export all data

### People & Culture (P&C)
- Staff list management
- Eligibility verification
- Attendance monitoring
- Add/remove staff from programs
- View all nominations and evaluations

### Department Heads / Principals
- Nominate for EOM
- Vote in EOM
- Complete MRE evaluations (as raters)
- View team evaluations
- Department-specific analytics

### Staff Members
- View own evaluations
- Complete self-evaluations (5%)
- View EOM nominations (public feed)
- Submit peer feedback (if applicable)

## 📊 Data Integration

### API Endpoints to Connect

1. **EOM Endpoints** (FastAPI `/api/v2/eom/`)
   - `POST /nominations/submit` - Submit nomination
   - `POST /nominations/validate` - Validate before submit
   - `GET /nominations/{cycle_id}` - List nominations
   - `POST /vote` - Submit vote
   - `GET /winners/{cycle_id}` - Get winners

2. **MRE Endpoints** (FastAPI `/api/v2/mre/`)
   - `GET /assignments/{cycle_id}` - Get assignments
   - `POST /evaluations/process` - Submit evaluation
   - `GET /evaluations/{cycle_id}/weighted-scores` - View scores

3. **Bias Detection** (FastAPI `/api/v2/bias/`)
   - `POST /reports/generate` - Generate report
   - `GET /reports/{cycle_id}` - Get report
   - `GET /reports/{cycle_id}/target/{email}` - Target-specific

4. **Dashboard** (FastAPI `/api/v2/dashboard/`)
   - `GET /participation/{cycle_id}` - Participation stats
   - `GET /analytics/{cycle_id}` - Analytics data

## 🚀 Next Immediate Steps

1. **Create Missing Components**:
   - `components/layout/Layout.jsx`
   - `components/auth/Login.jsx`
   - `components/dashboard/Dashboard.jsx` (enhance existing)
   - `components/eom/EOMNomination.jsx`
   - `components/mre/MREEvaluation.jsx`

2. **Set Up API Client**:
   - `lib/api.js` - Axios/fetch wrapper
   - `lib/supabase.js` - Supabase client utilities
   - `hooks/useAuth.js` - Authentication hook
   - `hooks/useAPI.js` - API data fetching hook

3. **Copy Brand Assets**:
   - Copy logo from `/Users/helmy/Desktop/team/assets/media/logo-no-bound.png`
   - Copy mascots from `/Users/helmy/Desktop/team/assets/mascots/`
   - Copy icons from `/Users/helmy/Desktop/team/assets/Icons/`

4. **Environment Setup**:
   - Create `.env.example` with required variables
   - Document environment setup in README

## 📝 Notes

- All dates follow the schedule: EOM nominations (15th), voting (18-20th), MRE rounds (Dec 15-25, Mar 15-25)
- Rotation rules: Max 1 win per term, categories can be skipped
- Weight matrices are cycle-specific and configurable
- All actions are logged in audit trail
- Bias detection runs automatically after cycle closure

