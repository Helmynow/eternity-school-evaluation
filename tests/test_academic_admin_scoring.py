"""
Unit tests for Academic vs Admin Weighted Scoring System.
"""

from unittest.mock import MagicMock, Mock

import numpy as np
import pytest

from backend.academic_admin_scoring import AcademicAdminScoring, StaffTypeScore
from backend.database import Assignment, Evaluation, Person


@pytest.fixture
def mock_db_session():
    """Create a mock database session"""
    return Mock()


@pytest.fixture
def sample_person_academic():
    """Create a sample academic staff person"""
    person = Mock(spec=Person)
    person.email = "teacher1@eternity.edu"
    person.role_title = "Mathematics Teacher"
    person.department = "Academics"
    person.active = True
    return person


@pytest.fixture
def sample_person_admin():
    """Create a sample admin staff person"""
    person = Mock(spec=Person)
    person.email = "admin1@eternity.edu"
    person.role_title = "Administrative Coordinator"
    person.department = "Administration"
    person.active = True
    return person


class TestStaffTypeDetection:
    """Test staff type detection"""

    def test_get_staff_type_academic_teacher(self, mock_db_session):
        """Test detecting academic staff by role title"""
        scorer = AcademicAdminScoring(mock_db_session)

        person = Mock(spec=Person)
        person.role_title = "Mathematics Teacher"
        person.department = None

        staff_type = scorer.get_staff_type(person)
        assert staff_type == "academic"

    def test_get_staff_type_admin_coordinator(self, mock_db_session):
        """Test detecting admin staff by role title"""
        scorer = AcademicAdminScoring(mock_db_session)

        person = Mock(spec=Person)
        person.role_title = "Administrative Coordinator"
        person.department = None

        staff_type = scorer.get_staff_type(person)
        assert staff_type == "admin"

    def test_get_staff_type_academic_department(self, mock_db_session):
        """Test detecting academic staff by department"""
        scorer = AcademicAdminScoring(mock_db_session)

        person = Mock(spec=Person)
        person.role_title = "Staff Member"
        person.department = "Academic Affairs"

        staff_type = scorer.get_staff_type(person)
        assert staff_type == "academic"

    def test_get_staff_type_admin_department(self, mock_db_session):
        """Test detecting admin staff by department"""
        scorer = AcademicAdminScoring(mock_db_session)

        person = Mock(spec=Person)
        person.role_title = "Staff Member"
        person.department = "Administration"

        staff_type = scorer.get_staff_type(person)
        assert staff_type == "admin"

    def test_get_staff_type_default(self, mock_db_session):
        """Test default to academic when unclear"""
        scorer = AcademicAdminScoring(mock_db_session)

        person = Mock(spec=Person)
        person.role_title = None
        person.department = None

        staff_type = scorer.get_staff_type(person)
        assert staff_type == "academic"  # Default


class TestWeightMatrix:
    """Test weight matrix retrieval"""

    def test_get_weight_matrix_academic(self, mock_db_session):
        """Test getting academic weight matrix"""
        scorer = AcademicAdminScoring(mock_db_session)

        matrix = scorer.get_weight_matrix("academic")

        assert isinstance(matrix, dict)
        assert "CEO" in matrix
        assert "QA" in matrix
        assert matrix["QA"] == 1.0  # Full weight for academics
        assert matrix["P&C"] == 0.8

    def test_get_weight_matrix_admin(self, mock_db_session):
        """Test getting admin weight matrix"""
        scorer = AcademicAdminScoring(mock_db_session)

        matrix = scorer.get_weight_matrix("admin")

        assert isinstance(matrix, dict)
        assert "CEO" in matrix
        assert "P&C" in matrix
        assert matrix["P&C"] == 1.0  # Full weight for admin
        assert matrix["QA"] == 0.7  # Lower weight for admin

    def test_get_weight_matrix_default(self, mock_db_session):
        """Test default to academic matrix"""
        scorer = AcademicAdminScoring(mock_db_session)

        matrix = scorer.get_weight_matrix("unknown")

        assert isinstance(matrix, dict)
        assert "QA" in matrix


class TestWeightedScoreCalculation:
    """Test weighted score calculation"""

    def test_calculate_weighted_score_academic(self, mock_db_session, sample_person_academic):
        """Test calculating weighted score for academic staff"""
        scorer = AcademicAdminScoring(mock_db_session)

        # Mock person query
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_person_academic

        # Mock evaluations query
        eval1 = Mock(spec=Evaluation)
        eval1.rating = 4.0
        eval1.assignment_id = 1

        eval2 = Mock(spec=Evaluation)
        eval2.rating = 4.5
        eval2.assignment_id = 2

        assign1 = Mock(spec=Assignment)
        assign1.rater_context = "QA"
        assign1.weight = None

        assign2 = Mock(spec=Assignment)
        assign2.rater_context = "peer_review"
        assign2.weight = None

        # Mock query chain
        query_mock = MagicMock()
        query_mock.join.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.all.return_value = [(eval1, assign1), (eval2, assign2)]

        mock_db_session.query.return_value = query_mock

        score = scorer.calculate_weighted_score(cycle_id=1, target_email="teacher1@eternity.edu")

        assert isinstance(score, StaffTypeScore)
        assert score.staff_type == "academic"
        assert score.total_evaluations == 2
        assert score.raw_average > 0
        assert score.weighted_average > 0

    def test_calculate_weighted_score_no_evaluations(self, mock_db_session, sample_person_academic):
        """Test calculating score when no evaluations exist"""
        scorer = AcademicAdminScoring(mock_db_session)

        # Mock person query
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_person_academic

        # Mock empty evaluations
        query_mock = MagicMock()
        query_mock.join.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.all.return_value = []

        mock_db_session.query.return_value = query_mock

        score = scorer.calculate_weighted_score(cycle_id=1, target_email="teacher1@eternity.edu")

        assert score.total_evaluations == 0
        assert score.raw_average == 0.0
        assert score.weighted_average == 0.0


