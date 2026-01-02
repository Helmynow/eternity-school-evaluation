# Migration Review: EOM Categories and Features

## Migration File
`supabase/migrations/20240101000013_fix_eom_categories_and_add_features.sql`

## Data Mapping Review

### EOM Category Mapping

The migration maps old categories to new categories as follows:

**Old Categories → New Categories:**
- `leadership` → `outstanding_leadership`
- `academic` → `outstanding_leadership`
- `admin` → `outstanding_leadership`
- `innovation` → `innovation` (unchanged)
- `support` → **Needs manual review** (not mapped)
- `collaboration` → **Needs manual review** (not mapped)
- `student_engagement` → **Needs manual review** (not mapped)

### ⚠️ Action Required

**Before running the migration**, review your existing data and update the mapping in the migration file:

1. **Check existing EOM data:**
   ```sql
   SELECT DISTINCT category, COUNT(*) 
   FROM eom_nominees 
   GROUP BY category;
   ```

2. **Update mapping for unmapped categories:**
   - `support` → Could map to `service_excellence` or `team_spirit`
   - `collaboration` → Could map to `team_spirit`
   - `student_engagement` → Could map to `innovation` or `service_excellence`

3. **Review and adjust the UPDATE statements** in the migration file before running.

### Recommended Mapping

```sql
-- Suggested additional mappings (add to migration):
UPDATE eom_nominees SET category = 'service_excellence'::text 
WHERE category::text = 'support';

UPDATE eom_nominees SET category = 'team_spirit'::text 
WHERE category::text = 'collaboration';

UPDATE eom_nominees SET category = 'innovation'::text 
WHERE category::text = 'student_engagement';
```

## New Features Added

### 1. Nomination Window
- Columns: `nomination_window_start_day`, `nomination_window_duration_days`, `announcement_date`
- Default: Opens on 15th of month, 7-day window

### 2. Weighted Voting
- Column: `vote_weight` in `eom_voters`
- Auto-set based on role (Principal: 0.40, Manager: 0.30, CEO: 0.30)

### 3. Variance Alerts
- Columns: `variance_flag`, `variance_alert_sent` in `evaluations`
- Automatic flagging for ≥2pt spread

### 4. Diversity Tracking
- View: `eom_diversity_tracking`
- Tracks recognition by segment, department, role

### 5. Hall of Fame
- View: `eom_hall_of_fame`
- Complete winners history

### 6. Feedback Collection
- Table: `eom_feedback`
- Collects post-cycle feedback

### 7. Email Notifications
- Table: `email_notifications`
- Tracks all sent notifications

## Running the Migration

```bash
cd /Users/helmy/Desktop/team/eternity-school-evaluation
supabase db push
```

**Note:** Review the category mapping above before running!
