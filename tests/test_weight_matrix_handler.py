"""
Tests for WeightMatrixHandler class.
"""
import pytest
import numpy as np
from unittest.mock import Mock, MagicMock
from backend.weight_matrix_handler import WeightMatrixHandler, ValidationResult
from backend.database import Evaluation, Assignment


@pytest.fixture
def mock_db_session():
    """Create a mock database session"""
    session = Mock()
    return session


@pytest.fixture
def sample_evaluations():
    """Create sample evaluation data"""
    evaluations = []
    for i in range(10):
        eval = Mock(spec=Evaluation)
        eval.id = i
        eval.rating = 3.0 + np.random.normal(0, 0.5)
        eval.rating = max(1.0, min(5.0, eval.rating))
        eval.status = 'submitted'
        eval.assignment_id = i
        evaluations.append(eval)
    return evaluations


@pytest.fixture
def sample_assignments():
    """Create sample assignment data"""
    assignments = []
    target_groups = ['academic', 'admin', 'academic']
    contexts = ['CEO', 'P&C', 'QA']
    
    for i in range(10):
        assignment = Mock(spec=Assignment)
        assignment.id = i
        assignment.rater_email = f"rater{i % 3}@example.com"
        assignment.target_email = f"target{i % 5}@example.com"
        assignment.target_group = target_groups[i % len(target_groups)]
        assignment.rater_context = contexts[i % len(contexts)]
        assignment.weight = 1.0
        assignment.cycle_id = 1
        assignments.append(assignment)
    return assignments


def test_get_weight(mock_db_session):
    """Test weight retrieval"""
    handler = WeightMatrixHandler(cycle_id=1, db_session=mock_db_session)
    
    # Test default weights
    weight = handler.get_weight('academic', 'CEO')
    assert weight == 1.0
    
    weight = handler.get_weight('academic', 'P&C')
    assert weight == 0.8
    
    # Test unknown combination (should default to 1.0)
    weight = handler.get_weight('unknown', 'unknown')
    assert weight == 1.0


def test_load_evaluations(mock_db_session, sample_evaluations, sample_assignments):
    """Test loading evaluations"""
    # Mock queries
    eval_query = MagicMock()
    eval_query.join.return_value = eval_query
    eval_query.filter.return_value = eval_query
    eval_query.all.return_value = sample_evaluations
    
    assignment_query = MagicMock()
    assignment_query.filter.return_value = assignment_query
    assignment_query.first.side_effect = sample_assignments
    
    mock_db_session.query.side_effect = lambda model: (
        eval_query if model == Evaluation else assignment_query
    )
    
    handler = WeightMatrixHandler(cycle_id=1, db_session=mock_db_session)
    scores = handler.load_evaluations()
    
    assert len(scores) > 0
    assert all(hasattr(s, 'weighted_score') for s in scores)


def test_calculate_final_scores(mock_db_session, sample_evaluations, sample_assignments):
    """Test final score calculation"""
    eval_query = MagicMock()
    eval_query.join.return_value = eval_query
    eval_query.filter.return_value = eval_query
    eval_query.all.return_value = sample_evaluations
    
    assignment_query = MagicMock()
    assignment_query.filter.return_value = assignment_query
    assignment_query.first.side_effect = sample_assignments
    
    mock_db_session.query.side_effect = lambda model: (
        eval_query if model == Evaluation else assignment_query
    )
    
    handler = WeightMatrixHandler(cycle_id=1, db_session=mock_db_session)
    final_scores = handler.calculate_final_scores()
    
    assert isinstance(final_scores, dict)
    assert len(final_scores) > 0
    
    # Check structure
    for target, data in final_scores.items():
        assert 'weighted_average' in data
        assert 'simple_average' in data
        assert 'evaluation_count' in data
        assert 'context_breakdown' in data


def test_validate_evaluations(mock_db_session, sample_evaluations, sample_assignments):
    """Test evaluation validation"""
    eval_query = MagicMock()
    eval_query.join.return_value = eval_query
    eval_query.filter.return_value = eval_query
    eval_query.all.return_value = sample_evaluations
    
    assignment_query = MagicMock()
    assignment_query.filter.return_value = assignment_query
    assignment_query.first.side_effect = sample_assignments
    
    mock_db_session.query.side_effect = lambda model: (
        eval_query if model == Evaluation else assignment_query
    )
    
    handler = WeightMatrixHandler(cycle_id=1, db_session=mock_db_session)
    validation = handler.validate_evaluations()
    
    assert isinstance(validation, ValidationResult)
    assert hasattr(validation, 'is_valid')
    assert hasattr(validation, 'errors')
    assert hasattr(validation, 'warnings')


def test_update_weight_matrix(mock_db_session):
    """Test weight matrix update"""
    handler = WeightMatrixHandler(cycle_id=1, db_session=mock_db_session)
    
    original_weight = handler.get_weight('academic', 'CEO')
    handler.update_weight_matrix('academic', 'CEO', 1.5)
    new_weight = handler.get_weight('academic', 'CEO')
    
    assert new_weight == 1.5
    assert new_weight != original_weight


def test_get_evaluation_summary(mock_db_session, sample_evaluations, sample_assignments):
    """Test evaluation summary"""
    eval_query = MagicMock()
    eval_query.join.return_value = eval_query
    eval_query.filter.return_value = eval_query
    eval_query.all.return_value = sample_evaluations
    
    assignment_query = MagicMock()
    assignment_query.filter.return_value = assignment_query
    assignment_query.first.side_effect = sample_assignments
    
    mock_db_session.query.side_effect = lambda model: (
        eval_query if model == Evaluation else assignment_query
    )
    
    handler = WeightMatrixHandler(cycle_id=1, db_session=mock_db_session)
    summary = handler.get_evaluation_summary()
    
    assert 'total_evaluations' in summary
    assert 'total_targets' in summary
    assert 'total_raters' in summary
    assert 'average_raw_score' in summary
    assert 'average_weighted_score' in summary
    assert 'group_distribution' in summary
    assert 'context_distribution' in summary

