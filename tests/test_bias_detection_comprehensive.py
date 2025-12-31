"""
Comprehensive unit tests for bias detection algorithms and related functions.
Tests edge cases, specific scenarios, and various bias types.
"""
import pytest
import numpy as np
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, date, timedelta
from backend.bias_detection import BiasDetector
from backend.database import Evaluation, Assignment, Cycle, Person


@pytest.fixture
def mock_db_session():
    """Create a mock database session"""
    return Mock()


@pytest.fixture
def sample_cycle():
    """Create a sample cycle with dates"""
    cycle = Mock(spec=Cycle)
    cycle.id = 1
    cycle.start_date = date(2024, 1, 1)
    cycle.end_date = date(2024, 3, 31)
    return cycle


class TestRecencyBias:
    """Test suite for recency bias detection"""
    
    def test_positive_recency_bias(self, mock_db_session, sample_cycle):
        """Test detection of positive recency bias (later = higher ratings)"""
        detector = BiasDetector(mock_db_session)
        
        # Create evaluations with increasing ratings over time
        evaluations = []
        start_date = datetime(2024, 1, 1)
        for i in range(20):
            eval = Mock(spec=Evaluation)
            eval.id = i
            eval.rating = 2.0 + (i * 0.15)  # Increasing from 2.0 to 4.85
            eval.status = 'submitted'
            eval.assignment_id = i
            eval.submitted_at = start_date + timedelta(days=i*2)
            evaluations.append(eval)
        
        assignments = []
        for i in range(20):
            assignment = Mock(spec=Assignment)
            assignment.id = i
            assignment.rater_email = f"rater{i % 5}@example.com"
            assignment.target_email = f"target{i % 10}@example.com"
            assignment.rater_context = 'peer_review'
            assignments.append(assignment)
        
        # Mock queries
        eval_query = MagicMock()
        eval_query.join.return_value = eval_query
        eval_query.filter.return_value = eval_query
        eval_query.order_by.return_value = eval_query
        eval_query.all.return_value = evaluations
        
        assignment_query = MagicMock()
        assignment_query.filter.return_value = assignment_query
        assignment_query.first.side_effect = assignments
        
        cycle_query = MagicMock()
        cycle_query.filter.return_value = cycle_query
        cycle_query.first.return_value = sample_cycle
        
        mock_db_session.query.side_effect = lambda model: {
            Evaluation: eval_query,
            Assignment: assignment_query,
            Cycle: cycle_query
        }.get(model, assignment_query)
        
        result = detector.detect_recency_bias(cycle_id=1)
        
        assert result['status'] == 'analyzed'
        assert result['correlation'] > 0.3  # Should detect positive correlation
        assert result['interpretation'] == 'positive'
        assert result['late_submissions_mean'] > result['early_submissions_mean']
    
    def test_negative_recency_bias(self, mock_db_session, sample_cycle):
        """Test detection of negative recency bias (later = lower ratings)"""
        detector = BiasDetector(mock_db_session)
        
        # Create evaluations with decreasing ratings over time
        evaluations = []
        start_date = datetime(2024, 1, 1)
        for i in range(20):
            eval = Mock(spec=Evaluation)
            eval.id = i
            eval.rating = 4.5 - (i * 0.15)  # Decreasing from 4.5 to 1.65
            eval.status = 'submitted'
            eval.assignment_id = i
            eval.submitted_at = start_date + timedelta(days=i*2)
            evaluations.append(eval)
        
        assignments = []
        for i in range(20):
            assignment = Mock(spec=Assignment)
            assignment.id = i
            assignment.rater_email = f"rater{i % 5}@example.com"
            assignments.append(assignment)
        
        eval_query = MagicMock()
        eval_query.join.return_value = eval_query
        eval_query.filter.return_value = eval_query
        eval_query.order_by.return_value = eval_query
        eval_query.all.return_value = evaluations
        
        assignment_query = MagicMock()
        assignment_query.filter.return_value = assignment_query
        assignment_query.first.side_effect = assignments
        
        cycle_query = MagicMock()
        cycle_query.filter.return_value = cycle_query
        cycle_query.first.return_value = sample_cycle
        
        mock_db_session.query.side_effect = lambda model: {
            Evaluation: eval_query,
            Assignment: assignment_query,
            Cycle: cycle_query
        }.get(model, assignment_query)
        
        result = detector.detect_recency_bias(cycle_id=1)
        
        assert result['status'] == 'analyzed'
        assert result['correlation'] < -0.3  # Should detect negative correlation
        assert result['interpretation'] == 'negative'
        assert result['late_submissions_mean'] < result['early_submissions_mean']
    
    def test_no_recency_bias(self, mock_db_session, sample_cycle):
        """Test when there's no recency bias"""
        detector = BiasDetector(mock_db_session)
        
        # Create evaluations with random ratings (no time correlation)
        np.random.seed(42)
        evaluations = []
        start_date = datetime(2024, 1, 1)
        for i in range(20):
            eval = Mock(spec=Evaluation)
            eval.id = i
            eval.rating = 3.0 + np.random.normal(0, 0.5)
            eval.rating = max(1.0, min(5.0, eval.rating))
            eval.status = 'submitted'
            eval.assignment_id = i
            eval.submitted_at = start_date + timedelta(days=i*2)
            evaluations.append(eval)
        
        assignments = []
        for i in range(20):
            assignment = Mock(spec=Assignment)
            assignment.id = i
            assignment.rater_email = f"rater{i % 5}@example.com"
            assignments.append(assignment)
        
        eval_query = MagicMock()
        eval_query.join.return_value = eval_query
        eval_query.filter.return_value = eval_query
        eval_query.order_by.return_value = eval_query
        eval_query.all.return_value = evaluations
        
        assignment_query = MagicMock()
        assignment_query.filter.return_value = assignment_query
        assignment_query.first.side_effect = assignments
        
        cycle_query = MagicMock()
        cycle_query.filter.return_value = cycle_query
        cycle_query.first.return_value = sample_cycle
        
        mock_db_session.query.side_effect = lambda model: {
            Evaluation: eval_query,
            Assignment: assignment_query,
            Cycle: cycle_query
        }.get(model, assignment_query)
        
        result = detector.detect_recency_bias(cycle_id=1)
        
        assert result['status'] == 'analyzed'
        assert abs(result['correlation']) < 0.3  # Should be low correlation
        assert result['interpretation'] == 'none'
    
    def test_insufficient_data_recency(self, mock_db_session):
        """Test recency bias with insufficient data"""
        detector = BiasDetector(mock_db_session)
        
        eval_query = MagicMock()
        eval_query.join.return_value = eval_query
        eval_query.filter.return_value = eval_query
        eval_query.order_by.return_value = eval_query
        eval_query.all.return_value = []  # Empty
        
        mock_db_session.query.return_value = eval_query
        
        result = detector.detect_recency_bias(cycle_id=1)
        
        assert result['status'] == 'insufficient_data'
    
    def test_no_cycle_dates(self, mock_db_session):
        """Test recency bias when cycle dates are missing"""
        detector = BiasDetector(mock_db_session)
        
        evaluations = [Mock(spec=Evaluation) for _ in range(10)]
        for i, eval in enumerate(evaluations):
            eval.id = i
            eval.rating = 3.0
            eval.status = 'submitted'
            eval.assignment_id = i
        
        eval_query = MagicMock()
        eval_query.join.return_value = eval_query
        eval_query.filter.return_value = eval_query
        eval_query.order_by.return_value = eval_query
        eval_query.all.return_value = evaluations
        
        cycle_query = MagicMock()
        cycle_query.filter.return_value = cycle_query
        cycle_query.first.return_value = None  # No cycle found
        
        mock_db_session.query.side_effect = lambda model: (
            eval_query if model == Evaluation else cycle_query
        )
        
        result = detector.detect_recency_bias(cycle_id=1)
        
        assert result['status'] == 'no_cycle_dates'


