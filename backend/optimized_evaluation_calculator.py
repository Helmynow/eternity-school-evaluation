"""
Optimized Evaluation Calculator for Large-Scale Processing (200+ Staff)
Uses bulk queries, vectorized operations, and efficient data structures.
"""

import logging
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sqlalchemy.orm import joinedload

from backend.database import Assignment, Cycle, Evaluation, Person


@dataclass
class OptimizedScore:
    """Optimized score structure for batch processing"""

    target_email: str
    staff_type: str
    total_evaluations: int
    raw_average: float
    weighted_average: float
    final_score: float
    context_breakdown: Dict[str, Dict]


class OptimizedEvaluationCalculator:
    """
    Optimized evaluation calculator for processing 200+ staff members efficiently.

    Key optimizations:
    - Bulk database queries (single query for all data)
    - Vectorized operations with NumPy/Pandas
    - Cached staff type lookups
    - Efficient data structures
    - Memory-efficient processing
    """

    # Expose the score dataclass via the class/instance for unit tests and callers.
    OptimizedScore = OptimizedScore

    # Academic Staff Weight Matrix
    ACADEMIC_WEIGHT_MATRIX = {
        "CEO": 1.0,
        "P&C": 0.8,
        "QA": 1.0,
        "peer_review": 0.9,
        "manager_review": 1.0,
        "direct_report_review": 0.7,
        "self_review": 0.5,
        "360_review": 0.85,
    }

    # Admin Staff Weight Matrix
    ADMIN_WEIGHT_MATRIX = {
        "CEO": 1.0,
        "P&C": 1.0,
        "QA": 0.7,
        "peer_review": 0.8,
        "manager_review": 1.0,
        "direct_report_review": 0.6,
        "self_review": 0.5,
        "360_review": 0.85,
    }

    def __init__(self, db_session):
        self.db = db_session
        self.logger = logging.getLogger(__name__)
        self._staff_type_cache = {}  # Cache for staff type lookups
        self._weight_matrix_cache = {"academic": self.ACADEMIC_WEIGHT_MATRIX, "admin": self.ADMIN_WEIGHT_MATRIX}

    def _get_staff_type_cached(self, person: Person) -> str:
        """Get staff type with caching"""
        if person.email in self._staff_type_cache:
            return self._staff_type_cache[person.email]

        staff_type = self._determine_staff_type(person)
        self._staff_type_cache[person.email] = staff_type
        return staff_type

    def _determine_staff_type(self, person: Person) -> str:
        """Determine staff type from person attributes"""
        if not person:
            return "academic"

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

        return "academic"  # Default

    def _load_all_data_bulk(
        self, cycle_id: int, target_emails: Optional[List[str]] = None
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Load all evaluation data in bulk using optimized queries.

        Returns:
            Tuple of (evaluations_df, people_df) DataFrames
        """
        # Build base query for evaluations
        query = (
            self.db.query(
                Evaluation.id,
                Evaluation.assignment_id,
                Evaluation.rating,
                Evaluation.status,
                Assignment.id.label("assignment_id"),
                Assignment.cycle_id,
                Assignment.rater_email,
                Assignment.target_email,
                Assignment.rater_context,
                Assignment.target_group,
                Assignment.weight.label("assignment_weight"),
            )
            .join(Assignment, Evaluation.assignment_id == Assignment.id)
            .filter(Assignment.cycle_id == cycle_id, Evaluation.status == "submitted", Evaluation.rating.isnot(None))
        )

        # Filter by target emails if provided
        if target_emails:
            query = query.filter(Assignment.target_email.in_(target_emails))

        # Execute query and convert to DataFrame
        evaluations_data = query.all()

        if not evaluations_data:
            return pd.DataFrame(), pd.DataFrame()

        # Convert to list of dicts for DataFrame creation
        eval_dicts = [
            {
                "evaluation_id": e.id,
                "assignment_id": e.assignment_id,
                "rating": float(e.rating),
                "rater_email": e.rater_email,
                "target_email": e.target_email,
                "rater_context": e.rater_context or "peer_review",
                "target_group": e.target_group or "other",
                "assignment_weight": float(e.assignment_weight) if e.assignment_weight else 1.0,
            }
            for e in evaluations_data
        ]

        evaluations_df = pd.DataFrame(eval_dicts)

        # Load all people in bulk
        people_query = self.db.query(Person)
        if target_emails:
            people_query = people_query.filter(Person.email.in_(target_emails))
        else:
            # Get unique target emails from evaluations
            if not evaluations_df.empty:
                unique_emails = evaluations_df["target_email"].unique().tolist()
                people_query = people_query.filter(Person.email.in_(unique_emails))

        people_data = people_query.all()

        if not people_data:
            return evaluations_df, pd.DataFrame()

        # Convert people to DataFrame
        people_dicts = [
            {
                "email": p.email,
                "full_name": p.full_name,
                "role_title": p.role_title,
                "department": p.department,
                "segment": p.segment.value if p.segment else None,
                "active": p.active,
            }
            for p in people_data
        ]

        people_df = pd.DataFrame(people_dicts)

        # Build staff type cache
        for person in people_data:
            if person.email not in self._staff_type_cache:
                self._staff_type_cache[person.email] = self._determine_staff_type(person)

        return evaluations_df, people_df

    def _apply_weights_vectorized(self, evaluations_df: pd.DataFrame, people_df: pd.DataFrame) -> pd.DataFrame:
        """
        Apply weights to evaluations using vectorized operations.

        Returns:
            DataFrame with weighted scores added
        """
        if evaluations_df.empty:
            return evaluations_df

        # Add staff type column
        staff_type_map = {
            email: self._staff_type_cache.get(email, "academic") for email in evaluations_df["target_email"].unique()
        }
        evaluations_df["staff_type"] = evaluations_df["target_email"].map(staff_type_map)

        # Create weight lookup function
        def get_weight(row):
            staff_type = row["staff_type"]
            rater_context = row["rater_context"]

            weight_matrix = self._weight_matrix_cache.get(staff_type, self.ACADEMIC_WEIGHT_MATRIX)
            base_weight = weight_matrix.get(rater_context, 1.0)

            # Apply assignment-specific weight multiplier
            return base_weight * row["assignment_weight"]

        # Apply weights vectorized
        evaluations_df["base_weight"] = evaluations_df.apply(get_weight, axis=1)
        evaluations_df["weighted_score"] = evaluations_df["rating"] * evaluations_df["base_weight"]

        return evaluations_df

    def calculate_batch_scores_optimized(
        self, cycle_id: int, staff_type: Optional[str] = None, target_emails: Optional[List[str]] = None
    ) -> List[OptimizedScore]:
        """
        Calculate scores for all staff members using optimized bulk processing.

        This method is optimized for 200+ staff members:
        - Single bulk query for all evaluations
        - Single bulk query for all people
        - Vectorized weight application
        - Efficient grouping and aggregation

        Args:
            cycle_id: Evaluation cycle ID
            staff_type: Filter by staff type (academic/admin)
            target_emails: Optional list of specific emails

        Returns:
            List of OptimizedScore objects
        """
        # Load all data in bulk
        evaluations_df, people_df = self._load_all_data_bulk(cycle_id, target_emails)

        if evaluations_df.empty:
            self.logger.warning(f"No evaluations found for cycle {cycle_id}")
            return []

        # Apply weights using vectorized operations
        evaluations_df = self._apply_weights_vectorized(evaluations_df, people_df)

        # Filter by staff type if specified
        if staff_type:
            evaluations_df = evaluations_df[evaluations_df["staff_type"].str.lower() == staff_type.lower()]

        # Group by target_email and calculate aggregates using vectorized operations
        grouped = evaluations_df.groupby("target_email")

        results = []

        for target_email, group_df in grouped:
            # Vectorized calculations
            ratings = group_df["rating"].values
            weights = group_df["base_weight"].values
            weighted_scores = group_df["weighted_score"].values

            # Calculate averages
            raw_average = float(np.mean(ratings))
            total_weight = float(np.sum(weights))
            weighted_average = float(np.sum(weighted_scores) / total_weight) if total_weight > 0 else 0.0

            # Build context breakdown efficiently
            context_grouped = group_df.groupby("rater_context")
            context_breakdown = {}

            for context, context_df in context_grouped:
                context_ratings = context_df["rating"].values
                context_weights = context_df["base_weight"].values
                context_weighted = context_df["weighted_score"].values

                context_breakdown[context] = {
                    "count": len(context_df),
                    "raw_average": float(np.mean(context_ratings)),
                    "weighted_average": (
                        float(np.sum(context_weighted) / np.sum(context_weights)) if np.sum(context_weights) > 0 else 0.0
                    ),
                    "weight": float(np.mean(context_weights)),
                    "min": float(np.min(context_ratings)),
                    "max": float(np.max(context_ratings)),
                    "std": float(np.std(context_ratings)),
                }

            # Get staff type
            staff_type_value = self._staff_type_cache.get(target_email, "academic")

            results.append(
                OptimizedScore(
                    target_email=target_email,
                    staff_type=staff_type_value,
                    total_evaluations=len(group_df),
                    raw_average=raw_average,
                    weighted_average=weighted_average,
                    final_score=weighted_average,
                    context_breakdown=context_breakdown,
                )
            )

        return results

    def calculate_single_score_optimized(
        self, cycle_id: int, target_email: str, staff_type: Optional[str] = None
    ) -> Optional[OptimizedScore]:
        """
        Calculate score for a single staff member using optimized approach.

        Args:
            cycle_id: Evaluation cycle ID
            target_email: Email of staff member
            staff_type: Optional staff type override

        Returns:
            OptimizedScore or None if not found
        """
        results = self.calculate_batch_scores_optimized(cycle_id=cycle_id, staff_type=staff_type, target_emails=[target_email])

        return results[0] if results else None

    def get_score_statistics(self, cycle_id: int, staff_type: Optional[str] = None) -> Dict:
        """
        Get aggregate statistics for all scores in a cycle.
        Uses optimized bulk processing.

        Args:
            cycle_id: Evaluation cycle ID
            staff_type: Filter by staff type

        Returns:
            Dictionary with statistics
        """
        scores = self.calculate_batch_scores_optimized(cycle_id=cycle_id, staff_type=staff_type)

        if not scores:
            return {"count": 0, "mean": 0.0, "median": 0.0, "std": 0.0, "min": 0.0, "max": 0.0}

        # Extract weighted averages for statistics
        weighted_averages = np.array([s.weighted_average for s in scores])

        return {
            "count": len(scores),
            "mean": float(np.mean(weighted_averages)),
            "median": float(np.median(weighted_averages)),
            "std": float(np.std(weighted_averages)),
            "min": float(np.min(weighted_averages)),
            "max": float(np.max(weighted_averages)),
            "q25": float(np.percentile(weighted_averages, 25)),
            "q75": float(np.percentile(weighted_averages, 75)),
        }

    def compare_academic_vs_admin_optimized(self, cycle_id: int) -> Dict:
        """
        Compare academic vs admin scoring using optimized bulk processing.

        Args:
            cycle_id: Evaluation cycle ID

        Returns:
            Dictionary with comparison statistics
        """
        # Calculate all scores at once
        all_scores = self.calculate_batch_scores_optimized(cycle_id=cycle_id)

        # Separate by staff type
        academic_scores = [s for s in all_scores if s.staff_type == "academic"]
        admin_scores = [s for s in all_scores if s.staff_type == "admin"]

        # Calculate statistics using NumPy
        academic_avgs = np.array([s.weighted_average for s in academic_scores]) if academic_scores else np.array([])
        admin_avgs = np.array([s.weighted_average for s in admin_scores]) if admin_scores else np.array([])

        academic_stats = {
            "count": len(academic_scores),
            "mean": float(np.mean(academic_avgs)) if len(academic_avgs) > 0 else 0.0,
            "median": float(np.median(academic_avgs)) if len(academic_avgs) > 0 else 0.0,
            "std": float(np.std(academic_avgs)) if len(academic_avgs) > 0 else 0.0,
            "min": float(np.min(academic_avgs)) if len(academic_avgs) > 0 else 0.0,
            "max": float(np.max(academic_avgs)) if len(academic_avgs) > 0 else 0.0,
        }

        admin_stats = {
            "count": len(admin_scores),
            "mean": float(np.mean(admin_avgs)) if len(admin_avgs) > 0 else 0.0,
            "median": float(np.median(admin_avgs)) if len(admin_avgs) > 0 else 0.0,
            "std": float(np.std(admin_avgs)) if len(admin_avgs) > 0 else 0.0,
            "min": float(np.min(admin_avgs)) if len(admin_avgs) > 0 else 0.0,
            "max": float(np.max(admin_avgs)) if len(admin_avgs) > 0 else 0.0,
        }

        # Calculate differences
        mean_diff = academic_stats["mean"] - admin_stats["mean"]

        # Generate recommendations
        recommendations = []
        if abs(mean_diff) > 0.5:
            recommendations.append(
                f"Significant difference in mean scores: {mean_diff:.2f} points. " "Review weight matrices to ensure fairness."
            )

        if academic_stats["count"] != admin_stats["count"]:
            recommendations.append(
                f"Different number of evaluations: Academic ({academic_stats['count']}) vs "
                f"Admin ({admin_stats['count']}). Ensure balanced evaluation coverage."
            )

        return {
            "cycle_id": cycle_id,
            "academic_stats": academic_stats,
            "admin_stats": admin_stats,
            "differences": {
                "mean_difference": mean_diff,
                "median_difference": academic_stats["median"] - admin_stats["median"],
                "std_difference": academic_stats["std"] - admin_stats["std"],
                "count_difference": academic_stats["count"] - admin_stats["count"],
            },
            "recommendations": recommendations,
        }

    def export_scores_to_dataframe(self, cycle_id: int, staff_type: Optional[str] = None) -> pd.DataFrame:
        """
        Export scores to pandas DataFrame for further analysis.

        Args:
            cycle_id: Evaluation cycle ID
            staff_type: Filter by staff type

        Returns:
            DataFrame with all scores
        """
        scores = self.calculate_batch_scores_optimized(cycle_id=cycle_id, staff_type=staff_type)

        if not scores:
            return pd.DataFrame()

        # Convert to list of dicts
        data = [
            {
                "target_email": s.target_email,
                "staff_type": s.staff_type,
                "total_evaluations": s.total_evaluations,
                "raw_average": s.raw_average,
                "weighted_average": s.weighted_average,
                "final_score": s.final_score,
            }
            for s in scores
        ]

        return pd.DataFrame(data)

    def clear_cache(self):
        """Clear internal caches"""
        self._staff_type_cache.clear()
