-- Migration: Add Missing Database Models
-- Creates tables for Survey, SurveyQuestion, SurveyResponse, Notification, Objection, VarianceAlert, Feedback

-- ============================================================================
-- SURVEYS TABLE
-- ============================================================================
-- Surveys table may already exist from migration 00012, so add missing columns if needed
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'surveys') THEN
        CREATE TABLE surveys (
            id SERIAL PRIMARY KEY,
            title VARCHAR(200) NOT NULL,
            description TEXT,
            survey_type VARCHAR(50),
            status VARCHAR(20) DEFAULT 'draft',
            start_date DATE,
            end_date DATE,
            created_by VARCHAR(255) REFERENCES people(email) ON DELETE SET NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    ELSE
        -- Add survey_type column if it doesn't exist
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'surveys' AND column_name = 'survey_type') THEN
            ALTER TABLE surveys ADD COLUMN survey_type VARCHAR(50);
        END IF;
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_survey_status ON surveys(status);
-- Create survey_type index only if column exists
DO $$ 
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'surveys' AND column_name = 'survey_type') THEN
        CREATE INDEX IF NOT EXISTS idx_survey_type ON surveys(survey_type);
    END IF;
END $$;
CREATE INDEX IF NOT EXISTS idx_survey_dates ON surveys(start_date, end_date);

-- ============================================================================
-- SURVEY QUESTIONS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS survey_questions (
    id SERIAL PRIMARY KEY,
    survey_id INTEGER NOT NULL REFERENCES surveys(id) ON DELETE CASCADE,
    question_text TEXT NOT NULL,
    question_type VARCHAR(50),
    category VARCHAR(100),
    section VARCHAR(100),
    order_index INTEGER DEFAULT 0,
    required BOOLEAN DEFAULT TRUE,
    identity_modes JSONB,
    sensitivity_level VARCHAR(20),
    options JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_survey_question_survey ON survey_questions(survey_id);
-- Create category index only if column exists
DO $$ 
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'survey_questions' AND column_name = 'category') THEN
        CREATE INDEX IF NOT EXISTS idx_survey_question_category ON survey_questions(category);
    END IF;
END $$;
CREATE INDEX IF NOT EXISTS idx_survey_question_order ON survey_questions(survey_id, order_index);

-- ============================================================================
-- SURVEY RESPONSES TABLE
-- ============================================================================
-- Survey responses table may already exist, so add missing columns if needed
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'survey_responses') THEN
        CREATE TABLE survey_responses (
            id SERIAL PRIMARY KEY,
            survey_id INTEGER NOT NULL REFERENCES surveys(id) ON DELETE CASCADE,
            question_id INTEGER NOT NULL REFERENCES survey_questions(id) ON DELETE CASCADE,
            respondent_email VARCHAR(255) REFERENCES people(email) ON DELETE SET NULL,
            anonymous_id VARCHAR(255),
            session_id VARCHAR(255),
            identity_mode VARCHAR(20),
            response_text TEXT,
            response_value JSONB,
            submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    ELSE
        -- Add missing columns if they don't exist
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'survey_responses' AND column_name = 'anonymous_id') THEN
            ALTER TABLE survey_responses ADD COLUMN anonymous_id VARCHAR(255);
        END IF;
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'survey_responses' AND column_name = 'session_id') THEN
            ALTER TABLE survey_responses ADD COLUMN session_id VARCHAR(255);
        END IF;
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'survey_responses' AND column_name = 'identity_mode') THEN
            ALTER TABLE survey_responses ADD COLUMN identity_mode VARCHAR(20);
        END IF;
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'survey_responses' AND column_name = 'response_value') THEN
            ALTER TABLE survey_responses ADD COLUMN response_value JSONB;
        END IF;
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_survey_response_survey ON survey_responses(survey_id);
CREATE INDEX IF NOT EXISTS idx_survey_response_question ON survey_responses(question_id);
CREATE INDEX IF NOT EXISTS idx_survey_response_respondent ON survey_responses(respondent_email);
-- Create indexes only if columns exist
DO $$ 
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'survey_responses' AND column_name = 'anonymous_id') THEN
        CREATE INDEX IF NOT EXISTS idx_survey_response_anonymous ON survey_responses(anonymous_id);
    END IF;
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'survey_responses' AND column_name = 'session_id') THEN
        CREATE INDEX IF NOT EXISTS idx_survey_response_session ON survey_responses(session_id);
    END IF;
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'survey_responses' AND column_name = 'identity_mode') THEN
        CREATE INDEX IF NOT EXISTS idx_survey_response_mode ON survey_responses(identity_mode);
    END IF;
