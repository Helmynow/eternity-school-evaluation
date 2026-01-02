-- RLS policy consolidation + auth initplan improvements
-- Generated automatically to merge duplicate permissive policies and wrap auth.* calls
DROP POLICY IF EXISTS "feedback_insert_own" ON "public"."feedback";
DROP POLICY IF EXISTS "feedback_service_role_insert" ON "public"."feedback";
CREATE POLICY "feedback_public_insert" ON "public"."feedback" AS PERMISSIVE FOR INSERT TO "public"
    WITH CHECK (((( SELECT auth.email() AS email) = (submitted_by)::text)) OR ((( SELECT auth.role() AS role) = 'service_role'::text)));
DROP POLICY IF EXISTS "feedback_select" ON "public"."feedback";
DROP POLICY IF EXISTS "feedback_select_own" ON "public"."feedback";
DROP POLICY IF EXISTS "feedback_service_role_select" ON "public"."feedback";
CREATE POLICY "feedback_public_select" ON "public"."feedback" AS PERMISSIVE FOR SELECT TO "public"
    USING (((((submitted_by)::text = auth.email()) OR (auth.role() = 'authenticated'::text))) OR (((( SELECT auth.email() AS email) = (submitted_by)::text) OR (( SELECT auth.role() AS role) = 'service_role'::text))) OR ((( SELECT auth.role() AS role) = 'service_role'::text)));
DROP POLICY IF EXISTS "hybrid_identity_sessions_delete" ON "public"."hybrid_identity_sessions";
DROP POLICY IF EXISTS "hybrid_identity_sessions_service_role_delete" ON "public"."hybrid_identity_sessions";
CREATE POLICY "hybrid_identity_sessions_public_delete" ON "public"."hybrid_identity_sessions" AS PERMISSIVE FOR DELETE TO "public"
    USING (((( SELECT auth.email() AS email) = (user_email)::text)) OR ((( SELECT auth.role() AS role) = 'service_role'::text)));
DROP POLICY IF EXISTS "hybrid_identity_sessions_insert" ON "public"."hybrid_identity_sessions";
DROP POLICY IF EXISTS "hybrid_identity_sessions_service_role_insert" ON "public"."hybrid_identity_sessions";
CREATE POLICY "hybrid_identity_sessions_public_insert" ON "public"."hybrid_identity_sessions" AS PERMISSIVE FOR INSERT TO "public"
    WITH CHECK (((( SELECT auth.email() AS email) = (user_email)::text)) OR ((( SELECT auth.role() AS role) = 'service_role'::text)));
DROP POLICY IF EXISTS "hybrid_identity_sessions_select" ON "public"."hybrid_identity_sessions";
DROP POLICY IF EXISTS "hybrid_identity_sessions_service_role_select" ON "public"."hybrid_identity_sessions";
CREATE POLICY "hybrid_identity_sessions_public_select" ON "public"."hybrid_identity_sessions" AS PERMISSIVE FOR SELECT TO "public"
    USING (((( SELECT auth.email() AS email) = (user_email)::text)) OR ((( SELECT auth.role() AS role) = 'service_role'::text)));
DROP POLICY IF EXISTS "hybrid_identity_sessions_service_role_update" ON "public"."hybrid_identity_sessions";
DROP POLICY IF EXISTS "hybrid_identity_sessions_update" ON "public"."hybrid_identity_sessions";
CREATE POLICY "hybrid_identity_sessions_public_update" ON "public"."hybrid_identity_sessions" AS PERMISSIVE FOR UPDATE TO "public"
    USING (((( SELECT auth.role() AS role) = 'service_role'::text)) OR ((( SELECT auth.email() AS email) = (user_email)::text)))
    WITH CHECK (true);
DROP POLICY IF EXISTS "notifications_select" ON "public"."notifications";
DROP POLICY IF EXISTS "notifications_select_own" ON "public"."notifications";
DROP POLICY IF EXISTS "notifications_service_role_select" ON "public"."notifications";
CREATE POLICY "notifications_public_select" ON "public"."notifications" AS PERMISSIVE FOR SELECT TO "public"
    USING (((((recipient_email)::text = auth.email()) OR (auth.role() = 'authenticated'::text))) OR ((( SELECT auth.email() AS email) = (recipient_email)::text)) OR ((( SELECT auth.role() AS role) = 'service_role'::text)));