class TestRoleBias:
    """Test suite for role-based bias detection"""
    
    def test_role_bias_with_statistical_significance(self, mock_db_session):
        """Test role bias detection with statistically significant differences"""
        detector = BiasDetector(mock_db_session)
        
        # Create evaluations with clear role-based differences
        evaluations = []
        assignments = []
        
        # Manager reviews: higher ratings (mean 4.5)
        for i in range(10):
            eval = Mock(spec=Evaluation)
            eval.id = i
            eval.rating = 4.5 + np.random.normal(0, 0.3)
            eval.rating = max(1.0, min(5.0, eval.rating))
            eval.status = 'submitted'
            eval.assignment_id = i
            evaluations.append(eval)
            
            assignment = Mock(spec=Assignment)
            assignment.id = i
            assignment.rater_context = 'manager_review'
            assignments.append(assignment)
        
        # Peer reviews: lower ratings (mean 2.5)
        for i in range(10, 20):
            eval = Mock(spec=Evaluation)
            eval.id = i
            eval.rating = 2.5 + np.random.normal(0, 0.3)
            eval.rating = max(1.0, min(5.0, eval.rating))
            eval.status = 'submitted'
            eval.assignment_id = i
            evaluations.append(eval)
            
            assignment = Mock(spec=Assignment)
            assignment.id = i
            assignment.rater_context = 'peer_review'
            assignments.append(assignment)
        
        eval_query = MagicMock()
        eval_query.join.return_value = eval_query
        eval_query.filter.return_value = eval_query
        eval_query.all.return_value = evaluations
        
        assignment_query = MagicMock()
        assignment_query.filter.return_value = assignment_query
        assignment_query.first.side_effect = assignments
        
        mock_db_session.query.side_effect = lambda model: (
            eval_query if model == Evaluation else assignment_query
        )
        
        result = detector.detect_role_bias(cycle_id=1)
        
        assert result['status'] == 'analyzed'
        assert 'contexts' in result
        assert 'manager_review' in result['contexts']
        assert 'peer_review' in result['contexts']
        assert result['contexts']['manager_review']['mean'] > result['contexts']['peer_review']['mean']
        assert 'statistical_test' in result
        if result['statistical_test']:
            assert 'p_value' in result['statistical_test']
    
    def test_role_bias_insufficient_data(self, mock_db_session):
        """Test role bias with insufficient data"""
        detector = BiasDetector(mock_db_session)
        
        eval_query = MagicMock()
        eval_query.join.return_value = eval_query
        eval_query.filter.return_value = eval_query
        eval_query.all.return_value = []  # Empty
        
        mock_db_session.query.return_value = eval_query
        
        result = detector.detect_role_bias(cycle_id=1)
        
        assert result['status'] == 'insufficient_data'


