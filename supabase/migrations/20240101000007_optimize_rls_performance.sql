-- Optimize RLS Performance: Fix auth.role() calls and consolidate multiple policies
-- This migration addresses Supabase performance warnings

-- ============================================================================
-- FIX AUTH.ROLE() CALLS: Wrap in (select auth.role()) for better performance
-- ============================================================================

-- Drop and recreate policies with optimized auth.role() calls

-- Cycles policies
DROP POLICY IF EXISTS "Cycles are viewable by authenticated users" ON cycles;
DROP POLICY IF EXISTS "Cycles are insertable by service role" ON cycles;
DROP POLICY IF EXISTS "Cycles are updatable by service role" ON cycles;

CREATE POLICY "Cycles are viewable by authenticated users"
    ON cycles FOR SELECT
    USING ((select auth.role()) = 'authenticated');

CREATE POLICY "Cycles are insertable by service role"
    ON cycles FOR INSERT
    WITH CHECK ((select auth.role()) = 'service_role');

CREATE POLICY "Cycles are updatable by service role"
    ON cycles FOR UPDATE
    USING ((select auth.role()) = 'service_role');

-- People policies
DROP POLICY IF EXISTS "People are viewable by authenticated users" ON people;
DROP POLICY IF EXISTS "people_select_all" ON people;  -- Remove if exists from legacy
DROP POLICY IF EXISTS "People are insertable by service role" ON people;
DROP POLICY IF EXISTS "People are updatable by service role" ON people;

CREATE POLICY "People are viewable by authenticated users"
    ON people FOR SELECT
    USING ((select auth.role()) = 'authenticated');

CREATE POLICY "People are insertable by service role"
    ON people FOR INSERT
    WITH CHECK ((select auth.role()) = 'service_role');

CREATE POLICY "People are updatable by service role"
    ON people FOR UPDATE
    USING ((select auth.role()) = 'service_role');

-- Assignments policies
DROP POLICY IF EXISTS "Users can view their own assignments" ON assignments;
DROP POLICY IF EXISTS "Assignments are insertable by service role" ON assignments;
DROP POLICY IF EXISTS "Assignments are updatable by service role" ON assignments;

CREATE POLICY "Users can view their own assignments"
    ON assignments FOR SELECT
    USING (
        ((select auth.role()) = 'authenticated' AND (
            rater_email = (select auth.email()) OR 
            target_email = (select auth.email())
        )) OR (select auth.role()) = 'service_role'
    );

CREATE POLICY "Assignments are insertable by service role"
    ON assignments FOR INSERT
    WITH CHECK ((select auth.role()) = 'service_role');

CREATE POLICY "Assignments are updatable by service role"
    ON assignments FOR UPDATE
    USING ((select auth.role()) = 'service_role');

-- Evaluations policies
DROP POLICY IF EXISTS "Users can view evaluations for their assignments" ON evaluations;
DROP POLICY IF EXISTS "Users can create evaluations for their assignments" ON evaluations;
DROP POLICY IF EXISTS "Users can update their own evaluations" ON evaluations;

CREATE POLICY "Users can view evaluations for their assignments"
    ON evaluations FOR SELECT
    USING (
        (select auth.role()) = 'authenticated' AND (
            EXISTS (
                SELECT 1 FROM assignments a
                WHERE a.id = evaluations.assignment_id
                  AND (a.rater_email = (select auth.email()) OR a.target_email = (select auth.email()))
            )
        )
    ) OR (select auth.role()) = 'service_role';

CREATE POLICY "Users can create evaluations for their assignments"
    ON evaluations FOR INSERT
    WITH CHECK (
        ((select auth.role()) = 'authenticated' AND
        EXISTS (
            SELECT 1 FROM assignments a
            WHERE a.id = evaluations.assignment_id
              AND a.rater_email = (select auth.email())
        )) OR (select auth.role()) = 'service_role'
    );

CREATE POLICY "Users can update their own evaluations"
    ON evaluations FOR UPDATE
    USING (
        ((select auth.role()) = 'authenticated' AND
        EXISTS (
            SELECT 1 FROM assignments a
            WHERE a.id = evaluations.assignment_id
              AND a.rater_email = (select auth.email())
        )) OR (select auth.role()) = 'service_role'
    );

-- EOM Cycles policies - Separate SELECT from write operations
DROP POLICY IF EXISTS "EOM cycles are viewable by authenticated users" ON eom_cycles;
DROP POLICY IF EXISTS "EOM cycles are modifiable by service role" ON eom_cycles;

