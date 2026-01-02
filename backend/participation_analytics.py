"""
Participation Analytics Module
Analyzes participation rates, engagement trends, and predicts future participation.
"""
import numpy as np
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
from datetime import datetime, timedelta
from sqlalchemy import func, and_, or_
from backend.database import (
    Cycle, Assignment, Evaluation, Person, EOMNominee, EOMVoter
)


class ParticipationAnalytics:
    """
    Analyzes participation rates, engagement trends, and predicts future participation
    across departments, segments, and evaluation cycles.
    """
    
    def __init__(self, db_session):
        self.db = db_session
    
    def analyze_participation(self, cycle: Cycle) -> Dict:
        """
        Comprehensive participation analysis for a given cycle.
        
        Args:
            cycle: Cycle object to analyze
        
        Returns:
            Dictionary containing:
            - participation_rates: Participation rates by department/segment
            - engagement_trends: Trend analysis over time
            - outlier_detection: Departments with low participation
            - prediction: Predictions for future cycles
        """
        # Get all assignments for this cycle
        assignments = self.db.query(Assignment).filter(
            Assignment.cycle_id == cycle.id
        ).all()
        
        if not assignments:
            return {
                'participation_rates': {},
                'engagement_trends': {},
                'outlier_detection': {},
                'prediction': {},
                'status': 'no_data',
                'message': 'No assignments found for this cycle'
            }
        
        # Calculate participation rates by department
        participation_rates = self._calculate_participation_rates(cycle, assignments)
        
        # Analyze engagement trends
        engagement_trends = self._analyze_engagement_trends(cycle)
        
        # Detect outliers (departments with low participation)
        outlier_detection = self._detect_outliers(participation_rates)
        
        # Predict future participation
        prediction = self._predict_future_participation(cycle)
        
        return {
            'participation_rates': participation_rates,
            'engagement_trends': engagement_trends,
            'outlier_detection': outlier_detection,
            'prediction': prediction
        }
    
    def _calculate_participation_rates(self, cycle: Cycle, assignments: List[Assignment]) -> Dict:
        """
        Calculate participation rates by department and segment.
        
        Args:
            cycle: Current cycle
            assignments: List of assignments for the cycle
        
        Returns:
            Dictionary with participation rates by department/segment
        """
        # Group assignments by department/segment
        dept_stats = defaultdict(lambda: {
            'total_assignments': 0,
            'completed_evaluations': 0,
            'pending_evaluations': 0,
            'not_started': 0,
            'people': set()
        })
        
        segment_stats = defaultdict(lambda: {
            'total_assignments': 0,
            'completed_evaluations': 0,
            'pending_evaluations': 0,
            'not_started': 0,
            'people': set()
        })
        
        # Process each assignment
        for assignment in assignments:
            # Get target person's department and segment
            target_person = self.db.query(Person).filter(
                Person.email == assignment.target_email
            ).first()
            
            if not target_person:
                continue
            
            # Get evaluation status
            evaluation = self.db.query(Evaluation).filter(
                Evaluation.assignment_id == assignment.id
            ).first()
            
            status = evaluation.status if evaluation else 'not_started'
            
            # Department stats
            dept = target_person.department or 'Unknown'
            dept_stats[dept]['total_assignments'] += 1
            dept_stats[dept]['people'].add(assignment.target_email)
            
            if status == 'submitted':
                dept_stats[dept]['completed_evaluations'] += 1
            elif status == 'in_progress':
                dept_stats[dept]['pending_evaluations'] += 1
            else:
                dept_stats[dept]['not_started'] += 1
            
            # Segment stats
            segment = target_person.segment.value if target_person.segment else 'unknown'
            segment_stats[segment]['total_assignments'] += 1
            segment_stats[segment]['people'].add(assignment.target_email)
            
            if status == 'submitted':
                segment_stats[segment]['completed_evaluations'] += 1
            elif status == 'in_progress':
                segment_stats[segment]['pending_evaluations'] += 1
            else:
                segment_stats[segment]['not_started'] += 1
        
        # Calculate rates
        dept_rates = {}
        for dept, stats in dept_stats.items():
            total = stats['total_assignments']
            if total > 0:
                completion_rate = (stats['completed_evaluations'] / total) * 100
                participation_rate = ((stats['completed_evaluations'] + stats['pending_evaluations']) / total) * 100
                
                dept_rates[dept] = {
                    'total_assignments': total,
                    'completed': stats['completed_evaluations'],
                    'in_progress': stats['pending_evaluations'],
                    'not_started': stats['not_started'],
                    'completion_rate': round(completion_rate, 2),
                    'participation_rate': round(participation_rate, 2),
                    'unique_people': len(stats['people'])
                }
        
        segment_rates = {}
        for segment, stats in segment_stats.items():
            total = stats['total_assignments']
            if total > 0:
                completion_rate = (stats['completed_evaluations'] / total) * 100
                participation_rate = ((stats['completed_evaluations'] + stats['pending_evaluations']) / total) * 100
                
                segment_rates[segment] = {
                    'total_assignments': total,
                    'completed': stats['completed_evaluations'],
                    'in_progress': stats['pending_evaluations'],
                    'not_started': stats['not_started'],
                    'completion_rate': round(completion_rate, 2),
                    'participation_rate': round(participation_rate, 2),
                    'unique_people': len(stats['people'])
                }
        
        # Overall statistics
        total_assignments = len(assignments)
        total_completed = sum(s['completed_evaluations'] for s in dept_stats.values())
        total_in_progress = sum(s['pending_evaluations'] for s in dept_stats.values())
        overall_completion_rate = (total_completed / total_assignments * 100) if total_assignments > 0 else 0
        overall_participation_rate = ((total_completed + total_in_progress) / total_assignments * 100) if total_assignments > 0 else 0
        
        return {
            'by_department': dept_rates,
            'by_segment': segment_rates,
            'overall': {
                'total_assignments': total_assignments,
                'completed': total_completed,
                'in_progress': total_in_progress,
                'not_started': total_assignments - total_completed - total_in_progress,
                'completion_rate': round(overall_completion_rate, 2),
                'participation_rate': round(overall_participation_rate, 2),
                'cycle_id': cycle.id,
                'cycle_code': cycle.code
            }
        }
    
    def _analyze_engagement_trends(self, cycle: Cycle) -> Dict:
        """
        Analyze engagement trends over time within the cycle.
        
        Args:
            cycle: Current cycle
        
        Returns:
            Dictionary with trend analysis
        """
        # Get all evaluations for this cycle with timestamps
        evaluations = (
            self.db.query(Evaluation)
            .join(Assignment)
            .filter(
                Assignment.cycle_id == cycle.id,
                Evaluation.status == 'submitted',
                Evaluation.submitted_at.isnot(None)
            )
            .order_by(Evaluation.submitted_at)
            .all()
        )
        
        if not evaluations:
            return {
                'status': 'insufficient_data',
                'message': 'No submitted evaluations with timestamps found'
            }
        
        # Group by date
        daily_submissions = defaultdict(int)
        for eval in evaluations:
            if eval.submitted_at:
                date_key = eval.submitted_at.date()
                daily_submissions[date_key] += 1
        
        # Calculate trends
        sorted_dates = sorted(daily_submissions.keys())
        if len(sorted_dates) < 2:
            return {
                'status': 'insufficient_data',
                'message': 'Need at least 2 days of data for trend analysis'
            }
        
        # Calculate daily rates
        daily_data = [
            {'date': str(date), 'count': daily_submissions[date]}
            for date in sorted_dates
        ]
        
        # Calculate cumulative submissions
        cumulative = 0
        cumulative_data = []
        for date in sorted_dates:
            cumulative += daily_submissions[date]
            cumulative_data.append({
                'date': str(date),
                'cumulative': cumulative
            })
        
        # Calculate trend direction
        first_half = sum(daily_submissions[d] for d in sorted_dates[:len(sorted_dates)//2])
        second_half = sum(daily_submissions[d] for d in sorted_dates[len(sorted_dates)//2:])
        
        first_half_days = len(sorted_dates) // 2
        second_half_days = len(sorted_dates) - first_half_days
        
        if first_half_days > 0 and second_half_days > 0:
            first_half_avg = first_half / first_half_days
            second_half_avg = second_half / second_half_days
            trend_direction = 'increasing' if second_half_avg > first_half_avg else 'decreasing' if second_half_avg < first_half_avg else 'stable'
            trend_strength = abs(second_half_avg - first_half_avg) / max(first_half_avg, 0.1) * 100
        else:
            trend_direction = 'stable'
            trend_strength = 0.0
        
        # Calculate submission velocity (evaluations per day)
        if cycle.start_date and cycle.end_date:
            total_days = (cycle.end_date - cycle.start_date).days + 1
            elapsed_days = (datetime.now().date() - cycle.start_date).days + 1 if cycle.start_date else total_days
            velocity = len(evaluations) / max(elapsed_days, 1)
        else:
            total_days = len(sorted_dates)
            elapsed_days = total_days
            velocity = len(evaluations) / max(total_days, 1)
        
        return {
            'daily_submissions': daily_data,
            'cumulative_submissions': cumulative_data,
            'trend_direction': trend_direction,
            'trend_strength': round(trend_strength, 2),
            'total_evaluations': len(evaluations),
            'submission_velocity': round(velocity, 2),
            'first_half_avg': round(first_half_avg, 2) if first_half_days > 0 else 0,
            'second_half_avg': round(second_half_avg, 2) if second_half_days > 0 else 0,
            'cycle_start': str(cycle.start_date) if cycle.start_date else None,
            'cycle_end': str(cycle.end_date) if cycle.end_date else None
        }
    
    def _detect_outliers(self, participation_rates: Dict) -> Dict:
        """
        Detect departments/segments with unusually low participation.
        
        Args:
            participation_rates: Participation rates dictionary from _calculate_participation_rates
        
        Returns:
            Dictionary with outlier detection results
        """
        outliers = {
            'low_participation_departments': [],
            'low_participation_segments': [],
            'threshold': 50.0,  # 50% participation threshold
            'statistical_outliers': []
        }
        
        # Get overall average participation rate
        overall_rate = participation_rates.get('overall', {}).get('participation_rate', 0)
        
        # Check departments
        dept_rates = participation_rates.get('by_department', {})
        if dept_rates:
            dept_participation_rates = [
                (dept, stats['participation_rate'])
                for dept, stats in dept_rates.items()
            ]
            
            if dept_participation_rates:
                rates_only = [rate for _, rate in dept_participation_rates]
                mean_rate = np.mean(rates_only)
                std_rate = np.std(rates_only) if len(rates_only) > 1 else 0
                
                # Departments below threshold
                for dept, rate in dept_participation_rates:
                    if rate < outliers['threshold']:
                        outliers['low_participation_departments'].append({
                            'department': dept,
                            'participation_rate': rate,
                            'total_assignments': dept_rates[dept]['total_assignments'],
                            'completed': dept_rates[dept]['completed'],
                            'gap': round(outliers['threshold'] - rate, 2)
                        })
                    
                    # Statistical outliers (more than 2 standard deviations below mean)
                    if std_rate > 0 and rate < (mean_rate - 2 * std_rate):
                        outliers['statistical_outliers'].append({
                            'type': 'department',
                            'name': dept,
                            'participation_rate': rate,
                            'mean': round(mean_rate, 2),
                            'std_dev': round(std_rate, 2),
                            'deviation': round(rate - mean_rate, 2)
                        })
        
        # Check segments
        segment_rates = participation_rates.get('by_segment', {})
        if segment_rates:
            segment_participation_rates = [
                (segment, stats['participation_rate'])
                for segment, stats in segment_rates.items()
            ]
            
            if segment_participation_rates:
                rates_only = [rate for _, rate in segment_participation_rates]
                mean_rate = np.mean(rates_only)
                std_rate = np.std(rates_only) if len(rates_only) > 1 else 0
                
                # Segments below threshold
                for segment, rate in segment_participation_rates:
                    if rate < outliers['threshold']:
                        outliers['low_participation_segments'].append({
                            'segment': segment,
                            'participation_rate': rate,
                            'total_assignments': segment_rates[segment]['total_assignments'],
                            'completed': segment_rates[segment]['completed'],
                            'gap': round(outliers['threshold'] - rate, 2)
                        })
                    
                    # Statistical outliers
                    if std_rate > 0 and rate < (mean_rate - 2 * std_rate):
                        outliers['statistical_outliers'].append({
                            'type': 'segment',
                            'name': segment,
                            'participation_rate': rate,
                            'mean': round(mean_rate, 2),
                            'std_dev': round(std_rate, 2),
                            'deviation': round(rate - mean_rate, 2)
                        })
        
        # Summary
        outliers['summary'] = {
            'total_low_participation_departments': len(outliers['low_participation_departments']),
            'total_low_participation_segments': len(outliers['low_participation_segments']),
            'total_statistical_outliers': len(outliers['statistical_outliers']),
            'overall_participation_rate': round(overall_rate, 2)
        }
        
        return outliers
    
    def _predict_future_participation(self, current_cycle: Cycle) -> Dict:
        """
        Predict participation rates for future cycles based on historical data.
        
        Args:
            current_cycle: Current cycle to use as baseline
        
        Returns:
            Dictionary with predictions for future cycles
        """
        # Get historical cycles (previous cycles)
        historical_cycles = (
            self.db.query(Cycle)
            .filter(
                Cycle.id != current_cycle.id,
                Cycle.end_date.isnot(None),
                Cycle.end_date < (current_cycle.start_date or datetime.now().date())
            )
            .order_by(Cycle.end_date.desc())
            .limit(5)
            .all()
        )
        
        if not historical_cycles:
            return {
                'status': 'insufficient_data',
                'message': 'No historical cycles found for prediction',
                'predicted_participation_rate': None
            }
        
        # Calculate historical participation rates
        historical_rates = []
        for hist_cycle in historical_cycles:
            assignments = self.db.query(Assignment).filter(
                Assignment.cycle_id == hist_cycle.id
            ).all()
            
            if assignments:
                evaluations = (
                    self.db.query(Evaluation)
                    .join(Assignment)
                    .filter(
                        Assignment.cycle_id == hist_cycle.id,
                        Evaluation.status == 'submitted'
                    )
                    .count()
                )
                
                participation_rate = (evaluations / len(assignments) * 100) if assignments else 0
                historical_rates.append({
                    'cycle_id': hist_cycle.id,
                    'cycle_code': hist_cycle.code,
                    'participation_rate': round(participation_rate, 2),
                    'end_date': str(hist_cycle.end_date) if hist_cycle.end_date else None
                })
        
        if not historical_rates:
            return {
                'status': 'insufficient_data',
                'message': 'No historical participation data found',
                'predicted_participation_rate': None
            }
        
        # Calculate current cycle participation rate
        current_assignments = self.db.query(Assignment).filter(
            Assignment.cycle_id == current_cycle.id
        ).count()
        
        current_evaluations = (
            self.db.query(Evaluation)
            .join(Assignment)
            .filter(
                Assignment.cycle_id == current_cycle.id,
                Evaluation.status == 'submitted'
            )
            .count()
        )
        
        current_rate = (current_evaluations / current_assignments * 100) if current_assignments > 0 else 0
        
        # Simple prediction: average of historical rates with trend adjustment
        historical_rates_values = [r['participation_rate'] for r in historical_rates]
        avg_historical_rate = np.mean(historical_rates_values)
        
        # Calculate trend (if we have enough data)
        if len(historical_rates_values) >= 2:
            # Simple linear trend
            recent_avg = np.mean(historical_rates_values[:2])  # Most recent 2 cycles
            older_avg = np.mean(historical_rates_values[2:]) if len(historical_rates_values) > 2 else recent_avg
            trend = recent_avg - older_avg
        else:
            trend = 0
        
        # Predict next cycle participation rate
        # Weighted average: 70% historical average, 30% trend adjustment
        predicted_rate = avg_historical_rate + (trend * 0.3)
        predicted_rate = max(0, min(100, predicted_rate))  # Clamp to 0-100
        
        # Confidence based on data quality
        confidence = min(100, len(historical_rates) * 20)  # 20% per historical cycle, max 100%
        
        # Predictions for next 3 cycles
        future_predictions = []
        for i in range(1, 4):
            # Apply trend decay (trend effect decreases over time)
            cycle_prediction = avg_historical_rate + (trend * 0.3 * (1 - i * 0.1))
            cycle_prediction = max(0, min(100, cycle_prediction))
            future_predictions.append({
                'cycle_number': i,
                'predicted_participation_rate': round(cycle_prediction, 2),
                'confidence': max(0, confidence - (i * 10))  # Decreasing confidence
            })
        
        return {
            'historical_data': historical_rates,
            'current_participation_rate': round(current_rate, 2),
            'average_historical_rate': round(avg_historical_rate, 2),
            'trend': round(trend, 2),
            'predicted_participation_rate': round(predicted_rate, 2),
            'confidence': round(confidence, 2),
            'future_cycles': future_predictions,
            'method': 'weighted_average_with_trend',
            'recommendations': self._generate_recommendations(current_rate, predicted_rate, historical_rates_values)
        }
    
    def _generate_recommendations(self, current_rate: float, predicted_rate: float, historical_rates: List[float]) -> List[str]:
        """
        Generate recommendations based on participation analysis.
        
        Args:
            current_rate: Current cycle participation rate
            predicted_rate: Predicted future participation rate
            historical_rates: List of historical participation rates
        
        Returns:
            List of recommendation strings
        """
        recommendations = []
        
        # Compare current to historical average
        if historical_rates:
            avg_historical = np.mean(historical_rates)
            if current_rate < avg_historical - 10:
                recommendations.append(
                    f"Current participation rate ({current_rate:.1f}%) is significantly below "
                    f"historical average ({avg_historical:.1f}%). Consider sending reminders or "
                    "identifying barriers to participation."
                )
            elif current_rate > avg_historical + 10:
                recommendations.append(
                    f"Current participation rate ({current_rate:.1f}%) is above historical average. "
                    "Maintain current engagement strategies."
                )
        
        # Trend-based recommendations
        if len(historical_rates) >= 2:
            recent_trend = historical_rates[0] - historical_rates[-1]
            if recent_trend < -5:
                recommendations.append(
                    "Participation is declining. Consider implementing engagement initiatives "
                    "or simplifying the evaluation process."
                )
            elif recent_trend > 5:
                recommendations.append(
                    "Participation is improving. Continue current strategies and consider "
                    "sharing success stories to maintain momentum."
                )
        
        # Prediction-based recommendations
        if predicted_rate < 60:
            recommendations.append(
                f"Predicted participation rate ({predicted_rate:.1f}%) is below optimal. "
                "Proactive outreach may be needed for next cycle."
            )
        
        if not recommendations:
            recommendations.append(
                "Participation rates are stable. Continue monitoring and maintain current engagement levels."
            )
        
        return recommendations
