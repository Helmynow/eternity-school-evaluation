-- Migration: Add new features tables
-- Objections, Announcements, Notifications, Surveys, Feedback

-- ============================================================================
-- OBJECTIONS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS objections (
    id SERIAL PRIMARY KEY,
    eom_nominee_id INTEGER REFERENCES eom_nominees(id) ON DELETE CASCADE,
    objector_email VARCHAR(255) REFERENCES people(email) ON DELETE CASCADE,
    reason TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'pending', -- pending, reviewed, resolved, dismissed
    reviewed_by VARCHAR(255) REFERENCES people(email),
    reviewed_at TIMESTAMP,
    resolution_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

DO $$ 
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'objections') THEN
        IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'objections' AND column_name = 'eom_nominee_id') THEN
            CREATE INDEX IF NOT EXISTS idx_objections_nominee ON objections(eom_nominee_id);
        END IF;
        IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'objections' AND column_name = 'status') THEN
            CREATE INDEX IF NOT EXISTS idx_objections_status ON objections(status);
        END IF;
        IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'objections' AND column_name = 'objector_email') THEN
            CREATE INDEX IF NOT EXISTS idx_objections_objector ON objections(objector_email);
        ELSIF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'objections' AND column_name = 'submitted_by') THEN
            CREATE INDEX IF NOT EXISTS idx_objection_submitter ON objections(submitted_by);
        END IF;
    END IF;
END $$;

-- ============================================================================
-- ANNOUNCEMENTS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS announcements (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    author_email VARCHAR(255) REFERENCES people(email),
    priority VARCHAR(20) DEFAULT 'normal', -- low, normal, high, urgent
    target_audience VARCHAR(50) DEFAULT 'all', -- all, ceo, pnc, department_head, staff
    is_active BOOLEAN DEFAULT TRUE,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_announcements_active ON announcements(is_active);
CREATE INDEX IF NOT EXISTS idx_announcements_priority ON announcements(priority);

-- ============================================================================
-- NOTIFICATIONS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS notifications (
    id SERIAL PRIMARY KEY,
    user_email VARCHAR(255) REFERENCES people(email) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL, -- vote_reminder, evaluation_due, winner_announced, objection_submitted, etc.
    title VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    link VARCHAR(500),
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

DO $$ 
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'notifications' AND column_name = 'user_email') THEN
        CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_email);
    ELSIF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'notifications' AND column_name = 'recipient_email') THEN
        CREATE INDEX IF NOT EXISTS idx_notifications_recipient ON notifications(recipient_email);
    END IF;
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'notifications' AND column_name = 'is_read') THEN
        CREATE INDEX IF NOT EXISTS idx_notifications_read ON notifications(is_read);
    ELSIF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'notifications' AND column_name = 'read') THEN
        CREATE INDEX IF NOT EXISTS idx_notifications_read ON notifications(read);
    END IF;
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'notifications' AND column_name = 'created_at') THEN
        CREATE INDEX IF NOT EXISTS idx_notifications_created ON notifications(created_at);
    END IF;
END $$;