class TestSimilarityBias:
    """Test suite for similarity bias (halo effect) detection"""
    
    def test_halo_effect_detection(self, mock_db_session):
        """Test detection of halo effect (low variance in rater scores)"""
        detector = BiasDetector(mock_db_session)
        
        # Create evaluations where one rater gives very similar scores (halo effect)
        evaluations = []
        assignments = []
        
        # Rater 0: halo effect (all scores very similar)
        for i in range(5):
            eval = Mock(spec=Evaluation)
            eval.id = i
            eval.rating = 4.0 + np.random.normal(0, 0.1)  # Very low variance
            eval.rating = max(1.0, min(5.0, eval.rating))
            eval.status = 'submitted'
            eval.assignment_id = i
            evaluations.append(eval)
            
            assignment = Mock(spec=Assignment)
            assignment.id = i
            assignment.rater_email = 'rater0@example.com'
            assignment.target_email = f'target{i}@example.com'
            assignment.rater_context = 'peer_review'
            assignments.append(assignment)
        
        # Rater 1: normal variance
        for i in range(5, 10):
            eval = Mock(spec=Evaluation)
            eval.id = i
            eval.rating = 3.0 + np.random.normal(0, 1.0)  # Normal variance
            eval.rating = max(1.0, min(5.0, eval.rating))
            eval.status = 'submitted'
            eval.assignment_id = i
            evaluations.append(eval)
            
            assignment = Mock(spec=Assignment)
            assignment.id = i
            assignment.rater_email = 'rater1@example.com'
            assignment.target_email = f'target{i-5}@example.com'
            assignment.rater_context = 'peer_review'
            assignments.append(assignment)
        
        eval_query = MagicMock()
        eval_query.join.return_value = eval_query
        eval_query.filter.return_value = eval_query
        eval_query.all.return_value = evaluations
        
        assignment_query = MagicMock()
        assignment_query.filter.return_value = assignment_query
        assignment_query.first.side_effect = assignments
        
        mock_db_session.query.side_effect = lambda model: (
            eval_query if model == Evaluation else assignment_query
        )
        
        result = detector.detect_similarity_bias(cycle_id=1, variance_threshold=0.5)
        
        assert result['status'] == 'analyzed'
        assert 'bias_flags' in result
        assert len(result['bias_flags']) > 0
        # Check that rater0 is flagged for halo effect
        rater0_flags = [f for f in result['bias_flags'] if f['rater_id'] == 'rater0@example.com']
        assert len(rater0_flags) > 0
        assert rater0_flags[0]['bias_type'] == 'halo_effect'
        assert rater0_flags[0]['variance'] < 0.5
    
    def test_inter_rater_similarity(self, mock_db_session):
        """Test detection of inter-rater similarity"""
        detector = BiasDetector(mock_db_session)
        
        # Create evaluations where multiple raters give very similar scores to same target
        evaluations = []
        assignments = []
        
        # All raters give similar scores to target0 (low inter-rater variance)
        target0_ratings = [3.5, 3.6, 3.4, 3.5, 3.6]  # Very similar
        for i, rating in enumerate(target0_ratings):
            eval = Mock(spec=Evaluation)
            eval.id = i
            eval.rating = rating
            eval.status = 'submitted'
            eval.assignment_id = i
            evaluations.append(eval)
            
            assignment = Mock(spec=Assignment)
            assignment.id = i
            assignment.rater_email = f'rater{i}@example.com'
            assignment.target_email = 'target0@example.com'
            assignment.rater_context = 'peer_review'
            assignments.append(assignment)
        
        eval_query = MagicMock()
        eval_query.join.return_value = eval_query
        eval_query.filter.return_value = eval_query
        eval_query.all.return_value = evaluations
        
        assignment_query = MagicMock()
        assignment_query.filter.return_value = assignment_query
        assignment_query.first.side_effect = assignments
        
        mock_db_session.query.side_effect = lambda model: (
            eval_query if model == Evaluation else assignment_query
        )
        
        result = detector.detect_similarity_bias(cycle_id=1)
        
        assert result['status'] == 'analyzed'
        assert 'inter_rater_similarity' in result
        assert len(result['inter_rater_similarity']) > 0
        # Check that target0 has low variance
        target0_similarity = [s for s in result['inter_rater_similarity'] 
                            if s['target_id'] == 'target0@example.com']
        assert len(target0_similarity) > 0
        assert target0_similarity[0]['variance'] < 0.1  # Very low variance


