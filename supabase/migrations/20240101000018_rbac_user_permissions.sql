-- Migration: RBAC User Permissions System
-- Creates user_permissions table for time-based permission management

-- ============================================================================
-- CREATE PERMISSION TYPE ENUM
-- ============================================================================

DO $$ BEGIN
    CREATE TYPE permission_type AS ENUM (
        'create_evaluation',
        'view_evaluation',
        'edit_evaluation',
        'delete_evaluation',
        'nominate_eom',
        'vote_eom',
        'view_eom_results',
        'manage_eom_cycles',
        'manage_staff',
        'manage_cycles',
        'view_reports',
        'export_data',
        'manage_settings',
        'grant_permissions',
        'revoke_permissions',
        'manage_roles',
        'create_survey',
        'view_survey',
        'respond_survey',
        'view_survey_results'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- ============================================================================
-- CREATE USER_PERMISSIONS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS user_permissions (
    id SERIAL PRIMARY KEY,
    user_email VARCHAR(255) NOT NULL,
    permission_type permission_type NOT NULL,
    granted_by VARCHAR(255) NOT NULL,
    granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    expires_at TIMESTAMP,  -- NULL = unlimited
    revoked_at TIMESTAMP,
    revoked_by VARCHAR(255),
    metadata JSONB DEFAULT '{}'::jsonb,
    
    CONSTRAINT user_permissions_user_email_fkey FOREIGN KEY (user_email) REFERENCES people(email) ON DELETE CASCADE,
    CONSTRAINT user_permissions_granted_by_fkey FOREIGN KEY (granted_by) REFERENCES people(email),
    CONSTRAINT user_permissions_revoked_by_fkey FOREIGN KEY (revoked_by) REFERENCES people(email)
);

-- ============================================================================
-- CREATE INDEXES
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_user_permission ON user_permissions(user_email, permission_type);
CREATE INDEX IF NOT EXISTS idx_permission_active ON user_permissions(user_email, permission_type, revoked_at) 
    WHERE revoked_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_permission_expires ON user_permissions(expires_at) 
    WHERE expires_at IS NOT NULL AND revoked_at IS NULL;

-- ============================================================================
-- ENABLE RLS
-- ============================================================================

ALTER TABLE IF EXISTS user_permissions ENABLE ROW LEVEL SECURITY;

-- Users can view their own permissions
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'user_permissions') THEN
        IF NOT EXISTS (
            SELECT 1 FROM pg_policies
            WHERE schemaname = 'public'
            AND tablename = 'user_permissions'
            AND policyname = 'Users can view their own permissions'
        ) THEN
            CREATE POLICY "Users can view their own permissions"
                ON user_permissions FOR SELECT
                USING (
                    (SELECT auth.email()) = user_email OR
                    (SELECT auth.email()) = 'ahelmy@eternityschoolegypt.com' OR
                    (SELECT auth.role()) = 'service_role'
                );
        END IF;
    END IF;
END $$;

-- Only super admin and service role can grant/revoke
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'user_permissions') THEN
        DROP POLICY IF EXISTS "Only super admin can manage permissions" ON user_permissions;

        IF NOT EXISTS (
            SELECT 1 FROM pg_policies
            WHERE schemaname = 'public'
            AND tablename = 'user_permissions'
            AND policyname = 'Super admin can insert permissions'
        ) THEN
            CREATE POLICY "Super admin can insert permissions"
                ON user_permissions FOR INSERT
                WITH CHECK (
                    (SELECT auth.email()) = 'ahelmy@eternityschoolegypt.com' OR
                    (SELECT auth.role()) = 'service_role'
                );
        END IF;

        IF NOT EXISTS (
            SELECT 1 FROM pg_policies
            WHERE schemaname = 'public'
            AND tablename = 'user_permissions'
            AND policyname = 'Super admin can update permissions'
        ) THEN
            CREATE POLICY "Super admin can update permissions"
                ON user_permissions FOR UPDATE
                USING (
                    (SELECT auth.email()) = 'ahelmy@eternityschoolegypt.com' OR
                    (SELECT auth.role()) = 'service_role'
                )
                WITH CHECK (
                    (SELECT auth.email()) = 'ahelmy@eternityschoolegypt.com' OR
                    (SELECT auth.role()) = 'service_role'
                );
        END IF;

        IF NOT EXISTS (
            SELECT 1 FROM pg_policies
            WHERE schemaname = 'public'
            AND tablename = 'user_permissions'
            AND policyname = 'Super admin can delete permissions'
        ) THEN
            CREATE POLICY "Super admin can delete permissions"
                ON user_permissions FOR DELETE
                USING (
                    (SELECT auth.email()) = 'ahelmy@eternityschoolegypt.com' OR
                    (SELECT auth.role()) = 'service_role'
                );
        END IF;
    END IF;
END $$;

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE user_permissions IS 'Time-based user permissions managed by super admin';
COMMENT ON COLUMN user_permissions.expires_at IS 'NULL means unlimited permission';
COMMENT ON COLUMN user_permissions.revoked_at IS 'NULL means permission is active';
