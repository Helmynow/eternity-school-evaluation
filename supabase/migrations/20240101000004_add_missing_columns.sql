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

-- ============================================================================
-- CREATE INDEXES IF THEY DON'T EXIST
-- ============================================================================

-- Create indexes only if they don't exist
CREATE INDEX IF NOT EXISTS idx_person_segment ON people(segment);
CREATE INDEX IF NOT EXISTS idx_person_active ON people(active);
CREATE INDEX IF NOT EXISTS idx_person_department ON people(department);

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