DROP POLICY IF EXISTS "notifications_service_role_update" ON "public"."notifications";
DROP POLICY IF EXISTS "notifications_update_own" ON "public"."notifications";
CREATE POLICY "notifications_public_update" ON "public"."notifications" AS PERMISSIVE FOR UPDATE TO "public"
    USING (((( SELECT auth.role() AS role) = 'service_role'::text)) OR ((( SELECT auth.email() AS email) = (recipient_email)::text)))
    WITH CHECK (true);
DROP POLICY IF EXISTS "objections_insert_own" ON "public"."objections";
DROP POLICY IF EXISTS "objections_service_role_insert" ON "public"."objections";
CREATE POLICY "objections_public_insert" ON "public"."objections" AS PERMISSIVE FOR INSERT TO "public"
    WITH CHECK (((( SELECT auth.email() AS email) = (submitted_by)::text)) OR ((( SELECT auth.role() AS role) = 'service_role'::text)));
DROP POLICY IF EXISTS "objections_select" ON "public"."objections";
DROP POLICY IF EXISTS "objections_select_own" ON "public"."objections";
CREATE POLICY "objections_public_select" ON "public"."objections" AS PERMISSIVE FOR SELECT TO "public"
    USING ((true) OR (((( SELECT auth.email() AS email) = (submitted_by)::text) OR (( SELECT auth.role() AS role) = 'service_role'::text))));
DROP POLICY IF EXISTS "survey_conditional_reveals_delete" ON "public"."survey_conditional_reveals";
DROP POLICY IF EXISTS "survey_conditional_reveals_service_role_delete" ON "public"."survey_conditional_reveals";
CREATE POLICY "survey_conditional_reveals_public_delete" ON "public"."survey_conditional_reveals" AS PERMISSIVE FOR DELETE TO "public"
    USING (((( SELECT auth.email() AS email) = (user_email)::text)) OR ((( SELECT auth.role() AS role) = 'service_role'::text)));
DROP POLICY IF EXISTS "survey_conditional_reveals_insert" ON "public"."survey_conditional_reveals";
DROP POLICY IF EXISTS "survey_conditional_reveals_service_role_insert" ON "public"."survey_conditional_reveals";
CREATE POLICY "survey_conditional_reveals_public_insert" ON "public"."survey_conditional_reveals" AS PERMISSIVE FOR INSERT TO "public"
    WITH CHECK (((( SELECT auth.email() AS email) = (user_email)::text)) OR ((( SELECT auth.role() AS role) = 'service_role'::text)));
DROP POLICY IF EXISTS "survey_conditional_reveals_select" ON "public"."survey_conditional_reveals";
DROP POLICY IF EXISTS "survey_conditional_reveals_service_role_select" ON "public"."survey_conditional_reveals";
CREATE POLICY "survey_conditional_reveals_public_select" ON "public"."survey_conditional_reveals" AS PERMISSIVE FOR SELECT TO "public"
    USING (((( SELECT auth.email() AS email) = (user_email)::text)) OR ((( SELECT auth.role() AS role) = 'service_role'::text)));
DROP POLICY IF EXISTS "survey_conditional_reveals_service_role_update" ON "public"."survey_conditional_reveals";
DROP POLICY IF EXISTS "survey_conditional_reveals_update" ON "public"."survey_conditional_reveals";
CREATE POLICY "survey_conditional_reveals_public_update" ON "public"."survey_conditional_reveals" AS PERMISSIVE FOR UPDATE TO "public"
    USING (((( SELECT auth.role() AS role) = 'service_role'::text)) OR ((( SELECT auth.email() AS email) = (user_email)::text)))
    WITH CHECK (true);
DROP POLICY IF EXISTS "survey_identity_preferences_delete" ON "public"."survey_identity_preferences";
DROP POLICY IF EXISTS "survey_identity_preferences_service_role_delete" ON "public"."survey_identity_preferences";
CREATE POLICY "survey_identity_preferences_public_delete" ON "public"."survey_identity_preferences" AS PERMISSIVE FOR DELETE TO "public"
    USING (((( SELECT auth.email() AS email) = (user_email)::text)) OR ((( SELECT auth.role() AS role) = 'service_role'::text)));
