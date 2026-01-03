# Database Scaling Guide: 200+ Concurrent Users

This guide explains how the ESE Evaluation System is configured to reliably handle 200+ concurrent users (e.g., during voting or evaluation periods).

## Quick Start

### 1. Update Your DATABASE_URL to Use Transaction Mode (Port 6543)

**Before (Session Mode - Limited):**
```
postgres://postgres.xxx:password@aws-0-region.pooler.supabase.com:5432/postgres
```

**After (Transaction Mode - Scalable):**
```
postgres://postgres.xxx:password@aws-0-region.pooler.supabase.com:6543/postgres
```

Just change the port from `5432` to `6543`. The system will automatically add `?pgbouncer=true` if missing.

### 2. Verify Your Supabase Plan

| Plan | Max Direct Connections | Supavisor Pool Size | Concurrent Clients (Transaction Mode) |
|------|----------------------|---------------------|--------------------------------------|
| Free | 15 | 15 | **200+** ✓ |
| Pro | 60 | 60 | **500+** ✓ |
| Team | 200 | 200 | **1000+** ✓ |

> **Transaction mode** allows many more clients than pool size because connections are shared and released after each query.

### 3. Set Environment Variables

```bash
# Required: Use Transaction mode URL (port 6543)
DATABASE_URL=postgres://postgres.xxx:password@aws-0-region.pooler.supabase.com:6543/postgres

# Optional: For serverless deployments (Vercel, Lambda)
DB_SERVERLESS=true

# Optional: Tune pool settings for persistent deployments
DB_POOL_SIZE=5        # Local pool size (default: 5)
DB_MAX_OVERFLOW=10    # Extra connections allowed (default: 10)
DB_POOL_TIMEOUT=30    # Wait time for connection (default: 30s)

# Optional: Query timeout (prevents long-running queries)
DB_STATEMENT_TIMEOUT=30000  # 30 seconds (default)
```

---

## How It Works

### Session Mode vs Transaction Mode

| Feature | Session Mode (5432) | Transaction Mode (6543) |
|---------|-------------------|------------------------|
| Connection held | Entire session | Per query only |
| Max clients | = Pool size | 200x pool size |
| Prepared statements | ✓ Supported | ✗ Disabled |
| Long transactions | ✓ Supported | Limited to 60s |
| Best for | Admin tools, migrations | Application traffic |

### Why Transaction Mode Scales Better

In **Session mode**, each user holds a database connection for their entire session:
- 200 users = 200 connections needed
- Free tier (15 connections) = ❌ FAIL

In **Transaction mode**, connections are returned to the pool after each query:
- 200 users making queries = ~5-10 concurrent connections
- Free tier (15 connections) = ✅ WORKS

### Architecture

```
┌──────────────────────┐
│   200+ Concurrent    │
│       Users          │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│   Your Application   │
│   (FastAPI + SQLAlchemy)
│                      │
│  NullPool (serverless)│
│  OR QueuePool(5-15)  │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  Supavisor (Port 6543)│
│  Transaction Mode    │
│                      │
│  Handles 200+ clients│
│  with ~15 connections│
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│   PostgreSQL         │
│   (15-60 connections)│
└──────────────────────┘
```

---

## Deployment Configurations

### Serverless (Vercel, AWS Lambda)

The system auto-detects serverless environments and uses `NullPool`:

```python
# Auto-detected via environment variables:
# - VERCEL=1
# - AWS_LAMBDA_FUNCTION_NAME
# - DB_SERVERLESS=true
```

**Why NullPool for serverless?**
- Each function invocation is short-lived
- No point maintaining a local pool
- Let Supavisor handle all pooling

### Persistent (VMs, Containers, Docker)

Uses `QueuePool` with conservative limits:

```bash
# Recommended settings for 200 users
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10
DB_POOL_TIMEOUT=30
```

---

## Monitoring

### Health Check Endpoints

```bash
# Simple health (no DB)
GET /api/v2/health/simple

# Database health with pool status
GET /api/v2/health/database

# Connection pool stats
GET /api/v2/health/pool
```

### Pool Status Response

```json
{
  "timestamp": "2024-01-03T12:00:00Z",
  "pool": {
    "mode": "persistent",
    "pool": "QueuePool",
    "size": 5,
    "checkedin": 4,
    "checkedout": 1,
    "overflow": 0
  }
}
```

### Warning Signs

Monitor these metrics during high load:

| Metric | Healthy | Warning | Critical |
|--------|---------|---------|----------|
| checkedout | < pool_size | = pool_size | Using overflow |
| overflow | 0 | < max_overflow | = max_overflow |
| Response time | < 200ms | < 1000ms | > 1000ms |

---

## Troubleshooting

### "MaxClientsInSessionMode" Error

**Problem:** Using Session mode (port 5432) with too many clients.

**Solution:** Switch to Transaction mode (port 6543):
```bash
# Change in your DATABASE_URL
:5432/postgres → :6543/postgres
```

### "Connection pool exhausted" Error

**Problem:** Too many concurrent queries.

**Solutions:**
1. Ensure you're using Transaction mode (port 6543)
2. Reduce `DB_POOL_SIZE` if in serverless mode
3. Increase Supabase plan for more connections
4. Check for slow queries blocking connections

### "Prepared statement already exists" Error

**Problem:** Prepared statements not disabled for Supavisor.

**Solution:** The system adds `?pgbouncer=true` automatically, but verify:
```bash
DATABASE_URL=...?pgbouncer=true
```

### Slow Queries Blocking Connections

**Problem:** Long-running queries hold connections too long.

**Solutions:**
1. Set query timeout: `DB_STATEMENT_TIMEOUT=30000` (30 seconds)
2. Add database indexes for common queries
3. Optimize N+1 query patterns
4. Use pagination for large result sets

---

## Supabase Plan Recommendations

### For 200 Staff (Your Use Case)

| Scenario | Recommended Plan | Reason |
|----------|-----------------|--------|
| Normal usage (< 50 concurrent) | Free tier | 15 connections sufficient |
| Peak voting (200 concurrent) | Pro ($25/mo) | 60 connections, better performance |
| Heavy analytics + voting | Team | 200 connections, dedicated resources |

### When to Upgrade

Consider upgrading if you see:
- Frequent "max clients reached" errors
- Response times > 1 second during peak
- Database CPU > 80% during voting

---

## Testing High Load

Before a voting period, test with:

```bash
# Install k6 load testing tool
brew install k6

# Create test script (k6-test.js)
cat > k6-test.js << 'EOF'
import http from 'k6/http';
import { check, sleep } from 'k6';

export let options = {
  stages: [
    { duration: '30s', target: 50 },   // Ramp up to 50 users
    { duration: '1m', target: 200 },   // Ramp up to 200 users
    { duration: '2m', target: 200 },   // Stay at 200 users
    { duration: '30s', target: 0 },    // Ramp down
  ],
};

export default function () {
  let res = http.get('https://your-app.vercel.app/api/v2/health/database');
  check(res, { 'status is 200': (r) => r.status === 200 });
  sleep(1);
}
EOF

# Run test
k6 run k6-test.js
```

---

## Summary

| Configuration | Value | Purpose |
|--------------|-------|---------|
| Port | 6543 | Transaction mode |
| pgbouncer | true | Disable prepared statements |
| Pool (serverless) | NullPool | Let Supavisor handle pooling |
| Pool (persistent) | QueuePool(5,10) | Conservative local pool |
| Statement timeout | 30s | Prevent long-running queries |
| Retry logic | 3 attempts | Handle transient failures |

With these settings, your system can reliably handle 200+ concurrent users voting or evaluating each other. 🎉
