"""
Tests for EOM nomination validation.
"""

from unittest.mock import MagicMock, Mock

import pytest

from backend.database import Attendance, Cycle, EOMCycle, EOMNominee, EOMWinner, Person
from backend.eom_validation import EOMNominationValidator, ValidationResult


@pytest.fixture
def mock_db_session():
    """Create a mock database session"""
    session = Mock()
    return session


@pytest.fixture
def sample_eom_cycle():
    """Create sample EOM cycle"""
    cycle = Mock(spec=EOMCycle)
    cycle.id = 1
    cycle.cycle_id = 1
    cycle.month = 3
    cycle.year = 2024
    cycle.status = "active"
    return cycle


@pytest.fixture
def sample_person():
    """Create sample person"""
    person = Mock(spec=Person)
    person.email = "test@example.com"
    person.full_name = "Test Person"
    person.role_title = "Teacher"
    person.active = True
    return person


def test_validate_nomination_rotation_rules(mock_db_session, sample_eom_cycle):
    """Test rotation rules validation"""
    # Mock queries
    eom_cycle_query = MagicMock()
    eom_cycle_query.filter.return_value = eom_cycle_query
    eom_cycle_query.first.return_value = sample_eom_cycle

    cycle_query = MagicMock()
    cycle_query.filter.return_value = cycle_query
    cycle = Mock(spec=Cycle)
    cycle.code = "2024-Q1"
    cycle_query.first.return_value = cycle

    winner_query = MagicMock()
    winner_query.filter.return_value = winner_query
    winner_query.first.return_value = None  # No existing winner

    person_query = MagicMock()
    person_query.filter.return_value = person_query
    person = Mock(spec=Person)
    person.email = "nominee@example.com"
    person.active = True
    person_query.first.return_value = person

    nominee_query = MagicMock()
    nominee_query.filter.return_value = nominee_query
    nominee_query.all.return_value = []

    attendance_query = MagicMock()
    attendance_query.filter.return_value = attendance_query
    attendance_query.all.return_value = []

    mock_db_session.query.side_effect = lambda model: {
        EOMCycle: eom_cycle_query,
        Cycle: cycle_query,
        EOMWinner: winner_query,
        Person: person_query,
        EOMNominee: nominee_query,
        Attendance: attendance_query,
    }.get(model, person_query)

    validator = EOMNominationValidator(mock_db_session)
    result = validator.validate_nomination(
        nominee_email="nominee@example.com", eom_cycle_id=1, nominated_by="nominator@example.com", category="academic"
    )

    assert isinstance(result, ValidationResult)
    assert "rotation_check" in result.details


def test_check_duplicate_nominations(mock_db_session):
    """Test duplicate nomination check"""
    validator = EOMNominationValidator(mock_db_session)

    # Mock existing nomination
    nominee_query = MagicMock()
    nominee_query.filter.return_value = nominee_query
    existing_nominee = Mock(spec=EOMNominee)
    nominee_query.all.return_value = [existing_nominee]

    mock_db_session.query.return_value = nominee_query

    result = validator._check_duplicate_nominations("nominee@example.com", 1, "academic")

    assert not result["is_valid"]
    assert len(result["errors"]) > 0


def test_check_leader_nomination_limit(mock_db_session):
    """Test leader nomination limit"""
    validator = EOMNominationValidator(mock_db_session)

    # Mock leader person
    person_query = MagicMock()
    person_query.filter.return_value = person_query
    leader = Mock(spec=Person)
    leader.email = "leader@example.com"
    leader.role_title = "School Manager"
    leader.active = True
    person_query.first.return_value = leader

    # Mock existing nomination by leader
    nominee_query = MagicMock()
    nominee_query.filter.return_value = nominee_query
    existing = Mock(spec=EOMNominee)
    nominee_query.all.return_value = [existing]

    mock_db_session.query.side_effect = lambda model: (person_query if model == Person else nominee_query)

    result = validator._check_leader_nomination_limit("leader@example.com", 1, "academic")

    assert not result["is_valid"]
    assert result["is_leader"] is True


def test_validate_attendance(mock_db_session):
    """Test attendance validation"""
    validator = EOMNominationValidator(mock_db_session)

    # Mock attendance records
    attendance_query = MagicMock()
    attendance_query.filter.return_value = attendance_query

    attendance_records = []
    for i in range(20):
        record = Mock(spec=Attendance)
        record.status = "present" if i < 18 else "absent"
        attendance_records.append(record)

    attendance_query.all.return_value = attendance_records

    mock_db_session.query.return_value = attendance_query

    result = validator._validate_attendance("nominee@example.com", 3, 2024, None)

    assert "attendance_rate" in result
    assert result["attendance_rate"] == 0.9  # 18/20


def test_get_validation_summary(mock_db_session):
    """Test validation summary generation"""
    validator = EOMNominationValidator(mock_db_session)

    # Mock nominations
    nominee_query = MagicMock()
    nominee_query.filter.return_value = nominee_query

    nominations = []
    for i in range(5):
        nom = Mock(spec=EOMNominee)
        nom.nominee_email = f"nominee{i}@example.com"
        nom.nominated_by = f"nominator{i}@example.com"
        nom.category = "academic" if i % 2 == 0 else "admin"
        nominations.append(nom)

    nominee_query.all.return_value = nominations

    # Mock all other queries to return empty/None
    mock_db_session.query.return_value = nominee_query

    summary = validator.get_validation_summary(1)

    assert "total_nominations" in summary
    assert "valid_nominations" in summary
    assert "by_category" in summary
    assert "by_nominator" in summary
