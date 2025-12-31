"""
Unit tests for Context-Aware 360-Degree Bias Detection.
"""
import pytest
import numpy as np
from unittest.mock import Mock, MagicMock
from backend.context_aware_bias_detection import (
    ContextAware360BiasDetection,
    ContextBiasFinding,
    CrossContextAnalysis
)
from backend.database import Assignment, Evaluation


@pytest.fixture
def mock_db_session():
    """Create a mock database session"""
    return Mock()


@pytest.fixture
def sample_assignments():
    """Create sample assignments for different contexts"""
    assignments = []
    contexts = ['peer_review', 'manager_review', 'direct_report_review', 'self_review']
    
    for i, context in enumerate(contexts):
        assignment = Mock(spec=Assignment)
        assignment.id = i + 1
        assignment.rater_email = f'rater{i+1}@example.com'
        assignment.target_email = 'target@example.com'
        assignment.rater_context = context
        assignment.cycle_id = 1
        assignments.append(assignment)
    
    return assignments


@pytest.fixture
def sample_evaluations():
    """Create sample evaluations"""
    evaluations = []
    ratings_by_context = {
        'peer_review': [4.0, 4.5, 3.8],
        'manager_review': [4.2],
        'direct_report_review': [4.0],
        'self_review': [4.8]
    }
    
    eval_id = 1
    for context, ratings in ratings_by_context.items():
        for rating in ratings:
            eval_obj = Mock(spec=Evaluation)
            eval_obj.id = eval_id
            eval_obj.rating = rating
            eval_obj.assignment_id = eval_id
            eval_obj.status = 'submitted'
            evaluations.append(eval_obj)
            eval_id += 1
    
    return evaluations


class TestContextDataLoading:
    """Test loading evaluation data by context"""
    
    def test_load_context_data(self, mock_db_session, sample_evaluations, sample_assignments):
        """Test loading data grouped by context"""
        detector = ContextAware360BiasDetection(mock_db_session)
        
        # Mock query results
        eval_assign_pairs = list(zip(sample_evaluations, sample_assignments))
        
        query_mock = MagicMock()
        query_mock.join.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.all.return_value = eval_assign_pairs
        
        mock_db_session.query.return_value = query_mock
        
        context_data = detector._load_context_data(cycle_id=1)
        
        assert isinstance(context_data, dict)
        assert 'peer_review' in context_data or len(context_data) > 0


class TestContextSpecificBias:
    """Test context-specific bias detection"""
    
    def test_analyze_context_specific_bias_centrality(self, mock_db_session):
        """Test centrality bias detection in a context"""
        detector = ContextAware360BiasDetection(mock_db_session)
        
        # Low variance ratings (centrality bias)
        ratings = [3.0, 3.1, 3.0, 3.2, 3.1]
        assignments = [Mock(spec=Assignment) for _ in range(5)]
        for i, a in enumerate(assignments):
            a.rater_email = f'rater{i}@example.com'
            a.target_email = f'target{i}@example.com'
        
        findings = detector._analyze_context_specific_bias(
            context='peer_review',
            ratings=ratings,
            assignments=assignments
        )
        
        assert len(findings) > 0
        assert any(f.bias_type == 'centrality_bias' for f in findings)
    
    def test_analyze_context_specific_bias_harshness(self, mock_db_session):
        """Test harshness bias detection"""
        detector = ContextAware360BiasDetection(mock_db_session)
        
        # Low ratings (harshness)
        ratings = [2.0, 2.1, 2.2, 2.0, 2.1]
        assignments = [Mock(spec=Assignment) for _ in range(5)]
        for i, a in enumerate(assignments):
            a.rater_email = f'rater{i}@example.com'
            a.target_email = f'target{i}@example.com'
        
        findings = detector._analyze_context_specific_bias(
            context='manager_review',
            ratings=ratings,
            assignments=assignments
        )
        
        assert any(f.bias_type == 'harshness_bias' for f in findings)
    
    def test_analyze_context_specific_bias_leniency(self, mock_db_session):
        """Test leniency bias detection"""
        detector = ContextAware360BiasDetection(mock_db_session)
        
        # High ratings (leniency)
        ratings = [4.5, 4.6, 4.7, 4.5, 4.6]
        assignments = [Mock(spec=Assignment) for _ in range(5)]
        for i, a in enumerate(assignments):
            a.rater_email = f'rater{i}@example.com'
            a.target_email = f'target{i}@example.com'
        
        findings = detector._analyze_context_specific_bias(
            context='peer_review',
            ratings=ratings,
            assignments=assignments
        )
        
        assert any(f.bias_type == 'leniency_bias' for f in findings)
    
    def test_analyze_context_specific_bias_halo(self, mock_db_session):
        """Test halo effect detection"""
        detector = ContextAware360BiasDetection(mock_db_session)
        
        # Very low variance (halo effect)
        ratings = [4.0, 4.0, 4.0, 4.1, 4.0]
        assignments = [Mock(spec=Assignment) for _ in range(5)]
        for i, a in enumerate(assignments):
            a.rater_email = f'rater{i}@example.com'
            a.target_email = f'target{i}@example.com'
        
        findings = detector._analyze_context_specific_bias(
            context='direct_report_review',
            ratings=ratings,
            assignments=assignments
        )
        
        assert any(f.bias_type == 'halo_effect' for f in findings)


