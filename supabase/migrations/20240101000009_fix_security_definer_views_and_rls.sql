-- Fix Security Definer Views and Enable RLS
-- This migration addresses Supabase security advisor warnings:
-- 1. Removes SECURITY DEFINER from all views (converts to SECURITY INVOKER)
-- 2. Enables RLS on all public tables that are missing it

-- ============================================================================
-- FIX VIEWS: Remove SECURITY DEFINER by dropping and recreating
-- ============================================================================

-- PostgreSQL doesn't support ALTER VIEW to change security definer property
-- We must drop and recreate the views. Views are SECURITY INVOKER by default
-- when created without explicitly specifying SECURITY DEFINER

-- 1. mre_who_evaluates_who
DROP VIEW IF EXISTS mre_who_evaluates_who CASCADE;
CREATE VIEW mre_who_evaluates_who AS
SELECT
    cy.code          AS cycle_code,
    a.rater_email,
    pr.full_name     AS rater_name,
    a.rater_role AS rater_role,
    a.target_email,
    pt.full_name     AS target_name,
    a.target_role AS target_role,
    a.target_group,
    a.rater_context,
    a.weight,
    e.rating,
    e.status AS evaluation_status
FROM assignments a
JOIN cycles cy ON cy.id = a.cycle_id
LEFT JOIN people pr ON pr.email = a.rater_email
LEFT JOIN people pt ON pt.email = a.target_email
LEFT JOIN evaluations e ON e.assignment_id = a.id
ORDER BY cycle_code, a.target_group, a.rater_context, rater_name, target_name;

-- 2. mre_evaluation_summary
DROP VIEW IF EXISTS mre_evaluation_summary CASCADE;
CREATE VIEW mre_evaluation_summary AS
SELECT
    cy.code AS cycle_code,
    a.target_email,
    pt.full_name AS target_name,
    NULL::staff_segment AS target_segment,
    COUNT(e.id) AS total_evaluations,
    COUNT(CASE WHEN e.status = 'submitted' THEN 1 END) AS submitted_evaluations,
    AVG(CASE WHEN e.status = 'submitted' THEN e.rating END) AS average_rating,
    AVG(CASE WHEN e.status = 'submitted' THEN e.weighted_rating END) AS average_weighted_rating,
    MIN(CASE WHEN e.status = 'submitted' THEN e.rating END) AS min_rating,
    MAX(CASE WHEN e.status = 'submitted' THEN e.rating END) AS max_rating
FROM assignments a
JOIN cycles cy ON cy.id = a.cycle_id
JOIN people pt ON pt.email = a.target_email
LEFT JOIN evaluations e ON e.assignment_id = a.id
GROUP BY cy.code, a.target_email, pt.full_name
ORDER BY cycle_code, target_name;

-- 3. eom_participants
DROP VIEW IF EXISTS eom_participants CASCADE;
CREATE VIEW eom_participants AS
SELECT
    cy.code || '-EOM-' || LPAD(e.month::text, 2, '0') || '-' || e.year AS eom_code,
    'voter' AS kind,
    v.voter_email AS email,
    p.full_name,
    NULL::VARCHAR(100) AS role_title,
    NULL::staff_segment AS segment
FROM eom_voters v
JOIN eom_cycles e ON e.id = v.eom_cycle_id
JOIN cycles cy ON cy.id = e.cycle_id
LEFT JOIN people p ON p.email = v.voter_email
UNION ALL
SELECT
    cy.code || '-EOM-' || LPAD(e.month::text, 2, '0') || '-' || e.year AS eom_code,
    'nominee' AS kind,
    n.nominee_email AS email,
    p2.full_name,
    NULL::VARCHAR(100) AS role_title,
    NULL::staff_segment AS segment
FROM eom_nominees n
JOIN eom_cycles e ON e.id = n.eom_cycle_id
JOIN cycles cy ON cy.id = e.cycle_id
LEFT JOIN people p2 ON p2.email = n.nominee_email
ORDER BY eom_code, kind, full_name;

