# Monitoring and Logging Setup Guide

## 📊 Structured Logging

### Configuration

Structured JSON logging is automatically enabled. Logs are output in JSON format for easy parsing by log aggregation services.

**Environment Variables:**
```env
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FILE=/var/log/app.log  # Optional: file path for logs
```

### Log Format

Logs are output in JSON format:
```json
{
  "timestamp": "2024-01-01T12:00:00.000Z",
  "level": "INFO",
  "logger": "backend.middleware.logging",
  "message": "Request completed",
  "module": "logging",
  "function": "dispatch",
  "line": 45,
  "extra_fields": {
    "type": "response",
    "method": "GET",
    "path": "/api/v2/health",
    "status_code": 200,
    "duration_ms": 12.34,
    "client_ip": "127.0.0.1"
  }
}
```

### Usage

```python
from backend.middleware.logging import get_logger

logger = get_logger(__name__)

logger.info("User action", extra={
    "extra_fields": {
        "user_id": 123,
        "action": "survey_submitted",
        "survey_id": 456
    }
})
```

## 🔄 Log Aggregation Services

### Sentry (Already Configured)

Sentry automatically captures:
- Errors and exceptions
- Performance data
- User context
- Request data

**Configuration:** Already set up in `fastapi_app.py`

### Other Log Aggregation Options

#### 1. CloudWatch (AWS)

```python
# Install: pip install watchtower
import watchtower

handler = watchtower.CloudWatchLogHandler(
    log_group="/aws/app/eternity-eval",
    stream_name="backend"
)
logger.addHandler(handler)
```

**Environment Variables:**
```env
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
AWS_REGION=us-east-1
CLOUDWATCH_LOG_GROUP=/aws/app/eternity-eval
```

#### 2. Datadog

```python
# Install: pip install ddtrace
from ddtrace import patch_all
patch_all()

# Configure in code or via environment
# DD_API_KEY=your-key
# DD_SERVICE=eternity-eval-backend
```

**Environment Variables:**
```env
DD_API_KEY=your-datadog-api-key
DD_SERVICE=eternity-eval-backend
DD_ENV=production
```

#### 3. Logstash/Elasticsearch

Send logs to Logstash endpoint:
```env
LOGSTASH_URL=http://logstash:5044
```

#### 4. Google Cloud Logging

```python
# Install: pip install google-cloud-logging
import google.cloud.logging
client = google.cloud.logging.Client()
client.setup_logging()
```

## 📈 Uptime Monitoring

### Health Check Endpoints

1. **Comprehensive Health Check:**
   ```
   GET /api/v2/health
   ```
   
   Returns:
   - Application status
   - Database connectivity
   - System metrics (CPU, memory, disk)
   - Uptime information
   - Request/error statistics

2. **Simple Health Check:**
   ```
   GET /api/v2/health/simple
   ```
   
   Returns basic status (no database dependency)

### Monitoring Service Setup

#### UptimeRobot

1. Create account at https://uptimerobot.com
2. Add monitor:
   - Type: HTTP(s)
   - URL: `https://api.yourdomain.com/api/v2/health/simple`
   - Interval: 5 minutes
   - Alert contacts: Your email/SMS

#### Pingdom

1. Create account at https://www.pingdom.com
2. Add check:
   - Type: HTTP
   - URL: `https://api.yourdomain.com/api/v2/health`
   - Expected status: 200
   - Check interval: 1 minute

#### Custom Monitoring Script

```bash
#!/bin/bash
# monitor.sh

HEALTH_URL="https://api.yourdomain.com/api/v2/health"
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" $HEALTH_URL)

if [ "$RESPONSE" != "200" ]; then
    echo "Health check failed: $RESPONSE"
    # Send alert (email, Slack, etc.)
fi
```

Run with cron:
```cron
*/5 * * * * /path/to/monitor.sh
```

### Metrics Exposed

The health check endpoint exposes:
- **Uptime**: Server uptime since start
- **CPU**: Usage percentage and core count
- **Memory**: Total, available, and usage percentage
- **Disk**: Total, free, and usage percentage
- **Database**: Connection status and response time
- **Application**: Request count, error count, error rate

## 🔴 Redis Rate Limiting

### Setup

1. **Install Redis:**
   ```bash
   # macOS
   brew install redis
   brew services start redis
   
   # Ubuntu/Debian
   sudo apt-get install redis-server
   sudo systemctl start redis
   ```

2. **Configure Environment:**
   ```env
   USE_REDIS_RATE_LIMIT=true
   REDIS_URL=redis://localhost:6379/0
   # Or for remote Redis:
   REDIS_URL=redis://:password@redis.example.com:6379/0
   ```

3. **Install Python Redis Client:**
   ```bash
   pip install redis>=5.0.0
   ```

### Benefits

- **Distributed**: Works across multiple server instances
- **Persistent**: Rate limits survive server restarts
- **Scalable**: Handles high traffic efficiently
- **Configurable**: Per-path rate limiting

### Fallback

If Redis is unavailable, the system automatically falls back to in-memory rate limiting (single server only).

## 📋 Environment Variables Summary

### Backend (.env)

```env
# Core
ENVIRONMENT=production
APP_VERSION=2.0.0

# Sentry
SENTRY_DSN=your-sentry-dsn

# Database
DATABASE_URL=postgresql://user:pass@host:5432/db
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20

# CORS
ALLOWED_ORIGINS=https://yourdomain.com

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60
USE_REDIS_RATE_LIMIT=true
REDIS_URL=redis://localhost:6379/0

# Logging
LOG_LEVEL=INFO
LOG_FILE=/var/log/app.log
```

## 🚀 Quick Start

1. **Enable Redis Rate Limiting:**
   ```env
   USE_REDIS_RATE_LIMIT=true
   REDIS_URL=redis://localhost:6379/0
   ```

2. **Configure Logging:**
   ```env
   LOG_LEVEL=INFO
   ```

3. **Set Up Uptime Monitoring:**
   - Add health check endpoint to monitoring service
   - Configure alerts for downtime

4. **Set Up Log Aggregation:**
   - Sentry: Already configured
   - Optional: Add CloudWatch, Datadog, or Logstash

## 📊 Monitoring Dashboard

Consider setting up a monitoring dashboard with:
- **Grafana**: Visualize metrics
- **Prometheus**: Metrics collection
- **Kibana**: Log analysis (with Elasticsearch)

## 🔔 Alerting

Recommended alerts:
- Health check failures
- High error rate (>5%)
- High response time (>1s)
- Database connection failures
- High CPU/Memory usage (>80%)
- Disk space low (<20% free)
