# Migration Files Location

## 📁 Location

All database migration files are located in:

```
supabase/migrations/
```

## 📋 Migration Files (19 total)

1. `20240101000000_initial_schema.sql` - Base schema (tables, enums, indexes)
2. `20240101000001_add_missing_columns.sql` - Additional columns
3. `20240101000002_create_views.sql` - Database views
4. `20240101000003_create_functions.sql` - Database functions
5. `.sql` - RLS policies
6. `20240101000005_fix_security_issues.sql` - Security fixes
7. `20240101000006_fix_function_search_path.sql` - Function search path fixes
8. `20240101000007_optimize_rls_performance.sql` - RLS performance optimization
9. `20240101000008_fix_multiple_permissive_policies.sql` - Policy fixes
10. `20240101000009_fix_security_definer_views_and_rls.sql` - Security definer fixes
11. `20240101000010_explicitly_set_security_invoker_on_views.sql` - View security
12. `20240101000011_fix_function_search_path_security.sql` - Function security
13. `20240101000012_add_new_features.sql` - Announcements, Notifications
14. `20240101000013_fix_eom_categories_and_add_features.sql` - EOM features
15. `20240101000014_survey_identity_system.sql` - Survey system
16. `20240101000015_conditional_anonymity_engine.sql` - Anonymity engine
17. `20240101000016_add_missing_models.sql` - Additional models
18. `20240101000017_add_survey_functions.sql` - Survey functions
19. `20240101000018_rbac_user_permissions.sql` - RBAC system

## 🚀 How to Apply Migrations

### Option 1: Via Supabase Dashboard (Recommended)

1. Go to https://supabase.com/dashboard/project/ywcfqlyhesnikclesgpr
2. Navigate to **SQL Editor**
3. Click **New Query**
4. Copy and paste the contents of each migration file
5. Run them in order (00000 → 00018)
6. Verify each completes successfully

### Option 2: Via Supabase CLI

```bash
# From project root
cd /Users/helmy/Desktop/team/eternity-school-evaluation

# Link project (if not already linked)
supabase link --project-ref ywcfqlyhesnikclesgpr

# Push all migrations
supabase db push
```

### Option 3: Individual Migration

```bash
# Apply a specific migration
supabase migration up <migration_name>
```

## 📍 Full Path

```
/Users/helmy/Desktop/team/eternity-school-evaluation/supabase/migrations/
```

## ⚠️ Important Notes

- Migrations must be run in order (by timestamp)
- Some migrations (00005-00018) need to be applied
- Migration 00007 has some SQL syntax that may need manual fixes
- Recommended: Use Supabase Dashboard for more control

## 🔍 Check Migration Status

```bash
# List migration status
supabase migration list

# Check which migrations are applied
supabase db diff
```