-- 4. eom_nomination_summary
DROP VIEW IF EXISTS eom_nomination_summary CASCADE;
CREATE VIEW eom_nomination_summary AS
SELECT
    cy.code || '-EOM-' || LPAD(e.month::text, 2, '0') || '-' || e.year AS eom_code,
    e.month,
    e.year,
    n.category,
    COUNT(DISTINCT n.nominee_email) AS nominee_count,
    COUNT(DISTINCT n.nominated_by) AS nominator_count,
    SUM(n.votes_received) AS total_votes,
    AVG(n.votes_received) AS avg_votes_per_nominee
FROM eom_nominees n
JOIN eom_cycles e ON e.id = n.eom_cycle_id
JOIN cycles cy ON cy.id = e.cycle_id
GROUP BY cy.code, e.month, e.year, n.category
ORDER BY e.year DESC, e.month DESC, n.category;

-- 5. eom_winner_history
DROP VIEW IF EXISTS eom_winner_history CASCADE;
CREATE VIEW eom_winner_history AS
SELECT
    w.id,
    cy.code || '-EOM-' || LPAD(e.month::text, 2, '0') || '-' || e.year AS eom_code,
    w.winner_email,
    p.full_name AS winner_name,
    w.category,
    w.term,
    w.votes_received,
    w.announced_at,
    e.month,
    e.year
FROM eom_winners w
JOIN eom_cycles e ON e.id = w.eom_cycle_id
JOIN cycles cy ON cy.id = e.cycle_id
LEFT JOIN people p ON p.email = w.winner_email
ORDER BY e.year DESC, e.month DESC, w.announced_at DESC;

-- 6. weighted_score_summary
DROP VIEW IF EXISTS weighted_score_summary CASCADE;
CREATE VIEW weighted_score_summary AS
SELECT
    cy.code AS cycle_code,
    NULL::staff_segment AS segment,
    'other'::VARCHAR(20) AS staff_type,
    COUNT(DISTINCT a.target_email) AS staff_count,
    COUNT(e.id) AS total_evaluations,
    AVG(CASE WHEN e.status = 'submitted' THEN e.weighted_rating END) AS avg_weighted_score,
    AVG(CASE WHEN e.status = 'submitted' THEN e.rating END) AS avg_raw_score
FROM assignments a
JOIN cycles cy ON cy.id = a.cycle_id
JOIN people pt ON pt.email = a.target_email
LEFT JOIN evaluations e ON e.assignment_id = a.id
GROUP BY cy.code
ORDER BY cycle_code;

-- 7. recent_audit_logs
DROP VIEW IF EXISTS recent_audit_logs CASCADE;
CREATE VIEW recent_audit_logs AS
SELECT
    al.id,
    al.action_type,
    al.entity_type,
    al.entity_id,
    al.user_email,
    p.full_name AS user_name,
    al.user_role,
    al.changes,
    al.timestamp
FROM audit_logs al
LEFT JOIN people p ON p.email = al.user_email
ORDER BY al.timestamp DESC
LIMIT 1000;

-- ============================================================================
-- ENABLE RLS ON ALL PUBLIC TABLES
-- ============================================================================

-- Enable RLS on all tables that are exposed to PostgREST
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
-- ENSURE RLS POLICIES EXIST FOR ALL TABLES
-- ============================================================================

-- Cycles policies
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE schemaname = 'public' 
        AND tablename = 'cycles' 
        AND policyname = 'Cycles are viewable by authenticated users'
    ) THEN
        CREATE POLICY "Cycles are viewable by authenticated users"
            ON cycles FOR SELECT
            USING ((select auth.role()) = 'authenticated');
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE schemaname = 'public' 
        AND tablename = 'cycles' 
        AND policyname = 'Cycles are insertable by service role'
    ) THEN
        CREATE POLICY "Cycles are insertable by service role"
            ON cycles FOR INSERT
            WITH CHECK ((select auth.role()) = 'service_role');
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE schemaname = 'public' 
        AND tablename = 'cycles' 
        AND policyname = 'Cycles are updatable by service role'
    ) THEN
        CREATE POLICY "Cycles are updatable by service role"
            ON cycles FOR UPDATE
            USING ((select auth.role()) = 'service_role');
    END IF;