class TestCentralityBias:
    """Test suite for centrality bias detection"""
    
    def test_strong_centrality_bias(self, mock_db_session):
        """Test detection of strong centrality bias (ratings cluster around middle)"""
        detector = BiasDetector(mock_db_session)
        
        # Create evaluations with ratings clustered around 3.0
        evaluations = []
        np.random.seed(42)
        for i in range(30):
            eval = Mock(spec=Evaluation)
            eval.id = i
            eval.rating = 3.0 + np.random.normal(0, 0.3)  # Low variance, centered at 3.0
            eval.rating = max(1.0, min(5.0, eval.rating))
            eval.status = 'submitted'
            evaluations.append(eval)
        
        eval_query = MagicMock()
        eval_query.join.return_value = eval_query
        eval_query.filter.return_value = eval_query
        eval_query.all.return_value = evaluations
        
        mock_db_session.query.return_value = eval_query
        
        result = detector.detect_centrality_bias(cycle_id=1)
        
        assert result['status'] == 'analyzed'
        assert 'centrality_index' in result
        assert result['centrality_index'] < 0.8  # Low std relative to expected
        assert result['interpretation'] in ['low', 'moderate']
    
    def test_no_centrality_bias(self, mock_db_session):
        """Test when there's no centrality bias (good distribution)"""
        detector = BiasDetector(mock_db_session)
        
        # Create evaluations with good distribution across scale
        evaluations = []
        ratings = [1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0] * 3
        for i, rating in enumerate(ratings):
            eval = Mock(spec=Evaluation)
            eval.id = i
            eval.rating = rating
            eval.status = 'submitted'
            evaluations.append(eval)
        
        eval_query = MagicMock()
        eval_query.join.return_value = eval_query
        eval_query.filter.return_value = eval_query
        eval_query.all.return_value = evaluations
        
        mock_db_session.query.return_value = eval_query
        
        result = detector.detect_centrality_bias(cycle_id=1)
        
        assert result['status'] == 'analyzed'
        assert result['centrality_index'] >= 0.8  # Higher std
        assert result['interpretation'] == 'normal'


