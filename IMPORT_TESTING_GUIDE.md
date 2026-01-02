# Import Testing Guide

## ✅ Migration Applied

The database migration `20240101000012_add_new_features.sql` has been successfully applied. This migration adds:
- `objections` table for EOM nomination disputes
- `announcements` table for system-wide announcements
- `notifications` table for user notifications
- `surveys`, `survey_questions`, `survey_responses` tables
- `feedback` table for user feedback
- `ai_feedback` table for AI-generated insights
- Approval workflow fields on `eom_nominees` and `evaluations` tables

## 🚀 Servers Status

- ✅ **Frontend**: Running on http://localhost:3000
- ✅ **Backend**: Running on http://localhost:8000
- ✅ **Dependencies**: pandas and openpyxl installed

## 📋 Testing the Import Functionality

### Step 1: Access the Import Page

1. Open your browser and navigate to: **http://localhost:3000/admin/import**
2. You should see the Bulk Import interface with options for:
   - Staff Database
   - EOM Voters
   - EOM Candidates
   - Weight Matrix

### Step 2: Import Staff Database

1. Select **"Staff Database"** from the dropdown
2. Click **"Choose File"** and select: `/Users/helmy/Desktop/team/ESE_program_overview.xlsx`
3. Click **"Import Data"**
4. Expected result: ~200 staff members imported/updated

**Expected File Format:**
- Sheet name: `Staff_Database`
- Columns: `Staff ID`, `Segment`, `Name`, `Emails`, `Title`

### Step 3: Create a Cycle (Required for EOM Voters and Weight Matrix)

1. Navigate to: **http://localhost:3000/admin/cycles**
2. Create a new cycle (e.g., "Q1 2025")
2. Note the **Cycle ID** (you'll need it for the next steps)

### Step 4: Import EOM Voters

1. Go back to **http://localhost:3000/admin/import**
2. Select **"EOM Voters"** from the dropdown
3. Enter:
   - **Cycle ID**: (from Step 3)
   - **Month**: 1 (or current month)
   - **Year**: 2025 (or current year)
4. Upload: `/Users/helmy/Desktop/team/EOM voters.xlsx` or use `ESE_program_overview.xlsx` (sheet: `EOM_ Nominators-Voters`)
5. Click **"Import Data"**
6. Expected result: ~13-17 voters imported

**Expected File Format:**
- Sheet name: `Sheet1` or `EOM_ Nominators-Voters`
- Columns: `Staff ID`, `Segment`, `Name`, `Emails`, `Title`

### Step 5: Import EOM Candidates

1. Select **"EOM Candidates"** from the dropdown
2. Upload: `/Users/helmy/Desktop/team/EOM nom.xlsx` or `ESE_program_overview.xlsx` (sheet: `EOM_candidates`)
3. Click **"Import Data"**
4. Expected result: ~185 candidates listed (this doesn't create nominations, just lists eligible candidates)

**Expected File Format:**
- Sheet name: `EOM_candidates` or `Sheet1`
- Columns: `Staff ID`, `Segment`, `Name`, `Emails`, `Title`, `Sub Title`, `Sub Department`

### Step 6: Import Weight Matrix

1. Select **"Weight Matrix"** from the dropdown
2. Enter **Cycle ID**: (from Step 3)
3. Upload: `/Users/helmy/Desktop/team/ESE_program_overview.xlsx`
4. Click **"Import Data"**
5. Expected result: Weight matrix configuration stored

**Expected File Format:**
- Sheet name: `Weight_Matrix`
- Columns: `target_group`, `evaluator_email`, `rater_context`, `weight`, `required`, `min_count`, `max_count`

## ✅ Verification Steps

### Verify Staff Import

1. Navigate to: **http://localhost:3000/admin/staff**
2. You should see ~200 staff members
3. Check that segments are correctly mapped:
   - "National" → `national`
   - "International" → `international`
   - "Whole School" → `whole_school`

### Verify EOM Voters

1. Navigate to: **http://localhost:3000/eom/vote**
2. Check that voters can see the voting interface
3. Or query the database:
   ```sql
   SELECT * FROM eom_voters WHERE eom_cycle_id = <your_cycle_id>;
   ```

### Verify Weight Matrix

1. Query the database:
   ```sql
   SELECT id, cycle_id, matrix_config FROM weight_matrices WHERE cycle_id = <your_cycle_id>;
   ```
2. The `matrix_config` should be a JSON object with the structure:
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

## 🐛 Troubleshooting

### Import Fails with "No email column found"

- Check that your Excel file has a column named `Emails` (case-sensitive)
- The import looks for columns containing "email" or "emails" (case-insensitive)

### Import Fails with "Cycle not found"

- Make sure you've created a cycle first in `/admin/cycles`
- Use the correct Cycle ID in the import form

### Import Fails with "Could not find sheet"

- For `ESE_program_overview.xlsx`, make sure you're using the correct sheet name:
  - Staff: `Staff_Database`
  - EOM Voters: `EOM_ Nominators-Voters`
  - EOM Candidates: `EOM_candidates`
  - Weight Matrix: `Weight_Matrix`

### Backend Not Responding

1. Check if backend is running:
   ```bash
   lsof -ti:8000
   ```
2. Restart backend:
   ```bash
   cd eternity-school-evaluation
   source venv/bin/activate
   uvicorn backend.fastapi_app:app --host 0.0.0.0 --port 8000 --reload
   ```

### Frontend Not Loading

1. Check if frontend is running:
   ```bash
   lsof -ti:3000
   ```
2. Restart frontend:
   ```bash
   cd eternity-school-evaluation/frontend
   npm run dev
   ```

## 📊 Expected Results

After successful imports:
- **Staff**: ~200 records in `people` table
- **EOM Voters**: ~13-17 records in `eom_voters` table
- **EOM Candidates**: List of ~185 eligible candidates (not stored in DB, just returned)
- **Weight Matrix**: 1 record in `weight_matrices` table with JSON configuration

## 🔗 Related Documentation

- See `docs/DATA_IMPORT_GUIDE.md` for detailed file format specifications
- See `docs/DATABASE_MODELS.md` for database schema details