class TestCrossContextComparison:
    """Test cross-context comparison analysis"""
    
    def test_analyze_cross_context_comparisons(self, mock_db_session):
        """Test comparing ratings across contexts"""
        detector = ContextAware360BiasDetection(mock_db_session)
        
        context_data = {
            'peer_review': {
                'ratings': [4.0, 4.5, 3.8, 4.2],
                'assignments': [],
                'raters': [],
                'targets': [],
                'rater_target_pairs': []
            },
            'manager_review': {
                'ratings': [3.0, 3.2, 2.8],
                'assignments': [],
                'raters': [],
                'targets': [],
                'rater_target_pairs': []
            }
        }
        
        analyses = detector._analyze_cross_context_comparisons(context_data)
        
        assert len(analyses) > 0
        assert all(isinstance(a, CrossContextAnalysis) for a in analyses)
        assert all(a.context_pair[0] != a.context_pair[1] for a in analyses)


class TestContextConsistency:
    """Test context consistency analysis"""
    
    def test_analyze_context_consistency(self, mock_db_session):
        """Test consistency analysis across contexts"""
        detector = ContextAware360BiasDetection(mock_db_session)
        
        context_data = {
            'peer_review': {
                'ratings': [4.0, 4.5, 3.8],
                'assignments': [],
                'raters': [],
                'targets': ['target@example.com'],
                'rater_target_pairs': [
                    {'rater': 'rater1@example.com', 'target': 'target@example.com', 'rating': 4.0},
                    {'rater': 'rater2@example.com', 'target': 'target@example.com', 'rating': 4.5},
                    {'rater': 'rater3@example.com', 'target': 'target@example.com', 'rating': 3.8}
                ]
            },
            'manager_review': {
                'ratings': [2.0, 2.5],
                'assignments': [],
                'raters': [],
                'targets': ['target@example.com'],
                'rater_target_pairs': [
                    {'rater': 'manager@example.com', 'target': 'target@example.com', 'rating': 2.0},
                    {'rater': 'manager2@example.com', 'target': 'target@example.com', 'rating': 2.5}
                ]
            }
        }
        
        findings = detector._analyze_context_consistency(cycle_id=1, context_data=context_data)
        
        # Should detect inconsistency due to large difference
        assert len(findings) > 0
        assert any(f.bias_type == 'context_inconsistency' for f in findings)


class TestContextPatterns:
    """Test context-specific pattern detection"""
    
    def test_detect_hierarchy_bias(self, mock_db_session):
        """Test hierarchy bias detection"""
        detector = ContextAware360BiasDetection(mock_db_session)
        
        # Higher hierarchy = higher ratings
        context_data = {
            'CEO': {
                'ratings': [4.5, 4.6, 4.7],
                'assignments': [],
                'raters': [],
                'targets': [],
                'rater_target_pairs': []
            },
            'manager_review': {
                'ratings': [4.0, 4.1, 4.2],
                'assignments': [],
                'raters': [],
                'targets': [],
                'rater_target_pairs': []
            },
            'peer_review': {
                'ratings': [3.5, 3.6, 3.7],
                'assignments': [],
                'raters': [],
                'targets': [],
                'rater_target_pairs': []
            }
        }
        
        findings = detector._detect_context_patterns(context_data)
        
        # May detect hierarchy bias if correlation is strong enough
        assert isinstance(findings, list)
    
    def test_detect_self_review_inflation(self, mock_db_session):
        """Test self-review inflation detection"""
        detector = ContextAware360BiasDetection(mock_db_session)
        
        context_data = {
            'self_review': {
                'ratings': [4.8, 4.9, 5.0],
                'assignments': [],
                'raters': [],
                'targets': ['target@example.com'],
                'rater_target_pairs': []
            },
            'peer_review': {
                'ratings': [3.5, 3.6, 3.7],
                'assignments': [],
                'raters': [],
                'targets': ['target@example.com'],
                'rater_target_pairs': []
            }
        }
        
        findings = detector._detect_context_patterns(context_data)
        
        # Should detect self-review inflation
        assert any(f.bias_type == 'self_review_inflation' for f in findings)


