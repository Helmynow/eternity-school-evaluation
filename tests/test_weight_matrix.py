"""
Tests for weight matrix calculations.
"""
import pytest
import numpy as np
from unittest.mock import Mock, MagicMock
from backend.weight_matrix import WeightMatrix
from backend.database import Assignment


@pytest.fixture
def mock_db_session():
    """Create a mock database session"""
    session = Mock()
    return session


@pytest.fixture
def sample_assignments():
    """Create sample assignment data"""
    assignments = []
    raters = ['rater1@example.com', 'rater2@example.com', 'rater3@example.com']
    targets = ['target1@example.com', 'target2@example.com', 'target3@example.com']
    
    for i, rater in enumerate(raters):
        for j, target in enumerate(targets):
            assignment = Mock(spec=Assignment)
            assignment.rater_email = rater
            assignment.target_email = target
            assignment.weight = 1.0 if i != j else 0.0  # No self-evaluations
            assignments.append(assignment)
    
    return assignments


def test_build_matrix(mock_db_session, sample_assignments):
    """Test matrix building"""
    # Mock query
    mock_query = MagicMock()
    mock_query.filter.return_value = mock_query
    mock_query.all.return_value = sample_assignments
    
    mock_db_session.query.return_value = mock_query
    
    wm = WeightMatrix(cycle_id=1, db_session=mock_db_session)
    matrix = wm.build_matrix()
    
    assert matrix is not None
    assert isinstance(matrix, np.ndarray)
    assert len(wm.rater_indices) > 0
    assert len(wm.target_indices) > 0


def test_calculate_fairness_metrics(mock_db_session, sample_assignments):
    """Test fairness metrics calculation"""
    mock_query = MagicMock()
    mock_query.filter.return_value = mock_query
    mock_query.all.return_value = sample_assignments
    
    mock_db_session.query.return_value = mock_query
    
    wm = WeightMatrix(cycle_id=1, db_session=mock_db_session)
    wm.build_matrix()
    metrics = wm.calculate_fairness_metrics()
    
    assert 'rater_load_mean' in metrics
    assert 'rater_load_std' in metrics
    assert 'target_load_mean' in metrics
    assert 'target_load_std' in metrics
    assert 'coverage' in metrics
    assert 'group_distribution' in metrics


def test_optimize_weights(mock_db_session, sample_assignments):
    """Test weight optimization"""
    mock_query = MagicMock()
    mock_query.filter.return_value = mock_query
    mock_query.all.return_value = sample_assignments
    
    mock_db_session.query.return_value = mock_query
    
    wm = WeightMatrix(cycle_id=1, db_session=mock_db_session)
    wm.build_matrix()
    optimized = wm.optimize_weights()
    
    assert optimized is not None
    assert isinstance(optimized, np.ndarray)
    assert optimized.shape == wm.matrix.shape


def test_get_imbalanced_assignments(mock_db_session, sample_assignments):
    """Test identification of imbalanced assignments"""
    mock_query = MagicMock()
    mock_query.filter.return_value = mock_query
    mock_query.all.return_value = sample_assignments
    
    mock_db_session.query.return_value = mock_query
    
    wm = WeightMatrix(cycle_id=1, db_session=mock_db_session)
    wm.build_matrix()
    imbalanced = wm.get_imbalanced_assignments()
    
    assert isinstance(imbalanced, list)
    # Each item should have required fields
    for item in imbalanced:
        assert 'type' in item
        assert 'email' in item
        assert 'load' in item
        assert 'deviation' in item

