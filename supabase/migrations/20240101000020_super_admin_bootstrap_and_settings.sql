-- Migration: CEO bootstrap super admin + system settings
-- - Removes hardcoded super admin email from RLS policies (user_permissions)
-- - Adds a singleton system_settings table used by the CEO Settings UI

-- ============================================================================
-- SUPER ADMIN BOOTSTRAP HELPERS
-- ============================================================================

-- Determine the first active CEO email (bootstrap super admin).
-- Convention: role_title contains 'ceo' or 'chief executive' (case-insensitive).
CREATE OR REPLACE FUNCTION ese_first_ceo_email()
RETURNS text
LANGUAGE sql
STABLE
AS $$
  SELECT p.email
  FROM people p
  WHERE p.active IS TRUE
    AND (
      lower(coalesce(p.role_title, '')) LIKE '%ceo%'
      OR lower(coalesce(p.role_title, '')) LIKE '%chief executive%'
    )
  ORDER BY p.created_at ASC NULLS LAST, p.email ASC
  LIMIT 1
$$;

-- True when the current authenticated user matches the bootstrap CEO email.
CREATE OR REPLACE FUNCTION ese_is_super_admin()
RETURNS boolean
LANGUAGE sql
STABLE
AS $$
  SELECT (SELECT auth.email()) IS NOT NULL
     AND (SELECT auth.email()) = ese_first_ceo_email()
$$;

-- ============================================================================
-- UPDATE USER_PERMISSIONS RLS POLICIES (REMOVE HARDCODED EMAIL)
-- ============================================================================

ALTER TABLE IF EXISTS user_permissions ENABLE ROW LEVEL SECURITY;

-- Drop legacy policies created in 20240101000018 (safe if they don't exist).
DROP POLICY IF EXISTS "Users can view their own permissions" ON user_permissions;
DROP POLICY IF EXISTS "Super admin can insert permissions" ON user_permissions;
DROP POLICY IF EXISTS "Super admin can update permissions" ON user_permissions;
DROP POLICY IF EXISTS "Super admin can delete permissions" ON user_permissions;

-- Users can view their own permissions; bootstrap CEO (super admin) and service_role can view all.
CREATE POLICY "Users can view their own permissions"
  ON user_permissions FOR SELECT
  USING (
    (SELECT auth.email()) = user_email
    OR ese_is_super_admin()
    OR (SELECT auth.role()) = 'service_role'
  );

-- Only bootstrap CEO (super admin) and service_role can manage permissions.
CREATE POLICY "Super admin can insert permissions"
  ON user_permissions FOR INSERT
  WITH CHECK (
    ese_is_super_admin()
    OR (SELECT auth.role()) = 'service_role'
  );

CREATE POLICY "Super admin can update permissions"
  ON user_permissions FOR UPDATE
  USING (
    ese_is_super_admin()
    OR (SELECT auth.role()) = 'service_role'
  )
  WITH CHECK (
    ese_is_super_admin()
    OR (SELECT auth.role()) = 'service_role'
  );

CREATE POLICY "Super admin can delete permissions"
  ON user_permissions FOR DELETE
  USING (
    ese_is_super_admin()
    OR (SELECT auth.role()) = 'service_role'
  );

-- ============================================================================
-- SYSTEM SETTINGS (SINGLETON ROW)
-- ============================================================================

-- Single-row settings table (id is always 1).
CREATE TABLE IF NOT EXISTS system_settings (
  id INTEGER PRIMARY KEY DEFAULT 1,
  email_notifications BOOLEAN DEFAULT TRUE,
  auto_activate_cycles BOOLEAN DEFAULT FALSE,
  require_approval BOOLEAN DEFAULT TRUE,
  default_rotation_period rotation_period_type DEFAULT 'term',
  max_nominations_per_person INTEGER DEFAULT 1,
  evaluation_deadline_days INTEGER DEFAULT 30,
  updated_by VARCHAR(255) REFERENCES people(email),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT system_settings_singleton CHECK (id = 1)
);

-- Ensure the singleton row exists.
INSERT INTO system_settings (id)
SELECT 1
WHERE NOT EXISTS (SELECT 1 FROM system_settings WHERE id = 1);

-- Updated_at trigger (reuse shared helper from initial schema migration).
DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM pg_proc WHERE proname = 'update_updated_at_column'
  ) THEN
    IF NOT EXISTS (
      SELECT 1 FROM pg_trigger WHERE tgname = 'update_system_settings_updated_at'
    ) THEN
      CREATE TRIGGER update_system_settings_updated_at
        BEFORE UPDATE ON system_settings
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    END IF;
  END IF;
END $$;

-- RLS for system settings (CEO-only).
ALTER TABLE IF EXISTS system_settings ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Super admin can read system settings" ON system_settings;
DROP POLICY IF EXISTS "Super admin can manage system settings" ON system_settings;

CREATE POLICY "Super admin can read system settings"
  ON system_settings FOR SELECT
  USING (
    ese_is_super_admin()
    OR (SELECT auth.role()) = 'service_role'
  );

CREATE POLICY "Super admin can manage system settings"
  ON system_settings FOR ALL
  USING (
    ese_is_super_admin()
    OR (SELECT auth.role()) = 'service_role'
  )
  WITH CHECK (
    ese_is_super_admin()
    OR (SELECT auth.role()) = 'service_role'
  );

