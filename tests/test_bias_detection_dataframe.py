"""
Unit tests for DataFrame-based bias detection methods.
Tests the detect_evaluation_bias method and its helper functions.
"""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, Mock

import numpy as np
import pandas as pd
import pytest

from backend.bias_detection import BiasDetector


@pytest.fixture
def mock_db_session():
    """Create a mock database session"""
    return Mock()


@pytest.fixture
def sample_evaluation_dataframe():
    """Create a sample evaluation DataFrame"""
    np.random.seed(42)
    n = 30

    data = {
        "rater_id": [f"rater{i % 5}@example.com" for i in range(n)],
        "target_id": [f"target{i % 10}@example.com" for i in range(n)],
        "score": np.random.normal(3.5, 0.8, n).clip(1.0, 5.0),
        "rater_context": ["peer_review", "manager_review"] * (n // 2),
        "target_group": ["academic", "admin"] * (n // 2),
        "department": ["national", "international", "whole_school"] * (n // 3),
        "segment": ["national", "international", "whole_school"] * (n // 3),
        "submitted_at": [datetime.now() - timedelta(days=i) for i in range(n)],
    }

    return pd.DataFrame(data)


class TestDetectEvaluationBias:
    """Test suite for detect_evaluation_bias method"""

    def test_detect_evaluation_bias_basic(self, mock_db_session, sample_evaluation_dataframe):
        """Test basic bias detection with valid DataFrame"""
        detector = BiasDetector(mock_db_session)

        result = detector.detect_evaluation_bias(sample_evaluation_dataframe)

        assert result["status"] == "analyzed"
        assert "total_evaluations" in result
        assert result["total_evaluations"] == len(sample_evaluation_dataframe)
        assert "similarity_bias" in result
        assert "recency_bias" in result
        assert "department_bias" in result
        assert "rater_reliability" in result

    def test_detect_evaluation_bias_empty_dataframe(self, mock_db_session):
        """Test with empty DataFrame"""
        detector = BiasDetector(mock_db_session)

        df = pd.DataFrame()
        result = detector.detect_evaluation_bias(df)

        assert result["status"] == "no_data"
        assert "message" in result

    def test_detect_evaluation_bias_missing_columns(self, mock_db_session):
        """Test with missing required columns"""
        detector = BiasDetector(mock_db_session)

        df = pd.DataFrame({"rater_id": ["rater1@example.com"]})
        result = detector.detect_evaluation_bias(df)

        assert result["status"] == "invalid_data"
        assert "missing_columns" in result or "message" in result

    def test_detect_evaluation_bias_column_aliases(self, mock_db_session):
        """Test that column aliases work (rater_email -> rater_id, etc.)"""
        detector = BiasDetector(mock_db_session)

        df = pd.DataFrame(
            {
                "rater_email": ["rater1@example.com", "rater2@example.com"],
                "target_email": ["target1@example.com", "target1@example.com"],
                "rating": [4.0, 3.5],
                "rater_context": ["peer_review", "manager_review"],
                "target_group": ["academic", "academic"],
            }
        )

        result = detector.detect_evaluation_bias(df)

        assert result["status"] == "analyzed"
        assert result["total_evaluations"] == 2

    def test_detect_evaluation_bias_with_halo_effect(self, mock_db_session):
        """Test detection of halo effect in similarity bias"""
        detector = BiasDetector(mock_db_session)

        # Create data with clear halo effect (rater0 gives very similar scores)
        np.random.seed(42)
        data = {
            "rater_id": ["rater0@example.com"] * 5 + ["rater1@example.com"] * 5,
            "target_id": [f"target{i}@example.com" for i in range(10)],
            # Very low variance for rater0 + normal variance for rater1
            "score": (np.random.normal(4.0, 0.05, 5).tolist() + np.random.normal(3.5, 1.0, 5).tolist()),
            "rater_context": ["peer_review"] * 10,
            "target_group": ["academic"] * 10,
        }

        df = pd.DataFrame(data)
        result = detector.detect_evaluation_bias(df)

        assert result["status"] == "analyzed"
        sim_bias = result["similarity_bias"]
        assert sim_bias["status"] == "analyzed"
        # Should detect at least one bias flag
        assert len(sim_bias["bias_flags"]) > 0

    def test_detect_evaluation_bias_with_recency_bias(self, mock_db_session):
        """Test detection of recency bias"""
        detector = BiasDetector(mock_db_session)

        # Create data with positive recency bias (later = higher)
        n = 20
        data = {
            "rater_id": [f"rater{i % 3}@example.com" for i in range(n)],
            "target_id": [f"target{i % 5}@example.com" for i in range(n)],
            "score": [2.0 + (i * 0.15) for i in range(n)],  # Increasing scores
            "rater_context": ["peer_review"] * n,
            "target_group": ["academic"] * n,
            "submitted_at": [datetime.now() - timedelta(days=n - i) for i in range(n)],  # Later = more recent
        }

        df = pd.DataFrame(data)
        result = detector.detect_evaluation_bias(df)

        assert result["status"] == "analyzed"
        rec_bias = result["recency_bias"]
        if rec_bias["status"] == "analyzed":
            assert rec_bias["correlation"] > 0.3  # Should detect positive correlation
            assert rec_bias["interpretation"] == "positive"

    def test_detect_evaluation_bias_with_department_bias(self, mock_db_session):
        """Test detection of department/segment bias"""
        detector = BiasDetector(mock_db_session)

        # Create data with clear department bias
        data = {
            "rater_id": [f"rater{i % 5}@example.com" for i in range(30)],
            "target_id": [f"target{i % 10}@example.com" for i in range(30)],
            "score": (
                [4.5] * 10 + [2.5] * 10 + [3.5] * 10  # National: high scores  # International: low scores
            ),  # Whole School: medium scores
            "rater_context": ["peer_review"] * 30,
            "target_group": ["academic"] * 30,
            "department": (["national"] * 10 + ["international"] * 10 + ["whole_school"] * 10),
            "segment": (["national"] * 10 + ["international"] * 10 + ["whole_school"] * 10),
        }

        df = pd.DataFrame(data)
        result = detector.detect_evaluation_bias(df)

        assert result["status"] == "analyzed"
        dept_bias = result["department_bias"]
        assert dept_bias["status"] == "analyzed"
        assert "departments" in dept_bias
        assert len(dept_bias["departments"]) == 3

        # Check that national has higher mean
        if "national" in dept_bias["departments"] and "international" in dept_bias["departments"]:
            assert dept_bias["departments"]["national"]["mean"] > dept_bias["departments"]["international"]["mean"]

        # Should have significant deviations
        assert len(dept_bias["significant_deviations"]) > 0


class TestDepartmentBiasDetection:
    """Test suite for department bias detection"""

    def test_detect_department_bias_no_department_column(self, mock_db_session):
        """Test when department column is missing"""
        detector = BiasDetector(mock_db_session)

        df = pd.DataFrame({"rater_id": ["rater1@example.com"], "target_id": ["target1@example.com"], "score": [4.0]})

        result = detector._detect_department_bias_from_df(df)

        assert result["status"] == "no_department_data"
        assert "message" in result

    def test_detect_department_bias_with_segment_column(self, mock_db_session):
        """Test using segment column instead of department"""
        detector = BiasDetector(mock_db_session)

        df = pd.DataFrame(
            {
                "rater_id": ["rater1@example.com", "rater2@example.com"],
                "target_id": ["target1@example.com", "target2@example.com"],
                "score": [4.0, 3.5],
                "segment": ["national", "international"],
            }
        )

        result = detector._detect_department_bias_from_df(df)

        assert result["status"] == "analyzed" or result["status"] == "insufficient_data"

    def test_detect_department_bias_statistical_test(self, mock_db_session):
        """Test statistical test for department differences"""
        detector = BiasDetector(mock_db_session)

        # Create data with significant differences
        np.random.seed(42)
        data = {
            "rater_id": [f"rater{i % 5}@example.com" for i in range(30)],
            "target_id": [f"target{i % 10}@example.com" for i in range(30)],
            "score": (
                np.random.normal(4.5, 0.5, 10).tolist()  # National: high
                + np.random.normal(2.5, 0.5, 10).tolist()  # International: low
                + np.random.normal(3.5, 0.5, 10).tolist()
            ),  # Whole School: medium
            "department": (["national"] * 10 + ["international"] * 10 + ["whole_school"] * 10),
        }

        df = pd.DataFrame(data)
        result = detector._detect_department_bias_from_df(df)

        assert result["status"] == "analyzed"
        if result.get("statistical_test"):
            assert "p_value" in result["statistical_test"]
            assert "significant" in result["statistical_test"]


class TestRaterReliability:
    """Test suite for rater reliability calculation"""

    def test_calculate_rater_reliability_high_agreement(self, mock_db_session):
        """Test reliability calculation with high agreement"""
        detector = BiasDetector(mock_db_session)

        # Create data where raters agree (low variance per target)
        data = {
            "rater_id": ["rater1@example.com", "rater2@example.com", "rater3@example.com"] * 5,
            "target_id": ["target1@example.com"] * 3
            + ["target2@example.com"] * 3
            + ["target3@example.com"] * 3
            + ["target4@example.com"] * 3
            + ["target5@example.com"] * 3,
            "score": (
                [4.0, 4.1, 3.9]  # High agreement for target1
                + [3.5, 3.6, 3.4]  # High agreement for target2
                + [4.2, 4.3, 4.1]  # High agreement for target3
                + [3.8, 3.9, 3.7]  # High agreement for target4
                + [4.1, 4.2, 4.0]
            ),  # High agreement for target5
        }

        df = pd.DataFrame(data)
        result = detector._calculate_rater_reliability_from_df(df)

        assert result["status"] == "analyzed"
        assert result["total_targets_analyzed"] == 5
        assert "overall_metrics" in result
        if result["overall_metrics"]["average_coefficient_of_variation"]:
            cv = result["overall_metrics"]["average_coefficient_of_variation"]
            assert cv < 0.15  # Should be low (high reliability)

    def test_calculate_rater_reliability_low_agreement(self, mock_db_session):
        """Test reliability calculation with low agreement"""
        detector = BiasDetector(mock_db_session)

        # Create data where raters disagree (high variance per target)
        data = {
            "rater_id": ["rater1@example.com", "rater2@example.com", "rater3@example.com"] * 3,
            "target_id": ["target1@example.com"] * 3 + ["target2@example.com"] * 3 + ["target3@example.com"] * 3,
            "score": (
                [5.0, 2.0, 3.0] + [4.0, 1.5, 3.5] + [4.5, 2.5, 3.2]  # Low agreement for target1  # Low agreement for target2
            ),  # Low agreement for target3
        }

        df = pd.DataFrame(data)
        result = detector._calculate_rater_reliability_from_df(df)

        assert result["status"] == "analyzed"
        if result["overall_metrics"]["average_coefficient_of_variation"]:
            cv = result["overall_metrics"]["average_coefficient_of_variation"]
            assert cv > 0.25  # Should be high (low reliability)

    def test_calculate_rater_reliability_missing_columns(self, mock_db_session):
        """Test reliability calculation with missing required columns"""
        detector = BiasDetector(mock_db_session)

        df = pd.DataFrame(
            {
                "score": [4.0, 3.5]
                # Missing rater_id and target_id
            }
        )

        result = detector._calculate_rater_reliability_from_df(df)

        assert result["status"] == "invalid_data"
        assert "message" in result


class TestLoadEvaluationsAsDataFrame:
    """Test suite for load_evaluations_as_dataframe method"""

    def test_load_evaluations_as_dataframe(self, mock_db_session):
        """Test loading evaluations from database as DataFrame"""
        detector = BiasDetector(mock_db_session)

        # Create mock evaluation data
        eval1 = Mock()
        eval1.rating = 4.0
        eval1.status = "submitted"
        eval1.id = 1
        eval1.submitted_at = datetime.now()
        eval1.assignment_id = 1

        assignment1 = Mock()
        assignment1.rater_email = "rater1@example.com"
        assignment1.target_email = "target1@example.com"
        assignment1.rater_context = "peer_review"
        assignment1.target_group = "academic"

        person1 = Mock()
        person1.segment.value = "national"
        person1.segment = Mock()
        person1.segment.value = "national"

        # Mock query
        query = MagicMock()
        query.join.return_value = query
        query.outerjoin.return_value = query
        query.filter.return_value = query
        query.all.return_value = [(eval1, assignment1, person1)]

        mock_db_session.query.return_value = query

        df = detector.load_evaluations_as_dataframe(cycle_id=1)

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 1
        assert "rater_id" in df.columns
        assert "target_id" in df.columns
        assert "score" in df.columns
        assert "department" in df.columns


class TestSimilarityBiasFromDataFrame:
    """Test suite for similarity bias detection from DataFrame"""

    def test_similarity_bias_empty_dataframe(self, mock_db_session):
        """Test similarity bias with empty DataFrame"""
        detector = BiasDetector(mock_db_session)

        df = pd.DataFrame()
        result = detector._detect_similarity_bias_from_df(df)

        assert result["status"] == "insufficient_data"

    def test_similarity_bias_no_rater_id(self, mock_db_session):
        """Test similarity bias when rater_id column is missing"""
        detector = BiasDetector(mock_db_session)

        df = pd.DataFrame({"target_id": ["target1@example.com"], "score": [4.0]})

        result = detector._detect_similarity_bias_from_df(df)

        # Should still work but with 0 raters checked
        assert result["status"] in ["analyzed", "insufficient_data"]


class TestRecencyBiasFromDataFrame:
    """Test suite for recency bias detection from DataFrame"""

    def test_recency_bias_no_timestamp(self, mock_db_session):
        """Test recency bias when timestamp column is missing"""
        detector = BiasDetector(mock_db_session)

        df = pd.DataFrame({"rater_id": ["rater1@example.com"], "target_id": ["target1@example.com"], "score": [4.0]})

        result = detector._detect_recency_bias_from_df(df)

        assert result["status"] == "insufficient_data"

    def test_recency_bias_with_timestamps(self, mock_db_session):
        """Test recency bias with valid timestamps"""
        detector = BiasDetector(mock_db_session)

        n = 20
        df = pd.DataFrame(
            {
                "rater_id": [f"rater{i % 3}@example.com" for i in range(n)],
                "target_id": [f"target{i % 5}@example.com" for i in range(n)],
                "score": [3.0 + (i * 0.1) for i in range(n)],  # Increasing
                "submitted_at": [datetime.now() - timedelta(days=n - i) for i in range(n)],
            }
        )

        result = detector._detect_recency_bias_from_df(df)

        assert result["status"] == "analyzed"
        assert "correlation" in result
        assert result["correlation"] > 0  # Should be positive
