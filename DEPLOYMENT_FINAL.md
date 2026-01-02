# 🚀 Final Deployment Steps - Complete

## ✅ Completed

1. **Sentry SDK Configured** ✅
   - DSN: `https://6a9a496b1708940e265abb51c5ce4879@o4510482211930112.ingest.de.sentry.io/4510633780183120`
   - `send_default_pii=True` enabled
   - `traces_sample_rate=1.0` for development

2. **Database Migrations** ✅
   - Migration conflicts repaired
   - Ready to apply migrations 00005-00018

3. **Git Repository** ✅
   - Changes committed
   - Ready to push

---

## 🎯 Final Steps

### Step 1: Apply Database Migrations

**Option A: Via Supabase Dashboard (Recommended)**
1. Go to https://supabase.com/dashboard/project/ywcfqlyhesnikclesgpr
2. Navigate to **SQL Editor**
3. Create new query
4. Run each migration file in order:
   - `20240101000005_fix_security_issues.sql`
   - `20240101000006_fix_function_search_path.sql`
   - `20240101000007_optimize_rls_performance.sql`
   - `20240101000008_fix_multiple_permissive_policies.sql`
   - `20240101000009_fix_security_definer_views_and_rls.sql`
   - `20240101000010_explicitly_set_security_invoker_on_views.sql`
   - `20240101000011_fix_function_search_path_security.sql`
   - `20240101000012_add_new_features.sql` (Announcements, Notifications)
   - `20240101000013_fix_eom_categories_and_add_features.sql`
   - `20240101000014_survey_identity_system.sql`
   - `20240101000015_conditional_anonymity_engine.sql`
   - `20240101000016_add_missing_models.sql`
   - `20240101000017_add_survey_functions.sql`
   - `20240101000018_rbac_user_permissions.sql`

**Option B: Via Supabase CLI**
```bash
supabase db push
```

### Step 2: Push to Git

```bash
git push origin main
```

### Step 3: Deploy to Vercel

**Via Dashboard:**
1. Go to https://vercel.com/new
2. Click "Import Git Repository"
3. Select your repository
4. Vercel will auto-detect configuration
5. **Before deploying**, add environment variables (see Step 4)
6. Click "Deploy"

**Via CLI:**
```bash
vercel login
vercel --prod
```

### Step 4: Set Environment Variables in Vercel

**Vercel Dashboard → Your Project → Settings → Environment Variables**

Add all variables from `VERCEL_ENV_VARIABLES.md`:

**Required:**
- `DATABASE_URL` - Already configured
- `SMTP_SERVER`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD` - Resend SMTP
- `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY` - Get from Supabase Dashboard
- `SENTRY_DSN` - Already configured
- `ENVIRONMENT=production`
- `EMAIL_ENABLED=true`
- `ALLOWED_ORIGINS` - Your Vercel deployment URL

**To get Supabase keys:**
1. Go to https://supabase.com/dashboard/project/ywcfqlyhesnikclesgpr
2. Settings → API
3. Copy `anon` and `service_role` keys

---

## ✅ Verification

After deployment:

1. **Health Check:**
   ```
   https://your-project.vercel.app/api/v2/health
   ```

2. **API Docs:**
   ```
   https://your-project.vercel.app/docs
   ```

3. **Test Announcements:**
   ```bash
   curl https://your-project.vercel.app/api/v2/announcements
   ```

4. **Check Logs:**
   - Vercel Dashboard → Logs
   - Verify scheduler started
   - Check Sentry for errors

---

## 📋 Quick Reference

**Files Created:**
- `vercel.json` - Vercel config
- `api/index.py` - Serverless entry
- `VERCEL_ENV_VARIABLES.md` - Environment variables list

**Scripts:**
- `./start_app.sh` - Start locally
- `./run_migrations.sh` - Run migrations
- `./fix_migrations.sh` - Fix conflicts

---

**Status: ✅ READY TO DEPLOY**

Follow the steps above to complete deployment!
