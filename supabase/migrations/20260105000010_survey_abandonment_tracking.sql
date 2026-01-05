-- Migration: Survey abandonment tracking + session timeout support
-- Adds session lifecycle fields to survey_responses (and hybrid_identity_sessions for convenience).

-- ==========================================================================
-- survey_responses: add columns
-- ==========================================================================
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name = 'survey_responses'
    ) THEN
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'survey_responses' AND column_name = 'started_at') THEN
            ALTER TABLE survey_responses ADD COLUMN started_at TIMESTAMP;
        END IF;

        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'survey_responses' AND column_name = 'abandoned_at') THEN
            ALTER TABLE survey_responses ADD COLUMN abandoned_at TIMESTAMP NULL;
        END IF;

        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'survey_responses' AND column_name = 'session_status') THEN
            ALTER TABLE survey_responses ADD COLUMN session_status VARCHAR(20) NULL;
        END IF;

        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'survey_responses' AND column_name = 'abandoned_confidence') THEN
            ALTER TABLE survey_responses ADD COLUMN abandoned_confidence VARCHAR(10) NULL;
        END IF;
    END IF;
END $$;

-- Defaults (safe if column exists)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'survey_responses' AND column_name = 'started_at') THEN
        ALTER TABLE survey_responses ALTER COLUMN started_at SET DEFAULT CURRENT_TIMESTAMP;
    END IF;
END $$;

-- Backfill started_at conservatively from created_at/submitted_at
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'survey_responses' AND column_name = 'started_at') THEN
        UPDATE survey_responses
        SET started_at = COALESCE(
            (CASE WHEN EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'survey_responses' AND column_name = 'created_at') THEN created_at ELSE NULL END),
            submitted_at,
            CURRENT_TIMESTAMP
        )
        WHERE started_at IS NULL;
    END IF;
END $$;

-- Selective (HIGH confidence) historical backfill for abandoned_at
-- Only when:
-- - created_at exists
-- - response content is empty
-- - submitted_at - created_at is extremely short (< 5 seconds)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'survey_responses' AND column_name = 'created_at') THEN
        UPDATE survey_responses
        SET abandoned_at = submitted_at,
            session_status = COALESCE(session_status, 'timeout'),
            abandoned_confidence = 'HIGH'
        WHERE abandoned_at IS NULL
          AND submitted_at IS NOT NULL
          AND created_at IS NOT NULL
          AND submitted_at - created_at < INTERVAL '5 seconds'
          AND response_text IS NULL
          AND response_value IS NULL;
    END IF;
END $$;

-- Indexes (only if columns exist)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'survey_responses' AND column_name = 'abandoned_at') THEN
        CREATE INDEX IF NOT EXISTS idx_survey_response_abandoned_at ON survey_responses(abandoned_at);
    END IF;
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'survey_responses' AND column_name = 'session_status') THEN
        CREATE INDEX IF NOT EXISTS idx_survey_response_session_status ON survey_responses(session_status);
    END IF;
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'survey_responses' AND column_name = 'started_at') THEN
        CREATE INDEX IF NOT EXISTS idx_survey_response_started_at ON survey_responses(started_at);
    END IF;
END $$;

-- ==========================================================================
-- hybrid_identity_sessions: add columns (optional but useful for analytics)
-- ==========================================================================
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name = 'hybrid_identity_sessions'
    ) THEN
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'hybrid_identity_sessions' AND column_name = 'session_status') THEN
            ALTER TABLE hybrid_identity_sessions ADD COLUMN session_status VARCHAR(20) DEFAULT 'active';
        END IF;
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'hybrid_identity_sessions' AND column_name = 'abandoned_at') THEN
            ALTER TABLE hybrid_identity_sessions ADD COLUMN abandoned_at TIMESTAMP NULL;
        END IF;
    END IF;
END $$;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name = 'hybrid_identity_sessions'
    ) THEN
        IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'hybrid_identity_sessions' AND column_name = 'session_status') THEN
            CREATE INDEX IF NOT EXISTS idx_hybrid_identity_sessions_status ON hybrid_identity_sessions(session_status);
        END IF;
        IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'hybrid_identity_sessions' AND column_name = 'abandoned_at') THEN
            CREATE INDEX IF NOT EXISTS idx_hybrid_identity_sessions_abandoned_at ON hybrid_identity_sessions(abandoned_at);
        END IF;
    END IF;
END $$;
