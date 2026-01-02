-- Fix Security Issues: Remove SECURITY DEFINER from views and enable RLS on missing tables
-- This migration addresses Supabase security advisor warnings

-- ============================================================================
-- FIX VIEWS: Change from SECURITY DEFINER to SECURITY INVOKER
-- ============================================================================

-- Views should use SECURITY INVOKER to respect the querying user's permissions
-- rather than the view creator's permissions

-- MRE Views
-- Note: Using ALTER VIEW to set security_invoker after creation
CREATE OR REPLACE VIEW mre_who_evaluates_who AS
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

ALTER VIEW mre_who_evaluates_who SET (security_invoker = true);

CREATE OR REPLACE VIEW mre_evaluation_summary AS
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

ALTER VIEW mre_evaluation_summary SET (security_invoker = true);

-- EOM Views
CREATE OR REPLACE VIEW eom_participants AS
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

ALTER VIEW eom_participants SET (security_invoker = true);

CREATE OR REPLACE VIEW eom_nomination_summary AS
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

ALTER VIEW eom_nomination_summary SET (security_invoker = true);

CREATE OR REPLACE VIEW eom_winner_history AS
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

ALTER VIEW eom_winner_history SET (security_invoker = true);

-- Scoring Views
CREATE OR REPLACE VIEW weighted_score_summary AS
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

ALTER VIEW weighted_score_summary SET (security_invoker = true);

-- Audit Views
CREATE OR REPLACE VIEW recent_audit_logs AS
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

ALTER VIEW recent_audit_logs SET (security_invoker = true);

-- Create or replace eom_eligible_current view (mentioned in security warnings)
-- Drop first if exists to avoid column mismatch errors
DROP VIEW IF EXISTS eom_eligible_current;

CREATE VIEW eom_eligible_current AS
SELECT DISTINCT
    p.email,
    p.full_name,
    p.segment,
    CASE 
        WHEN n.rotation_eligible = FALSE THEN FALSE
        WHEN n.last_won_cycle_id IS NOT NULL THEN
            EXISTS (
                SELECT 1 FROM eom_cycles ec
                WHERE ec.id = n.last_won_cycle_id
                AND ec.year >= EXTRACT(YEAR FROM CURRENT_DATE) - 1
            )
        ELSE TRUE
    END AS is_eligible
FROM people p
LEFT JOIN eom_nominees n ON n.nominee_email = p.email
WHERE p.active = TRUE;

ALTER VIEW eom_eligible_current SET (security_invoker = true);

-- ============================================================================
-- ENABLE RLS ON MISSING TABLES
-- ============================================================================

-- Enable RLS on tables that may exist but don't have it enabled
-- These tables might be legacy or created elsewhere

