-- Migration: Fix EOM Categories and Add Missing Features
-- Updates EOM categories to match original design (5 categories)
-- Adds nomination window, weighted voting, variance alerts, and other features

-- ============================================================================
-- 1. UPDATE EOM CATEGORY ENUM
-- ============================================================================

-- Drop ALL dependent views first (CASCADE will handle dependencies)
DROP VIEW IF EXISTS eom_nomination_summary CASCADE;
DROP VIEW IF EXISTS eom_winner_history CASCADE;
DROP VIEW IF EXISTS eom_diversity_tracking CASCADE;
DROP VIEW IF EXISTS eom_hall_of_fame CASCADE;
DROP VIEW IF EXISTS eom_participants CASCADE;
DROP VIEW IF EXISTS eom_eligible_current CASCADE;
DROP FUNCTION IF EXISTS check_eom_eligibility(character varying, integer, eom_category);

-- Create new enum with correct categories
DO $$ BEGIN
    CREATE TYPE eom_category_new AS ENUM (
        'outstanding_leadership',
        'team_spirit',
        'innovation',
        'rising_star',
        'service_excellence'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- First, alter columns to use new enum (this will map existing values)
-- Alter columns to use new enum
ALTER TABLE eom_nominees 
    ALTER COLUMN category TYPE eom_category_new 
    USING CASE 
        WHEN category::text IN ('leadership', 'academic', 'admin') THEN 'outstanding_leadership'::eom_category_new
        WHEN category::text = 'innovation' THEN 'innovation'::eom_category_new
        WHEN category::text = 'collaboration' THEN 'team_spirit'::eom_category_new
        WHEN category::text = 'student_engagement' THEN 'service_excellence'::eom_category_new
        WHEN category::text = 'support' THEN 'service_excellence'::eom_category_new
        ELSE 'outstanding_leadership'::eom_category_new  -- Default fallback
    END;

ALTER TABLE eom_rotation_rules 
    ALTER COLUMN category TYPE eom_category_new 
    USING CASE 
        WHEN category::text IN ('leadership', 'academic', 'admin') THEN 'outstanding_leadership'::eom_category_new
        WHEN category::text = 'innovation' THEN 'innovation'::eom_category_new
        WHEN category::text = 'collaboration' THEN 'team_spirit'::eom_category_new
        WHEN category::text = 'student_engagement' THEN 'service_excellence'::eom_category_new
        WHEN category::text = 'support' THEN 'service_excellence'::eom_category_new
        ELSE 'outstanding_leadership'::eom_category_new  -- Default fallback
    END;

ALTER TABLE eom_winners 
    ALTER COLUMN category TYPE VARCHAR(50);  -- First change to text

-- Update eom_winners (it's now text, so we can update directly)
UPDATE eom_winners SET category = 'outstanding_leadership'
WHERE category IN ('leadership', 'academic', 'admin');
UPDATE eom_winners SET category = 'innovation'
WHERE category = 'innovation';
UPDATE eom_winners SET category = 'team_spirit'
WHERE category = 'collaboration';
UPDATE eom_winners SET category = 'service_excellence'
WHERE category IN ('student_engagement', 'support');

-- Now change eom_winners to new enum
ALTER TABLE eom_winners 
    ALTER COLUMN category TYPE eom_category_new 
    USING category::eom_category_new;

-- Drop old enum and rename new one (CASCADE will drop dependent functions)
DROP TYPE IF EXISTS eom_category CASCADE;
ALTER TYPE eom_category_new RENAME TO eom_category;

-- Recreate the function that was dropped
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

-- ============================================================================
-- 2. ADD NOMINATION WINDOW TO EOM CYCLES
-- ============================================================================

ALTER TABLE eom_cycles 
ADD COLUMN IF NOT EXISTS nomination_window_start_day INTEGER DEFAULT 15,
ADD COLUMN IF NOT EXISTS nomination_window_duration_days INTEGER DEFAULT 7,
ADD COLUMN IF NOT EXISTS announcement_date DATE;

COMMENT ON COLUMN eom_cycles.nomination_window_start_day IS 'Day of month when nominations open (default: 15th)';
COMMENT ON COLUMN eom_cycles.nomination_window_duration_days IS 'Number of days nominations are open (default: 7)';
COMMENT ON COLUMN eom_cycles.announcement_date IS 'Date when winners are announced (first working day of following month)';

-- ============================================================================
-- 3. ADD WEIGHTED VOTING TO EOM VOTERS
-- ============================================================================

ALTER TABLE eom_voters 
ADD COLUMN IF NOT EXISTS vote_weight DECIMAL(5,2) DEFAULT 1.0;

COMMENT ON COLUMN eom_voters.vote_weight IS 'Vote weight: Principal 0.40, Manager 0.30, CEO 0.30';

-- Function to set default vote weights based on role
CREATE OR REPLACE FUNCTION set_default_vote_weights()
RETURNS TRIGGER AS $$
BEGIN
    -- Set vote weights based on role (if not already set)
    IF NEW.vote_weight IS NULL OR NEW.vote_weight = 1.0 THEN
        -- Check role from people table or voter role
        IF NEW.voter_role ILIKE '%principal%' OR NEW.voter_role ILIKE '%stage principal%' THEN
            NEW.vote_weight := 0.40;
        ELSIF NEW.voter_role ILIKE '%manager%' OR NEW.voter_role ILIKE '%head%' THEN
            NEW.vote_weight := 0.30;
        ELSIF NEW.voter_role ILIKE '%CEO%' OR NEW.voter_role ILIKE '%director%' THEN
            NEW.vote_weight := 0.30;
        ELSE
            NEW.vote_weight := 1.0; -- Default equal weight
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_set_vote_weights ON eom_voters;
CREATE TRIGGER trigger_set_vote_weights
    BEFORE INSERT OR UPDATE ON eom_voters
    FOR EACH ROW
    EXECUTE FUNCTION set_default_vote_weights();

-- ============================================================================
-- 4. ADD VARIANCE ALERT SYSTEM
-- ============================================================================

-- Add variance tracking to evaluations
ALTER TABLE evaluations 
ADD COLUMN IF NOT EXISTS variance_flag VARCHAR(50),
ADD COLUMN IF NOT EXISTS variance_alert_sent BOOLEAN DEFAULT FALSE;

COMMENT ON COLUMN evaluations.variance_flag IS 'Flag for variance alerts (e.g., "ALERT – ≥2pt spread")';
COMMENT ON COLUMN evaluations.variance_alert_sent IS 'Whether variance alert email has been sent';

-- Function to calculate and flag variance
CREATE OR REPLACE FUNCTION calculate_evaluation_variance()
RETURNS TRIGGER AS $$
DECLARE
    avg_score DECIMAL;
    variance_threshold DECIMAL := 2.0;
BEGIN
    -- Calculate average score for this target in this cycle
    SELECT AVG(e.rating) INTO avg_score
    FROM evaluations e
    JOIN assignments a ON e.assignment_id = a.id
    WHERE a.target_email = (
        SELECT a2.target_email 
        FROM assignments a2 
        WHERE a2.id = NEW.assignment_id
    )
    AND a.cycle_id = (
        SELECT a3.cycle_id 
        FROM assignments a3 
        WHERE a3.id = NEW.assignment_id
    )
    AND e.status = 'submitted'
    AND e.rating IS NOT NULL;
    
    -- Flag if variance is >= 2 points
    IF avg_score IS NOT NULL AND NEW.rating IS NOT NULL THEN
        IF ABS(NEW.rating - avg_score) >= variance_threshold THEN
            NEW.variance_flag := 'ALERT – ≥2pt spread';
            NEW.variance_alert_sent := FALSE;
        ELSE
            NEW.variance_flag := NULL;
        END IF;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SET search_path = public;

DROP TRIGGER IF EXISTS trigger_calculate_variance ON evaluations;
CREATE TRIGGER trigger_calculate_variance
    BEFORE INSERT OR UPDATE OF rating ON evaluations
    FOR EACH ROW
    WHEN (NEW.rating IS NOT NULL)
    EXECUTE FUNCTION calculate_evaluation_variance();

-- ============================================================================
-- 5. ADD DIVERSITY MONITORING FOR EOM
-- ============================================================================

-- Create view for EOM diversity tracking
CREATE OR REPLACE VIEW eom_diversity_tracking AS
SELECT 
    ec.id as cycle_id,
    ec.name as cycle_name,
    ew.category,
    p.segment,
    p.department,
    p.role_title,
    COUNT(DISTINCT ew.winner_email) as winners_count,
    COUNT(DISTINCT en.nominee_email) as nominees_count
FROM eom_cycles ec
LEFT JOIN eom_winners ew ON ew.eom_cycle_id = ec.id
LEFT JOIN eom_nominees en ON en.eom_cycle_id = ec.id
LEFT JOIN people p ON p.email = COALESCE(ew.winner_email, en.nominee_email)
GROUP BY ec.id, ec.name, ew.category, p.segment, p.department, p.role_title;

COMMENT ON VIEW eom_diversity_tracking IS 'Tracks EOM recognition across gender, department, and role for diversity monitoring';

-- ============================================================================
-- 6. ADD FEEDBACK COLLECTION SYSTEM
-- ============================================================================

CREATE TABLE IF NOT EXISTS eom_feedback (
    id SERIAL PRIMARY KEY,
    eom_cycle_id INTEGER NOT NULL REFERENCES eom_cycles(id) ON DELETE CASCADE,
    feedback_type VARCHAR(50) NOT NULL, -- 'nominee', 'nominator', 'voter'
    person_email VARCHAR(255) REFERENCES people(email) ON DELETE SET NULL,
    feedback_text TEXT NOT NULL,
    rating INTEGER CHECK (rating >= 1 AND rating <= 5), -- 1-5 scale
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_eom_feedback_cycle ON eom_feedback(eom_cycle_id);
CREATE INDEX IF NOT EXISTS idx_eom_feedback_person ON eom_feedback(person_email);
CREATE INDEX IF NOT EXISTS idx_eom_feedback_type ON eom_feedback(feedback_type);

COMMENT ON TABLE eom_feedback IS 'Collects feedback from nominees, nominators, and voters after each EOM cycle';

-- ============================================================================
-- 7. ADD HALL OF FAME / WINNERS HISTORY VIEW
-- ============================================================================

CREATE OR REPLACE VIEW eom_hall_of_fame AS
SELECT 
    ew.id,
    ew.eom_cycle_id,
    ec.name as cycle_name,
    ec.start_date as cycle_start,
    ec.end_date as cycle_end,
    ew.category,
    p.full_name as winner_name,
    p.email as winner_email,
    p.department,
    p.role_title,
    p.segment,
    en.nomination_reason,
    COUNT(DISTINCT ev.id) as total_votes,
    SUM(ev.vote_weight) as weighted_votes,
    ew.created_at as won_at
FROM eom_winners ew
JOIN eom_cycles ec ON ew.eom_cycle_id = ec.id
JOIN people p ON ew.winner_email = p.email
LEFT JOIN eom_nominees en ON en.eom_cycle_id = ew.eom_cycle_id 
    AND en.nominee_email = ew.winner_email 
    AND en.category = ew.category
LEFT JOIN eom_voters ev ON ev.eom_cycle_id = ew.eom_cycle_id
GROUP BY ew.id, ew.eom_cycle_id, ec.name, ec.start_date, ec.end_date, 
    ew.category, p.full_name, p.email, p.department, p.role_title, 
    p.segment, en.nomination_reason, ew.created_at
ORDER BY ec.start_date DESC, ew.category;

COMMENT ON VIEW eom_hall_of_fame IS 'Complete history of EOM winners - the Hall of Fame';

-- ============================================================================
-- 8. ADD EMAIL NOTIFICATION TRACKING
-- ============================================================================

CREATE TABLE IF NOT EXISTS email_notifications (
    id SERIAL PRIMARY KEY,
    notification_type VARCHAR(100) NOT NULL, -- 'variance_alert', 'nomination_submitted', 'eom_winner'
    recipient_email VARCHAR(255) NOT NULL,
    subject VARCHAR(500),
    body TEXT,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) DEFAULT 'sent', -- 'sent', 'failed', 'pending'
    error_message TEXT,
    related_entity_type VARCHAR(100), -- 'evaluation', 'nomination', 'cycle'
    related_entity_id INTEGER
);

CREATE INDEX IF NOT EXISTS idx_email_notifications_type ON email_notifications(notification_type);
CREATE INDEX IF NOT EXISTS idx_email_notifications_recipient ON email_notifications(recipient_email);
CREATE INDEX IF NOT EXISTS idx_email_notifications_sent_at ON email_notifications(sent_at);

COMMENT ON TABLE email_notifications IS 'Tracks all email notifications sent by the system';
