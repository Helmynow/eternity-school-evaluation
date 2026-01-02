-- Fix Function Search Path Mutable warnings
-- Set search_path for survey/identity/admin functions to prevent manipulation

-- ============================================================================
-- SURVEY RESPONSE & NOTIFICATION FUNCTIONS
-- ============================================================================

DO $$ BEGIN
    IF to_regprocedure('public.aggregate_survey_responses(integer, integer)') IS NOT NULL THEN
        EXECUTE 'ALTER FUNCTION public.aggregate_survey_responses(integer, integer) SET search_path = public';
    END IF;
    IF to_regprocedure('public.get_survey_response_stats(integer)') IS NOT NULL THEN
        EXECUTE 'ALTER FUNCTION public.get_survey_response_stats(integer) SET search_path = public';
    END IF;
    IF to_regprocedure('public.notify_survey_response_submitted()') IS NOT NULL THEN
        EXECUTE 'ALTER FUNCTION public.notify_survey_response_submitted() SET search_path = public';
    END IF;
    IF to_regprocedure('public.notify_objection_submitted()') IS NOT NULL THEN
        EXECUTE 'ALTER FUNCTION public.notify_objection_submitted() SET search_path = public';
    END IF;
END $$;

-- ============================================================================
-- ANONYMOUS DATA CLEANUP
-- ============================================================================

DO $$ BEGIN
    IF to_regprocedure('public.cleanup_expired_anonymous_responses()') IS NOT NULL THEN
        EXECUTE 'ALTER FUNCTION public.cleanup_expired_anonymous_responses() SET search_path = public';
    END IF;
    IF to_regprocedure('public.cleanup_expired_anonymous_data_by_preference()') IS NOT NULL THEN
        EXECUTE 'ALTER FUNCTION public.cleanup_expired_anonymous_data_by_preference() SET search_path = public';
    END IF;
END $$;

-- ============================================================================
-- IDENTITY TRANSITION
-- ============================================================================

DO $$ BEGIN
    IF to_regprocedure('public.link_anonymous_responses(character varying, character varying, integer)') IS NOT NULL THEN
        EXECUTE 'ALTER FUNCTION public.link_anonymous_responses(character varying, character varying, integer) SET search_path = public';
    END IF;
    IF to_regprocedure('public.transition_survey_identity(character varying, integer, character varying, character varying)') IS NOT NULL THEN
        EXECUTE 'ALTER FUNCTION public.transition_survey_identity(character varying, integer, character varying, character varying) SET search_path = public';
    END IF;
    IF to_regprocedure('public.get_identity_transition_status(character varying, integer)') IS NOT NULL THEN
        EXECUTE 'ALTER FUNCTION public.get_identity_transition_status(character varying, integer) SET search_path = public';
    END IF;
END $$;

-- ============================================================================
-- SUPER ADMIN BOOTSTRAP HELPERS
-- ============================================================================

DO $$ BEGIN
    IF to_regprocedure('public.ese_first_ceo_email()') IS NOT NULL THEN
        EXECUTE 'ALTER FUNCTION public.ese_first_ceo_email() SET search_path = public';
    END IF;
    IF to_regprocedure('public.ese_is_super_admin()') IS NOT NULL THEN
        EXECUTE 'ALTER FUNCTION public.ese_is_super_admin() SET search_path = public';
    END IF;
END $$;

-- ============================================================================
-- UPDATED_AT TRIGGER HELPERS
-- ============================================================================

DO $$ BEGIN
    IF to_regprocedure('public.update_survey_identity_preferences_updated_at()') IS NOT NULL THEN
        EXECUTE 'ALTER FUNCTION public.update_survey_identity_preferences_updated_at() SET search_path = public';
    END IF;
    IF to_regprocedure('public.update_survey_conditional_reveals_updated_at()') IS NOT NULL THEN
        EXECUTE 'ALTER FUNCTION public.update_survey_conditional_reveals_updated_at() SET search_path = public';
    END IF;
    IF to_regprocedure('public.update_updated_at_column()') IS NOT NULL THEN
        EXECUTE 'ALTER FUNCTION public.update_updated_at_column() SET search_path = public';
    END IF;
    IF to_regprocedure('public.update_surveys_updated_at()') IS NOT NULL THEN
        EXECUTE 'ALTER FUNCTION public.update_surveys_updated_at() SET search_path = public';
    END IF;
    IF to_regprocedure('public.update_survey_questions_updated_at()') IS NOT NULL THEN
        EXECUTE 'ALTER FUNCTION public.update_survey_questions_updated_at() SET search_path = public';
    END IF;
    IF to_regprocedure('public.update_objections_updated_at()') IS NOT NULL THEN
        EXECUTE 'ALTER FUNCTION public.update_objections_updated_at() SET search_path = public';
    END IF;
    IF to_regprocedure('public.update_feedback_updated_at()') IS NOT NULL THEN
        EXECUTE 'ALTER FUNCTION public.update_feedback_updated_at() SET search_path = public';
    END IF;
END $$;

-- ============================================================================
-- VOTE WEIGHT DEFAULTS
-- ============================================================================

DO $$ BEGIN
    IF to_regprocedure('public.set_default_vote_weights()') IS NOT NULL THEN
        EXECUTE 'ALTER FUNCTION public.set_default_vote_weights() SET search_path = public';
    END IF;
END $$;
