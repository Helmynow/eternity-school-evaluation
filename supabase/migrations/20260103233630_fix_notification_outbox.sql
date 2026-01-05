-- Migration: Add read_at to notification_outbox and update nav badge RPC
-- Date: 2026-01-04

BEGIN;

-- 1. Add read_at if missing
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'notification_outbox') THEN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'notification_outbox' AND column_name = 'read_at') THEN
      ALTER TABLE public.notification_outbox ADD COLUMN read_at TIMESTAMPTZ;
    END IF;
  END IF;
END $$;

-- 2. Update RPC to be safe
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
  -- Admissions
  SELECT count(*) INTO v_admissions
  FROM public.applications
  WHERE state IN ('docs_pending', 'assessment_scheduled', 'interview_scheduled', 'submitted');

  -- Finance
  SELECT count(*) INTO v_finance
  FROM public.applications
  WHERE state = 'fee_pending';

  -- Scheduling
  SELECT count(*) INTO v_scheduling
  FROM public.applications
  WHERE state = 'submitted';

  -- Decisions
  SELECT count(*) INTO v_decisions
  FROM public.applications
  WHERE state IN ('assessment_completed', 'interview_completed', 'under_review');

  -- Notifications
  -- Now we can safely check read_at
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

COMMIT;