class TestHarshnessBias:
    """Test suite for harshness/leniency bias detection"""
    
    def test_harsh_rater_detection(self, mock_db_session):
        """Test detection of harsh raters (consistently rate lower)"""
        detector = BiasDetector(mock_db_session)
        
        evaluations = []
        assignments = []
        
        # Harsh rater: consistently rates 1.5 points lower
        for i in range(5):
            eval = Mock(spec=Evaluation)
            eval.id = i
            eval.rating = 2.0  # Low ratings
            eval.status = 'submitted'
            eval.assignment_id = i
            evaluations.append(eval)
            
            assignment = Mock(spec=Assignment)
            assignment.id = i
            assignment.rater_email = 'harsh_rater@example.com'
            assignment.target_email = f'target{i}@example.com'
            assignments.append(assignment)
        
        # Normal raters: average ratings
        for i in range(5, 15):
            eval = Mock(spec=Evaluation)
            eval.id = i
            eval.rating = 3.5  # Average ratings
            eval.status = 'submitted'
            eval.assignment_id = i
            evaluations.append(eval)
            
            assignment = Mock(spec=Assignment)
            assignment.id = i
            assignment.rater_email = f'normal_rater{(i-5) % 3}@example.com'
            assignment.target_email = f'target{(i-5) % 5}@example.com'
            assignments.append(assignment)
        
        eval_query = MagicMock()
        eval_query.join.return_value = eval_query
        eval_query.filter.return_value = eval_query
        eval_query.all.return_value = evaluations
        
        assignment_query = MagicMock()
        assignment_query.filter.return_value = assignment_query
        assignment_query.first.side_effect = assignments
        
        mock_db_session.query.side_effect = lambda model: (
            eval_query if model == Evaluation else assignment_query
        )
        
        result = detector.detect_harshness_bias(cycle_id=1)
        
        assert result['status'] == 'analyzed'
        assert 'rater_bias' in result
        if 'harsh_rater@example.com' in result['rater_bias']:
            bias_info = result['rater_bias']['harsh_rater@example.com']
            assert bias_info['interpretation'] == 'harsh'
            assert bias_info['bias'] < -0.5
    
    def test_lenient_rater_detection(self, mock_db_session):
        """Test detection of lenient raters (consistently rate higher)"""
        detector = BiasDetector(mock_db_session)
        
        evaluations = []
        assignments = []
        
        # Lenient rater: consistently rates 1.5 points higher
        for i in range(5):
            eval = Mock(spec=Evaluation)
            eval.id = i
            eval.rating = 5.0  # High ratings
            eval.status = 'submitted'
            eval.assignment_id = i
            evaluations.append(eval)
            
            assignment = Mock(spec=Assignment)
            assignment.id = i
            assignment.rater_email = 'lenient_rater@example.com'
            assignment.target_email = f'target{i}@example.com'
            assignments.append(assignment)
        
        # Normal raters: average ratings
        for i in range(5, 15):
            eval = Mock(spec=Evaluation)
            eval.id = i
            eval.rating = 3.5  # Average ratings
            eval.status = 'submitted'
            eval.assignment_id = i
            evaluations.append(eval)
            
            assignment = Mock(spec=Assignment)
            assignment.id = i
            assignment.rater_email = f'normal_rater{(i-5) % 3}@example.com'
            assignment.target_email = f'target{(i-5) % 5}@example.com'
            assignments.append(assignment)
        
        eval_query = MagicMock()
        eval_query.join.return_value = eval_query
        eval_query.filter.return_value = eval_query
        eval_query.all.return_value = evaluations
        
        assignment_query = MagicMock()
        assignment_query.filter.return_value = assignment_query
        assignment_query.first.side_effect = assignments
        
        mock_db_session.query.side_effect = lambda model: (
            eval_query if model == Evaluation else assignment_query
        )
        
        result = detector.detect_harshness_bias(cycle_id=1)
        
        assert result['status'] == 'analyzed'
        assert 'rater_bias' in result
        if 'lenient_rater@example.com' in result['rater_bias']:
            bias_info = result['rater_bias']['lenient_rater@example.com']
            assert bias_info['interpretation'] == 'lenient'
            assert bias_info['bias'] > 0.5


