# Migration Files - Full Content Reference

All migration files are located in: `supabase/migrations/`

## Quick Access

To view any migration file:
```bash
cat supabase/migrations/20240101000000_initial_schema.sql
```

Or open in your editor:
```bash
code supabase/migrations/20240101000000_initial_schema.sql
```

---

## All 42 Migration Files

### 1. `20240101000000_initial_schema.sql` (285 lines)
**Purpose:** Base schema - Creates all tables, enums, indexes, and constraints

**Creates:**
- Enums: `staff_segment`, `eom_category`, `action_type`, `rotation_period_type`
- Tables: `cycles`, `people`, `assignments`, `evaluations`, `eom_cycles`, `eom_voters`, `eom_nominees`, `eom_winners`, `eom_rotation_rules`, `weight_matrices`, `audit_logs`
- Triggers for `updated_at` columns
- Indexes for performance

**Full path:** `supabase/migrations/20240101000000_initial_schema.sql`

---

### 2. `20240101000001_add_missing_columns.sql` (316 lines)
**Purpose:** Add missing columns to existing tables

**Adds columns to:**
- `people`: segment, created_at, updated_at, active, department, role_title, hire_date
- `cycles`: created_at, updated_at
- `assignments`: weight_matrix_id, created_at, updated_at
- `evaluations`: weighted_rating, domain_scores, created_at, updated_at
- `eom_nominees`: category, rotation_eligible, last_nominated_cycle_id, last_won_cycle_id, nomination_count, win_count, votes_received, created_at, updated_at
- `eom_cycles`: category_rotation, created_at, updated_at
- `weight_matrices`: created_at, updated_at
- `eom_rotation_rules`: max_nominations_per_year, created_at, updated_at

**Full path:** `supabase/migrations/20240101000001_add_missing_columns.sql`

---

### 3. `20240101000002_create_views.sql` (161 lines)
**Purpose:** Create reporting views

**Creates views:**
- `mre_who_evaluates_who` - MRE evaluation relationships
- `mre_evaluation_summary` - Evaluation summary by target
- `eom_participants` - EOM voters and nominees
- `eom_nomination_summary` - Nomination statistics
- `eom_winner_history` - Winner history
- `weighted_score_summary` - Weighted scores by staff type
- `recent_audit_logs` - Recent audit trail

**Full path:** `supabase/migrations/20240101000002_create_views.sql`

---

### 4. `20240101000003_create_functions.sql` (282 lines)
**Purpose:** Create database functions

**Creates functions:**
- `calculate_weighted_score()` - Calculate weighted scores
- `get_cycle_statistics()` - Get cycle statistics
- `check_eom_eligibility()` - Check EOM nomination eligibility
- `get_eom_cycle_stats()` - Get EOM cycle statistics
- `validate_evaluation_requirements()` - Validate evaluation requirements
- `get_staff_count_by_segment()` - Get staff counts by segment
- `get_cycle_completion_status()` - Get cycle completion status

**Full path:** `supabase/migrations/20240101000003_create_functions.sql`

---

### 5. `20240101000004_row_level_security.sql` (184 lines)
**Purpose:** Enable RLS and create security policies

**Enables RLS on:**
- All core tables (cycles, people, assignments, evaluations, eom_* tables, etc.)

**Creates policies:**
- SELECT policies for authenticated users
- INSERT/UPDATE/DELETE policies for service_role only

**Full path:** `supabase/migrations/20240101000004_row_level_security.sql`

---

### 6. `20240101000005_fix_security_issues.sql` (277 lines)
**Purpose:** Fix security issues - Remove SECURITY DEFINER from views

**Fixes:**
- Changes views from SECURITY DEFINER to SECURITY INVOKER
- Enables RLS on missing tables
- Creates basic RLS policies for legacy tables

**Full path:** `supabase/migrations/20240101000005_fix_security_issues.sql`

---

### 7. `20240101000006_fix_function_search_path.sql` (380 lines)
**Purpose:** Fix function search path security