DO $$ 
BEGIN
    -- Enable RLS on eval_rater_rules if it exists
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'eval_rater_rules') THEN
        ALTER TABLE eval_rater_rules ENABLE ROW LEVEL SECURITY;
        
        -- Create basic RLS policies
        IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname = 'public' AND tablename = 'eval_rater_rules' AND policyname = 'eval_rater_rules_select') THEN
            CREATE POLICY "eval_rater_rules_select" ON eval_rater_rules
                FOR SELECT USING (auth.role() = 'authenticated');
        END IF;
        
        DROP POLICY IF EXISTS "eval_rater_rules_modify" ON eval_rater_rules;

        IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname = 'public' AND tablename = 'eval_rater_rules' AND policyname = 'eval_rater_rules_insert') THEN
            CREATE POLICY "eval_rater_rules_insert" ON eval_rater_rules
                FOR INSERT WITH CHECK (auth.role() = 'service_role');
        END IF;

        IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname = 'public' AND tablename = 'eval_rater_rules' AND policyname = 'eval_rater_rules_update') THEN
            CREATE POLICY "eval_rater_rules_update" ON eval_rater_rules
                FOR UPDATE USING (auth.role() = 'service_role')
                WITH CHECK (auth.role() = 'service_role');
        END IF;

        IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname = 'public' AND tablename = 'eval_rater_rules' AND policyname = 'eval_rater_rules_delete') THEN
            CREATE POLICY "eval_rater_rules_delete" ON eval_rater_rules
                FOR DELETE USING (auth.role() = 'service_role');
        END IF;
    END IF;
    
    -- Enable RLS on eval_domain_rules if it exists
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'eval_domain_rules') THEN
        ALTER TABLE eval_domain_rules ENABLE ROW LEVEL SECURITY;
        
        IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname = 'public' AND tablename = 'eval_domain_rules' AND policyname = 'eval_domain_rules_select') THEN
            CREATE POLICY "eval_domain_rules_select" ON eval_domain_rules
                FOR SELECT USING (auth.role() = 'authenticated');
        END IF;
        
        DROP POLICY IF EXISTS "eval_domain_rules_modify" ON eval_domain_rules;

        IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname = 'public' AND tablename = 'eval_domain_rules' AND policyname = 'eval_domain_rules_insert') THEN
            CREATE POLICY "eval_domain_rules_insert" ON eval_domain_rules
                FOR INSERT WITH CHECK (auth.role() = 'service_role');
        END IF;

        IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname = 'public' AND tablename = 'eval_domain_rules' AND policyname = 'eval_domain_rules_update') THEN
            CREATE POLICY "eval_domain_rules_update" ON eval_domain_rules
                FOR UPDATE USING (auth.role() = 'service_role')
                WITH CHECK (auth.role() = 'service_role');
        END IF;

        IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname = 'public' AND tablename = 'eval_domain_rules' AND policyname = 'eval_domain_rules_delete') THEN
            CREATE POLICY "eval_domain_rules_delete" ON eval_domain_rules
                FOR DELETE USING (auth.role() = 'service_role');
        END IF;
    END IF;
    
    -- Enable RLS on voters if it exists (different from eom_voters)
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'voters') THEN
        ALTER TABLE voters ENABLE ROW LEVEL SECURITY;
        
        IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname = 'public' AND tablename = 'voters' AND policyname = 'voters_select') THEN
            CREATE POLICY "voters_select" ON voters
                FOR SELECT USING (auth.role() = 'authenticated');
        END IF;
        
        DROP POLICY IF EXISTS "voters_modify" ON voters;

        IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname = 'public' AND tablename = 'voters' AND policyname = 'voters_insert') THEN
            CREATE POLICY "voters_insert" ON voters
                FOR INSERT WITH CHECK (auth.role() = 'service_role');
        END IF;

        IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname = 'public' AND tablename = 'voters' AND policyname = 'voters_update') THEN
            CREATE POLICY "voters_update" ON voters
                FOR UPDATE USING (auth.role() = 'service_role')
                WITH CHECK (auth.role() = 'service_role');
        END IF;

        IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname = 'public' AND tablename = 'voters' AND policyname = 'voters_delete') THEN
            CREATE POLICY "voters_delete" ON voters
                FOR DELETE USING (auth.role() = 'service_role');
        END IF;
    END IF;
    
    -- Enable RLS on winners if it exists (different from eom_winners)
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'winners') THEN
        ALTER TABLE winners ENABLE ROW LEVEL SECURITY;
        
        IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname = 'public' AND tablename = 'winners' AND policyname = 'winners_select') THEN
            CREATE POLICY "winners_select" ON winners
                FOR SELECT USING (auth.role() = 'authenticated');
        END IF;
        
        DROP POLICY IF EXISTS "winners_modify" ON winners;

        IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname = 'public' AND tablename = 'winners' AND policyname = 'winners_insert') THEN
            CREATE POLICY "winners_insert" ON winners
                FOR INSERT WITH CHECK (auth.role() = 'service_role');
        END IF;

        IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname = 'public' AND tablename = 'winners' AND policyname = 'winners_update') THEN
            CREATE POLICY "winners_update" ON winners
                FOR UPDATE USING (auth.role() = 'service_role')
                WITH CHECK (auth.role() = 'service_role');
        END IF;

        IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname = 'public' AND tablename = 'winners' AND policyname = 'winners_delete') THEN
            CREATE POLICY "winners_delete" ON winners
                FOR DELETE USING (auth.role() = 'service_role');
        END IF;
    END IF;
    
    -- Enable RLS on school_terms if it exists
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'school_terms') THEN
        ALTER TABLE school_terms ENABLE ROW LEVEL SECURITY;
        
        IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname = 'public' AND tablename = 'school_terms' AND policyname = 'school_terms_select') THEN
            CREATE POLICY "school_terms_select" ON school_terms
                FOR SELECT USING (auth.role() = 'authenticated');
        END IF;
        
        DROP POLICY IF EXISTS "school_terms_modify" ON school_terms;

        IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname = 'public' AND tablename = 'school_terms' AND policyname = 'school_terms_insert') THEN
            CREATE POLICY "school_terms_insert" ON school_terms
                FOR INSERT WITH CHECK (auth.role() = 'service_role');
        END IF;

        IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname = 'public' AND tablename = 'school_terms' AND policyname = 'school_terms_update') THEN
            CREATE POLICY "school_terms_update" ON school_terms
                FOR UPDATE USING (auth.role() = 'service_role')
                WITH CHECK (auth.role() = 'service_role');
        END IF;

        IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname = 'public' AND tablename = 'school_terms' AND policyname = 'school_terms_delete') THEN
            CREATE POLICY "school_terms_delete" ON school_terms
                FOR DELETE USING (auth.role() = 'service_role');
        END IF;
    END IF;
END $$;