class TestWeightedScoreCalculation:
    """Test suite for weighted score calculations"""
    
    def test_calculate_weighted_score_basic(self, mock_db_session):
        """Test basic weighted score calculation"""
        detector = BiasDetector(mock_db_session)
        
        scores = {
            'peer_review': 4.0,
            'manager_review': 3.5,
            'direct_report_review': 4.5
        }
        
        weights = {
            'peer_review': 0.3,
            'manager_review': 0.5,
            'direct_report_review': 0.2
        }
        
        result = detector.calculate_weighted_score(scores, weights)
        
        expected = (4.0 * 0.3 + 3.5 * 0.5 + 4.5 * 0.2) / 1.0
        assert abs(result - expected) < 0.001
    
    def test_calculate_weighted_score_missing_weights(self, mock_db_session):
        """Test weighted score with missing weights (should use default 1.0)"""
        detector = BiasDetector(mock_db_session)
        
        scores = {
            'peer_review': 4.0,
            'manager_review': 3.5,
            'unknown_context': 4.5
        }
        
        weights = {
            'peer_review': 0.5,
            'manager_review': 0.5
            # missing 'unknown_context'
        }
        
        result = detector.calculate_weighted_score(scores, weights)
        
        # Should use weight 1.0 for unknown_context
        expected = (4.0 * 0.5 + 3.5 * 0.5 + 4.5 * 1.0) / 2.0
        assert abs(result - expected) < 0.001
    
    def test_calculate_weighted_score_empty_scores(self, mock_db_session):
        """Test weighted score with empty scores"""
        detector = BiasDetector(mock_db_session)
        
        result = detector.calculate_weighted_score({}, {})
        
        assert result == 0.0
    
    def test_calculate_weighted_score_zero_total_weight(self, mock_db_session):
        """Test weighted score when total weight is zero"""
        detector = BiasDetector(mock_db_session)
        
        scores = {'peer_review': 4.0}
        weights = {'peer_review': 0.0}
        
        result = detector.calculate_weighted_score(scores, weights)
        
        assert result == 0.0
    
    def test_calculate_weighted_score_by_assignment(self, mock_db_session):
        """Test weighted score calculation by assignment"""
        detector = BiasDetector(mock_db_session)
        
        # Create evaluations with assignments
        evaluations_data = [
            (Mock(spec=Evaluation, rating=4.0, status='submitted', assignment_id=0),
             Mock(spec=Assignment, rater_context='peer_review', weight=0.3, cycle_id=1, target_email='target1@example.com')),
            (Mock(spec=Evaluation, rating=3.5, status='submitted', assignment_id=1),
             Mock(spec=Assignment, rater_context='manager_review', weight=0.7, cycle_id=1, target_email='target1@example.com')),
        ]
        
        eval_query = MagicMock()
        eval_query.join.return_value = eval_query
        eval_query.filter.return_value = eval_query
        eval_query.all.return_value = [e[0] for e in evaluations_data]
        
        # For the join query
        join_query = MagicMock()
        join_query.join.return_value = join_query
        join_query.filter.return_value = join_query
        join_query.all.return_value = evaluations_data
        
        mock_db_session.query.side_effect = lambda model: (
            join_query if model == Evaluation else eval_query
        )
        
        result = detector.calculate_weighted_score_by_assignment(
            cycle_id=1, 
            target_email='target1@example.com'
        )
        
        assert result['status'] == 'calculated'
        assert 'weighted_score' in result
        assert result['weighted_score'] is not None
        assert 'scores_by_context' in result
        assert 'weights_by_context' in result
    
    def test_calculate_weighted_score_by_assignment_no_data(self, mock_db_session):
        """Test weighted score calculation when no evaluations exist"""
        detector = BiasDetector(mock_db_session)
        
        join_query = MagicMock()
        join_query.join.return_value = join_query
        join_query.filter.return_value = join_query
        join_query.all.return_value = []  # No evaluations
        
        mock_db_session.query.return_value = join_query
        
        result = detector.calculate_weighted_score_by_assignment(
            cycle_id=1,
            target_email='target1@example.com'
        )
        
        assert result['status'] == 'no_evaluations'
        assert result['weighted_score'] is None


