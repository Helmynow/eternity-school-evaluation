# FastAPI Endpoints Documentation

## Overview

The FastAPI application provides high-performance endpoints for the Eternity School Evaluation System, including EOM nominations, MRE evaluations, bias detection, and CEO report exports.

## Base URL

```
http://localhost:8000
```

## Authentication (Optional)

If API key auth is enabled (`REQUIRE_API_KEY=true`), include:

```
Header: x-api-key: <your-api-key>
```

## API Documentation

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## Endpoints

### 1. EOM Nomination Endpoints

#### Submit EOM Nomination
```http
POST /api/v2/eom/nominations/submit
```

**Request Body:**
```json
{
  "nominee_email": "teacher1@eternity.edu",
  "eom_cycle_id": 1,
  "nominated_by": "principal@eternity.edu",
  "nomination_reason": "Outstanding performance in student engagement",
  "category": "student_engagement",
  "check_attendance": true
}
```

**Response:**
```json
{
  "nomination_id": 123,
  "is_valid": true,
  "errors": [],
  "warnings": ["Person has won EOM 2 time(s) recently. Consider rotation for fairness."],
  "details": {
    "nominee_email": "teacher1@eternity.edu",
    "eom_cycle_id": 1,
    "category": "student_engagement",
    "rotation_check": {...},
    "attendance_check": {...}
  }
}
```

**Validation Checks:**
- Rotation rules (one win per term)
- Attendance records (minimum 90% attendance)
- Duplicate nominations
- Leader nomination limits

#### Validate EOM Nomination (Pre-submission)
```http
POST /api/v2/eom/nominations/validate
```

Validates a nomination without creating it. Same request body as submit endpoint.

#### Batch Validate Nominations
```http
POST /api/v2/eom/nominations/batch-validate?eom_cycle_id=1
```

**Request Body:**
```json
[
  {
    "nominee_email": "teacher1@eternity.edu",
    "nominated_by": "principal@eternity.edu",
    "category": "academic"
  },
  {
    "nominee_email": "admin1@eternity.edu",
    "nominated_by": "ceo@eternity.edu",
    "category": "admin"
  }
]
```

### 2. MRE Evaluation Endpoints

#### Process MRE Evaluation
```http
POST /api/v2/mre/evaluations/process
```

**Request Body:**
```json
{
  "assignment_id": 456,
  "rating": 4.5,
  "comments": "Excellent performance across all domains",
  "domain_scores": {
    "teaching": 4.5,
    "collaboration": 4.0,
    "innovation": 5.0
  },
  "status": "submitted"
}
```

**Response:**
```json
{
  "evaluation_id": 789,
  "assignment_id": 456,
  "rating": 4.5,
  "weighted_rating": 4.05,
  "weight_applied": 0.9,
  "target_email": "teacher1@eternity.edu",
  "rater_email": "manager@eternity.edu",
  "target_group": "academic",
  "rater_context": "manager_review",
  "status": "submitted"
}
```

**Features:**
- Automatic weight calculation based on target group and rater context
- Weighted rating computation
- Domain-specific score storage

#### Get Weighted Scores
```http
GET /api/v2/mre/evaluations/{cycle_id}/weighted-scores
GET /api/v2/mre/evaluations/{cycle_id}/weighted-scores?target_email=teacher1@eternity.edu
```

Returns weighted evaluation scores for a cycle, optionally filtered by target.

### 3. Bias Detection Endpoints

#### Generate Bias Report
```http
POST /api/v2/bias/reports/generate
GET /api/v2/bias/reports/{cycle_id}
```

**Request Body (POST):**
```json
{
  "cycle_id": 1,
  "include_target_analysis": true,
  "target_email": "teacher1@eternity.edu"
}
```

