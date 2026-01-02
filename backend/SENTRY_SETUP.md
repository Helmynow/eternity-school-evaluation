# Sentry Setup for FastAPI Backend

## Configuration

Sentry SDK has been configured in `fastapi_app.py` with the following settings:

### DSN Configuration

The Sentry DSN is configured via environment variable. If no DSN is provided, Sentry is disabled.

**Set it in your `.env` file:**
```env
SENTRY_DSN=your-sentry-dsn-here
```

## Integrations

The following Sentry integrations are enabled:

1. **FastApiIntegration** - Automatic error and performance tracking for FastAPI
2. **SqlalchemyIntegration** - Database query performance monitoring
3. **MCPIntegration** - Tracks inputs and responses to/from MCP (Model Context Protocol) servers

## Features

### Error Tracking
- Automatic capture of all unhandled exceptions
- HTTP exception tracking
- Database error tracking

### Performance Monitoring
- Request/response time tracking
- Database query performance
- Transaction tracing
- **Performance Profiling:** Detailed profiling of all transactions to identify bottlenecks

### Configuration

- **Traces Sample Rate:** `SENTRY_TRACES_SAMPLE_RATE`
  - Defaults: 1.0 in development, 0.1 in production

- **Profile Session Sample Rate:** `SENTRY_PROFILES_SAMPLE_RATE`
  - Defaults: 1.0 in development, 0.0 in production

- **Profile Lifecycle:** "trace"
  - Automatically runs the profiler when there is an active transaction
  - Provides detailed performance profiling data

- **Send Default PII:** Disabled by default
  - Enable with `SENTRY_SEND_PII=true` if required
  - See [Sentry Data Management](https://docs.sentry.io/platforms/python/data-management/data-collected/) for details

- **Release Tracking:** Configured via `APP_VERSION` environment variable

- **Health Check Filtering:** Health check endpoints are excluded from error tracking

## Testing

### Verify Installation

A test route has been added to verify Sentry integration:

```bash
curl http://localhost:8000/sentry-debug
```

Or visit in browser: `http://localhost:8000/sentry-debug`

This will:
1. Trigger a division by zero error
2. Create a transaction in Sentry Performance section
3. Send an error event to Sentry
4. Connect the error to the transaction

**Note:** The route returns 404 in production.

**Note:** It takes a couple of moments for data to appear in Sentry.

## Environment Variables

Add to your `.env` file:

```env
# Sentry Configuration
SENTRY_DSN=https://your-dsn@sentry.io/project-id
ENVIRONMENT=production  # or development
APP_VERSION=1.0.0
SENTRY_TRACES_SAMPLE_RATE=0.1
SENTRY_PROFILES_SAMPLE_RATE=0.0
SENTRY_SEND_PII=false
```

## Manual Error Reporting

You can manually capture errors:

```python
import sentry_sdk

try:
    # Your code
    pass
except Exception as e:
    sentry_sdk.capture_exception(e)
    raise
```

## Performance Monitoring

Sentry automatically tracks:
- Request duration
- Database query time
- API endpoint performance

View performance data in Sentry dashboard under "Performance" section.

## Best Practices

1. **Don't log sensitive data** - Sentry captures request data by default
2. **Use environment variables** - Don't hardcode DSN
3. **Adjust sample rates** - Reduce in production to avoid overhead
4. **Filter health checks** - Already configured to exclude `/health` endpoints
5. **Monitor performance** - Review slow transactions in Sentry dashboard

## Troubleshooting

### Sentry not capturing errors

1. Check DSN is correct
2. Verify network connectivity to Sentry
3. Check Sentry project settings
4. Review logs for Sentry errors

### Too much data in Sentry

1. Reduce `traces_sample_rate` in production
2. Add more filters in `before_send`
3. Exclude more endpoints from tracking

### Performance impact

1. Reduce sample rate in production
2. Use async error reporting
3. Filter out high-volume endpoints
