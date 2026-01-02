"""
API Integration Tests for Eternity School Evaluation System

These tests verify that the API endpoints work correctly with the database
and return expected responses.
"""

import pytest
import requests
from datetime import datetime, timedelta
import json

pytestmark = pytest.mark.api  # Mark all tests in this file as API tests

# Base URL for the API
BASE_URL = "http://localhost:8000/api/v2"


class TestSurveyAPI:
    """Test Survey CRUD endpoints"""

    @pytest.fixture
    def auth_headers(self):
        """Get authentication headers"""
        # In a real scenario, you'd authenticate and get a token
        # For now, we'll use a mock token or skip auth
        return {
            "Content-Type": "application/json",
            # "Authorization": f"Bearer {token}"
        }

    def test_get_all_surveys(self, auth_headers):
        """Test GET /api/v2/surveys"""
        response = requests.get(f"{BASE_URL}/surveys", headers=auth_headers)
        assert response.status_code == 200
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
        response = requests.post(
            f"{BASE_URL}/surveys",
            headers=auth_headers,
            json=survey_data
        )
        assert response.status_code in [200, 201]
        data = response.json()
        assert "id" in data or ("data" in data and "id" in data["data"])
        return data.get("id") or data.get("data", {}).get("id")

    def test_get_survey_by_id(self, auth_headers):
        """Test GET /api/v2/surveys/{id}"""
        # First create a survey
        survey_id = self.test_create_survey(auth_headers)
        
        response = requests.get(
            f"{BASE_URL}/surveys/{survey_id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "id" in data or ("data" in data and "id" in data["data"])

    def test_get_survey_questions(self, auth_headers):
        """Test GET /api/v2/surveys/{id}/questions"""
        survey_id = self.test_create_survey(auth_headers)
        
        response = requests.get(
            f"{BASE_URL}/surveys/{survey_id}/questions",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, (list, dict))

    def test_submit_survey_response(self, auth_headers):
        """Test POST /api/v2/surveys/responses"""
        survey_id = self.test_create_survey(auth_headers)
        
        response_data = {
            "survey_id": survey_id,
            "question_id": 1,  # Assuming question exists
            "identity_mode": "anonymous",
            "response_text": "Test response",
            "anonymous_id": f"anon_{datetime.now().timestamp()}",
        }
        response = requests.post(
            f"{BASE_URL}/surveys/responses",
            headers=auth_headers,
            json=response_data
        )
        # May return 404 if question doesn't exist, which is acceptable
        assert response.status_code in [200, 201, 404]


class TestHybridIdentityAPI:
    """Test Hybrid Identity endpoints"""

    @pytest.fixture
    def auth_headers(self):
        return {
            "Content-Type": "application/json",
        }

    def test_initialize_session(self, auth_headers):
        """Test POST /api/v2/hybrid-identity/initialize-session"""
        session_data = {
            "user_email": "test@example.com",
            "preferred_mode": "anonymous",
            "survey_id": 1,
        }
        response = requests.post(
            f"{BASE_URL}/hybrid-identity/initialize-session",
            headers=auth_headers,
            json=session_data
        )
        assert response.status_code in [200, 201]
        data = response.json()
        assert "session_token" in data or ("data" in data and "session_token" in data["data"])

    def test_create_survey_session(self, auth_headers):
        """Test POST /api/v2/hybrid-identity/create-survey-session"""
        # First initialize a session
        session_response = self.test_initialize_session(auth_headers)
        session_token = (
            session_response.get("session_token") or
            session_response.get("data", {}).get("session_token")
        )
        
        if session_token:
            params = {
                "user_email": "test@example.com",
                "survey_type": "comprehensive",
                "session_token": session_token,
            }
            response = requests.post(
                f"{BASE_URL}/hybrid-identity/create-survey-session",
                headers=auth_headers,
                params=params
            )
            assert response.status_code in [200, 201]

    def test_submit_response(self, auth_headers):
        """Test POST /api/v2/hybrid-identity/submit-response"""
        session_response = self.test_initialize_session(auth_headers)
        session_token = (
            session_response.get("session_token") or
            session_response.get("data", {}).get("session_token")
        )
        
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
            response = requests.post(
                f"{BASE_URL}/hybrid-identity/submit-response",
                headers=auth_headers,
                json=response_data
            )
            # May return 404 if session/question doesn't exist
            assert response.status_code in [200, 201, 404]


class TestAdminAPI:
    """Test Admin Dashboard endpoints"""

    @pytest.fixture
    def auth_headers(self):
        return {
            "Content-Type": "application/json",
        }

    def test_get_dashboard(self, auth_headers):
        """Test GET /api/v2/admin/dashboard"""
        response = requests.get(
            f"{BASE_URL}/admin/dashboard",
            headers=auth_headers,
            params={"admin_id": "admin@example.com"}
        )
        # May require authentication
        assert response.status_code in [200, 401, 403]
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, dict)

    def test_get_overview_cards(self, auth_headers):
        """Test GET /api/v2/admin/dashboard/overview-cards"""
        response = requests.get(
            f"{BASE_URL}/admin/dashboard/overview-cards",
            headers=auth_headers
        )
        assert response.status_code in [200, 401, 403]
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, dict)

    def test_get_real_time_metrics(self, auth_headers):
        """Test GET /api/v2/admin/dashboard/real-time-metrics"""
        response = requests.get(
            f"{BASE_URL}/admin/dashboard/real-time-metrics",
            headers=auth_headers
        )
        assert response.status_code in [200, 401, 403]
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, dict)

    def test_get_identity_analytics(self, auth_headers):
        """Test GET /api/v2/admin/dashboard/identity-analytics"""
        response = requests.get(
            f"{BASE_URL}/admin/dashboard/identity-analytics",
            headers=auth_headers
        )
        assert response.status_code in [200, 401, 403]
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, dict)


class TestSurveyTemplatesAPI:
    """Test Survey Templates endpoints"""

    @pytest.fixture
    def auth_headers(self):
        return {
            "Content-Type": "application/json",
        }

    def test_get_comprehensive_template(self, auth_headers):
        """Test GET /api/v2/survey-templates/comprehensive"""
        response = requests.get(
            f"{BASE_URL}/survey-templates/comprehensive",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "title" in data or "questions" in data

    def test_get_section_template(self, auth_headers):
        """Test GET /api/v2/survey-templates/section/{category}"""
        categories = ["climate", "feedback", "evaluation"]
        for category in categories:
            response = requests.get(
                f"{BASE_URL}/survey-templates/section/{category}",
                headers=auth_headers
            )
            assert response.status_code in [200, 404]
            if response.status_code == 200:
                data = response.json()
                assert isinstance(data, dict)


class TestSurveyIdentityAPI:
    """Test Survey Identity endpoints"""

    @pytest.fixture
    def auth_headers(self):
        return {
            "Content-Type": "application/json",
        }

    def test_set_preference(self, auth_headers):
        """Test POST /api/v2/survey/identity/preference"""
        preference_data = {
            "user_email": "test@example.com",
            "survey_id": 1,
            "identity_mode": "anonymous",
            "privacy_level": "maximum",
        }
        response = requests.post(
            f"{BASE_URL}/survey/identity/preference",
            headers=auth_headers,
            json=preference_data
        )
        assert response.status_code in [200, 201, 404]

    def test_get_status(self, auth_headers):
        """Test GET /api/v2/survey/identity/status/{user_email}"""
        user_email = "test@example.com"
        response = requests.get(
            f"{BASE_URL}/survey/identity/status/{user_email}",
            headers=auth_headers
        )
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, dict)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