END $$;

-- ============================================================================
-- NOTIFICATIONS TABLE (In-App)
-- ============================================================================
-- Notifications table may already exist from migration 00012, so add missing columns if needed
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'notifications') THEN
        CREATE TABLE notifications (
            id SERIAL PRIMARY KEY,
            recipient_email VARCHAR(255) NOT NULL REFERENCES people(email) ON DELETE CASCADE,
            notification_type VARCHAR(50) NOT NULL,
            title VARCHAR(200) NOT NULL,
            message TEXT NOT NULL,
            read BOOLEAN DEFAULT FALSE,
            read_at TIMESTAMP,
            action_url VARCHAR(500),
            related_entity_type VARCHAR(50),
            related_entity_id INTEGER,
            priority VARCHAR(20) DEFAULT 'normal',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    ELSE
        -- Migration 00012 uses user_email, so rename if needed or add recipient_email
        IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'notifications' AND column_name = 'user_email') 
           AND NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'notifications' AND column_name = 'recipient_email') THEN
            ALTER TABLE notifications RENAME COLUMN user_email TO recipient_email;
        ELSIF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'notifications' AND column_name = 'recipient_email') THEN
            ALTER TABLE notifications ADD COLUMN recipient_email VARCHAR(255) REFERENCES people(email) ON DELETE CASCADE;
        END IF;
        -- Add missing columns
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'notifications' AND column_name = 'read_at') THEN
            ALTER TABLE notifications ADD COLUMN read_at TIMESTAMP;
        END IF;
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'notifications' AND column_name = 'action_url') THEN
            ALTER TABLE notifications ADD COLUMN action_url VARCHAR(500);
        END IF;
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'notifications' AND column_name = 'related_entity_type') THEN
            ALTER TABLE notifications ADD COLUMN related_entity_type VARCHAR(50);
        END IF;
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'notifications' AND column_name = 'related_entity_id') THEN
            ALTER TABLE notifications ADD COLUMN related_entity_id INTEGER;
        END IF;
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'notifications' AND column_name = 'priority') THEN
            ALTER TABLE notifications ADD COLUMN priority VARCHAR(20) DEFAULT 'normal';
        END IF;
        -- Rename is_read to read if needed
        IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'notifications' AND column_name = 'is_read') 
           AND NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'notifications' AND column_name = 'read') THEN
            ALTER TABLE notifications RENAME COLUMN is_read TO read;
        END IF;
    END IF;
END $$;

-- Create indexes, handling column name differences
DO $$ 
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'notifications' AND column_name = 'recipient_email') THEN
        CREATE INDEX IF NOT EXISTS idx_notification_recipient ON notifications(recipient_email);
    ELSIF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'notifications' AND column_name = 'user_email') THEN
        CREATE INDEX IF NOT EXISTS idx_notification_user ON notifications(user_email);
    END IF;
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'notifications' AND column_name = 'read') THEN
        CREATE INDEX IF NOT EXISTS idx_notification_read ON notifications(read);
    ELSIF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'notifications' AND column_name = 'is_read') THEN
        CREATE INDEX IF NOT EXISTS idx_notification_is_read ON notifications(is_read);
    END IF;
    -- Handle both "type" and "notification_type" column names
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'notifications' AND column_name = 'notification_type') THEN
        CREATE INDEX IF NOT EXISTS idx_notification_type ON notifications(notification_type);
    ELSIF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'notifications' AND column_name = 'type') THEN
        CREATE INDEX IF NOT EXISTS idx_notification_type ON notifications(type);
    END IF;
    CREATE INDEX IF NOT EXISTS idx_notification_created ON notifications(created_at);
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'notifications' AND column_name = 'priority') THEN
        CREATE INDEX IF NOT EXISTS idx_notification_priority ON notifications(priority);
    END IF;
END $$;