DROP POLICY IF EXISTS "survey_identity_preferences_insert" ON "public"."survey_identity_preferences";
DROP POLICY IF EXISTS "survey_identity_preferences_service_role_insert" ON "public"."survey_identity_preferences";
CREATE POLICY "survey_identity_preferences_public_insert" ON "public"."survey_identity_preferences" AS PERMISSIVE FOR INSERT TO "public"
    WITH CHECK (((( SELECT auth.email() AS email) = (user_email)::text)) OR ((( SELECT auth.role() AS role) = 'service_role'::text)));
DROP POLICY IF EXISTS "survey_identity_preferences_select" ON "public"."survey_identity_preferences";
DROP POLICY IF EXISTS "survey_identity_preferences_service_role_select" ON "public"."survey_identity_preferences";
CREATE POLICY "survey_identity_preferences_public_select" ON "public"."survey_identity_preferences" AS PERMISSIVE FOR SELECT TO "public"
    USING (((( SELECT auth.email() AS email) = (user_email)::text)) OR ((( SELECT auth.role() AS role) = 'service_role'::text)));
DROP POLICY IF EXISTS "survey_identity_preferences_service_role_update" ON "public"."survey_identity_preferences";
DROP POLICY IF EXISTS "survey_identity_preferences_update" ON "public"."survey_identity_preferences";
CREATE POLICY "survey_identity_preferences_public_update" ON "public"."survey_identity_preferences" AS PERMISSIVE FOR UPDATE TO "public"
    USING (((( SELECT auth.role() AS role) = 'service_role'::text)) OR ((( SELECT auth.email() AS email) = (user_email)::text)))
    WITH CHECK (true);
DROP POLICY IF EXISTS "survey_identity_reveals_insert" ON "public"."survey_identity_reveals";
DROP POLICY IF EXISTS "survey_identity_reveals_service_role_insert" ON "public"."survey_identity_reveals";
CREATE POLICY "survey_identity_reveals_public_insert" ON "public"."survey_identity_reveals" AS PERMISSIVE FOR INSERT TO "public"
    WITH CHECK (((( SELECT auth.email() AS email) = (user_email)::text)) OR ((( SELECT auth.role() AS role) = 'service_role'::text)));
DROP POLICY IF EXISTS "survey_identity_reveals_select" ON "public"."survey_identity_reveals";
DROP POLICY IF EXISTS "survey_identity_reveals_service_role_select" ON "public"."survey_identity_reveals";
CREATE POLICY "survey_identity_reveals_public_select" ON "public"."survey_identity_reveals" AS PERMISSIVE FOR SELECT TO "public"
    USING (((( SELECT auth.email() AS email) = (user_email)::text)) OR ((( SELECT auth.role() AS role) = 'service_role'::text)));
DROP POLICY IF EXISTS "survey_responses_insert_own" ON "public"."survey_responses";
DROP POLICY IF EXISTS "survey_responses_service_role_insert" ON "public"."survey_responses";
CREATE POLICY "survey_responses_public_insert" ON "public"."survey_responses" AS PERMISSIVE FOR INSERT TO "public"
    WITH CHECK ((((( SELECT auth.email() AS email) = (respondent_email)::text) OR (respondent_email IS NULL))) OR ((( SELECT auth.role() AS role) = 'service_role'::text)));
DROP POLICY IF EXISTS "survey_responses_select_own" ON "public"."survey_responses";
DROP POLICY IF EXISTS "survey_responses_service_role_select" ON "public"."survey_responses";
CREATE POLICY "survey_responses_public_select" ON "public"."survey_responses" AS PERMISSIVE FOR SELECT TO "public"
    USING ((((( SELECT auth.email() AS email) = (respondent_email)::text) OR (( SELECT auth.role() AS role) = 'service_role'::text) OR (respondent_email IS NULL))) OR ((( SELECT auth.role() AS role) = 'service_role'::text)));
DROP POLICY IF EXISTS "surveys_select" ON "public"."surveys";
DROP POLICY IF EXISTS "surveys_select_active" ON "public"."surveys";
CREATE POLICY "surveys_public_select" ON "public"."surveys" AS PERMISSIVE FOR SELECT TO "public"
    USING (((((status)::text <> 'draft'::text) OR (auth.role() = 'authenticated'::text))) OR ((((status)::text = 'active'::text) OR (( SELECT auth.role() AS role) = 'service_role'::text))));