-- ============================================================================
-- SURVEYS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS surveys (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    cycle_id INTEGER REFERENCES cycles(id),
    created_by VARCHAR(255) REFERENCES people(email),
    status VARCHAR(20) DEFAULT 'draft', -- draft, active, closed
    start_date TIMESTAMP,
    end_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS survey_questions (
    id SERIAL PRIMARY KEY,
    survey_id INTEGER REFERENCES surveys(id) ON DELETE CASCADE,
    question_text TEXT NOT NULL,
    question_type VARCHAR(50) NOT NULL, -- text, multiple_choice, rating, yes_no
    options JSONB, -- For multiple choice questions
    is_required BOOLEAN DEFAULT FALSE,
    order_index INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS survey_responses (
    id SERIAL PRIMARY KEY,
    survey_id INTEGER REFERENCES surveys(id) ON DELETE CASCADE,
    respondent_email VARCHAR(255) REFERENCES people(email),
    question_id INTEGER REFERENCES survey_questions(id) ON DELETE CASCADE,
    response_text TEXT,
    response_value JSONB, -- For structured responses
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_surveys_cycle ON surveys(cycle_id);
CREATE INDEX IF NOT EXISTS idx_surveys_status ON surveys(status);
CREATE INDEX IF NOT EXISTS idx_survey_responses_survey ON survey_responses(survey_id);
CREATE INDEX IF NOT EXISTS idx_survey_responses_respondent ON survey_responses(respondent_email);

-- ============================================================================
-- FEEDBACK TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS feedback (
    id SERIAL PRIMARY KEY,
    feedback_type VARCHAR(50) NOT NULL, -- system, process, evaluation, general
    submitted_by VARCHAR(255) REFERENCES people(email),
    title VARCHAR(200),
    content TEXT NOT NULL,
    rating INTEGER, -- 1-5 rating
    status VARCHAR(20) DEFAULT 'new', -- new, acknowledged, in_progress, resolved, closed
    responded_by VARCHAR(255) REFERENCES people(email),
    response TEXT,
    responded_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_feedback_type ON feedback(feedback_type);
CREATE INDEX IF NOT EXISTS idx_feedback_status ON feedback(status);
CREATE INDEX IF NOT EXISTS idx_feedback_submitted_by ON feedback(submitted_by);

-- ============================================================================
-- APPROVAL WORKFLOW TABLES
-- ============================================================================
-- Add approval fields to existing tables
ALTER TABLE eom_nominees ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'pending'; -- pending, approved, rejected
ALTER TABLE eom_nominees ADD COLUMN IF NOT EXISTS approved_by VARCHAR(255) REFERENCES people(email);
ALTER TABLE eom_nominees ADD COLUMN IF NOT EXISTS approved_at TIMESTAMP;
ALTER TABLE eom_nominees ADD COLUMN IF NOT EXISTS rejection_reason TEXT;
ALTER TABLE eom_nominees ADD COLUMN IF NOT EXISTS can_edit BOOLEAN DEFAULT TRUE;

ALTER TABLE evaluations ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'draft'; -- draft, submitted, approved, rejected
ALTER TABLE evaluations ADD COLUMN IF NOT EXISTS approved_by VARCHAR(255) REFERENCES people(email);
ALTER TABLE evaluations ADD COLUMN IF NOT EXISTS approved_at TIMESTAMP;
ALTER TABLE evaluations ADD COLUMN IF NOT EXISTS rejection_reason TEXT;
ALTER TABLE evaluations ADD COLUMN IF NOT EXISTS can_edit BOOLEAN DEFAULT TRUE;

-- ============================================================================
-- AI FEEDBACK TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS ai_feedback (
    id SERIAL PRIMARY KEY,
    entity_type VARCHAR(50) NOT NULL, -- evaluation, nomination, cycle
    entity_id INTEGER NOT NULL,
    feedback_type VARCHAR(50) NOT NULL, -- bias_detection, improvement_suggestions, performance_insights
    content TEXT NOT NULL,
    confidence_score FLOAT, -- 0-1
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reviewed_by VARCHAR(255) REFERENCES people(email),
    reviewed_at TIMESTAMP,
    is_helpful BOOLEAN
);

CREATE INDEX IF NOT EXISTS idx_ai_feedback_entity ON ai_feedback(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_ai_feedback_type ON ai_feedback(feedback_type);

-- ============================================================================
-- TRIGGERS FOR UPDATED_AT
-- ============================================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_objections_updated_at ON objections;
CREATE TRIGGER update_objections_updated_at BEFORE UPDATE ON objections
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_announcements_updated_at ON announcements;
CREATE TRIGGER update_announcements_updated_at BEFORE UPDATE ON announcements
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_surveys_updated_at ON surveys;
CREATE TRIGGER update_surveys_updated_at BEFORE UPDATE ON surveys
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_feedback_updated_at ON feedback;
CREATE TRIGGER update_feedback_updated_at BEFORE UPDATE ON feedback
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- RLS POLICIES
-- ============================================================================
ALTER TABLE objections ENABLE ROW LEVEL SECURITY;
ALTER TABLE announcements ENABLE ROW LEVEL SECURITY;
ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE surveys ENABLE ROW LEVEL SECURITY;
ALTER TABLE survey_questions ENABLE ROW LEVEL SECURITY;
ALTER TABLE survey_responses ENABLE ROW LEVEL SECURITY;
ALTER TABLE feedback ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_feedback ENABLE ROW LEVEL SECURITY;

-- Basic policies (can be refined later)
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies WHERE schemaname = 'public' AND tablename = 'objections' AND policyname = 'objections_select'
    ) THEN
        CREATE POLICY objections_select ON objections FOR SELECT USING (true);
    END IF;
END $$;

DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies WHERE schemaname = 'public' AND tablename = 'announcements' AND policyname = 'announcements_select'
    ) THEN
        CREATE POLICY announcements_select ON announcements FOR SELECT USING (is_active = true OR auth.role() = 'authenticated');
    END IF;
END $$;

DO $$ BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'notifications') THEN
        IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'notifications' AND column_name = 'user_email') THEN
            IF NOT EXISTS (
                SELECT 1 FROM pg_policies WHERE schemaname = 'public' AND tablename = 'notifications' AND policyname = 'notifications_select'
            ) THEN
                CREATE POLICY notifications_select ON notifications FOR SELECT USING (user_email = auth.email() OR auth.role() = 'authenticated');
            END IF;
        ELSIF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'notifications' AND column_name = 'recipient_email') THEN
            IF NOT EXISTS (
                SELECT 1 FROM pg_policies WHERE schemaname = 'public' AND tablename = 'notifications' AND policyname = 'notifications_select'
            ) THEN
                CREATE POLICY notifications_select ON notifications FOR SELECT USING (recipient_email = auth.email() OR auth.role() = 'authenticated');
            END IF;
        END IF;
    END IF;
END $$;

DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies WHERE schemaname = 'public' AND tablename = 'surveys' AND policyname = 'surveys_select'
    ) THEN
        CREATE POLICY surveys_select ON surveys FOR SELECT USING (status != 'draft' OR auth.role() = 'authenticated');
    END IF;
END $$;

DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies WHERE schemaname = 'public' AND tablename = 'feedback' AND policyname = 'feedback_select'
    ) THEN
        CREATE POLICY feedback_select ON feedback FOR SELECT USING (submitted_by = auth.email() OR auth.role() = 'authenticated');
    END IF;
END $$;
