# Next Steps - Security Audit Fixes

## ✅ Completed (Frontend Audit)

### Low Priority - All Fixed
- ✅ Removed unused `supabase` import from `App.jsx`
- ✅ Fixed auth token retrieval in `api.js` to use Supabase v2 sessions
- ✅ Added backend persistence to `Settings.jsx` component
- ✅ Verified localStorage usage is secure and appropriate

---

## 🔴 High Priority - Remaining Issues

### 1. Hard-coded Database Credentials ⚠️ CRITICAL
**Files:**
- `setup_db.sh` (line 5)
- `supabase/setup.sh` (line 82)
- `run.sh` (if present)

**Issue:** Database password exposed in shell scripts
```bash
export DATABASE_URL="postgresql://postgres:oRyY5M5S5op6ARqi@db.ywcfqlyhesnikclesgpr.supabase.co:5432/postgres"
```

**Action Required:**
1. Remove hard-coded credentials
2. Use environment variables or `.env` file
3. Add these files to `.gitignore` if they contain secrets
4. Rotate the exposed database password immediately

**Fix:**
```bash
# setup_db.sh should use:
export DATABASE_URL="${DATABASE_URL:-postgresql://postgres:${DB_PASSWORD}@${DB_HOST}:5432/postgres}"
```

---

### 2. Sentry Configuration ✅ VERIFIED
**Status:** Already fixed - uses environment variables
- ✅ No hard-coded DSN
- ✅ `send_default_pii` uses env var (defaults to false)
- ✅ Sample rates are environment-aware (10% in production)

**No action needed** - Configuration is secure

---

### 3. CORS Configuration ✅ VERIFIED
**Status:** Already fixed
- ✅ Uses `ALLOWED_ORIGINS` environment variable
- ✅ No `allow_origins=["*"]` with `allow_credentials=True`
- ✅ Properly configured for production

**No action needed** - Configuration is secure

---

### 4. Backend Entrypoint Mismatch ✅ RESOLVED
**Status:** FastAPI is the primary backend  
**Fixes Applied:**
- `run.sh` uses FastAPI
- Docs updated to reference FastAPI
- `backend/app.py` deprecated stub

---

## 🟡 Medium Priority - Remaining Issues

### 5. AuditLogger Request Handling ✅ RESOLVED
**Files:** `audit_logger.py`, `fastapi_app.py`

**Fix:** Removed Flask dependency; added optional request object handling

---

### 6. Example Scripts Missing Helper ✅ RESOLVED
**Files:**
- `bias_free_suggestions_example.py`
- `participation_analytics_example.py`
- `identity_transition_example.py`
- `eom_predictive_example.py`

**Fix:** Added `get_db_session` helper to `backend/database.py`

---

### 7. Pydantic v2 Compatibility ✅ RESOLVED
**File:** `fastapi_app.py`

**Fix:** Updated to `@field_validator`

---

### 8. Duplicate Route Definitions ✅ RESOLVED
**File:** `fastapi_app.py`

**Fix:** Single `/sentry-debug` route with production guard

---

## 📋 Recommended Action Order

### Immediate (Before Next Commit)
1. **Fix hard-coded database credentials** (Critical security issue)
   - Update `setup_db.sh`
   - Update `supabase/setup.sh`
   - Rotate exposed password
   - Add to `.gitignore` if needed

### Short-term (This Week)
2. **Fix AuditLogger for FastAPI**
3. **Fix example scripts** (add missing helper)
4. **Fix Pydantic v2 compatibility**
5. **Remove duplicate routes**

### Documentation
6. **Update README.md** to reflect FastAPI as primary backend
7. **Verify backend entrypoint** in all scripts/docs

---

## 🚀 Quick Start Commands

### To fix database credentials:
```bash
# 1. Remove hard-coded password from setup_db.sh
# 2. Use environment variable instead
# 3. Rotate the exposed password in Supabase
```

### To verify backend entrypoint:
```bash
# Check what run.sh actually runs
cat run.sh
# Should use: uvicorn backend.fastapi_app:app
```

### To test fixes:
```bash
# Test example scripts
python examples/bias_free_suggestions_example.py
python examples/participation_analytics_example.py
```

---

## 📝 Notes

- Frontend audit is **100% complete** ✅
- Most backend security issues are already fixed ✅
- Remaining issues are primarily code quality and configuration
- Database credentials exposure is the **only critical security issue** remaining
