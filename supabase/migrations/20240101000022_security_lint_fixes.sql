-- Security lint fixes: enforce SECURITY INVOKER on views + enable RLS on missing tables

-- ============================================================================
-- 1) Views should be SECURITY INVOKER (not SECURITY DEFINER)
-- ============================================================================

ALTER VIEW IF EXISTS public.eom_diversity_tracking SET (security_invoker = true);
ALTER VIEW IF EXISTS public.eom_hall_of_fame SET (security_invoker = true);

-- ============================================================================
-- 2) Enable RLS on public tables flagged by linter
-- ============================================================================

ALTER TABLE IF EXISTS public.eom_feedback ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.email_notifications ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- 3) RLS policies for eom_feedback (allow owners, super admin, service role)
-- ============================================================================

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public'
          AND tablename = 'eom_feedback'
          AND policyname = 'EOM feedback is viewable by owner'
    ) THEN
        CREATE POLICY "EOM feedback is viewable by owner"
            ON public.eom_feedback FOR SELECT
            USING (
                (SELECT auth.email()) = person_email
                OR ese_is_super_admin()
                OR (SELECT auth.role()) = 'service_role'
            );
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public'
          AND tablename = 'eom_feedback'
          AND policyname = 'EOM feedback can be submitted by authenticated users'
    ) THEN
        CREATE POLICY "EOM feedback can be submitted by authenticated users"
            ON public.eom_feedback FOR INSERT
            WITH CHECK (
                (SELECT auth.email()) = person_email
                OR (SELECT auth.role()) = 'service_role'
            );
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public'
          AND tablename = 'eom_feedback'
          AND policyname = 'EOM feedback is manageable by super admin'
    ) THEN
        CREATE POLICY "EOM feedback is manageable by super admin"
            ON public.eom_feedback FOR UPDATE
            USING (
                ese_is_super_admin()
                OR (SELECT auth.role()) = 'service_role'
            )
            WITH CHECK (
                ese_is_super_admin()
                OR (SELECT auth.role()) = 'service_role'
            );
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public'
          AND tablename = 'eom_feedback'
          AND policyname = 'EOM feedback is deletable by super admin'
    ) THEN
        CREATE POLICY "EOM feedback is deletable by super admin"
            ON public.eom_feedback FOR DELETE
            USING (
                ese_is_super_admin()
                OR (SELECT auth.role()) = 'service_role'
            );
    END IF;
END $$;

-- ============================================================================
-- 4) RLS policies for email_notifications (admin/service-only)
-- ============================================================================

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public'
          AND tablename = 'email_notifications'
          AND policyname = 'Email notifications are viewable by super admin'
    ) THEN
        CREATE POLICY "Email notifications are viewable by super admin"
            ON public.email_notifications FOR SELECT
            USING (
                ese_is_super_admin()
                OR (SELECT auth.role()) = 'service_role'
            );
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public'
          AND tablename = 'email_notifications'
          AND policyname = 'Email notifications are manageable by service role'
    ) THEN
        CREATE POLICY "Email notifications are manageable by service role"
            ON public.email_notifications FOR ALL
            USING (
                (SELECT auth.role()) = 'service_role'
                OR ese_is_super_admin()
            )
            WITH CHECK (
                (SELECT auth.role()) = 'service_role'
                OR ese_is_super_admin()
            );
    END IF;
END $$;
