# Fix Deployment Issues ⚠️

## Issue 1: Vercel Blank Screen - Authentication Protection Enabled

### Problem
Vercel is showing "Authentication Required" instead of your app.

### Solution: Disable Deployment Protection

1. Go to: https://vercel.com/eternity-school-of-egypt/eternity-school-evaluation/settings/deployment-protection
2. **Disable "Vercel Authentication"** or **"Password Protection"**
3. Save settings
4. Your app will be publicly accessible

**OR** if you want to keep protection:
- Add bypass token to your URL
- Configure team authentication
- Set up custom authentication

## Issue 2: GitHub Tests Failing

### Problem
All CI tests are failing on GitHub Actions.

### Likely Causes
1. Missing dependencies in requirements.txt
2. Python path issues
3. Database initialization failures
4. Test configuration issues

### Solution: Check GitHub Actions Logs

```bash
# View latest workflow run
gh run list --limit 1

# View specific run logs
gh run view [RUN_ID] --log
```

### Common Fixes

1. **Missing `lib/` directory in .gitignore**:
   - The `.gitignore` file has `lib/` ignored
   - This blocks `frontend/src/lib/` files from being pushed
   - **FIX**: Update `.gitignore` to exclude frontend lib files

2. **Python dependencies**:
   - Ensure all backend dependencies are in `backend/requirements.txt`
   - Ensure root `requirements.txt` has common dependencies

3. **pytest configuration**:
   - Check `pytest.ini` and `pyproject.toml` are valid
   - Ensure test markers are properly defined

## Quick Fixes to Apply

### 1. Fix .gitignore (CRITICAL)

The `lib/` entry in `.gitignore` is blocking `frontend/src/lib/` files.

**Current .gitignore line 16**:
```
lib/
```

**Should be**:
```
# Python lib directories (not frontend)
/lib/
/lib64/
```

### 2. Fix vercel.json routing

Updated to properly serve the built frontend files.

### 3. Check GitHub Actions

Run locally to debug:
```bash
# Install dependencies
pip install -r requirements.txt
pip install -r backend/requirements.txt

# Set environment
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/eternity_school_test"
export SENTRY_DSN=""
export ENVIRONMENT="test"
export EMAIL_ENABLED="false"
export PYTHONPATH="$PWD/backend:$PWD"

# Run tests
pytest tests/ -v --ignore=tests/test_api_integration.py -m "not api"
```

## Steps to Fix Both Issues

### Step 1: Disable Vercel Authentication

1. Go to Vercel Dashboard: https://vercel.com/eternity-school-of-egypt/eternity-school-evaluation/settings/deployment-protection
2. **Turn OFF** Deployment Protection
3. Save

### Step 2: Fix .gitignore

```bash
cd /Users/helmy/Desktop/team/eternity-school-evaluation

# Update .gitignore to not ignore frontend/src/lib/
# Change line 16 from "lib/" to "/lib/" and "/lib64/"

git add .gitignore
git commit -m "Fix: Update .gitignore to not block frontend/src/lib/ files"
git push origin main
```

### Step 3: Push Missing Files

```bash
# Force add the lib files that were ignored
git add -f frontend/src/lib/
git commit -m "Fix: Add missing frontend lib files"
git push origin main
```

### Step 4: Redeploy to Vercel

```bash
vercel --prod
```

### Step 5: Check GitHub Tests

After pushing, check if tests pass:
```bash
gh run list --limit 1
gh run watch
```

## Verification

### Vercel
- Visit: https://eternity-school-evaluation-dk66gk5yz-eternity-school-of-egypt.vercel.app
- Should show your app, not authentication page

### GitHub
- Check: https://github.com/Helmynow/eternity-school-evaluation/actions
- Tests should pass (green checkmark)

---

## Need Help?

If issues persist:
1. Check Vercel function logs: `vercel logs [URL]`
2. Check GitHub Actions logs: `gh run view [RUN_ID] --log`
3. Test locally first before deploying
