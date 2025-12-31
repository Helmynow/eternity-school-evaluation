-- Row Level Security (RLS) Policies for Eternity School Evaluation System
-- Enable RLS and create policies for secure data access

-- ============================================================================
-- ENABLE RLS
-- ============================================================================

ALTER TABLE cycles ENABLE ROW LEVEL SECURITY;
ALTER TABLE people ENABLE ROW LEVEL SECURITY;
ALTER TABLE assignments ENABLE ROW LEVEL SECURITY;
ALTER TABLE evaluations ENABLE ROW LEVEL SECURITY;
ALTER TABLE eom_cycles ENABLE ROW LEVEL SECURITY;
ALTER TABLE eom_voters ENABLE ROW LEVEL SECURITY;
ALTER TABLE eom_nominees ENABLE ROW LEVEL SECURITY;
ALTER TABLE eom_winners ENABLE ROW LEVEL SECURITY;
ALTER TABLE eom_rotation_rules ENABLE ROW LEVEL SECURITY;
ALTER TABLE weight_matrices ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- RLS POLICIES
-- ============================================================================

-- Cycles: All authenticated users can read, only admins can write
CREATE POLICY "Cycles are viewable by authenticated users"
    ON cycles FOR SELECT
    USING (auth.role() = 'authenticated');

CREATE POLICY "Cycles are insertable by service role"
    ON cycles FOR INSERT
    WITH CHECK (auth.role() = 'service_role');

CREATE POLICY "Cycles are updatable by service role"
    ON cycles FOR UPDATE
    USING (auth.role() = 'service_role');

-- People: All authenticated users can read, only service role can write
CREATE POLICY "People are viewable by authenticated users"
    ON people FOR SELECT
    USING (auth.role() = 'authenticated');

CREATE POLICY "People are insertable by service role"
    ON people FOR INSERT
    WITH CHECK (auth.role() = 'service_role');

CREATE POLICY "People are updatable by service role"
    ON people FOR UPDATE
    USING (auth.role() = 'service_role');

-- Assignments: Users can view their own assignments
CREATE POLICY "Users can view their own assignments"
    ON assignments FOR SELECT
    USING (
        auth.role() = 'authenticated' AND (
            rater_email = auth.email() OR 
            target_email = auth.email() OR
            auth.role() = 'service_role'
        )
    );

CREATE POLICY "Assignments are insertable by service role"
    ON assignments FOR INSERT
    WITH CHECK (auth.role() = 'service_role');

CREATE POLICY "Assignments are updatable by service role"
    ON assignments FOR UPDATE
    USING (auth.role() = 'service_role');

-- Evaluations: Users can view and create their own evaluations
CREATE POLICY "Users can view evaluations for their assignments"
    ON evaluations FOR SELECT
    USING (
        auth.role() = 'authenticated' AND (
            EXISTS (
                SELECT 1 FROM assignments a
                WHERE a.id = evaluations.assignment_id
                  AND (a.rater_email = auth.email() OR a.target_email = auth.email())
            ) OR
            auth.role() = 'service_role'
        )
    );

CREATE POLICY "Users can create evaluations for their assignments"
    ON evaluations FOR INSERT
    WITH CHECK (
        auth.role() = 'authenticated' AND
        EXISTS (
            SELECT 1 FROM assignments a
            WHERE a.id = evaluations.assignment_id
              AND a.rater_email = auth.email()
        )
    );

CREATE POLICY "Users can update their own evaluations"
    ON evaluations FOR UPDATE
    USING (
        auth.role() = 'authenticated' AND
        EXISTS (
            SELECT 1 FROM assignments a
            WHERE a.id = evaluations.assignment_id
              AND a.rater_email = auth.email()
        )
    );

-- EOM Cycles: All authenticated users can read
CREATE POLICY "EOM cycles are viewable by authenticated users"
    ON eom_cycles FOR SELECT
    USING (auth.role() = 'authenticated');

CREATE POLICY "EOM cycles are modifiable by service role"
    ON eom_cycles FOR ALL
    USING (auth.role() = 'service_role')
    WITH CHECK (auth.role() = 'service_role');

-- EOM Voters: Users can view if they are voters
CREATE POLICY "Users can view EOM voters"
    ON eom_voters FOR SELECT
    USING (auth.role() = 'authenticated');

CREATE POLICY "EOM voters are modifiable by service role"
    ON eom_voters FOR ALL
    USING (auth.role() = 'service_role')
    WITH CHECK (auth.role() = 'service_role');

-- EOM Nominees: All authenticated users can view
CREATE POLICY "EOM nominees are viewable by authenticated users"
    ON eom_nominees FOR SELECT
    USING (auth.role() = 'authenticated');

CREATE POLICY "Users can create nominations"
    ON eom_nominees FOR INSERT
    WITH CHECK (
        auth.role() = 'authenticated' AND
        (nominated_by = auth.email() OR auth.role() = 'service_role')
    );

CREATE POLICY "EOM nominees are updatable by service role"
    ON eom_nominees FOR UPDATE
    USING (auth.role() = 'service_role');

-- EOM Winners: All authenticated users can view
CREATE POLICY "EOM winners are viewable by authenticated users"
    ON eom_winners FOR SELECT
    USING (auth.role() = 'authenticated');

CREATE POLICY "EOM winners are modifiable by service role"
    ON eom_winners FOR ALL
    USING (auth.role() = 'service_role')
    WITH CHECK (auth.role() = 'service_role');

-- EOM Rotation Rules: All authenticated users can view
CREATE POLICY "Rotation rules are viewable by authenticated users"
    ON eom_rotation_rules FOR SELECT
    USING (auth.role() = 'authenticated');

CREATE POLICY "Rotation rules are modifiable by service role"
    ON eom_rotation_rules FOR ALL
    USING (auth.role() = 'service_role')
    WITH CHECK (auth.role() = 'service_role');

-- Weight Matrices: All authenticated users can view
CREATE POLICY "Weight matrices are viewable by authenticated users"
    ON weight_matrices FOR SELECT
    USING (auth.role() = 'authenticated');

CREATE POLICY "Weight matrices are modifiable by service role"
    ON weight_matrices FOR ALL
    USING (auth.role() = 'service_role')
    WITH CHECK (auth.role() = 'service_role');

-- Audit Logs: Only service role can view (sensitive data)
CREATE POLICY "Audit logs are viewable by service role only"
    ON audit_logs FOR SELECT
    USING (auth.role() = 'service_role');

CREATE POLICY "Audit logs are insertable by service role"
    ON audit_logs FOR INSERT
    WITH CHECK (auth.role() = 'service_role');

-- ============================================================================
-- NOTE: For development/testing, you may want to disable RLS temporarily
-- ALTER TABLE table_name DISABLE ROW LEVEL SECURITY;
-- ============================================================================

