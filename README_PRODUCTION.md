# Production Deployment - Quick Start (ENVIRONMENT=production, REQUIRE_SUPABASE_AUTH=true, SUPABASE_JWT_SECRET=...)

## Important note for Vercel deployments

Vercel Serverless Functions have a **250MB unzipped** size limit. This project’s FastAPI backend includes large binary dependencies (notably `numpy`/`pandas`), which commonly exceed that limit when deployed as a Vercel Python Function.

Recommended production approach:

1) Deploy the **frontend** on Vercel (static).
2) Deploy the **backend** as a separate service (Docker/container).
3) Set `VITE_API_URL` in Vercel to point to your backend base URL.

See `README_BACKEND_DEPLOY.md`.

## 🚀 All Production Features Implemented

### ✅ Completed Features

1. **Structured Logging (JSON Format)** - `backend/middleware/logging.py`
2. **Log Aggregation Service Support** - Ready for Sentry, CloudWatch, Datadog, etc.
3. **Uptime Monitoring Setup** - `backend/monitoring/uptime.py`
4. **Redis for Distributed Rate Limiting** - `backend/middleware/rate_limit_redis.py`
5. **Security Headers** - `backend/middleware/security.py`
6. **CORS Configuration** - Environment-aware
7. **Database Connection Pooling** - Production-ready
8. **Sentry Integration** - Error tracking and performance monitoring

## 📋 Quick Setup

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure Environment Variables

**Backend:**
```bash
cp backend/.env.example backend/.env
# Edit backend/.env with your production values
```

**Frontend:**
```bash
cp frontend/.env.example frontend/.env
# Edit frontend/.env with your production values
```

### 2.1 Bootstrap CEO (First Super Admin) — REQUIRED

The **first super admin is the CEO**, derived from the database:
- `people.role_title` must contain **"CEO"** (case-insensitive)
- the **first active** matching row (by `created_at`) becomes the bootstrap super admin

Ensure the CEO exists in `people` *before* first production login.

**Option A (recommended):** run the bootstrap script (idempotent)
```bash
# From the repo root
python -m backend.bootstrap_ceo --email "ceo@yourdomain.com" --full-name "CEO Name"
# If a different CEO already exists and you need to override:
python -m backend.bootstrap_ceo --email "ceo@yourdomain.com" --full-name "CEO Name" --force
```

**Option B:** run SQL in Supabase SQL Editor (Dashboard → SQL Editor)
```sql
insert into public.people (email, full_name, role_title, segment, active)
values ('ceo@yourdomain.com', 'CEO Name', 'CEO', 'whole_school', true)
on conflict (email) do update
set full_name = excluded.full_name,
    role_title = excluded.role_title,
    segment = excluded.segment,
    active = true,
    updated_at = now();
```

### 3. Set Up Redis (Optional, for distributed rate limiting)

```bash
# macOS
brew install redis
brew services start redis

# Ubuntu
sudo apt-get install redis-server
sudo systemctl start redis
```

Then in `backend/.env`:
```env
USE_REDIS_RATE_LIMIT=true
REDIS_URL=redis://localhost:6379/0
```

### 4. Set Up Monitoring

1. **Uptime Monitoring:**
   - Add `GET /api/v2/health/simple` to UptimeRobot/Pingdom
   - Set alert contacts

2. **Log Aggregation:**
   - Sentry: Already configured
   - Optional: Add CloudWatch, Datadog, or Logstash

### 5. Deploy

**Backend:**
```bash
ENVIRONMENT=production uvicorn backend.fastapi_app:app --host 0.0.0.0 --port 8000
```

**Frontend:**
```bash
cd frontend
npm run build
# Deploy dist/ to your hosting service
```

## 📚 Documentation

- **PRODUCTION_READINESS.md** - Complete checklist
- **MONITORING_SETUP.md** - Monitoring and logging guide
- **IMPLEMENTATION_SUMMARY.md** - Implementation details
- **SENTRY_SETUP.md** - Sentry configuration

## 🔑 Key Environment Variables

### Backend (.env)
- `ENVIRONMENT=production`
- `ALLOWED_ORIGINS=https://yourdomain.com`
- `DATABASE_URL=postgresql://...`
- `REQUIRE_SUPABASE_AUTH=true`
- `SUPABASE_JWT_SECRET=...` (from Supabase Dashboard → Project Settings → API → JWT Secret)
- `SUPABASE_JWT_AUD=authenticated` (default)
- `USE_REDIS_RATE_LIMIT=true` (if using Redis)
- `REDIS_URL=redis://...` (if using Redis)
- `LOG_LEVEL=INFO`

### Frontend (.env)
- `VITE_API_URL=https://api.yourdomain.com`
- `VITE_SUPABASE_URL=...`
- `VITE_SENTRY_DSN=...`

## ✅ Production Checklist

- [x] CORS configured
- [x] Security headers added
- [x] Rate limiting implemented
- [x] Database pooling configured
- [x] Structured logging enabled
- [x] Uptime monitoring ready
- [x] Redis rate limiting available
- [x] Sentry error tracking configured
- [x] Environment variables documented
- [x] Health check endpoints available

**System is production-ready!** 🎉