**Response:**
```json
{
  "cycle_id": 1,
  "overall_bias_score": 0.45,
  "bias_level": "medium",
  "total_evaluations": 150,
  "total_raters": 25,
  "total_targets": 30,
  "findings_count": 5,
  "findings_by_type": {
    "role_bias": 1,
    "harshness_bias": 2,
    "structural_incomplete_360": 1,
    "temporal_bias": 1
  },
  "findings_by_severity": {
    "high": 1,
    "medium": 3,
    "low": 1
  },
  "findings": [...],
  "context_coverage": {...},
  "statistical_summary": {...},
  "recommendations": [...],
  "generated_at": "2024-01-15T10:30:00"
}
```

**Bias Types Detected:**
- Structural incompleteness (missing 360-degree perspectives)
- Role-based bias
- Temporal bias (recency/primacy)
- Distribution bias (centrality, harshness, leniency)
- Similarity bias (halo effect)
- ML-based patterns (outliers, reciprocal bias)
- Inter-rater reliability

#### Get Target-Specific Bias Summary
```http
GET /api/v2/bias/reports/{cycle_id}/target/{target_email}
```

Returns bias analysis for a specific target person.

### 4. CEO Report Export Endpoints

#### Export CEO Report
```http
POST /api/v2/reports/ceo/export
GET /api/v2/reports/ceo/{cycle_id}?format=csv&include_bias_analysis=true
```

**Request Body (POST):**
```json
{
  "cycle_id": 1,
  "format": "csv",
  "include_bias_analysis": true,
  "include_weighted_scores": true,
  "segment_filter": "national"
}
```

**Supported Formats:**
- `csv`: Comma-separated values file
- `json`: Structured JSON response
- `excel`: Excel spreadsheet (requires openpyxl)

**Query Parameters (GET):**
- `format`: csv, json, or excel (default: json)
- `include_bias_analysis`: Include bias analysis in report (default: true)
- `include_weighted_scores`: Include weighted scores (default: true)
- `segment_filter`: Filter by segment (national, international, whole_school)

**CSV Export Includes:**
- Cycle information
- Target and rater details
- Ratings and weighted ratings
- Domain scores (if available)
- Bias analysis summary

**Excel Export Includes:**
- Main evaluation data sheet
- Separate bias analysis sheet
- Formatted headers and styling

## Error Handling

All endpoints return standard HTTP status codes:

- `200 OK`: Successful request
- `400 Bad Request`: Invalid request data
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

**Error Response Format:**
```json
{
  "detail": "Error message describing what went wrong"
}
```

## Authentication

Currently, endpoints do not require authentication. In production, add authentication middleware:

```python
from fastapi.security import HTTPBearer

security = HTTPBearer()

@app.post("/api/v2/eom/nominations/submit")
async def submit_eom_nomination(
    nomination: EOMNominationRequest,
    token: str = Depends(security),
    ...
):
    # Verify token and get user
    ...
```

## Rate Limiting

Consider adding rate limiting for production:

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/v2/eom/nominations/submit")
@limiter.limit("10/minute")
async def submit_eom_nomination(...):
    ...
```

## Running the Server

```bash
# Using the provided script
./run_fastapi.sh

# Or directly with uvicorn
uvicorn backend.fastapi_app:app --host 0.0.0.0 --port 8000 --reload
```

## Testing

Use the interactive API documentation at `/docs` to test endpoints, or use curl:

```bash
# Submit EOM nomination
curl -X POST "http://localhost:8000/api/v2/eom/nominations/submit" \
  -H "Content-Type: application/json" \
  -d '{
    "nominee_email": "teacher1@eternity.edu",
    "eom_cycle_id": 1,
    "nominated_by": "principal@eternity.edu",
    "category": "academic"
  }'

# Get bias report
curl "http://localhost:8000/api/v2/bias/reports/1"

# Export CEO report as CSV
curl "http://localhost:8000/api/v2/reports/ceo/1?format=csv" \
  --output ceo_report.csv
```

## Performance Considerations

- FastAPI uses async/await for better performance
- Database sessions are properly managed with dependencies
- Background tasks for audit logging don't block responses
- Large exports use streaming responses to avoid memory issues

## Flask Deprecation

FastAPI is the primary and only supported API. The legacy Flask app is deprecated and should not be used.