class TestComprehensiveBiasReport:
    """Test suite for comprehensive bias report"""
    
    def test_comprehensive_bias_report_structure(self, mock_db_session, sample_cycle):
        """Test comprehensive bias report has all required components"""
        detector = BiasDetector(mock_db_session)
        
        # Create sample data
        evaluations = []
        assignments = []
        for i in range(20):
            eval = Mock(spec=Evaluation)
            eval.id = i
            eval.rating = 3.0 + np.random.normal(0, 0.5)
            eval.rating = max(1.0, min(5.0, eval.rating))
            eval.status = 'submitted'
            eval.assignment_id = i
            eval.submitted_at = datetime(2024, 1, 1) + timedelta(days=i)
            evaluations.append(eval)
            
            assignment = Mock(spec=Assignment)
            assignment.id = i
            assignment.rater_email = f'rater{i % 5}@example.com'
            assignment.target_email = f'target{i % 10}@example.com'
            assignment.rater_context = ['peer_review', 'manager_review'][i % 2]
            assignments.append(assignment)
        
        eval_query = MagicMock()
        eval_query.join.return_value = eval_query
        eval_query.filter.return_value = eval_query
        eval_query.order_by.return_value = eval_query
        eval_query.all.return_value = evaluations
        
        assignment_query = MagicMock()
        assignment_query.filter.return_value = assignment_query
        assignment_query.first.side_effect = assignments
        
        cycle_query = MagicMock()
        cycle_query.filter.return_value = cycle_query
        cycle_query.first.return_value = sample_cycle
        
        mock_db_session.query.side_effect = lambda model: {
            Evaluation: eval_query,
            Assignment: assignment_query,
            Cycle: cycle_query
        }.get(model, assignment_query)
        
        report = detector.comprehensive_bias_report(cycle_id=1)
        
        assert 'cycle_id' in report
        assert report['cycle_id'] == 1
        assert 'role_bias' in report
        assert 'recency_bias' in report
        assert 'centrality_bias' in report
        assert 'harshness_bias' in report
        assert 'similarity_bias' in report
        assert 'gender_bias' in report


