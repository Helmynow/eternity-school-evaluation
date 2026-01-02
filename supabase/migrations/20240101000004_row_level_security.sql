-- Row Level Security (RLS) Policies for Eternity School Evaluation System
-- Enable RLS and create policies for secure data access

-- ============================================================================
-- ENABLE RLS
-- ============================================================================

ALTER TABLE IF EXISTS cycles ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS people ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS assignments ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS evaluations ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS eom_cycles ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS eom_voters ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS eom_nominees ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS eom_winners ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS eom_rotation_rules ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS weight_matrices ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS audit_logs ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- RLS POLICIES
-- ============================================================================

-- Cycles: All authenticated users can read, only admins can write
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name = 'cycles'
    ) AND NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public'
        AND tablename = 'cycles'
        AND policyname = 'Cycles are viewable by authenticated users'
    ) THEN
        CREATE POLICY "Cycles are viewable by authenticated users"
            ON cycles FOR SELECT
            USING (auth.role() = 'authenticated');
    END IF;
END $$;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name = 'cycles'
    ) AND NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public'
        AND tablename = 'cycles'
        AND policyname = 'Cycles are insertable by service role'
    ) THEN
        CREATE POLICY "Cycles are insertable by service role"
            ON cycles FOR INSERT
            WITH CHECK (auth.role() = 'service_role');
    END IF;
END $$;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name = 'cycles'
    ) AND NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public'
        AND tablename = 'cycles'
        AND policyname = 'Cycles are updatable by service role'
    ) THEN
        CREATE POLICY "Cycles are updatable by service role"
            ON cycles FOR UPDATE
            USING (auth.role() = 'service_role');
    END IF;
END $$;

-- People: All authenticated users can read, only service role can write
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name = 'people'
    ) AND NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public'
        AND tablename = 'people'
        AND policyname = 'People are viewable by authenticated users'
    ) THEN
        CREATE POLICY "People are viewable by authenticated users"
            ON people FOR SELECT
            USING (auth.role() = 'authenticated');
    END IF;
END $$;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name = 'people'
    ) AND NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public'
        AND tablename = 'people'
        AND policyname = 'People are insertable by service role'
    ) THEN
        CREATE POLICY "People are insertable by service role"
            ON people FOR INSERT
            WITH CHECK (auth.role() = 'service_role');
    END IF;
END $$;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name = 'people'
    ) AND NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public'
        AND tablename = 'people'
        AND policyname = 'People are updatable by service role'
    ) THEN
        CREATE POLICY "People are updatable by service role"
            ON people FOR UPDATE
            USING (auth.role() = 'service_role');
    END IF;
END $$;

-- Assignments: Users can view their own assignments
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name = 'assignments'
    ) AND NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public'
        AND tablename = 'assignments'
        AND policyname = 'Users can view their own assignments'
    ) THEN
        CREATE POLICY "Users can view their own assignments"
            ON assignments FOR SELECT
            USING (
                auth.role() = 'authenticated' AND (
                    rater_email = auth.email() OR
                    target_email = auth.email() OR
                    auth.role() = 'service_role'
                )
            );
    END IF;
END $$;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name = 'assignments'
    ) AND NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public'
        AND tablename = 'assignments'
        AND policyname = 'Assignments are insertable by service role'
    ) THEN
        CREATE POLICY "Assignments are insertable by service role"
            ON assignments FOR INSERT
            WITH CHECK (auth.role() = 'service_role');
    END IF;
END $$;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name = 'assignments'
    ) AND NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public'
        AND tablename = 'assignments'
        AND policyname = 'Assignments are updatable by service role'
    ) THEN
        CREATE POLICY "Assignments are updatable by service role"
            ON assignments FOR UPDATE
            USING (auth.role() = 'service_role');
    END IF;
END $$;

-- Evaluations: Users can view and create their own evaluations
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name = 'evaluations'
    ) AND NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public'
        AND tablename = 'evaluations'
        AND policyname = 'Users can view evaluations for their assignments'
    ) THEN
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
    END IF;
END $$;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name = 'evaluations'
    ) AND NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public'
        AND tablename = 'evaluations'
        AND policyname = 'Users can create evaluations for their assignments'
    ) THEN
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
    END IF;
END $$;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name = 'evaluations'
    ) AND NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public'
        AND tablename = 'evaluations'
        AND policyname = 'Users can update their own evaluations'
    ) THEN
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
    END IF;
END $$;

-- EOM Cycles: All authenticated users can read
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name = 'eom_cycles'
    ) AND NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public'
        AND tablename = 'eom_cycles'
        AND policyname = 'EOM cycles are viewable by authenticated users'
    ) THEN
        CREATE POLICY "EOM cycles are viewable by authenticated users"
            ON eom_cycles FOR SELECT
            USING (auth.role() = 'authenticated');
    END IF;
