-- Explicitly Set Security Invoker on All Views
-- This migration uses PostgreSQL 15+ syntax to explicitly set security_invoker
-- on all views to resolve Supabase security advisor warnings

-- ============================================================================
-- SET SECURITY INVOKER ON ALL VIEWS
-- ============================================================================

-- In PostgreSQL 15+, we can use ALTER VIEW to set security_invoker
-- This ensures views respect RLS policies of the querying user

ALTER VIEW mre_who_evaluates_who SET (security_invoker = true);
ALTER VIEW mre_evaluation_summary SET (security_invoker = true);
ALTER VIEW eom_participants SET (security_invoker = true);
ALTER VIEW eom_nomination_summary SET (security_invoker = true);
ALTER VIEW eom_winner_history SET (security_invoker = true);
ALTER VIEW weighted_score_summary SET (security_invoker = true);
ALTER VIEW recent_audit_logs SET (security_invoker = true);