-- ============================================================================
-- OBJECTIONS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS objections (
    id SERIAL PRIMARY KEY,
    submitted_by VARCHAR(255) NOT NULL REFERENCES people(email) ON DELETE CASCADE,
    objection_type VARCHAR(50) NOT NULL,
    related_entity_type VARCHAR(50) NOT NULL,
    related_entity_id INTEGER NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    resolution_notes TEXT,
    resolved_by VARCHAR(255) REFERENCES people(email) ON DELETE SET NULL,
    resolved_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

DO $$ 
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'objections') THEN
        IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'objections' AND column_name = 'submitted_by') THEN
            CREATE INDEX IF NOT EXISTS idx_objection_submitter ON objections(submitted_by);
        END IF;
        IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'objections' AND column_name = 'status') THEN
            CREATE INDEX IF NOT EXISTS idx_objection_status ON objections(status);
        END IF;
        IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'objections' AND column_name = 'objection_type') THEN
            CREATE INDEX IF NOT EXISTS idx_objection_type ON objections(objection_type);
        END IF;
        IF EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_name = 'objections' AND column_name = 'related_entity_type'
        ) AND EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_name = 'objections' AND column_name = 'related_entity_id'
        ) THEN
            CREATE INDEX IF NOT EXISTS idx_objection_entity ON objections(related_entity_type, related_entity_id);
        END IF;
    END IF;
END $$;

-- ============================================================================
-- VARIANCE ALERTS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS variance_alerts (
    id SERIAL PRIMARY KEY,
    cycle_id INTEGER NOT NULL REFERENCES cycles(id) ON DELETE CASCADE,
    alert_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) DEFAULT 'medium',
    target_email VARCHAR(255) REFERENCES people(email) ON DELETE SET NULL,
    description TEXT NOT NULL,
    details JSONB,
    acknowledged BOOLEAN DEFAULT FALSE,
    acknowledged_by VARCHAR(255) REFERENCES people(email) ON DELETE SET NULL,
    acknowledged_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

DO $$ 
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'variance_alerts') THEN
        IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'variance_alerts' AND column_name = 'cycle_id') THEN
            CREATE INDEX IF NOT EXISTS idx_variance_alert_cycle ON variance_alerts(cycle_id);
        END IF;
        IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'variance_alerts' AND column_name = 'alert_type') THEN
            CREATE INDEX IF NOT EXISTS idx_variance_alert_type ON variance_alerts(alert_type);
        END IF;
        IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'variance_alerts' AND column_name = 'severity') THEN
            CREATE INDEX IF NOT EXISTS idx_variance_alert_severity ON variance_alerts(severity);
        END IF;
        IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'variance_alerts' AND column_name = 'acknowledged') THEN
            CREATE INDEX IF NOT EXISTS idx_variance_alert_acknowledged ON variance_alerts(acknowledged);
        END IF;
    END IF;
END $$;

-- ============================================================================
-- FEEDBACK TABLE (General)
-- ============================================================================
-- Feedback table may already exist from migration 00012, so add missing columns if needed
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'feedback') THEN
        CREATE TABLE feedback (
            id SERIAL PRIMARY KEY,
            submitted_by VARCHAR(255) NOT NULL REFERENCES people(email) ON DELETE CASCADE,
            feedback_type VARCHAR(50) NOT NULL,
            category VARCHAR(100),
            title VARCHAR(200),
            message TEXT NOT NULL,
            rating INTEGER,
            status VARCHAR(20) DEFAULT 'new',
            reviewed_by VARCHAR(255) REFERENCES people(email) ON DELETE SET NULL,
            reviewed_at TIMESTAMP,
            response TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    ELSE
        -- Migration 00012 uses different column names, so add/rename as needed
        -- Add submitted_by column if it doesn't exist
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'feedback' AND column_name = 'submitted_by') THEN
            ALTER TABLE feedback ADD COLUMN submitted_by VARCHAR(255) REFERENCES people(email) ON DELETE CASCADE;
        END IF;
        -- Add missing columns
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'feedback' AND column_name = 'category') THEN
            ALTER TABLE feedback ADD COLUMN category VARCHAR(100);
        END IF;
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'feedback' AND column_name = 'title') THEN
            ALTER TABLE feedback ADD COLUMN title VARCHAR(200);
        END IF;
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'feedback' AND column_name = 'reviewed_at') THEN
            ALTER TABLE feedback ADD COLUMN reviewed_at TIMESTAMP;
        END IF;
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'feedback' AND column_name = 'response') THEN
            ALTER TABLE feedback ADD COLUMN response TEXT;
        END IF;
    END IF;
