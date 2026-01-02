-- Fix Function Search Path Security
-- Set search_path for all functions to prevent search path manipulation attacks
-- Using ALTER FUNCTION to ensure search_path is properly set

-- ============================================================================
-- SET SEARCH_PATH FOR ALL FUNCTIONS
-- ============================================================================

-- According to Supabase best practices, we should use SET search_path = ''
-- However, since our functions reference tables in the public schema,
-- we'll use SET search_path = public to maintain functionality while
-- preventing search path manipulation attacks

-- update_updated_at_column (trigger function, no arguments)
ALTER FUNCTION update_updated_at_column() SET search_path = public;

-- calculate_weighted_score
ALTER FUNCTION calculate_weighted_score(integer, character varying) SET search_path = public;

-- get_cycle_statistics
ALTER FUNCTION get_cycle_statistics(integer) SET search_path = public;

-- check_eom_eligibility
ALTER FUNCTION check_eom_eligibility(character varying, integer, eom_category) SET search_path = public;

-- get_eom_cycle_stats
ALTER FUNCTION get_eom_cycle_stats(integer) SET search_path = public;

-- validate_evaluation_requirements
ALTER FUNCTION validate_evaluation_requirements(integer, character varying, integer) SET search_path = public;

-- get_staff_count_by_segment (no arguments)
ALTER FUNCTION get_staff_count_by_segment() SET search_path = public;

-- get_cycle_completion_status
ALTER FUNCTION get_cycle_completion_status(integer) SET search_path = public;