**Updates functions with:**
- `SET search_path = public` to prevent security vulnerabilities
- Applies to all existing functions

**Full path:** `supabase/migrations/20240101000006_fix_function_search_path.sql`

---

### 8. `20240101000007_optimize_rls_performance.sql` (323 lines)
**Purpose:** Optimize RLS performance - Fix auth.role() calls

**Fixes:**
- Wraps `auth.role()` calls in `(select auth.role())` for better performance
- Separates SELECT policies from write policies
- Updates all RLS policies for better performance

**Full path:** `supabase/migrations/20240101000007_optimize_rls_performance.sql`

---

### 9. `20240101000008_fix_multiple_permissive_policies.sql` (316 lines)
**Purpose:** Fix multiple permissive policies - Separate SELECT from write operations

**Fixes:**
- Separates SELECT policies (authenticated users) from write policies (service_role)
- Creates separate policies for INSERT, UPDATE, DELETE operations
- Fixes legacy table policies

**Full path:** `supabase/migrations/20240101000008_fix_multiple_permissive_policies.sql`

---

### 10. `20240101000009_fix_security_definer_views_and_rls.sql` (741 lines)
**Purpose:** Fix security definer views and ensure RLS policies exist

**Fixes:**
- Drops and recreates all views without SECURITY DEFINER
- Ensures all RLS policies exist for all tables
- Creates missing policies using DO blocks

**Full path:** `supabase/migrations/20240101000009_fix_security_definer_views_and_rls.sql`

---

### 11. `20240101000010_explicitly_set_security_invoker_on_views.sql` (19 lines)
**Purpose:** Explicitly set security_invoker on all views

**Sets:**
- `ALTER VIEW ... SET (security_invoker = true)` on all views

**Full path:** `supabase/migrations/20240101000010_explicitly_set_security_invoker_on_views.sql`

---

### 12. `20240101000011_fix_function_search_path_security.sql` (37 lines)
**Purpose:** Fix function search path security using ALTER FUNCTION

**Updates:**
- All functions with `ALTER FUNCTION ... SET search_path = public`

**Full path:** `supabase/migrations/20240101000011_fix_function_search_path_security.sql`

---

### 13. `20240101000012_add_new_features.sql` (235 lines)
**Purpose:** Add new features - Announcements, Notifications, Surveys, Feedback

**Creates tables:**
- `objections` - EOM objection system
- `announcements` - System announcements
- `notifications` - In-app notifications
- `surveys`, `survey_questions`, `survey_responses` - Survey system
- `feedback` - General feedback
- `ai_feedback` - AI-generated feedback

**Adds columns:**
- Approval workflow fields to `eom_nominees` and `evaluations`

**Full path:** `supabase/migrations/20240101000012_add_new_features.sql`

---

### 14. `20240101000013_fix_eom_categories_and_add_features.sql` (260 lines)
**Purpose:** Fix EOM categories and add features

**Updates:**
- EOM category enum to: `outstanding_leadership`, `team_spirit`, `innovation`, `rising_star`, `service_excellence`
- Adds nomination window to `eom_cycles`
- Adds weighted voting to `eom_voters`
- Adds variance alert system to `evaluations`
- Creates `eom_diversity_tracking` view
- Creates `eom_feedback` table
- Creates `eom_hall_of_fame` view
- Creates `email_notifications` table

**Full path:** `supabase/migrations/20240101000013_fix_eom_categories_and_add_features.sql`

---

### 15. `20240101000014_survey_identity_system.sql` (92 lines)
**Purpose:** Survey identity management system

**Creates tables:**
- `survey_identity_preferences` - User identity preferences per survey
- `survey_identity_reveals` - Identity reveal tracking

**Full path:** `supabase/migrations/20240101000014_survey_identity_system.sql`

---

### 16. `20240101000015_conditional_anonymity_engine.sql` (58 lines)
**Purpose:** Conditional anonymity engine

**Creates table:**
- `survey_conditional_reveals` - Conditional reveal configurations

