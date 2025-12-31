# Supabase Backend Setup Guide

## Overview

This guide explains how to set up and use the Supabase backend for the Eternity School Evaluation System.

## What is Supabase?

Supabase is an open-source Firebase alternative that provides:
- **PostgreSQL Database**: Full-featured relational database
- **Authentication**: Built-in auth system
- **Real-time**: Real-time subscriptions
- **Storage**: File storage
- **Edge Functions**: Serverless functions
- **Auto-generated APIs**: REST and GraphQL APIs

## Project Configuration

- **Project ID**: `ywcfqlyhesnikclesgpr`
- **Database URL**: `postgresql://postgres:oRyY5M5S5op6ARqi@db.ywcfqlyhesnikclesgpr.supabase.co:5432/postgres`
- **API URL**: `https://ywcfqlyhesnikclesgpr.supabase.co`

## Quick Start

### 1. Install Supabase CLI

```bash
# macOS
brew install supabase/tap/supabase

# Or using npm
npm install -g supabase
```

### 2. Login

```bash
supabase login
```

### 3. Link Project

```bash
cd eternity-school-evaluation
supabase link --project-ref ywcfqlyhesnikclesgpr
```

### 4. Run Setup Script

```bash
cd supabase
./setup.sh
```

Or manually apply migrations:

```bash
supabase db push
```

## Migration Files

### 1. Initial Schema (`20240101000000_initial_schema.sql`)

**Creates:**
- All database tables
- Enums (staff_segment, eom_category, action_type, rotation_period_type)
- Indexes for performance
- Triggers for `updated_at` timestamps

**Tables:**
- `cycles`: Evaluation cycles
- `people`: Staff members
- `assignments`: MRE assignments
- `evaluations`: Evaluation submissions
- `eom_cycles`: EOM cycles
- `eom_voters`: EOM voters
- `eom_nominees`: EOM nominees
- `eom_winners`: EOM winners
- `eom_rotation_rules`: Rotation rules
- `weight_matrices`: Weight matrix configurations
- `audit_logs`: Audit trail

### 2. Views (`20240101000001_create_views.sql`)

**Reporting Views:**
- `mre_who_evaluates_who`: MRE evaluation relationships
- `mre_evaluation_summary`: Evaluation statistics
- `eom_participants`: EOM voters and nominees
- `eom_nomination_summary`: EOM nomination statistics
- `eom_winner_history`: Historical winners
- `weighted_score_summary`: Weighted scores by staff type
- `recent_audit_logs`: Recent audit entries

### 3. Functions (`20240101000002_create_functions.sql`)

**Database Functions:**
- `calculate_weighted_score(cycle_id, target_email)`: Calculate weighted scores
- `get_cycle_statistics(cycle_id)`: Get cycle statistics
- `check_eom_eligibility(nominee_email, eom_cycle_id, category)`: Check EOM eligibility
- `get_eom_cycle_stats(eom_cycle_id)`: Get EOM cycle statistics
- `validate_evaluation_requirements(cycle_id, target_email, min_evaluations)`: Validate requirements
- `get_staff_count_by_segment()`: Get staff counts
- `get_cycle_completion_status(cycle_id)`: Get completion status

### 4. Row Level Security (`20240101000003_row_level_security.sql`)

**RLS Policies:**
- Read access for authenticated users
- Write access for service role only
- User-specific access for evaluations

## Using Database Functions

### Calculate Weighted Score

```sql
SELECT * FROM calculate_weighted_score(1, 'teacher1@eternity.edu');
```

**Returns:**
- `target_email`: Staff member email
- `total_evaluations`: Number of evaluations
- `raw_average`: Average raw score
- `weighted_average`: Weighted average score
- `weighted_sum`: Sum of weighted scores
- `total_weight`: Total weight

### Get Cycle Statistics

```sql
SELECT * FROM get_cycle_statistics(1);
```

**Returns:**
- `total_assignments`: Total assignments
- `total_evaluations`: Total evaluations
- `submitted_evaluations`: Submitted evaluations
- `average_rating`: Average rating
- `average_weighted_rating`: Average weighted rating
- `completion_rate`: Completion percentage

### Check EOM Eligibility

```sql
SELECT * FROM check_eom_eligibility(
    'teacher1@eternity.edu',
    1,
    'academic'
);
```

**Returns:**
- `is_eligible`: Boolean eligibility status
- `reason`: Explanation of eligibility

## Using Views

### MRE Who Evaluates Who

```sql
SELECT * FROM mre_who_evaluates_who 
WHERE cycle_code = 'CYCLE-2024-Q1';
```

### EOM Participants

```sql
SELECT * FROM eom_participants 
WHERE eom_code LIKE '2024%';
```

### Weighted Score Summary

```sql
SELECT * FROM weighted_score_summary 
WHERE cycle_code = 'CYCLE-2024-Q1' 
  AND staff_type = 'academic';
```

