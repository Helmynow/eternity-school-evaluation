"""
Weighted Scoring System for Academic vs Admin Staff Evaluations
Specialized scoring system with different weight matrices and calculations for academic and administrative staff.
"""

import logging
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from backend.database import Assignment, Cycle, Evaluation, Person


@dataclass
class StaffTypeScore:
    """Score breakdown for a staff type (academic or admin)"""

    staff_type: str  # 'academic' or 'admin'
    target_email: str
    total_evaluations: int
    raw_average: float
    weighted_average: float
    context_breakdown: Dict[str, Dict]  # Context -> {count, raw_avg, weighted_avg, weight}
    final_score: float
    score_components: Dict[str, float]  # Component scores if available


@dataclass
class ComparisonResult:
    """Comparison between academic and admin scoring"""

    cycle_id: int
    academic_stats: Dict
    admin_stats: Dict
    differences: Dict
    recommendations: List[str]


class AcademicAdminScoring:
    """
    Specialized weighted scoring system for Academic vs Admin staff evaluations.

    Features:
    - Separate weight matrices for academic and admin staff
    - Context-specific weighting
    - Comparative analysis
    - Fairness validation
    - Score normalization
    """

    # Academic Staff Weight Matrix (relative weights)
    # 1.0 means "full weight" for the staff type; values < 1.0 reduce influence.
    ACADEMIC_WEIGHT_MATRIX = {
        "CEO": 1.0,
        "P&C": 0.8,
        "QA": 1.0,
        "peer_review": 0.7,
        "manager_review": 0.9,
        "coordinator_hod": 0.9,
        "direct_report_review": 0.7,
        "self_review": 0.5,
        "360_review": 0.85,
    }

    # Admin Staff Weight Matrix (relative weights)
    ADMIN_WEIGHT_MATRIX = {
        "CEO": 1.0,
        "P&C": 1.0,
        "QA": 0.7,
        "peer_review": 0.8,
        "manager_review": 1.0,
        "coordinator_hod": 0.8,
        "direct_report_review": 0.7,
        "self_review": 0.5,
        "360_review": 0.85,
    }

    # Minimum evaluations required per staff type
    MIN_EVALUATIONS = {
        "academic": {
            "CEO": 1,
            "P&C": 1,
            "QA": 2,  # More QA evaluations for academics
            "peer_review": 3,  # More peer reviews for academics
            "manager_review": 1,
            "direct_report_review": 1,
            "self_review": 1,
            "360_review": 1,
        },
        "admin": {
            "CEO": 1,
            "P&C": 2,  # More P&C evaluations for admin
            "QA": 1,
            "peer_review": 2,
            "manager_review": 1,
            "direct_report_review": 1,
            "self_review": 1,
            "360_review": 1,
        },
    }

    # Maximum evaluations allowed per staff type
    MAX_EVALUATIONS = {
        "academic": {
            "CEO": 1,
            "P&C": 2,
            "QA": 5,
            "peer_review": 8,
            "manager_review": 2,
            "direct_report_review": 5,
            "self_review": 1,
            "360_review": 1,
        },
        "admin": {
            "CEO": 1,
            "P&C": 5,
            "QA": 3,
            "peer_review": 6,
            "manager_review": 2,
            "direct_report_review": 4,
            "self_review": 1,
            "360_review": 1,
        },
    }

    def __init__(self, db_session):
        self.db = db_session
        self.logger = logging.getLogger(__name__)

    def get_staff_type(self, person: Person) -> str:
        """
        Determine if a person is academic or admin staff.

        Args:
            person: Person object

        Returns:
            'academic' or 'admin' based on role/department
        """
        if not person:
            return "academic"  # Default

        # Check role title for academic indicators
        role_lower = (person.role_title or "").lower()
        dept_lower = (person.department or "").lower()

        academic_keywords = [
            "teacher",
            "instructor",
            "professor",
            "lecturer",
            "faculty",
            "academic",
            "curriculum",
            "pedagogy",
            "education",
        ]

        admin_keywords = [
            "admin",
            "administrative",
            "coordinator",
            "manager",
            "director",
            "secretary",
            "assistant",
            "operations",
            "hr",
            "finance",
            "it",
        ]

        # Check role title
        for keyword in academic_keywords:
            if keyword in role_lower:
                return "academic"

        for keyword in admin_keywords:
            if keyword in role_lower:
                return "admin"

        # Check department
        for keyword in academic_keywords:
            if keyword in dept_lower:
                return "academic"

        for keyword in admin_keywords:
            if keyword in dept_lower:
                return "admin"

        # Default to academic if unclear
        return "academic"

    def get_weight_matrix(self, staff_type: str) -> Dict[str, float]:
        """
        Get weight matrix for a staff type.

        Args:
            staff_type: 'academic' or 'admin'

        Returns:
            Weight matrix dictionary
        """
        if staff_type.lower() == "academic":
            return self.ACADEMIC_WEIGHT_MATRIX.copy()
        elif staff_type.lower() == "admin":
            return self.ADMIN_WEIGHT_MATRIX.copy()
        else:
            # Default to academic
            return self.ACADEMIC_WEIGHT_MATRIX.copy()

    def calculate_weighted_score(self, cycle_id: int, target_email: str, staff_type: Optional[str] = None) -> StaffTypeScore:
        """
        Calculate weighted score for a specific staff member.

        Args:
            cycle_id: Evaluation cycle ID
            target_email: Email of staff member
            staff_type: Optional staff type override

        Returns:
            StaffTypeScore with detailed breakdown
        """
        # Get person to determine staff type
        person = self.db.query(Person).filter(Person.email == target_email).first()

        if not person:
            raise ValueError(f"Person not found: {target_email}")

        # Determine staff type
        if not staff_type:
            staff_type = self.get_staff_type(person)

        # Get weight matrix
        weight_matrix = self.get_weight_matrix(staff_type)

        # Load evaluations with assignments
        evaluations = (
            self.db.query(Evaluation, Assignment)
            .join(Assignment, Evaluation.assignment_id == Assignment.id)
            .filter(
                Assignment.cycle_id == cycle_id,
                Assignment.target_email == target_email,
                Evaluation.status == "submitted",
                Evaluation.rating.isnot(None),
            )
            .all()
        )

        if not evaluations:
            return StaffTypeScore(
                staff_type=staff_type,
                target_email=target_email,
                total_evaluations=0,
                raw_average=0.0,
                weighted_average=0.0,
                context_breakdown={},
                final_score=0.0,
                score_components={},
            )

        # Group by context
        context_scores = defaultdict(list)
        context_weights = defaultdict(list)

        for eval_obj, assignment in evaluations:
            context = assignment.rater_context or "peer_review"
            weight = weight_matrix.get(context, 1.0)

            # Apply assignment-specific weight multiplier if present
            final_weight = weight * (assignment.weight if assignment.weight else 1.0)

            context_scores[context].append(eval_obj.rating)
            context_weights[context].append(final_weight)

        # Calculate context breakdown
        context_breakdown = {}
        all_weighted_scores = []
        all_weights = []

        for context, scores in context_scores.items():
            weights = context_weights[context]

            raw_avg = float(np.mean(scores))

            # Calculate weighted average for this context
            weighted_scores = [s * w for s, w in zip(scores, weights)]
            weighted_avg = float(np.mean(weighted_scores)) if weighted_scores else 0.0

            context_breakdown[context] = {
                "count": len(scores),
                "raw_average": raw_avg,
                "weighted_average": weighted_avg,
                "weight": float(np.mean(weights)) if weights else 0.0,
                "min": float(np.min(scores)),
                "max": float(np.max(scores)),
                "std": float(np.std(scores)),
            }

            # Collect for overall calculation
            all_weighted_scores.extend(weighted_scores)
            all_weights.extend(weights)

        # Calculate overall scores
        raw_average = float(np.mean([s for scores in context_scores.values() for s in scores]))

        # Weighted average: sum(score * weight) / sum(weight)
        total_weighted = sum(all_weighted_scores)
        total_weight = sum(all_weights)
        weighted_average = total_weighted / total_weight if total_weight > 0 else 0.0

        # Final score (can be adjusted based on requirements)
        final_score = weighted_average

        return StaffTypeScore(
            staff_type=staff_type,
            target_email=target_email,
            total_evaluations=len(evaluations),
            raw_average=raw_average,
            weighted_average=weighted_average,
            context_breakdown=context_breakdown,
            final_score=final_score,
            score_components={},
        )

    def calculate_batch_scores(
        self, cycle_id: int, staff_type: Optional[str] = None, target_emails: Optional[List[str]] = None
    ) -> List[StaffTypeScore]:
        """
        Calculate weighted scores for multiple staff members.

        Args:
            cycle_id: Evaluation cycle ID
            staff_type: Filter by staff type ('academic' or 'admin')
            target_emails: Optional list of specific emails to calculate

        Returns:
            List of StaffTypeScore objects
        """
        # Get target emails
        if target_emails:
            people = self.db.query(Person).filter(Person.email.in_(target_emails), Person.active == True).all()
        else:
            # Get all active people
            people = self.db.query(Person).filter(Person.active == True).all()

        scores = []

        for person in people:
            person_staff_type = self.get_staff_type(person)

            # Filter by staff type if specified
            if staff_type and person_staff_type.lower() != staff_type.lower():
                continue

            try:
                score = self.calculate_weighted_score(
                    cycle_id=cycle_id, target_email=person.email, staff_type=person_staff_type
                )
                scores.append(score)
            except Exception as e:
                self.logger.warning(f"Error calculating score for {person.email}: {e}")
                continue

        return scores

    def compare_academic_vs_admin(self, cycle_id: int) -> ComparisonResult:
        """
        Compare scoring between academic and admin staff.

        Args:
            cycle_id: Evaluation cycle ID

        Returns:
            ComparisonResult with statistics and recommendations
        """
        # Calculate scores for all staff
        academic_scores = self.calculate_batch_scores(cycle_id=cycle_id, staff_type="academic")

        admin_scores = self.calculate_batch_scores(cycle_id=cycle_id, staff_type="admin")

        # Calculate statistics
        academic_stats = self._calculate_statistics(academic_scores)
        admin_stats = self._calculate_statistics(admin_scores)

        # Calculate differences
        differences = {
            "mean_difference": academic_stats["mean_weighted"] - admin_stats["mean_weighted"],
            "median_difference": academic_stats["median_weighted"] - admin_stats["median_weighted"],
            "std_difference": academic_stats["std_weighted"] - admin_stats["std_weighted"],
            "count_difference": len(academic_scores) - len(admin_scores),
        }

        # Generate recommendations
        recommendations = self._generate_recommendations(academic_stats, admin_stats, differences)

        return ComparisonResult(
            cycle_id=cycle_id,
            academic_stats=academic_stats,
            admin_stats=admin_stats,
            differences=differences,
            recommendations=recommendations,
        )

    def _calculate_statistics(self, scores: List[StaffTypeScore]) -> Dict:
        """Calculate statistics for a list of scores"""
        if not scores:
            return {
                "count": 0,
                "mean_weighted": 0.0,
                "median_weighted": 0.0,
                "std_weighted": 0.0,
                "mean_raw": 0.0,
                "min_weighted": 0.0,
                "max_weighted": 0.0,
            }

        weighted_scores = [s.weighted_average for s in scores]
        raw_scores = [s.raw_average for s in scores]

        return {
            "count": len(scores),
            "mean_weighted": float(np.mean(weighted_scores)),
            "median_weighted": float(np.median(weighted_scores)),
            "std_weighted": float(np.std(weighted_scores)),
            "mean_raw": float(np.mean(raw_scores)),
            "min_weighted": float(np.min(weighted_scores)),
            "max_weighted": float(np.max(weighted_scores)),
            "q25_weighted": float(np.percentile(weighted_scores, 25)),
            "q75_weighted": float(np.percentile(weighted_scores, 75)),
        }

    def _generate_recommendations(self, academic_stats: Dict, admin_stats: Dict, differences: Dict) -> List[str]:
        """Generate recommendations based on comparison"""
        recommendations = []

        # Check for significant differences
        mean_diff = abs(differences["mean_difference"])
        if mean_diff > 0.5:
            recommendations.append(
                f"Significant difference in mean scores: {mean_diff:.2f} points. " "Review weight matrices to ensure fairness."
            )

        # Check evaluation counts
        count_diff = differences["count_difference"]
        if abs(count_diff) > 0:
            recommendations.append(
                f"Different number of evaluations: Academic ({academic_stats['count']}) vs "
                f"Admin ({admin_stats['count']}). Ensure balanced evaluation coverage."
            )

        # Check standard deviations
        if academic_stats["std_weighted"] > 1.5 or admin_stats["std_weighted"] > 1.5:
            recommendations.append("High variance in scores detected. Review evaluation criteria and rater training.")

        # Check for fairness
        if mean_diff < 0.2 and academic_stats["count"] > 0 and admin_stats["count"] > 0:
            recommendations.append(
                "Scores are relatively balanced between academic and admin staff. " "Current weight matrices appear fair."
            )

        if not recommendations:
            recommendations.append("No significant issues detected. Continue monitoring scores for fairness.")

        return recommendations

    def validate_evaluations(self, cycle_id: int, staff_type: str) -> Dict:
        """
        Validate that evaluations meet minimum/maximum requirements for a staff type.

        Args:
            cycle_id: Evaluation cycle ID
            staff_type: 'academic' or 'admin'

        Returns:
            Validation result with errors and warnings
        """
        min_reqs = self.MIN_EVALUATIONS.get(staff_type, {})
        max_reqs = self.MAX_EVALUATIONS.get(staff_type, {})

        # Get all people of this staff type
        people = self.db.query(Person).filter(Person.active == True).all()

        staff_people = [p for p in people if self.get_staff_type(p).lower() == staff_type.lower()]

        errors = []
        warnings = []

        for person in staff_people:
            # Get evaluations for this person
            evaluations = (
                self.db.query(Evaluation, Assignment)
                .join(Assignment, Evaluation.assignment_id == Assignment.id)
                .filter(
                    Assignment.cycle_id == cycle_id, Assignment.target_email == person.email, Evaluation.status == "submitted"
                )
                .all()
            )

            # Count by context
            context_counts = defaultdict(int)
            for eval_obj, assignment in evaluations:
                context = assignment.rater_context or "peer_review"
                context_counts[context] += 1

            # Check minimums
            for context, min_count in min_reqs.items():
                actual = context_counts.get(context, 0)
                if actual < min_count:
                    errors.append(
                        f"{person.email} ({staff_type}): Only {actual} {context} evaluation(s), "
                        f"minimum {min_count} required"
                    )

            # Check maximums
            for context, max_count in max_reqs.items():
                actual = context_counts.get(context, 0)
                if actual > max_count:
                    warnings.append(
                        f"{person.email} ({staff_type}): {actual} {context} evaluation(s), " f"maximum {max_count} recommended"
                    )

        return {
            "staff_type": staff_type,
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "total_people_checked": len(staff_people),
        }

    def get_score_distribution(self, cycle_id: int, staff_type: Optional[str] = None) -> Dict:
        """
        Get score distribution for academic or admin staff.

        Args:
            cycle_id: Evaluation cycle ID
            staff_type: 'academic', 'admin', or None for both

        Returns:
            Distribution statistics
        """
        if staff_type:
            scores = self.calculate_batch_scores(cycle_id=cycle_id, staff_type=staff_type)
        else:
            academic_scores = self.calculate_batch_scores(cycle_id=cycle_id, staff_type="academic")
            admin_scores = self.calculate_batch_scores(cycle_id=cycle_id, staff_type="admin")
            scores = academic_scores + admin_scores

        if not scores:
            return {"staff_type": staff_type or "all", "count": 0, "distribution": {}}

        weighted_scores = [s.weighted_average for s in scores]

        # Create distribution bins
        bins = [0, 1, 2, 3, 4, 5, float("inf")]
        labels = ["0-1", "1-2", "2-3", "3-4", "4-5", "5+"]

        hist, _ = np.histogram(weighted_scores, bins=bins)

        distribution = {label: int(count) for label, count in zip(labels, hist)}

        return {
            "staff_type": staff_type or "all",
            "count": len(scores),
            "distribution": distribution,
            "mean": float(np.mean(weighted_scores)),
            "median": float(np.median(weighted_scores)),
            "std": float(np.std(weighted_scores)),
            "min": float(np.min(weighted_scores)),
            "max": float(np.max(weighted_scores)),
        }

    def export_scores_to_dict(self, scores: List[StaffTypeScore]) -> List[Dict]:
        """Export scores to dictionary format for API responses"""
        return [asdict(score) for score in scores]
