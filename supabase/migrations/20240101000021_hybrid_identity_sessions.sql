-- Migration: Hybrid Identity session persistence
-- Stores session tokens (hashed) to allow cross-request survey flows.

CREATE TABLE IF NOT EXISTS hybrid_identity_sessions (
    id SERIAL PRIMARY KEY,
    token_hash VARCHAR(64) NOT NULL UNIQUE,
    user_email VARCHAR(255) NOT NULL REFERENCES people(email) ON DELETE CASCADE,
    identity_mode VARCHAR(20) NOT NULL,
    survey_id INTEGER REFERENCES surveys(id) ON DELETE SET NULL,
    permissions JSONB DEFAULT '{}'::jsonb,
    consent_granted JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP DEFAULT (CURRENT_TIMESTAMP + INTERVAL '24 hours')
);

CREATE INDEX IF NOT EXISTS idx_hybrid_identity_sessions_user ON hybrid_identity_sessions(user_email);
CREATE INDEX IF NOT EXISTS idx_hybrid_identity_sessions_survey ON hybrid_identity_sessions(survey_id);
CREATE INDEX IF NOT EXISTS idx_hybrid_identity_sessions_last_activity ON hybrid_identity_sessions(last_activity);

-- Row Level Security
ALTER TABLE hybrid_identity_sessions ENABLE ROW LEVEL SECURITY;

-- Users can view/manage their own sessions
DROP POLICY IF EXISTS hybrid_identity_sessions_select ON hybrid_identity_sessions;
CREATE POLICY hybrid_identity_sessions_select ON hybrid_identity_sessions
    FOR SELECT
    USING ((select auth.email()) = user_email);

DROP POLICY IF EXISTS hybrid_identity_sessions_insert ON hybrid_identity_sessions;
CREATE POLICY hybrid_identity_sessions_insert ON hybrid_identity_sessions
    FOR INSERT
    WITH CHECK ((select auth.email()) = user_email);

DROP POLICY IF EXISTS hybrid_identity_sessions_update ON hybrid_identity_sessions;
CREATE POLICY hybrid_identity_sessions_update ON hybrid_identity_sessions
    FOR UPDATE
    USING ((select auth.email()) = user_email);

DROP POLICY IF EXISTS hybrid_identity_sessions_delete ON hybrid_identity_sessions;
CREATE POLICY hybrid_identity_sessions_delete ON hybrid_identity_sessions
    FOR DELETE
    USING ((select auth.email()) = user_email);

-- Service role can do everything
DROP POLICY IF EXISTS hybrid_identity_sessions_service_role_select ON hybrid_identity_sessions;
CREATE POLICY hybrid_identity_sessions_service_role_select ON hybrid_identity_sessions
    FOR SELECT
    USING ((select auth.role()) = 'service_role');

DROP POLICY IF EXISTS hybrid_identity_sessions_service_role_insert ON hybrid_identity_sessions;
CREATE POLICY hybrid_identity_sessions_service_role_insert ON hybrid_identity_sessions
    FOR INSERT
    WITH CHECK ((select auth.role()) = 'service_role');

DROP POLICY IF EXISTS hybrid_identity_sessions_service_role_update ON hybrid_identity_sessions;
CREATE POLICY hybrid_identity_sessions_service_role_update ON hybrid_identity_sessions
    FOR UPDATE
    USING ((select auth.role()) = 'service_role')
    WITH CHECK ((select auth.role()) = 'service_role');

DROP POLICY IF EXISTS hybrid_identity_sessions_service_role_delete ON hybrid_identity_sessions;
CREATE POLICY hybrid_identity_sessions_service_role_delete ON hybrid_identity_sessions
    FOR DELETE
    USING ((select auth.role()) = 'service_role');

