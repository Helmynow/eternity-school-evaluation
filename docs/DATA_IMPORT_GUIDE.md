# Data Import Guide

This guide explains how to import data from the Excel files into the EVALVision system.

## Excel Files Structure

### 1. ESE_program_overview.xlsx

This is the main file containing all program data:

#### Sheet: Staff_Database
- **Purpose**: Complete staff database
- **Columns**: Staff ID, Segment, Name, Emails, Title
- **Rows**: ~200 staff members
- **Import**: Use "Staff Database" import type

#### Sheet: EOM_candidates
- **Purpose**: All eligible EOM candidates
- **Columns**: Staff ID, Segment, Name, Emails, Title, Sub Title, Sub Department
- **Rows**: ~185 candidates
- **Import**: Use "EOM Candidates" import type

#### Sheet: EOM_ Nominators-Voters
- **Purpose**: List of people who can nominate and vote for EOM
- **Columns**: Staff ID, Segment, Name, Emails, Title
- **Rows**: ~17 voters/nominators
- **Import**: Use "EOM Voters" import type

#### Sheet: Weight_Matrix
- **Purpose**: Defines who evaluates who in MRE evaluations
- **Columns**: 
  - `target_group`: academic, admin, support
  - `evaluator_email`: Email of the evaluator
  - `rater_context`: ceo, pc, qa, manager, principal, etc.
  - `weight`: Weight value (0.0-1.0)
  - `required`: Boolean (required evaluator)
  - `min_count`: Minimum number of evaluations needed
  - `max_count`: Maximum number of evaluations allowed
- **Import**: Use "Weight Matrix" import type

#### Sheet: Domain_Weights_Admin
- **Purpose**: Domain-specific weights for admin staff evaluations
- **Columns**: target_group, rater_context, domain_code, domain_label, domain_weight
- **Note**: This is used to configure evaluation domains and their weights

#### Sheet: Domain_Weights_Academic
- **Purpose**: Domain-specific weights for academic staff evaluations
- **Columns**: target_group, rater_context, domain_code, domain_label, domain_weight
- **Note**: This is used to configure evaluation domains and their weights

#### Sheet: EOM_Categories
- **Purpose**: List of EOM categories
- **Note**: Categories are already defined in the database enum

#### Sheet: Program_Rules
- **Purpose**: Program rules and requirements
- **Note**: These are configured in the Settings page

### 2. EOM nom.xlsx

- **Purpose**: EOM candidates list (same as EOM_candidates sheet)
- **Columns**: Staff ID, Segment, Name, Emails, Title, Sub Title, Sub Department
- **Rows**: 185 candidates
- **Import**: Use "EOM Candidates" import type

### 3. EOM voters.xlsx

- **Purpose**: EOM voters list
- **Columns**: Staff ID, Segment, Name, Emails, Title
- **Rows**: 13 voters
- **Import**: Use "EOM Voters" import type

## Import Process

### Step 1: Import Staff Database

1. Go to `/admin/import`
2. Select "Staff Database" as import type
3. Upload `ESE_program_overview.xlsx`
4. Click "Import Data"
5. This will import/update all 200 staff members

### Step 2: Create a Cycle

1. Go to `/admin/cycles`
2. Create a new cycle (e.g., "Q1 2025")
3. Note the Cycle ID

### Step 3: Import Weight Matrix

1. Go to `/admin/import`
2. Select "Weight Matrix" as import type
3. Enter the Cycle ID from Step 2
4. Upload `ESE_program_overview.xlsx`
5. Click "Import Data"
6. This creates the evaluation structure (who evaluates who)

### Step 4: Import EOM Voters

1. Go to `/admin/import`
2. Select "EOM Voters" as import type
3. Enter Cycle ID, Month, and Year
4. Upload `EOM voters.xlsx` or use `ESE_program_overview.xlsx` (EOM_ Nominators-Voters sheet)
5. Click "Import Data"

### Step 5: Import EOM Candidates (Optional)

1. Go to `/admin/import`
2. Select "EOM Candidates" as import type
3. Upload `EOM nom.xlsx` or `ESE_program_overview.xlsx` (EOM_candidates sheet)
4. Click "Import Data"
5. This provides a list of eligible candidates (they still need to be nominated)

## Data Mapping

### Segment Mapping
- "National" → `national`
- "International" → `international`
- "Whole School" → `whole_school`

### EOM Code Format
EOM cycles use the format: `{CYCLE_CODE}-EOM-{MM}-{YYYY}`
- Example: `Q1-2025-EOM-01-2025`

### Weight Matrix Structure
The weight matrix is stored as JSON:
```json
{
  "academic": {
    "ceo": {
      "ahemy@eternityschoolegypt.com": {
        "weight": 1.0,
        "required": false,
        "min_count": 1,
        "max_count": 1
      }
    }
  }
}
```

## Views Available

After importing, you can query these views:

1. **mre_who_evaluates_who**: Shows all evaluation assignments
2. **eom_participants**: Shows all EOM voters and nominees
3. **eom_nomination_summary**: Summary of nominations by category
4. **eom_winner_history**: Historical EOM winners

## Troubleshooting

### Common Issues

1. **Email not found**: Ensure staff are imported before importing EOM voters/candidates
2. **Cycle not found**: Create the cycle first before importing cycle-specific data
3. **Duplicate entries**: The import handles duplicates by updating existing records
4. **Missing columns**: Check that your Excel file matches the expected format

### Validation

After importing, verify:
- Staff count matches expected (~200)
- EOM voters are assigned to the correct cycle
- Weight matrix is properly structured
- All emails are valid and exist in the people table