END $$;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name = 'eom_cycles'
    ) AND NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public'
        AND tablename = 'eom_cycles'
        AND policyname = 'EOM cycles are insertable by service role'
    ) THEN
        CREATE POLICY "EOM cycles are insertable by service role"
            ON eom_cycles FOR INSERT
            WITH CHECK (auth.role() = 'service_role');
    END IF;
END $$;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name = 'eom_cycles'
    ) AND NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public'
        AND tablename = 'eom_cycles'
        AND policyname = 'EOM cycles are updatable by service role'
    ) THEN
        CREATE POLICY "EOM cycles are updatable by service role"
            ON eom_cycles FOR UPDATE
            USING (auth.role() = 'service_role')
            WITH CHECK (auth.role() = 'service_role');
    END IF;
END $$;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name = 'eom_cycles'
    ) AND NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public'
        AND tablename = 'eom_cycles'
        AND policyname = 'EOM cycles are deletable by service role'
    ) THEN
        CREATE POLICY "EOM cycles are deletable by service role"
            ON eom_cycles FOR DELETE
            USING (auth.role() = 'service_role');
    END IF;
END $$;

-- EOM Voters: Users can view if they are voters
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name = 'eom_voters'
    ) AND NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public'
        AND tablename = 'eom_voters'
        AND policyname = 'Users can view EOM voters'
    ) THEN
        CREATE POLICY "Users can view EOM voters"
            ON eom_voters FOR SELECT
            USING (auth.role() = 'authenticated');
    END IF;
END $$;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name = 'eom_voters'
    ) AND NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public'
        AND tablename = 'eom_voters'
        AND policyname = 'EOM voters are insertable by service role'
    ) THEN
        CREATE POLICY "EOM voters are insertable by service role"
            ON eom_voters FOR INSERT
            WITH CHECK (auth.role() = 'service_role');
    END IF;
END $$;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name = 'eom_voters'
    ) AND NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public'
        AND tablename = 'eom_voters'
        AND policyname = 'EOM voters are updatable by service role'
    ) THEN
        CREATE POLICY "EOM voters are updatable by service role"
            ON eom_voters FOR UPDATE
            USING (auth.role() = 'service_role')
            WITH CHECK (auth.role() = 'service_role');
    END IF;
END $$;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name = 'eom_voters'
    ) AND NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public'
        AND tablename = 'eom_voters'
        AND policyname = 'EOM voters are deletable by service role'
    ) THEN
        CREATE POLICY "EOM voters are deletable by service role"
            ON eom_voters FOR DELETE
            USING (auth.role() = 'service_role');
    END IF;
END $$;

-- EOM Nominees: All authenticated users can view
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name = 'eom_nominees'
    ) AND NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public'
        AND tablename = 'eom_nominees'
        AND policyname = 'EOM nominees are viewable by authenticated users'
    ) THEN
        CREATE POLICY "EOM nominees are viewable by authenticated users"
            ON eom_nominees FOR SELECT
            USING (auth.role() = 'authenticated');
    END IF;
END $$;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name = 'eom_nominees'
    ) AND NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public'
        AND tablename = 'eom_nominees'
        AND policyname = 'Users can create nominations'
    ) THEN
        CREATE POLICY "Users can create nominations"
            ON eom_nominees FOR INSERT
            WITH CHECK (
                auth.role() = 'authenticated' AND
                (nominated_by = auth.email() OR auth.role() = 'service_role')
            );
    END IF;
END $$;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name = 'eom_nominees'
    ) AND NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public'
        AND tablename = 'eom_nominees'
        AND policyname = 'EOM nominees are updatable by service role'
    ) THEN
        CREATE POLICY "EOM nominees are updatable by service role"
            ON eom_nominees FOR UPDATE
            USING (auth.role() = 'service_role');
    END IF;
END $$;

-- EOM Winners: All authenticated users can view
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name = 'eom_winners'
    ) AND NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public'
        AND tablename = 'eom_winners'
        AND policyname = 'EOM winners are viewable by authenticated users'
    ) THEN
        CREATE POLICY "EOM winners are viewable by authenticated users"
            ON eom_winners FOR SELECT
            USING (auth.role() = 'authenticated');
    END IF;
END $$;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name = 'eom_winners'
    ) AND NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public'
        AND tablename = 'eom_winners'
        AND policyname = 'EOM winners are insertable by service role'
    ) THEN
        CREATE POLICY "EOM winners are insertable by service role"
            ON eom_winners FOR INSERT
            WITH CHECK (auth.role() = 'service_role');
    END IF;