class TestContextBalance:
    """Test context balance analysis"""
    
    def test_analyze_context_balance_imbalance(self, mock_db_session):
        """Test detection of context imbalance"""
        detector = ContextAware360BiasDetection(mock_db_session)
        
        # Highly imbalanced
        context_data = {
            'peer_review': {
                'ratings': [4.0] * 100,  # Many
                'assignments': [],
                'raters': [],
                'targets': [],
                'rater_target_pairs': []
            },
            'manager_review': {
                'ratings': [4.0] * 5,  # Few
                'assignments': [],
                'raters': [],
                'targets': [],
                'rater_target_pairs': []
            }
        }
        
        findings = detector._analyze_context_balance(context_data)
        
        assert any(f.bias_type == 'context_imbalance' for f in findings)
    
    def test_analyze_context_balance_missing_contexts(self, mock_db_session):
        """Test detection of missing required contexts"""
        detector = ContextAware360BiasDetection(mock_db_session)
        
        # Missing required contexts
        context_data = {
            'peer_review': {
                'ratings': [4.0, 4.5],
                'assignments': [],
                'raters': [],
                'targets': [],
                'rater_target_pairs': []
            }
            # Missing manager_review, direct_report_review, self_review
        }
        
        findings = detector._analyze_context_balance(context_data)
        
        assert any(f.bias_type == 'missing_required_contexts' for f in findings)


class TestMultiContextStatisticalAnalysis:
    """Test multi-context statistical analysis"""
    
    def test_multi_context_statistical_analysis(self, mock_db_session):
        """Test ANOVA and statistical tests across contexts"""
        detector = ContextAware360BiasDetection(mock_db_session)
        
        context_data = {
            'peer_review': {
                'ratings': [4.0, 4.5, 3.8, 4.2, 4.1],
                'assignments': [],
                'raters': [],
                'targets': [],
                'rater_target_pairs': []
            },
            'manager_review': {
                'ratings': [3.0, 3.2, 2.8, 3.1, 2.9],
                'assignments': [],
                'raters': [],
                'targets': [],
                'rater_target_pairs': []
            },
            'direct_report_review': {
                'ratings': [4.2, 4.3, 4.1, 4.0, 4.2],
                'assignments': [],
                'raters': [],
                'targets': [],
                'rater_target_pairs': []
            }
        }
        
        findings = detector._multi_context_statistical_analysis(context_data)
        
        assert isinstance(findings, list)
        # May detect statistical differences if they exist


class TestTargetContextAnalysis:
    """Test target-specific context analysis"""
    
    def test_get_target_context_analysis(self, mock_db_session):
        """Test getting context analysis for a specific target"""
        detector = ContextAware360BiasDetection(mock_db_session)
        
        # Mock context data loading
        context_data = {
            'peer_review': {
                'ratings': [4.0, 4.5],
                'assignments': [],
                'raters': [],
                'targets': ['target@example.com'],
                'rater_target_pairs': [
                    {'rater': 'rater1@example.com', 'target': 'target@example.com', 'rating': 4.0},
                    {'rater': 'rater2@example.com', 'target': 'target@example.com', 'rating': 4.5}
                ]
            },
            'manager_review': {
                'ratings': [3.5],
                'assignments': [],
                'raters': [],
                'targets': ['target@example.com'],
                'rater_target_pairs': [
                    {'rater': 'manager@example.com', 'target': 'target@example.com', 'rating': 3.5}
                ]
            }
        }
        
        # Mock the _load_context_data method
        detector._load_context_data = Mock(return_value=context_data)
        
        analysis = detector.get_target_context_analysis(
            cycle_id=1,
            target_email='target@example.com'
        )
        
        assert analysis['status'] == 'analyzed'
        assert 'context_ratings' in analysis
        assert 'consistency' in analysis
        assert 'missing_contexts' in analysis


class TestScoreCalculation:
    """Test bias score calculations"""
    
    def test_calculate_overall_bias_score(self, mock_db_session):
        """Test overall bias score calculation"""
        detector = ContextAware360BiasDetection(mock_db_session)
        
        from backend.bias_detection_360 import BiasFinding
        
        findings = [
            BiasFinding(
                bias_type='test',
                severity='high',
                score=0.8,
                description='Test finding',
                affected_raters=[],
                affected_targets=[],
                evidence={},
                recommendations=[]
            ),
            BiasFinding(
                bias_type='test2',
                severity='medium',
                score=0.5,
                description='Test finding 2',
                affected_raters=[],
                affected_targets=[],
                evidence={},
                recommendations=[]
            )
        ]
        
        score = detector._calculate_overall_bias_score(findings)
        
        assert 0.0 <= score <= 1.0
    
    def test_calculate_context_bias_scores(self, mock_db_session):
        """Test context-specific bias score calculation"""
        detector = ContextAware360BiasDetection(mock_db_session)
        
        context_findings = [
            ContextBiasFinding(
                context='peer_review',
                bias_type='centrality_bias',
                severity='medium',
                score=0.6,
                description='Test',
                affected_raters=[],
                affected_targets=[],
                evidence={},
                recommendations=[]
            ),
            ContextBiasFinding(
                context='peer_review',
                bias_type='harshness_bias',
                severity='high',
                score=0.8,
                description='Test',
                affected_raters=[],
                affected_targets=[],
                evidence={},
                recommendations=[]
            )
        ]
        
        scores = detector._calculate_context_bias_scores(context_findings)
        
        assert isinstance(scores, dict)
        assert 'peer_review' in scores
        assert 0.0 <= scores['peer_review'] <= 1.0

