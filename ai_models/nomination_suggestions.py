"""
AI-powered nomination suggestions for EOM (Employee of the Month) and other recognition programs.
Uses evaluation data to suggest candidates based on performance patterns.
"""
import numpy as np
from typing import List, Dict, Tuple, Optional
from collections import defaultdict
from datetime import datetime, timedelta
from backend.database import Person, Evaluation, Assignment, Cycle, EOMNominee, EOMCategory, EOMCycle


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
    
    def suggest_candidates(self, category: str, cycle_id: Optional[int] = None, limit: int = 5) -> List[str]:
        """
        Suggest candidates who might be overlooked for a specific EOM category.
        
        Args:
            category: EOM category name (e.g., "Team Spirit", "Outstanding Leadership")
            cycle_id: Optional cycle ID. If None, uses current cycle
            limit: Maximum number of suggestions to return
        
        Returns:
            List of suggestion strings in format: "Consider nominating [Name] - [reason]"
        """
        # Resolve cycle ID
        if cycle_id is None:
            current_cycle = self.db.query(Cycle).filter(
                Cycle.is_active == True
            ).first()
            if not current_cycle:
                return []
            cycle_id = current_cycle.id
        
        # Map category string to enum
        category_map = {
            'team_spirit': EOMCategory.TEAM_SPIRIT,
            'outstanding_leadership': EOMCategory.OUTSTANDING_LEADERSHIP,
            'innovation': EOMCategory.INNOVATION,
            'rising_star': EOMCategory.RISING_STAR,
            'service_excellence': EOMCategory.SERVICE_EXCELLENCE,
        }
        
        category_lower = category.lower().replace(' ', '_')
        eom_category = category_map.get(category_lower)
        
        if not eom_category:
            return []
        
        # Get all staff
        all_staff = self.db.query(Person).all()
        
        # Get recent nominations to identify overlooked candidates
        recent_nominations = self.db.query(EOMNominee).join(EOMCycle).filter(
            EOMCycle.cycle_id == cycle_id
        ).all()
        recently_nominated_emails = {n.nominee_email for n in recent_nominations}
        
        # Get evaluations for the cycle
        evaluations = self.db.query(Evaluation).join(Assignment).filter(
            Assignment.cycle_id == cycle_id,
            Evaluation.status == 'submitted',
            Evaluation.rating.isnot(None)
        ).all()
        
        if len(evaluations) < 5:
            return []
        
        # Analyze candidates for the specific category
        candidate_scores = []
        
        for person in all_staff:
            # Skip if already nominated
            if person.email in recently_nominated_emails:
                continue
            
            # Get person's evaluations
            person_evaluations = [
                e for e in evaluations
                for a in [self.db.query(Assignment).filter(Assignment.id == e.assignment_id).first()]
                if a and a.target_email == person.email
            ]
            
            if len(person_evaluations) < 2:
                continue
            
            # Calculate category-specific metrics
            category_score, reason = self._calculate_category_fit(
                person, person_evaluations, eom_category, cycle_id
            )
            
            if category_score > 0.5:  # Only suggest if score is above threshold
                candidate_scores.append({
                    'person': person,
                    'score': category_score,
                    'reason': reason
                })
        
        # Sort by score and generate suggestions
        candidate_scores.sort(key=lambda x: x['score'], reverse=True)
        
        suggestions = []
        for candidate in candidate_scores[:limit]:
            person = candidate['person']
            reason = candidate['reason']
            name = person.full_name or person.email.split('@')[0]
            suggestions.append(f"Consider nominating {name} - {reason}")
        
        return suggestions
    
    def _calculate_category_fit(
        self,
        person: Person,
        evaluations: List[Evaluation],
        category: EOMCategory,
        cycle_id: int
    ) -> Tuple[float, str]:
        """
        Calculate how well a person fits a specific EOM category.
        
        Returns:
            Tuple of (score: float, reason: str)
        """
        # Get assignment details for evaluations
        assignments = []
        ratings = []
        comments = []
        
        for eval in evaluations:
            assignment = self.db.query(Assignment).filter(
                Assignment.id == eval.assignment_id
            ).first()
            if assignment:
                assignments.append(assignment)
                ratings.append(eval.rating)
                if eval.comments:
                    comments.append(eval.comments)
        
        if not ratings:
            return 0.0, ""
        
        ratings_array = np.array(ratings)
        avg_rating = float(np.mean(ratings_array))
        
        # Category-specific analysis
        if category == EOMCategory.TEAM_SPIRIT:
            return self._analyze_team_spirit(person, assignments, ratings, comments, avg_rating)
        elif category == EOMCategory.OUTSTANDING_LEADERSHIP:
            return self._analyze_leadership(person, assignments, ratings, comments, avg_rating)
        elif category == EOMCategory.INNOVATION:
            return self._analyze_innovation(person, assignments, ratings, comments, avg_rating)
        elif category == EOMCategory.RISING_STAR:
            return self._analyze_rising_star(person, assignments, ratings, comments, avg_rating, cycle_id)
        elif category == EOMCategory.SERVICE_EXCELLENCE:
            return self._analyze_service_excellence(person, assignments, ratings, comments, avg_rating)
        else:
            return 0.0, ""
    
    def _analyze_team_spirit(
        self,
        person: Person,
        assignments: List[Assignment],
        ratings: List[float],
        comments: List[str],
        avg_rating: float
    ) -> Tuple[float, str]:
        """Analyze candidate for Team Spirit category"""
        # Check for peer collaboration indicators
        peer_assignments = [a for a in assignments if a.rater_context == 'peer_review']
        peer_ratings = [
            ratings[i] for i, a in enumerate(assignments)
            if a.rater_context == 'peer_review'
        ]
        
        # Analyze comments for collaboration keywords
        collaboration_keywords = [
            'helped', 'supported', 'collaborated', 'teamwork', 'assisted',
            'cooperative', 'team player', 'worked together', 'shared'
        ]
        
        collaboration_score = 0.0
        found_keywords = []
        
        for comment in comments:
            comment_lower = comment.lower() if comment else ""
            for keyword in collaboration_keywords:
                if keyword in comment_lower:
                    collaboration_score += 0.1
                    if keyword not in found_keywords:
                        found_keywords.append(keyword)
        
        # Calculate peer collaboration score
        peer_score = 0.0
        if peer_ratings:
            peer_avg = float(np.mean(peer_ratings))
            peer_score = peer_avg / 5.0  # Normalize to 0-1
        
        # Composite score
        score = (
            avg_rating / 5.0 * 0.4 +  # Overall rating (40%)
            min(collaboration_score, 1.0) * 0.4 +  # Collaboration indicators (40%)
            peer_score * 0.2  # Peer ratings (20%)
        )
        
        # Generate reason
        reasons = []
        if peer_ratings and len(peer_ratings) >= 3:
            peer_avg = float(np.mean(peer_ratings))
            reasons.append(f"high peer collaboration score ({peer_avg:.1f}/5.0)")
        if collaboration_score > 0.3:
            reasons.append("strong collaboration indicators in evaluations")
        if avg_rating >= 4.0:
            reasons.append("consistently high ratings from colleagues")
        
        reason = ", ".join(reasons) if reasons else "strong team collaboration performance"
        
        return float(score), reason
    
    def _analyze_leadership(
        self,
        person: Person,
        assignments: List[Assignment],
        ratings: List[float],
        comments: List[str],
        avg_rating: float
    ) -> Tuple[float, str]:
        """Analyze candidate for Outstanding Leadership category"""
        # Check for leadership indicators
        leadership_keywords = [
            'led', 'managed', 'initiated', 'coordinated', 'directed',
            'mentored', 'guided', 'strategic', 'vision', 'decision'
        ]
        
        leadership_score = 0.0
        found_keywords = []
        
        for comment in comments:
            comment_lower = comment.lower() if comment else ""
            for keyword in leadership_keywords:
                if keyword in comment_lower:
                    leadership_score += 0.15
                    if keyword not in found_keywords:
                        found_keywords.append(keyword)
        
        # Check manager/direct report context ratings
        manager_ratings = [
            ratings[i] for i, a in enumerate(assignments)
            if a.rater_context in ['manager_review', 'direct_report_review']
        ]
        
        manager_score = 0.0
        if manager_ratings:
            manager_avg = float(np.mean(manager_ratings))
            manager_score = manager_avg / 5.0
        
        # Composite score
        score = (
            avg_rating / 5.0 * 0.3 +  # Overall rating (30%)
            min(leadership_score, 1.0) * 0.5 +  # Leadership indicators (50%)
            manager_score * 0.2  # Manager/direct report ratings (20%)
        )
        
        # Generate reason
        reasons = []
        if leadership_score > 0.3:
            reasons.append("strong leadership indicators in evaluations")
        if manager_ratings and len(manager_ratings) >= 2:
            manager_avg = float(np.mean(manager_ratings))
            reasons.append(f"strong leadership ratings ({manager_avg:.1f}/5.0)")
        if avg_rating >= 4.2:
            reasons.append("excellent overall performance")
        
        reason = ", ".join(reasons) if reasons else "demonstrates strong leadership qualities"
        
        return float(score), reason
    
    def _analyze_innovation(
        self,
        person: Person,
        assignments: List[Assignment],
        ratings: List[float],
        comments: List[str],
        avg_rating: float
    ) -> Tuple[float, str]:
        """Analyze candidate for Innovation category"""
        # Check for innovation indicators
        innovation_keywords = [
            'improved', 'streamlined', 'automated', 'created', 'developed',
            'designed', 'implemented', 'optimized', 'enhanced', 'innovative',
            'solution', 'process improvement', 'efficiency'
        ]
        
        innovation_score = 0.0
        found_keywords = []
        
        for comment in comments:
            comment_lower = comment.lower() if comment else ""
            for keyword in innovation_keywords:
                if keyword in comment_lower:
                    innovation_score += 0.12
                    if keyword not in found_keywords:
                        found_keywords.append(keyword)
        
        # Composite score
        score = (
            avg_rating / 5.0 * 0.4 +  # Overall rating (40%)
            min(innovation_score, 1.0) * 0.6  # Innovation indicators (60%)
        )
        
        # Generate reason
        reasons = []
        if innovation_score > 0.3:
            reasons.append("strong innovation indicators in evaluations")
        if avg_rating >= 4.0:
            reasons.append("high performance with process improvements")
        
        reason = ", ".join(reasons) if reasons else "demonstrates innovation and process improvement"
        
        return float(score), reason
    
    def _analyze_rising_star(
        self,
        person: Person,
        assignments: List[Assignment],
        ratings: List[float],
        comments: List[str],
        avg_rating: float,
        cycle_id: int
    ) -> Tuple[float, str]:
        """Analyze candidate for Rising Star category"""
        # Check if person is new (first 6 months)
        # This would require hire_date in Person model - for now, use evaluation count
        total_evaluations = len(ratings)
        
        # Check for new employee indicators
        new_employee_keywords = [
            'new', 'quickly adapted', 'exceeded expectations', 'fast learner',
            'early success', 'quickly integrated'
        ]
        
        new_employee_score = 0.0
        for comment in comments:
            comment_lower = comment.lower() if comment else ""
            for keyword in new_employee_keywords:
                if keyword in comment_lower:
                    new_employee_score += 0.2
        
        # Check if they have few evaluations (might be new)
        is_new = total_evaluations <= 5
        
        # Composite score
        score = (
            avg_rating / 5.0 * 0.5 +  # Overall rating (50%)
            min(new_employee_score, 1.0) * 0.3 +  # New employee indicators (30%)
            (1.0 if is_new else 0.0) * 0.2  # New employee flag (20%)
        )
        
        # Generate reason
        reasons = []
        if is_new:
            reasons.append("new employee showing exceptional performance")
        if new_employee_score > 0.2:
            reasons.append("quickly adapted and exceeded expectations")
        if avg_rating >= 4.0:
            reasons.append("high ratings despite being new")
        
        reason = ", ".join(reasons) if reasons else "new employee with strong early performance"
        
        return float(score), reason
    
    def _analyze_service_excellence(
        self,
        person: Person,
        assignments: List[Assignment],
        ratings: List[float],
        comments: List[str],
        avg_rating: float
    ) -> Tuple[float, str]:
        """Analyze candidate for Service Excellence category"""
        # Check for service excellence indicators
        service_keywords = [
            'punctual', 'reliable', 'consistent', 'dependable', 'on time',
            'never late', 'high standard', 'proactive', 'self-directed'
        ]
        
        service_score = 0.0
        for comment in comments:
            comment_lower = comment.lower() if comment else ""
            for keyword in service_keywords:
                if keyword in comment_lower:
                    service_score += 0.15
        
        # Check rating consistency (low variance = consistent)
        rating_std = float(np.std(ratings)) if len(ratings) > 1 else 0.0
        consistency_score = 1.0 - min(rating_std / 2.0, 1.0)  # Lower std = higher consistency
        
        # Composite score
        score = (
            avg_rating / 5.0 * 0.4 +  # Overall rating (40%)
            min(service_score, 1.0) * 0.4 +  # Service indicators (40%)
            consistency_score * 0.2  # Consistency (20%)
        )
        
        # Generate reason
        reasons = []
        if service_score > 0.3:
            reasons.append("strong service excellence indicators")
        if consistency_score > 0.8:
            reasons.append("highly consistent performance")
        if avg_rating >= 4.0:
            reasons.append("consistently high ratings")
        
        reason = ", ".join(reasons) if reasons else "demonstrates service excellence and reliability"
        
        return float(score), reason