## Row Level Security

RLS is enabled by default. Policies allow:
- **Authenticated users**: Read access to most tables
- **Service role**: Full access to all tables
- **Users**: Can create/update their own evaluations

### Disable RLS (Development Only)

```sql
ALTER TABLE table_name DISABLE ROW LEVEL SECURITY;
```

### Re-enable RLS

```sql
ALTER TABLE table_name ENABLE ROW LEVEL SECURITY;
```

## Supabase Studio

Access the web-based database management interface:

```bash
supabase studio
```

Or visit: https://supabase.com/dashboard/project/ywcfqlyhesnikclesgpr

**Features:**
- Table Editor: View and edit data
- SQL Editor: Run SQL queries
- API Docs: View auto-generated API documentation
- Database: View schema and relationships
- Logs: View database logs

## Auto-generated APIs

Supabase automatically generates REST and GraphQL APIs:

### REST API

**Base URL**: `https://ywcfqlyhesnikclesgpr.supabase.co/rest/v1/`

**Example:**
```bash
# Get all people
curl -X GET \
  'https://ywcfqlyhesnikclesgpr.supabase.co/rest/v1/people?select=*' \
  -H "apikey: YOUR_ANON_KEY" \
  -H "Authorization: Bearer YOUR_ANON_KEY"
```

### GraphQL API

**Base URL**: `https://ywcfqlyhesnikclesgpr.supabase.co/graphql/v1`

**Example:**
```graphql
query {
  people {
    email
    full_name
    segment
  }
}
```

## Authentication (Optional)

If you want to use Supabase Auth:

1. **Enable Auth in Dashboard**
   - Go to Authentication → Settings
   - Enable email provider
   - Configure OAuth providers if needed

2. **Use in Frontend**
   ```javascript
   import { createClient } from '@supabase/supabase-js'
   
   const supabase = createClient(
     'https://ywcfqlyhesnikclesgpr.supabase.co',
     'YOUR_ANON_KEY'
   )
   
   // Sign up
   const { data, error } = await supabase.auth.signUp({
     email: 'user@example.com',
     password: 'password'
   })
   ```

## Storage (Optional)

If you need file storage:

```bash
# Create storage bucket
supabase storage create evaluations

# Upload file
supabase storage upload evaluations file.pdf
```

## Edge Functions (Optional)

Create serverless functions:

```bash
# Create function
supabase functions new process-evaluation

# Deploy function
supabase functions deploy process-evaluation
```

## Backup and Restore

### Backup

```bash
# Dump database
supabase db dump -f backup.sql

# Or using pg_dump
pg_dump -h db.ywcfqlyhesnikclesgpr.supabase.co \
        -U postgres \
        -d postgres \
        > backup.sql
```

### Restore

```bash
# Reset and restore
supabase db reset
psql -h db.ywcfqlyhesnikclesgpr.supabase.co \
     -U postgres \
     -d postgres \
     < backup.sql
```

## Monitoring

### Database Logs

View logs in Supabase Dashboard:
- Go to Logs → Database
- Filter by query type, duration, etc.

### Performance

Monitor query performance:
- Use `EXPLAIN ANALYZE` for slow queries
- Check indexes are being used
- Review query plans

## Troubleshooting

### Connection Issues

1. **Check `.env` file**
   ```env
   DATABASE_URL=postgresql://postgres:password@db.ywcfqlyhesnikclesgpr.supabase.co:5432/postgres
   ```

2. **Verify project is active**
   - Check Supabase Dashboard
   - Ensure project is not paused

3. **Check network/firewall**
   - Ensure port 5432 is accessible
   - Check IP allowlist if configured

### Migration Issues

```bash
# Check migration status
supabase migration list

# View migration history
supabase db diff

# Create new migration
supabase migration new migration_name
```

### RLS Blocking Access

If RLS is blocking legitimate access:

1. **Check policies**
   ```sql
   SELECT * FROM pg_policies WHERE tablename = 'table_name';
   ```

2. **Temporarily disable** (development only)
   ```sql
   ALTER TABLE table_name DISABLE ROW LEVEL SECURITY;
   ```

3. **Fix policies**
   ```sql
   -- Update policy
   DROP POLICY policy_name ON table_name;
   CREATE POLICY policy_name ON table_name ...;
   ```

## Best Practices

1. **Always use migrations** for schema changes
2. **Test migrations** on a branch database first
3. **Backup before** major changes
4. **Use transactions** for data migrations
5. **Monitor performance** regularly
6. **Keep RLS enabled** in production
7. **Use indexes** for frequently queried columns
8. **Document** custom functions and views

## Resources

- [Supabase Documentation](https://supabase.com/docs)
- [Supabase CLI Reference](https://supabase.com/docs/reference/cli)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Row Level Security Guide](https://supabase.com/docs/guides/auth/row-level-security)

