-- Fix auth initplan warnings and consolidate SELECT policies (email_notifications, system_settings)
ALTER POLICY "announcements_select" ON public.announcements USING (((is_active = true) OR ((select auth.role()) = 'authenticated'::text)));
DROP POLICY IF EXISTS "Email notifications are viewable by super admin" ON public.email_notifications;
DROP POLICY IF EXISTS "Email notifications are manageable by service role" ON public.email_notifications;
CREATE POLICY email_notifications_select ON public.email_notifications FOR SELECT USING ((ese_is_super_admin() OR (select auth.role()) = 'service_role'));
CREATE POLICY email_notifications_insert ON public.email_notifications FOR INSERT WITH CHECK ((ese_is_super_admin() OR (select auth.role()) = 'service_role'));
CREATE POLICY email_notifications_update ON public.email_notifications FOR UPDATE USING ((ese_is_super_admin() OR (select auth.role()) = 'service_role')) WITH CHECK ((ese_is_super_admin() OR (select auth.role()) = 'service_role'));
CREATE POLICY email_notifications_delete ON public.email_notifications FOR DELETE USING ((ese_is_super_admin() OR (select auth.role()) = 'service_role'));
DROP POLICY IF EXISTS "Super admin can read system settings" ON public.system_settings;
DROP POLICY IF EXISTS "Super admin can manage system settings" ON public.system_settings;
CREATE POLICY system_settings_select ON public.system_settings FOR SELECT USING ((ese_is_super_admin() OR (select auth.role()) = 'service_role'));
CREATE POLICY system_settings_insert ON public.system_settings FOR INSERT WITH CHECK ((ese_is_super_admin() OR (select auth.role()) = 'service_role'));
CREATE POLICY system_settings_update ON public.system_settings FOR UPDATE USING ((ese_is_super_admin() OR (select auth.role()) = 'service_role')) WITH CHECK ((ese_is_super_admin() OR (select auth.role()) = 'service_role'));
CREATE POLICY system_settings_delete ON public.system_settings FOR DELETE USING ((ese_is_super_admin() OR (select auth.role()) = 'service_role'));
