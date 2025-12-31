"""
AI-powered nomination suggestions for EOM (Employee of the Month) and other recognition programs.
Uses evaluation data to suggest candidates based on performance patterns.
"""
import numpy as np
from typing import List, Dict, Tuple
from collections import defaultdict
from backend.database import Person, Evaluation, Assignment, Cycle, EOMNominee


class NominationSuggester:
    """Suggests nominees based on evaluation patterns and performance metrics"""
    
    def __init__(self, db_session):
        self.db = db_session
    
    def suggest_eom_nominees(self, cycle_id: int, limit: int = 10) -> List[Dict]:
        """
        Suggest EOM nominees based on:
        - High average ratings
        - Consistent performance
        - Positive trend
        - Cross-context recognition (peers, managers, direct reports)
        """
        # Get all evaluations for the cycle
        evaluations = self.db.query(Evaluation).join(Assignment).filter(
            Assignment.cycle_id == cycle_id,
            Evaluation.status == 'submitted',
            Evaluation.rating.isnot(None)
        ).all()
        
        if len(evaluations) < 5:
            return []
        
        # Aggregate by target
        target_stats = defaultdict(lambda: {
            'ratings': [],
            'contexts': set(),
            'raters': set(),
            'comments': []
        })
        
        for eval in evaluations:
            assignment = self.db.query(Assignment).filter(
                Assignment.id == eval.assignment_id
            ).first()
            if assignment:
                target_stats[assignment.target_email]['ratings'].append(eval.rating)
                target_stats[assignment.target_email]['contexts'].add(assignment.rater_context)
                target_stats[assignment.target_email]['raters'].add(assignment.rater_email)
                if eval.comments:
                    target_stats[assignment.target_email]['comments'].append(eval.comments)
        
        # Calculate scores for each target
        suggestions = []
        for target_email, stats in target_stats.items():
            if len(stats['ratings']) < 2:  # Need at least 2 evaluations
                continue
            
            ratings = np.array(stats['ratings'])
            
            # Scoring factors
            avg_rating = float(np.mean(ratings))
            consistency = 1.0 / (1.0 + float(np.std(ratings)))  # Higher for lower std
            diversity = len(stats['contexts'])  # More contexts = better
            volume = len(stats['ratings'])  # More evaluations = more recognition
            
            # Composite score
            score = (
                avg_rating * 0.4 +  # Average rating (40%)
                consistency * 2.0 * 0.2 +  # Consistency (20%)
                diversity * 0.5 * 0.2 +  # Context diversity (20%)
                min(volume / 10.0, 1.0) * 0.2  # Volume (20%, capped)
            )
            
            # Get person details
            person = self.db.query(Person).filter(Person.email == target_email).first()
            
            suggestions.append({
                'email': target_email,
                'full_name': person.full_name if person else target_email,
                'role_title': person.role_title if person else None,
                'score': score,
                'avg_rating': avg_rating,
                'rating_count': len(ratings),
                'consistency': float(np.std(ratings)),
                'context_diversity': diversity,
                'contexts': list(stats['contexts']),
                'reasons': self._extract_reasons(stats['comments'])
            })
        
        # Sort by score and return top N
        suggestions.sort(key=lambda x: x['score'], reverse=True)
        return suggestions[:limit]
    
    def _extract_reasons(self, comments: List[str]) -> List[str]:
        """Extract key reasons from comments (simplified - could use NLP)"""
        # Simple keyword extraction
        positive_keywords = [
            'excellent', 'outstanding', 'great', 'amazing', 'helpful',
            'dedicated', 'hardworking', 'collaborative', 'innovative',
            'leadership', 'mentor', 'supportive', 'reliable'
        ]
        
        reasons = []
        for comment in comments[:3]:  # Limit to first 3 comments
            if comment:
                comment_lower = comment.lower()
                found_keywords = [kw for kw in positive_keywords if kw in comment_lower]
                if found_keywords:
                    reasons.append(f"Recognized for: {', '.join(found_keywords[:3])}")
        
        return reasons[:3]  # Return top 3 reasons
    
    def suggest_peer_nominees(self, cycle_id: int, rater_email: str, limit: int = 5) -> List[Dict]:
        """
        Suggest nominees based on peer evaluations.
        Focuses on peer-to-peer recognition.
        """
        # Get peer evaluations
        evaluations = self.db.query(Evaluation).join(Assignment).filter(
            Assignment.cycle_id == cycle_id,
            Assignment.rater_context == 'peer_review',
            Evaluation.status == 'submitted',
            Evaluation.rating.isnot(None)
        ).all()
        
        # Aggregate by target
        target_ratings = defaultdict(list)
        for eval in evaluations:
            assignment = self.db.query(Assignment).filter(
                Assignment.id == eval.assignment_id
            ).first()
            if assignment:
                target_ratings[assignment.target_email].append(eval.rating)
        
        # Calculate scores
        suggestions = []
        for target_email, ratings in target_ratings.items():
            if len(ratings) >= 2:
                avg_rating = float(np.mean(ratings))
                person = self.db.query(Person).filter(Person.email == target_email).first()
                
                suggestions.append({
                    'email': target_email,
                    'full_name': person.full_name if person else target_email,
                    'avg_peer_rating': avg_rating,
                    'peer_count': len(ratings)
                })
        
        suggestions.sort(key=lambda x: x['avg_peer_rating'], reverse=True)
        return suggestions[:limit]
    
    def detect_rising_stars(self, cycle_id: int, previous_cycle_id: int = None, limit: int = 5) -> List[Dict]:
        """
        Detect employees showing significant improvement.
        Compares current cycle with previous cycle.
        """
        if previous_cycle_id is None:
            # Try to find previous cycle
            current_cycle = self.db.query(Cycle).filter(Cycle.id == cycle_id).first()
            if current_cycle:
                previous_cycles = self.db.query(Cycle).filter(
                    Cycle.end_date < current_cycle.start_date
                ).order_by(Cycle.end_date.desc()).limit(1).all()
                if previous_cycles:
                    previous_cycle_id = previous_cycles[0].id
                else:
                    return []
            else:
                return []
        
        # Get current cycle ratings
        current_evaluations = self.db.query(Evaluation).join(Assignment).filter(
            Assignment.cycle_id == cycle_id,
            Evaluation.status == 'submitted',
            Evaluation.rating.isnot(None)
        ).all()
        
        # Get previous cycle ratings
        previous_evaluations = self.db.query(Evaluation).join(Assignment).filter(
            Assignment.cycle_id == previous_cycle_id,
            Evaluation.status == 'submitted',
            Evaluation.rating.isnot(None)
        ).all()
        
        # Aggregate by target
        current_ratings = defaultdict(list)
        previous_ratings = defaultdict(list)
        
        for eval in current_evaluations:
            assignment = self.db.query(Assignment).filter(
                Assignment.id == eval.assignment_id
            ).first()
            if assignment:
                current_ratings[assignment.target_email].append(eval.rating)
        
        for eval in previous_evaluations:
            assignment = self.db.query(Assignment).filter(
                Assignment.id == eval.assignment_id
            ).first()
            if assignment:
                previous_ratings[assignment.target_email].append(eval.rating)
        
        # Find improvements
        rising_stars = []
        for email in current_ratings.keys():
            if email in previous_ratings:
                current_avg = float(np.mean(current_ratings[email]))
                previous_avg = float(np.mean(previous_ratings[email]))
                improvement = current_avg - previous_avg
                
                if improvement > 0.3:  # Significant improvement
                    person = self.db.query(Person).filter(Person.email == email).first()
                    rising_stars.append({
                        'email': email,
                        'full_name': person.full_name if person else email,
                        'current_avg': current_avg,
                        'previous_avg': previous_avg,
                        'improvement': improvement,
                        'improvement_pct': (improvement / previous_avg * 100) if previous_avg > 0 else 0
                    })
        
        rising_stars.sort(key=lambda x: x['improvement'], reverse=True)
        return rising_stars[:limit]

