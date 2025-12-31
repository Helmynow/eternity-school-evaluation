-- Fix Multiple Permissive Policies: Separate SELECT from write operations
-- This migration addresses Supabase performance warnings about overlapping policies
-- Strategy: SELECT policies only for authenticated, write policies only for service_role
-- Service role bypasses RLS when using service key, so no need to include in SELECT policies

-- ============================================================================
-- FIX EOM CYCLES: Separate SELECT from write operations
-- ============================================================================

DROP POLICY IF EXISTS "EOM cycles are viewable by authenticated users" ON eom_cycles;
DROP POLICY IF EXISTS "EOM cycles are modifiable by service role" ON eom_cycles;
DROP POLICY IF EXISTS "EOM cycles are insertable by service role" ON eom_cycles;
DROP POLICY IF EXISTS "EOM cycles are updatable by service role" ON eom_cycles;
DROP POLICY IF EXISTS "EOM cycles are deletable by service role" ON eom_cycles;

-- SELECT: authenticated users only (service_role bypasses RLS)
CREATE POLICY "EOM cycles are viewable by authenticated users"
    ON eom_cycles FOR SELECT
    USING ((select auth.role()) = 'authenticated');

-- Write operations: service_role only (separate policies for each operation)
CREATE POLICY "EOM cycles are insertable by service role"
    ON eom_cycles FOR INSERT
    WITH CHECK ((select auth.role()) = 'service_role');

CREATE POLICY "EOM cycles are updatable by service role"
    ON eom_cycles FOR UPDATE
    USING ((select auth.role()) = 'service_role')
    WITH CHECK ((select auth.role()) = 'service_role');

CREATE POLICY "EOM cycles are deletable by service role"
    ON eom_cycles FOR DELETE
    USING ((select auth.role()) = 'service_role');

-- ============================================================================
-- FIX EOM VOTERS: Separate SELECT from write operations
-- ============================================================================

DROP POLICY IF EXISTS "Users can view EOM voters" ON eom_voters;
DROP POLICY IF EXISTS "EOM voters are modifiable by service role" ON eom_voters;
DROP POLICY IF EXISTS "EOM voters are insertable by service role" ON eom_voters;
DROP POLICY IF EXISTS "EOM voters are updatable by service role" ON eom_voters;
DROP POLICY IF EXISTS "EOM voters are deletable by service role" ON eom_voters;

-- SELECT: authenticated users only
CREATE POLICY "Users can view EOM voters"
    ON eom_voters FOR SELECT
    USING ((select auth.role()) = 'authenticated');

-- Write operations: service_role only
CREATE POLICY "EOM voters are insertable by service role"
    ON eom_voters FOR INSERT
    WITH CHECK ((select auth.role()) = 'service_role');

CREATE POLICY "EOM voters are updatable by service role"
    ON eom_voters FOR UPDATE
    USING ((select auth.role()) = 'service_role')
    WITH CHECK ((select auth.role()) = 'service_role');

CREATE POLICY "EOM voters are deletable by service role"
    ON eom_voters FOR DELETE
    USING ((select auth.role()) = 'service_role');

-- ============================================================================
-- FIX EOM WINNERS: Separate SELECT from write operations
-- ============================================================================

DROP POLICY IF EXISTS "EOM winners are viewable by authenticated users" ON eom_winners;
DROP POLICY IF EXISTS "EOM winners are modifiable by service role" ON eom_winners;
DROP POLICY IF EXISTS "EOM winners are insertable by service role" ON eom_winners;
DROP POLICY IF EXISTS "EOM winners are updatable by service role" ON eom_winners;
DROP POLICY IF EXISTS "EOM winners are deletable by service role" ON eom_winners;

-- SELECT: authenticated users only
CREATE POLICY "EOM winners are viewable by authenticated users"
    ON eom_winners FOR SELECT
    USING ((select auth.role()) = 'authenticated');

-- Write operations: service_role only
CREATE POLICY "EOM winners are insertable by service role"
    ON eom_winners FOR INSERT
    WITH CHECK ((select auth.role()) = 'service_role');

CREATE POLICY "EOM winners are updatable by service role"
    ON eom_winners FOR UPDATE
    USING ((select auth.role()) = 'service_role')
    WITH CHECK ((select auth.role()) = 'service_role');

CREATE POLICY "EOM winners are deletable by service role"
    ON eom_winners FOR DELETE
    USING ((select auth.role()) = 'service_role');

-- ============================================================================
-- FIX EOM ROTATION RULES: Separate SELECT from write operations
-- ============================================================================

