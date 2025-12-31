-- Add missing columns to existing tables
-- This migration handles the case where tables exist but are missing new columns

-- ============================================================================
-- ADD MISSING COLUMNS TO PEOPLE TABLE
-- ============================================================================

-- Add segment column if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'people' AND column_name = 'segment'
    ) THEN
        ALTER TABLE people ADD COLUMN segment staff_segment NOT NULL DEFAULT 'whole_school';
    END IF;
END $$;

-- Add created_at if missing
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'people' AND column_name = 'created_at'
    ) THEN
        ALTER TABLE people ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
    END IF;
END $$;

-- Add updated_at if missing
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'people' AND column_name = 'updated_at'
    ) THEN
        ALTER TABLE people ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
    END IF;
END $$;

-- Add active column if missing
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'people' AND column_name = 'active'
    ) THEN
        ALTER TABLE people ADD COLUMN active BOOLEAN DEFAULT TRUE;
    END IF;
END $$;

-- Add department column if missing
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'people' AND column_name = 'department'
    ) THEN
        ALTER TABLE people ADD COLUMN department VARCHAR(100);
    END IF;
END $$;

-- Add role_title column if missing
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'people' AND column_name = 'role_title'
    ) THEN
        ALTER TABLE people ADD COLUMN role_title VARCHAR(100);
    END IF;
END $$;

-- Add hire_date column if missing
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'people' AND column_name = 'hire_date'
    ) THEN
        ALTER TABLE people ADD COLUMN hire_date DATE;
    END IF;
END $$;

-- ============================================================================
-- CREATE INDEXES IF THEY DON'T EXIST (only if columns exist)
-- ============================================================================

-- Create indexes only if columns exist
DO $$ 
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'people' AND column_name = 'segment'
    ) THEN
        CREATE INDEX IF NOT EXISTS idx_person_segment ON people(segment);
    END IF;
    
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'people' AND column_name = 'active'
    ) THEN
        CREATE INDEX IF NOT EXISTS idx_person_active ON people(active);
    END IF;
    
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'people' AND column_name = 'department'
    ) THEN
        CREATE INDEX IF NOT EXISTS idx_person_department ON people(department);
    END IF;
END $$;

-- ============================================================================
-- ADD MISSING COLUMNS TO OTHER TABLES
-- ============================================================================

-- Cycles table
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'cycles' AND column_name = 'created_at'
    ) THEN
        ALTER TABLE cycles ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'cycles' AND column_name = 'updated_at'
    ) THEN
        ALTER TABLE cycles ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
    END IF;
END $$;

-- Assignments table
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'assignments' AND column_name = 'weight_matrix_id'
    ) THEN
        ALTER TABLE assignments ADD COLUMN weight_matrix_id INTEGER;
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'assignments' AND column_name = 'created_at'
    ) THEN
        ALTER TABLE assignments ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'assignments' AND column_name = 'updated_at'
    ) THEN
        ALTER TABLE assignments ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
    END IF;
END $$;

-- Evaluations table
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'evaluations' AND column_name = 'weighted_rating'
    ) THEN
        ALTER TABLE evaluations ADD COLUMN weighted_rating FLOAT;
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'evaluations' AND column_name = 'domain_scores'
    ) THEN
        ALTER TABLE evaluations ADD COLUMN domain_scores JSONB;
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'evaluations' AND column_name = 'created_at'
    ) THEN
        ALTER TABLE evaluations ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'evaluations' AND column_name = 'updated_at'
    ) THEN
        ALTER TABLE evaluations ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
    END IF;
END $$;

-- EOM Nominees table - add missing columns
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'eom_nominees' AND column_name = 'category'
    ) THEN
        ALTER TABLE eom_nominees ADD COLUMN category eom_category;
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'eom_nominees' AND column_name = 'rotation_eligible'
    ) THEN
        ALTER TABLE eom_nominees ADD COLUMN rotation_eligible BOOLEAN DEFAULT TRUE;
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'eom_nominees' AND column_name = 'last_nominated_cycle_id'
    ) THEN
        ALTER TABLE eom_nominees ADD COLUMN last_nominated_cycle_id INTEGER;
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'eom_nominees' AND column_name = 'last_won_cycle_id'
    ) THEN
        ALTER TABLE eom_nominees ADD COLUMN last_won_cycle_id INTEGER;
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'eom_nominees' AND column_name = 'nomination_count'
    ) THEN
        ALTER TABLE eom_nominees ADD COLUMN nomination_count INTEGER DEFAULT 0;
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'eom_nominees' AND column_name = 'win_count'
    ) THEN
        ALTER TABLE eom_nominees ADD COLUMN win_count INTEGER DEFAULT 0;
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'eom_nominees' AND column_name = 'votes_received'
    ) THEN
        ALTER TABLE eom_nominees ADD COLUMN votes_received INTEGER DEFAULT 0;
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'eom_nominees' AND column_name = 'created_at'
    ) THEN
        ALTER TABLE eom_nominees ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'eom_nominees' AND column_name = 'updated_at'
    ) THEN
        ALTER TABLE eom_nominees ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
    END IF;
END $$;

-- EOM Cycles table
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'eom_cycles' AND column_name = 'category_rotation'
    ) THEN
        ALTER TABLE eom_cycles ADD COLUMN category_rotation JSONB;
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'eom_cycles' AND column_name = 'created_at'
    ) THEN
        ALTER TABLE eom_cycles ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'eom_cycles' AND column_name = 'updated_at'
    ) THEN
        ALTER TABLE eom_cycles ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
    END IF;
END $$;

-- Weight Matrices table
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'weight_matrices' AND column_name = 'created_at'
    ) THEN
        ALTER TABLE weight_matrices ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'weight_matrices' AND column_name = 'updated_at'
    ) THEN
        ALTER TABLE weight_matrices ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
    END IF;
END $$;

-- EOM Rotation Rules table
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'eom_rotation_rules' AND column_name = 'max_nominations_per_year'
    ) THEN
        ALTER TABLE eom_rotation_rules ADD COLUMN max_nominations_per_year INTEGER DEFAULT 2;
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'eom_rotation_rules' AND column_name = 'created_at'
    ) THEN
        ALTER TABLE eom_rotation_rules ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'eom_rotation_rules' AND column_name = 'updated_at'
    ) THEN
        ALTER TABLE eom_rotation_rules ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
    END IF;
END $$;

-- ============================================================================
-- CREATE ALL INDEXES (after columns are added)
-- ============================================================================

-- EOM Nominees indexes
CREATE INDEX IF NOT EXISTS idx_eom_nominee_category ON eom_nominees(category) WHERE category IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_eom_nominee_rotation ON eom_nominees(rotation_eligible);

