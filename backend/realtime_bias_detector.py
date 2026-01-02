"""
Real-time bias detection for individual evaluations.
Provides immediate feedback during evaluation submission.
"""
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import logging
from backend.database import Evaluation, Assignment, Person, Cycle
from backend.bias_detection import BiasDetector


class HistoricalBiasTracker:
    """Tracks historical bias patterns for comparison"""
    
    def __init__(self, db_session):
        self.db = db_session
        self.logger = logging.getLogger(__name__)
    
    def get_rater_history(self, rater_email: str, cycle_id: int) -> Dict:
        """Get historical evaluation patterns for a rater"""
        # Get previous evaluations by this rater
        previous_evals = (
            self.db.query(Evaluation)
            .join(Assignment)
            .filter(
                Assignment.rater_email == rater_email,
                Assignment.cycle_id != cycle_id,
                Evaluation.status == 'submitted',
                Evaluation.rating.isnot(None)
            )
            .all()
        )
        
        if not previous_evals:
            return {'status': 'no_history', 'ratings': []}
        
        ratings = [e.rating for e in previous_evals]
        return {
            'status': 'has_history',
            'ratings': ratings,
            'mean_rating': float(np.mean(ratings)),
            'std_rating': float(np.std(ratings)),
            'count': len(ratings)
        }
    
    def get_target_history(self, target_email: str, cycle_id: int) -> Dict:
        """Get historical evaluation patterns for a target"""
        previous_evals = (
            self.db.query(Evaluation)
            .join(Assignment)
            .filter(
                Assignment.target_email == target_email,
                Assignment.cycle_id != cycle_id,
                Evaluation.status == 'submitted',
                Evaluation.rating.isnot(None)
            )
            .all()
        )
        
        if not previous_evals:
            return {'status': 'no_history', 'ratings': []}
        
        ratings = [e.rating for e in previous_evals]
        return {
            'status': 'has_history',
            'ratings': ratings,
            'mean_rating': float(np.mean(ratings)),
            'std_rating': float(np.std(ratings)),
            'count': len(ratings)
        }


