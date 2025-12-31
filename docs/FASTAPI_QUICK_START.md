# FastAPI Quick Start Guide

## Installation

1. **Install dependencies:**
   ```bash
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Run the FastAPI server:**
   ```bash
   ./run_fastapi.sh
   ```
   
   Or manually:
   ```bash
   uvicorn backend.fastapi_app:app --host 0.0.0.0 --port 8000 --reload
   ```

3. **Access API documentation:**
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

## Quick Examples

### 1. Submit EOM Nomination

```bash
curl -X POST "http://localhost:8000/api/v2/eom/nominations/submit" \
  -H "Content-Type: application/json" \
  -d '{
    "nominee_email": "teacher1@eternity.edu",
    "eom_cycle_id": 1,
    "nominated_by": "principal@eternity.edu",
    "nomination_reason": "Outstanding performance",
    "category": "student_engagement",
    "check_attendance": true
  }'
```

### 2. Process MRE Evaluation

```bash
curl -X POST "http://localhost:8000/api/v2/mre/evaluations/process" \
  -H "Content-Type: application/json" \
  -d '{
    "assignment_id": 456,
    "rating": 4.5,
    "comments": "Excellent work",
    "domain_scores": {
      "teaching": 4.5,
      "collaboration": 4.0
    },
    "status": "submitted"
  }'
```

### 3. Generate Bias Report

```bash
curl "http://localhost:8000/api/v2/bias/reports/1"
```

### 4. Export CEO Report (CSV)

```bash
curl "http://localhost:8000/api/v2/reports/ceo/1?format=csv" \
  --output ceo_report.csv
```

## Python Client Example

```python
import requests

BASE_URL = "http://localhost:8000"

# Submit EOM nomination
response = requests.post(
    f"{BASE_URL}/api/v2/eom/nominations/submit",
    json={
        "nominee_email": "teacher1@eternity.edu",
        "eom_cycle_id": 1,
        "nominated_by": "principal@eternity.edu",
        "category": "academic"
    }
)
print(response.json())

# Process MRE evaluation
response = requests.post(
    f"{BASE_URL}/api/v2/mre/evaluations/process",
    json={
        "assignment_id": 456,
        "rating": 4.5,
        "status": "submitted"
    }
)
print(response.json())

# Get bias report
response = requests.get(f"{BASE_URL}/api/v2/bias/reports/1")
print(response.json())

# Export CEO report
response = requests.get(
    f"{BASE_URL}/api/v2/reports/ceo/1",
    params={"format": "csv"}
)
with open("ceo_report.csv", "wb") as f:
    f.write(response.content)
```

## Key Features

✅ **Automatic Validation**: EOM nominations are validated before submission
✅ **Weight Calculation**: MRE evaluations automatically apply weight matrix
✅ **Comprehensive Bias Detection**: Full 360-degree bias analysis
✅ **Multiple Export Formats**: CSV, JSON, and Excel support
✅ **Audit Trail**: All actions are logged automatically
✅ **Async Performance**: FastAPI provides excellent performance

## Next Steps

- Review the full API documentation at `/docs`
- Check the detailed endpoint documentation in `FASTAPI_ENDPOINTS.md`
- Integrate with your frontend application
- Add authentication as needed for production

