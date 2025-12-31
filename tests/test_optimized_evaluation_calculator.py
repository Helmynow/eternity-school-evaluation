"""
Unit tests for Optimized Evaluation Calculator.
Tests performance optimizations for 200+ staff members.
"""
import pytest
import numpy as np
import pandas as pd
from unittest.mock import Mock, MagicMock
from backend.optimized_evaluation_calculator import OptimizedEvaluationCalculator
from backend.database import Person, Assignment, Evaluation


@pytest.fixture
def mock_db_session():
    """Create a mock database session"""
    return Mock()


@pytest.fixture
def sample_people():
    """Create sample people data"""
    return [
        Mock(spec=Person, email=f'person{i}@eternity.edu', 
             role_title='Teacher' if i % 2 == 0 else 'Coordinator',
             department='Academics' if i % 2 == 0 else 'Administration',
             active=True)
        for i in range(10)
    ]


class TestBulkDataLoading:
    """Test bulk data loading optimizations"""
    
    def test_load_all_data_bulk(self, mock_db_session):
        """Test bulk loading of all evaluation data"""
        calculator = OptimizedEvaluationCalculator(mock_db_session)
        
        # Mock query results
        mock_eval_data = [
            Mock(
                id=i,
                assignment_id=i,
                rating=4.0 + (i * 0.1),
                rater_email=f'rater{i}@eternity.edu',
                target_email=f'target{i%5}@eternity.edu',
                rater_context='peer_review',
                target_group='academic',
                assignment_weight=1.0
            )
            for i in range(20)
        ]
        
        mock_person_data = [
            Mock(
                email=f'target{i}@eternity.edu',
                full_name=f'Person {i}',
                role_title='Teacher',
                department='Academics',
                segment=Mock(value='NATIONAL'),
                active=True
            )
            for i in range(5)
        ]
        
        # Mock query chain
        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.join.return_value = query_mock
        query_mock.all.return_value = mock_eval_data
        
        mock_db_session.query.return_value = query_mock
        
        # Mock people query
        people_query_mock = MagicMock()
        people_query_mock.filter.return_value = people_query_mock
        people_query_mock.all.return_value = mock_person_data
        
        def query_side_effect(model):
            if model == Evaluation:
                return query_mock
            elif model == Person:
                return people_query_mock
            return query_mock
        
        mock_db_session.query.side_effect = query_side_effect
        
        eval_df, people_df = calculator._load_all_data_bulk(cycle_id=1)
        
        assert not eval_df.empty
        assert not people_df.empty
        assert len(eval_df) == 20
        assert len(people_df) == 5


class TestVectorizedOperations:
    """Test vectorized operations"""
    
    def test_apply_weights_vectorized(self, mock_db_session):
        """Test vectorized weight application"""
        calculator = OptimizedEvaluationCalculator(mock_db_session)
        
        # Create sample DataFrame
        eval_df = pd.DataFrame({
            'target_email': ['person1@eternity.edu', 'person2@eternity.edu'],
            'rater_context': ['peer_review', 'manager_review'],
            'rating': [4.0, 4.5],
            'assignment_weight': [1.0, 1.0]
        })
        
        people_df = pd.DataFrame({
            'email': ['person1@eternity.edu', 'person2@eternity.edu'],
            'role_title': ['Teacher', 'Coordinator']
        })
        
        # Set staff type cache
        calculator._staff_type_cache = {
            'person1@eternity.edu': 'academic',
            'person2@eternity.edu': 'admin'
        }
        
        result_df = calculator._apply_weights_vectorized(eval_df, people_df)
        
        assert 'base_weight' in result_df.columns
        assert 'weighted_score' in result_df.columns
        assert 'staff_type' in result_df.columns
        assert len(result_df) == 2


class TestBatchProcessing:
    """Test optimized batch processing"""
    
    def test_calculate_batch_scores_optimized(self, mock_db_session):
        """Test optimized batch score calculation"""
        calculator = OptimizedEvaluationCalculator(mock_db_session)
        
        # Mock bulk data loading
        eval_df = pd.DataFrame({
            'target_email': ['person1@eternity.edu', 'person1@eternity.edu', 'person2@eternity.edu'],
            'rater_context': ['peer_review', 'manager_review', 'peer_review'],
            'rating': [4.0, 4.5, 3.8],
            'assignment_weight': [1.0, 1.0, 1.0]
        })
        
        people_df = pd.DataFrame({
            'email': ['person1@eternity.edu', 'person2@eternity.edu'],
            'role_title': ['Teacher', 'Coordinator']
        })
        
        calculator._load_all_data_bulk = Mock(return_value=(eval_df, people_df))
        calculator._staff_type_cache = {
            'person1@eternity.edu': 'academic',
            'person2@eternity.edu': 'admin'
        }
        
        scores = calculator.calculate_batch_scores_optimized(cycle_id=1)
        
        assert len(scores) == 2
        assert all(isinstance(s, calculator.OptimizedScore) for s in scores)
        assert all(s.weighted_average > 0 for s in scores)


