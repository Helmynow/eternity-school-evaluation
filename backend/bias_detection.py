"""
Bias detection algorithms for identifying potential bias in evaluations.
For Eternity School Evaluation & Recognition System
"""

import logging
from collections import defaultdict
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from scipy import stats

from backend.database import Assignment, Cycle, Evaluation, Person


class BiasDetector:
    """Detects various types of bias in evaluation data"""

    def __init__(self, db_session):
        self.db = db_session
        self.logger = logging.getLogger(__name__)

    def detect_gender_bias(self, cycle_id: int) -> Dict:
        """
        Detect gender bias in evaluations.
        Compares average ratings by gender of rater and target.
        """
        # This would require gender data in Person model
        # For now, returns structure
        evaluations = (
            self.db.query(Evaluation)
            .join(Assignment)
            .filter(Assignment.cycle_id == cycle_id, Evaluation.status == "submitted")
            .all()
        )

        if len(evaluations) < 10:
            return {"status": "insufficient_data", "message": "Need at least 10 evaluations"}

        # Group by rater-target gender combinations
        ratings_by_group = defaultdict(list)

        for eval in evaluations:
            # Would need to join with Person to get gender
            # For now, placeholder structure
            ratings_by_group["all"].append(eval.rating)

        results = {
            "status": "analyzed",
            "total_evaluations": len(evaluations),
            "mean_rating": float(np.mean([e.rating for e in evaluations])),
            "std_rating": float(np.std([e.rating for e in evaluations])),
            "message": "Gender data not available in current schema",
        }

        return results

    def detect_role_bias(self, cycle_id: int) -> Dict:
        """
        Detect bias based on role hierarchy.
        Checks if ratings differ significantly by role relationships.
        """
        assignments = self.db.query(Assignment).filter(Assignment.cycle_id == cycle_id).all()

        evaluations = (
            self.db.query(Evaluation)
            .join(Assignment)
            .filter(Assignment.cycle_id == cycle_id, Evaluation.status == "submitted")
            .all()
        )

        if len(evaluations) < 10:
            return {"status": "insufficient_data"}

        # Group ratings by rater context (peer, manager, direct_report, etc.)
        ratings_by_context = defaultdict(list)

        for eval in evaluations:
            assignment = self.db.query(Assignment).filter(Assignment.id == eval.assignment_id).first()
            if assignment:
                ratings_by_context[assignment.rater_context].append(eval.rating)

        results = {"status": "analyzed", "contexts": {}}

        for context, ratings in ratings_by_context.items():
            if len(ratings) >= 3:
                results["contexts"][context] = {
                    "count": len(ratings),
                    "mean": float(np.mean(ratings)),
                    "std": float(np.std(ratings)),
                    "median": float(np.median(ratings)),
                }

        # Statistical test for differences
        if len(ratings_by_context) >= 2:
            context_groups = [ratings for ratings in ratings_by_context.values() if len(ratings) >= 3]
            if len(context_groups) >= 2:
                # Kruskal-Wallis test for multiple groups
                try:
                    h_stat, p_value = stats.kruskal(*context_groups)
                    results["statistical_test"] = {
                        "test": "kruskal_wallis",
                        "h_statistic": float(h_stat),
                        "p_value": float(p_value),
                        "significant": p_value < 0.05,
                    }
                except:
                    pass

        return results

    def detect_similarity_bias(self, cycle_id: int, variance_threshold: float = 0.5) -> Dict:
        """
        Detects if raters consistently give similar scores across all domains
        (halo effect) or if scores are too similar to other raters.

        Args:
            cycle_id: The evaluation cycle ID
            variance_threshold: Threshold for flagging low variance (default 0.5)

        Returns:
            Dictionary with bias flags for each rater showing halo effect
        """
        evaluations = (
            self.db.query(Evaluation)
            .join(Assignment)
            .filter(Assignment.cycle_id == cycle_id, Evaluation.status == "submitted", Evaluation.rating.isnot(None))
            .all()
        )

        if len(evaluations) < 5:
            return {"status": "insufficient_data", "message": "Need at least 5 evaluations"}

        # Convert to DataFrame for easier analysis
        eval_data = []
        for eval in evaluations:
            assignment = self.db.query(Assignment).filter(Assignment.id == eval.assignment_id).first()
            if assignment:
                eval_data.append(
                    {
                        "rater_id": assignment.rater_email,
                        "target_id": assignment.target_email,
                        "score": eval.rating,
                        "rater_context": assignment.rater_context,
                    }
                )

        if not eval_data:
            return {"status": "no_data"}

        df = pd.DataFrame(eval_data)
        bias_flags = []

        # Check each rater for low variance (halo effect)
        for rater_id in df["rater_id"].unique():
            rater_scores = df[df["rater_id"] == rater_id]["score"]

            if len(rater_scores) < 2:
                continue

            # Check for low variance (halo effect)
            score_variance = rater_scores.var()

            if score_variance < variance_threshold:
                severity = "high" if score_variance < 0.2 else "medium"
                bias_flags.append(
                    {
                        "rater_id": rater_id,
                        "bias_type": "halo_effect",
                        "variance": float(score_variance),
                        "mean_score": float(rater_scores.mean()),
                        "std_score": float(rater_scores.std()),
                        "count": len(rater_scores),
                        "severity": severity,
                        "message": f"Rater shows halo effect: very similar scores across all evaluations (variance: {score_variance:.3f})",
                    }
                )

        # Check for inter-rater similarity (raters giving similar scores to same targets)
        inter_rater_similarity = []
        for target_id in df["target_id"].unique():
            target_ratings = df[df["target_id"] == target_id]
            if len(target_ratings) >= 2:
                target_variance = target_ratings["score"].var()
                inter_rater_similarity.append(
                    {
                        "target_id": target_id,
                        "variance": float(target_variance),
                        "mean_score": float(target_ratings["score"].mean()),
                        "rater_count": len(target_ratings),
                    }
                )

        return {
            "status": "analyzed",
            "bias_flags": bias_flags,
            "total_raters_checked": len(df["rater_id"].unique()),
            "raters_with_bias": len(bias_flags),
            "inter_rater_similarity": inter_rater_similarity,
            "overall_variance": float(df["score"].var()),
        }

    def detect_recency_bias(self, cycle_id: int) -> Dict:
        """
        Detect recency bias - tendency to rate based on recent events.
        Analyzes if ratings correlate with submission timing.
        Enhanced version for Eternity School Evaluation System.
        """
        evaluations = (
            self.db.query(Evaluation)
            .join(Assignment)
            .filter(Assignment.cycle_id == cycle_id, Evaluation.status == "submitted", Evaluation.rating.isnot(None))
            .order_by(Evaluation.submitted_at)
            .all()
        )

        if len(evaluations) < 10:
            return {"status": "insufficient_data", "message": "Need at least 10 evaluations"}

        # Calculate days since cycle start
        cycle = self.db.query(Cycle).filter(Cycle.id == cycle_id).first()
        if not cycle or not cycle.start_date:
            return {"status": "no_cycle_dates", "message": "Cycle start date not available"}

        days_since_start = []
        ratings = []
        rater_ids = []

        for eval in evaluations:
            assignment = self.db.query(Assignment).filter(Assignment.id == eval.assignment_id).first()
            if assignment and eval.submitted_at:
                days = (
                    (eval.submitted_at.date() - cycle.start_date).days
                    if hasattr(eval.submitted_at, "date")
                    else (eval.submitted_at - cycle.start_date).days
                )
                days_since_start.append(days)
                ratings.append(eval.rating)
                rater_ids.append(assignment.rater_email)

        if len(days_since_start) < 10:
            return {"status": "insufficient_data"}

        # Correlation analysis
        correlation = np.corrcoef(days_since_start, ratings)[0, 1] if len(days_since_start) > 1 else 0

        # Additional analysis: compare early vs late submissions
        median_days = np.median(days_since_start)
        early_ratings = [r for d, r in zip(days_since_start, ratings) if d <= median_days]
        late_ratings = [r for d, r in zip(days_since_start, ratings) if d > median_days]

        early_mean = np.mean(early_ratings) if early_ratings else 0
        late_mean = np.mean(late_ratings) if late_ratings else 0
        mean_difference = late_mean - early_mean

        return {
            "status": "analyzed",
            "correlation": float(correlation),
            "interpretation": "positive" if correlation > 0.3 else "negative" if correlation < -0.3 else "none",
            "early_submissions_mean": float(early_mean),
            "late_submissions_mean": float(late_mean),
            "mean_difference": float(mean_difference),
            "median_days": float(median_days),
            "total_evaluations": len(evaluations),
            "message": (
                "Positive correlation suggests later submissions rate higher (recency bias)"
                if correlation > 0.3
                else (
                    "Negative correlation suggests later submissions rate lower"
                    if correlation < -0.3
                    else "No significant recency bias detected"
                )
            ),
        }

    def detect_centrality_bias(self, cycle_id: int) -> Dict:
        """
        Detect centrality bias - tendency to avoid extreme ratings.
        Checks distribution of ratings for clustering around middle values.
        """
        evaluations = (
            self.db.query(Evaluation)
            .join(Assignment)
            .filter(Assignment.cycle_id == cycle_id, Evaluation.status == "submitted")
            .all()
        )

        if len(evaluations) < 10:
            return {"status": "insufficient_data"}

        ratings = [e.rating for e in evaluations]

        # Check distribution
        rating_counts = defaultdict(int)
        for r in ratings:
            rating_counts[int(r)] += 1

        # Calculate how clustered ratings are
        mean_rating = np.mean(ratings)
        std_rating = np.std(ratings)

        # Expected std for uniform distribution (1-5 scale)
        expected_std = np.sqrt((5 - 1) ** 2 / 12)  # ~1.29 for uniform

        results = {
            "status": "analyzed",
            "mean_rating": float(mean_rating),
            "std_rating": float(std_rating),
            "expected_std_uniform": float(expected_std),
            "centrality_index": float(std_rating / expected_std),
            "distribution": dict(rating_counts),
            "interpretation": (
                "low" if std_rating < 0.5 * expected_std else "moderate" if std_rating < 0.8 * expected_std else "normal"
            ),
        }

        return results

    def detect_harshness_bias(self, cycle_id: int) -> Dict:
        """
        Detect individual rater harshness/leniency bias.
        Identifies raters who consistently rate higher or lower than average.
        """
        evaluations = (
            self.db.query(Evaluation)
            .join(Assignment)
            .filter(Assignment.cycle_id == cycle_id, Evaluation.status == "submitted")
            .all()
        )

        if len(evaluations) < 10:
            return {"status": "insufficient_data"}

        # Group by rater
        ratings_by_rater = defaultdict(list)
        target_means = defaultdict(list)  # Average rating each target receives

        for eval in evaluations:
            assignment = self.db.query(Assignment).filter(Assignment.id == eval.assignment_id).first()
            if assignment:
                ratings_by_rater[assignment.rater_email].append(eval.rating)
                target_means[assignment.target_email].append(eval.rating)

        # Calculate target averages
        target_avg = {target: np.mean(ratings) for target, ratings in target_means.items()}

        # Calculate rater bias (their average vs what targets typically get)
        rater_bias = {}
        for rater_email, ratings in ratings_by_rater.items():
            if len(ratings) >= 3:  # Need multiple ratings
                rater_mean = np.mean(ratings)
                # Compare against average of targets they rated
                rated_targets = [
                    assignment.target_email
                    for eval in evaluations
                    for assignment in [self.db.query(Assignment).filter(Assignment.id == eval.assignment_id).first()]
                    if assignment and assignment.rater_email == rater_email
                ]
                target_avgs = [target_avg.get(t, rater_mean) for t in rated_targets]
                expected_mean = np.mean(target_avgs) if target_avgs else rater_mean

                bias = rater_mean - expected_mean
                rater_bias[rater_email] = {
                    "mean_rating": float(rater_mean),
                    "expected_mean": float(expected_mean),
                    "bias": float(bias),
                    "count": len(ratings),
                    "interpretation": "harsh" if bias < -0.5 else "lenient" if bias > 0.5 else "neutral",
                }

        return {
            "status": "analyzed",
            "rater_bias": rater_bias,
            "overall_mean": float(np.mean([e.rating for e in evaluations])),
        }

    def calculate_weighted_score(self, scores: Dict, weights: Dict) -> float:
        """
        Calculate weighted average score efficiently using vectorized operations.

        Args:
            scores: Dictionary mapping domain/context to score
                   (e.g., {'peer_review': 4.5, 'manager_review': 3.8})
            weights: Dictionary mapping domain/context to weight
                    (e.g., {'peer_review': 0.3, 'manager_review': 0.7})

        Returns:
            Weighted average score (0.0 if no valid scores)
        """
        if not scores:
            return 0.0

        # Use numpy for efficient vectorized calculation
        score_values = []
        weight_values = []

        for domain, score in scores.items():
            weight = weights.get(domain, 1.0)

            # Log warning only if weight was expected but missing
            if domain not in weights and len(weights) > 0:
                self.logger.warning(f"Weight not found for domain '{domain}', using default weight of 1.0")

            score_values.append(score)
            weight_values.append(weight)

        # Convert to numpy arrays for efficient computation
        scores_array = np.array(score_values)
        weights_array = np.array(weight_values)

        # Calculate weighted average: sum(scores * weights) / sum(weights)
        total_weight = weights_array.sum()
        if total_weight == 0:
            self.logger.warning("Total weight is 0, returning 0")
            return 0.0

        weighted_sum = (scores_array * weights_array).sum()
        return float(weighted_sum / total_weight)

    def calculate_weighted_score_by_assignment(self, cycle_id: int, target_email: str) -> Dict:
        """
        Calculate weighted score for a specific target based on all their evaluations.
        Optimized to use a single join query instead of N+1 queries.

        Args:
            cycle_id: The evaluation cycle ID
            target_email: Email of the person being evaluated

        Returns:
            Dictionary with weighted score and breakdown
        """
        # Single query with join to avoid N+1 problem
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
            return {
                "status": "no_evaluations",
                "weighted_score": None,
                "message": f"No submitted evaluations found for {target_email}",
            }

        # Build scores and weights dictionaries efficiently
        scores = {}
        weights = {}

        for eval_obj, assignment in evaluations:
            context = assignment.rater_context or "default"
            scores[context] = eval_obj.rating
            weights[context] = assignment.weight if assignment.weight else 1.0

        weighted_score = self.calculate_weighted_score(scores, weights)

        return {
            "status": "calculated",
            "target_email": target_email,
            "weighted_score": float(weighted_score),
            "scores_by_context": scores,
            "weights_by_context": weights,
            "evaluation_count": len(scores),
        }

    def comprehensive_bias_report(self, cycle_id: int) -> Dict:
        """Generate a comprehensive bias analysis report"""
        return {
            "cycle_id": cycle_id,
            "role_bias": self.detect_role_bias(cycle_id),
            "recency_bias": self.detect_recency_bias(cycle_id),
            "centrality_bias": self.detect_centrality_bias(cycle_id),
            "harshness_bias": self.detect_harshness_bias(cycle_id),
            "similarity_bias": self.detect_similarity_bias(cycle_id),
            "gender_bias": self.detect_gender_bias(cycle_id),
        }

    def load_evaluations_as_dataframe(self, cycle_id: int) -> pd.DataFrame:
        """
        Load evaluations from database and convert to pandas DataFrame.
        Useful for the detect_evaluation_bias method.

        Args:
            cycle_id: The evaluation cycle ID

        Returns:
            DataFrame with evaluation data
        """
        evaluations = (
            self.db.query(Evaluation, Assignment, Person)
            .join(Assignment, Evaluation.assignment_id == Assignment.id)
            .outerjoin(Person, Assignment.target_email == Person.email)
            .filter(Assignment.cycle_id == cycle_id, Evaluation.status == "submitted", Evaluation.rating.isnot(None))
            .all()
        )

        eval_data = []
        for eval_obj, assignment, person in evaluations:
            eval_data.append(
                {
                    "rater_id": assignment.rater_email,
                    "target_id": assignment.target_email,
                    "score": eval_obj.rating,
                    "rater_context": assignment.rater_context or "unknown",
                    "target_group": assignment.target_group or "unknown",
                    "department": person.segment.value if person and person.segment else "unknown",
                    "segment": person.segment.value if person and person.segment else "unknown",
                    "submitted_at": eval_obj.submitted_at,
                    "evaluation_id": eval_obj.id,
                }
            )

        return pd.DataFrame(eval_data)

    def detect_evaluation_bias(self, evaluations: pd.DataFrame) -> Dict:
        """
        Comprehensive bias detection for Eternity School evaluations.
        Works with a pandas DataFrame containing evaluation data.

        Args:
            evaluations: DataFrame with columns:
                - rater_id (or rater_email): Email/ID of the rater
                - target_id (or target_email): Email/ID of the target
                - score (or rating): Evaluation score/rating
                - rater_context: Context of the rater (CEO, P&C, QA, peer_review, etc.)
                - target_group: Group of the target (academic, admin, peers, etc.)
                - department (or segment): Department/segment (National, International, Whole School)
                - submitted_at (optional): Timestamp for recency analysis

        Returns:
            Dictionary containing comprehensive bias analysis
        """
        if evaluations.empty:
            return {"status": "no_data", "message": "No evaluation data provided"}

        # Normalize column names
        df = evaluations.copy()
        column_mapping = {"rater_email": "rater_id", "target_email": "target_id", "rating": "score"}
        for old_col, new_col in column_mapping.items():
            if old_col in df.columns and new_col not in df.columns:
                df[new_col] = df[old_col]

        # Validate required columns
        required_cols = ["rater_id", "target_id", "score"]
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            return {
                "status": "invalid_data",
                "message": f"Missing required columns: {missing_cols}",
                "required_columns": required_cols,
            }

        bias_report = {
            "status": "analyzed",
            "total_evaluations": len(df),
            "similarity_bias": self._detect_similarity_bias_from_df(df),
            "recency_bias": (
                self._detect_recency_bias_from_df(df)
                if "submitted_at" in df.columns
                else {"status": "no_timestamp_data", "message": "submitted_at column not available for recency analysis"}
            ),
            "department_bias": self._detect_department_bias_from_df(df),
            "rater_reliability": self._calculate_rater_reliability_from_df(df),
        }

        return bias_report

    def _detect_similarity_bias_from_df(self, df: pd.DataFrame) -> Dict:
        """
        Detect similarity bias from DataFrame.
        Analyzes halo effect and inter-rater similarity.
        """
        if df.empty or "score" not in df.columns:
            return {"status": "insufficient_data"}

        bias_flags = []
        variance_threshold = 0.5

        # Check each rater for low variance (halo effect)
        if "rater_id" in df.columns:
            for rater_id in df["rater_id"].unique():
                rater_scores = df[df["rater_id"] == rater_id]["score"]

                if len(rater_scores) < 2:
                    continue

                score_variance = rater_scores.var()

                if pd.notna(score_variance) and score_variance < variance_threshold:
                    severity = "high" if score_variance < 0.2 else "medium"
                    bias_flags.append(
                        {
                            "rater_id": rater_id,
                            "bias_type": "halo_effect",
                            "variance": float(score_variance),
                            "mean_score": float(rater_scores.mean()),
                            "std_score": float(rater_scores.std()),
                            "count": len(rater_scores),
                            "severity": severity,
                        }
                    )

        # Check for inter-rater similarity
        inter_rater_similarity = []
        if "target_id" in df.columns:
            for target_id in df["target_id"].unique():
                target_ratings = df[df["target_id"] == target_id]
                if len(target_ratings) >= 2:
                    target_variance = target_ratings["score"].var()
                    if pd.notna(target_variance):
                        inter_rater_similarity.append(
                            {
                                "target_id": target_id,
                                "variance": float(target_variance),
                                "mean_score": float(target_ratings["score"].mean()),
                                "rater_count": len(target_ratings),
                            }
                        )

        return {
            "status": "analyzed",
            "bias_flags": bias_flags,
            "total_raters_checked": len(df["rater_id"].unique()) if "rater_id" in df.columns else 0,
            "raters_with_bias": len(bias_flags),
            "inter_rater_similarity": inter_rater_similarity,
            "overall_variance": float(df["score"].var()) if pd.notna(df["score"].var()) else 0.0,
        }

    def _detect_recency_bias_from_df(self, df: pd.DataFrame) -> Dict:
        """
        Detect recency bias from DataFrame.
        Analyzes correlation between submission timing and ratings.
        """
        if df.empty or "submitted_at" not in df.columns or "score" not in df.columns:
            return {"status": "insufficient_data"}

        # Convert submitted_at to numeric (days since earliest)
        df_clean = df[df["submitted_at"].notna() & df["score"].notna()].copy()

        if len(df_clean) < 10:
            return {"status": "insufficient_data", "message": "Need at least 10 evaluations with timestamps"}

        # Convert timestamps to days (relative to earliest)
        df_clean["submitted_at"] = pd.to_datetime(df_clean["submitted_at"])
        earliest = df_clean["submitted_at"].min()
        df_clean["days_since_start"] = (df_clean["submitted_at"] - earliest).dt.days

        # Calculate correlation
        correlation = df_clean["days_since_start"].corr(df_clean["score"])

        if pd.isna(correlation):
            return {"status": "calculation_error"}

        # Compare early vs late submissions
        median_days = df_clean["days_since_start"].median()
        early_ratings = df_clean[df_clean["days_since_start"] <= median_days]["score"]
        late_ratings = df_clean[df_clean["days_since_start"] > median_days]["score"]

        early_mean = float(early_ratings.mean()) if len(early_ratings) > 0 else 0.0
        late_mean = float(late_ratings.mean()) if len(late_ratings) > 0 else 0.0
        mean_difference = late_mean - early_mean

        return {
            "status": "analyzed",
            "correlation": float(correlation),
            "interpretation": "positive" if correlation > 0.3 else "negative" if correlation < -0.3 else "none",
            "early_submissions_mean": early_mean,
            "late_submissions_mean": late_mean,
            "mean_difference": mean_difference,
            "median_days": float(median_days),
            "total_evaluations": len(df_clean),
            "message": (
                "Positive correlation suggests later submissions rate higher (recency bias)"
                if correlation > 0.3
                else (
                    "Negative correlation suggests later submissions rate lower"
                    if correlation < -0.3
                    else "No significant recency bias detected"
                )
            ),
        }

    def _detect_department_bias_from_df(self, df: pd.DataFrame) -> Dict:
        """
        Detect bias based on department/segment (National, International, Whole School).
        Analyzes if ratings differ significantly across departments.
        """
        if df.empty or "score" not in df.columns:
            return {"status": "insufficient_data"}

        # Check for department/segment column
        dept_col = None
        for col in ["department", "segment", "target_segment", "dept"]:
            if col in df.columns:
                dept_col = col
                break

        if dept_col is None:
            return {"status": "no_department_data", "message": "No department/segment column found in data"}

        df_clean = df[df[dept_col].notna() & df["score"].notna()].copy()

        if len(df_clean) < 10:
            return {"status": "insufficient_data", "message": "Need at least 10 evaluations with department data"}

        # Group by department
        dept_stats = {}
        dept_ratings = {}

        for dept in df_clean[dept_col].unique():
            dept_data = df_clean[df_clean[dept_col] == dept]["score"]
            if len(dept_data) >= 3:
                dept_ratings[dept] = dept_data.tolist()
                dept_stats[dept] = {
                    "count": len(dept_data),
                    "mean": float(dept_data.mean()),
                    "std": float(dept_data.std()),
                    "median": float(dept_data.median()),
                    "min": float(dept_data.min()),
                    "max": float(dept_data.max()),
                }

        if len(dept_stats) == 0:
            return {"status": "insufficient_data", "message": "No departments with sufficient data"}

        # Statistical test for differences between departments
        statistical_test = None
        if len(dept_ratings) >= 2:
            dept_groups = [ratings for ratings in dept_ratings.values() if len(ratings) >= 3]
            if len(dept_groups) >= 2:
                try:
                    h_stat, p_value = stats.kruskal(*dept_groups)
                    statistical_test = {
                        "test": "kruskal_wallis",
                        "h_statistic": float(h_stat),
                        "p_value": float(p_value),
                        "significant": p_value < 0.05,
                        "interpretation": (
                            "Significant difference between departments"
                            if p_value < 0.05
                            else "No significant difference between departments"
                        ),
                    }
                except Exception as e:
                    self.logger.warning(f"Statistical test failed: {e}")

        # Calculate overall statistics
        overall_mean = float(df_clean["score"].mean())
        overall_std = float(df_clean["score"].std())

        # Identify departments with significant deviations
        deviations = {}
        for dept, stats_data in dept_stats.items():
            mean_diff = stats_data["mean"] - overall_mean
            std_diff = abs(stats_data["std"] - overall_std)

            # Flag if mean is more than 0.5 points different or std is significantly different
            if abs(mean_diff) > 0.5 or std_diff > 0.3:
                deviations[dept] = {
                    "mean_difference": float(mean_diff),
                    "std_difference": float(std_diff),
                    "severity": "high" if abs(mean_diff) > 1.0 else "medium",
                }

        return {
            "status": "analyzed",
            "departments": dept_stats,
            "overall_mean": overall_mean,
            "overall_std": overall_std,
            "statistical_test": statistical_test,
            "significant_deviations": deviations,
            "total_departments": len(dept_stats),
            "message": f"Analyzed {len(dept_stats)} departments. "
            + (
                f"Found {len(deviations)} departments with significant deviations."
                if deviations
                else "No significant deviations detected."
            ),
        }

    def _calculate_rater_reliability_from_df(self, df: pd.DataFrame) -> Dict:
        """
        Calculate inter-rater reliability metrics.
        Measures agreement between multiple raters for the same targets.
        """
        if df.empty or "score" not in df.columns:
            return {"status": "insufficient_data"}

        if "target_id" not in df.columns or "rater_id" not in df.columns:
            return {"status": "invalid_data", "message": "target_id and rater_id columns required for reliability analysis"}

        df_clean = df[df["score"].notna()].copy()

        if len(df_clean) < 5:
            return {"status": "insufficient_data", "message": "Need at least 5 evaluations"}

        # Group by target to calculate inter-rater reliability
        target_reliability = []
        all_ratings = []

        for target_id in df_clean["target_id"].unique():
            target_data = df_clean[df_clean["target_id"] == target_id]

            if len(target_data) >= 2:  # Need at least 2 raters
                scores = target_data["score"].tolist()
                all_ratings.extend(scores)

                # Calculate coefficient of variation (CV) - lower is better
                mean_score = target_data["score"].mean()
                std_score = target_data["score"].std()
                cv = (std_score / mean_score) if mean_score != 0 else float("inf")

                # Calculate range
                score_range = target_data["score"].max() - target_data["score"].min()

                target_reliability.append(
                    {
                        "target_id": target_id,
                        "rater_count": len(target_data),
                        "mean_score": float(mean_score),
                        "std_score": float(std_score),
                        "coefficient_of_variation": float(cv) if pd.notna(cv) and cv != float("inf") else None,
                        "score_range": float(score_range),
                        "min_score": float(target_data["score"].min()),
                        "max_score": float(target_data["score"].max()),
                        "reliability_rating": "high" if cv < 0.1 else "medium" if cv < 0.2 else "low",
                    }
                )

        if not target_reliability:
            return {"status": "insufficient_data", "message": "No targets with multiple raters"}

        # Calculate overall reliability metrics
        cvs = [t["coefficient_of_variation"] for t in target_reliability if t["coefficient_of_variation"] is not None]
        avg_cv = float(np.mean(cvs)) if cvs else None

        # Calculate intraclass correlation coefficient (ICC) approximation
        # Using variance components
        overall_mean = float(np.mean(all_ratings))
        between_target_variance = 0.0
        within_target_variance = 0.0

        for target_data in target_reliability:
            target_mean = target_data["mean_score"]
            target_std = target_data["std_score"]
            n_raters = target_data["rater_count"]

            between_target_variance += (target_mean - overall_mean) ** 2
            within_target_variance += target_std**2

        n_targets = len(target_reliability)
        if n_targets > 0:
            between_target_variance /= n_targets
            within_target_variance /= n_targets

        # Approximate ICC
        total_variance = between_target_variance + within_target_variance
        icc_approx = (between_target_variance / total_variance) if total_variance > 0 else 0.0

        # Count reliability ratings
        reliability_distribution = {
            "high": sum(1 for t in target_reliability if t["reliability_rating"] == "high"),
            "medium": sum(1 for t in target_reliability if t["reliability_rating"] == "medium"),
            "low": sum(1 for t in target_reliability if t["reliability_rating"] == "low"),
        }

        return {
            "status": "analyzed",
            "target_reliability": target_reliability,
            "overall_metrics": {
                "average_coefficient_of_variation": avg_cv,
                "approximate_icc": float(icc_approx),
                "between_target_variance": float(between_target_variance),
                "within_target_variance": float(within_target_variance),
                "overall_mean": overall_mean,
            },
            "reliability_distribution": reliability_distribution,
            "total_targets_analyzed": len(target_reliability),
            "interpretation": (
                "High reliability"
                if avg_cv and avg_cv < 0.15
                else (
                    "Moderate reliability"
                    if avg_cv and avg_cv < 0.25
                    else "Low reliability - significant disagreement between raters"
                )
            ),
        }
