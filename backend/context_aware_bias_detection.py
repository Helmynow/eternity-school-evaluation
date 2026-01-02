"""
Context-Aware Bias Detection for 360-Degree Feedback
Comprehensive bias detection system that analyzes multiple rater contexts.
"""

import logging
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple

import numpy as np
import pandas as pd
try:
    from scipy import stats
except Exception:  # pragma: no cover
    stats = None

from backend.bias_detection import BiasDetector
from backend.bias_detection_360 import BiasFinding, BiasReport
from backend.database import Assignment, Cycle, Evaluation, Person


@dataclass
class ContextBiasFinding:
    """Bias finding specific to a rater context"""

    context: str
    bias_type: str
    severity: str
    score: float
    description: str
    affected_raters: List[str]
    affected_targets: List[str]
    evidence: Dict
    recommendations: List[str]
    comparison_with_other_contexts: Optional[Dict] = None


@dataclass
class CrossContextAnalysis:
    """Analysis comparing ratings across different contexts"""

    context_pair: Tuple[str, str]
    mean_difference: float
    statistical_significance: bool
    p_value: float
    effect_size: float
    interpretation: str
    bias_indication: str  # 'none', 'low', 'medium', 'high'


class ContextAware360BiasDetection:
    """
    Enhanced 360-degree bias detection with comprehensive context-aware analysis.

    Features:
    - Context-specific bias detection (per rater context)
    - Cross-context comparison and consistency analysis
    - Context-specific patterns (e.g., manager vs peer bias)
    - Context balance and coverage validation
    - Multi-context statistical analysis
    - Context-aware recommendations
    """

    # Standard 360-degree contexts
    STANDARD_CONTEXTS = {
        "peer_review",
        "manager_review",
        "direct_report_review",
        "self_review",
        "CEO",
        "P&C",
        "QA",
        "360_review",
    }

    # Required contexts for complete 360
    REQUIRED_360_CONTEXTS = {"peer_review", "manager_review", "direct_report_review", "self_review"}

    # Minimum evaluations per context
    MIN_EVALUATIONS_PER_CONTEXT = {
        "peer_review": 2,
        "manager_review": 1,
        "direct_report_review": 1,
        "self_review": 1,
        "CEO": 1,
        "P&C": 1,
        "QA": 1,
    }

    # Context hierarchy (for role-based analysis)
    CONTEXT_HIERARCHY = {
        "CEO": 5,
        "P&C": 4,
        "QA": 4,
        "manager_review": 3,
        "peer_review": 2,
        "direct_report_review": 2,
        "self_review": 1,
        "360_review": 2,
    }

    def __init__(self, db_session):
        self.db = db_session
        self.logger = logging.getLogger(__name__)
        self.bias_detector = BiasDetector(db_session)

    def generate_context_aware_report(self, cycle_id: int) -> Dict:
        """
        Generate comprehensive context-aware bias detection report.

        Args:
            cycle_id: Evaluation cycle ID

        Returns:
            Dictionary with complete context-aware analysis
        """
        findings = []
        context_findings = []
        cross_context_analyses = []

        # 1. Load all evaluation data grouped by context
        context_data = self._load_context_data(cycle_id)

        if not context_data:
            return {"status": "no_data", "message": "No evaluation data found for this cycle"}

        # 2. Context-specific bias detection
        for context, data in context_data.items():
            context_specific = self._analyze_context_specific_bias(
                context=context, ratings=data["ratings"], assignments=data["assignments"]
            )
            context_findings.extend(context_specific)

        # 3. Cross-context comparison
        cross_context_analyses = self._analyze_cross_context_comparisons(context_data)

        # 4. Context consistency analysis
        consistency_findings = self._analyze_context_consistency(cycle_id, context_data)
        findings.extend(consistency_findings)

        # 5. Context-specific patterns
        pattern_findings = self._detect_context_patterns(context_data)
        findings.extend(pattern_findings)

        # 6. Context balance and coverage
        balance_findings = self._analyze_context_balance(context_data)
        findings.extend(balance_findings)

        # 7. Multi-context statistical analysis
        statistical_findings = self._multi_context_statistical_analysis(context_data)
        findings.extend(statistical_findings)

        # 8. Context coverage validation
        coverage_findings = self._validate_context_coverage(cycle_id, context_data)
        findings.extend(coverage_findings)

        # Combine all findings
        all_findings = findings + context_findings

        # Calculate overall scores
        overall_bias_score = self._calculate_overall_bias_score(all_findings)
        context_bias_scores = self._calculate_context_bias_scores(context_findings)

        # Generate recommendations
        recommendations = self._generate_context_aware_recommendations(all_findings, cross_context_analyses, context_data)

        return {
            "cycle_id": cycle_id,
            "overall_bias_score": overall_bias_score,
            "context_bias_scores": context_bias_scores,
            "total_findings": len(all_findings),
            "context_specific_findings": len(context_findings),
            "cross_context_findings": len(findings),
            "findings": [
                {
                    "bias_type": f.bias_type,
                    "severity": f.severity,
                    "score": f.score,
                    "description": f.description,
                    "affected_raters": f.affected_raters,
                    "affected_targets": f.affected_targets,
                    "recommendations": f.recommendations,
                    "context": getattr(f, "context", None),
                }
                for f in all_findings
            ],
            "context_findings": [
                {
                    "context": f.context,
                    "bias_type": f.bias_type,
                    "severity": f.severity,
                    "score": f.score,
                    "description": f.description,
                    "comparison_with_other_contexts": f.comparison_with_other_contexts,
                }
                for f in context_findings
            ],
            "cross_context_analyses": [
                {
                    "context_pair": list(analysis.context_pair),
                    "mean_difference": analysis.mean_difference,
                    "statistical_significance": analysis.statistical_significance,
                    "p_value": analysis.p_value,
                    "effect_size": analysis.effect_size,
                    "interpretation": analysis.interpretation,
                    "bias_indication": analysis.bias_indication,
                }
                for analysis in cross_context_analyses
            ],
            "context_coverage": self._get_context_coverage_summary(context_data),
            "statistical_summary": self._get_multi_context_statistics(context_data),
            "recommendations": recommendations,
            "generated_at": datetime.utcnow().isoformat(),
        }

    def _load_context_data(self, cycle_id: int) -> Dict[str, Dict]:
        """
        Load all evaluation data grouped by rater context.

        Returns:
            Dictionary mapping context to data (ratings, assignments, etc.)
        """
        # Single query with join
        evaluations_and_assignments = (
            self.db.query(Evaluation, Assignment)
            .join(Assignment, Evaluation.assignment_id == Assignment.id)
            .filter(Assignment.cycle_id == cycle_id, Evaluation.status == "submitted", Evaluation.rating.isnot(None))
            .all()
        )

        context_data = defaultdict(
            lambda: {"ratings": [], "assignments": [], "raters": set(), "targets": set(), "rater_target_pairs": []}
        )

        for eval_obj, assignment in evaluations_and_assignments:
            context = assignment.rater_context or "unknown"

            context_data[context]["ratings"].append(eval_obj.rating)
            context_data[context]["assignments"].append(assignment)
            context_data[context]["raters"].add(assignment.rater_email)
            context_data[context]["targets"].add(assignment.target_email)
            context_data[context]["rater_target_pairs"].append(
                {"rater": assignment.rater_email, "target": assignment.target_email, "rating": eval_obj.rating}
            )

        # Convert sets to lists for JSON serialization
        for context in context_data:
            context_data[context]["raters"] = list(context_data[context]["raters"])
            context_data[context]["targets"] = list(context_data[context]["targets"])

        return dict(context_data)

    def _analyze_context_specific_bias(
        self, context: str, ratings: List[float], assignments: List[Assignment]
    ) -> List[ContextBiasFinding]:
        """Analyze bias specific to a rater context"""
        findings = []

        if len(ratings) < 3:
            return findings

        ratings_array = np.array(ratings)
        mean_rating = float(np.mean(ratings_array))
        std_rating = float(np.std(ratings_array))

        # 1. Check for centrality bias in this context
        expected_std = 1.29  # For 1-5 scale uniform distribution
        if std_rating < expected_std * 0.5:
            findings.append(
                ContextBiasFinding(
                    context=context,
                    bias_type="centrality_bias",
                    severity="medium",
                    score=1.0 - (std_rating / expected_std),
                    description=f"{context} raters show centrality bias (std={std_rating:.2f}, expected={expected_std:.2f})",
                    affected_raters=list(set(a.rater_email for a in assignments)),
                    affected_targets=list(set(a.target_email for a in assignments)),
                    evidence={"std_rating": std_rating, "expected_std": expected_std, "mean_rating": mean_rating},
                    recommendations=[
                        f"Provide training to {context} raters on using full rating scale",
                        "Clarify rating criteria for this context",
                        "Review examples of appropriate rating differentiation",
                    ],
                    comparison_with_other_contexts=None,
                )
            )

        # 2. Check for harshness/leniency in this context
        overall_mean = 3.0  # Midpoint of 1-5 scale
        bias = mean_rating - overall_mean

        if bias < -0.5:  # Harsh
            findings.append(
                ContextBiasFinding(
                    context=context,
                    bias_type="harshness_bias",
                    severity="medium",
                    score=min(abs(bias) / 2.0, 1.0),
                    description=f"{context} raters show harshness bias (mean={mean_rating:.2f}, expected={overall_mean:.2f})",
                    affected_raters=list(set(a.rater_email for a in assignments)),
                    affected_targets=list(set(a.target_email for a in assignments)),
                    evidence={"mean_rating": mean_rating, "expected_mean": overall_mean, "bias": bias},
                    recommendations=[
                        f"Calibration training for {context} raters",
                        "Review rating standards and examples",
                        "Consider if context-specific expectations are appropriate",
                    ],
                    comparison_with_other_contexts=None,
                )
            )
        elif bias > 0.5:  # Lenient
            findings.append(
                ContextBiasFinding(
                    context=context,
                    bias_type="leniency_bias",
                    severity="medium",
                    score=min(abs(bias) / 2.0, 1.0),
                    description=f"{context} raters show leniency bias (mean={mean_rating:.2f}, expected={overall_mean:.2f})",
                    affected_raters=list(set(a.rater_email for a in assignments)),
                    affected_targets=list(set(a.target_email for a in assignments)),
                    evidence={"mean_rating": mean_rating, "expected_mean": overall_mean, "bias": bias},
                    recommendations=[
                        f"Calibration training for {context} raters",
                        "Emphasize importance of differentiated ratings",
                        "Review if leniency is context-appropriate",
                    ],
                    comparison_with_other_contexts=None,
                )
            )

        # 3. Check for low variance (halo effect) in this context
        if std_rating < 0.5:
            findings.append(
                ContextBiasFinding(
                    context=context,
                    bias_type="halo_effect",
                    severity="high" if std_rating < 0.3 else "medium",
                    score=1.0 - (std_rating / 0.5),
                    description=f"{context} raters show halo effect (low variance: std={std_rating:.2f})",
                    affected_raters=list(set(a.rater_email for a in assignments)),
                    affected_targets=list(set(a.target_email for a in assignments)),
                    evidence={"std_rating": std_rating, "mean_rating": mean_rating},
                    recommendations=[
                        f"Train {context} raters on differentiated evaluation",
                        "Encourage independent assessment of each dimension",
                        "Review evaluation criteria clarity",
                    ],
                    comparison_with_other_contexts=None,
                )
            )

        return findings

    def _analyze_cross_context_comparisons(self, context_data: Dict[str, Dict]) -> List[CrossContextAnalysis]:
        """Compare ratings across different contexts"""
        analyses = []

        contexts = list(context_data.keys())

        # Compare all pairs of contexts
        for i, context1 in enumerate(contexts):
            for context2 in contexts[i + 1 :]:
                ratings1 = context_data[context1]["ratings"]
                ratings2 = context_data[context2]["ratings"]

                if len(ratings1) < 3 or len(ratings2) < 3:
                    continue

                # Statistical comparison
                mean1 = np.mean(ratings1)
                mean2 = np.mean(ratings2)
                mean_diff = mean1 - mean2

                # Perform t-test if we have enough data
                try:
                    t_stat, p_value = stats.ttest_ind(ratings1, ratings2)
                    significant = p_value < 0.05
                except:
                    t_stat, p_value = None, None
                    significant = False

                # Calculate effect size (Cohen's d)
                pooled_std = np.sqrt((np.var(ratings1) + np.var(ratings2)) / 2)
                effect_size = mean_diff / pooled_std if pooled_std > 0 else 0

                # Interpret effect size
                if abs(effect_size) < 0.2:
                    effect_interpretation = "negligible"
                elif abs(effect_size) < 0.5:
                    effect_interpretation = "small"
                elif abs(effect_size) < 0.8:
                    effect_interpretation = "medium"
                else:
                    effect_interpretation = "large"

                # Determine bias indication
                if significant and abs(effect_size) >= 0.5:
                    if abs(mean_diff) > 1.0:
                        bias_indication = "high"
                    elif abs(mean_diff) > 0.5:
                        bias_indication = "medium"
                    else:
                        bias_indication = "low"
                else:
                    bias_indication = "none"

                interpretation = (
                    f"{context1} mean ({mean1:.2f}) vs {context2} mean ({mean2:.2f}): "
                    f"difference={mean_diff:.2f}, effect={effect_interpretation}"
                )

                analyses.append(
                    CrossContextAnalysis(
                        context_pair=(context1, context2),
                        mean_difference=float(mean_diff),
                        statistical_significance=significant,
                        p_value=float(p_value) if p_value else None,
                        effect_size=float(effect_size),
                        interpretation=interpretation,
                        bias_indication=bias_indication,
                    )
                )

        return analyses

    def _analyze_context_consistency(self, cycle_id: int, context_data: Dict[str, Dict]) -> List[BiasFinding]:
        """Analyze consistency of ratings across contexts for same targets"""
        findings = []

        # Group by target across all contexts
        target_context_ratings = defaultdict(lambda: defaultdict(list))

        for context, data in context_data.items():
            for pair in data["rater_target_pairs"]:
                target_context_ratings[pair["target"]][context].append(pair["rating"])

        # Check consistency for each target
        inconsistent_targets = []
        for target, context_ratings in target_context_ratings.items():
            if len(context_ratings) < 2:
                continue

            # Calculate mean per context
            context_means = {ctx: np.mean(ratings) for ctx, ratings in context_ratings.items()}

            if len(context_means) >= 2:
                means = list(context_means.values())
                cv = np.std(means) / np.mean(means) if np.mean(means) > 0 else 0

                # High variation indicates inconsistency
                max_diff = max(means) - min(means)
                # Use both relative and absolute thresholds so small samples still flag clear gaps.
                if cv > 0.25 or max_diff >= 1.0:
                    inconsistent_targets.append(
                        {
                            "target": target,
                            "context_means": context_means,
                            "coefficient_of_variation": float(cv),
                            "max_difference": float(max_diff),
                        }
                    )

        if inconsistent_targets:
            severity = "high" if len(inconsistent_targets) > len(target_context_ratings) * 0.3 else "medium"

            findings.append(
                BiasFinding(
                    bias_type="context_inconsistency",
                    severity=severity,
                    score=len(inconsistent_targets) / len(target_context_ratings) if target_context_ratings else 0,
                    description=f"{len(inconsistent_targets)} targets show high variation across contexts",
                    affected_raters=[],
                    affected_targets=[t["target"] for t in inconsistent_targets],
                    evidence={"inconsistent_targets": inconsistent_targets},
                    recommendations=[
                        "Review evaluation criteria for consistency across contexts",
                        "Investigate why same targets receive different ratings from different contexts",
                        "Consider calibration sessions across all rater contexts",
                        "Ensure all contexts use same evaluation standards",
                    ],
                )
            )

        return findings

    def _detect_context_patterns(self, context_data: Dict[str, Dict]) -> List[BiasFinding]:
        """Detect specific patterns across contexts"""
        findings = []

        # Pattern 1: Hierarchy bias (higher hierarchy = higher ratings)
        hierarchy_means = {}
        for context, data in context_data.items():
            if context in self.CONTEXT_HIERARCHY and len(data["ratings"]) >= 3:
                hierarchy_means[context] = {"mean": np.mean(data["ratings"]), "hierarchy": self.CONTEXT_HIERARCHY[context]}

        if len(hierarchy_means) >= 2:
            # Check correlation between hierarchy and mean rating
            hierarchies = [v["hierarchy"] for v in hierarchy_means.values()]
            means = [v["mean"] for v in hierarchy_means.values()]

            if len(hierarchies) >= 2:
                correlation = np.corrcoef(hierarchies, means)[0, 1]

                if correlation > 0.5:  # Strong positive correlation
                    findings.append(
                        BiasFinding(
                            bias_type="hierarchy_bias",
                            severity="high",
                            score=min((correlation - 0.5) * 2, 1.0),
                            description=f"Hierarchy bias detected: higher hierarchy contexts rate higher (correlation={correlation:.3f})",
                            affected_raters=[],
                            affected_targets=[],
                            evidence={"hierarchy_means": hierarchy_means, "correlation": float(correlation)},
                            recommendations=[
                                "Review if hierarchy-based rating differences are appropriate",
                                "Provide training to reduce hierarchy bias",
                                "Consider anonymous evaluation to reduce hierarchy effects",
                                "Emphasize objective evaluation standards regardless of rater position",
                            ],
                        )
                    )

        # Pattern 2: Self-review inflation
        if "self_review" in context_data:
            self_ratings = context_data["self_review"]["ratings"]
            if len(self_ratings) >= 3:
                self_mean = np.mean(self_ratings)

                # Compare with other contexts
                other_means = [
                    np.mean(data["ratings"])
                    for ctx, data in context_data.items()
                    if ctx != "self_review" and len(data["ratings"]) >= 3
                ]

                if other_means:
                    other_mean = np.mean(other_means)
                    if self_mean > other_mean + 0.5:  # Self-rating significantly higher
                        findings.append(
                            BiasFinding(
                                bias_type="self_review_inflation",
                                severity="medium",
                                score=min((self_mean - other_mean) / 2.0, 1.0),
                                description=f"Self-review inflation: self-ratings ({self_mean:.2f}) significantly higher than others ({other_mean:.2f})",
                                affected_raters=[],
                                affected_targets=context_data["self_review"]["targets"],
                                evidence={
                                    "self_mean": float(self_mean),
                                    "other_mean": float(other_mean),
                                    "difference": float(self_mean - other_mean),
                                },
                                recommendations=[
                                    "Provide training on realistic self-assessment",
                                    "Emphasize importance of honest self-evaluation",
                                    "Consider self-review calibration exercises",
                                ],
                            )
                        )

        return findings

    def _analyze_context_balance(self, context_data: Dict[str, Dict]) -> List[BiasFinding]:
        """Analyze balance of evaluations across contexts"""
        findings = []

        context_counts = {ctx: len(data["ratings"]) for ctx, data in context_data.items()}

        # Check for missing required contexts (should work even if only 1 context exists)
        present_contexts = set(context_data.keys())
        missing_required = self.REQUIRED_360_CONTEXTS - present_contexts

        if missing_required:
            findings.append(
                BiasFinding(
                    bias_type="missing_required_contexts",
                    severity="high",
                    score=len(missing_required) / len(self.REQUIRED_360_CONTEXTS),
                    description=f"Missing required 360-degree contexts: {', '.join(missing_required)}",
                    affected_raters=[],
                    affected_targets=[],
                    evidence={
                        "missing_contexts": list(missing_required),
                        "present_contexts": list(present_contexts),
                        "required_contexts": list(self.REQUIRED_360_CONTEXTS),
                    },
                    recommendations=[
                        "Ensure all required contexts are represented",
                        "Review assignment process to include all perspectives",
                        "Validate 360-degree completeness before finalizing evaluations",
                    ],
                )
            )

        # Imbalance only makes sense when at least two contexts exist
        if len(context_counts) < 2:
            return findings

        counts = list(context_counts.values())
        mean_count = np.mean(counts)
        std_count = np.std(counts)
        cv = std_count / mean_count if mean_count > 0 else 0

        # Check for imbalance
        if cv > 0.5:
            findings.append(
                BiasFinding(
                    bias_type="context_imbalance",
                    severity="medium",
                    score=min(cv, 1.0),
                    description=f"Imbalanced distribution across contexts (CV={cv:.2f})",
                    affected_raters=[],
                    affected_targets=[],
                    evidence={"context_counts": context_counts, "coefficient_of_variation": float(cv)},
                    recommendations=[
                        "Balance evaluation assignments across all contexts",
                        "Ensure adequate representation from each perspective",
                        "Review assignment matrix for even distribution",
                    ],
                )
            )

        return findings

    def _multi_context_statistical_analysis(self, context_data: Dict[str, Dict]) -> List[BiasFinding]:
        """Perform multi-context statistical analysis"""
        findings = []

        # ANOVA across contexts
        if len(context_data) >= 2:
            context_groups = [data["ratings"] for data in context_data.values() if len(data["ratings"]) >= 3]

            if len(context_groups) >= 2:
                try:
                    f_stat, p_value = stats.f_oneway(*context_groups)

                    if p_value < 0.05:  # Significant difference
                        # Calculate effect size (eta-squared)
                        all_ratings = [r for group in context_groups for r in group]
                        grand_mean = np.mean(all_ratings)

                        ss_between = sum(len(group) * (np.mean(group) - grand_mean) ** 2 for group in context_groups)
                        ss_total = sum((r - grand_mean) ** 2 for r in all_ratings)
                        eta_squared = ss_between / ss_total if ss_total > 0 else 0

                        findings.append(
                            BiasFinding(
                                bias_type="multi_context_statistical_difference",
                                severity="high" if eta_squared > 0.2 else "medium",
                                score=min(eta_squared * 2, 1.0),
                                description=f"Statistically significant differences across contexts (F={f_stat:.2f}, p={p_value:.4f}, η²={eta_squared:.3f})",
                                affected_raters=[],
                                affected_targets=[],
                                evidence={
                                    "f_statistic": float(f_stat),
                                    "p_value": float(p_value),
                                    "eta_squared": float(eta_squared),
                                    "context_means": {
                                        ctx: float(np.mean(data["ratings"]))
                                        for ctx, data in context_data.items()
                                        if len(data["ratings"]) >= 3
                                    },
                                },
                                recommendations=[
                                    "Investigate why contexts show significant rating differences",
                                    "Review if differences are appropriate or indicate bias",
                                    "Consider context-specific calibration",
                                    "Ensure consistent evaluation standards across contexts",
                                ],
                            )
                        )
                except Exception as e:
                    self.logger.warning(f"Error in ANOVA: {e}")

        return findings

    def _validate_context_coverage(self, cycle_id: int, context_data: Dict[str, Dict]) -> List[BiasFinding]:
        """Validate that targets have adequate coverage across contexts"""
        findings = []

        # Get all targets
        all_targets = set()
        for data in context_data.values():
            all_targets.update(data["targets"])

        # Check coverage for each target
        target_context_coverage = defaultdict(set)
        for context, data in context_data.items():
            for target in data["targets"]:
                target_context_coverage[target].add(context)

        # Check for targets with insufficient context coverage
        insufficient_coverage = []
        for target, contexts in target_context_coverage.items():
            missing_required = self.REQUIRED_360_CONTEXTS - contexts

            # Check minimum evaluations per context
            context_counts = {}
            for context, data in context_data.items():
                if target in data["targets"]:
                    count = sum(1 for pair in data["rater_target_pairs"] if pair["target"] == target)
                    context_counts[context] = count

            insufficient = []
            for context, min_count in self.MIN_EVALUATIONS_PER_CONTEXT.items():
                if context in contexts and context_counts.get(context, 0) < min_count:
                    insufficient.append({"context": context, "current": context_counts.get(context, 0), "required": min_count})

            if missing_required or insufficient:
                insufficient_coverage.append(
                    {
                        "target": target,
                        "missing_contexts": list(missing_required),
                        "insufficient_evaluations": insufficient,
                        "present_contexts": list(contexts),
                    }
                )

        if insufficient_coverage:
            severity = "high" if len(insufficient_coverage) > len(all_targets) * 0.3 else "medium"

            findings.append(
                BiasFinding(
                    bias_type="insufficient_context_coverage",
                    severity=severity,
                    score=len(insufficient_coverage) / len(all_targets) if all_targets else 0,
                    description=f"{len(insufficient_coverage)} targets have insufficient context coverage",
                    affected_raters=[],
                    affected_targets=[t["target"] for t in insufficient_coverage],
                    evidence={"insufficient_coverage": insufficient_coverage},
                    recommendations=[
                        "Ensure all targets receive evaluations from all required contexts",
                        "Meet minimum evaluation requirements per context",
                        "Review assignment matrix for complete 360-degree coverage",
                    ],
                )
            )

        return findings

    def _calculate_overall_bias_score(self, findings: List[BiasFinding]) -> float:
        """Calculate overall bias score"""
        if not findings:
            return 0.0

        severity_weights = {"critical": 1.0, "high": 0.75, "medium": 0.5, "low": 0.25}

        weighted_scores = [f.score * severity_weights.get(f.severity, 0.5) for f in findings]

        max_score = max(weighted_scores) if weighted_scores else 0
        avg_score = np.mean(weighted_scores) if weighted_scores else 0

        return min(0.6 * max_score + 0.4 * avg_score, 1.0)

    def _calculate_context_bias_scores(self, context_findings: List[ContextBiasFinding]) -> Dict[str, float]:
        """Calculate bias scores per context"""
        context_scores = defaultdict(list)

        for finding in context_findings:
            severity_weights = {"critical": 1.0, "high": 0.75, "medium": 0.5, "low": 0.25}
            weight = severity_weights.get(finding.severity, 0.5)
            context_scores[finding.context].append(finding.score * weight)

        return {context: float(np.mean(scores)) if scores else 0.0 for context, scores in context_scores.items()}

    def _get_context_coverage_summary(self, context_data: Dict[str, Dict]) -> Dict:
        """Get summary of context coverage"""
        return {
            context: {
                "total_evaluations": len(data["ratings"]),
                "unique_raters": len(data["raters"]),
                "unique_targets": len(data["targets"]),
                "mean_rating": float(np.mean(data["ratings"])) if data["ratings"] else 0,
                "std_rating": float(np.std(data["ratings"])) if data["ratings"] else 0,
            }
            for context, data in context_data.items()
        }

    def _get_multi_context_statistics(self, context_data: Dict[str, Dict]) -> Dict:
        """Get statistical summary across all contexts"""
        all_ratings = [rating for data in context_data.values() for rating in data["ratings"]]

        if not all_ratings:
            return {}

        return {
            "total_evaluations": len(all_ratings),
            "total_contexts": len(context_data),
            "overall_mean": float(np.mean(all_ratings)),
            "overall_std": float(np.std(all_ratings)),
            "overall_min": float(np.min(all_ratings)),
            "overall_max": float(np.max(all_ratings)),
            "overall_median": float(np.median(all_ratings)),
            "context_means": {ctx: float(np.mean(data["ratings"])) for ctx, data in context_data.items() if data["ratings"]},
            "context_stds": {ctx: float(np.std(data["ratings"])) for ctx, data in context_data.items() if data["ratings"]},
        }

    def _generate_context_aware_recommendations(
        self, findings: List[BiasFinding], cross_context_analyses: List[CrossContextAnalysis], context_data: Dict[str, Dict]
    ) -> List[str]:
        """Generate context-aware recommendations"""
        recommendations = []

        # Group findings by type
        finding_types = defaultdict(int)
        for finding in findings:
            finding_types[finding.bias_type] += 1

        # Context-specific recommendations
        high_bias_contexts = []
        for context, data in context_data.items():
            if len(data["ratings"]) >= 3:
                mean = np.mean(data["ratings"])
                std = np.std(data["ratings"])

                # Flag contexts with extreme means or low variance
                if mean < 2.0 or mean > 4.5 or std < 0.5:
                    high_bias_contexts.append(context)

        if high_bias_contexts:
            recommendations.append(f"Priority: Provide calibration training for contexts: {', '.join(high_bias_contexts)}")

        # Cross-context recommendations
        high_bias_pairs = [analysis for analysis in cross_context_analyses if analysis.bias_indication in ["high", "medium"]]

        if high_bias_pairs:
            recommendations.append(f"Review rating differences between {len(high_bias_pairs)} context pairs showing bias")

        # Coverage recommendations
        if finding_types.get("insufficient_context_coverage", 0) > 0:
            recommendations.append("CRITICAL: Ensure complete 360-degree coverage for all targets")

        if finding_types.get("missing_required_contexts", 0) > 0:
            recommendations.append("CRITICAL: Include all required rater contexts in evaluation cycle")

        # Pattern-based recommendations
        if finding_types.get("hierarchy_bias", 0) > 0:
            recommendations.append("Implement measures to reduce hierarchy-based rating bias")

        if finding_types.get("self_review_inflation", 0) > 0:
            recommendations.append("Provide training on realistic self-assessment")

        # Consistency recommendations
        if finding_types.get("context_inconsistency", 0) > 0:
            recommendations.append("Conduct cross-context calibration sessions to improve consistency")

        if not recommendations:
            recommendations.append("No significant context-specific bias detected. Continue monitoring.")

        return recommendations

    def get_target_context_analysis(self, cycle_id: int, target_email: str) -> Dict:
        """
        Get detailed context analysis for a specific target.

        Args:
            cycle_id: Evaluation cycle ID
            target_email: Target person email

        Returns:
            Dictionary with context-specific analysis for the target
        """
        context_data = self._load_context_data(cycle_id)

        # Filter to this target
        target_context_ratings = {}
        for context, data in context_data.items():
            target_ratings = [pair["rating"] for pair in data["rater_target_pairs"] if pair["target"] == target_email]
            if target_ratings:
                target_context_ratings[context] = target_ratings

        if not target_context_ratings:
            return {
                "target_email": target_email,
                "status": "no_evaluations",
                "message": "No evaluations found for this target",
            }

        # Calculate statistics per context
        context_stats = {}
        for context, ratings in target_context_ratings.items():
            context_stats[context] = {
                "count": len(ratings),
                "mean": float(np.mean(ratings)),
                "std": float(np.std(ratings)),
                "min": float(np.min(ratings)),
                "max": float(np.max(ratings)),
            }

        # Check consistency
        means = [stats["mean"] for stats in context_stats.values()]
        if len(means) >= 2:
            cv = np.std(means) / np.mean(means) if np.mean(means) > 0 else 0
            consistency = "high" if cv < 0.2 else "medium" if cv < 0.4 else "low"
        else:
            cv = None
            consistency = "unknown"

        # Check completeness
        present_contexts = set(target_context_ratings.keys())
        missing_contexts = self.REQUIRED_360_CONTEXTS - present_contexts

        return {
            "target_email": target_email,
            "status": "analyzed",
            "context_ratings": context_stats,
            "missing_contexts": list(missing_contexts),
            "is_complete_360": len(missing_contexts) == 0,
            "consistency": {"coefficient_of_variation": float(cv) if cv is not None else None, "interpretation": consistency},
            "overall_mean": float(np.mean([r for ratings in target_context_ratings.values() for r in ratings])),
            "context_count": len(target_context_ratings),
        }
