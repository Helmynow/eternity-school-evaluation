-- Migration: Conditional Anonymity Engine
-- Creates table for conditional reveal configurations

-- ============================================================================
-- SURVEY CONDITIONAL REVEALS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS survey_conditional_reveals (
    id SERIAL PRIMARY KEY,
    user_email VARCHAR(255) NOT NULL REFERENCES people(email) ON DELETE CASCADE,
    survey_id INTEGER REFERENCES surveys(id) ON DELETE CASCADE,
    reveal_conditions JSONB NOT NULL, -- Stored conditions configuration
    trigger_events JSONB NOT NULL, -- Stored trigger events configuration
    notification_preferences JSONB, -- Stored notification preferences
    status VARCHAR(20) DEFAULT 'active', -- active, paused, completed
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_user_survey_conditional UNIQUE(user_email, survey_id)
);

CREATE INDEX IF NOT EXISTS idx_survey_conditional_user ON survey_conditional_reveals(user_email);
CREATE INDEX IF NOT EXISTS idx_survey_conditional_survey ON survey_conditional_reveals(survey_id);
CREATE INDEX IF NOT EXISTS idx_survey_conditional_status ON survey_conditional_reveals(status);

-- ============================================================================
-- TRIGGERS
-- ============================================================================
CREATE OR REPLACE FUNCTION update_survey_conditional_reveals_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_survey_conditional_reveals_updated_at
    BEFORE UPDATE ON survey_conditional_reveals
    FOR EACH ROW
    EXECUTE FUNCTION update_survey_conditional_reveals_updated_at();

-- ============================================================================
-- ROW LEVEL SECURITY
-- ============================================================================
ALTER TABLE survey_conditional_reveals ENABLE ROW LEVEL SECURITY;

-- Users can view their own conditional reveals
CREATE POLICY survey_conditional_reveals_select ON survey_conditional_reveals
    FOR SELECT
    USING ((select auth.email()) = user_email);

-- Users can insert/update their own conditional reveals
CREATE POLICY survey_conditional_reveals_insert ON survey_conditional_reveals
    FOR INSERT
    WITH CHECK ((select auth.email()) = user_email);

CREATE POLICY survey_conditional_reveals_update ON survey_conditional_reveals
    FOR UPDATE
    USING ((select auth.email()) = user_email);

CREATE POLICY survey_conditional_reveals_delete ON survey_conditional_reveals
    FOR DELETE
    USING ((select auth.email()) = user_email);

-- Service role can do everything
CREATE POLICY survey_conditional_reveals_service_role_select ON survey_conditional_reveals
    FOR SELECT
    USING ((select auth.role()) = 'service_role');

CREATE POLICY survey_conditional_reveals_service_role_insert ON survey_conditional_reveals
    FOR INSERT
    WITH CHECK ((select auth.role()) = 'service_role');

CREATE POLICY survey_conditional_reveals_service_role_update ON survey_conditional_reveals
    FOR UPDATE
    USING ((select auth.role()) = 'service_role')
    WITH CHECK ((select auth.role()) = 'service_role');

CREATE POLICY survey_conditional_reveals_service_role_delete ON survey_conditional_reveals
    FOR DELETE
    USING ((select auth.role()) = 'service_role');