END $$;

-- People policies
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE schemaname = 'public' 
        AND tablename = 'people' 
        AND policyname = 'People are viewable by authenticated users'
    ) THEN
        CREATE POLICY "People are viewable by authenticated users"
            ON people FOR SELECT
            USING ((select auth.role()) = 'authenticated');
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE schemaname = 'public' 
        AND tablename = 'people' 
        AND policyname = 'People are insertable by service role'
    ) THEN
        CREATE POLICY "People are insertable by service role"
            ON people FOR INSERT
            WITH CHECK ((select auth.role()) = 'service_role');
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE schemaname = 'public' 
        AND tablename = 'people' 
        AND policyname = 'People are updatable by service role'
    ) THEN
        CREATE POLICY "People are updatable by service role"
            ON people FOR UPDATE
            USING ((select auth.role()) = 'service_role');
    END IF;
END $$;

-- Assignments policies
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE schemaname = 'public' 
        AND tablename = 'assignments' 
        AND policyname = 'Users can view their own assignments'
    ) THEN
        CREATE POLICY "Users can view their own assignments"
            ON assignments FOR SELECT
            USING (
                (select auth.role()) = 'authenticated' AND
                (rater_email = auth.email() OR target_email = auth.email())
            );
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE schemaname = 'public' 
        AND tablename = 'assignments' 
        AND policyname = 'Assignments are insertable by service role'
    ) THEN
        CREATE POLICY "Assignments are insertable by service role"
            ON assignments FOR INSERT
            WITH CHECK ((select auth.role()) = 'service_role');
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE schemaname = 'public' 
        AND tablename = 'assignments' 
        AND policyname = 'Assignments are updatable by service role'
    ) THEN
        CREATE POLICY "Assignments are updatable by service role"
            ON assignments FOR UPDATE
            USING ((select auth.role()) = 'service_role');
    END IF;
END $$;

-- Evaluations policies
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE schemaname = 'public' 
        AND tablename = 'evaluations' 
        AND policyname = 'Users can view evaluations for their assignments'
    ) THEN
        CREATE POLICY "Users can view evaluations for their assignments"
            ON evaluations FOR SELECT
            USING (
                (select auth.role()) = 'authenticated' AND
                EXISTS (
                    SELECT 1 FROM assignments a
                    WHERE a.id = evaluations.assignment_id
                    AND (a.rater_email = auth.email() OR a.target_email = auth.email())
                )
            );
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE schemaname = 'public' 
        AND tablename = 'evaluations' 
        AND policyname = 'Users can create evaluations for their assignments'
    ) THEN
        CREATE POLICY "Users can create evaluations for their assignments"
            ON evaluations FOR INSERT
            WITH CHECK (
                (select auth.role()) = 'authenticated' AND
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
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE schemaname = 'public' 
        AND tablename = 'evaluations' 
        AND policyname = 'Users can update their own evaluations'
    ) THEN
        CREATE POLICY "Users can update their own evaluations"
            ON evaluations FOR UPDATE
            USING (
                (select auth.role()) = 'authenticated' AND
                EXISTS (
                    SELECT 1 FROM assignments a
                    WHERE a.id = evaluations.assignment_id
                    AND a.rater_email = auth.email()
                )
            );
    END IF;
END $$;