class TestBatchScoring:
    """Test batch score calculation"""

    def test_calculate_batch_scores_filter_by_type(self, mock_db_session):
        """Test filtering batch scores by staff type"""
        scorer = AcademicAdminScoring(mock_db_session)

        # Mock people query
        academic_person = Mock(spec=Person)
        academic_person.email = "teacher1@eternity.edu"
        academic_person.role_title = "Teacher"
        academic_person.active = True

        admin_person = Mock(spec=Person)
        admin_person.email = "admin1@eternity.edu"
        admin_person.role_title = "Coordinator"
        admin_person.active = True

        mock_db_session.query.return_value.filter.return_value.all.return_value = [academic_person, admin_person]

        # Mock calculate_weighted_score to return scores
        def mock_calculate(cycle_id, target_email, staff_type=None):
            score = Mock(spec=StaffTypeScore)
            score.staff_type = "academic" if "teacher" in target_email else "admin"
            score.target_email = target_email
            score.total_evaluations = 3
            score.raw_average = 4.0
            score.weighted_average = 4.2
            score.context_breakdown = {}
            score.final_score = 4.2
            score.score_components = {}
            return score

        scorer.calculate_weighted_score = mock_calculate

        scores = scorer.calculate_batch_scores(cycle_id=1, staff_type="academic")

        # Should only return academic scores
        assert len(scores) == 1
        assert scores[0].staff_type == "academic"


class TestComparison:
    """Test academic vs admin comparison"""

    def test_compare_academic_vs_admin(self, mock_db_session):
        """Test comparing academic and admin scores"""
        scorer = AcademicAdminScoring(mock_db_session)

        # Mock batch scoring
        def mock_batch(cycle_id, staff_type=None, target_emails=None):
            if staff_type == "academic":
                score = Mock(spec=StaffTypeScore)
                score.weighted_average = 4.2
                score.raw_average = 4.0
                return [score]
            else:
                score = Mock(spec=StaffTypeScore)
                score.weighted_average = 3.8
                score.raw_average = 3.6
                return [score]

        scorer.calculate_batch_scores = mock_batch

        comparison = scorer.compare_academic_vs_admin(cycle_id=1)

        assert comparison.cycle_id == 1
        assert "academic_stats" in comparison.__dict__
        assert "admin_stats" in comparison.__dict__
        assert "differences" in comparison.__dict__
        assert "recommendations" in comparison.__dict__


class TestValidation:
    """Test evaluation validation"""

    def test_validate_evaluations(self, mock_db_session):
        """Test validating evaluations for a staff type"""
        scorer = AcademicAdminScoring(mock_db_session)

        # Mock people query
        person = Mock(spec=Person)
        person.email = "teacher1@eternity.edu"
        person.role_title = "Teacher"
        person.active = True

        mock_db_session.query.return_value.filter.return_value.all.return_value = [person]

        # Mock evaluations query
        eval_obj = Mock(spec=Evaluation)
        eval_obj.rating = 4.0
        eval_obj.assignment_id = 1

        assignment = Mock(spec=Assignment)
        assignment.rater_context = "QA"

        query_mock = MagicMock()
        query_mock.join.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.all.return_value = [(eval_obj, assignment)]

        # Override query for evaluations
        def query_side_effect(model):
            if model == Person:
                return MagicMock()
            else:
                return query_mock

        mock_db_session.query.side_effect = query_side_effect

        validation = scorer.validate_evaluations(cycle_id=1, staff_type="academic")

        assert validation["staff_type"] == "academic"
        assert "is_valid" in validation
        assert "errors" in validation
        assert "warnings" in validation


class TestScoreDistribution:
    """Test score distribution calculation"""

    def test_get_score_distribution(self, mock_db_session):
        """Test getting score distribution"""
        scorer = AcademicAdminScoring(mock_db_session)

        # Mock batch scoring
        def mock_batch(cycle_id, staff_type=None, target_emails=None):
            scores = []
            for i in range(5):
                score = Mock(spec=StaffTypeScore)
                score.weighted_average = 3.0 + (i * 0.5)
                score.raw_average = 3.0 + (i * 0.5)
                scores.append(score)
            return scores

        scorer.calculate_batch_scores = mock_batch

        distribution = scorer.get_score_distribution(cycle_id=1, staff_type="academic")

        assert distribution["staff_type"] == "academic"
        assert distribution["count"] == 5
        assert "distribution" in distribution
        assert "mean" in distribution
        assert "median" in distribution
        assert "std" in distribution
