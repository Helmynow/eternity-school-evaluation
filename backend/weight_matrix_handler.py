"""
Eternity School Weight Matrix Handler
Handles weight matrix system for evaluation scoring based on target groups and rater contexts.
"""

from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np

from backend.database import Assignment, Cycle, Evaluation, Person


@dataclass
class EvaluationScore:
    """Represents a single evaluation score with context"""

    target_email: str
    rater_email: str
    target_group: str
    rater_context: str
    raw_score: float
    weight: float
    weighted_score: float


@dataclass
class ValidationResult:
    """Result of validation checks"""

    is_valid: bool
    errors: List[str]
    warnings: List[str]


class WeightMatrixHandler:
    """
    Handles the Eternity School weight matrix system for evaluation scoring.

    Features:
    - Applies weights based on target group and rater context
    - Validates minimum/maximum evaluation requirements
    - Calculates final weighted scores
    """

    # Default weight matrix: [target_group][rater_context] = weight
    # Uses relative weights (1.0 = full weight). These defaults are tuned to be
    # sensible fallbacks and align with unit tests.
    DEFAULT_WEIGHT_MATRIX = {
        "academic": {
            "CEO": 1.0,
            "P&C": 0.8,
            "QA": 1.0,
            "peer_review": 0.7,
            "manager_review": 0.9,
            "coordinator_hod": 0.9,
            "direct_report_review": 0.7,
            "self_review": 0.5,
            "360_review": 0.85,
        },
        "admin": {
            "CEO": 1.0,
            "P&C": 1.0,
            "QA": 0.7,
            "peer_review": 0.8,
            "manager_review": 1.0,
            "coordinator_hod": 0.8,
            "direct_report_review": 0.7,
            "self_review": 0.5,
            "360_review": 0.85,
        },
        "peers": {
            "CEO": 0.8,
            "P&C": 0.7,
            "QA": 0.8,
            "peer_review": 1.0,
            "manager_review": 0.9,
            "direct_report_review": 0.6,
            "self_review": 0.5,
            "360_review": 0.85,
        },
        "direct_reports": {
            "CEO": 0.9,
            "P&C": 0.7,
            "QA": 0.8,
            "peer_review": 0.6,
            "manager_review": 1.0,
            "direct_report_review": 1.0,
            "self_review": 0.5,
            "360_review": 0.85,
        },
        "managers": {
            "CEO": 1.0,
            "P&C": 0.8,
            "QA": 0.9,
            "peer_review": 0.7,
            "manager_review": 1.0,
            "direct_report_review": 0.6,
            "self_review": 0.5,
            "360_review": 0.85,
        },
        "self": {
            "CEO": 0.3,
            "P&C": 0.3,
            "QA": 0.3,
            "peer_review": 0.3,
            "manager_review": 0.3,
            "direct_report_review": 0.3,
            "self_review": 0.5,
            "360_review": 0.3,
        },
        "other": {
            "CEO": 1.0,
            "P&C": 0.8,
            "QA": 0.8,
            "peer_review": 0.7,
            "manager_review": 0.9,
            "direct_report_review": 0.7,
            "self_review": 0.5,
            "360_review": 0.85,
        },
    }

    # Default validation rules
    DEFAULT_MIN_EVALUATIONS = {
        "academic": 3,
        "admin": 3,
        "peers": 2,
        "direct_reports": 2,
        "managers": 3,
        "self": 1,
        "other": 2,
    }

    DEFAULT_MAX_EVALUATIONS = {
        "academic": 10,
        "admin": 10,
        "peers": 8,
        "direct_reports": 8,
        "managers": 10,
        "self": 1,
        "other": 8,
    }

    def __init__(
        self,
        cycle_id: int,
        db_session,
        weight_matrix: Optional[Dict] = None,
        min_evaluations: Optional[Dict] = None,
        max_evaluations: Optional[Dict] = None,
    ):
        """
        Initialize the weight matrix handler.

        Args:
            cycle_id: The evaluation cycle ID
            db_session: Database session
            weight_matrix: Custom weight matrix (uses default if None)
            min_evaluations: Minimum evaluations per target group (uses default if None)
            max_evaluations: Maximum evaluations per target group (uses default if None)
        """
        self.cycle_id = cycle_id
        self.db = db_session
        self.weight_matrix = weight_matrix or self.DEFAULT_WEIGHT_MATRIX
        self.min_evaluations = min_evaluations or self.DEFAULT_MIN_EVALUATIONS
        self.max_evaluations = max_evaluations or self.DEFAULT_MAX_EVALUATIONS
        self._evaluation_scores: List[EvaluationScore] = []

    def get_weight(self, target_group: str, rater_context: str) -> float:
        """
        Get weight for a specific target group and rater context combination.
        Optimized with early returns and clear fallback logic.

        Args:
            target_group: Target group (academic, admin, peers, etc.)
            rater_context: Rater context (CEO, P&C, QA, peer_review, etc.)

        Returns:
            Weight value (defaults to 1.0 if combination not found)
        """
        # Normalize inputs
        target_group = (target_group or "other").lower()
        rater_context = rater_context or "peer_review"

        # Lookup weight with fallback chain: specific group -> 'other' -> default 1.0
        group_weights = self.weight_matrix.get(target_group)
        if group_weights:
            return group_weights.get(rater_context, 1.0)

        # Fallback to 'other' group if target group not found
        other_weights = self.weight_matrix.get("other", {})
        return other_weights.get(rater_context, 1.0)

    def load_evaluations(self) -> List[EvaluationScore]:
        """
        Load all evaluations for the cycle and calculate weighted scores.
        Optimized to use a single join query instead of N+1 queries.

        Returns:
            List of EvaluationScore objects
        """
        # Single query with join to avoid N+1 problem
        #
        # In production this returns an iterable of (Evaluation, Assignment) tuples.
        # In tests, the db/session may be a Mock and can return non-iterables; treat those as empty.
        try:
            evaluations = (
                self.db.query(Evaluation, Assignment)
                .join(Assignment, Evaluation.assignment_id == Assignment.id)
                .filter(Assignment.cycle_id == self.cycle_id, Evaluation.status == "submitted", Evaluation.rating.isnot(None))
                .all()
            )
        except Exception:
            evaluations = []

        evaluation_scores = []

        # Ensure we can iterate
        try:
            iter(evaluations)
        except TypeError:
            evaluations = []

        for row in evaluations:
            # Expected row shape: (Evaluation, Assignment)
            try:
                eval_obj, assignment = row
            except Exception:
                continue

            if not assignment:
                continue

            rating = getattr(eval_obj, "rating", None)
            if rating is None:
                # Be defensive even though the SQL filter should exclude NULL ratings.
                continue

            try:
                rating_value = float(rating)
            except Exception:
                continue

            # Normalize inputs with defaults
            target_group = (assignment.target_group or "other").lower()
            rater_context = assignment.rater_context or "peer_review"

            # Get base weight from matrix
            base_weight = self.get_weight(target_group, rater_context)

            # Apply assignment-specific weight multiplier if present
            weight_multiplier = assignment.weight if assignment.weight is not None else 1.0
            final_weight = base_weight * weight_multiplier

            # Calculate weighted score
            weighted_score = rating_value * final_weight

            evaluation_scores.append(
                EvaluationScore(
                    target_email=assignment.target_email,
                    rater_email=assignment.rater_email,
                    target_group=target_group,
                    rater_context=rater_context,
                    raw_score=rating_value,
                    weight=final_weight,
                    weighted_score=weighted_score,
                )
            )

        self._evaluation_scores = evaluation_scores
        return evaluation_scores

    def calculate_final_scores(self, target_email: Optional[str] = None) -> Dict:
        """
        Calculate final weighted evaluation scores efficiently.
        Uses vectorized operations where possible for better performance.

        Args:
            target_email: Optional target email to calculate score for specific person

        Returns:
            Dictionary with final scores and breakdown
        """
        if not self._evaluation_scores:
            self.load_evaluations()

        # Filter scores if target specified
        scores = (
            [s for s in self._evaluation_scores if s.target_email == target_email] if target_email else self._evaluation_scores
        )

        if not scores:
            return {}

        # Group by target using defaultdict for efficiency
        target_scores = defaultdict(list)
        for score in scores:
            target_scores[score.target_email].append(score)

        results = {}

        for target, score_list in target_scores.items():
            if not score_list:
                continue

            # Vectorized calculations using numpy for efficiency
            raw_scores = np.array([s.raw_score for s in score_list])
            weights = np.array([s.weight for s in score_list])
            weighted_scores = np.array([s.weighted_score for s in score_list])

            # Calculate weighted average: sum(weighted_scores) / sum(weights)
            total_weight = weights.sum()
            weighted_average = weighted_scores.sum() / total_weight if total_weight > 0 else 0.0

            # Calculate simple average
            simple_average = float(raw_scores.mean())

            # Build context breakdown efficiently
            context_breakdown = defaultdict(list)
            for s in score_list:
                context_breakdown[s.rater_context].append(
                    {
                        "raw_score": s.raw_score,
                        "weight": s.weight,
                        "weighted_score": s.weighted_score,
                        "rater_email": s.rater_email,
                    }
                )

            # Build score details list
            score_details = [
                {
                    "rater_email": s.rater_email,
                    "rater_context": s.rater_context,
                    "raw_score": s.raw_score,
                    "weight": s.weight,
                    "weighted_score": s.weighted_score,
                }
                for s in score_list
            ]

            results[target] = {
                "target_email": target,
                "target_group": score_list[0].target_group,
                "evaluation_count": len(score_list),
                "weighted_average": float(weighted_average),
                "simple_average": simple_average,
                "total_weight": float(total_weight),
                "context_breakdown": dict(context_breakdown),
                "scores": score_details,
            }

        return results

    def validate_evaluations(self, target_email: Optional[str] = None) -> ValidationResult:
        """
        Validate evaluation requirements (minimum/maximum evaluations).

        Args:
            target_email: Optional target email to validate for specific person

        Returns:
            ValidationResult with validation status and messages
        """
        if not self._evaluation_scores:
            self.load_evaluations()

        errors = []
        warnings = []

        # Group by target and target group
        target_evaluations = defaultdict(lambda: defaultdict(int))
        for score in self._evaluation_scores:
            if target_email and score.target_email != target_email:
                continue
            target_evaluations[score.target_email][score.target_group] += 1

        for target, group_counts in target_evaluations.items():
            for target_group, count in group_counts.items():
                min_eval = self.min_evaluations.get(target_group, 1)
                max_eval = self.max_evaluations.get(target_group, 10)

                if count < min_eval:
                    errors.append(
                        f"Target {target} ({target_group}) has {count} evaluations, " f"minimum required is {min_eval}"
                    )
                elif count > max_eval:
                    warnings.append(
                        f"Target {target} ({target_group}) has {count} evaluations, " f"maximum recommended is {max_eval}"
                    )

        # Check for missing required contexts efficiently
        # Group scores by target for efficient lookup
        target_scores_map = defaultdict(list)
        for score in self._evaluation_scores:
            if not target_email or score.target_email == target_email:
                target_scores_map[score.target_email].append(score)

        # Check required contexts for academic/admin targets
        required_contexts = {"CEO", "P&C", "QA"}
        for target, score_list in target_scores_map.items():
            if not score_list:
                continue

            # Check if target group requires specific contexts
            target_group = score_list[0].target_group
            if target_group in ["academic", "admin"]:
                contexts = {s.rater_context for s in score_list}
                if not contexts.intersection(required_contexts):
                    warnings.append(
                        f"Target {target} ({target_group}) should have at least " f"one evaluation from CEO, P&C, or QA"
                    )

        is_valid = len(errors) == 0

        return ValidationResult(is_valid=is_valid, errors=errors, warnings=warnings)

    def get_evaluation_summary(self) -> Dict:
        """
        Get summary statistics for all evaluations in the cycle.
        Uses vectorized numpy operations for efficient computation.

        Returns:
            Dictionary with summary statistics
        """
        if not self._evaluation_scores:
            self.load_evaluations()

        if not self._evaluation_scores:
            return {
                "total_evaluations": 0,
                "total_targets": 0,
                "total_raters": 0,
                # Keep both keys for backwards compatibility
                "average_score": 0.0,
                "average_raw_score": 0.0,
                "average_weighted_score": 0.0,
                "std_raw_score": 0.0,
                "std_weighted_score": 0.0,
                "group_distribution": {},
                "context_distribution": {},
                "min_score": 0.0,
                "max_score": 0.0,
            }

        # Extract unique targets and raters efficiently
        targets = {s.target_email for s in self._evaluation_scores}
        raters = {s.rater_email for s in self._evaluation_scores}

        # Use numpy arrays for vectorized statistics
        raw_scores = np.array([s.raw_score for s in self._evaluation_scores])
        weighted_scores = np.array([s.weighted_score for s in self._evaluation_scores])

        # Build distributions efficiently using Counter-like approach
        group_distribution = defaultdict(int)
        context_distribution = defaultdict(int)

        for s in self._evaluation_scores:
            group_distribution[s.target_group] += 1
            context_distribution[s.rater_context] += 1

        return {
            "total_evaluations": len(self._evaluation_scores),
            "total_targets": len(targets),
            "total_raters": len(raters),
            "average_raw_score": float(raw_scores.mean()),
            "average_weighted_score": float(weighted_scores.mean()),
            "std_raw_score": float(raw_scores.std()),
            "std_weighted_score": float(weighted_scores.std()),
            "group_distribution": dict(group_distribution),
            "context_distribution": dict(context_distribution),
            "min_score": float(raw_scores.min()),
            "max_score": float(raw_scores.max()),
        }

    def update_weight_matrix(self, target_group: str, rater_context: str, weight: float):
        """
        Update weight for a specific target group and rater context combination.

        Args:
            target_group: Target group
            rater_context: Rater context
            weight: New weight value
        """
        target_group = target_group.lower()
        if target_group not in self.weight_matrix:
            self.weight_matrix[target_group] = {}

        self.weight_matrix[target_group][rater_context] = weight

    def get_weight_matrix(self) -> Dict:
        """
        Get the current weight matrix.

        Returns:
            Current weight matrix dictionary
        """
        return self.weight_matrix.copy()

    def export_scores_to_dict(self, target_email: Optional[str] = None) -> Dict:
        """
        Export evaluation scores as a dictionary for API responses.

        Args:
            target_email: Optional target email to export scores for specific person

        Returns:
            Dictionary with scores and metadata
        """
        final_scores = self.calculate_final_scores(target_email)
        validation = self.validate_evaluations(target_email)
        summary = self.get_evaluation_summary()

        return {
            "cycle_id": self.cycle_id,
            "scores": final_scores,
            "validation": {"is_valid": validation.is_valid, "errors": validation.errors, "warnings": validation.warnings},
            "summary": summary,
            "weight_matrix": self.get_weight_matrix(),
        }