DROP POLICY IF EXISTS "Rotation rules are viewable by authenticated users" ON eom_rotation_rules;
DROP POLICY IF EXISTS "Rotation rules are modifiable by service role" ON eom_rotation_rules;
DROP POLICY IF EXISTS "Rotation rules are insertable by service role" ON eom_rotation_rules;
DROP POLICY IF EXISTS "Rotation rules are updatable by service role" ON eom_rotation_rules;
DROP POLICY IF EXISTS "Rotation rules are deletable by service role" ON eom_rotation_rules;

-- SELECT: authenticated users only
CREATE POLICY "Rotation rules are viewable by authenticated users"
    ON eom_rotation_rules FOR SELECT
    USING ((select auth.role()) = 'authenticated');

-- Write operations: service_role only
CREATE POLICY "Rotation rules are insertable by service role"
    ON eom_rotation_rules FOR INSERT
    WITH CHECK ((select auth.role()) = 'service_role');

CREATE POLICY "Rotation rules are updatable by service role"
    ON eom_rotation_rules FOR UPDATE
    USING ((select auth.role()) = 'service_role')
    WITH CHECK ((select auth.role()) = 'service_role');

CREATE POLICY "Rotation rules are deletable by service role"
    ON eom_rotation_rules FOR DELETE
    USING ((select auth.role()) = 'service_role');

-- ============================================================================
-- FIX WEIGHT MATRICES: Separate SELECT from write operations
-- ============================================================================

DROP POLICY IF EXISTS "Weight matrices are viewable by authenticated users" ON weight_matrices;
DROP POLICY IF EXISTS "Weight matrices are modifiable by service role" ON weight_matrices;
DROP POLICY IF EXISTS "Weight matrices are insertable by service role" ON weight_matrices;
DROP POLICY IF EXISTS "Weight matrices are updatable by service role" ON weight_matrices;
DROP POLICY IF EXISTS "Weight matrices are deletable by service role" ON weight_matrices;

-- SELECT: authenticated users only
CREATE POLICY "Weight matrices are viewable by authenticated users"
    ON weight_matrices FOR SELECT
    USING ((select auth.role()) = 'authenticated');

-- Write operations: service_role only
CREATE POLICY "Weight matrices are insertable by service role"
    ON weight_matrices FOR INSERT
    WITH CHECK ((select auth.role()) = 'service_role');

CREATE POLICY "Weight matrices are updatable by service role"
    ON weight_matrices FOR UPDATE
    USING ((select auth.role()) = 'service_role')
    WITH CHECK ((select auth.role()) = 'service_role');

CREATE POLICY "Weight matrices are deletable by service role"
    ON weight_matrices FOR DELETE
    USING ((select auth.role()) = 'service_role');

-- ============================================================================
-- FIX LEGACY TABLES: Separate SELECT from write operations
-- ============================================================================

-- Fix eval_rater_rules policies (if table exists)
DO $$ 
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'eval_rater_rules') THEN
        DROP POLICY IF EXISTS "eval_rater_rules_select" ON eval_rater_rules;
        DROP POLICY IF EXISTS "eval_rater_rules_modify" ON eval_rater_rules;
        DROP POLICY IF EXISTS "eval_rater_rules_insert" ON eval_rater_rules;
        DROP POLICY IF EXISTS "eval_rater_rules_update" ON eval_rater_rules;
        DROP POLICY IF EXISTS "eval_rater_rules_delete" ON eval_rater_rules;
        
        -- SELECT: authenticated users only
        CREATE POLICY "eval_rater_rules_select"
            ON eval_rater_rules FOR SELECT
            USING ((select auth.role()) = 'authenticated');
        
        -- Write operations: service_role only
        CREATE POLICY "eval_rater_rules_insert"
            ON eval_rater_rules FOR INSERT
            WITH CHECK ((select auth.role()) = 'service_role');
        
        CREATE POLICY "eval_rater_rules_update"
            ON eval_rater_rules FOR UPDATE
            USING ((select auth.role()) = 'service_role')
            WITH CHECK ((select auth.role()) = 'service_role');
        
        CREATE POLICY "eval_rater_rules_delete"
            ON eval_rater_rules FOR DELETE
            USING ((select auth.role()) = 'service_role');
    END IF;
END $$;