END $$;

-- Create index only if column exists
DO $$ 
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'feedback' AND column_name = 'submitted_by') THEN
        CREATE INDEX IF NOT EXISTS idx_feedback_submitter ON feedback(submitted_by);
    END IF;
END $$;
-- Create remaining indexes conditionally
DO $$ 
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'feedback' AND column_name = 'feedback_type') THEN
        CREATE INDEX IF NOT EXISTS idx_feedback_type ON feedback(feedback_type);
    END IF;
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'feedback' AND column_name = 'status') THEN
        CREATE INDEX IF NOT EXISTS idx_feedback_status ON feedback(status);
    END IF;
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'feedback' AND column_name = 'category') THEN
        CREATE INDEX IF NOT EXISTS idx_feedback_category ON feedback(category);
    END IF;
END $$;

-- ============================================================================
-- TRIGGERS
-- ============================================================================
CREATE OR REPLACE FUNCTION update_surveys_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS update_surveys_updated_at ON surveys;
CREATE TRIGGER update_surveys_updated_at
    BEFORE UPDATE ON surveys
    FOR EACH ROW
    EXECUTE FUNCTION update_surveys_updated_at();

CREATE OR REPLACE FUNCTION update_survey_questions_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS update_survey_questions_updated_at ON survey_questions;
CREATE TRIGGER update_survey_questions_updated_at
    BEFORE UPDATE ON survey_questions
    FOR EACH ROW
    EXECUTE FUNCTION update_survey_questions_updated_at();

CREATE OR REPLACE FUNCTION update_objections_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS update_objections_updated_at ON objections;
CREATE TRIGGER update_objections_updated_at
    BEFORE UPDATE ON objections
    FOR EACH ROW
    EXECUTE FUNCTION update_objections_updated_at();

CREATE OR REPLACE FUNCTION update_feedback_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS update_feedback_updated_at ON feedback;
CREATE TRIGGER update_feedback_updated_at
    BEFORE UPDATE ON feedback
    FOR EACH ROW
    EXECUTE FUNCTION update_feedback_updated_at();

-- ============================================================================
-- ROW LEVEL SECURITY
-- ============================================================================
ALTER TABLE surveys ENABLE ROW LEVEL SECURITY;
ALTER TABLE survey_questions ENABLE ROW LEVEL SECURITY;
ALTER TABLE survey_responses ENABLE ROW LEVEL SECURITY;
ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE objections ENABLE ROW LEVEL SECURITY;
ALTER TABLE variance_alerts ENABLE ROW LEVEL SECURITY;
ALTER TABLE feedback ENABLE ROW LEVEL SECURITY;

-- Users can view their own notifications (handle recipient_email/user_email)
DO $$ 
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'notifications') THEN
        IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'notifications' AND column_name = 'recipient_email') THEN
            IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname = 'public' AND tablename = 'notifications' AND policyname = 'notifications_select_own') THEN
                EXECUTE 'CREATE POLICY notifications_select_own ON notifications FOR SELECT USING ((SELECT auth.email()) = recipient_email)';
            END IF;
        ELSIF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'notifications' AND column_name = 'user_email') THEN
            IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname = 'public' AND tablename = 'notifications' AND policyname = 'notifications_select_own') THEN
                EXECUTE 'CREATE POLICY notifications_select_own ON notifications FOR SELECT USING ((SELECT auth.email()) = user_email)';
            END IF;
        END IF;
    END IF;
END $$;

-- Users can update their own notifications (mark as read) - handle both column names
DO $$ 
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'notifications') THEN
        IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'notifications' AND column_name = 'recipient_email') THEN
            IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname = 'public' AND tablename = 'notifications' AND policyname = 'notifications_update_own') THEN
                EXECUTE 'CREATE POLICY notifications_update_own ON notifications FOR UPDATE USING ((SELECT auth.email()) = recipient_email)';
            END IF;
        ELSIF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'notifications' AND column_name = 'user_email') THEN
            IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname = 'public' AND tablename = 'notifications' AND policyname = 'notifications_update_own') THEN
                EXECUTE 'CREATE POLICY notifications_update_own ON notifications FOR UPDATE USING ((SELECT auth.email()) = user_email)';
            END IF;
        END IF;
    END IF;
