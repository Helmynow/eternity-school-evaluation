"""
Unit tests for WeightMatrixCalculator class.
"""

import numpy as np
import pytest

from backend.weight_matrix_calculator import WeightMatrixCalculator


@pytest.fixture
def sample_weight_matrix_config():
    """Create a sample weight matrix configuration"""
    return {
        "academic": {"CEO": 1.0, "P&C": 0.8, "QA": 0.9, "peer_review": 0.7},
        "admin": {"CEO": 1.0, "P&C": 0.9, "QA": 0.7, "peer_review": 0.8},
        "other": {"CEO": 0.8, "P&C": 0.7, "QA": 0.8, "peer_review": 0.7},
    }


class TestWeightMatrixCalculator:
    """Test suite for WeightMatrixCalculator"""

    def test_init_with_config(self, sample_weight_matrix_config):
        """Test initialization with custom config"""
        calculator = WeightMatrixCalculator(sample_weight_matrix_config)

        assert calculator.config == sample_weight_matrix_config

    def test_init_without_config(self):
        """Test initialization without config (uses defaults)"""
        calculator = WeightMatrixCalculator()

        assert calculator.config is not None
        assert "academic" in calculator.config
        assert "admin" in calculator.config

    def test_calculate_weighted_evaluation_single_score(self, sample_weight_matrix_config):
        """Test weighted evaluation with single score"""
        calculator = WeightMatrixCalculator(sample_weight_matrix_config)

        scores = {"overall": 4.5}
        result = calculator.calculate_weighted_evaluation(target_group="academic", rater_context="CEO", scores=scores)

        # CEO weight is 1.0, so result should be 4.5
        assert result == 4.5

    def test_calculate_weighted_evaluation_multiple_scores(self, sample_weight_matrix_config):
        """Test weighted evaluation with multiple domain scores"""
        calculator = WeightMatrixCalculator(sample_weight_matrix_config)

        scores = {"teaching": 4.0, "collaboration": 3.5, "leadership": 4.2}

        # Since we have a single weight for the context, it will be distributed
        result = calculator.calculate_weighted_evaluation(target_group="academic", rater_context="CEO", scores=scores)

        # Should calculate weighted average
        assert isinstance(result, float)
        assert 3.5 <= result <= 4.2

    def test_calculate_weighted_evaluation_with_pc_context(self, sample_weight_matrix_config):
        """Test weighted evaluation with P&C context (weight 0.8)"""
        calculator = WeightMatrixCalculator(sample_weight_matrix_config)

        scores = {"overall": 4.0}
        result = calculator.calculate_weighted_evaluation(target_group="academic", rater_context="P&C", scores=scores)

        # P&C weight is 0.8, so result should be 4.0 * 0.8 = 3.2
        # But since it's a single score, it applies the weight directly
        assert result == 3.2

    def test_calculate_weighted_evaluation_unknown_group(self, sample_weight_matrix_config):
        """Test weighted evaluation with unknown target group"""
        calculator = WeightMatrixCalculator(sample_weight_matrix_config)

        scores = {"overall": 4.0}
        result = calculator.calculate_weighted_evaluation(target_group="unknown_group", rater_context="CEO", scores=scores)

        # Should fallback to 'other' or use simple average
        assert isinstance(result, float)
        assert result >= 0

    def test_apply_weights_single_weight(self, sample_weight_matrix_config):
        """Test apply_weights with single weight value"""
        calculator = WeightMatrixCalculator(sample_weight_matrix_config)

        scores = {"teaching": 4.0, "collaboration": 3.5}
        weights = 0.8  # Single weight value

        result = calculator.apply_weights(scores, weights)

        # Should apply weight to average
        expected = (4.0 + 3.5) / 2.0 * 0.8
        assert abs(result - expected) < 0.001

    def test_apply_weights_dict_weights(self, sample_weight_matrix_config):
        """Test apply_weights with dictionary of weights"""
        calculator = WeightMatrixCalculator(sample_weight_matrix_config)

        scores = {"teaching": 4.0, "collaboration": 3.5, "leadership": 4.2}

        weights = {"teaching": 0.4, "collaboration": 0.3, "leadership": 0.3}

        result = calculator.apply_weights(scores, weights)

        expected = (4.0 * 0.4 + 3.5 * 0.3 + 4.2 * 0.3) / 1.0
        assert abs(result - expected) < 0.001

    def test_apply_weights_missing_weights(self, sample_weight_matrix_config):
        """Test apply_weights when some scores don't have weights"""
        calculator = WeightMatrixCalculator(sample_weight_matrix_config)

        scores = {"teaching": 4.0, "collaboration": 3.5, "leadership": 4.2}

        weights = {
            "teaching": 0.5,
            "collaboration": 0.3,
            # Missing 'leadership'
        }

        result = calculator.apply_weights(scores, weights)

        # Should use default weight of 1.0 for 'leadership'
        expected = (4.0 * 0.5 + 3.5 * 0.3 + 4.2 * 1.0) / (0.5 + 0.3 + 1.0)
        assert abs(result - expected) < 0.001

    def test_apply_weights_empty_scores(self, sample_weight_matrix_config):
        """Test apply_weights with empty scores"""
        calculator = WeightMatrixCalculator(sample_weight_matrix_config)

        result = calculator.apply_weights({}, {})

        assert result == 0.0

    def test_apply_weights_zero_total_weight(self, sample_weight_matrix_config):
        """Test apply_weights when total weight is zero"""
        calculator = WeightMatrixCalculator(sample_weight_matrix_config)

        scores = {"teaching": 4.0}
        weights = {"teaching": 0.0}

        result = calculator.apply_weights(scores, weights)

        # Should return simple average when total weight is 0
        assert result == 4.0

    def test_calculate_weighted_evaluation_batch(self, sample_weight_matrix_config):
        """Test batch calculation of weighted evaluations"""
        calculator = WeightMatrixCalculator(sample_weight_matrix_config)

        evaluations = [
            {"target_group": "academic", "rater_context": "CEO", "scores": {"overall": 4.5}},
            {"target_group": "admin", "rater_context": "P&C", "scores": {"overall": 3.8}},
            {"target_group": "academic", "rater_context": "QA", "scores": {"overall": 4.2}},
        ]

        results = calculator.calculate_weighted_evaluation_batch(evaluations)

        assert len(results) == 3
        assert all("weighted_score" in r for r in results)
        assert all("weights_applied" in r for r in results)

        # Check first result
        assert results[0]["target_group"] == "academic"
        assert results[0]["rater_context"] == "CEO"
        assert results[0]["weighted_score"] == 4.5  # CEO weight is 1.0

    def test_get_weight(self, sample_weight_matrix_config):
        """Test getting weight for specific group and context"""
        calculator = WeightMatrixCalculator(sample_weight_matrix_config)

        weight = calculator.get_weight("academic", "CEO")
        assert weight == 1.0

        weight = calculator.get_weight("academic", "P&C")
        assert weight == 0.8

        weight = calculator.get_weight("unknown", "CEO")
        # Should fallback to 'other' or default to 1.0
        assert weight >= 0

    def test_update_config(self, sample_weight_matrix_config):
        """Test updating weight matrix configuration"""
        calculator = WeightMatrixCalculator(sample_weight_matrix_config)

        # Update existing weight
        calculator.update_config("academic", "CEO", 1.2)
        weight = calculator.get_weight("academic", "CEO")
        assert weight == 1.2

        # Add new weight
        calculator.update_config("new_group", "new_context", 0.9)
        weight = calculator.get_weight("new_group", "new_context")
        assert weight == 0.9

    def test_get_config(self, sample_weight_matrix_config):
        """Test getting configuration copy"""
        calculator = WeightMatrixCalculator(sample_weight_matrix_config)

        config = calculator.get_config()

        assert config == sample_weight_matrix_config
        # Should be a copy, not the same object
        assert config is not calculator.config

    def test_case_insensitive_target_group(self, sample_weight_matrix_config):
        """Test that target group is case-insensitive"""
        calculator = WeightMatrixCalculator(sample_weight_matrix_config)

        scores = {"overall": 4.0}
        result1 = calculator.calculate_weighted_evaluation("ACADEMIC", "CEO", scores)
        result2 = calculator.calculate_weighted_evaluation("academic", "CEO", scores)
        result3 = calculator.calculate_weighted_evaluation("Academic", "CEO", scores)

        assert result1 == result2 == result3

    def test_multiple_domain_scores_with_single_context_weight(self, sample_weight_matrix_config):
        """Test handling multiple domain scores when context has single weight"""
        calculator = WeightMatrixCalculator(sample_weight_matrix_config)

        scores = {"domain1": 4.0, "domain2": 3.5, "domain3": 4.2}

        result = calculator.calculate_weighted_evaluation(target_group="academic", rater_context="CEO", scores=scores)

        # Should distribute the CEO weight (1.0) equally across domains
        # Or apply it uniformly
        assert isinstance(result, float)
        assert 3.5 <= result <= 4.2
