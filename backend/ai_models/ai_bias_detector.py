"""
AI-Powered Bias Detector for Individual Evaluations
Uses machine learning and statistical analysis to detect bias in real-time during evaluation submission.
"""

import logging
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from backend.bias_detection import BiasDetector
from backend.database import Assignment, Cycle, Evaluation, Person
from backend.realtime_bias_detector import RealTimeBiasDetector


class AIBiasDetector:
    """
    AI-powered bias detector for analyzing individual evaluations.

    Uses advanced algorithms to detect:
    - Similarity bias (halo effect)
    - Harshness/leniency bias
    - Centrality bias
    - Context-based bias
    - Temporal bias

    Provides confidence scores and specific mitigation suggestions.
    """

    def __init__(self, db_session):
        self.db = db_session
        self.logger = logging.getLogger(__name__)
        self.bias_detector = BiasDetector(db_session)
        self.realtime_detector = RealTimeBiasDetector(db_session)

    def analyze_evaluation(self, evaluation: Evaluation) -> Dict:
        """
        Analyze a single evaluation for bias using AI-powered algorithms.

        Args:
            evaluation: Evaluation object to analyze

        Returns:
            Dictionary containing:
            - bias_indicators: Similarity bias score and confidence
            - bias_flags: List of detected bias types
            - mitigation_suggestions: Specific recommendations
        """
        if not evaluation:
            return {"status": "error", "message": "Evaluation object required"}

        # Get assignment details
        assignment = self.db.query(Assignment).filter(Assignment.id == evaluation.assignment_id).first()

        if not assignment:
            return {"status": "error", "message": "Assignment not found"}

        # Get context for analysis
        cycle_id = assignment.cycle_id
        rater_email = assignment.rater_email
        target_email = assignment.target_email

        # Get all evaluations by this rater in this cycle
        rater_evaluations = self._get_rater_evaluations(rater_email, cycle_id)

        # Get all evaluations for this target in this cycle
        target_evaluations = self._get_target_evaluations(target_email, cycle_id)

        # Analyze different bias types
        similarity_analysis = self._analyze_similarity_bias(evaluation, assignment, rater_evaluations)

        harshness_analysis = self._analyze_harshness_bias(evaluation, assignment, target_evaluations)

        centrality_analysis = self._analyze_centrality_bias(evaluation, assignment, rater_evaluations)

        context_analysis = self._analyze_context_bias(evaluation, assignment, target_evaluations)

        # Aggregate results
        bias_flags = []
        bias_scores = []
        confidence_scores = []

        # Similarity bias (halo effect)
        if similarity_analysis["detected"]:
            bias_flags.append("halo_effect_detected")
            bias_scores.append(similarity_analysis["score"])
            confidence_scores.append(similarity_analysis["confidence"])

        # Harshness bias
        if harshness_analysis["detected"]:
            if harshness_analysis["type"] == "harsh":
                bias_flags.append("harshness_bias_detected")
            else:
                bias_flags.append("leniency_bias_detected")
            bias_scores.append(harshness_analysis["score"])
            confidence_scores.append(harshness_analysis["confidence"])

        # Centrality bias
        if centrality_analysis["detected"]:
            bias_flags.append("centrality_bias_detected")
            bias_scores.append(centrality_analysis["score"])
            confidence_scores.append(centrality_analysis["confidence"])

        # Context bias
        if context_analysis["detected"]:
            bias_flags.append("context_bias_detected")
            bias_scores.append(context_analysis["score"])
            confidence_scores.append(context_analysis["confidence"])

        # Calculate overall similarity bias score (primary metric)
        similarity_bias_score = similarity_analysis.get("score", 0.0)
        overall_confidence = np.mean(confidence_scores) if confidence_scores else 0.5

        # Generate mitigation suggestions
        mitigation_suggestions = self._generate_mitigation_suggestions(
            similarity_analysis, harshness_analysis, centrality_analysis, context_analysis, bias_flags
        )

        return {
            "status": "analyzed",
            "bias_indicators": {
                "similarity_bias_score": float(similarity_bias_score),
                "confidence": float(overall_confidence),
                "overall_bias_score": float(np.mean(bias_scores)) if bias_scores else 0.0,
            },
            "bias_flags": bias_flags,
            "mitigation_suggestions": mitigation_suggestions,
            "detailed_analysis": {
                "similarity": similarity_analysis,
                "harshness": harshness_analysis,
                "centrality": centrality_analysis,
                "context": context_analysis,
            },
            "timestamp": datetime.utcnow().isoformat(),
        }

    def _get_rater_evaluations(self, rater_email: str, cycle_id: int) -> List[Evaluation]:
        """Get all evaluations by a rater in a cycle"""
        return (
            self.db.query(Evaluation)
            .join(Assignment)
            .filter(
                Assignment.rater_email == rater_email,
                Assignment.cycle_id == cycle_id,
                Evaluation.status == "submitted",
                Evaluation.rating.isnot(None),
            )
            .all()
        )

    def _get_target_evaluations(self, target_email: str, cycle_id: int) -> List[Evaluation]:
        """Get all evaluations for a target in a cycle"""
        return (
            self.db.query(Evaluation)
            .join(Assignment)
            .filter(
                Assignment.target_email == target_email,
                Assignment.cycle_id == cycle_id,
                Evaluation.status == "submitted",
                Evaluation.rating.isnot(None),
            )
            .all()
        )

    def _analyze_similarity_bias(
        self, evaluation: Evaluation, assignment: Assignment, rater_evaluations: List[Evaluation]
    ) -> Dict:
        """
        Analyze similarity bias (halo effect).
        Detects if rater gives similar scores across all evaluations.
        """
        if len(rater_evaluations) < 2:
            return {"detected": False, "score": 0.0, "confidence": 0.0, "reason": "insufficient_data"}

        # Get all ratings by this rater
        ratings = [e.rating for e in rater_evaluations]

        # Calculate variance
        variance = np.var(ratings)
        std = np.std(ratings)
        mean_rating = np.mean(ratings)

        # Low variance indicates halo effect
        # For a 1-5 scale, variance < 0.5 is suspicious
        # For a 1-10 scale, variance < 1.0 is suspicious
        scale_max = 5.0  # Assuming 1-5 scale, adjust if needed
        variance_threshold = (scale_max - 1.0) ** 2 / 12 * 0.3  # 30% of expected variance

        detected = variance < variance_threshold

        # Calculate bias score (0-1, higher = more bias)
        if detected:
            # Normalize: lower variance = higher bias score
            bias_score = 1.0 - (variance / variance_threshold)
            bias_score = max(0.0, min(1.0, bias_score))

            # Confidence based on number of evaluations and variance
            n_evaluations = len(ratings)
            confidence = min(0.95, 0.5 + (n_evaluations / 10) * 0.3 + (1 - variance / variance_threshold) * 0.15)
        else:
            bias_score = 0.0
            confidence = 0.7  # High confidence in no bias

        return {
            "detected": detected,
            "score": float(bias_score),
            "confidence": float(confidence),
            "variance": float(variance),
            "std": float(std),
            "mean_rating": float(mean_rating),
            "evaluation_count": len(ratings),
            "reason": "low_variance" if detected else "normal_variance",
        }

    def _analyze_harshness_bias(
        self, evaluation: Evaluation, assignment: Assignment, target_evaluations: List[Evaluation]
    ) -> Dict:
        """
        Analyze harshness/leniency bias.
        Compares this rater's rating to other raters' ratings for the same target.
        """
        if len(target_evaluations) < 2:
            return {"detected": False, "score": 0.0, "confidence": 0.0, "type": None, "reason": "insufficient_data"}

        # Get all ratings for this target
        all_ratings = [e.rating for e in target_evaluations]
        current_rating = evaluation.rating

        # Calculate statistics
        mean_rating = np.mean(all_ratings)
        std_rating = np.std(all_ratings)

        # Compare current rating to mean
        deviation = current_rating - mean_rating

        # Threshold: more than 1 standard deviation is significant
        threshold = std_rating if std_rating > 0 else 0.5

        detected = abs(deviation) > threshold

        if detected:
            bias_type = "harsh" if deviation < -threshold else "lenient"
            # Bias score: normalized deviation
            bias_score = min(1.0, abs(deviation) / (threshold * 2))

            # Confidence based on number of comparisons and deviation magnitude
            n_comparisons = len(target_evaluations) - 1
            confidence = min(0.95, 0.6 + (n_comparisons / 5) * 0.2 + (abs(deviation) / threshold - 1) * 0.15)
        else:
            bias_type = None
            bias_score = 0.0
            confidence = 0.7

        return {
            "detected": detected,
            "score": float(bias_score),
            "confidence": float(confidence),
            "type": bias_type,
            "deviation": float(deviation),
            "mean_rating": float(mean_rating),
            "current_rating": float(current_rating),
            "comparison_count": len(target_evaluations) - 1,
            "reason": f"{bias_type}_bias" if detected else "normal_rating",
        }

    def _analyze_centrality_bias(
        self, evaluation: Evaluation, assignment: Assignment, rater_evaluations: List[Evaluation]
    ) -> Dict:
        """
        Analyze centrality bias (avoiding extreme ratings).
        Detects if rater consistently avoids high/low scores.
        """
        if len(rater_evaluations) < 3:
            return {"detected": False, "score": 0.0, "confidence": 0.0, "reason": "insufficient_data"}

        ratings = [e.rating for e in rater_evaluations]
        current_rating = evaluation.rating

        # Check distribution
        min_rating = min(ratings)
        max_rating = max(ratings)
        rating_range = max_rating - min_rating

        # Expected range for 1-5 scale is 4, for 1-10 is 9
        scale_max = 5.0
        expected_range = scale_max - 1.0

        # If range is less than 50% of expected, likely centrality bias
        range_ratio = rating_range / expected_range if expected_range > 0 else 0

        detected = range_ratio < 0.5

        if detected:
            # Bias score based on how compressed the range is
            bias_score = 1.0 - range_ratio
            confidence = min(0.9, 0.5 + (len(ratings) / 10) * 0.3 + (1 - range_ratio) * 0.1)
        else:
            bias_score = 0.0
            confidence = 0.7

        return {
            "detected": detected,
            "score": float(bias_score),
            "confidence": float(confidence),
            "rating_range": float(rating_range),
            "expected_range": float(expected_range),
            "range_ratio": float(range_ratio),
            "min_rating": float(min_rating),
            "max_rating": float(max_rating),
            "reason": "compressed_range" if detected else "normal_range",
        }

    def _analyze_context_bias(
        self, evaluation: Evaluation, assignment: Assignment, target_evaluations: List[Evaluation]
    ) -> Dict:
        """
        Analyze context-based bias.
        Compares rating to other ratings from same rater context.
        """
        if len(target_evaluations) < 2:
            return {"detected": False, "score": 0.0, "confidence": 0.0, "reason": "insufficient_data"}

        current_context = assignment.rater_context
        current_rating = evaluation.rating

        # Group ratings by context
        context_ratings = defaultdict(list)
        for eval_obj in target_evaluations:
            eval_assignment = self.db.query(Assignment).filter(Assignment.id == eval_obj.assignment_id).first()
            if eval_assignment:
                context_ratings[eval_assignment.rater_context].append(eval_obj.rating)

        if len(context_ratings) < 2:
            return {"detected": False, "score": 0.0, "confidence": 0.0, "reason": "single_context"}

        # Compare current context to others
        current_context_ratings = context_ratings.get(current_context, [])
        other_context_ratings = []
        for ctx, ratings in context_ratings.items():
            if ctx != current_context:
                other_context_ratings.extend(ratings)

        if not other_context_ratings:
            return {"detected": False, "score": 0.0, "confidence": 0.0, "reason": "no_other_contexts"}

        current_mean = np.mean(current_context_ratings) if current_context_ratings else current_rating
        other_mean = np.mean(other_context_ratings)

        deviation = current_mean - other_mean
        threshold = 0.5  # Significant difference threshold

        detected = abs(deviation) > threshold

        if detected:
            bias_score = min(1.0, abs(deviation) / (threshold * 2))
            confidence = min(0.9, 0.6 + (len(other_context_ratings) / 5) * 0.2)
        else:
            bias_score = 0.0
            confidence = 0.7

        return {
            "detected": detected,
            "score": float(bias_score),
            "confidence": float(confidence),
            "context": current_context,
            "context_mean": float(current_mean),
            "other_contexts_mean": float(other_mean),
            "deviation": float(deviation),
            "reason": "context_difference" if detected else "normal_context_rating",
        }

    def _generate_mitigation_suggestions(
        self,
        similarity_analysis: Dict,
        harshness_analysis: Dict,
        centrality_analysis: Dict,
        context_analysis: Dict,
        bias_flags: List[str],
    ) -> List[str]:
        """Generate specific mitigation suggestions based on detected biases"""
        suggestions = []

        # Similarity bias (halo effect)
        if similarity_analysis.get("detected"):
            suggestions.append(
                "Consider reviewing domain scores for consistency. "
                "The evaluation shows very similar scores across different aspects, "
                "which may indicate a halo effect. Please ensure each domain is "
                "evaluated independently based on specific evidence."
            )

        # Harshness bias
        if harshness_analysis.get("detected"):
            if harshness_analysis.get("type") == "harsh":
                suggestions.append(
                    f"This rating ({harshness_analysis.get('current_rating', 'N/A')}) is significantly "
                    f"lower than the average rating ({harshness_analysis.get('mean_rating', 'N/A'):.1f}) "
                    f"from other evaluators. Please review the evaluation criteria and ensure "
                    f"the rating accurately reflects the target's performance."
                )
            else:
                suggestions.append(
                    f"This rating ({harshness_analysis.get('current_rating', 'N/A')}) is significantly "
                    f"higher than the average rating ({harshness_analysis.get('mean_rating', 'N/A'):.1f}) "
                    f"from other evaluators. Please ensure the rating is based on objective "
                    f"performance evidence and not influenced by personal relationships."
                )

        # Centrality bias
        if centrality_analysis.get("detected"):
            suggestions.append(
                "The evaluation pattern shows a tendency to avoid extreme ratings. "
                "Please use the full rating scale appropriately - if performance truly "
                "deserves a high or low rating, it should be reflected accurately."
            )

        # Context bias
        if context_analysis.get("detected"):
            suggestions.append(
                f"Ratings from {context_analysis.get('context', 'this context')} context "
                f"differ significantly from other evaluation contexts. Please ensure "
                f"evaluations are objective and not influenced by role relationships."
            )

        # General suggestions if multiple biases detected
        if len(bias_flags) > 1:
            suggestions.append(
                "Multiple bias indicators detected. Consider participating in rater "
                "calibration training to improve evaluation consistency and objectivity."
            )

        # Default if no specific biases
        if not suggestions:
            suggestions.append(
                "No significant bias patterns detected. Continue evaluating based on "
                "objective performance evidence and established criteria."
            )

        return suggestions