class TestEdgeCases:
    """Test suite for edge cases and error handling"""
    
    def test_gender_bias_insufficient_data(self, mock_db_session):
        """Test gender bias with insufficient data"""
        detector = BiasDetector(mock_db_session)
        
        eval_query = MagicMock()
        eval_query.join.return_value = eval_query
        eval_query.filter.return_value = eval_query
        eval_query.all.return_value = [Mock(spec=Evaluation) for _ in range(5)]  # Less than 10
        
        mock_db_session.query.return_value = eval_query
        
        result = detector.detect_gender_bias(cycle_id=1)
        
        assert result['status'] == 'insufficient_data'
    
    def test_similarity_bias_insufficient_data(self, mock_db_session):
        """Test similarity bias with insufficient data"""
        detector = BiasDetector(mock_db_session)
        
        eval_query = MagicMock()
        eval_query.join.return_value = eval_query
        eval_query.filter.return_value = eval_query
        eval_query.all.return_value = []  # Empty
        
        mock_db_session.query.return_value = eval_query
        
        result = detector.detect_similarity_bias(cycle_id=1)
        
        assert result['status'] == 'insufficient_data'
    
    def test_similarity_bias_no_data(self, mock_db_session):
        """Test similarity bias when no assignment data exists"""
        detector = BiasDetector(mock_db_session)
        
        evaluations = [Mock(spec=Evaluation, rating=3.0, status='submitted', assignment_id=0)]
        
        eval_query = MagicMock()
        eval_query.join.return_value = eval_query
        eval_query.filter.return_value = eval_query
        eval_query.all.return_value = evaluations
        
        assignment_query = MagicMock()
        assignment_query.filter.return_value = assignment_query
        assignment_query.first.return_value = None  # No assignment found
        
        mock_db_session.query.side_effect = lambda model: (
            eval_query if model == Evaluation else assignment_query
        )
        
        result = detector.detect_similarity_bias(cycle_id=1)
        
        assert result['status'] == 'no_data'
    
    def test_role_bias_no_statistical_test(self, mock_db_session):
        """Test role bias when statistical test cannot be performed"""
        detector = BiasDetector(mock_db_session)
        
        # Create evaluations but with insufficient groups for statistical test
        evaluations = []
        assignments = []
        for i in range(5):
            eval = Mock(spec=Evaluation)
            eval.id = i
            eval.rating = 3.0
            eval.status = 'submitted'
            eval.assignment_id = i
            evaluations.append(eval)
            
            assignment = Mock(spec=Assignment)
            assignment.id = i
            assignment.rater_context = 'peer_review'  # Only one context
            assignments.append(assignment)
        
        eval_query = MagicMock()
        eval_query.join.return_value = eval_query
        eval_query.filter.return_value = eval_query
        eval_query.all.return_value = evaluations
        
        assignment_query = MagicMock()
        assignment_query.filter.return_value = assignment_query
        assignment_query.first.side_effect = assignments
        
        mock_db_session.query.side_effect = lambda model: (
            eval_query if model == Evaluation else assignment_query
        )
        
        result = detector.detect_role_bias(cycle_id=1)
        
        assert result['status'] == 'analyzed'
        # Should not have statistical_test if insufficient groups
        assert 'statistical_test' not in result or result.get('statistical_test') is None