-- Fix eval_domain_rules policies (if table exists)
DO $$ 
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'eval_domain_rules') THEN
        DROP POLICY IF EXISTS "eval_domain_rules_select" ON eval_domain_rules;
        DROP POLICY IF EXISTS "eval_domain_rules_modify" ON eval_domain_rules;
        DROP POLICY IF EXISTS "eval_domain_rules_insert" ON eval_domain_rules;
        DROP POLICY IF EXISTS "eval_domain_rules_update" ON eval_domain_rules;
        DROP POLICY IF EXISTS "eval_domain_rules_delete" ON eval_domain_rules;
        
        -- SELECT: authenticated users only
        CREATE POLICY "eval_domain_rules_select"
            ON eval_domain_rules FOR SELECT
            USING ((select auth.role()) = 'authenticated');
        
        -- Write operations: service_role only
        CREATE POLICY "eval_domain_rules_insert"
            ON eval_domain_rules FOR INSERT
            WITH CHECK ((select auth.role()) = 'service_role');
        
        CREATE POLICY "eval_domain_rules_update"
            ON eval_domain_rules FOR UPDATE
            USING ((select auth.role()) = 'service_role')
            WITH CHECK ((select auth.role()) = 'service_role');
        
        CREATE POLICY "eval_domain_rules_delete"
            ON eval_domain_rules FOR DELETE
            USING ((select auth.role()) = 'service_role');
    END IF;
END $$;

-- Fix voters policies (if table exists)
DO $$ 
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'voters') THEN
        DROP POLICY IF EXISTS "voters_select" ON voters;
        DROP POLICY IF EXISTS "voters_modify" ON voters;
        DROP POLICY IF EXISTS "voters_insert" ON voters;
        DROP POLICY IF EXISTS "voters_update" ON voters;
        DROP POLICY IF EXISTS "voters_delete" ON voters;
        
        -- SELECT: authenticated users only
        CREATE POLICY "voters_select"
            ON voters FOR SELECT
            USING ((select auth.role()) = 'authenticated');
        
        -- Write operations: service_role only
        CREATE POLICY "voters_insert"
            ON voters FOR INSERT
            WITH CHECK ((select auth.role()) = 'service_role');
        
        CREATE POLICY "voters_update"
            ON voters FOR UPDATE
            USING ((select auth.role()) = 'service_role')
            WITH CHECK ((select auth.role()) = 'service_role');
        
        CREATE POLICY "voters_delete"
            ON voters FOR DELETE
            USING ((select auth.role()) = 'service_role');
    END IF;
END $$;

-- Fix winners policies (if table exists)
DO $$ 
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'winners') THEN
        DROP POLICY IF EXISTS "winners_select" ON winners;
        DROP POLICY IF EXISTS "winners_modify" ON winners;
        DROP POLICY IF EXISTS "winners_insert" ON winners;
        DROP POLICY IF EXISTS "winners_update" ON winners;
        DROP POLICY IF EXISTS "winners_delete" ON winners;
        
        -- SELECT: authenticated users only
        CREATE POLICY "winners_select"
            ON winners FOR SELECT
            USING ((select auth.role()) = 'authenticated');
        
        -- Write operations: service_role only
        CREATE POLICY "winners_insert"
            ON winners FOR INSERT
            WITH CHECK ((select auth.role()) = 'service_role');
        
        CREATE POLICY "winners_update"
            ON winners FOR UPDATE
            USING ((select auth.role()) = 'service_role')
            WITH CHECK ((select auth.role()) = 'service_role');
        
        CREATE POLICY "winners_delete"
            ON winners FOR DELETE
            USING ((select auth.role()) = 'service_role');
    END IF;
END $$;

-- Fix school_terms policies (if table exists)
DO $$ 
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'school_terms') THEN
        DROP POLICY IF EXISTS "school_terms_select" ON school_terms;
        DROP POLICY IF EXISTS "school_terms_modify" ON school_terms;
        DROP POLICY IF EXISTS "school_terms_insert" ON school_terms;
        DROP POLICY IF EXISTS "school_terms_update" ON school_terms;
        DROP POLICY IF EXISTS "school_terms_delete" ON school_terms;
        
        -- SELECT: authenticated users only
        CREATE POLICY "school_terms_select"
            ON school_terms FOR SELECT
            USING ((select auth.role()) = 'authenticated');
        
        -- Write operations: service_role only
        CREATE POLICY "school_terms_insert"
            ON school_terms FOR INSERT
            WITH CHECK ((select auth.role()) = 'service_role');
        
        CREATE POLICY "school_terms_update"
            ON school_terms FOR UPDATE
            USING ((select auth.role()) = 'service_role')
            WITH CHECK ((select auth.role()) = 'service_role');
        
        CREATE POLICY "school_terms_delete"
            ON school_terms FOR DELETE
            USING ((select auth.role()) = 'service_role');
    END IF;
END $$;

-- ============================================================================
-- FIX DUPLICATE PEOPLE SELECT POLICY
-- ============================================================================

-- Remove duplicate people_select_all policy if it exists
DROP POLICY IF EXISTS "people_select_all" ON people;

