# Vercel Deployment Guide

## Prerequisites

1. **Vercel Account**: Sign up at https://vercel.com
2. **Supabase Project**: Already configured (Project ID: `ywcfqlyhesnikclesgpr`)
3. **Git Repository**: Your code should be in a Git repository (GitHub, GitLab, or Bitbucket)

## Step 1: Connect to Git

1. Push your code to GitHub/GitLab/Bitbucket
2. Go to https://vercel.com/new
3. Import your Git repository
4. Vercel will auto-detect the project

## Step 2: Configure Vercel Project

### Environment Variables

Add these in Vercel Dashboard → Project Settings → Environment Variables:

```env
# Database
DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@db.ywcfqlyhesnikclesgpr.supabase.co:5432/postgres

# Email (Resend SMTP)
SMTP_SERVER=smtp.resend.com
SMTP_PORT=465
SMTP_USER=resend
SMTP_PASSWORD=re_6dFf5Vue_73jUTecAhnqZaonoGEPaGax2
FROM_EMAIL=noreply@eternityschoolegypt.com
EMAIL_ENABLED=true

# Supabase
SUPABASE_URL=https://ywcfqlyhesnikclesgpr.supabase.co
SUPABASE_ANON_KEY=[YOUR-SUPABASE-ANON-KEY]
SUPABASE_SERVICE_ROLE_KEY=[YOUR-SUPABASE-SERVICE-ROLE-KEY]

# Application
ENVIRONMENT=production
ENABLE_DOCS=false

# Optional
SENTRY_DSN=[YOUR-SENTRY-DSN]
REQUIRE_API_KEY=false
ALLOWED_ORIGINS=https://your-domain.vercel.app
```

### Build Settings

- **Framework Preset**: Other
- **Build Command**: `pip install -r backend/requirements.txt`
- **Output Directory**: `backend`
- **Install Command**: `pip install -r backend/requirements.txt`

## Step 3: Run Database Migrations

### Option A: Using Supabase CLI (Recommended)

```bash
# Install Supabase CLI
npm install -g supabase

# Login
supabase login

# Link to your project
supabase link --project-ref ywcfqlyhesnikclesgpr

# Push migrations
cd supabase
supabase db push
```

### Option B: Using Supabase Dashboard

1. Go to https://supabase.com/dashboard/project/ywcfqlyhesnikclesgpr
2. Navigate to SQL Editor
3. Run each migration file from `supabase/migrations/` in order

## Step 4: Deploy

1. Push to your Git repository
2. Vercel will automatically deploy
3. Check deployment logs for any issues

## Step 5: Verify Deployment

1. Check health endpoint: `https://your-project.vercel.app/api/v2/health`
2. Test API: `https://your-project.vercel.app/api/v2/cycles/current`
3. Check logs in Vercel Dashboard

## Troubleshooting

### Database Connection Issues
- Verify DATABASE_URL is correct
- Check Supabase connection pooling settings
- Ensure IP is whitelisted in Supabase

### Build Failures
- Check Python version (should be 3.11+)
- Verify all dependencies in requirements.txt
- Check build logs in Vercel Dashboard

### Runtime Errors
- Check function logs in Vercel Dashboard
- Verify environment variables are set
- Check Supabase connection

## Next Steps

1. Set up custom domain (optional)
2. Configure monitoring (Sentry)
3. Set up CI/CD for automatic deployments
4. Configure backups for Supabase
