"""
Edge case tests for weight calculation functions.
Tests boundary conditions, error handling, and special scenarios.
"""

from unittest.mock import MagicMock, Mock

import numpy as np
import pytest

from backend.bias_detection import BiasDetector
from backend.database import Assignment, Evaluation
from backend.weight_matrix_handler import EvaluationScore, ValidationResult, WeightMatrixHandler


@pytest.fixture
def mock_db_session():
    """Create a mock database session"""
    return Mock()


class TestWeightMatrixHandlerEdgeCases:
    """Test edge cases for WeightMatrixHandler"""

    def test_get_weight_unknown_combinations(self, mock_db_session):
        """Test weight retrieval for unknown target group/rater context combinations"""
        handler = WeightMatrixHandler(cycle_id=1, db_session=mock_db_session)

        # Unknown target group should fallback to 'other'
        weight = handler.get_weight("unknown_group", "CEO")
        assert weight == 1.0  # Should default to 1.0

        # Unknown rater context should default to 1.0
        weight = handler.get_weight("academic", "unknown_context")
        assert weight == 1.0

        # Both unknown
        weight = handler.get_weight("unknown_group", "unknown_context")
        assert weight == 1.0

    def test_get_weight_case_insensitive(self, mock_db_session):
        """Test that weight retrieval is case-insensitive for target groups"""
        handler = WeightMatrixHandler(cycle_id=1, db_session=mock_db_session)

        weight_lower = handler.get_weight("academic", "CEO")
        weight_upper = handler.get_weight("ACADEMIC", "CEO")
        weight_mixed = handler.get_weight("Academic", "CEO")

        assert weight_lower == weight_upper == weight_mixed

    def test_load_evaluations_empty(self, mock_db_session):
        """Test loading evaluations when none exist"""
        handler = WeightMatrixHandler(cycle_id=1, db_session=mock_db_session)

        eval_query = MagicMock()
        eval_query.join.return_value = eval_query
        eval_query.filter.return_value = eval_query
        eval_query.all.return_value = []  # Empty

        mock_db_session.query.return_value = eval_query

        scores = handler.load_evaluations()

        assert scores == []
        assert handler._evaluation_scores == []

    def test_load_evaluations_with_null_ratings(self, mock_db_session):
        """Test loading evaluations when some have null ratings"""
        handler = WeightMatrixHandler(cycle_id=1, db_session=mock_db_session)

        # Create evaluations with some null ratings
        eval1 = Mock(spec=Evaluation)
        eval1.rating = 4.0
        eval1.status = "submitted"
        eval1.assignment_id = 0

        eval2 = Mock(spec=Evaluation)
        eval2.rating = None  # Null rating
        eval2.status = "submitted"
        eval2.assignment_id = 1

        eval3 = Mock(spec=Evaluation)
        eval3.rating = 3.5
        eval3.status = "submitted"
        eval3.assignment_id = 2

        assignment0 = Mock(spec=Assignment)
        assignment0.target_email = "target1@example.com"
        assignment0.rater_email = "rater1@example.com"
        assignment0.target_group = "academic"
        assignment0.rater_context = "CEO"
        assignment0.weight = None
        assignment0.cycle_id = 1

        assignment1 = Mock(spec=Assignment)
        assignment1.target_email = "target2@example.com"
        assignment1.rater_email = "rater2@example.com"
        assignment1.target_group = "academic"
        assignment1.rater_context = "P&C"
        assignment1.weight = None
        assignment1.cycle_id = 1

        assignment2 = Mock(spec=Assignment)
        assignment2.target_email = "target3@example.com"
        assignment2.rater_email = "rater3@example.com"
        assignment2.target_group = "admin"
        assignment2.rater_context = "QA"
        assignment2.weight = None
        assignment2.cycle_id = 1

        eval_query = MagicMock()
        eval_query.join.return_value = eval_query
        eval_query.filter.return_value = eval_query
        eval_query.all.return_value = [eval1, eval2, eval3]

        # Mock the join query to return (eval, assignment) tuples
        join_query = MagicMock()
        join_query.join.return_value = join_query
        join_query.filter.return_value = join_query
        join_query.all.return_value = [
            (eval1, assignment0),
            (eval2, assignment1),  # This should be filtered out due to null rating
            (eval3, assignment2),
        ]

        mock_db_session.query.side_effect = lambda model: (join_query if model == Evaluation else eval_query)

        # WeightMatrixHandler.load_evaluations uses query(Evaluation, Assignment) (single join query)
        mock_db_session.query.side_effect = None
        mock_db_session.query.return_value = join_query

        scores = handler.load_evaluations()

        # Should only include evaluations with non-null ratings
        assert len(scores) == 2
        assert all(s.raw_score is not None for s in scores)

    def test_calculate_final_scores_single_target(self, mock_db_session):
        """Test final score calculation for a single target"""
        handler = WeightMatrixHandler(cycle_id=1, db_session=mock_db_session)

        # Create evaluation scores manually
        handler._evaluation_scores = [
            EvaluationScore(
                target_email="target1@example.com",
                rater_email="rater1@example.com",
                target_group="academic",
                rater_context="CEO",
                raw_score=4.0,
                weight=1.0,
                weighted_score=4.0,
            ),
            EvaluationScore(
                target_email="target1@example.com",
                rater_email="rater2@example.com",
                target_group="academic",
                rater_context="P&C",
                raw_score=3.5,
                weight=0.8,
                weighted_score=2.8,
            ),
        ]

        result = handler.calculate_final_scores(target_email="target1@example.com")

        assert "target1@example.com" in result
        target_data = result["target1@example.com"]
        assert target_data["evaluation_count"] == 2
        assert target_data["weighted_average"] == (4.0 + 2.8) / (1.0 + 0.8)
        assert target_data["simple_average"] == (4.0 + 3.5) / 2.0

    def test_calculate_final_scores_empty(self, mock_db_session):
        """Test final score calculation with no scores"""
        handler = WeightMatrixHandler(cycle_id=1, db_session=mock_db_session)
        handler._evaluation_scores = []

        result = handler.calculate_final_scores()

        assert result == {}

    def test_validate_evaluations_below_minimum(self, mock_db_session):
        """Test validation when evaluations are below minimum"""
        handler = WeightMatrixHandler(cycle_id=1, db_session=mock_db_session)

        # Create scores with only 1 evaluation for academic (min is 3)
        handler._evaluation_scores = [
            EvaluationScore(
                target_email="target1@example.com",
                rater_email="rater1@example.com",
                target_group="academic",
                rater_context="CEO",
                raw_score=4.0,
                weight=1.0,
                weighted_score=4.0,
            )
        ]

        result = handler.validate_evaluations()

        assert isinstance(result, ValidationResult)
        assert result.is_valid == False
        assert len(result.errors) > 0
        assert any("minimum required" in error.lower() for error in result.errors)

    def test_validate_evaluations_above_maximum(self, mock_db_session):
        """Test validation when evaluations exceed maximum"""
        handler = WeightMatrixHandler(cycle_id=1, db_session=mock_db_session)

        # Create scores with 15 evaluations for academic (max is 10)
        handler._evaluation_scores = [
            EvaluationScore(
                target_email="target1@example.com",
                rater_email=f"rater{i}@example.com",
                target_group="academic",
                rater_context="CEO",
                raw_score=4.0,
                weight=1.0,
                weighted_score=4.0,
            )
            for i in range(15)
        ]

        result = handler.validate_evaluations()

        assert isinstance(result, ValidationResult)
        assert len(result.warnings) > 0
        assert any("maximum recommended" in warning.lower() for warning in result.warnings)

    def test_validate_evaluations_missing_required_contexts(self, mock_db_session):
        """Test validation when required contexts are missing"""
        handler = WeightMatrixHandler(cycle_id=1, db_session=mock_db_session)

        # Create scores for academic target but only peer_review (missing CEO/P&C/QA)
        handler._evaluation_scores = [
            EvaluationScore(
                target_email="target1@example.com",
                rater_email="rater1@example.com",
                target_group="academic",
                rater_context="peer_review",
                raw_score=4.0,
                weight=0.7,
                weighted_score=2.8,
            ),
            EvaluationScore(
                target_email="target1@example.com",
                rater_email="rater2@example.com",
                target_group="academic",
                rater_context="peer_review",
                raw_score=3.5,
                weight=0.7,
                weighted_score=2.45,
            ),
            EvaluationScore(
                target_email="target1@example.com",
                rater_email="rater3@example.com",
                target_group="academic",
                rater_context="peer_review",
                raw_score=4.2,
                weight=0.7,
                weighted_score=2.94,
            ),
        ]

        result = handler.validate_evaluations()

        assert isinstance(result, ValidationResult)
        assert len(result.warnings) > 0
        assert any(
            "ceo" in warning.lower() or "p&c" in warning.lower() or "qa" in warning.lower() for warning in result.warnings
        )

    def test_get_evaluation_summary_empty(self, mock_db_session):
        """Test evaluation summary with no evaluations"""
        handler = WeightMatrixHandler(cycle_id=1, db_session=mock_db_session)
        handler._evaluation_scores = []

        summary = handler.get_evaluation_summary()

        assert summary["total_evaluations"] == 0
        assert summary["total_targets"] == 0
        assert summary["total_raters"] == 0
        assert summary["average_raw_score"] == 0
        assert summary["average_weighted_score"] == 0

    def test_update_weight_matrix_new_group(self, mock_db_session):
        """Test updating weight matrix with a new target group"""
        handler = WeightMatrixHandler(cycle_id=1, db_session=mock_db_session)

        # Update with new group
        handler.update_weight_matrix("new_group", "CEO", 1.2)

        weight = handler.get_weight("new_group", "CEO")
        assert weight == 1.2

    def test_export_scores_to_dict(self, mock_db_session):
        """Test exporting scores to dictionary format"""
        handler = WeightMatrixHandler(cycle_id=1, db_session=mock_db_session)

        # Create some evaluation scores
        handler._evaluation_scores = [
            EvaluationScore(
                target_email="target1@example.com",
                rater_email="rater1@example.com",
                target_group="academic",
                rater_context="CEO",
                raw_score=4.0,
                weight=1.0,
                weighted_score=4.0,
            )
        ]

        result = handler.export_scores_to_dict()

        assert "cycle_id" in result
        assert "scores" in result
        assert "validation" in result
        assert "summary" in result
        assert "weight_matrix" in result
        assert result["cycle_id"] == 1


