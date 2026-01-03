-- Fix Function Search Path Mutable warnings for SLA/decision helpers
-- Set search_path for functions if they exist (schema-tolerant)

DO $$
DECLARE
    r RECORD;
BEGIN
    FOR r IN
        SELECT n.nspname AS schema_name,
               p.proname AS func_name,
               pg_get_function_identity_arguments(p.oid) AS args
        FROM pg_proc p
        JOIN pg_namespace n ON n.oid = p.pronamespace
        WHERE n.nspname = 'public'
          AND p.proname IN ('should_start_sla_timer', 'map_decision_type_to_state')
    LOOP
        EXECUTE format('ALTER FUNCTION %I.%I(%s) SET search_path = public', r.schema_name, r.func_name, r.args);
    END LOOP;
END $$;