-- SELECT: authenticated users only (service_role bypasses RLS)
CREATE POLICY "EOM cycles are viewable by authenticated users"
    ON eom_cycles FOR SELECT
    USING ((select auth.role()) = 'authenticated');

-- Write operations: service_role only (INSERT/UPDATE/DELETE, not SELECT)
CREATE POLICY "EOM cycles are modifiable by service role"
    ON eom_cycles FOR INSERT, UPDATE, DELETE
    USING ((select auth.role()) = 'service_role')
    WITH CHECK ((select auth.role()) = 'service_role');

-- EOM Voters policies - Separate SELECT from write operations
DROP POLICY IF EXISTS "Users can view EOM voters" ON eom_voters;
DROP POLICY IF EXISTS "EOM voters are modifiable by service role" ON eom_voters;

-- SELECT: authenticated users only
CREATE POLICY "Users can view EOM voters"
    ON eom_voters FOR SELECT
    USING ((select auth.role()) = 'authenticated');

-- Write operations: service_role only
CREATE POLICY "EOM voters are modifiable by service role"
    ON eom_voters FOR INSERT, UPDATE, DELETE
    USING ((select auth.role()) = 'service_role')
    WITH CHECK ((select auth.role()) = 'service_role');

-- EOM Nominees policies
DROP POLICY IF EXISTS "EOM nominees are viewable by authenticated users" ON eom_nominees;
DROP POLICY IF EXISTS "Users can create nominations" ON eom_nominees;
DROP POLICY IF EXISTS "EOM nominees are updatable by service role" ON eom_nominees;

CREATE POLICY "EOM nominees are viewable by authenticated users"
    ON eom_nominees FOR SELECT
    USING ((select auth.role()) = 'authenticated');

CREATE POLICY "Users can create nominations"
    ON eom_nominees FOR INSERT
    WITH CHECK (
        ((select auth.role()) = 'authenticated' AND nominated_by = (select auth.email())) 
        OR (select auth.role()) = 'service_role'
    );

CREATE POLICY "EOM nominees are updatable by service role"
    ON eom_nominees FOR UPDATE
    USING ((select auth.role()) = 'service_role');

-- EOM Winners policies - Separate SELECT from write operations
DROP POLICY IF EXISTS "EOM winners are viewable by authenticated users" ON eom_winners;
DROP POLICY IF EXISTS "EOM winners are modifiable by service role" ON eom_winners;

-- SELECT: authenticated users only
CREATE POLICY "EOM winners are viewable by authenticated users"
    ON eom_winners FOR SELECT
    USING ((select auth.role()) = 'authenticated');

-- Write operations: service_role only
CREATE POLICY "EOM winners are modifiable by service role"
    ON eom_winners FOR INSERT, UPDATE, DELETE
    USING ((select auth.role()) = 'service_role')
    WITH CHECK ((select auth.role()) = 'service_role');

-- EOM Rotation Rules policies - Separate SELECT from write operations
DROP POLICY IF EXISTS "Rotation rules are viewable by authenticated users" ON eom_rotation_rules;
DROP POLICY IF EXISTS "Rotation rules are modifiable by service role" ON eom_rotation_rules;

-- SELECT: authenticated users only
CREATE POLICY "Rotation rules are viewable by authenticated users"
    ON eom_rotation_rules FOR SELECT
    USING ((select auth.role()) = 'authenticated');

-- Write operations: service_role only
CREATE POLICY "Rotation rules are modifiable by service role"
    ON eom_rotation_rules FOR INSERT, UPDATE, DELETE
    USING ((select auth.role()) = 'service_role')
    WITH CHECK ((select auth.role()) = 'service_role');

-- Weight Matrices policies - Separate SELECT from write operations
DROP POLICY IF EXISTS "Weight matrices are viewable by authenticated users" ON weight_matrices;
DROP POLICY IF EXISTS "Weight matrices are modifiable by service role" ON weight_matrices;

-- SELECT: authenticated users only
CREATE POLICY "Weight matrices are viewable by authenticated users"
    ON weight_matrices FOR SELECT
    USING ((select auth.role()) = 'authenticated');

-- Write operations: service_role only
CREATE POLICY "Weight matrices are modifiable by service role"
    ON weight_matrices FOR INSERT, UPDATE, DELETE
    USING ((select auth.role()) = 'service_role')
    WITH CHECK ((select auth.role()) = 'service_role');

-- Audit Logs policies
DROP POLICY IF EXISTS "Audit logs are viewable by service role only" ON audit_logs;
DROP POLICY IF EXISTS "Audit logs are insertable by service role" ON audit_logs;

