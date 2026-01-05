"""
API Integration Tests for Eternity School Evaluation System

These tests verify that the API endpoints work correctly with the database
and return expected responses.
"""

import json
import os
from datetime import datetime, timedelta

import pytest

try:
    import requests
except ModuleNotFoundError:  # pragma: no cover
    requests = None

pytestmark = pytest.mark.api  # Mark all tests in this file as API tests

# Base URL for the API
BASE_URL = os.getenv("TEST_API_BASE_URL", "http://localhost:8000/api/v2")


@pytest.fixture(autouse=True, scope="module")
def require_api_server():
    """Skip these tests unless the API server is running."""
    if requests is None:
        pytest.skip("requests is not installed; skipping API integration tests")
    try:
        res = requests.get(f"{BASE_URL}/health/simple", timeout=2)
        # Health is public; anything other than 200 is treated as unavailable.
        if res.status_code != 200:
            pytest.skip(f"API server not healthy (status={res.status_code}) at {BASE_URL}")
    except Exception:
        pytest.skip(f"API server not running at {BASE_URL}")


class TestSurveyAPI:
    """Test Survey CRUD endpoints"""

    @pytest.fixture
    def auth_headers(self):
        """Get authentication headers"""
        headers = {"Content-Type": "application/json"}
        token = os.getenv("TEST_AUTH_BEARER_TOKEN")
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers

    def test_get_all_surveys(self, auth_headers):
        """Test GET /api/v2/surveys"""
        response = requests.get(f"{BASE_URL}/surveys", headers=auth_headers)
        assert response.status_code in [200, 401, 403]
        if response.status_code != 200:
            return
        data = response.json()
        assert isinstance(data, (list, dict))
        if isinstance(data, dict):
            assert "data" in data or "surveys" in data

    def test_create_survey(self, auth_headers):
        """Test POST /api/v2/surveys"""
        survey_data = {
            "title": f"Test Survey {datetime.now().isoformat()}",
            "description": "Integration test survey",
            "survey_type": "comprehensive",
            "start_date": datetime.now().isoformat(),
            "end_date": (datetime.now() + timedelta(days=30)).isoformat(),
        }
        response = requests.post(f"{BASE_URL}/surveys", headers=auth_headers, json=survey_data)
        assert response.status_code in [200, 201, 401, 403]
        if response.status_code not in [200, 201]:
            return None
        data = response.json()
        assert "id" in data or ("data" in data and "id" in data["data"])
        return data.get("id") or data.get("data", {}).get("id")

    def test_get_survey_by_id(self, auth_headers):
        """Test GET /api/v2/surveys/{id}"""
        # First create a survey
        survey_id = self.test_create_survey(auth_headers)
        if not survey_id:
            pytest.skip("No survey created (auth required or forbidden)")

        response = requests.get(f"{BASE_URL}/surveys/{survey_id}", headers=auth_headers)
        assert response.status_code in [200, 401, 403]
        if response.status_code != 200:
            return
        data = response.json()
        assert "id" in data or ("data" in data and "id" in data["data"])

    def test_get_survey_questions(self, auth_headers):
        """Test GET /api/v2/surveys/{id}/questions"""
        survey_id = self.test_create_survey(auth_headers)
        if not survey_id:
            pytest.skip("No survey created (auth required or forbidden)")

        response = requests.get(f"{BASE_URL}/surveys/{survey_id}/questions", headers=auth_headers)
        assert response.status_code in [200, 401, 403]
        if response.status_code != 200:
            return
        data = response.json()
        assert isinstance(data, (list, dict))

    def test_submit_survey_response(self, auth_headers):
        """Test POST /api/v2/surveys/responses"""
        survey_id = self.test_create_survey(auth_headers)
        if not survey_id:
            pytest.skip("No survey created (auth required or forbidden)")

        response_data = {
            "survey_id": survey_id,
            "question_id": 1,  # Assuming question exists
            "identity_mode": "anonymous",
            "response_text": "Test response",
            "anonymous_id": f"anon_{datetime.now().timestamp()}",
        }
        response = requests.post(f"{BASE_URL}/surveys/responses", headers=auth_headers, json=response_data)
        # May return 404 if question doesn't exist, which is acceptable
        assert response.status_code in [200, 201, 401, 403, 404]

    def test_get_survey_responses_paginated(self, auth_headers):
        """Test GET /api/v2/surveys/{id}/responses with pagination params"""
        # We don't assume survey 1 exists in every environment.
        response = requests.get(
            f"{BASE_URL}/surveys/1/responses", headers=auth_headers, params={"skip": 0, "limit": 10}
        )
        assert response.status_code in [200, 401, 403, 404]
        if response.status_code != 200:
            return
        data = response.json()
        assert isinstance(data, dict)
        assert "responses" in data
        assert isinstance(data["responses"], list)


