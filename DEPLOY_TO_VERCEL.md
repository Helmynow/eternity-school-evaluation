# Deploy to Vercel - Step by Step Guide

## ✅ Pre-Deployment Checklist

### 1. Commit Your Changes
```bash
git add .
git commit -m "Fix: Security improvements and bug fixes

- Remove hardcoded Sentry DSN (security)
- Make send_default_pii configurable (defaults to False)
- Fix misspelled icon filename (warning_alert.png)
- Fix infinite loop in EvaluatorManagement useEffect
- Update vercel.json for correct deployment"
```

### 2. Push to GitHub
```bash
git push origin main
# or
git push origin master
```

## 🚀 Deploy to Vercel

### Option A: Deploy via Vercel CLI (Recommended)

1. **Install Vercel CLI** (if not already installed):
```bash
npm i -g vercel
```

2. **Login to Vercel**:
```bash
vercel login
```

3. **Link to your project** (if not already linked):
```bash
vercel link
```

4. **Deploy to Production**:
```bash
vercel --prod
```

### Option B: Deploy via Vercel Dashboard

1. Go to https://vercel.com/dashboard
2. Click **"Add New Project"** (or select existing project)
3. **Import your Git repository** (GitHub/GitLab/Bitbucket)
4. Configure:
   - **Framework Preset**: Other
   - **Root Directory**: `./` (root)
   - **Build Command**: (leave empty, handled by vercel.json)
   - **Output Directory**: (leave empty, handled by vercel.json)

5. Click **"Deploy"**

## ⚙️ Set Environment Variables

**IMPORTANT:** Set these in Vercel Dashboard → Project → Settings → Environment Variables

### Required Variables

```env
# Database (Supabase)
DATABASE_URL=postgresql://postgres:oRyY5M5S5op6ARqi@db.ywcfqlyhesnikclesgpr.supabase.co:5432/postgres

# Email (Resend SMTP)
SMTP_SERVER=smtp.resend.com
SMTP_PORT=465
SMTP_USER=resend
SMTP_PASSWORD=re_6dFf5Vue_73jUTecAhnqZaonoGEPaGax2
FROM_EMAIL=noreply@eternityschoolegypt.com
EMAIL_ENABLED=true

# Supabase (Get from Dashboard → API Settings)
SUPABASE_URL=https://ywcfqlyhesnikclesgpr.supabase.co
SUPABASE_ANON_KEY=[GET-FROM-SUPABASE-DASHBOARD]
SUPABASE_SERVICE_ROLE_KEY=[GET-FROM-SUPABASE-DASHBOARD]

# Sentry (Optional - for error tracking)
SENTRY_DSN=[YOUR-SENTRY-DSN]
SENTRY_SEND_DEFAULT_PII=false
SENTRY_TRACES_SAMPLE_RATE=0.1
SENTRY_PROFILES_SAMPLE_RATE=0.0

# Application
ENVIRONMENT=production
ENABLE_DOCS=false
ALLOWED_ORIGINS=https://your-project.vercel.app
APP_VERSION=2.0.0
```

### How to Get Supabase Keys

1. Go to https://supabase.com/dashboard/project/ywcfqlyhesnikclesgpr
2. Navigate to **Settings → API**
3. Copy:
   - **anon** key → `SUPABASE_ANON_KEY`
   - **service_role** key → `SUPABASE_SERVICE_ROLE_KEY`

### Important Notes

- ✅ Replace `[GET-FROM-SUPABASE-DASHBOARD]` with actual keys
- ✅ Replace `https://your-project.vercel.app` with your actual Vercel URL
- ✅ Set `ALLOWED_ORIGINS` to your production frontend URL
- ✅ All variables should be set for **Production** environment
- ✅ `SENTRY_DSN` is now optional (no hardcoded default for security)

## 📋 Post-Deployment Steps

### 1. Verify Deployment
- Check Vercel deployment logs for errors
- Visit your deployed URL
- Test API endpoints: `https://your-project.vercel.app/api/v2/health`

### 2. Test Critical Features
- ✅ User authentication
- ✅ Database connections
- ✅ Email sending (if configured)
- ✅ API endpoints
- ✅ Frontend routing

### 3. Monitor
- Check Vercel function logs
- Monitor Sentry (if configured)
- Check Supabase logs

## 🔧 Troubleshooting

### Build Fails
- Check Python version (should be 3.11)
- Verify all dependencies in `requirements.txt`
- Check build logs in Vercel dashboard

### API Not Working
- Verify `DATABASE_URL` is set correctly
- Check CORS settings (`ALLOWED_ORIGINS`)
- Verify Supabase connection

### Frontend Not Loading
- Check `frontend/dist` directory exists
- Verify build command in `package.json`
- Check Vercel build logs

## ✅ Deployment Complete!

Once deployed, your app will be available at:
- **Frontend**: `https://your-project.vercel.app`
- **API**: `https://your-project.vercel.app/api/v2/...`

---

**Need Help?** Check `VERCEL_DEPLOYMENT.md` for more details.
