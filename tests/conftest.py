"""
Pytest configuration and shared fixtures for all tests.
"""
import os
import sys
from pathlib import Path

# Add backend AND root directory to Python path
root_path = Path(__file__).parent.parent
backend_path = root_path / "backend"

# Add root first, then backend
if str(root_path) not in sys.path:
    sys.path.insert(0, str(root_path))
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

# Set environment variables for tests if not already set
os.environ.setdefault("SENTRY_DSN", "")
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("EMAIL_ENABLED", "false")

import pytest
from unittest.mock import Mock, MagicMock


@pytest.fixture(scope="session")
def test_database_url():
    """Get test database URL from environment or use default"""
    return os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/eternity_school_test"
    )


@pytest.fixture
def mock_db_session():
    """Create a mock database session"""
    session = Mock()
    return session


@pytest.fixture(autouse=True)
def disable_sentry():
    """Disable Sentry for all tests"""
    os.environ["SENTRY_DSN"] = ""
    yield
    # Cleanup if needed


@pytest.fixture(autouse=True)
def disable_email():
    """Disable email for all tests"""
    os.environ["EMAIL_ENABLED"] = "false"
    yield
    # Cleanup if needed
