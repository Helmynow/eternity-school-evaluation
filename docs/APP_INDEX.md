# Eternity School Evaluation System - Application Index

## 📋 Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [API Endpoints](#api-endpoints)
4. [Core Modules](#core-modules)
5. [Features](#features)
6. [Database Schema](#database-schema)
7. [Frontend Components](#frontend-components)
8. [Documentation](#documentation)

---

## Overview

**Eternity School Evaluation System** is a comprehensive fair evaluation platform featuring:
- **Multi-Rater Evaluation (MRE)** with weighted scoring
- **Employee of the Month (EOM)** nomination and voting
- **Advanced Bias Detection** and mitigation (360-degree, context-aware, real-time)
- **AI-Powered Features** (nomination suggestions, bias detection, analytics)
- **Smart Notifications** (behavior-based reminders, escalation alerts)
- **Comprehensive Analytics** and reporting
- **Hybrid Identity Survey System** (4 identity modes: Anonymous, Conditional, Partial, Identified)
- **Complete Survey Templates** (50+ questions across 6+ sections)
- **Admin Dashboard** (real-time monitoring, identity analytics, bias detection)
- **HR & Evaluation Integration** (bidirectional sync, evaluation bridge)

**Version:** 2.0.0  
**Framework:** FastAPI (v2) + React (v18)  
**Database:** PostgreSQL (Supabase)

---

## Architecture

```
eternity-school-evaluation/
├── backend/                    # Python FastAPI backend
│   ├── fastapi_app.py         # Main API application (80+ endpoints)
│   ├── database.py            # SQLAlchemy models (20+ tables)
│   ├── bias_detection*.py     # Bias detection modules
│   ├── eom_*.py              # EOM validation & rotation
│   ├── weight_matrix*.py      # Weight calculation
│   ├── smart_notification_system.py  # Smart notifications
│   ├── hybrid_identity_system.py  # Hybrid identity controller
│   ├── hybrid_identity_components.py  # Identity components
│   ├── survey_identity_manager.py  # Identity preferences
│   ├── conditional_anonymity_engine.py  # Conditional anonymity
│   ├── survey_templates.py    # Survey templates (50+ questions)
│   ├── admin_dashboard.py     # Admin dashboard
│   ├── integration_hub.py    # HR & evaluation integration
│   ├── system_setup.py       # System setup & configuration
│   └── ai_models/            # AI/ML modules
├── frontend/                 # React frontend (v18)
│   ├── src/
│   │   ├── components/        # React components
│   │   ├── hooks/           # Custom hooks
│   │   └── lib/            # Utilities
│   └── public/              # Static assets
├── supabase/                # Database migrations
│   └── migrations/          # SQL migration files (15+ migrations)
└── docs/                    # Documentation (20+ docs)
```

---

## API Endpoints

### Root & Health
- `GET /` - API information and endpoint index
- `GET /api/v2/health` - Health check

### Cycles Management
- `GET /api/v2/cycles` - List all cycles
- `GET /api/v2/cycles/current` - Get current active cycle
- `GET /api/v2/cycles/{cycle_id}` - Get cycle details

### EOM (Employee of the Month)

#### Nominations
- `POST /api/v2/eom/nominations/suggest-category` - AI category suggestion
- `POST /api/v2/eom/nominations/submit` - Submit nomination
- `POST /api/v2/eom/nominations/validate` - Validate single nomination
- `POST /api/v2/eom/nominations/batch-validate` - Validate multiple nominations

#### Rotation Rules
- `POST /api/v2/eom/rotation-rules/create` - Create rotation rule
- `PUT /api/v2/eom/rotation-rules/{rule_id}` - Update rotation rule
- `GET /api/v2/eom/rotation-rules/cycle/{cycle_id}` - Get rules for cycle
- `POST /api/v2/eom/rotation-rules/check-eligibility` - Check nominee eligibility
- `GET /api/v2/eom/rotation-rules/eligible-nominees/{eom_cycle_id}` - List eligible nominees
- `GET /api/v2/eom/rotation-rules/ineligible-nominees/{eom_cycle_id}` - List ineligible nominees
- `POST /api/v2/eom/rotation-rules/setup-defaults/{cycle_id}` - Setup default rules
- `GET /api/v2/eom/rotation-rules/analytics/{cycle_id}` - Rotation analytics
- `GET /api/v2/eom/rotation-rules/nominee-history/{nominee_email}` - Get nominee history
- `GET /api/v2/eom/rotation-rules/summary/{cycle_id}` - Get rotation summary
- `POST /api/v2/eom/rotation-rules/update-eligibility-flags/{eom_cycle_id}` - Update eligibility flags

#### EOM Features
- `GET /api/v2/eom/hall-of-fame` - EOM winners history
- `GET /api/v2/eom/diversity-tracking` - Diversity monitoring
- `POST /api/v2/eom/feedback` - Submit feedback
- `GET /api/v2/eom/cycles/{cycle_id}/window-status` - Nomination window status

### MRE (Multi-Rater Evaluation)

#### Evaluations
- `POST /api/v2/mre/evaluations/process` - Process evaluation submission
- `GET /api/v2/mre/evaluations/{cycle_id}/weighted-scores` - Get weighted scores

### Bias Detection

#### Reports
- `POST /api/v2/bias/reports/generate` - Generate comprehensive bias report
- `GET /api/v2/bias/reports/{cycle_id}` - Get bias report for cycle
- `GET /api/v2/bias/reports/{cycle_id}/target/{target_email}` - Get target-specific bias summary

#### Analytics
- `GET /api/v2/bias/analytics/{cycle}` - Generate bias analytics report
- `POST /api/v2/bias/ai/analyze-evaluation/{evaluation_id}` - AI-powered evaluation analysis

#### 360-Degree Bias Detection
- `POST /api/v2/bias/360/context-aware-report/{cycle_id}` - Context-aware 360 report
- `GET /api/v2/bias/360/context-analysis/{cycle_id}/target/{email}` - Target context analysis
- `GET /api/v2/bias/360/context-comparison/{cycle_id}` - Context comparison
- `GET /api/v2/bias/360/context-coverage/{cycle_id}` - Context coverage analysis

### Scoring

#### Academic/Admin Scoring
- `GET /api/v2/scoring/academic-admin/{cycle_id}/score/{email}` - Get score for person
- `GET /api/v2/scoring/academic-admin/{cycle_id}/batch` - Batch scoring
- `GET /api/v2/scoring/academic-admin/{cycle_id}/compare` - Compare scoring methods
- `GET /api/v2/scoring/academic-admin/{cycle_id}/distribution` - Score distribution
- `GET /api/v2/scoring/academic-admin/{cycle_id}/validate` - Validate scoring
- `GET /api/v2/scoring/academic-admin/weight-matrices` - Get weight matrices

#### Optimized Scoring
- `GET /api/v2/scoring/optimized/batch/{cycle_id}` - Optimized batch scoring
- `GET /api/v2/scoring/optimized/statistics/{cycle_id}` - Scoring statistics
- `GET /api/v2/scoring/optimized/compare/{cycle_id}` - Compare optimized vs standard

### Reports

#### CEO Reports
- `POST /api/v2/reports/ceo/export` - Export CEO report (Excel/PDF)
- `GET /api/v2/reports/ceo/{cycle_id}` - Get CEO report data

### Notifications

#### Smart Notifications
- `GET /api/v2/notifications/user-behavior/{user_email}` - Get user behavior profile
- `POST /api/v2/notifications/smart-reminder/{cycle_id}` - Send smart reminders
- `POST /api/v2/notifications/check-overdue/{cycle_id}` - Check overdue evaluations
- `POST /api/v2/notifications/due-soon-reminders/{cycle_id}` - Send due soon reminders

#### Standard Notifications
- `GET /api/v2/notifications` - Get user notifications
- `POST /api/v2/notifications/{notification_id}/read` - Mark as read
- `POST /api/v2/notifications/read-all` - Mark all as read

### Objections
- `POST /api/v2/objections` - Submit objection
- `GET /api/v2/objections` - Get objections
- `POST /api/v2/objections/{objection_id}/resolve` - Resolve objection

### Audit Logs
- `GET /api/v2/audit-logs` - Get audit logs with filters

### Data Import
- `POST /api/v2/import/staff` - Import staff data
- `POST /api/v2/import/eom-voters` - Import EOM voters
- `POST /api/v2/import/eom-candidates` - Import EOM candidates
- `POST /api/v2/import/weight-matrix` - Import weight matrix

### Analytics
- `GET /api/v2/analytics/participation/{cycle_id}` - Participation analytics

### Hybrid Identity Survey System
- `POST /api/v2/hybrid-identity/initialize-session` - Initialize hybrid identity session
- `POST /api/v2/hybrid-identity/create-survey-session` - Create survey session with mode-specific questions
- `POST /api/v2/hybrid-identity/submit-response` - Submit survey response with identity processing
- `POST /api/v2/hybrid-identity/switch-mode` - Switch identity mode
- `POST /api/v2/hybrid-identity/process-reveal-request` - Process identity reveal request
- `GET /api/v2/hybrid-identity/analyze-survey-data` - Comprehensive survey data analysis

### Survey Templates
- `GET /api/v2/survey-templates/comprehensive` - Get comprehensive school climate survey template
- `GET /api/v2/survey-templates/section/{category}` - Get specific survey section by category

### Admin Dashboard
- `GET /api/v2/admin/dashboard` - Get comprehensive admin dashboard
- `GET /api/v2/admin/dashboard/overview-cards` - Get overview metric cards
- `GET /api/v2/admin/dashboard/real-time-metrics` - Get real-time system metrics
- `GET /api/v2/admin/dashboard/identity-analytics` - Get identity mode analytics

### Integration Hub
- `POST /api/v2/integration/hr/setup` - Setup HR system integration
- `GET /api/v2/integration/evaluation-bridge` - Get evaluation data bridge configuration
- `POST /api/v2/integration/sync/staff` - Sync staff data from HR system
- `POST /api/v2/integration/sync/evaluation` - Sync evaluation data between systems

### System Setup
- `POST /api/v2/system/setup` - Setup complete integrated system
- `GET /api/v2/system/go-live-checklist` - Get go-live checklist

---

## Core Modules

### Backend Modules

#### Database (`backend/database.py`)
- SQLAlchemy models for all tables
- Database connection and session management
- Enums: `StaffSegment`, `EOMCategory`, `ActionType`

#### Bias Detection
- **`bias_detection.py`** - Core bias detection algorithms
- **`bias_detection_360.py`** - Complete 360-degree bias detection
- **`context_aware_bias_detection.py`** - Context-aware bias analysis
- **`realtime_bias_detector.py`** - Real-time bias detection

#### EOM System
- **`eom_validation.py`** - Nomination validation (rotation, attendance, duplicates)
- **`eom_rotation_manager.py`** - Rotation rule management

#### Weight Matrix
- **`weight_matrix_handler.py`** - Weight matrix operations
- **`academic_admin_scoring.py`** - Academic vs Admin scoring
- **`weight_matrix_calculator.py`** - Weight calculations
- **`optimized_evaluation_calculator.py`** - Optimized scoring

#### Notifications
- **`smart_notification_system.py`** - Smart reminders, behavior tracking, escalation alerts
- **`email_service.py`** - Email sending service

#### Analytics
- **`participation_analytics.py`** - Participation tracking and analytics
- **`audit_logger.py`** - Audit logging

#### AI Models (`backend/ai_models/`)
- **`eom_category_recommender.py`** - AI category recommendations
- **`bias_analytics.py`** - Bias analytics with ML
- **`ai_bias_detector.py`** - AI-powered bias detection

#### Utilities
- **`bulk_import.py`** - Bulk data import

#### Hybrid Identity System
- **`hybrid_identity_system.py`** - Main hybrid identity system controller
- **`hybrid_identity_components.py`** - Core components (IdentityManager, SurveyEngine, AnalyticsEngine, PrivacyManager, ConsentTracker)
- **`survey_identity_manager.py`** - Survey identity preference management
- **`conditional_anonymity_engine.py`** - Conditional anonymity engine

#### Survey & Admin
- **`survey_templates.py`** - Complete survey templates system (50+ questions, 6+ sections)
- **`admin_dashboard.py`** - Admin dashboard and analytics (real-time metrics, identity analytics)
- **`integration_hub.py`** - HR and evaluation system integration (bidirectional sync, evaluation bridge)
- **`system_setup.py`** - System setup and configuration (go-live checklist, training materials)

### Frontend Components

#### Layout (`frontend/src/components/layout/`)
- **`Layout.jsx`** - Main application layout with navigation

#### Auth (`frontend/src/components/auth/`)
- **`Login.jsx`** - Login page with Supabase authentication

#### Dashboard (`frontend/src/components/dashboard/`)
- **`Dashboard.jsx`** - Main dashboard with cycle selection, statistics, charts

#### EOM (`frontend/src/components/eom/`)
- **`EOMNomination.jsx`** - EOM nomination interface
- **`EOMVoting.jsx`** - EOM voting interface

#### MRE (`frontend/src/components/mre/`)
- **`MREEvaluation.jsx`** - Multi-rater evaluation form

#### Hooks (`frontend/src/hooks/`)
- **`useAuth.js`** - Authentication hook
- **`useAPI.js`** - API data fetching hook

#### Libraries (`frontend/src/lib/`)
- **`api.js`** - Axios API client
- **`supabase.js`** - Supabase client

---

## Features

### 1. Multi-Rater Evaluation (MRE)
- Weighted scoring system
- Academic vs Administrative staff differentiation
- Multiple evaluation contexts (CEO, P&C, QA, Peer, Manager, Self)
- Domain-specific scoring
- Validation and completeness checks

### 2. Employee of the Month (EOM)
- 5 categories: Outstanding Leadership, Team Spirit, Innovation, Rising Star, Service Excellence
- Nomination window validation (15th of month, 7-day window)
- Weighted voting (Principal 40%, Manager 30%, CEO 30%)
- Rotation rules (one win per term)
- Attendance validation (90% minimum)
- Hall of Fame / Winners history
- Diversity monitoring

### 3. Bias Detection
- **360-Degree Bias Detection:**
  - Structural completeness
  - Role-based bias
  - Temporal bias (recency/primacy)
  - Distribution bias (centrality, harshness, leniency)
  - Similarity bias (halo effect)
  - ML-based pattern detection
  - Inter-rater reliability
  - Context balance

- **Context-Aware Bias Detection:**
  - Context-specific analysis
  - Cross-context comparison
  - Coverage analysis

- **Real-Time Bias Detection:**
  - Halo effect detection
  - Recency bias detection
  - Department bias detection
  - Mitigation suggestions

### 4. Smart Notifications
- **User Behavior Tracking:**
  - Preferred completion hours
  - Average completion time
  - Completion patterns (early/on_time/late)
  - Optimal reminder timing

- **Smart Reminders:**
  - Behavior-based timing
  - Optimal time detection
  - Frequency limits

- **Escalation Alerts:**
  - Overdue detection
  - Two-tier escalation (regular + manager notification)
  - Days overdue tracking

- **User Preferences:**
  - Enable/disable notification types
  - Frequency limits (immediate/daily/weekly)
  - Quiet hours configuration

### 5. Weight Matrix System
- Default weight matrices for Academic and Administrative staff
- Custom weight matrices per cycle
- Weight optimization
- Balanced evaluation load distribution

### 6. Analytics & Reporting
- Participation analytics
- Bias analytics with heat maps
- CEO reports (Excel/PDF export)
- Score distribution analysis
- Comparison reports

### 7. Data Import
- Staff data import
- EOM voters import
- EOM candidates import
- Weight matrix import (Excel)

### 8. Hybrid Identity Survey System
- **4 Identity Modes**: Anonymous, Conditional, Partial, Full
- **Dynamic Mode Switching**: Change identity modes during survey
- **Mode-Specific Questions**: Different questions based on identity mode
- **Conditional Reveals**: User-controlled identity revelation
- **Advanced Analytics**: Mode-based analysis and honesty indicators
- **Bias Detection**: Comprehensive bias analysis across modes
- **Privacy Management**: Full privacy compliance and data protection

### 9. Survey Templates System
- **50+ Questions**: Comprehensive question bank
- **6+ Sections**: Physical environment, workplace culture, management, etc.
- **Mode-Specific Sections**: Identity mode-specific question sets
- **Sensitive Topics**: Anonymous-only sensitive questions
- **Accountability**: Identified-only accountability questions
- **Future Engagement**: Conditional-only engagement questions

### 10. Admin Dashboard
- **Real-Time Metrics**: System health and activity monitoring
- **Overview Cards**: Key metrics at a glance
- **Identity Analytics**: Mode-based analysis and trends
- **Bias Detection Summary**: Bias alerts and fairness scores
- **Action Items**: Prioritized admin tasks
- **Charts & Visualizations**: Data visualization
- **Admin Tools**: System management utilities

### 11. HR & Evaluation Integration
- **Bidirectional Sync**: Two-way data synchronization with HR
- **Evaluation Bridge**: Survey feedback to evaluation integration
- **Weight Mapping**: Different weights per identity mode
- **Security Protocols**: OAuth2, encryption, audit logging
- **Real-Time Sync**: Optional real-time synchronization
- **Error Handling**: Robust error handling and retry logic

---

## Database Schema

### Core Tables
- **`cycles`** - Evaluation cycles
- **`people`** - Staff members
- **`assignments`** - MRE assignments (who evaluates whom)
- **`evaluations`** - Evaluation submissions
- **`weight_matrices`** - Weight matrix definitions

### EOM Tables
- **`eom_cycles`** - EOM cycles
- **`eom_voters`** - EOM voters with weights
- **`eom_nominees`** - EOM nominations
- **`eom_winners`** - EOM winners history
- **`eom_rotation_rules`** - Rotation rules

### Supporting Tables
- **`email_notifications`** - Email notification tracking
- **`feedback`** - Feedback collection
- **`variance_alerts`** - Variance alert tracking
- **`audit_logs`** - Audit trail
- **`attendance`** - Attendance records

### Views
- **`eom_hall_of_fame`** - EOM winners view
- **`eom_diversity_monitoring`** - Diversity tracking view
- **`mre_evaluation_summary`** - MRE summary view
- **`weighted_score_summary`** - Weighted scores view

### Survey & Identity Tables
- **`surveys`** - Survey definitions
- **`survey_questions`** - Survey questions
- **`survey_responses`** - Survey responses
- **`survey_identity_preferences`** - User identity mode preferences
- **`survey_identity_reveals`** - Identity reveal tracking
- **`survey_conditional_reveals`** - Conditional reveal configurations

---

## Frontend Components

### Pages
- **Login** (`/login`) - Authentication
- **Dashboard** (`/dashboard`) - Main dashboard
- **EOM Nomination** (`/eom/nominate`) - Nomination interface
- **EOM Voting** (`/eom/vote`) - Voting interface
- **MRE Evaluation** (`/mre/evaluate`) - Evaluation form
- **Survey** (`/survey`) - Survey completion interface
- **Admin Dashboard** (`/admin`) - Admin management dashboard

### UI Components
- Layout with navigation
- Charts and statistics
- Forms with validation
- Toast notifications
- Loading states

### Styling
- Tailwind CSS
- ESE brand theme
- Custom color palette
- Responsive design

---

## Documentation

### Setup & Configuration
- `README.md` - Main project README
- `QUICK_START_AUTH.md` - Quick authentication setup
- `AUTHENTICATION_SETUP.md` - Detailed auth setup
- `SUPABASE_SETUP.md` - Supabase configuration

### Feature Documentation
- `SMART_NOTIFICATIONS.md` - Smart notification system
- `360_BIAS_DETECTION.md` - 360-degree bias detection
- `CONTEXT_AWARE_BIAS_DETECTION.md` - Context-aware bias
- `EOM_ROTATION_VALIDATION.md` - EOM validation
- `ACADEMIC_ADMIN_SCORING.md` - Scoring system
- `EVALUATION_OPTIMIZATION.md` - Optimization features
- `SURVEY_IDENTITY_SYSTEM.md` - Survey identity management
- `HYBRID_IDENTITY_SYSTEM.md` - Complete hybrid identity survey system
- `SURVEY_TEMPLATES_AND_ADMIN.md` - Survey templates and admin dashboard

### API Documentation
- `FASTAPI_ENDPOINTS.md` - Complete API reference
- `FASTAPI_QUICK_START.md` - Quick start guide

### Database Documentation
- `DATABASE_MODELS.md` - Database models
- `MIGRATION_REVIEW.md` - Migration guide

### Development
- `CONTRIBUTING.md` - Contribution guidelines
- `GAP_ANALYSIS.md` - Feature gap analysis
- `FIXES_APPLIED.md` - Applied fixes log

### System Evaluation
- `SYSTEM_EVALUATION.md` - Comprehensive system evaluation (94.25% - Grade A)
- `EVALUATION_SUMMARY.md` - Quick evaluation summary

---

## Quick Links

### API Documentation
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Frontend
- Development: `http://localhost:5173`
- Production: Configure in `vite.config.js`

### Database
- Supabase Dashboard: Check `supabase/config.toml`
- Migrations: `supabase/migrations/`

---

## Version History

- **v2.0.0** - Current version with FastAPI, smart notifications, enhanced bias detection
- **v1.0.0** - Initial Flask-based version (deprecated)

---

---

## Complete Feature Matrix

### Survey System Features

| Feature | Anonymous | Conditional | Partial | Identified |
|---------|-----------|------------|---------|------------|
| **Questions Available** | 35+ | 40+ | 38+ | 42+ |
| **Sensitive Topics** | ✅ Yes | ❌ No | ❌ No | ❌ No |
| **Accountability** | ❌ No | ❌ No | ❌ No | ✅ Yes |
| **Future Engagement** | ❌ No | ✅ Yes | ❌ No | ❌ No |
| **Data Retention** | 90 days | 180 days | 365 days | 365 days |
| **Can Reveal Identity** | ❌ No | ✅ Yes | ✅ Yes | ✅ Yes |
| **Honesty Score** | 8.7/10 | 7.8/10 | 7.5/10 | 6.9/10 |

### Integration Capabilities

| Integration Type | Status | Features |
|-----------------|--------|----------|
| **HR System** | ✅ Ready | Bidirectional sync, field mapping, conflict resolution |
| **Evaluation System** | ✅ Ready | Weight mapping, bias adjustment, context-aware weighting |
| **Real-Time Sync** | ✅ Optional | Webhooks, event-driven updates |
| **Batch Sync** | ✅ Enabled | Daily sync, retry logic, error handling |

### Admin Dashboard Features

| Feature Category | Features Count | Status |
|------------------|----------------|--------|
| **Overview Metrics** | 4 cards | ✅ Active |
| **Real-Time Monitoring** | 4 categories | ✅ Active |
| **Analytics** | 5+ analysis types | ✅ Active |
| **Bias Detection** | 4+ bias types | ✅ Active |
| **Action Items** | Dynamic | ✅ Active |
| **Charts** | 5+ chart types | ✅ Active |

### Survey Template Sections

| Section | Questions | Identity Modes | Sensitivity |
|---------|-----------|----------------|-------------|
| **Physical Environment** | 5 | All | Low |
| **Workplace Culture** | 5 | All | Medium-High |
| **Management** | 5 | All (some conditional) | Medium |
| **Inter-Departmental** | 3 | All | Low |
| **Personal Wellbeing** | 4 | All | Medium |
| **School Improvement** | 3 | All | Low |
| **Sensitive Topics** | 3 | Anonymous only | Very High |
| **Accountability** | 2 | Identified only | Low |
| **Future Engagement** | 2 | Conditional only | Low |

---

## System Statistics

- **Total API Endpoints**: 80+
- **Total Database Tables**: 20+
- **Total Migrations**: 15+
- **Total Documentation Files**: 20+
- **Survey Questions**: 50+
- **Survey Sections**: 9
- **Identity Modes**: 4
- **Bias Detection Types**: 10+
- **Integration Types**: 2 (HR, Evaluation)

---

**Last Updated:** 2024-01-15  
**Version:** 2.0.0  
**Maintained By:** Eternity School Development Team