class TestHybridIdentityAPI:
    """Test Hybrid Identity endpoints"""

    @pytest.fixture
    def auth_headers(self):
        headers = {"Content-Type": "application/json"}
        token = os.getenv("TEST_AUTH_BEARER_TOKEN")
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers

    def _initialize_session(self, auth_headers):
        session_data = {
            "preferred_mode": "anonymous",
            "survey_id": 1,
        }
        response = requests.post(f"{BASE_URL}/hybrid-identity/initialize-session", headers=auth_headers, json=session_data)
        assert response.status_code in [200, 201, 401, 403]
        if response.status_code not in [200, 201]:
            return None
        payload = response.json()
        return payload.get("session_token") or payload.get("data", {}).get("session_token")

    def test_initialize_session(self, auth_headers):
        """Test POST /api/v2/hybrid-identity/initialize-session"""
        session_token = self._initialize_session(auth_headers)
        if not session_token:
            pytest.skip("Auth required or forbidden")
        assert isinstance(session_token, str)

    def test_create_survey_session(self, auth_headers):
        """Test POST /api/v2/hybrid-identity/create-survey-session"""
        session_token = self._initialize_session(auth_headers)

        if session_token:
            params = {
                "survey_type": "comprehensive",
                "session_token": session_token,
            }
            response = requests.post(f"{BASE_URL}/hybrid-identity/create-survey-session", headers=auth_headers, params=params)
            assert response.status_code in [200, 201, 401, 403]

    def test_submit_response(self, auth_headers):
        """Test POST /api/v2/hybrid-identity/submit-response"""
        session_token = self._initialize_session(auth_headers)

        if session_token:
            response_data = {
                "session_token": session_token,
                "responses": {
                    "1": {
                        "question_id": 1,
                        "response_text": "Test response",
                    }
                },
            }
            response = requests.post(f"{BASE_URL}/hybrid-identity/submit-response", headers=auth_headers, json=response_data)
            # May return 400 if questions don't exist for the referenced survey
            assert response.status_code in [200, 201, 400, 401, 403, 404]


class TestSurveyAbandonmentAnalyticsAPI:
    """Smoke test for the admin abandonment analytics endpoint"""

    @pytest.fixture
    def auth_headers(self):
        headers = {"Content-Type": "application/json"}
        token = os.getenv("TEST_AUTH_BEARER_TOKEN")
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers

    def test_abandonment_analytics(self, auth_headers):
        response = requests.get(
            f"{BASE_URL}/surveys/admin/abandonment-analytics",
            headers=auth_headers,
            params={"survey_id": 1, "date_range": "30d"},
        )
        assert response.status_code in [200, 401, 403, 404]
        if response.status_code != 200:
            return
        data = response.json()
        assert isinstance(data, dict)
        assert "summary" in data and "charts" in data


class TestAdminAPI:
    """Test Admin Dashboard endpoints"""

    @pytest.fixture
    def auth_headers(self):
        headers = {"Content-Type": "application/json"}
        token = os.getenv("TEST_AUTH_BEARER_TOKEN")
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers

    def test_get_dashboard(self, auth_headers):
        """Test GET /api/v2/admin/dashboard"""
        response = requests.get(f"{BASE_URL}/admin/dashboard", headers=auth_headers, params={"admin_id": "admin@example.com"})
        # May require authentication
        assert response.status_code in [200, 401, 403]
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, dict)

    def test_get_overview_cards(self, auth_headers):
        """Test GET /api/v2/admin/dashboard/overview-cards"""
        response = requests.get(f"{BASE_URL}/admin/dashboard/overview-cards", headers=auth_headers)
        assert response.status_code in [200, 401, 403]
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, dict)

    def test_get_real_time_metrics(self, auth_headers):
        """Test GET /api/v2/admin/dashboard/real-time-metrics"""
        response = requests.get(f"{BASE_URL}/admin/dashboard/real-time-metrics", headers=auth_headers)
        assert response.status_code in [200, 401, 403]
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, dict)

    def test_get_identity_analytics(self, auth_headers):
        """Test GET /api/v2/admin/dashboard/identity-analytics"""
        response = requests.get(f"{BASE_URL}/admin/dashboard/identity-analytics", headers=auth_headers)
        assert response.status_code in [200, 401, 403]
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, dict)


class TestSurveyTemplatesAPI:
    """Test Survey Templates endpoints"""

    @pytest.fixture
    def auth_headers(self):
        headers = {"Content-Type": "application/json"}
        token = os.getenv("TEST_AUTH_BEARER_TOKEN")
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers

    def test_get_comprehensive_template(self, auth_headers):
        """Test GET /api/v2/survey-templates/comprehensive"""
        response = requests.get(
            f"{BASE_URL}/survey-templates/comprehensive", headers=auth_headers, params={"identity_mode": "identified"}
        )
        assert response.status_code in [200, 401, 403]
        if response.status_code != 200:
            return
        data = response.json()
        assert isinstance(data, dict)
        assert "title" in data or "questions" in data

    def test_get_section_template(self, auth_headers):
        """Test GET /api/v2/survey-templates/section/{category}"""
        categories = ["climate", "feedback", "evaluation"]
        for category in categories:
            response = requests.get(
                f"{BASE_URL}/survey-templates/section/{category}",
                headers=auth_headers,
                params={"identity_mode": "identified"},
            )
            assert response.status_code in [200, 401, 403, 404]
            if response.status_code == 200:
                data = response.json()
                assert isinstance(data, dict)


class TestSurveyIdentityAPI:
    """Test Survey Identity endpoints"""

    @pytest.fixture
    def auth_headers(self):
        headers = {"Content-Type": "application/json"}
        token = os.getenv("TEST_AUTH_BEARER_TOKEN")
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers

    def test_set_preference(self, auth_headers):
        """Test POST /api/v2/survey/identity/preference"""
        preference_data = {
            "survey_id": 1,
            "preference": "anonymous",
        }
        response = requests.post(f"{BASE_URL}/survey/identity/preference", headers=auth_headers, json=preference_data)
        assert response.status_code in [200, 201, 401, 403, 404]

    def test_get_status(self, auth_headers):
        """Test GET /api/v2/survey/identity/status/{user_email}"""
        user_email = "test@example.com"
        response = requests.get(f"{BASE_URL}/survey/identity/status/{user_email}", headers=auth_headers)
        assert response.status_code in [200, 401, 403, 404]
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, dict)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
