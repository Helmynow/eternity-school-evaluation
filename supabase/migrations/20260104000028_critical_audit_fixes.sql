-- Critical audit fixes: soft deletes, cascade protections, vote tracking, status constraints

-- --------------------------------------------------------------------------
-- Soft delete support
-- --------------------------------------------------------------------------
ALTER TABLE cycles ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP NULL;
ALTER TABLE cycles ADD COLUMN IF NOT EXISTS deleted_by VARCHAR(255) REFERENCES people(email) ON DELETE SET NULL;

ALTER TABLE people ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP NULL;
ALTER TABLE people ADD COLUMN IF NOT EXISTS deleted_by VARCHAR(255) REFERENCES people(email) ON DELETE SET NULL;

ALTER TABLE assignments ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP NULL;
ALTER TABLE assignments ADD COLUMN IF NOT EXISTS deleted_by VARCHAR(255) REFERENCES people(email) ON DELETE SET NULL;

ALTER TABLE evaluations ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP NULL;
ALTER TABLE evaluations ADD COLUMN IF NOT EXISTS deleted_by VARCHAR(255) REFERENCES people(email) ON DELETE SET NULL;

ALTER TABLE eom_cycles ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP NULL;
ALTER TABLE eom_cycles ADD COLUMN IF NOT EXISTS deleted_by VARCHAR(255) REFERENCES people(email) ON DELETE SET NULL;

ALTER TABLE eom_nominees ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP NULL;
ALTER TABLE eom_nominees ADD COLUMN IF NOT EXISTS deleted_by VARCHAR(255) REFERENCES people(email) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_cycles_deleted_at ON cycles(deleted_at);
CREATE INDEX IF NOT EXISTS idx_people_deleted_at ON people(deleted_at);
CREATE INDEX IF NOT EXISTS idx_assignments_deleted_at ON assignments(deleted_at);
CREATE INDEX IF NOT EXISTS idx_evaluations_deleted_at ON evaluations(deleted_at);
CREATE INDEX IF NOT EXISTS idx_eom_cycles_deleted_at ON eom_cycles(deleted_at);
CREATE INDEX IF NOT EXISTS idx_eom_nominees_deleted_at ON eom_nominees(deleted_at);

-- --------------------------------------------------------------------------
-- Cascade protection for critical entities
-- --------------------------------------------------------------------------
ALTER TABLE assignments DROP CONSTRAINT IF EXISTS assignments_cycle_id_fkey;
ALTER TABLE assignments
    ADD CONSTRAINT assignments_cycle_id_fkey
    FOREIGN KEY (cycle_id)
    REFERENCES cycles(id)
    ON DELETE RESTRICT;

ALTER TABLE eom_cycles DROP CONSTRAINT IF EXISTS eom_cycles_cycle_id_fkey;
ALTER TABLE eom_cycles
    ADD CONSTRAINT eom_cycles_cycle_id_fkey
    FOREIGN KEY (cycle_id)
    REFERENCES cycles(id)
    ON DELETE RESTRICT;

ALTER TABLE weight_matrices DROP CONSTRAINT IF EXISTS weight_matrices_cycle_id_fkey;
ALTER TABLE weight_matrices
    ADD CONSTRAINT weight_matrices_cycle_id_fkey
    FOREIGN KEY (cycle_id)
    REFERENCES cycles(id)
    ON DELETE RESTRICT;

-- Ensure nominees are removed when the owning EOM cycle is removed
ALTER TABLE eom_nominees DROP CONSTRAINT IF EXISTS eom_nominees_eom_cycle_id_fkey;
ALTER TABLE eom_nominees
    ADD CONSTRAINT eom_nominees_eom_cycle_id_fkey
    FOREIGN KEY (eom_cycle_id)
    REFERENCES eom_cycles(id)
    ON DELETE CASCADE;

-- --------------------------------------------------------------------------
-- Vote tracking improvements
-- --------------------------------------------------------------------------
ALTER TABLE eom_voters ADD COLUMN IF NOT EXISTS nominee_email VARCHAR(255);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'eom_voters_nominee_email_fkey'
    ) THEN
        ALTER TABLE eom_voters
            ADD CONSTRAINT eom_voters_nominee_email_fkey
            FOREIGN KEY (nominee_email)
            REFERENCES people(email)
            ON DELETE CASCADE;
    END IF;
END $$;

-- --------------------------------------------------------------------------
-- Evaluation status constraint
-- --------------------------------------------------------------------------
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'evaluations_status_check'
    ) THEN
        ALTER TABLE evaluations
            ADD CONSTRAINT evaluations_status_check
            CHECK (status IN ('draft', 'submitted', 'reviewed'));
    END IF;
END $$;