**Full path:** `supabase/migrations/20240101000015_conditional_anonymity_engine.sql`

---

### 17. `20240101000016_add_missing_models.sql` (330 lines)
**Purpose:** Add missing database models

**Creates/updates tables:**
- `surveys`, `survey_questions`, `survey_responses` (enhanced)
- `notifications` (enhanced)
- `objections` (enhanced)
- `variance_alerts` - Variance alert tracking
- `feedback` (enhanced)

**Full path:** `supabase/migrations/20240101000016_add_missing_models.sql`

---

### 18. `20240101000017_add_survey_functions.sql` (456 lines)
**Purpose:** Add survey and identity management database functions

**Creates functions:**
- `aggregate_survey_responses()` - Aggregate survey responses
- `get_survey_response_stats()` - Get survey statistics
- `notify_survey_response_submitted()` - Notification trigger
- `notify_objection_submitted()` - Objection notification trigger
- `cleanup_expired_anonymous_responses()` - Cleanup expired data
- `cleanup_expired_anonymous_data_by_preference()` - Cleanup by user preference
- `link_anonymous_responses()` - Link anonymous to identified
- `transition_survey_identity()` - Transition identity mode
- `get_identity_transition_status()` - Get transition status

**Full path:** `supabase/migrations/20240101000017_add_survey_functions.sql`

---

### 19. `20240101000018_rbac_user_permissions.sql` (95 lines)
**Purpose:** RBAC user permissions system

**Creates:**
- `permission_type` enum with 20 permission types
- `user_permissions` table for time-based permission management
- RLS policies for permission management
- Indexes for performance

**Full path:** `supabase/migrations/20240101000018_rbac_user_permissions.sql`

---

### 20. `20240101000019_normalize_objections_submitted_by.sql` (77 lines)
**Purpose:** Normalize objections submitter data

**Updates:**
- Renames/backfills legacy objection submitter fields safely
- Adds/repairs related indexes

**Full path:** `supabase/migrations/20240101000019_normalize_objections_submitted_by.sql`

---

### 21. `20240101000020_super_admin_bootstrap_and_settings.sql` (147 lines)
**Purpose:** CEO bootstrap super admin + system settings

**Updates:**
- Removes hardcoded super admin email from policies
- Adds `system_settings` singleton table for Settings UI
- Adds bootstrap helpers used by CEO/Super Admin logic

**Full path:** `supabase/migrations/20240101000020_super_admin_bootstrap_and_settings.sql`

---

### 22. `20240101000021_hybrid_identity_sessions.sql` (66 lines)
**Purpose:** Hybrid identity session persistence

**Creates:**
- `hybrid_identity_sessions` for cross-request survey flows

**Full path:** `supabase/migrations/20240101000021_hybrid_identity_sessions.sql`

---

### 23. `20240101000022_security_lint_fixes.sql` (134 lines)
**Purpose:** Security lint fixes (RLS + SECURITY INVOKER)

**Updates:**
- Ensures views use SECURITY INVOKER
- Enables RLS on missing tables
- Adds missing policies where needed

**Full path:** `supabase/migrations/20240101000022_security_lint_fixes.sql`

---

### 24. `20240101000023_fix_function_search_path_mutable.sql` (101 lines)
**Purpose:** Fix function search_path warnings (survey/identity/admin)

**Updates:**
- Sets `search_path` for survey/identity/admin functions

**Full path:** `supabase/migrations/20240101000023_fix_function_search_path_mutable.sql`

---

### 25. `20240101000024_rls_policy_consolidation.sql` (100 lines)
**Purpose:** RLS policy consolidation + auth initplan improvements

**Updates:**
- Merges duplicate permissive policies
- Wraps `auth.*` calls for initplan caching

**Full path:** `supabase/migrations/20240101000024_rls_policy_consolidation.sql`

---

### 26. `20240101000025_drop_duplicate_indexes.sql` (9 lines)
**Purpose:** Drop duplicate indexes (safe)

