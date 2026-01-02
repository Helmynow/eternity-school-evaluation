-- Migration: Survey Identity Management System
-- Creates tables for hybrid identity survey system with flexible identity controller

-- ============================================================================
-- SURVEY IDENTITY PREFERENCES TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS survey_identity_preferences (
    id SERIAL PRIMARY KEY,
    user_email VARCHAR(255) NOT NULL REFERENCES people(email) ON DELETE CASCADE,
    survey_id INTEGER REFERENCES surveys(id) ON DELETE CASCADE,
    identity_mode VARCHAR(20) NOT NULL, -- anonymous, identified, conditional
    privacy_level VARCHAR(20), -- maximum, high, medium, low
    retention_days INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_user_survey_preference UNIQUE(user_email, survey_id)
);

CREATE INDEX IF NOT EXISTS idx_survey_identity_user ON survey_identity_preferences(user_email);
CREATE INDEX IF NOT EXISTS idx_survey_identity_survey ON survey_identity_preferences(survey_id);
CREATE INDEX IF NOT EXISTS idx_survey_identity_mode ON survey_identity_preferences(identity_mode);

-- ============================================================================
-- SURVEY IDENTITY REVEALS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS survey_identity_reveals (
    id SERIAL PRIMARY KEY,
    user_email VARCHAR(255) NOT NULL REFERENCES people(email) ON DELETE CASCADE,
    survey_id INTEGER REFERENCES surveys(id) ON DELETE CASCADE,
    reveal_method VARCHAR(50) NOT NULL, -- full, partial_role, partial_department, gradual, consent_based
    revealed_info JSONB, -- What information was revealed
    target VARCHAR(255), -- Who the reveal was for (optional)
    consent_confirmed BOOLEAN DEFAULT FALSE,
    next_reveal_date TIMESTAMP, -- For gradual reveals
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_survey_reveal_user ON survey_identity_reveals(user_email);
CREATE INDEX IF NOT EXISTS idx_survey_reveal_survey ON survey_identity_reveals(survey_id);
CREATE INDEX IF NOT EXISTS idx_survey_reveal_method ON survey_identity_reveals(reveal_method);

-- ============================================================================
-- TRIGGERS
-- ============================================================================
CREATE OR REPLACE FUNCTION update_survey_identity_preferences_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_survey_identity_preferences_updated_at
    BEFORE UPDATE ON survey_identity_preferences
    FOR EACH ROW
    EXECUTE FUNCTION update_survey_identity_preferences_updated_at();

-- ============================================================================
-- ROW LEVEL SECURITY
-- ============================================================================
ALTER TABLE survey_identity_preferences ENABLE ROW LEVEL SECURITY;
ALTER TABLE survey_identity_reveals ENABLE ROW LEVEL SECURITY;

-- Users can view their own preferences
CREATE POLICY survey_identity_preferences_select ON survey_identity_preferences
    FOR SELECT
    USING ((select auth.email()) = user_email);

-- Users can insert/update their own preferences
CREATE POLICY survey_identity_preferences_insert ON survey_identity_preferences
    FOR INSERT
    WITH CHECK ((select auth.email()) = user_email);

CREATE POLICY survey_identity_preferences_update ON survey_identity_preferences
    FOR UPDATE
    USING ((select auth.email()) = user_email);

CREATE POLICY survey_identity_preferences_delete ON survey_identity_preferences
    FOR DELETE
    USING ((select auth.email()) = user_email);

-- Service role can do everything
CREATE POLICY survey_identity_preferences_service_role_select ON survey_identity_preferences
    FOR SELECT
    USING ((select auth.role()) = 'service_role');

CREATE POLICY survey_identity_preferences_service_role_insert ON survey_identity_preferences
    FOR INSERT
    WITH CHECK ((select auth.role()) = 'service_role');

CREATE POLICY survey_identity_preferences_service_role_update ON survey_identity_preferences
    FOR UPDATE
    USING ((select auth.role()) = 'service_role')
    WITH CHECK ((select auth.role()) = 'service_role');

CREATE POLICY survey_identity_preferences_service_role_delete ON survey_identity_preferences
    FOR DELETE
    USING ((select auth.role()) = 'service_role');

-- Users can view their own reveals
CREATE POLICY survey_identity_reveals_select ON survey_identity_reveals
    FOR SELECT
    USING ((select auth.email()) = user_email);

-- Users can insert their own reveals
CREATE POLICY survey_identity_reveals_insert ON survey_identity_reveals
    FOR INSERT
    WITH CHECK ((select auth.email()) = user_email);

-- Service role can do everything
CREATE POLICY survey_identity_reveals_service_role_select ON survey_identity_reveals
    FOR SELECT
    USING ((select auth.role()) = 'service_role');

CREATE POLICY survey_identity_reveals_service_role_insert ON survey_identity_reveals
    FOR INSERT
    WITH CHECK ((select auth.role()) = 'service_role');

CREATE POLICY survey_identity_reveals_service_role_update ON survey_identity_reveals
    FOR UPDATE
    USING ((select auth.role()) = 'service_role')
    WITH CHECK ((select auth.role()) = 'service_role');

CREATE POLICY survey_identity_reveals_service_role_delete ON survey_identity_reveals
    FOR DELETE
    USING ((select auth.role()) = 'service_role');
