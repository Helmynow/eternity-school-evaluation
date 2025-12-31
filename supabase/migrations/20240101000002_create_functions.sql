-- Database Functions for Eternity School Evaluation System

-- ============================================================================
-- SCORING FUNCTIONS
-- ============================================================================

-- Calculate weighted score for a target in a cycle
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
) AS $$
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
$$ LANGUAGE plpgsql;

-- Get evaluation statistics for a cycle
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
) AS $$
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
$$ LANGUAGE plpgsql;

-- ============================================================================
-- EOM FUNCTIONS
-- ============================================================================

-- Check if nominee is eligible for EOM nomination
CREATE OR REPLACE FUNCTION check_eom_eligibility(
    p_nominee_email VARCHAR(255),
    p_eom_cycle_id INTEGER,
    p_category eom_category
)
RETURNS TABLE (
    is_eligible BOOLEAN,
    reason TEXT
) AS $$
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
$$ LANGUAGE plpgsql;

-- Get EOM cycle statistics
CREATE OR REPLACE FUNCTION get_eom_cycle_stats(
    p_eom_cycle_id INTEGER
)
RETURNS TABLE (
    total_voters BIGINT,
    total_nominees BIGINT,
    total_votes BIGINT,
    categories_count BIGINT,
    avg_votes_per_nominee NUMERIC
) AS $$
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
$$ LANGUAGE plpgsql;

-- ============================================================================
-- VALIDATION FUNCTIONS
-- ============================================================================

-- Validate evaluation requirements for a target
CREATE OR REPLACE FUNCTION validate_evaluation_requirements(
    p_cycle_id INTEGER,
    p_target_email VARCHAR(255),
    p_min_evaluations INTEGER DEFAULT 3
)
RETURNS TABLE (
    is_valid BOOLEAN,
    evaluation_count BIGINT,
    message TEXT
) AS $$
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
$$ LANGUAGE plpgsql;

-- ============================================================================
-- UTILITY FUNCTIONS
-- ============================================================================

-- Get active staff count by segment
CREATE OR REPLACE FUNCTION get_staff_count_by_segment()
RETURNS TABLE (
    segment staff_segment,
    staff_count BIGINT
) AS $$
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
$$ LANGUAGE plpgsql;

-- Get cycle completion status
CREATE OR REPLACE FUNCTION get_cycle_completion_status(
    p_cycle_id INTEGER
)
RETURNS TABLE (
    total_assignments BIGINT,
    completed_assignments BIGINT,
    completion_percentage NUMERIC,
    status TEXT
) AS $$
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
$$ LANGUAGE plpgsql;