class TestStatistics:
    """Test statistics calculation"""
    
    def test_get_score_statistics(self, mock_db_session):
        """Test getting aggregate statistics"""
        calculator = OptimizedEvaluationCalculator(mock_db_session)
        
        # Mock scores
        scores = [
            calculator.OptimizedScore(
                target_email=f'person{i}@eternity.edu',
                staff_type='academic',
                total_evaluations=3,
                raw_average=4.0 + (i * 0.1),
                weighted_average=4.2 + (i * 0.1),
                final_score=4.2 + (i * 0.1),
                context_breakdown={}
            )
            for i in range(10)
        ]
        
        calculator.calculate_batch_scores_optimized = Mock(return_value=scores)
        
        stats = calculator.get_score_statistics(cycle_id=1)
        
        assert stats['count'] == 10
        assert 'mean' in stats
        assert 'median' in stats
        assert 'std' in stats
        assert 'min' in stats
        assert 'max' in stats


class TestComparison:
    """Test comparison operations"""
    
    def test_compare_academic_vs_admin_optimized(self, mock_db_session):
        """Test optimized academic vs admin comparison"""
        calculator = OptimizedEvaluationCalculator(mock_db_session)
        
        # Mock scores
        scores = [
            calculator.OptimizedScore(
                target_email=f'person{i}@eternity.edu',
                staff_type='academic' if i % 2 == 0 else 'admin',
                total_evaluations=3,
                raw_average=4.0,
                weighted_average=4.2 if i % 2 == 0 else 3.8,
                final_score=4.2 if i % 2 == 0 else 3.8,
                context_breakdown={}
            )
            for i in range(10)
        ]
        
        calculator.calculate_batch_scores_optimized = Mock(return_value=scores)
        
        comparison = calculator.compare_academic_vs_admin_optimized(cycle_id=1)
        
        assert 'academic_stats' in comparison
        assert 'admin_stats' in comparison
        assert 'differences' in comparison
        assert 'recommendations' in comparison


class TestCaching:
    """Test caching mechanisms"""
    
    def test_staff_type_caching(self, mock_db_session):
        """Test staff type lookup caching"""
        calculator = OptimizedEvaluationCalculator(mock_db_session)
        
        person = Mock(spec=Person)
        person.email = 'test@eternity.edu'
        person.role_title = 'Teacher'
        person.department = None
        
        # First call should determine and cache
        staff_type1 = calculator._get_staff_type_cached(person)
        
        # Second call should use cache
        staff_type2 = calculator._get_staff_type_cached(person)
        
        assert staff_type1 == staff_type2
        assert person.email in calculator._staff_type_cache
    
    def test_clear_cache(self, mock_db_session):
        """Test cache clearing"""
        calculator = OptimizedEvaluationCalculator(mock_db_session)
        
        calculator._staff_type_cache['test@eternity.edu'] = 'academic'
        
        calculator.clear_cache()
        
        assert len(calculator._staff_type_cache) == 0


class TestDataFrameExport:
    """Test DataFrame export"""
    
    def test_export_scores_to_dataframe(self, mock_db_session):
        """Test exporting scores to DataFrame"""
        calculator = OptimizedEvaluationCalculator(mock_db_session)
        
        scores = [
            calculator.OptimizedScore(
                target_email=f'person{i}@eternity.edu',
                staff_type='academic',
                total_evaluations=3,
                raw_average=4.0,
                weighted_average=4.2,
                final_score=4.2,
                context_breakdown={}
            )
            for i in range(5)
        ]
        
        calculator.calculate_batch_scores_optimized = Mock(return_value=scores)
        
        df = calculator.export_scores_to_dataframe(cycle_id=1)
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 5
        assert 'target_email' in df.columns
        assert 'weighted_average' in df.columns