-- EOM Cycles policies
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE schemaname = 'public' 
        AND tablename = 'eom_cycles' 
        AND policyname = 'EOM cycles are viewable by authenticated users'
    ) THEN
        CREATE POLICY "EOM cycles are viewable by authenticated users"
            ON eom_cycles FOR SELECT
            USING ((select auth.role()) = 'authenticated');
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE schemaname = 'public' 
        AND tablename = 'eom_cycles' 
        AND policyname = 'EOM cycles are insertable by service role'
    ) THEN
        CREATE POLICY "EOM cycles are insertable by service role"
            ON eom_cycles FOR INSERT
            WITH CHECK ((select auth.role()) = 'service_role');
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE schemaname = 'public' 
        AND tablename = 'eom_cycles' 
        AND policyname = 'EOM cycles are updatable by service role'
    ) THEN
        CREATE POLICY "EOM cycles are updatable by service role"
            ON eom_cycles FOR UPDATE
            USING ((select auth.role()) = 'service_role')
            WITH CHECK ((select auth.role()) = 'service_role');
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE schemaname = 'public' 
        AND tablename = 'eom_cycles' 
        AND policyname = 'EOM cycles are deletable by service role'
    ) THEN
        CREATE POLICY "EOM cycles are deletable by service role"
            ON eom_cycles FOR DELETE
            USING ((select auth.role()) = 'service_role');
    END IF;
END $$;

-- EOM Voters policies
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE schemaname = 'public' 
        AND tablename = 'eom_voters' 
        AND policyname = 'Users can view EOM voters'
    ) THEN
        CREATE POLICY "Users can view EOM voters"
            ON eom_voters FOR SELECT
            USING ((select auth.role()) = 'authenticated');
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE schemaname = 'public' 
        AND tablename = 'eom_voters' 
        AND policyname = 'EOM voters are insertable by service role'
    ) THEN
        CREATE POLICY "EOM voters are insertable by service role"
            ON eom_voters FOR INSERT
            WITH CHECK ((select auth.role()) = 'service_role');
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE schemaname = 'public' 
        AND tablename = 'eom_voters' 
        AND policyname = 'EOM voters are updatable by service role'
    ) THEN
        CREATE POLICY "EOM voters are updatable by service role"
            ON eom_voters FOR UPDATE
            USING ((select auth.role()) = 'service_role')
            WITH CHECK ((select auth.role()) = 'service_role');
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE schemaname = 'public' 
        AND tablename = 'eom_voters' 
        AND policyname = 'EOM voters are deletable by service role'
    ) THEN
        CREATE POLICY "EOM voters are deletable by service role"
            ON eom_voters FOR DELETE
            USING ((select auth.role()) = 'service_role');
    END IF;
END $$;

-- EOM Nominees policies
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE schemaname = 'public' 
        AND tablename = 'eom_nominees' 
        AND policyname = 'EOM nominees are viewable by authenticated users'
    ) THEN
        CREATE POLICY "EOM nominees are viewable by authenticated users"
            ON eom_nominees FOR SELECT
            USING ((select auth.role()) = 'authenticated');
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE schemaname = 'public' 
        AND tablename = 'eom_nominees' 
        AND policyname = 'Users can create nominations'
    ) THEN
        CREATE POLICY "Users can create nominations"
            ON eom_nominees FOR INSERT
            WITH CHECK (
                (select auth.role()) = 'authenticated' AND
                (nominated_by = auth.email() OR (select auth.role()) = 'service_role')
            );
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE schemaname = 'public' 
        AND tablename = 'eom_nominees' 
        AND policyname = 'EOM nominees are updatable by service role'
    ) THEN
        CREATE POLICY "EOM nominees are updatable by service role"
            ON eom_nominees FOR UPDATE
            USING ((select auth.role()) = 'service_role');
    END IF;
END $$;

-- EOM Winners policies
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE schemaname = 'public' 
        AND tablename = 'eom_winners' 
        AND policyname = 'EOM winners are viewable by authenticated users'
    ) THEN
        CREATE POLICY "EOM winners are viewable by authenticated users"
            ON eom_winners FOR SELECT
            USING ((select auth.role()) = 'authenticated');
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE schemaname = 'public' 
        AND tablename = 'eom_winners' 
        AND policyname = 'EOM winners are insertable by service role'
    ) THEN
        CREATE POLICY "EOM winners are insertable by service role"
            ON eom_winners FOR INSERT
            WITH CHECK ((select auth.role()) = 'service_role');
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE schemaname = 'public' 
        AND tablename = 'eom_winners' 
        AND policyname = 'EOM winners are updatable by service role'
    ) THEN
        CREATE POLICY "EOM winners are updatable by service role"
            ON eom_winners FOR UPDATE
            USING ((select auth.role()) = 'service_role')
            WITH CHECK ((select auth.role()) = 'service_role');
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE schemaname = 'public' 
        AND tablename = 'eom_winners' 
        AND policyname = 'EOM winners are deletable by service role'
    ) THEN
        CREATE POLICY "EOM winners are deletable by service role"
            ON eom_winners FOR DELETE
            USING ((select auth.role()) = 'service_role');
    END IF;