class TestBiasDetectorWeightCalculationEdgeCases:
    """Test edge cases for weighted score calculation in BiasDetector"""

    def test_calculate_weighted_score_single_score(self, mock_db_session):
        """Test weighted score with single score"""
        detector = BiasDetector(mock_db_session)

        scores = {"peer_review": 4.5}
        weights = {"peer_review": 1.0}

        result = detector.calculate_weighted_score(scores, weights)

        assert result == 4.5

    def test_calculate_weighted_score_all_same_weights(self, mock_db_session):
        """Test weighted score when all weights are equal"""
        detector = BiasDetector(mock_db_session)

        scores = {"peer_review": 4.0, "manager_review": 3.5, "direct_report_review": 4.5}

        weights = {"peer_review": 0.33, "manager_review": 0.33, "direct_report_review": 0.34}

        result = detector.calculate_weighted_score(scores, weights)

        # Should be close to simple average
        simple_avg = (4.0 + 3.5 + 4.5) / 3.0
        assert abs(result - simple_avg) < 0.1

    def test_calculate_weighted_score_extreme_weights(self, mock_db_session):
        """Test weighted score with extreme weight values"""
        detector = BiasDetector(mock_db_session)

        scores = {"peer_review": 4.0, "manager_review": 2.0}

        weights = {"peer_review": 0.99, "manager_review": 0.01}  # Very high weight  # Very low weight

        result = detector.calculate_weighted_score(scores, weights)

        # Should be very close to peer_review score
        assert abs(result - 4.0) < 0.1

    def test_calculate_weighted_score_negative_scores(self, mock_db_session):
        """Test weighted score with negative scores (edge case)"""
        detector = BiasDetector(mock_db_session)

        scores = {"peer_review": -1.0, "manager_review": 3.0}  # Negative score (shouldn't happen in practice)

        weights = {"peer_review": 0.5, "manager_review": 0.5}

        result = detector.calculate_weighted_score(scores, weights)

        # Should still calculate correctly
        expected = (-1.0 * 0.5 + 3.0 * 0.5) / 1.0
        assert abs(result - expected) < 0.001

    def test_calculate_weighted_score_very_large_values(self, mock_db_session):
        """Test weighted score with very large score values"""
        detector = BiasDetector(mock_db_session)

        scores = {"peer_review": 1000.0, "manager_review": 2000.0}

        weights = {"peer_review": 0.4, "manager_review": 0.6}

        result = detector.calculate_weighted_score(scores, weights)

        expected = (1000.0 * 0.4 + 2000.0 * 0.6) / 1.0
        assert abs(result - expected) < 0.001

    def test_calculate_weighted_score_many_contexts(self, mock_db_session):
        """Test weighted score with many different contexts"""
        detector = BiasDetector(mock_db_session)

        scores = {f"context_{i}": 3.0 + i * 0.1 for i in range(20)}
        weights = {f"context_{i}": 1.0 / 20.0 for i in range(20)}

        result = detector.calculate_weighted_score(scores, weights)

        # Should be close to average
        expected = sum(scores.values()) / len(scores)
        assert abs(result - expected) < 0.001
