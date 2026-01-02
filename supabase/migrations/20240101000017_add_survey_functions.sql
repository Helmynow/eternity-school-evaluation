-- Migration: Add Survey and Identity Management Database Functions
-- Creates functions for survey response aggregation, notification triggers, 
-- auto-cleanup for expired anonymous data, and identity transition management

-- ============================================================================
-- SURVEY RESPONSE AGGREGATION FUNCTIONS
-- ============================================================================

-- Aggregate survey responses by question
CREATE OR REPLACE FUNCTION aggregate_survey_responses(
    p_survey_id INTEGER,
    p_question_id INTEGER DEFAULT NULL
)
RETURNS TABLE (
    question_id INTEGER,
    question_text TEXT,
    question_type VARCHAR(50),
    total_responses BIGINT,
    response_distribution JSONB,
    average_rating NUMERIC,
    identity_mode_breakdown JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        sq.id AS question_id,
        sq.question_text,
        sq.question_type,
        COUNT(sr.id)::BIGINT AS total_responses,
        CASE 
            WHEN sq.question_type IN ('multiple_choice', 'yes_no') THEN
                jsonb_object_agg(
                    COALESCE(sr.response_value->>'value', sr.response_text),
                    COUNT(*)::TEXT
                )
            WHEN sq.question_type = 'rating' THEN
                jsonb_build_object(
                    'average', AVG((sr.response_value->>'value')::NUMERIC),
                    'min', MIN((sr.response_value->>'value')::NUMERIC),
                    'max', MAX((sr.response_value->>'value')::NUMERIC),
                    'distribution', jsonb_object_agg(
                        (sr.response_value->>'value'),
                        COUNT(*)::TEXT
                    )
                )
            ELSE
                NULL::JSONB
        END AS response_distribution,
        CASE 
            WHEN sq.question_type = 'rating' THEN
                AVG((sr.response_value->>'value')::NUMERIC)
            ELSE NULL
        END AS average_rating,
        jsonb_object_agg(
            COALESCE(sr.identity_mode, 'unknown'),
            COUNT(*)::TEXT
        ) AS identity_mode_breakdown
    FROM survey_questions sq
    LEFT JOIN survey_responses sr ON sr.question_id = sq.id
    WHERE sq.survey_id = p_survey_id
      AND (p_question_id IS NULL OR sq.id = p_question_id)
    GROUP BY sq.id, sq.question_text, sq.question_type
    ORDER BY sq.order_index;
END;
$$ LANGUAGE plpgsql;

-- Get survey response statistics
CREATE OR REPLACE FUNCTION get_survey_response_stats(
    p_survey_id INTEGER
)
RETURNS TABLE (
    total_responses BIGINT,
    unique_respondents BIGINT,
    completion_rate NUMERIC,
    identity_mode_distribution JSONB,
    response_rate_by_question JSONB
) AS $$
DECLARE
    v_total_questions INTEGER;
BEGIN
    -- Get total questions
    SELECT COUNT(*) INTO v_total_questions
    FROM survey_questions
    WHERE survey_id = p_survey_id;
    
    RETURN QUERY
    SELECT
        COUNT(DISTINCT sr.id)::BIGINT AS total_responses,
        COUNT(DISTINCT COALESCE(sr.respondent_email, sr.anonymous_id, sr.session_id))::BIGINT AS unique_respondents,
        CASE 
            WHEN v_total_questions > 0 THEN
                (COUNT(DISTINCT sr.id)::NUMERIC / v_total_questions * 100)
            ELSE 0
        END AS completion_rate,
        jsonb_object_agg(
            COALESCE(sr.identity_mode, 'unknown'),
            COUNT(DISTINCT COALESCE(sr.respondent_email, sr.anonymous_id, sr.session_id))::TEXT
        ) AS identity_mode_distribution,
        jsonb_object_agg(
            sq.id::TEXT,
            jsonb_build_object(
                'question_text', sq.question_text,
                'responses', COUNT(sr.id),
                'response_rate', CASE 
                    WHEN v_total_questions > 0 THEN
                        (COUNT(sr.id)::NUMERIC / v_total_questions * 100)
                    ELSE 0
                END
            )
        ) AS response_rate_by_question
    FROM survey_questions sq
    LEFT JOIN survey_responses sr ON sr.question_id = sq.id
    WHERE sq.survey_id = p_survey_id
    GROUP BY sq.survey_id;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- NOTIFICATION TRIGGER FUNCTIONS
-- ============================================================================

-- Function to create notification when survey response is submitted
CREATE OR REPLACE FUNCTION notify_survey_response_submitted()
RETURNS TRIGGER AS $$
DECLARE
    v_survey_title VARCHAR(200);
    v_recipient_email VARCHAR(255);
BEGIN
    -- Get survey title
    SELECT title INTO v_survey_title
    FROM surveys
    WHERE id = NEW.survey_id;
    
    -- Determine recipient (for identified responses)
    IF NEW.respondent_email IS NOT NULL THEN
        v_recipient_email := NEW.respondent_email;
        
        -- Create notification for survey creator
        INSERT INTO notifications (
            recipient_email,
            notification_type,
            title,
            message,
            action_url,
            related_entity_type,
            related_entity_id,
            priority
        )
        SELECT
            s.created_by,
            'survey_response_submitted',
            'New Survey Response',
            format('A new response was submitted for survey: %s', v_survey_title),
            format('/survey/%s/responses', NEW.survey_id),
            'survey',
            NEW.survey_id,
            'normal'
        FROM surveys s
        WHERE s.id = NEW.survey_id
          AND s.created_by IS NOT NULL;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for survey response notifications
DROP TRIGGER IF EXISTS trigger_survey_response_notification ON survey_responses;
CREATE TRIGGER trigger_survey_response_notification
    AFTER INSERT ON survey_responses
    FOR EACH ROW
    EXECUTE FUNCTION notify_survey_response_submitted();

-- Function to create notification when objection is submitted
CREATE OR REPLACE FUNCTION notify_objection_submitted()
RETURNS TRIGGER AS $$
DECLARE
    v_recipient_email VARCHAR(255);
BEGIN
    -- Determine recipient based on objection type
    CASE NEW.objection_type
        WHEN 'evaluation' THEN
            -- Notify evaluation target
            SELECT target_email INTO v_recipient_email
            FROM evaluations
            WHERE id = NEW.related_entity_id;
        WHEN 'nomination' THEN
            -- Notify nominee
            SELECT nominee_email INTO v_recipient_email
            FROM eom_nominees
            WHERE id = NEW.related_entity_id;
        ELSE
            -- Notify admin/CEO
            v_recipient_email := NULL; -- Will be handled by admin dashboard
    END CASE;
    
    -- Create notification for relevant parties
    IF v_recipient_email IS NOT NULL THEN
        INSERT INTO notifications (
            recipient_email,
            notification_type,
            title,
            message,
            action_url,
            related_entity_type,
            related_entity_id,
            priority
        ) VALUES (
            v_recipient_email,
            'objection_submitted',
            'Objection Submitted',
            format('An objection has been submitted regarding: %s', NEW.title),
            format('/objections/%s', NEW.id),
            'objection',
            NEW.id,
            'high'
        );
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for objection notifications
DROP TRIGGER IF EXISTS trigger_objection_notification ON objections;
CREATE TRIGGER trigger_objection_notification
    AFTER INSERT ON objections
    FOR EACH ROW
    EXECUTE FUNCTION notify_objection_submitted();

-- ============================================================================
-- AUTO-CLEANUP FUNCTIONS FOR EXPIRED ANONYMOUS DATA
-- ============================================================================

-- Cleanup expired anonymous survey responses
CREATE OR REPLACE FUNCTION cleanup_expired_anonymous_responses()
RETURNS TABLE (
    deleted_count BIGINT,
    message TEXT
) AS $$
DECLARE
    v_deleted_count BIGINT;
    v_retention_days INTEGER := 90; -- Default retention period
BEGIN
    -- Delete anonymous responses older than retention period
    WITH deleted AS (
        DELETE FROM survey_responses
        WHERE identity_mode = 'anonymous'
          AND anonymous_id IS NOT NULL
          AND created_at < NOW() - (v_retention_days || ' days')::INTERVAL
        RETURNING id
    )
    SELECT COUNT(*) INTO v_deleted_count FROM deleted;
    
    RETURN QUERY
    SELECT
        v_deleted_count,
        format('Deleted %s expired anonymous survey responses', v_deleted_count)::TEXT;
END;
$$ LANGUAGE plpgsql;

-- Cleanup expired anonymous data based on user preferences
CREATE OR REPLACE FUNCTION cleanup_expired_anonymous_data_by_preference()
RETURNS TABLE (
    deleted_count BIGINT,
    message TEXT
) AS $$
DECLARE
    v_deleted_count BIGINT;
BEGIN
    -- Delete anonymous responses based on user retention preferences
    WITH expired_responses AS (
        SELECT sr.id
        FROM survey_responses sr
        JOIN survey_identity_preferences sip ON 
            sip.survey_id = sr.survey_id
            AND sr.anonymous_id IS NOT NULL
            AND sr.identity_mode = 'anonymous'
        WHERE sip.retention_days IS NOT NULL
          AND sr.created_at < NOW() - (sip.retention_days || ' days')::INTERVAL
    ),
    deleted AS (
        DELETE FROM survey_responses
        WHERE id IN (SELECT id FROM expired_responses)
        RETURNING id
    )
    SELECT COUNT(*) INTO v_deleted_count FROM deleted;
    
    RETURN QUERY
    SELECT
        v_deleted_count,
        format('Deleted %s expired anonymous responses based on user preferences', v_deleted_count)::TEXT;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- IDENTITY TRANSITION FUNCTIONS
-- ============================================================================

-- Link anonymous responses to identified user
CREATE OR REPLACE FUNCTION link_anonymous_responses(
    p_anonymous_id VARCHAR(255),
    p_user_email VARCHAR(255),
    p_survey_id INTEGER DEFAULT NULL
)
RETURNS TABLE (
    linked_count BIGINT,
    message TEXT
) AS $$
DECLARE
    v_linked_count BIGINT;
BEGIN
    -- Update anonymous responses to link to user email
    WITH updated AS (
        UPDATE survey_responses
        SET 
            respondent_email = p_user_email,
            anonymous_id = NULL, -- Remove anonymous ID after linking
            identity_mode = 'identified'
        WHERE anonymous_id = p_anonymous_id
          AND (p_survey_id IS NULL OR survey_id = p_survey_id)
          AND respondent_email IS NULL
        RETURNING id
    )
    SELECT COUNT(*) INTO v_linked_count FROM updated;
    
    RETURN QUERY
    SELECT
        v_linked_count,
        format('Linked %s anonymous responses to user %s', v_linked_count, p_user_email)::TEXT;
END;
$$ LANGUAGE plpgsql;

-- Transition user identity mode for a survey
CREATE OR REPLACE FUNCTION transition_survey_identity(
    p_user_email VARCHAR(255),
    p_survey_id INTEGER,
    p_new_mode VARCHAR(20),
    p_anonymous_id VARCHAR(255) DEFAULT NULL
)
RETURNS TABLE (
    transitioned_count BIGINT,
    message TEXT
) AS $$
DECLARE
    v_transitioned_count BIGINT;
BEGIN
    -- Update identity preferences
    INSERT INTO survey_identity_preferences (
        user_email,
        survey_id,
        identity_mode,
        updated_at
    ) VALUES (
        p_user_email,
        p_survey_id,
        p_new_mode,
        NOW()
    )
    ON CONFLICT (user_email, survey_id)
    DO UPDATE SET
        identity_mode = p_new_mode,
        updated_at = NOW();
    
    -- If transitioning from anonymous to identified, link responses
    IF p_new_mode = 'identified' AND p_anonymous_id IS NOT NULL THEN
        PERFORM link_anonymous_responses(p_anonymous_id, p_user_email, p_survey_id);
    END IF;
    
    -- Update existing responses identity mode
    WITH updated AS (
        UPDATE survey_responses
        SET identity_mode = p_new_mode
        WHERE survey_id = p_survey_id
          AND (
              respondent_email = p_user_email
              OR anonymous_id = p_anonymous_id
          )
        RETURNING id
    )
    SELECT COUNT(*) INTO v_transitioned_count FROM updated;
    
    RETURN QUERY
    SELECT
        v_transitioned_count,
        format('Transitioned %s responses to %s mode for user %s', 
               v_transitioned_count, p_new_mode, p_user_email)::TEXT;
END;
$$ LANGUAGE plpgsql;

-- Get identity transition status
CREATE OR REPLACE FUNCTION get_identity_transition_status(
    p_user_email VARCHAR(255),
    p_survey_id INTEGER
)
RETURNS TABLE (
    current_mode VARCHAR(20),
    previous_mode VARCHAR(20),
    transition_date TIMESTAMP,
    linked_responses_count BIGINT,
    can_transition BOOLEAN,
    transition_message TEXT
) AS $$
DECLARE
    v_current_mode VARCHAR(20);
    v_previous_mode VARCHAR(20);
    v_transition_date TIMESTAMP;
    v_linked_count BIGINT;
    v_can_transition BOOLEAN := TRUE;
    v_message TEXT;
BEGIN
    -- Get current identity mode
    SELECT identity_mode, updated_at INTO v_current_mode, v_transition_date
    FROM survey_identity_preferences
    WHERE user_email = p_user_email
      AND survey_id = p_survey_id;
    
    -- Get linked responses count
    SELECT COUNT(*) INTO v_linked_count
    FROM survey_responses
    WHERE survey_id = p_survey_id
      AND respondent_email = p_user_email;
    
    -- Check if transition is possible
    IF v_current_mode = 'identified' THEN
        v_can_transition := FALSE;
        v_message := 'Cannot transition from identified mode';
    ELSIF v_current_mode IS NULL THEN
        v_message := 'No identity mode set, can transition';
    ELSE
        v_message := format('Current mode: %s, can transition', v_current_mode);
    END IF;
    
    RETURN QUERY
    SELECT
        COALESCE(v_current_mode, 'anonymous')::VARCHAR(20),
        v_previous_mode,
        v_transition_date,
        v_linked_count,
        v_can_transition,
        v_message::TEXT;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

-- Index for cleanup queries
CREATE INDEX IF NOT EXISTS idx_survey_response_anonymous_created 
    ON survey_responses(identity_mode, anonymous_id, created_at)
    WHERE identity_mode = 'anonymous' AND anonymous_id IS NOT NULL;

-- Index for identity transition queries
CREATE INDEX IF NOT EXISTS idx_survey_response_transition 
    ON survey_responses(survey_id, respondent_email, anonymous_id, identity_mode);
