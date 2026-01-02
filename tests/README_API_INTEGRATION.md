# API Integration Tests

These tests verify that API endpoints work correctly with the database and return expected responses.

## Setup

1. Ensure the backend server is running:
```bash
cd backend
python -m uvicorn fastapi_app:app --reload
```

2. Install test dependencies:
```bash
pip install pytest requests
```

## Running Tests

### Run all API integration tests:
```bash
pytest tests/test_api_integration.py -v
```

### Run specific test class:
```bash
pytest tests/test_api_integration.py::TestSurveyAPI -v
```

### Run with coverage:
```bash
pytest tests/test_api_integration.py --cov=backend --cov-report=html
```

## Test Structure

- `TestSurveyAPI` - Tests for Survey CRUD endpoints
- `TestHybridIdentityAPI` - Tests for Hybrid Identity endpoints
- `TestAdminAPI` - Tests for Admin Dashboard endpoints
- `TestSurveyTemplatesAPI` - Tests for Survey Templates endpoints
- `TestSurveyIdentityAPI` - Tests for Survey Identity endpoints

## Configuration

Update `BASE_URL` in `test_api_integration.py` to match your backend URL:
```python
BASE_URL = "http://localhost:8000/api/v2"
```

## Authentication

Tests currently use mock authentication headers. In production, you should:
1. Authenticate and get a real token
2. Include the token in `auth_headers` fixture
3. Handle token refresh if needed

## Notes

- Some tests may return 404 if test data doesn't exist (this is acceptable)
- Tests are designed to be idempotent where possible
- Clean up test data after tests if needed