END $$;

-- EOM Rotation Rules policies
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE schemaname = 'public' 
        AND tablename = 'eom_rotation_rules' 
        AND policyname = 'Rotation rules are viewable by authenticated users'
    ) THEN
        CREATE POLICY "Rotation rules are viewable by authenticated users"
            ON eom_rotation_rules FOR SELECT
            USING ((select auth.role()) = 'authenticated');
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE schemaname = 'public' 
        AND tablename = 'eom_rotation_rules' 
        AND policyname = 'Rotation rules are insertable by service role'
    ) THEN
        CREATE POLICY "Rotation rules are insertable by service role"
            ON eom_rotation_rules FOR INSERT
            WITH CHECK ((select auth.role()) = 'service_role');
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE schemaname = 'public' 
        AND tablename = 'eom_rotation_rules' 
        AND policyname = 'Rotation rules are updatable by service role'
    ) THEN
        CREATE POLICY "Rotation rules are updatable by service role"
            ON eom_rotation_rules FOR UPDATE
            USING ((select auth.role()) = 'service_role')
            WITH CHECK ((select auth.role()) = 'service_role');
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE schemaname = 'public' 
        AND tablename = 'eom_rotation_rules' 
        AND policyname = 'Rotation rules are deletable by service role'
    ) THEN
        CREATE POLICY "Rotation rules are deletable by service role"
            ON eom_rotation_rules FOR DELETE
            USING ((select auth.role()) = 'service_role');
    END IF;
END $$;

-- Weight Matrices policies
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE schemaname = 'public' 
        AND tablename = 'weight_matrices' 
        AND policyname = 'Weight matrices are viewable by authenticated users'
    ) THEN
        CREATE POLICY "Weight matrices are viewable by authenticated users"
            ON weight_matrices FOR SELECT
            USING ((select auth.role()) = 'authenticated');
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE schemaname = 'public' 
        AND tablename = 'weight_matrices' 
        AND policyname = 'Weight matrices are insertable by service role'
    ) THEN
        CREATE POLICY "Weight matrices are insertable by service role"
            ON weight_matrices FOR INSERT
            WITH CHECK ((select auth.role()) = 'service_role');
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE schemaname = 'public' 
        AND tablename = 'weight_matrices' 
        AND policyname = 'Weight matrices are updatable by service role'
    ) THEN
        CREATE POLICY "Weight matrices are updatable by service role"
            ON weight_matrices FOR UPDATE
            USING ((select auth.role()) = 'service_role')
            WITH CHECK ((select auth.role()) = 'service_role');
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE schemaname = 'public' 
        AND tablename = 'weight_matrices' 
        AND policyname = 'Weight matrices are deletable by service role'
    ) THEN
        CREATE POLICY "Weight matrices are deletable by service role"
            ON weight_matrices FOR DELETE
            USING ((select auth.role()) = 'service_role');
    END IF;
END $$;

-- Audit Logs policies
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE schemaname = 'public' 
        AND tablename = 'audit_logs' 
        AND policyname = 'Audit logs are viewable by service role only'
    ) THEN
        CREATE POLICY "Audit logs are viewable by service role only"
            ON audit_logs FOR SELECT
            USING ((select auth.role()) = 'service_role');
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE schemaname = 'public' 
        AND tablename = 'audit_logs' 
        AND policyname = 'Audit logs are insertable by service role'
    ) THEN
        CREATE POLICY "Audit logs are insertable by service role"
            ON audit_logs FOR INSERT
            WITH CHECK ((select auth.role()) = 'service_role');
    END IF;
END $$;