END $$;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name = 'eom_winners'
    ) AND NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public'
        AND tablename = 'eom_winners'
        AND policyname = 'EOM winners are updatable by service role'
    ) THEN
        CREATE POLICY "EOM winners are updatable by service role"
            ON eom_winners FOR UPDATE
            USING (auth.role() = 'service_role')
            WITH CHECK (auth.role() = 'service_role');
    END IF;
END $$;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name = 'eom_winners'
    ) AND NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public'
        AND tablename = 'eom_winners'
        AND policyname = 'EOM winners are deletable by service role'
    ) THEN
        CREATE POLICY "EOM winners are deletable by service role"
            ON eom_winners FOR DELETE
            USING (auth.role() = 'service_role');
    END IF;
END $$;

-- EOM Rotation Rules: All authenticated users can view
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name = 'eom_rotation_rules'
    ) AND NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public'
        AND tablename = 'eom_rotation_rules'
        AND policyname = 'Rotation rules are viewable by authenticated users'
    ) THEN
        CREATE POLICY "Rotation rules are viewable by authenticated users"
            ON eom_rotation_rules FOR SELECT
            USING (auth.role() = 'authenticated');
    END IF;
END $$;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name = 'eom_rotation_rules'
    ) AND NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public'
        AND tablename = 'eom_rotation_rules'
        AND policyname = 'Rotation rules are insertable by service role'
    ) THEN
        CREATE POLICY "Rotation rules are insertable by service role"
            ON eom_rotation_rules FOR INSERT
            WITH CHECK (auth.role() = 'service_role');
    END IF;
END $$;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name = 'eom_rotation_rules'
    ) AND NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public'
        AND tablename = 'eom_rotation_rules'
        AND policyname = 'Rotation rules are updatable by service role'
    ) THEN
        CREATE POLICY "Rotation rules are updatable by service role"
            ON eom_rotation_rules FOR UPDATE
            USING (auth.role() = 'service_role')
            WITH CHECK (auth.role() = 'service_role');
    END IF;
END $$;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name = 'eom_rotation_rules'
    ) AND NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public'
        AND tablename = 'eom_rotation_rules'
        AND policyname = 'Rotation rules are deletable by service role'
    ) THEN
        CREATE POLICY "Rotation rules are deletable by service role"
            ON eom_rotation_rules FOR DELETE
            USING (auth.role() = 'service_role');
    END IF;
END $$;

-- Weight Matrices: All authenticated users can view
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name = 'weight_matrices'
    ) AND NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public'
        AND tablename = 'weight_matrices'
        AND policyname = 'Weight matrices are viewable by authenticated users'
    ) THEN
        CREATE POLICY "Weight matrices are viewable by authenticated users"
            ON weight_matrices FOR SELECT
            USING (auth.role() = 'authenticated');
    END IF;
END $$;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name = 'weight_matrices'
    ) AND NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public'
        AND tablename = 'weight_matrices'
        AND policyname = 'Weight matrices are insertable by service role'
    ) THEN
        CREATE POLICY "Weight matrices are insertable by service role"
            ON weight_matrices FOR INSERT
            WITH CHECK (auth.role() = 'service_role');
    END IF;
END $$;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name = 'weight_matrices'
    ) AND NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public'
        AND tablename = 'weight_matrices'
        AND policyname = 'Weight matrices are updatable by service role'
    ) THEN
        CREATE POLICY "Weight matrices are updatable by service role"
            ON weight_matrices FOR UPDATE
            USING (auth.role() = 'service_role')
            WITH CHECK (auth.role() = 'service_role');
    END IF;
END $$;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name = 'weight_matrices'
    ) AND NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public'
        AND tablename = 'weight_matrices'
        AND policyname = 'Weight matrices are deletable by service role'
    ) THEN
        CREATE POLICY "Weight matrices are deletable by service role"
            ON weight_matrices FOR DELETE
            USING (auth.role() = 'service_role');
    END IF;
END $$;

-- Audit Logs: Only service role can view (sensitive data)
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name = 'audit_logs'
    ) AND NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public'
        AND tablename = 'audit_logs'
        AND policyname = 'Audit logs are viewable by service role only'
    ) THEN
        CREATE POLICY "Audit logs are viewable by service role only"
            ON audit_logs FOR SELECT
            USING (auth.role() = 'service_role');
    END IF;
END $$;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name = 'audit_logs'
    ) AND NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public'
        AND tablename = 'audit_logs'
        AND policyname = 'Audit logs are insertable by service role'
    ) THEN
        CREATE POLICY "Audit logs are insertable by service role"
            ON audit_logs FOR INSERT
            WITH CHECK (auth.role() = 'service_role');
    END IF;
END $$;

-- ============================================================================
-- NOTE: For development/testing, you may want to disable RLS temporarily
-- ALTER TABLE table_name DISABLE ROW LEVEL SECURITY;
-- ============================================================================