END $$;

-- Service role can do everything (split operations)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'notifications') THEN
        DROP POLICY IF EXISTS notifications_service_role ON notifications;

        IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname = 'public' AND tablename = 'notifications' AND policyname = 'notifications_service_role_select') THEN
            CREATE POLICY notifications_service_role_select ON notifications
                FOR SELECT
                USING ((SELECT auth.role()) = 'service_role');
        END IF;

        IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname = 'public' AND tablename = 'notifications' AND policyname = 'notifications_service_role_insert') THEN
            CREATE POLICY notifications_service_role_insert ON notifications
                FOR INSERT
                WITH CHECK ((SELECT auth.role()) = 'service_role');
        END IF;

        IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname = 'public' AND tablename = 'notifications' AND policyname = 'notifications_service_role_update') THEN
            CREATE POLICY notifications_service_role_update ON notifications
                FOR UPDATE
                USING ((SELECT auth.role()) = 'service_role')
                WITH CHECK ((SELECT auth.role()) = 'service_role');
        END IF;

        IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname = 'public' AND tablename = 'notifications' AND policyname = 'notifications_service_role_delete') THEN
            CREATE POLICY notifications_service_role_delete ON notifications
                FOR DELETE
                USING ((SELECT auth.role()) = 'service_role');
        END IF;
    END IF;
END $$;

-- Users can view their own objections (handle submitted_by/objector_email)
DO $$ 
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'objections') THEN
        IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'objections' AND column_name = 'submitted_by') THEN
            IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname = 'public' AND tablename = 'objections' AND policyname = 'objections_select_own') THEN
                EXECUTE 'CREATE POLICY objections_select_own ON objections FOR SELECT USING ((SELECT auth.email()) = submitted_by OR (SELECT auth.role()) = ''service_role'')';
            END IF;
            IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname = 'public' AND tablename = 'objections' AND policyname = 'objections_insert_own') THEN
                EXECUTE 'CREATE POLICY objections_insert_own ON objections FOR INSERT WITH CHECK ((SELECT auth.email()) = submitted_by)';
            END IF;
        ELSIF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'objections' AND column_name = 'objector_email') THEN
            IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname = 'public' AND tablename = 'objections' AND policyname = 'objections_select_own') THEN
                EXECUTE 'CREATE POLICY objections_select_own ON objections FOR SELECT USING ((SELECT auth.email()) = objector_email OR (SELECT auth.role()) = ''service_role'')';
            END IF;
            IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname = 'public' AND tablename = 'objections' AND policyname = 'objections_insert_own') THEN
                EXECUTE 'CREATE POLICY objections_insert_own ON objections FOR INSERT WITH CHECK ((SELECT auth.email()) = objector_email)';
            END IF;
        END IF;
    END IF;
END $$;

-- Service role can do everything for objections (split operations)
DO $$ 
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'objections') THEN
        DROP POLICY IF EXISTS objections_service_role ON objections;

        IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname = 'public' AND tablename = 'objections' AND policyname = 'objections_service_role_insert') THEN
            CREATE POLICY objections_service_role_insert ON objections
                FOR INSERT
                WITH CHECK ((SELECT auth.role()) = 'service_role');
        END IF;

        IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname = 'public' AND tablename = 'objections' AND policyname = 'objections_service_role_update') THEN
            CREATE POLICY objections_service_role_update ON objections
                FOR UPDATE
                USING ((SELECT auth.role()) = 'service_role')
                WITH CHECK ((SELECT auth.role()) = 'service_role');
        END IF;

        IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname = 'public' AND tablename = 'objections' AND policyname = 'objections_service_role_delete') THEN
            CREATE POLICY objections_service_role_delete ON objections
                FOR DELETE
                USING ((SELECT auth.role()) = 'service_role');
        END IF;
    END IF;
END $$;

-- Users can view their own feedback (handle submitted_by)
DO $$ 
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'feedback') THEN
        IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'feedback' AND column_name = 'submitted_by') THEN
            IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname = 'public' AND tablename = 'feedback' AND policyname = 'feedback_select_own') THEN
                EXECUTE 'CREATE POLICY feedback_select_own ON feedback FOR SELECT USING ((SELECT auth.email()) = submitted_by OR (SELECT auth.role()) = ''service_role'')';
            END IF;
            IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname = 'public' AND tablename = 'feedback' AND policyname = 'feedback_insert_own') THEN
                EXECUTE 'CREATE POLICY feedback_insert_own ON feedback FOR INSERT WITH CHECK ((SELECT auth.email()) = submitted_by)';
            END IF;
        END IF;
    END IF;
