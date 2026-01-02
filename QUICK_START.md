# Quick Start Guide - Vercel + Supabase Deployment

## ✅ What's Already Done

1. ✅ **Dependencies Installed** - All Python packages from `requirements.txt`
2. ✅ **Vercel Configuration** - `vercel.json` created
3. ✅ **Migration Scripts** - Ready to run
4. ✅ **Startup Scripts** - Application can start locally

---

## 🚀 Step-by-Step Deployment

### Step 1: Install CLI Tools (if not already installed)

```bash
# Install Supabase CLI
npm install -g supabase

# Install Vercel CLI
npm install -g vercel
```

### Step 2: Set Up Environment Variables

Create/update `.env` file with your credentials:

```bash
# Get these from Supabase Dashboard → Project Settings → Database
DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@db.ywcfqlyhesnikclesgpr.supabase.co:5432/postgres

# Email (already configured)
SMTP_SERVER=smtp.resend.com
SMTP_PORT=465
SMTP_USER=resend
SMTP_PASSWORD=[YOUR-SMTP_PASSWORD]
FROM_EMAIL=noreply@eternityschoolegypt.com
EMAIL_ENABLED=true

# Supabase (get from Dashboard → API Settings)
SUPABASE_URL=https://ywcfqlyhesnikclesgpr.supabase.co
SUPABASE_ANON_KEY=[YOUR-ANON-KEY]
SUPABASE_SERVICE_ROLE_KEY=[YOUR-SERVICE-ROLE-KEY]

# Application
ENVIRONMENT=production
ENABLE_DOCS=false
```

### Step 3: Run Database Migrations

```bash
# Login to Supabase
supabase login

# Link to your project
supabase link --project-ref ywcfqlyhesnikclesgpr

# Run migrations
./run_migrations.sh
```

**OR** manually in Supabase Dashboard:
1. Go to https://supabase.com/dashboard/project/ywcfqlyhesnikclesgpr
2. SQL Editor → New Query
3. Run each file from `supabase/migrations/` in order (00000 to 00018)

### Step 4: Test Locally

```bash
# Start the application
./start_app.sh
```

Then test:
- Health: http://localhost:8000/api/v2/health
- API Docs: http://localhost:8000/docs

### Step 5: Deploy to Vercel

**Option A: Via Vercel Dashboard (Recommended)**
1. Go to https://vercel.com/new
2. Import your Git repository
3. Vercel will auto-detect configuration
4. Add environment variables in Settings → Environment Variables
5. Deploy!

**Option B: Via Vercel CLI**
```bash
# Login
vercel login

# Deploy
vercel --prod
```

---

## 📋 Environment Variables for Vercel

Add these in Vercel Dashboard → Project → Settings → Environment Variables:

```
DATABASE_URL=postgresql://postgres:[PASSWORD]@db.ywcfqlyhesnikclesgpr.supabase.co:5432/postgres
SMTP_SERVER=smtp.resend.com
SMTP_PORT=465
SMTP_USER=resend
SMTP_PASSWORD=[YOUR-SMTP_PASSWORD]
FROM_EMAIL=noreply@eternityschoolegypt.com
EMAIL_ENABLED=true
SUPABASE_URL=https://ywcfqlyhesnikclesgpr.supabase.co
SUPABASE_ANON_KEY=[YOUR-KEY]
SUPABASE_SERVICE_ROLE_KEY=[YOUR-KEY]
ENVIRONMENT=production
ENABLE_DOCS=false
```

---

## ✅ Verification

After deployment, verify:
- [ ] Health endpoint: `https://your-project.vercel.app/api/v2/health`
- [ ] API docs: `https://your-project.vercel.app/docs`
- [ ] Database connected (check logs)
- [ ] Scheduler running (check logs)

---

## 🆘 Troubleshooting

### Database Connection
- Verify `DATABASE_URL` format
- Check Supabase connection pooling
- Ensure database password is correct

### Build Failures
- Check Python version (3.11+)
- Verify all dependencies in `requirements.txt`
- Check Vercel build logs

### Migration Issues
- Ensure Supabase CLI is installed
- Verify project is linked
- Check migration file order

---

**Ready to deploy!** 🚀
