"""
Bias-Free EOM Nomination Suggestions
Ensures fair representation and identifies underrepresented groups in EOM nominations.
"""
import numpy as np
from typing import List, Dict, Optional, Tuple
from collections import defaultdict
from datetime import datetime, timedelta
from sqlalchemy import func, and_, or_
from backend.database import (
    Person, Evaluation, Assignment, Cycle, EOMNominee, EOMWinner, 
    EOMCycle, StaffSegment
)


class BiasFreeSuggestions:
    """
    Provides bias-free EOM nomination suggestions by:
    - Identifying underrepresented groups
    - Analyzing recent winning patterns
    - Calculating nomination novelty
    - Ensuring demographic balance
    """
    
    def __init__(self, db_session):
        self.db = db_session
    
    def suggest_candidates(self, department: Optional[str] = None, 
                          cycle_id: int = None, limit: int = 10) -> List[Dict]:
        """
        Suggest EOM candidates with bias-free analysis.
        
        Args:
            department: Optional department filter
            cycle_id: Current cycle ID
            limit: Maximum number of suggestions to return
        
        Returns:
            List of candidate suggestions with bias analysis
        """
        # Identify underrepresented groups
        underrepresented = self.identify_underrepresented_groups(cycle_id)
        
        # Get recent winning patterns
        recent_winners = self.get_recent_winning_patterns(cycle_id)
        
        # Get eligible candidates
        eligible_candidates = self.get_eligible_candidates(department, cycle_id)
        
        suggestions = []
        for candidate in eligible_candidates:
            # Calculate novelty factor (how new/unique this nomination would be)
            novelty_factor = self.calculate_nomination_novelty(candidate, recent_winners)
            
            # Calculate demographic balance score
            representation_score = self.calculate_demographic_balance(
                candidate, underrepresented, recent_winners
            )
            
            # Calculate bias indicators
            bias_indicators = self._calculate_bias_indicators(candidate, recent_winners)
            
            # Identify bias flags
            bias_flags = self._identify_bias_flags(
                candidate, bias_indicators, underrepresented, recent_winners
            )
            
            # Generate recommended actions
            suggested_action = self._generate_recommended_actions(
                candidate, bias_flags, underrepresented, novelty_factor, representation_score
            )
            
            # Calculate overall score (combining performance and fairness)
            overall_score = self._calculate_overall_score(
                candidate, novelty_factor, representation_score, bias_indicators
            )
            
            suggestions.append({
                'candidate': {
                    'email': candidate['email'],
                    'full_name': candidate['full_name'],
                    'role_title': candidate.get('role_title'),
                    'department': candidate.get('department'),
                    'segment': candidate.get('segment')
                },
                'bias_indicators': bias_indicators,
                'bias_flags': bias_flags,
                'suggested_action': suggested_action,
                'novelty_factor': round(novelty_factor, 3),
                'representation_score': round(representation_score, 3),
                'overall_score': round(overall_score, 3),
                'performance_metrics': candidate.get('performance_metrics', {})
            })
        
        # Sort by overall score (prioritizing fairness and performance)
        suggestions.sort(key=lambda x: x['overall_score'], reverse=True)
        
        return suggestions[:limit]
    
    def identify_underrepresented_groups(self, cycle_id: Optional[int] = None) -> Dict:
        """
        Identify groups that are underrepresented in EOM nominations/wins.
        
        Args:
            cycle_id: Optional cycle ID to filter by
        
        Returns:
            Dictionary with underrepresented groups by department, segment, and role
        """
        # Get all active people
        all_people = self.db.query(Person).filter(Person.active == True).all()
        
        # Get all EOM winners (or nominees if no winners yet)
        if cycle_id:
            winners_query = self.db.query(EOMWinner).join(EOMCycle).filter(
                EOMCycle.cycle_id == cycle_id
            )
        else:
            winners_query = self.db.query(EOMWinner)
        
        winners = winners_query.all()
        
        # Calculate total population by group
        total_by_department = defaultdict(int)
        total_by_segment = defaultdict(int)
        total_by_role = defaultdict(int)
        
        for person in all_people:
            dept = person.department or 'Unknown'
            segment = person.segment.value if person.segment else 'unknown'
            role = person.role_title or 'Unknown'
            
            total_by_department[dept] += 1
            total_by_segment[segment] += 1
            total_by_role[role] += 1
        
        # Calculate winners by group
        winners_by_department = defaultdict(int)
        winners_by_segment = defaultdict(int)
        winners_by_role = defaultdict(int)
        
        for winner in winners:
            person = self.db.query(Person).filter(Person.email == winner.winner_email).first()
            if person:
                dept = person.department or 'Unknown'
                segment = person.segment.value if person.segment else 'unknown'
                role = person.role_title or 'Unknown'
                
                winners_by_department[dept] += 1
                winners_by_segment[segment] += 1
                winners_by_role[role] += 1
        
        # Calculate representation rates
        underrepresented = {
            'by_department': {},
            'by_segment': {},
            'by_role': {}
        }
        
        # Department analysis
        for dept, total in total_by_department.items():
            winners = winners_by_department.get(dept, 0)
            representation_rate = (winners / total * 100) if total > 0 else 0
            expected_rate = (len(winners) / len(all_people) * 100) if all_people else 0
            
            if representation_rate < expected_rate * 0.5:  # Less than 50% of expected
                underrepresented['by_department'][dept] = {
                    'total_people': total,
                    'winners': winners,
                    'representation_rate': round(representation_rate, 2),
                    'expected_rate': round(expected_rate, 2),
                    'gap': round(expected_rate - representation_rate, 2)
                }
        
        # Segment analysis
        for segment, total in total_by_segment.items():
            winners = winners_by_segment.get(segment, 0)
            representation_rate = (winners / total * 100) if total > 0 else 0
            expected_rate = (len(winners) / len(all_people) * 100) if all_people else 0
            
            if representation_rate < expected_rate * 0.5:
                underrepresented['by_segment'][segment] = {
                    'total_people': total,
                    'winners': winners,
                    'representation_rate': round(representation_rate, 2),
                    'expected_rate': round(expected_rate, 2),
                    'gap': round(expected_rate - representation_rate, 2)
                }
        
        # Role analysis (top roles only)
        for role, total in total_by_role.items():
            if total < 3:  # Skip roles with very few people
                continue
            winners = winners_by_role.get(role, 0)
            representation_rate = (winners / total * 100) if total > 0 else 0
            expected_rate = (len(winners) / len(all_people) * 100) if all_people else 0
            
            if representation_rate < expected_rate * 0.5:
                underrepresented['by_role'][role] = {
                    'total_people': total,
                    'winners': winners,
                    'representation_rate': round(representation_rate, 2),
                    'expected_rate': round(expected_rate, 2),
                    'gap': round(expected_rate - representation_rate, 2)
                }
        
        return underrepresented
    
    def get_recent_winning_patterns(self, cycle_id: Optional[int] = None) -> Dict:
        """
        Analyze recent winning patterns to identify biases.
        
        Args:
            cycle_id: Optional cycle ID
        
        Returns:
            Dictionary with winning patterns by various dimensions
        """
        # Get recent winners (last 12 months or specified cycle)
        if cycle_id:
            winners_query = self.db.query(EOMWinner).join(EOMCycle).filter(
                EOMCycle.cycle_id == cycle_id
            )
        else:
            # Last 12 months
            cutoff_date = datetime.now().date() - timedelta(days=365)
            winners_query = self.db.query(EOMWinner).filter(
                EOMWinner.announced_at >= cutoff_date
            )
        
        winners = winners_query.all()
        
        if not winners:
            return {
                'total_winners': 0,
                'by_department': {},
                'by_segment': {},
                'by_category': {},
                'repeat_winners': [],
                'patterns': {}
            }
        
        # Analyze patterns
        winners_by_department = defaultdict(int)
        winners_by_segment = defaultdict(int)
        winners_by_category = defaultdict(int)
        winner_counts = defaultdict(int)
        
        for winner in winners:
            person = self.db.query(Person).filter(Person.email == winner.winner_email).first()
            if person:
                dept = person.department or 'Unknown'
                segment = person.segment.value if person.segment else 'unknown'
                
                winners_by_department[dept] += 1
                winners_by_segment[segment] += 1
                winner_counts[winner.winner_email] += 1
            
            category = winner.category or 'Unknown'
            winners_by_category[category] += 1
        
        # Find repeat winners
        repeat_winners = [
            {'email': email, 'win_count': count}
            for email, count in winner_counts.items() if count > 1
        ]
        repeat_winners.sort(key=lambda x: x['win_count'], reverse=True)
        
        # Identify patterns
        patterns = {
            'most_common_department': max(winners_by_department.items(), key=lambda x: x[1])[0] if winners_by_department else None,
            'most_common_segment': max(winners_by_segment.items(), key=lambda x: x[1])[0] if winners_by_segment else None,
            'most_common_category': max(winners_by_category.items(), key=lambda x: x[1])[0] if winners_by_category else None,
            'repeat_winner_rate': len(repeat_winners) / len(winners) * 100 if winners else 0
        }
        
        return {
            'total_winners': len(winners),
            'by_department': dict(winners_by_department),
            'by_segment': dict(winners_by_segment),
            'by_category': dict(winners_by_category),
            'repeat_winners': repeat_winners[:10],  # Top 10
            'patterns': patterns
        }
    
    def get_eligible_candidates(self, department: Optional[str], cycle_id: int) -> List[Dict]:
        """
        Get eligible candidates for EOM nomination.
        
        Args:
            department: Optional department filter
            cycle_id: Current cycle ID
        
        Returns:
            List of candidate dictionaries with performance metrics
        """
        # Get all active people
        query = self.db.query(Person).filter(Person.active == True)
        
        if department:
            query = query.filter(Person.department == department)
        
        people = query.all()
        
        # Get evaluations for the cycle
        evaluations = self.db.query(Evaluation).join(Assignment).filter(
            Assignment.cycle_id == cycle_id,
            Evaluation.status == 'submitted',
            Evaluation.rating.isnot(None)
        ).all()
        
        # Aggregate performance by person
        candidate_performance = defaultdict(lambda: {
            'ratings': [],
            'contexts': set(),
            'comments': []
        })
        
        for eval in evaluations:
            assignment = self.db.query(Assignment).filter(
                Assignment.id == eval.assignment_id
            ).first()
            if assignment:
                candidate_performance[assignment.target_email]['ratings'].append(eval.rating)
                candidate_performance[assignment.target_email]['contexts'].add(assignment.rater_context)
                if eval.comments:
                    candidate_performance[assignment.target_email]['comments'].append(eval.comments)
        
        # Build candidate list
        candidates = []
        for person in people:
            if person.email not in candidate_performance:
                continue  # Skip if no evaluations
            
            stats = candidate_performance[person.email]
            if len(stats['ratings']) < 2:
                continue  # Need at least 2 evaluations
            
            ratings = np.array(stats['ratings'])
            
            candidates.append({
                'email': person.email,
                'full_name': person.full_name,
                'role_title': person.role_title,
                'department': person.department,
                'segment': person.segment.value if person.segment else None,
                'performance_metrics': {
                    'avg_rating': float(np.mean(ratings)),
                    'rating_count': len(ratings),
                    'consistency': float(np.std(ratings)),
                    'context_diversity': len(stats['contexts'])
                }
            })
        
        return candidates
    
    def calculate_nomination_novelty(self, candidate: Dict, recent_winners: Dict) -> float:
        """
        Calculate how novel/unique this nomination would be.
        Higher score = more novel (hasn't won recently, different from recent patterns).
        
        Args:
            candidate: Candidate dictionary
            recent_winners: Recent winning patterns
        
        Returns:
            Novelty factor (0-1, higher is more novel)
        """
        novelty_score = 1.0
        
        # Check if candidate has won recently
        candidate_email = candidate['email']
        repeat_winners = recent_winners.get('repeat_winners', [])
        
        for repeat in repeat_winners:
            if repeat['email'] == candidate_email:
                # Reduce novelty for repeat winners
                novelty_score -= 0.3 * min(repeat['win_count'], 3)  # Max reduction 0.9
                break
        
        # Check department novelty
        candidate_dept = candidate.get('department')
        if candidate_dept:
            patterns = recent_winners.get('patterns', {})
            most_common_dept = patterns.get('most_common_department')
            if candidate_dept == most_common_dept:
                novelty_score -= 0.2
        
        # Check segment novelty
        candidate_segment = candidate.get('segment')
        if candidate_segment:
            patterns = recent_winners.get('patterns', {})
            most_common_segment = patterns.get('most_common_segment')
            if candidate_segment == most_common_segment:
                novelty_score -= 0.1
        
        # Ensure score is between 0 and 1
        return max(0.0, min(1.0, novelty_score))
    
    def calculate_demographic_balance(self, candidate: Dict, underrepresented: Dict, 
                                     recent_winners: Dict) -> float:
        """
        Calculate how well this candidate would balance demographics.
        Higher score = better balance (from underrepresented group).
        
        Args:
            candidate: Candidate dictionary
            underrepresented: Underrepresented groups dictionary
            recent_winners: Recent winning patterns
        
        Returns:
            Representation score (0-1, higher is better balance)
        """
        balance_score = 0.5  # Base score
        
        # Check department representation
        candidate_dept = candidate.get('department')
        if candidate_dept and candidate_dept in underrepresented.get('by_department', {}):
            dept_info = underrepresented['by_department'][candidate_dept]
            gap = dept_info.get('gap', 0)
            # Higher gap = higher boost
            balance_score += min(0.3, gap / 50.0)  # Max boost 0.3
        
        # Check segment representation
        candidate_segment = candidate.get('segment')
        if candidate_segment and candidate_segment in underrepresented.get('by_segment', {}):
            segment_info = underrepresented['by_segment'][candidate_segment]
            gap = segment_info.get('gap', 0)
            balance_score += min(0.2, gap / 50.0)  # Max boost 0.2
        
        # Check role representation
        candidate_role = candidate.get('role_title')
        if candidate_role and candidate_role in underrepresented.get('by_role', {}):
            role_info = underrepresented['by_role'][candidate_role]
            gap = role_info.get('gap', 0)
            balance_score += min(0.1, gap / 50.0)  # Max boost 0.1
        
        # Penalize if from overrepresented group
        patterns = recent_winners.get('patterns', {})
        if candidate_dept == patterns.get('most_common_department'):
            balance_score -= 0.1
        if candidate_segment == patterns.get('most_common_segment'):
            balance_score -= 0.1
        
        # Ensure score is between 0 and 1
        return max(0.0, min(1.0, balance_score))
    
    def _calculate_bias_indicators(self, candidate: Dict, recent_winners: Dict) -> Dict:
        """
        Calculate various bias indicators for a candidate.
        
        Args:
            candidate: Candidate dictionary
            recent_winners: Recent winning patterns
        
        Returns:
            Dictionary of bias indicators
        """
        indicators = {
            'repeat_winner_risk': False,
            'pattern_match_risk': False,
            'department_concentration': 0.0,
            'segment_concentration': 0.0,
            'category_concentration': 0.0
        }
        
        candidate_email = candidate['email']
        
        # Check for repeat winner
        repeat_winners = recent_winners.get('repeat_winners', [])
        for repeat in repeat_winners:
            if repeat['email'] == candidate_email:
                indicators['repeat_winner_risk'] = True
                indicators['repeat_winner_count'] = repeat['win_count']
                break
        
        # Check pattern matching
        patterns = recent_winners.get('patterns', {})
        candidate_dept = candidate.get('department')
        candidate_segment = candidate.get('segment')
        
        if candidate_dept == patterns.get('most_common_department'):
            indicators['pattern_match_risk'] = True
            indicators['department_concentration'] = 1.0
        
        if candidate_segment == patterns.get('most_common_segment'):
            indicators['pattern_match_risk'] = True
            indicators['segment_concentration'] = 1.0
        
        # Calculate concentration scores
        winners_by_dept = recent_winners.get('by_department', {})
        total_winners = recent_winners.get('total_winners', 1)
        
        if candidate_dept and candidate_dept in winners_by_dept:
            indicators['department_concentration'] = winners_by_dept[candidate_dept] / total_winners
        
        winners_by_segment = recent_winners.get('by_segment', {})
        if candidate_segment and candidate_segment in winners_by_segment:
            indicators['segment_concentration'] = winners_by_segment[candidate_segment] / total_winners
        
        return indicators
    
    def _identify_bias_flags(self, candidate: Dict, bias_indicators: Dict,
                            underrepresented: Dict, recent_winners: Dict) -> List[str]:
        """
        Identify specific bias flags for a candidate.
        
        Args:
            candidate: Candidate dictionary
            bias_indicators: Bias indicators dictionary
            underrepresented: Underrepresented groups
            recent_winners: Recent winning patterns
        
        Returns:
            List of bias flag strings
        """
        flags = []
        
        # Repeat winner flag
        if bias_indicators.get('repeat_winner_risk'):
            count = bias_indicators.get('repeat_winner_count', 1)
            flags.append(f"Repeat winner ({count} previous wins)")
        
        # Pattern matching flags
        if bias_indicators.get('pattern_match_risk'):
            flags.append("Matches recent winning patterns")
        
        # Overrepresentation flags
        if bias_indicators.get('department_concentration', 0) > 0.4:
            flags.append("High department concentration in recent winners")
        
        if bias_indicators.get('segment_concentration', 0) > 0.4:
            flags.append("High segment concentration in recent winners")
        
        # Check if from overrepresented group
        patterns = recent_winners.get('patterns', {})
        candidate_dept = candidate.get('department')
        candidate_segment = candidate.get('segment')
        
        if candidate_dept == patterns.get('most_common_department'):
            flags.append("From most frequently winning department")
        
        if candidate_segment == patterns.get('most_common_segment'):
            flags.append("From most frequently winning segment")
        
        return flags
    
    def _generate_recommended_actions(self, candidate: Dict, bias_flags: List[str],
                                     underrepresented: Dict, novelty_factor: float,
                                     representation_score: float) -> List[str]:
        """
        Generate recommended actions based on bias analysis.
        
        Args:
            candidate: Candidate dictionary
            bias_flags: List of bias flags
            underrepresented: Underrepresented groups
            representation_score: Representation balance score
            novelty_factor: Novelty factor
        
        Returns:
            List of recommended action strings
        """
        actions = []
        
        # High representation score = good for diversity
        if representation_score > 0.7:
            actions.append("Strong candidate for improving demographic balance")
            if candidate.get('department') in underrepresented.get('by_department', {}):
                actions.append(f"Would improve representation for {candidate.get('department')} department")
            if candidate.get('segment') in underrepresented.get('by_segment', {}):
                actions.append(f"Would improve representation for {candidate.get('segment')} segment")
        
        # High novelty = good for variety
        if novelty_factor > 0.7:
            actions.append("Would introduce diversity in recent winner patterns")
        
        # Bias flags = warnings
        if bias_flags:
            if len(bias_flags) > 2:
                actions.append("⚠️ Consider alternative candidates to avoid bias patterns")
            else:
                actions.append("⚠️ Review bias indicators before nomination")
        
        # Performance-based recommendations
        perf_metrics = candidate.get('performance_metrics', {})
        if perf_metrics.get('avg_rating', 0) >= 4.5:
            actions.append("High performance ratings support nomination")
        
        if perf_metrics.get('context_diversity', 0) >= 3:
            actions.append("Recognized across multiple evaluation contexts")
        
        # Default if no specific actions
        if not actions:
            actions.append("Candidate meets basic eligibility criteria")
        
        return actions
    
    def _calculate_overall_score(self, candidate: Dict, novelty_factor: float,
                                representation_score: float, bias_indicators: Dict) -> float:
        """
        Calculate overall score combining performance and fairness.
        
        Args:
            candidate: Candidate dictionary
            novelty_factor: Novelty factor (0-1)
            representation_score: Representation score (0-1)
            bias_indicators: Bias indicators dictionary
        
        Returns:
            Overall score (0-1, higher is better)
        """
        # Performance component (40%)
        perf_metrics = candidate.get('performance_metrics', {})
        avg_rating = perf_metrics.get('avg_rating', 0)
        performance_score = (avg_rating / 5.0) * 0.4  # Normalize to 0-0.4
        
        # Fairness component (35%)
        fairness_score = (novelty_factor * 0.15) + (representation_score * 0.20)
        
        # Bias penalty (25%)
        bias_penalty = 0.0
        if bias_indicators.get('repeat_winner_risk'):
            bias_penalty += 0.1
        if bias_indicators.get('pattern_match_risk'):
            bias_penalty += 0.05
        if bias_indicators.get('department_concentration', 0) > 0.4:
            bias_penalty += 0.05
        if bias_indicators.get('segment_concentration', 0) > 0.4:
            bias_penalty += 0.05
        
        bias_score = max(0.0, 0.25 - bias_penalty)
        
        # Combine scores
        overall = performance_score + fairness_score + bias_score
        
        return min(1.0, overall)