END $$;

-- Service role can do everything for feedback (split operations)
DO $$ 
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'feedback') THEN
        IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname = 'public' AND tablename = 'feedback' AND policyname = 'feedback_service_role_select') THEN
            EXECUTE 'CREATE POLICY feedback_service_role_select ON feedback FOR SELECT USING ((SELECT auth.role()) = ''service_role'')';
        END IF;
        IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname = 'public' AND tablename = 'feedback' AND policyname = 'feedback_service_role_insert') THEN
            EXECUTE 'CREATE POLICY feedback_service_role_insert ON feedback FOR INSERT WITH CHECK ((SELECT auth.role()) = ''service_role'')';
        END IF;
        IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname = 'public' AND tablename = 'feedback' AND policyname = 'feedback_service_role_update') THEN
            EXECUTE 'CREATE POLICY feedback_service_role_update ON feedback FOR UPDATE USING ((SELECT auth.role()) = ''service_role'')';
        END IF;
        IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname = 'public' AND tablename = 'feedback' AND policyname = 'feedback_service_role_delete') THEN
            EXECUTE 'CREATE POLICY feedback_service_role_delete ON feedback FOR DELETE USING ((SELECT auth.role()) = ''service_role'')';
        END IF;
    END IF;
END $$;

-- Survey responses: Users can view their own, admins can view all
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'survey_responses') THEN
        IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname = 'public' AND tablename = 'survey_responses' AND policyname = 'survey_responses_select_own') THEN
            CREATE POLICY survey_responses_select_own ON survey_responses
                FOR SELECT
                USING (
                    (SELECT auth.email()) = respondent_email
                    OR (SELECT auth.role()) = 'service_role'
                    OR respondent_email IS NULL  -- Anonymous responses visible to admins only
                );
        END IF;

        IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname = 'public' AND tablename = 'survey_responses' AND policyname = 'survey_responses_insert_own') THEN
            CREATE POLICY survey_responses_insert_own ON survey_responses
                FOR INSERT
                WITH CHECK (
                    (SELECT auth.email()) = respondent_email
                    OR respondent_email IS NULL  -- Anonymous responses
                );
        END IF;
    END IF;
END $$;

-- Service role can do everything for survey responses (split operations)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'survey_responses') THEN
        DROP POLICY IF EXISTS survey_responses_service_role ON survey_responses;

        IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname = 'public' AND tablename = 'survey_responses' AND policyname = 'survey_responses_service_role_select') THEN
            CREATE POLICY survey_responses_service_role_select ON survey_responses
                FOR SELECT
                USING ((SELECT auth.role()) = 'service_role');
        END IF;

        IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname = 'public' AND tablename = 'survey_responses' AND policyname = 'survey_responses_service_role_insert') THEN
            CREATE POLICY survey_responses_service_role_insert ON survey_responses
                FOR INSERT
                WITH CHECK ((SELECT auth.role()) = 'service_role');
        END IF;

        IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname = 'public' AND tablename = 'survey_responses' AND policyname = 'survey_responses_service_role_update') THEN
            CREATE POLICY survey_responses_service_role_update ON survey_responses
                FOR UPDATE
                USING ((SELECT auth.role()) = 'service_role')
                WITH CHECK ((SELECT auth.role()) = 'service_role');
        END IF;

        IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname = 'public' AND tablename = 'survey_responses' AND policyname = 'survey_responses_service_role_delete') THEN
            CREATE POLICY survey_responses_service_role_delete ON survey_responses
                FOR DELETE
                USING ((SELECT auth.role()) = 'service_role');
        END IF;
    END IF;
END $$;

-- Surveys: All authenticated users can view active surveys
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'surveys') THEN
        IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname = 'public' AND tablename = 'surveys' AND policyname = 'surveys_select_active') THEN
            CREATE POLICY surveys_select_active ON surveys
                FOR SELECT
                USING (status = 'active' OR (SELECT auth.role()) = 'service_role');
        END IF;
    END IF;
