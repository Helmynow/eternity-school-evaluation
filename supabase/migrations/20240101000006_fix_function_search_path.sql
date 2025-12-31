-- Fix Function Search Path Security Issue
-- Set search_path for all functions to prevent security vulnerabilities

-- ============================================================================
-- UPDATE EXISTING FUNCTIONS WITH SECURE SEARCH_PATH
-- ============================================================================

-- Update update_updated_at_column function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER 
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$;

-- Update calculate_weighted_score function
CREATE OR REPLACE FUNCTION calculate_weighted_score(
    p_cycle_id INTEGER,
    p_target_email VARCHAR(255)
)
RETURNS TABLE (
    target_email VARCHAR(255),
    total_evaluations BIGINT,
    raw_average NUMERIC,
    weighted_average NUMERIC,
    weighted_sum NUMERIC,
    total_weight NUMERIC
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
    RETURN QUERY
    SELECT
        a.target_email,
        COUNT(e.id)::BIGINT AS total_evaluations,
        AVG(e.rating)::NUMERIC AS raw_average,
        (SUM(e.rating * a.weight) / NULLIF(SUM(a.weight), 0))::NUMERIC AS weighted_average,
        SUM(e.rating * a.weight)::NUMERIC AS weighted_sum,
        SUM(a.weight)::NUMERIC AS total_weight
    FROM assignments a
    LEFT JOIN evaluations e ON e.assignment_id = a.id
    WHERE a.cycle_id = p_cycle_id
      AND a.target_email = p_target_email
      AND e.status = 'submitted'
      AND e.rating IS NOT NULL
    GROUP BY a.target_email;
END;
$$;

-- Update get_cycle_statistics function
CREATE OR REPLACE FUNCTION get_cycle_statistics(
    p_cycle_id INTEGER
)
RETURNS TABLE (
    total_assignments BIGINT,
    total_evaluations BIGINT,
    submitted_evaluations BIGINT,
    average_rating NUMERIC,
    average_weighted_rating NUMERIC,
    completion_rate NUMERIC
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
    RETURN QUERY
    SELECT
        COUNT(DISTINCT a.id)::BIGINT AS total_assignments,
        COUNT(e.id)::BIGINT AS total_evaluations,
        COUNT(CASE WHEN e.status = 'submitted' THEN 1 END)::BIGINT AS submitted_evaluations,
        AVG(CASE WHEN e.status = 'submitted' THEN e.rating END)::NUMERIC AS average_rating,
        AVG(CASE WHEN e.status = 'submitted' THEN e.weighted_rating END)::NUMERIC AS average_weighted_rating,
        (COUNT(CASE WHEN e.status = 'submitted' THEN 1 END)::NUMERIC / 
         NULLIF(COUNT(DISTINCT a.id), 0) * 100)::NUMERIC AS completion_rate
    FROM assignments a
    LEFT JOIN evaluations e ON e.assignment_id = a.id
    WHERE a.cycle_id = p_cycle_id;
END;
$$;

-- Update check_eom_eligibility function
CREATE OR REPLACE FUNCTION check_eom_eligibility(
    p_nominee_email VARCHAR(255),
    p_eom_cycle_id INTEGER,
    p_category eom_category
)
RETURNS TABLE (
    is_eligible BOOLEAN,
    reason TEXT
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    v_last_won_cycle_id INTEGER;
    v_cooldown_period INTEGER;
    v_rule_exists BOOLEAN;
    v_max_wins INTEGER;
    v_current_wins INTEGER;
    v_cycle_month INTEGER;
    v_cycle_year INTEGER;
BEGIN
    -- Get cycle info
    SELECT month, year INTO v_cycle_month, v_cycle_year
    FROM eom_cycles WHERE id = p_eom_cycle_id;
    
    -- Check if rotation rule exists
    SELECT EXISTS(
        SELECT 1 FROM eom_rotation_rules
        WHERE category = p_category
          AND is_active = TRUE
    ) INTO v_rule_exists;
    
    IF NOT v_rule_exists THEN
        RETURN QUERY SELECT TRUE, 'No rotation rule for this category'::TEXT;
        RETURN;
    END IF;
    
    -- Get rotation rule
    SELECT cooldown_period, max_wins_per_period INTO v_cooldown_period, v_max_wins
    FROM eom_rotation_rules
    WHERE category = p_category
      AND is_active = TRUE
    LIMIT 1;
    
    -- Check last win
    SELECT last_won_cycle_id INTO v_last_won_cycle_id
    FROM eom_nominees
    WHERE nominee_email = p_nominee_email
      AND category = p_category
    ORDER BY last_won_cycle_id DESC NULLS LAST
    LIMIT 1;
    
    -- Check cooldown period
    IF v_last_won_cycle_id IS NOT NULL THEN
        DECLARE
            v_last_won_month INTEGER;
            v_last_won_year INTEGER;
            v_months_since_win INTEGER;
        BEGIN
            SELECT month, year INTO v_last_won_month, v_last_won_year
            FROM eom_cycles WHERE id = v_last_won_cycle_id;
            
            v_months_since_win := (v_cycle_year - v_last_won_year) * 12 + (v_cycle_month - v_last_won_month);
            
            IF v_months_since_win < v_cooldown_period THEN
                RETURN QUERY SELECT FALSE, 
                    format('Still in cooldown period. %s months since last win, %s months required', 
                           v_months_since_win, v_cooldown_period)::TEXT;
                RETURN;
            END IF;
        END;
    END IF;
    
    -- Check max wins per period
    SELECT COUNT(*) INTO v_current_wins
    FROM eom_winners w
    JOIN eom_cycles ec ON ec.id = w.eom_cycle_id
    WHERE w.winner_email = p_nominee_email
      AND w.category = p_category::VARCHAR
      AND ec.year = v_cycle_year;
    
    IF v_current_wins >= v_max_wins THEN
        RETURN QUERY SELECT FALSE, 
            format('Maximum wins per period exceeded. Current wins: %s, Max: %s', 
                   v_current_wins, v_max_wins)::TEXT;
        RETURN;
    END IF;
    
    RETURN QUERY SELECT TRUE, 'Eligible for nomination'::TEXT;
END;
$$;

-- Update get_eom_cycle_stats function
CREATE OR REPLACE FUNCTION get_eom_cycle_stats(
    p_eom_cycle_id INTEGER
)
RETURNS TABLE (
    total_voters BIGINT,
    total_nominees BIGINT,
    total_votes BIGINT,
    categories_count BIGINT,
    avg_votes_per_nominee NUMERIC
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
    RETURN QUERY
    SELECT
        COUNT(DISTINCT v.voter_email)::BIGINT AS total_voters,
        COUNT(DISTINCT n.nominee_email)::BIGINT AS total_nominees,
        SUM(n.votes_received)::BIGINT AS total_votes,
        COUNT(DISTINCT n.category)::BIGINT AS categories_count,
        AVG(n.votes_received)::NUMERIC AS avg_votes_per_nominee
    FROM eom_cycles ec
    LEFT JOIN eom_voters v ON v.eom_cycle_id = ec.id
    LEFT JOIN eom_nominees n ON n.eom_cycle_id = ec.id
    WHERE ec.id = p_eom_cycle_id
    GROUP BY ec.id;
END;
$$;

-- Update validate_evaluation_requirements function
CREATE OR REPLACE FUNCTION validate_evaluation_requirements(
    p_cycle_id INTEGER,
    p_target_email VARCHAR(255),
    p_min_evaluations INTEGER DEFAULT 3
)
RETURNS TABLE (
    is_valid BOOLEAN,
    evaluation_count BIGINT,
    message TEXT
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    v_count BIGINT;
BEGIN
    SELECT COUNT(*) INTO v_count
    FROM assignments a
    JOIN evaluations e ON e.assignment_id = a.id
    WHERE a.cycle_id = p_cycle_id
      AND a.target_email = p_target_email
      AND e.status = 'submitted';
    
    IF v_count >= p_min_evaluations THEN
        RETURN QUERY SELECT TRUE, v_count, 
            format('Valid: %s evaluations (minimum: %s)', v_count, p_min_evaluations)::TEXT;
    ELSE
        RETURN QUERY SELECT FALSE, v_count, 
            format('Invalid: Only %s evaluations (minimum: %s required)', v_count, p_min_evaluations)::TEXT;
    END IF;
END;
$$;

-- Update get_staff_count_by_segment function
CREATE OR REPLACE FUNCTION get_staff_count_by_segment()
RETURNS TABLE (
    segment staff_segment,
    staff_count BIGINT
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
    RETURN QUERY
    SELECT
        p.segment,
        COUNT(*)::BIGINT AS staff_count
    FROM people p
    WHERE p.active = TRUE
    GROUP BY p.segment
    ORDER BY p.segment;
END;
$$;

-- Update get_cycle_completion_status function
CREATE OR REPLACE FUNCTION get_cycle_completion_status(
    p_cycle_id INTEGER
)
RETURNS TABLE (
    total_assignments BIGINT,
    completed_assignments BIGINT,
    completion_percentage NUMERIC,
    status TEXT
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    v_total BIGINT;
    v_completed BIGINT;
    v_percentage NUMERIC;
BEGIN
    SELECT 
        COUNT(DISTINCT a.id),
        COUNT(DISTINCT CASE WHEN e.status = 'submitted' THEN a.id END)
    INTO v_total, v_completed
    FROM assignments a
    LEFT JOIN evaluations e ON e.assignment_id = a.id
    WHERE a.cycle_id = p_cycle_id;
    
    v_percentage := (v_completed::NUMERIC / NULLIF(v_total, 0) * 100);
    
    RETURN QUERY
    SELECT
        v_total,
        v_completed,
        v_percentage,
        CASE
            WHEN v_percentage >= 90 THEN 'Complete'::TEXT
            WHEN v_percentage >= 50 THEN 'In Progress'::TEXT
            ELSE 'Not Started'::TEXT
        END AS status;
END;
$$;

-- ============================================================================
-- HANDLE FUNCTIONS THAT MIGHT NOT EXIST YET (Use ALTER FUNCTION)
-- ============================================================================

-- Set search_path for get_conversation_messages function (if it exists)
DO $$ 
DECLARE
    rec RECORD;
BEGIN
    FOR rec IN 
        SELECT pg_get_function_identity_arguments(p.oid) as args
        FROM pg_proc p
        JOIN pg_namespace n ON p.pronamespace = n.oid
        WHERE p.proname = 'get_conversation_messages' 
        AND n.nspname = 'public'
    LOOP
        EXECUTE format('ALTER FUNCTION get_conversation_messages(%s) SET search_path = public', rec.args);
    END LOOP;
END $$;

-- Set search_path for upsert_people function (if it exists)
DO $$ 
DECLARE
    rec RECORD;
BEGIN
    FOR rec IN 
        SELECT pg_get_function_identity_arguments(p.oid) as args
        FROM pg_proc p
        JOIN pg_namespace n ON p.pronamespace = n.oid
        WHERE p.proname = 'upsert_people' 
        AND n.nspname = 'public'
    LOOP
        EXECUTE format('ALTER FUNCTION upsert_people(%s) SET search_path = public', rec.args);
    END LOOP;
END $$;

-- Set search_path for resolve_term_for_date function (if it exists)
DO $$ 
DECLARE
    rec RECORD;
BEGIN
    FOR rec IN 
        SELECT pg_get_function_identity_arguments(p.oid) as args
        FROM pg_proc p
        JOIN pg_namespace n ON p.pronamespace = n.oid
        WHERE p.proname = 'resolve_term_for_date' 
        AND n.nspname = 'public'
    LOOP
        EXECUTE format('ALTER FUNCTION resolve_term_for_date(%s) SET search_path = public', rec.args);
    END LOOP;
END $$;

-- Set search_path for eom_eligible function (if it exists)
DO $$ 
DECLARE
    rec RECORD;
BEGIN
    FOR rec IN 
        SELECT pg_get_function_identity_arguments(p.oid) as args
        FROM pg_proc p
        JOIN pg_namespace n ON p.pronamespace = n.oid
        WHERE p.proname = 'eom_eligible' 
        AND n.nspname = 'public'
    LOOP
        EXECUTE format('ALTER FUNCTION eom_eligible(%s) SET search_path = public', rec.args);
    END LOOP;
END $$;

