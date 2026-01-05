-- Migration: Dashboard Data Consolidation & Realtime
-- Date: 2026-01-04
-- Description: Consolidated RPCs for dashboard stats and nav badges

BEGIN;

-- 1. Dashboard Stats RPC
CREATE OR REPLACE FUNCTION public.get_dashboard_stats()
RETURNS jsonb
LANGUAGE plpgsql
STABLE
SECURITY INVOKER
SET search_path = ''
AS $$
DECLARE
  v_docs_pending int;
  v_interviews_pending int;
  v_decisions_pending int;
  v_payments_pending int;
  v_sla_urgent int;
  v_sla_overdue int;
  v_total_active int;
BEGIN
  -- docs_pending
  SELECT count(*) INTO v_docs_pending
  FROM public.applications
  WHERE state = 'docs_pending';

  -- interviews_pending
  SELECT count(*) INTO v_interviews_pending
  FROM public.applications
  WHERE state IN ('assessment_scheduled', 'interview_scheduled');

  -- decisions_pending
  SELECT count(*) INTO v_decisions_pending
  FROM public.applications
  WHERE state IN ('assessment_completed', 'interview_completed', 'under_review');

  -- payments_pending
  SELECT count(*) INTO v_payments_pending
  FROM public.applications
  WHERE state = 'fee_pending';

  -- SLA metrics (using sla_status column if available, else 0)
  -- We assume columns exist based on previous analysis.
  SELECT count(*) INTO v_sla_urgent
  FROM public.applications
  WHERE sla_status = 'warning';

  SELECT count(*) INTO v_sla_overdue
  FROM public.applications
  WHERE sla_status = 'breached';

  -- Total active
  SELECT count(*) INTO v_total_active
  FROM public.applications
  WHERE COALESCE(state, status) NOT IN ('draft', 'withdrawn', 'declined', 'enrolled', 'closed');

  RETURN jsonb_build_object(
    'docs_pending', v_docs_pending,
    'interviews_pending', v_interviews_pending,
    'decisions_pending', v_decisions_pending,
    'payments_pending', v_payments_pending,
    'sla_urgent', v_sla_urgent,
    'sla_overdue', v_sla_overdue,
    'total_active', v_total_active,
    'fetched_at', now()
  );
END;
$$;

-- 2. Nav Badge Counts RPC
CREATE OR REPLACE FUNCTION public.get_nav_badge_counts()
RETURNS jsonb
LANGUAGE plpgsql
STABLE
SECURITY INVOKER
SET search_path = ''
AS $$
DECLARE
  v_admissions int;
  v_finance int;
  v_scheduling int;
  v_decisions int;
  v_notifications int;
BEGIN
  -- Admissions: Docs + Interviews (Assessment/Interview Scheduled) + Submitted (needs scheduling)
  SELECT count(*) INTO v_admissions
  FROM public.applications
  WHERE state IN ('docs_pending', 'assessment_scheduled', 'interview_scheduled', 'submitted');

  -- Finance: Fee Pending
  SELECT count(*) INTO v_finance
  FROM public.applications
  WHERE state = 'fee_pending';

  -- Scheduling: Submitted (needs scheduling)
  SELECT count(*) INTO v_scheduling
  FROM public.applications
  WHERE state = 'submitted';

  -- Decisions: Assessment Completed / Under Review
  SELECT count(*) INTO v_decisions
  FROM public.applications
  WHERE state IN ('assessment_completed', 'interview_completed', 'under_review');

  -- Notifications: Unread in_app notifications
  -- Using notification_outbox as per NotificationBell.tsx
  SELECT count(*) INTO v_notifications
  FROM public.notification_outbox
  WHERE user_id = auth.uid()
    AND channel = 'in_app'
    AND read_at IS NULL;

  RETURN jsonb_build_object(
    'admissions', v_admissions,
    'finance', v_finance,
    'scheduling', v_scheduling,
    'decisions', v_decisions,
    'notifications', v_notifications,
    'fetched_at', now()
  );
END;
$$;

GRANT EXECUTE ON FUNCTION public.get_dashboard_stats() TO authenticated;
GRANT EXECUTE ON FUNCTION public.get_nav_badge_counts() TO authenticated;

COMMIT;
