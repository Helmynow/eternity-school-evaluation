# Vercel Environment Variables

Copy and paste these into **Vercel Dashboard → Project → Settings → Environment Variables**

## Required Variables

```env
# Database (Supabase)
DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@db.ywcfqlyhesnikclesgpr.supabase.co:5432/postgres

# Email (Resend SMTP)
SMTP_SERVER=smtp.resend.com
SMTP_PORT=465
SMTP_USER=resend
SMTP_PASSWORD=[YOUR-SMTP_PASSWORD]
FROM_EMAIL=noreply@eternityschoolegypt.com
EMAIL_ENABLED=false

# Supabase (Get from Dashboard → API Settings)
SUPABASE_URL=https://ywcfqlyhesnikclesgpr.supabase.co
SUPABASE_ANON_KEY=[GET-FROM-SUPABASE-DASHBOARD]
SUPABASE_SERVICE_ROLE_KEY=[GET-FROM-SUPABASE-DASHBOARD]

# Frontend (Vite)
VITE_SUPABASE_URL=https://ywcfqlyhesnikclesgpr.supabase.co
VITE_SUPABASE_ANON_KEY=[GET-FROM-SUPABASE-DASHBOARD]

# Sentry
SENTRY_DSN=[YOUR-SENTRY_DSN]

# Application
ENVIRONMENT=production
ENABLE_DOCS=false
ALLOWED_ORIGINS=https://your-project.vercel.app
```

## How to Get Supabase Keys

1. Go to https://supabase.com/dashboard/project/ywcfqlyhesnikclesgpr
2. Navigate to **Settings → API**
3. Copy:
   - **anon** key → `SUPABASE_ANON_KEY`
   - **service_role** key → `SUPABASE_SERVICE_ROLE_KEY`

## Important Notes

- Replace `[GET-FROM-SUPABASE-DASHBOARD]` with actual keys
- Replace `https://your-project.vercel.app` with your actual Vercel URL
- Set `ALLOWED_ORIGINS` to your production frontend URL
- All variables should be set for **Production** environment