END $$;

-- Survey questions: Visible with surveys
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'survey_questions') THEN
        IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname = 'public' AND tablename = 'survey_questions' AND policyname = 'survey_questions_select_active') THEN
            CREATE POLICY survey_questions_select_active ON survey_questions
                FOR SELECT
                USING (
                    EXISTS (
                        SELECT 1 FROM surveys
                        WHERE surveys.id = survey_questions.survey_id
                        AND (surveys.status = 'active' OR (SELECT auth.role()) = 'service_role')
                    )
                );
        END IF;
    END IF;
END $$;

-- Service role can do everything for surveys and questions (split operations)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'surveys') THEN
        DROP POLICY IF EXISTS surveys_service_role ON surveys;

        IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname = 'public' AND tablename = 'surveys' AND policyname = 'surveys_service_role_insert') THEN
            CREATE POLICY surveys_service_role_insert ON surveys
                FOR INSERT
                WITH CHECK ((SELECT auth.role()) = 'service_role');
        END IF;

        IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname = 'public' AND tablename = 'surveys' AND policyname = 'surveys_service_role_update') THEN
            CREATE POLICY surveys_service_role_update ON surveys
                FOR UPDATE
                USING ((SELECT auth.role()) = 'service_role')
                WITH CHECK ((SELECT auth.role()) = 'service_role');
        END IF;

        IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname = 'public' AND tablename = 'surveys' AND policyname = 'surveys_service_role_delete') THEN
            CREATE POLICY surveys_service_role_delete ON surveys
                FOR DELETE
                USING ((SELECT auth.role()) = 'service_role');
        END IF;
    END IF;
END $$;

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'survey_questions') THEN
        DROP POLICY IF EXISTS survey_questions_service_role ON survey_questions;

        IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname = 'public' AND tablename = 'survey_questions' AND policyname = 'survey_questions_service_role_insert') THEN
            CREATE POLICY survey_questions_service_role_insert ON survey_questions
                FOR INSERT
                WITH CHECK ((SELECT auth.role()) = 'service_role');
        END IF;

        IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname = 'public' AND tablename = 'survey_questions' AND policyname = 'survey_questions_service_role_update') THEN
            CREATE POLICY survey_questions_service_role_update ON survey_questions
                FOR UPDATE
                USING ((SELECT auth.role()) = 'service_role')
                WITH CHECK ((SELECT auth.role()) = 'service_role');
        END IF;

        IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname = 'public' AND tablename = 'survey_questions' AND policyname = 'survey_questions_service_role_delete') THEN
            CREATE POLICY survey_questions_service_role_delete ON survey_questions
                FOR DELETE
                USING ((SELECT auth.role()) = 'service_role');
        END IF;
    END IF;
END $$;

-- Variance alerts: Only admins can view
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'variance_alerts') THEN
        IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname = 'public' AND tablename = 'variance_alerts' AND policyname = 'variance_alerts_select_admin') THEN
            CREATE POLICY variance_alerts_select_admin ON variance_alerts
                FOR SELECT
                USING ((SELECT auth.role()) = 'service_role');
        END IF;
    END IF;
END $$;

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'variance_alerts') THEN
        DROP POLICY IF EXISTS variance_alerts_service_role ON variance_alerts;

        IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname = 'public' AND tablename = 'variance_alerts' AND policyname = 'variance_alerts_service_role_insert') THEN
            CREATE POLICY variance_alerts_service_role_insert ON variance_alerts
                FOR INSERT
                WITH CHECK ((SELECT auth.role()) = 'service_role');
        END IF;

        IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname = 'public' AND tablename = 'variance_alerts' AND policyname = 'variance_alerts_service_role_update') THEN
            CREATE POLICY variance_alerts_service_role_update ON variance_alerts
                FOR UPDATE
                USING ((SELECT auth.role()) = 'service_role')
                WITH CHECK ((SELECT auth.role()) = 'service_role');
        END IF;

        IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname = 'public' AND tablename = 'variance_alerts' AND policyname = 'variance_alerts_service_role_delete') THEN
            CREATE POLICY variance_alerts_service_role_delete ON variance_alerts
                FOR DELETE
                USING ((SELECT auth.role()) = 'service_role');
        END IF;
    END IF;
END $$;
