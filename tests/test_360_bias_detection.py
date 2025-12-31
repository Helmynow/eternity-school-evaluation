"""
Tests for Complete 360-Degree Bias Detection System.
"""
import pytest
import numpy as np
from unittest.mock import Mock, MagicMock
from backend.bias_detection_360 import Complete360BiasDetection, BiasFinding, BiasReport
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
    for i in range(30):
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
    """Create sample assignment data with 360-degree contexts"""
    assignments = []
    contexts = ['peer_review', 'manager_review', 'direct_report_review', 'self_review']
    target_groups = ['academic', 'admin', 'peers']
    
    for i in range(30):
        assignment = Mock(spec=Assignment)
        assignment.id = i
        assignment.rater_email = f"rater{i % 5}@example.com"
        assignment.target_email = f"target{i % 10}@example.com"
        assignment.target_group = target_groups[i % len(target_groups)]
        assignment.rater_context = contexts[i % len(contexts)]
        assignment.weight = 1.0
        assignment.cycle_id = 1
        assignments.append(assignment)
    return assignments


def test_generate_complete_report(mock_db_session, sample_evaluations, sample_assignments):
    """Test complete report generation"""
    # Mock queries
    eval_query = MagicMock()
    eval_query.join.return_value = eval_query
    eval_query.filter.return_value = eval_query
    eval_query.all.return_value = sample_evaluations
    
    assignment_query = MagicMock()
    assignment_query.filter.return_value = assignment_query
    assignment_query.all.return_value = sample_assignments
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
    }.get(model, assignment_query)
    
    detector = Complete360BiasDetection(mock_db_session)
    report = detector.generate_complete_report(cycle_id=1)
    
    assert isinstance(report, BiasReport)
    assert report.cycle_id == 1
    assert isinstance(report.findings, list)
    assert 'overall_bias_score' in asdict(report)
    assert 'recommendations' in asdict(report)


def test_check_360_completeness(mock_db_session, sample_assignments):
    """Test 360-degree completeness check"""
    assignment_query = MagicMock()
    assignment_query.filter.return_value = assignment_query
    assignment_query.all.return_value = sample_assignments
    
    mock_db_session.query.return_value = assignment_query
    
    detector = Complete360BiasDetection(mock_db_session)
    findings = detector._check_360_completeness(cycle_id=1)
    
    assert isinstance(findings, list)
    # All findings should be BiasFinding instances
    for finding in findings:
        assert isinstance(finding, BiasFinding)
        assert finding.bias_type.startswith('structural')


def test_calculate_overall_bias_score():
    """Test overall bias score calculation"""
    detector = Complete360BiasDetection(Mock())
    
    findings = [
        BiasFinding(
            bias_type='test',
            severity='high',
            score=0.8,
            description='Test',
            affected_raters=[],
            affected_targets=[],
            evidence={},
            recommendations=[]
        ),
        BiasFinding(
            bias_type='test2',
            severity='medium',
            score=0.5,
            description='Test2',
            affected_raters=[],
            affected_targets=[],
            evidence={},
            recommendations=[]
        )
    ]
    
    score = detector._calculate_overall_bias_score(findings)
    
    assert 0.0 <= score <= 1.0
    assert score > 0


def test_get_bias_summary_by_target(mock_db_session, sample_evaluations, sample_assignments):
    """Test target-specific bias summary"""
    eval_query = MagicMock()
    eval_query.join.return_value = eval_query
    eval_query.filter.return_value = eval_query
    eval_query.all.return_value = sample_evaluations
    
    assignment_query = MagicMock()
    assignment_query.filter.return_value = assignment_query
    assignment_query.all.return_value = sample_assignments
    assignment_query.first.side_effect = sample_assignments
    
    mock_db_session.query.side_effect = lambda model: (
        eval_query if model == Evaluation else assignment_query
    )
    
    detector = Complete360BiasDetection(mock_db_session)
    summary = detector.get_bias_summary_by_target(cycle_id=1, target_email='target1@example.com')
    
    assert 'target_email' in summary
    assert 'status' in summary
    if summary['status'] == 'analyzed':
        assert 'mean_rating' in summary
        assert 'context_breakdown' in summary
        assert 'is_complete_360' in summary


def test_export_report_to_dict():
    """Test report export to dictionary"""
    detector = Complete360BiasDetection(Mock())
    
    report = BiasReport(
        cycle_id=1,
        overall_bias_score=0.5,
        total_evaluations=30,
        total_raters=5,
        total_targets=10,
        findings=[],
        context_coverage={},
        statistical_summary={},
        recommendations=['Test recommendation'],
        generated_at='2024-01-01T00:00:00'
    )
    
    export = detector.export_report_to_dict(report)
    
    assert 'cycle_id' in export
    assert 'overall_bias_score' in export
    assert 'bias_level' in export
    assert 'findings' in export
    assert 'recommendations' in export