**Updates:**
- Removes redundant indexes on survey and notification tables

**Full path:** `supabase/migrations/20240101000025_drop_duplicate_indexes.sql`

---

### 27. `20240101000026_rls_announcements_email_settings.sql` (14 lines)
**Purpose:** Fix auth initplan warnings + consolidate SELECT policies

**Updates:**
- Improves announcements policy
- Consolidates `email_notifications` and `system_settings` policies

**Full path:** `supabase/migrations/20240101000026_rls_announcements_email_settings.sql`

---

### 28. `20240101000027_fix_sla_function_search_path.sql` (19 lines)
**Purpose:** Fix function search_path warnings for SLA/decision helpers

**Updates:**
- Sets `search_path` for SLA/decision helper functions (guarded)

**Full path:** `supabase/migrations/20240101000027_fix_sla_function_search_path.sql`

---

### 29. `20260103233511_dashboard_consolidation.sql` (129 lines)
**Purpose:** Dashboard data consolidation + realtime support

**Updates:**
- Adds consolidated RPCs for dashboard stats/nav badges

**Full path:** `supabase/migrations/20260103233511_dashboard_consolidation.sql`

---

### 30. `20260103233630_fix_notification_outbox.sql` (70 lines)
**Purpose:** Fix notification outbox + nav badge RPC

**Updates:**
- Adds `read_at` to notification outbox
- Updates nav badge counts

**Full path:** `supabase/migrations/20260103233630_fix_notification_outbox.sql`

---

### 31. `20260103235729_create_kv_table_70ac3e4c.sql` (1 line)
**Purpose:** Create KV store table with RLS

**Creates:**
- `kv_store_70ac3e4c` with JSONB value and RLS enabled

**Full path:** `supabase/migrations/20260103235729_create_kv_table_70ac3e4c.sql`

---

### 32. `20260104000028_critical_audit_fixes.sql` (93 lines)
**Purpose:** Critical audit fixes

**Updates:**
- Soft delete support
- Cascade protections
- Vote tracking + status constraints

**Full path:** `supabase/migrations/20260104000028_critical_audit_fixes.sql`

---

### 33. `20260105000010_survey_abandonment_tracking.sql` (138 lines)
**Purpose:** Survey abandonment tracking + session timeout support

**Updates:**
- Adds lifecycle fields to `survey_responses`
- Adds optional session fields to `hybrid_identity_sessions`
- Backfills/indices with safety guards

**Full path:** `supabase/migrations/20260105000010_survey_abandonment_tracking.sql`

---

### 34–42. Remote-applied placeholder migrations (no local SQL)
These are placeholder files added to align local history with remote migration versions. The original SQL was applied directly on the remote database.

- `20260105030420_remote_applied_placeholder.sql`
- `20260105030438_remote_applied_placeholder.sql`
- `20260105030451_remote_applied_placeholder.sql`
- `20260105030457_remote_applied_placeholder.sql`
- `20260105030524_remote_applied_placeholder.sql`
- `20260105030538_remote_applied_placeholder.sql`
- `20260105030629_remote_applied_placeholder.sql`
- `20260105030709_remote_applied_placeholder.sql`
- `20260105030814_remote_applied_placeholder.sql`

---

## View All Files at Once

```bash
# List all migrations
ls -lh supabase/migrations/*.sql

# View first 20 lines of each
for file in supabase/migrations/*.sql; do
    echo "=== $(basename $file) ==="
    head -20 "$file"
    echo ""
done

# View full content of a specific migration
cat supabase/migrations/20240101000000_initial_schema.sql
```

---

## Apply Migrations

**Via Supabase Dashboard:**
1. Go to https://supabase.com/dashboard/project/ywcfqlyhesnikclesgpr
2. SQL Editor → New Query
3. Copy and paste each migration file in order (00000 → latest)
4. Run each one

**Via CLI:**
```bash
supabase db push
```

---

All migration files are ready and contain the full SQL content for each feature!
