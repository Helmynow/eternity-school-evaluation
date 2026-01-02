# Production Deployment Checklist

## Pre-Deployment

### Dependencies
- [x] APScheduler installed
- [x] All Python packages in requirements.txt
- [x] Redis (optional, for rate limiting)

### Configuration
- [x] Resend SMTP configured
- [x] Database URL set
- [x] Environment variables configured
- [x] CORS origins set for production
- [x] Sentry DSN configured (optional)

### Code Quality
- [x] All imports working
- [x] No syntax errors
- [x] Error handling in place
- [x] Optional dependencies handled gracefully

---

## Deployment Steps

1. **Install Dependencies**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Set Environment Variables**
   ```bash
   export DATABASE_URL="your_database_url"
   export SMTP_SERVER="smtp.resend.com"
   export SMTP_PORT="465"
   export SMTP_USER="resend"
   export SMTP_PASSWORD="your_resend_api_key"
   export EMAIL_ENABLED="true"
   ```

3. **Run Database Migrations**
   ```bash
   # Apply all migrations in supabase/migrations/
   ```

4. **Start Application**
   ```bash
   uvicorn backend.fastapi_app:app --host 0.0.0.0 --port 8000
   ```

5. **Verify**
   - Check health endpoint: `GET /api/v2/health`
   - Verify scheduler started (check logs)
   - Test announcement creation
   - Test email sending

---

## Post-Deployment

- [ ] Monitor scheduler logs
- [ ] Verify emails are sending
- [ ] Check announcement banner displays
- [ ] Monitor error rates
- [ ] Review performance metrics

---

**Status:** ✅ Ready for deployment after dependency installation