CREATE POLICY "Audit logs are viewable by service role only"
    ON audit_logs FOR SELECT
    USING ((select auth.role()) = 'service_role');

CREATE POLICY "Audit logs are insertable by service role"
    ON audit_logs FOR INSERT
    WITH CHECK ((select auth.role()) = 'service_role');

-- ============================================================================
-- FIX POLICIES FOR LEGACY TABLES (if they exist)
-- ============================================================================

-- Fix eval_rater_rules policies (if table exists) - Separate SELECT from write operations
DO $$ 
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'eval_rater_rules') THEN
        DROP POLICY IF EXISTS "eval_rater_rules_select" ON eval_rater_rules;
        DROP POLICY IF EXISTS "eval_rater_rules_modify" ON eval_rater_rules;
        
        -- SELECT: authenticated users only
        CREATE POLICY "eval_rater_rules_select"
            ON eval_rater_rules FOR SELECT
            USING ((select auth.role()) = 'authenticated');
        
        -- Write operations: service_role only
        CREATE POLICY "eval_rater_rules_modify"
            ON eval_rater_rules FOR INSERT, UPDATE, DELETE
            USING ((select auth.role()) = 'service_role')
            WITH CHECK ((select auth.role()) = 'service_role');
    END IF;
END $$;

-- Fix eval_domain_rules policies (if table exists) - Separate SELECT from write operations
DO $$ 
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'eval_domain_rules') THEN
        DROP POLICY IF EXISTS "eval_domain_rules_select" ON eval_domain_rules;
        DROP POLICY IF EXISTS "eval_domain_rules_modify" ON eval_domain_rules;
        
        -- SELECT: authenticated users only
        CREATE POLICY "eval_domain_rules_select"
            ON eval_domain_rules FOR SELECT
            USING ((select auth.role()) = 'authenticated');
        
        -- Write operations: service_role only
        CREATE POLICY "eval_domain_rules_modify"
            ON eval_domain_rules FOR INSERT, UPDATE, DELETE
            USING ((select auth.role()) = 'service_role')
            WITH CHECK ((select auth.role()) = 'service_role');
    END IF;
END $$;

-- Fix voters policies (if table exists) - Separate SELECT from write operations
DO $$ 
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'voters') THEN
        DROP POLICY IF EXISTS "voters_select" ON voters;
        DROP POLICY IF EXISTS "voters_modify" ON voters;
        
        -- SELECT: authenticated users only
        CREATE POLICY "voters_select"
            ON voters FOR SELECT
            USING ((select auth.role()) = 'authenticated');
        
        -- Write operations: service_role only
        CREATE POLICY "voters_modify"
            ON voters FOR INSERT, UPDATE, DELETE
            USING ((select auth.role()) = 'service_role')
            WITH CHECK ((select auth.role()) = 'service_role');
    END IF;
END $$;

-- Fix winners policies (if table exists) - Separate SELECT from write operations
DO $$ 
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'winners') THEN
        DROP POLICY IF EXISTS "winners_select" ON winners;
        DROP POLICY IF EXISTS "winners_modify" ON winners;
        
        -- SELECT: authenticated users only
        CREATE POLICY "winners_select"
            ON winners FOR SELECT
            USING ((select auth.role()) = 'authenticated');
        
        -- Write operations: service_role only
        CREATE POLICY "winners_modify"
            ON winners FOR INSERT, UPDATE, DELETE
            USING ((select auth.role()) = 'service_role')
            WITH CHECK ((select auth.role()) = 'service_role');
    END IF;
END $$;

-- Fix school_terms policies (if table exists) - Separate SELECT from write operations
DO $$ 
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'school_terms') THEN
        DROP POLICY IF EXISTS "school_terms_select" ON school_terms;
        DROP POLICY IF EXISTS "school_terms_modify" ON school_terms;
        
        -- SELECT: authenticated users only
        CREATE POLICY "school_terms_select"
            ON school_terms FOR SELECT
            USING ((select auth.role()) = 'authenticated');
        
        -- Write operations: service_role only
        CREATE POLICY "school_terms_modify"
            ON school_terms FOR INSERT, UPDATE, DELETE
            USING ((select auth.role()) = 'service_role')
            WITH CHECK ((select auth.role()) = 'service_role');
    END IF;
END $$;

-- ============================================================================
-- FIX DUPLICATE PEOPLE SELECT POLICY
-- ============================================================================

-- Remove duplicate people_select_all policy if it exists
DROP POLICY IF EXISTS "people_select_all" ON people;

