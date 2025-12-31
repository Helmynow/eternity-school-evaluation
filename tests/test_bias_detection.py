"""
Tests for bias detection algorithms.
"""
import pytest
import numpy as np
from unittest.mock import Mock, MagicMock
from backend.bias_detection import BiasDetector
from backend.database import Evaluation, Assignment, Cycle


@pytest.fixture
def mock_db_session():
    """Create a mock database session"""
    session = Mock()
    return session


@pytest.fixture
def sample_evaluations():
    """Create sample evaluation data"""
    evaluations = []
    for i in range(20):
        eval = Mock(spec=Evaluation)
        eval.id = i
        eval.rating = 3.0 + np.random.normal(0, 0.5)
        eval.rating = max(1.0, min(5.0, eval.rating))  # Clamp to 1-5
        eval.status = 'submitted'
        eval.comments = f"Comment {i}"
        eval.assignment_id = i
        evaluations.append(eval)
    return evaluations


@pytest.fixture
def sample_assignments():
    """Create sample assignment data"""
    assignments = []
    contexts = ['peer_review', 'manager_review', 'direct_report_review']
    for i in range(20):
        assignment = Mock(spec=Assignment)
        assignment.id = i
        assignment.rater_email = f"rater{i % 5}@example.com"
        assignment.target_email = f"target{i % 10}@example.com"
        assignment.rater_context = contexts[i % len(contexts)]
        assignment.target_group = 'peers'
        assignment.cycle_id = 1
        assignments.append(assignment)
    return assignments


def test_detect_centrality_bias(mock_db_session, sample_evaluations):
    """Test centrality bias detection"""
    detector = BiasDetector(mock_db_session)
    
    # Mock query
    mock_query = MagicMock()
    mock_query.join.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.all.return_value = sample_evaluations
    
    mock_db_session.query.return_value = mock_query
    
    result = detector.detect_centrality_bias(cycle_id=1)
    
    assert result['status'] == 'analyzed'
    assert 'mean_rating' in result
    assert 'std_rating' in result
    assert 'centrality_index' in result


def test_detect_harshness_bias(mock_db_session, sample_evaluations, sample_assignments):
    """Test harshness bias detection"""
    detector = BiasDetector(mock_db_session)
    
    # Mock evaluation query
    eval_query = MagicMock()
    eval_query.join.return_value = eval_query
    eval_query.filter.return_value = eval_query
    eval_query.all.return_value = sample_evaluations
    
    # Mock assignment query
    assignment_query = MagicMock()
    assignment_query.filter.return_value = assignment_query
    assignment_query.first.side_effect = sample_assignments
    
    mock_db_session.query.side_effect = lambda model: (
        eval_query if model == Evaluation else assignment_query
    )
    
    result = detector.detect_harshness_bias(cycle_id=1)
    
    assert result['status'] == 'analyzed'
    assert 'rater_bias' in result


def test_insufficient_data(mock_db_session):
    """Test that insufficient data returns appropriate status"""
    detector = BiasDetector(mock_db_session)
    
    # Mock query with few results
    mock_query = MagicMock()
    mock_query.join.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.all.return_value = []  # Empty results
    
    mock_db_session.query.return_value = mock_query
    
    result = detector.detect_centrality_bias(cycle_id=1)
    
    assert result['status'] == 'insufficient_data'


def test_detect_similarity_bias(mock_db_session, sample_evaluations, sample_assignments):
    """Test similarity bias (halo effect) detection"""
    detector = BiasDetector(mock_db_session)
    
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
    
    result = detector.detect_similarity_bias(cycle_id=1)
    
    assert 'status' in result
    if result['status'] == 'analyzed':
        assert 'bias_flags' in result
        assert 'total_raters_checked' in result


def test_calculate_weighted_score(mock_db_session):
    """Test weighted score calculation"""
    detector = BiasDetector(mock_db_session)
    
    scores = {
        'peer_review': 4.5,
        'manager_review': 3.8,
        'direct_report_review': 4.2
    }
    
    weights = {
        'peer_review': 0.3,
        'manager_review': 0.5,
        'direct_report_review': 0.2
    }
    
    weighted_score = detector.calculate_weighted_score(scores, weights)
    
    # Manual calculation: (4.5*0.3 + 3.8*0.5 + 4.2*0.2) / 1.0 = 4.09
    expected = (4.5 * 0.3 + 3.8 * 0.5 + 4.2 * 0.2)
    assert abs(weighted_score - expected) < 0.01


def test_comprehensive_bias_report(mock_db_session, sample_evaluations, sample_assignments):
    """Test comprehensive bias report generation"""
    detector = BiasDetector(mock_db_session)
    
    # Mock queries
    eval_query = MagicMock()
    eval_query.join.return_value = eval_query
    eval_query.filter.return_value = eval_query
    eval_query.all.return_value = sample_evaluations
    
    assignment_query = MagicMock()
    assignment_query.filter.return_value = assignment_query
    assignment_query.first.side_effect = sample_assignments
    
    cycle_query = MagicMock()
    cycle_query.filter.return_value = cycle_query
    cycle = Mock(spec=Cycle)
    cycle.id = 1
    cycle.start_date = Mock()
    cycle_query.first.return_value = cycle
    
    mock_db_session.query.side_effect = lambda model: {
        Evaluation: eval_query,
        Assignment: assignment_query,
        Cycle: cycle_query
    }.get(model, eval_query)
    
    report = detector.comprehensive_bias_report(cycle_id=1)
    
    assert 'cycle_id' in report
    assert 'role_bias' in report
    assert 'recency_bias' in report
    assert 'centrality_bias' in report
    assert 'harshness_bias' in report
    assert 'similarity_bias' in report