class RealTimeBiasDetector:
    """
    Real-time bias detection for individual evaluations.
    Analyzes evaluations as they are submitted to provide immediate feedback.
    """
    
    def __init__(self, db_session):
        self.db = db_session
        self.historical_biases = HistoricalBiasTracker(db_session)
        self.bias_detector = BiasDetector(db_session)
        self.logger = logging.getLogger(__name__)
    
    def analyze_evaluation(
        self, 
        evaluation_data: Dict,
        cycle_id: int
    ) -> Dict:
        """
        Analyze a single evaluation for bias in real-time.
        
        Args:
            evaluation_data: Dictionary containing:
                - assignment_id: ID of the assignment
                - rating: The rating score (1-10)
                - domain_scores: Optional dict of domain-specific scores
                - submitted_at: Timestamp of submission
            cycle_id: Current evaluation cycle ID
        
        Returns:
            Dictionary with bias analysis results
        """
        assignment_id = evaluation_data.get('assignment_id')
        rating = evaluation_data.get('rating')
        domain_scores = evaluation_data.get('domain_scores', {})
        submitted_at = evaluation_data.get('submitted_at', datetime.utcnow())
        
        if not assignment_id or rating is None:
            return {
                'status': 'error',
                'message': 'Missing required evaluation data'
            }
        
        # Get assignment details
        assignment = self.db.query(Assignment).filter(
            Assignment.id == assignment_id
        ).first()
        
        if not assignment:
            return {
                'status': 'error',
                'message': 'Assignment not found'
            }
        
        # Get all evaluations for this target in this cycle (for comparison)
        target_evaluations = (
            self.db.query(Evaluation)
            .join(Assignment)
            .filter(
                Assignment.cycle_id == cycle_id,
                Assignment.target_email == assignment.target_email,
                Evaluation.status == 'submitted',
                Evaluation.rating.isnot(None)
            )
            .all()
        )
        
        # Analyze different types of bias
        similarity_bias_score = self.check_halo_effect(
            assignment, rating, domain_scores, target_evaluations
        )
        
        recency_bias = self.check_recency_bias(
            assignment, rating, submitted_at, cycle_id
        )
        
        department_bias = self.check_department_bias(
            assignment, rating, target_evaluations
        )
        
        # Generate mitigation suggestions
        bias_mitigation_suggestions = self.generate_mitigation_suggestions(
            similarity_bias_score, recency_bias, department_bias
        )
        
        # Calculate overall fairness score
        fairness_score = self.calculate_fairness_score(
            similarity_bias_score, recency_bias, department_bias
        )
        
        return {
            'status': 'analyzed',
            'similarity_bias_score': similarity_bias_score,
            'recency_bias': recency_bias,
            'department_bias': department_bias,
            'bias_mitigation_suggestions': bias_mitigation_suggestions,
            'fairness_score': fairness_score,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def check_halo_effect(
        self,
        assignment: Assignment,
        rating: float,
        domain_scores: Dict,
        target_evaluations: List[Evaluation]
    ) -> Dict:
        """
        Check for halo effect (similarity bias) - similar scores across domains.
        
        Returns:
            Dictionary with similarity bias analysis
        """
        # If domain scores are provided, check variance
        if domain_scores:
            domain_values = list(domain_scores.values())
            if len(domain_values) > 1:
                variance = float(np.var(domain_values))
                std_dev = float(np.std(domain_values))
                
                # Low variance indicates halo effect
                if variance < 0.5:  # Threshold for low variance
                    return {
                        'detected': True,
                        'severity': 'high' if variance < 0.2 else 'medium',
                        'variance': variance,
                        'std_dev': std_dev,
                        'message': 'Halo effect detected: scores are too similar across domains',
                        'score': max(0, 1.0 - variance * 2)  # Lower score = more bias
                    }
        
        # Check against other evaluations for this target
        if len(target_evaluations) > 0:
            other_ratings = [e.rating for e in target_evaluations]
            avg_other_ratings = np.mean(other_ratings)
            
            # If this rating is very similar to all others, might indicate halo
            rating_diff = abs(rating - avg_other_ratings)
            if rating_diff < 0.5 and len(other_ratings) >= 3:
                return {
                    'detected': True,
                    'severity': 'low',
                    'variance': rating_diff,
                    'message': 'Rating is very similar to other evaluations (possible halo effect)',
                    'score': 0.7
                }
        
        return {
            'detected': False,
            'severity': 'none',
            'message': 'No significant halo effect detected',
            'score': 1.0
        }
    
    def check_recency_bias(
        self,
        assignment: Assignment,
        rating: float,
        submitted_at: datetime,
        cycle_id: int
    ) -> Dict:
        """
        Check for recency bias - correlation between submission timing and rating.
        
        Returns:
            Dictionary with recency bias analysis
        """
        # Get cycle dates
        cycle = self.db.query(Cycle).filter(Cycle.id == cycle_id).first()
        if not cycle or not cycle.start_date:
            return {
                'detected': False,
                'message': 'Cycle dates not available',
                'score': 1.0
            }
        
        # Calculate days since cycle start
        if isinstance(submitted_at, str):
            submitted_at = datetime.fromisoformat(submitted_at.replace('Z', '+00:00'))
        
        days_since_start = (submitted_at.date() - cycle.start_date).days
        
        # Get all evaluations in this cycle with submission dates
        all_evaluations = (
            self.db.query(Evaluation)
            .join(Assignment)
            .filter(
                Assignment.cycle_id == cycle_id,
                Evaluation.status == 'submitted',
                Evaluation.rating.isnot(None),
                Evaluation.submitted_at.isnot(None)
            )
            .all()
        )
        
        if len(all_evaluations) < 10:
            return {
                'detected': False,
                'message': 'Insufficient data for recency analysis',
                'score': 1.0
            }
        
        # Compare early vs late submissions
        early_evaluations = [
            e for e in all_evaluations 
            if e.submitted_at and (e.submitted_at.date() - cycle.start_date).days < 30
        ]
        late_evaluations = [
            e for e in all_evaluations 
            if e.submitted_at and (e.submitted_at.date() - cycle.start_date).days >= 30
        ]
        
        if len(early_evaluations) > 0 and len(late_evaluations) > 0:
            early_avg = np.mean([e.rating for e in early_evaluations])
            late_avg = np.mean([e.rating for e in late_evaluations])
            diff = late_avg - early_avg
            
            # If late submissions are significantly higher, possible recency bias
            if diff > 1.0:  # More than 1 point difference
                return {
                    'detected': True,
                    'severity': 'high' if diff > 2.0 else 'medium',
                    'early_avg': float(early_avg),
                    'late_avg': float(late_avg),
                    'difference': float(diff),
                    'days_since_start': days_since_start,
                    'message': f'Recency bias detected: late submissions average {diff:.2f} points higher',
                    'score': max(0, 1.0 - abs(diff) / 5.0)
                }
        
        return {
            'detected': False,
            'message': 'No significant recency bias detected',
            'score': 1.0
        }
    
    def check_department_bias(
        self,
        assignment: Assignment,
        rating: float,
        target_evaluations: List[Evaluation]
    ) -> Dict:
        """
        Check for department/segment bias - differences across departments.
        
        Returns:
            Dictionary with department bias analysis
        """
        # Get target person's department/segment
        target_person = self.db.query(Person).filter(
            Person.email == assignment.target_email
        ).first()
        
        if not target_person:
            return {
                'detected': False,
                'message': 'Target person not found',
                'score': 1.0
            }
        
        # Get all evaluations grouped by target department/segment
        if len(target_evaluations) < 5:
            return {
                'detected': False,
                'message': 'Insufficient data for department analysis',
                'score': 1.0
            }
        
        # Group evaluations by target segment
        segment_ratings = defaultdict(list)
        for eval in target_evaluations:
            eval_assignment = self.db.query(Assignment).filter(
                Assignment.id == eval.assignment_id
            ).first()
            if eval_assignment:
                target_p = self.db.query(Person).filter(
                    Person.email == eval_assignment.target_email
                ).first()
                if target_p and target_p.segment:
                    segment_ratings[target_p.segment.value].append(eval.rating)
        
        # Compare current rating to segment average
        if target_person.segment and target_person.segment.value in segment_ratings:
            segment_avg = np.mean(segment_ratings[target_person.segment.value])
            rating_diff = abs(rating - segment_avg)
            
            # If rating differs significantly from segment average
            if rating_diff > 2.0:
                return {
                    'detected': True,
                    'severity': 'high' if rating_diff > 3.0 else 'medium',
                    'segment': target_person.segment.value,
                    'segment_avg': float(segment_avg),
                    'rating_diff': float(rating_diff),
                    'message': f'Rating differs significantly from {target_person.segment.value} segment average',
                    'score': max(0, 1.0 - rating_diff / 5.0)
                }
        
        return {
            'detected': False,
            'message': 'No significant department bias detected',
            'score': 1.0
        }
    
    def generate_mitigation_suggestions(
        self,
        similarity_bias: Dict,
        recency_bias: Dict,
        department_bias: Dict
    ) -> List[str]:
        """
        Generate suggestions to mitigate detected biases.
        
        Returns:
            List of mitigation suggestions
        """
        suggestions = []
        
        # Similarity bias suggestions
        if similarity_bias.get('detected'):
            if similarity_bias.get('severity') == 'high':
                suggestions.append(
                    "Consider differentiating scores across evaluation domains. "
                    "Each domain should reflect distinct aspects of performance."
                )
            else:
                suggestions.append(
                    "Review domain scores to ensure they reflect different aspects of performance."
                )
        
        # Recency bias suggestions
        if recency_bias.get('detected'):
            suggestions.append(
                "Consider reviewing performance over the entire evaluation period, "
                "not just recent events. Document specific examples from throughout the period."
            )
        
        # Department bias suggestions
        if department_bias.get('detected'):
            suggestions.append(
                f"Ensure evaluation is based on objective performance criteria, "
                f"not department/segment affiliation. Compare against role-specific standards."
            )
        
        # General suggestions if no specific bias detected
        if not suggestions:
            suggestions.append(
                "Continue to evaluate based on objective criteria and documented evidence."
            )
        
        return suggestions
    
    def calculate_fairness_score(
        self,
        similarity_bias: Dict,
        recency_bias: Dict,
        department_bias: Dict
    ) -> Dict:
        """
        Calculate overall fairness score based on all bias checks.
        Applies weights to different bias types.
        
        Returns:
            Dictionary with fairness score and breakdown
        """
        # Weights for different bias types
        weights = {
            'similarity': 0.4,  # Halo effect is most important
            'recency': 0.3,
            'department': 0.3
        }
        
        # Get scores (1.0 = no bias, 0.0 = high bias)
        similarity_score = similarity_bias.get('score', 1.0)
        recency_score = recency_bias.get('score', 1.0)
        department_score = department_bias.get('score', 1.0)
        
        # Calculate weighted average
        weighted_score = (
            similarity_score * weights['similarity'] +
            recency_score * weights['recency'] +
            department_score * weights['department']
        )
        
        # Convert to 0-100 scale
        fairness_percentage = weighted_score * 100
        
        # Determine rating
        if fairness_percentage >= 80:
            rating = 'excellent'
        elif fairness_percentage >= 60:
            rating = 'good'
        elif fairness_percentage >= 40:
            rating = 'fair'
        else:
            rating = 'needs_improvement'
        
        return {
            'overall_score': float(weighted_score),
            'percentage': float(fairness_percentage),
            'rating': rating,
            'breakdown': {
                'similarity_bias': {
                    'score': similarity_score,
                    'weight': weights['similarity'],
                    'weighted_contribution': similarity_score * weights['similarity']
                },
                'recency_bias': {
                    'score': recency_score,
                    'weight': weights['recency'],
                    'weighted_contribution': recency_score * weights['recency']
                },
                'department_bias': {
                    'score': department_score,
                    'weight': weights['department'],
                    'weighted_contribution': department_score * weights['department']
                }
            }
        }
