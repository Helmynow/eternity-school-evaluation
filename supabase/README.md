# Supabase Backend Setup

This directory contains the Supabase backend configuration, migrations, and functions for the Eternity School Evaluation System.

## Structure

```
supabase/
├── migrations/          # Database migration files
│   ├── 20240101000000_initial_schema.sql
│   ├── 20240101000001_create_views.sql
│   ├── 20240101000002_create_functions.sql
│   └── 20240101000003_row_level_security.sql
├── config.toml          # Supabase project configuration
└── README.md           # This file
```

## Setup Instructions

### 1. Install Supabase CLI

```bash
# macOS
brew install supabase/tap/supabase

# Or using npm
npm install -g supabase
```

### 2. Login to Supabase

```bash
supabase login
```

### 3. Link to Your Project

```bash
cd eternity-school-evaluation
supabase link --project-ref ywcfqlyhesnikclesgpr
```

### 4. Run Migrations

```bash
# Apply all migrations
supabase db push

# Or apply specific migration
supabase migration up
```

### 5. Verify Setup

```bash
# Check database connection
supabase db status

# Open Supabase Studio
supabase studio
```

## Migration Files

### 1. Initial Schema (`20240101000000_initial_schema.sql`)

Creates:
- All database tables (cycles, people, assignments, evaluations, etc.)
- Enums (staff_segment, eom_category, action_type, etc.)
- Indexes for performance
- Triggers for `updated_at` timestamps

### 2. Views (`20240101000001_create_views.sql`)

Creates reporting views:
- `mre_who_evaluates_who`: MRE evaluation relationships
- `mre_evaluation_summary`: Evaluation statistics by target
- `eom_participants`: EOM voters and nominees
- `eom_nomination_summary`: EOM nomination statistics
- `eom_winner_history`: Historical EOM winners
- `weighted_score_summary`: Weighted scoring by staff type
- `recent_audit_logs`: Recent audit trail entries

### 3. Functions (`20240101000002_create_functions.sql`)

Creates database functions:
- `calculate_weighted_score()`: Calculate weighted scores
- `get_cycle_statistics()`: Get cycle statistics
- `check_eom_eligibility()`: Check EOM nomination eligibility
- `get_eom_cycle_stats()`: Get EOM cycle statistics
- `validate_evaluation_requirements()`: Validate evaluation requirements
- `get_staff_count_by_segment()`: Get staff counts by segment
- `get_cycle_completion_status()`: Get cycle completion status

### 4. Row Level Security (`20240101000003_row_level_security.sql`)

Sets up RLS policies:
- Read access for authenticated users
- Write access for service role only
- User-specific access for evaluations

## Database Connection

The connection string is configured in `.env`:

```env
DATABASE_URL=postgresql://postgres:oRyY5M5S5op6ARqi@db.ywcfqlyhesnikclesgpr.supabase.co:5432/postgres
```

## Using Supabase Features

### 1. Database Functions

```sql
-- Calculate weighted score
SELECT * FROM calculate_weighted_score(1, 'teacher1@eternity.edu');

-- Get cycle statistics
SELECT * FROM get_cycle_statistics(1);

-- Check EOM eligibility
SELECT * FROM check_eom_eligibility('teacher1@eternity.edu', 1, 'academic');
```

### 2. Views

```sql
-- View MRE relationships
SELECT * FROM mre_who_evaluates_who WHERE cycle_code = 'CYCLE-2024-Q1';

-- View EOM participants
SELECT * FROM eom_participants WHERE eom_code LIKE '2024%';

-- View weighted scores
SELECT * FROM weighted_score_summary WHERE cycle_code = 'CYCLE-2024-Q1';
```

### 3. Row Level Security

RLS is enabled by default. To disable for development:

```sql
ALTER TABLE table_name DISABLE ROW LEVEL SECURITY;
```

## Supabase Studio

Access the Supabase Studio dashboard:

```bash
supabase studio
```

Or visit: https://supabase.com/dashboard/project/ywcfqlyhesnikclesgpr

## API Endpoints

Supabase automatically generates REST and GraphQL APIs:

- **REST API**: `https://ywcfqlyhesnikclesgpr.supabase.co/rest/v1/`
- **GraphQL API**: `https://ywcfqlyhesnikclesgpr.supabase.co/graphql/v1`

## Authentication

Supabase Auth is configured. To use authentication:

1. Enable authentication in Supabase Dashboard
2. Configure providers (Email, OAuth, etc.)
3. Use Supabase client libraries in frontend

## Storage (Optional)

If you need file storage:

```bash
# Create storage bucket
supabase storage create evaluations

# Set policies
supabase storage policy create evaluations-public-read
```

## Edge Functions (Optional)

Create serverless functions:

```bash
# Create new function
supabase functions new process-evaluation

# Deploy function
supabase functions deploy process-evaluation
```

## Backup and Restore

```bash
# Backup database
supabase db dump -f backup.sql

# Restore database
supabase db reset
psql -h db.ywcfqlyhesnikclesgpr.supabase.co -U postgres -d postgres < backup.sql
```

## Troubleshooting

### Connection Issues

1. Check `.env` file has correct `DATABASE_URL`
2. Verify Supabase project is active
3. Check firewall/network settings

### Migration Issues

```bash
# Check migration status
supabase migration list

# Reset database (WARNING: Deletes all data)
supabase db reset

# Create new migration
supabase migration new migration_name
```

### RLS Issues

If RLS is blocking access:

```sql
-- Temporarily disable RLS for testing
ALTER TABLE table_name DISABLE ROW LEVEL SECURITY;

-- Re-enable RLS
ALTER TABLE table_name ENABLE ROW LEVEL SECURITY;
```

## Next Steps

1. **Run Migrations**: Apply all migrations to create the schema
2. **Seed Data**: Add initial data (optional)
3. **Configure Auth**: Set up authentication if needed
4. **Test Functions**: Verify database functions work
5. **Monitor**: Use Supabase Dashboard to monitor usage

## Resources

- [Supabase Documentation](https://supabase.com/docs)
- [Supabase CLI Reference](https://supabase.com/docs/reference/cli)
- [PostgreSQL Functions](https://www.postgresql.org/docs/current/sql-createfunction.html)
- [Row Level Security](https://www.postgresql.org/docs/current/ddl-rowsecurity.html)

