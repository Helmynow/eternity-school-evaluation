"""
Complete Bias Detection System for 360-Degree Evaluations
Comprehensive system for detecting and analyzing bias in multi-rater evaluations.
"""

import logging
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import date, datetime
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy import stats

from ai_models.bias_algorithms import AdvancedBiasAlgorithms
from backend.bias_detection import BiasDetector
from backend.database import Assignment, Cycle, Evaluation, Person


@dataclass
class BiasFinding:
    """Represents a single bias finding"""

    bias_type: str
    severity: str  # 'low', 'medium', 'high', 'critical'
    score: float  # 0-1, where 1 is most biased
    description: str
    affected_raters: List[str]
    affected_targets: List[str]
    evidence: Dict
    recommendations: List[str]


@dataclass
class BiasReport:
    """Complete bias detection report"""

    cycle_id: int
    overall_bias_score: float  # 0-1, composite score
    total_evaluations: int
    total_raters: int
    total_targets: int
    findings: List[BiasFinding]
    context_coverage: Dict  # Coverage of different rater contexts
    statistical_summary: Dict
    recommendations: List[str]
    generated_at: str


class Complete360BiasDetection:
    """
    Complete bias detection system for 360-degree evaluations.

    Detects and analyzes:
    - Role-based bias (manager vs peer vs direct report)
    - Temporal bias (recency, primacy)
    - Distribution bias (centrality, leniency, harshness)
    - Similarity bias (halo effect, inter-rater agreement)
    - Structural bias (coverage, balance)
    - Advanced ML-detected patterns
    """

    # Required contexts for complete 360-degree evaluation
    REQUIRED_360_CONTEXTS = {"peer_review", "manager_review", "direct_report_review", "self_review"}

    # Minimum evaluations per context for valid 360
    MIN_EVALUATIONS_PER_CONTEXT = {"peer_review": 2, "manager_review": 1, "direct_report_review": 1, "self_review": 1}

    def __init__(self, db_session):
        self.db = db_session
        self.logger = logging.getLogger(__name__)
        self.bias_detector = BiasDetector(db_session)
        self.advanced_detector = AdvancedBiasAlgorithms(db_session)

    def generate_complete_report(self, cycle_id: int) -> BiasReport:
        """
        Generate a complete bias detection report for a 360-degree evaluation cycle.

        Args:
            cycle_id: The evaluation cycle ID

        Returns:
            Complete BiasReport with all findings and recommendations
        """
        findings = []

        # 1. Structural/360-degree completeness checks
        structural_findings = self._check_360_completeness(cycle_id)
        findings.extend(structural_findings)

        # 2. Role-based bias
        role_findings = self._analyze_role_bias(cycle_id)
        findings.extend(role_findings)

        # 3. Temporal bias
        temporal_findings = self._analyze_temporal_bias(cycle_id)
        findings.extend(temporal_findings)

        # 4. Distribution bias
        distribution_findings = self._analyze_distribution_bias(cycle_id)
        findings.extend(distribution_findings)

        # 5. Similarity bias
        similarity_findings = self._analyze_similarity_bias(cycle_id)
        findings.extend(similarity_findings)

        # 6. Advanced ML-based detection
        ml_findings = self._analyze_ml_patterns(cycle_id)
        findings.extend(ml_findings)

        # 7. Inter-rater reliability
        reliability_findings = self._analyze_inter_rater_reliability(cycle_id)
        findings.extend(reliability_findings)

        # 8. Context balance
        balance_findings = self._analyze_context_balance(cycle_id)
        findings.extend(balance_findings)

        # Calculate overall bias score
        overall_score = self._calculate_overall_bias_score(findings)

        # Get statistical summary
        statistical_summary = self._get_statistical_summary(cycle_id)

        # Get context coverage
        context_coverage = self._get_context_coverage(cycle_id)

        # Generate recommendations
        recommendations = self._generate_recommendations(findings, context_coverage)

        return BiasReport(
            cycle_id=cycle_id,
            overall_bias_score=overall_score,
            total_evaluations=statistical_summary.get("total_evaluations", 0),
            total_raters=statistical_summary.get("total_raters", 0),
            total_targets=statistical_summary.get("total_targets", 0),
            findings=findings,
            context_coverage=context_coverage,
            statistical_summary=statistical_summary,
            recommendations=recommendations,
            generated_at=datetime.utcnow().isoformat(),
        )

    def _check_360_completeness(self, cycle_id: int) -> List[BiasFinding]:
        """Check if 360-degree evaluations are complete"""
        findings = []

        # Get all assignments
        assignments = self.db.query(Assignment).filter(Assignment.cycle_id == cycle_id).all()

        # Group by target
        target_contexts = defaultdict(set)
        target_evaluations = defaultdict(int)

        for assignment in assignments:
            target_contexts[assignment.target_email].add(assignment.rater_context)
            target_evaluations[assignment.target_email] += 1

        # Check each target for 360 completeness
        incomplete_targets = []
        for target_email, contexts in target_contexts.items():
            missing_contexts = self.REQUIRED_360_CONTEXTS - contexts

            if missing_contexts:
                incomplete_targets.append(
                    {"target": target_email, "missing_contexts": list(missing_contexts), "present_contexts": list(contexts)}
                )

        if incomplete_targets:
            severity = "high" if len(incomplete_targets) > len(target_contexts) * 0.3 else "medium"

            findings.append(
                BiasFinding(
                    bias_type="structural_incomplete_360",
                    severity=severity,
                    score=len(incomplete_targets) / len(target_contexts) if target_contexts else 1.0,
                    description=f"{len(incomplete_targets)} targets missing required 360-degree perspectives",
                    affected_raters=[],
                    affected_targets=[t["target"] for t in incomplete_targets],
                    evidence={
                        "incomplete_targets": incomplete_targets,
                        "total_targets": len(target_contexts),
                        "required_contexts": list(self.REQUIRED_360_CONTEXTS),
                    },
                    recommendations=[
                        "Ensure all targets receive evaluations from peers, managers, direct reports, and self",
                        "Review assignment matrix to identify missing perspectives",
                        "Consider minimum evaluation requirements per context",
                    ],
                )
            )

        # Check evaluation counts per context
        context_counts = defaultdict(lambda: defaultdict(int))
        for assignment in assignments:
            context_counts[assignment.target_email][assignment.rater_context] += 1

        insufficient_evaluations = []
        for target_email, counts in context_counts.items():
            for context, min_count in self.MIN_EVALUATIONS_PER_CONTEXT.items():
                if counts.get(context, 0) < min_count:
                    insufficient_evaluations.append(
                        {"target": target_email, "context": context, "current": counts.get(context, 0), "required": min_count}
                    )

        if insufficient_evaluations:
            findings.append(
                BiasFinding(
                    bias_type="structural_insufficient_evaluations",
                    severity="medium",
                    score=len(insufficient_evaluations) / (len(context_counts) * len(self.MIN_EVALUATIONS_PER_CONTEXT)),
                    description=f"Some targets have insufficient evaluations per context",
                    affected_raters=[],
                    affected_targets=list(set(t["target"] for t in insufficient_evaluations)),
                    evidence={"insufficient": insufficient_evaluations},
                    recommendations=[
                        "Increase number of evaluations per context to meet minimum requirements",
                        "Review assignment distribution to ensure adequate coverage",
                    ],
                )
            )

        return findings

    def _analyze_role_bias(self, cycle_id: int) -> List[BiasFinding]:
        """Analyze role-based bias patterns"""
        findings = []

        role_result = self.bias_detector.detect_role_bias(cycle_id)

        if role_result.get("status") != "analyzed":
            return findings

        contexts = role_result.get("contexts", {})
        if len(contexts) < 2:
            return findings

        # Calculate mean differences between contexts
        context_means = {ctx: data["mean"] for ctx, data in contexts.items()}
        mean_values = list(context_means.values())

        if len(mean_values) >= 2:
            max_diff = max(mean_values) - min(mean_values)

            if max_diff > 1.0:  # Significant difference
                severity = "high" if max_diff > 1.5 else "medium"

                # Find which contexts differ most
                sorted_contexts = sorted(context_means.items(), key=lambda x: x[1])
                highest = sorted_contexts[-1]
                lowest = sorted_contexts[0]

                findings.append(
                    BiasFinding(
                        bias_type="role_bias",
                        severity=severity,
                        score=min(max_diff / 2.0, 1.0),  # Normalize to 0-1
                        description=f"Significant rating differences between contexts: {highest[0]} ({highest[1]:.2f}) vs {lowest[0]} ({lowest[1]:.2f})",
                        affected_raters=[],
                        affected_targets=[],
                        evidence={
                            "context_means": context_means,
                            "max_difference": max_diff,
                            "statistical_test": role_result.get("statistical_test", {}),
                        },
                        recommendations=[
                            "Review rating criteria across different rater contexts",
                            "Consider calibration training for raters",
                            "Investigate if role relationships are affecting objectivity",
                        ],
                    )
                )

        return findings

    def _analyze_temporal_bias(self, cycle_id: int) -> List[BiasFinding]:
        """Analyze temporal bias (recency, primacy)"""
        findings = []

        recency_result = self.bias_detector.detect_recency_bias(cycle_id)

        if recency_result.get("status") != "analyzed":
            return findings

        correlation = recency_result.get("correlation", 0)
        mean_difference = recency_result.get("mean_difference", 0)

        if abs(correlation) > 0.3 or abs(mean_difference) > 0.5:
            severity = "high" if abs(correlation) > 0.5 or abs(mean_difference) > 1.0 else "medium"

            findings.append(
                BiasFinding(
                    bias_type="temporal_bias",
                    severity=severity,
                    score=min(abs(correlation) * 0.5 + abs(mean_difference) / 2.0, 1.0),
                    description=f"Temporal bias detected: correlation={correlation:.3f}, mean_diff={mean_difference:.3f}",
                    affected_raters=[],
                    affected_targets=[],
                    evidence=recency_result,
                    recommendations=[
                        "Implement staggered evaluation deadlines to reduce recency effects",
                        "Provide training on evaluating performance across entire period",
                        "Consider requiring documentation of performance throughout the cycle",
                    ],
                )
            )

        return findings

    def _analyze_distribution_bias(self, cycle_id: int) -> List[BiasFinding]:
        """Analyze distribution biases (centrality, harshness, leniency)"""
        findings = []

        # Centrality bias
        centrality_result = self.bias_detector.detect_centrality_bias(cycle_id)
        if centrality_result.get("status") == "analyzed":
            std_rating = centrality_result.get("std_rating", 0)
            expected_std = centrality_result.get("expected_std_uniform", 1.29)
            centrality_index = centrality_result.get("centrality_index", 1.0)

            if centrality_index < 0.5:  # Low variance indicates centrality bias
                findings.append(
                    BiasFinding(
                        bias_type="centrality_bias",
                        severity="medium",
                        score=1.0 - centrality_index,
                        description=f"Centrality bias: raters avoiding extreme ratings (std={std_rating:.2f}, expected={expected_std:.2f})",
                        affected_raters=[],
                        affected_targets=[],
                        evidence=centrality_result,
                        recommendations=[
                            "Provide training on using full rating scale appropriately",
                            "Clarify rating scale definitions and anchors",
                            "Encourage honest, differentiated ratings",
                        ],
                    )
                )

        # Harshness/Leniency bias
        harshness_result = self.bias_detector.detect_harshness_bias(cycle_id)
        if harshness_result.get("status") == "analyzed":
            rater_bias = harshness_result.get("rater_bias", {})

            harsh_raters = []
            lenient_raters = []

            for rater_email, data in rater_bias.items():
                bias = data.get("bias", 0)
                if bias < -0.5:
                    harsh_raters.append({"rater": rater_email, "bias": bias, "mean_rating": data.get("mean_rating", 0)})
                elif bias > 0.5:
                    lenient_raters.append({"rater": rater_email, "bias": bias, "mean_rating": data.get("mean_rating", 0)})

            if harsh_raters:
                findings.append(
                    BiasFinding(
                        bias_type="harshness_bias",
                        severity="medium",
                        score=min(len(harsh_raters) / max(len(rater_bias), 1) * 2, 1.0),
                        description=f"{len(harsh_raters)} raters show harshness bias (consistently rate lower)",
                        affected_raters=[r["rater"] for r in harsh_raters],
                        affected_targets=[],
                        evidence={"harsh_raters": harsh_raters},
                        recommendations=[
                            "Provide calibration training for harsh raters",
                            "Review rating criteria and examples with affected raters",
                            "Consider rater calibration sessions",
                        ],
                    )
                )

            if lenient_raters:
                findings.append(
                    BiasFinding(
                        bias_type="leniency_bias",
                        severity="medium",
                        score=min(len(lenient_raters) / max(len(rater_bias), 1) * 2, 1.0),
                        description=f"{len(lenient_raters)} raters show leniency bias (consistently rate higher)",
                        affected_raters=[r["rater"] for r in lenient_raters],
                        affected_targets=[],
                        evidence={"lenient_raters": lenient_raters},
                        recommendations=[
                            "Provide calibration training for lenient raters",
                            "Emphasize importance of differentiated ratings",
                            "Review rating standards and expectations",
                        ],
                    )
                )

        return findings

    def _analyze_similarity_bias(self, cycle_id: int) -> List[BiasFinding]:
        """Analyze similarity bias (halo effect)"""
        findings = []

        similarity_result = self.bias_detector.detect_similarity_bias(cycle_id)

        if similarity_result.get("status") == "analyzed":
            bias_flags = similarity_result.get("bias_flags", [])

            if bias_flags:
                high_severity = [f for f in bias_flags if f.get("severity") == "high"]
                medium_severity = [f for f in bias_flags if f.get("severity") == "medium"]

                if high_severity or medium_severity:
                    severity = "high" if high_severity else "medium"

                    findings.append(
                        BiasFinding(
                            bias_type="similarity_bias_halo",
                            severity=severity,
                            score=len(bias_flags) / max(similarity_result.get("total_raters_checked", 1), 1),
                            description=f"Halo effect detected: {len(bias_flags)} raters show low variance in ratings",
                            affected_raters=[f.get("rater_id") for f in bias_flags],
                            affected_targets=[],
                            evidence=similarity_result,
                            recommendations=[
                                "Provide training on differentiated evaluation across dimensions",
                                "Encourage raters to evaluate each aspect independently",
                                "Review evaluation criteria to ensure clarity",
                            ],
                        )
                    )

        return findings

    def _analyze_ml_patterns(self, cycle_id: int) -> List[BiasFinding]:
        """Analyze using advanced ML algorithms"""
        findings = []

        # Outlier detection
        try:
            outlier_result = self.advanced_detector.detect_outlier_ratings(cycle_id)
            if outlier_result.get("status") == "analyzed":
                outliers = outlier_result.get("outliers", [])
                outlier_rate = outlier_result.get("outlier_rate", 0)

                if outlier_rate > 0.15:  # More than 15% outliers
                    findings.append(
                        BiasFinding(
                            bias_type="outlier_patterns",
                            severity="high" if outlier_rate > 0.25 else "medium",
                            score=outlier_rate,
                            description=f"High rate of outlier ratings detected ({outlier_rate:.1%})",
                            affected_raters=list(set(o.get("rater_email") for o in outliers if o.get("rater_email"))),
                            affected_targets=list(set(o.get("target_email") for o in outliers if o.get("target_email"))),
                            evidence=outlier_result,
                            recommendations=[
                                "Review outlier evaluations for potential bias or errors",
                                "Investigate specific rater-target pairs with extreme ratings",
                                "Consider additional validation for outlier cases",
                            ],
                        )
                    )
        except Exception as e:
            self.logger.warning(f"Error in outlier detection: {e}")

        # Reciprocal bias
        try:
            reciprocal_result = self.advanced_detector.detect_reciprocal_bias(cycle_id)
            if reciprocal_result.get("status") == "analyzed":
                pairs = reciprocal_result.get("reciprocal_pairs", [])

                if len(pairs) > 0:
                    findings.append(
                        BiasFinding(
                            bias_type="reciprocal_bias",
                            severity="medium",
                            score=min(len(pairs) / 10.0, 1.0),
                            description=f"Reciprocal bias detected: {len(pairs)} pairs with mutual high ratings",
                            affected_raters=list(
                                set(p.get("person_a") for p in pairs) | set(p.get("person_b") for p in pairs)
                            ),
                            affected_targets=[],
                            evidence=reciprocal_result,
                            recommendations=[
                                "Review reciprocal high ratings for potential bias",
                                "Consider anonymous evaluation to reduce reciprocal effects",
                                "Emphasize objective evaluation standards",
                            ],
                        )
                    )
        except Exception as e:
            self.logger.warning(f"Error in reciprocal bias detection: {e}")

        return findings

    def _analyze_inter_rater_reliability(self, cycle_id: int) -> List[BiasFinding]:
        """Analyze inter-rater reliability (agreement between raters)"""
        findings = []

        evaluations = (
            self.db.query(Evaluation)
            .join(Assignment)
            .filter(Assignment.cycle_id == cycle_id, Evaluation.status == "submitted", Evaluation.rating.isnot(None))
            .all()
        )

        if len(evaluations) < 10:
            return findings

        # Group evaluations by target
        target_ratings = defaultdict(list)

        for eval in evaluations:
            assignment = self.db.query(Assignment).filter(Assignment.id == eval.assignment_id).first()
            if assignment:
                target_ratings[assignment.target_email].append(eval.rating)

        # Calculate inter-rater reliability (using coefficient of variation)
        low_reliability_targets = []
        for target_email, ratings in target_ratings.items():
            if len(ratings) >= 3:
                cv = np.std(ratings) / np.mean(ratings) if np.mean(ratings) > 0 else 0
                # High CV indicates low agreement
                if cv > 0.3:  # More than 30% variation
                    low_reliability_targets.append(
                        {
                            "target": target_email,
                            "cv": cv,
                            "mean": np.mean(ratings),
                            "std": np.std(ratings),
                            "count": len(ratings),
                        }
                    )

        if low_reliability_targets:
            findings.append(
                BiasFinding(
                    bias_type="low_inter_rater_reliability",
                    severity="medium",
                    score=len(low_reliability_targets) / len(target_ratings) if target_ratings else 0,
                    description=f"Low inter-rater reliability for {len(low_reliability_targets)} targets",
                    affected_raters=[],
                    affected_targets=[t["target"] for t in low_reliability_targets],
                    evidence={"low_reliability_targets": low_reliability_targets},
                    recommendations=[
                        "Review evaluation criteria for clarity and consistency",
                        "Provide rater training on evaluation standards",
                        "Consider calibration sessions to align rater expectations",
                    ],
                )
            )

        return findings

    def _analyze_context_balance(self, cycle_id: int) -> List[BiasFinding]:
        """Analyze balance of evaluations across contexts"""
        findings = []

        assignments = self.db.query(Assignment).filter(Assignment.cycle_id == cycle_id).all()

        # Count evaluations per context
        context_counts = defaultdict(int)
        for assignment in assignments:
            context_counts[assignment.rater_context] += 1

        if len(context_counts) < 2:
            return findings

        counts = list(context_counts.values())
        mean_count = np.mean(counts)
        std_count = np.std(counts)
        cv = std_count / mean_count if mean_count > 0 else 0

        if cv > 0.5:  # High variation in context distribution
            findings.append(
                BiasFinding(
                    bias_type="context_imbalance",
                    severity="medium",
                    score=min(cv, 1.0),
                    description=f"Imbalanced distribution of evaluations across contexts (CV={cv:.2f})",
                    affected_raters=[],
                    affected_targets=[],
                    evidence={"context_counts": dict(context_counts), "coefficient_of_variation": cv},
                    recommendations=[
                        "Balance evaluation assignments across all contexts",
                        "Ensure adequate representation from each perspective",
                        "Review assignment matrix for even distribution",
                    ],
                )
            )

        return findings

    def _calculate_overall_bias_score(self, findings: List[BiasFinding]) -> float:
        """Calculate overall bias score from all findings"""
        if not findings:
            return 0.0

        # Weight findings by severity
        severity_weights = {"critical": 1.0, "high": 0.75, "medium": 0.5, "low": 0.25}

        weighted_scores = []
        for finding in findings:
            weight = severity_weights.get(finding.severity, 0.5)
            weighted_scores.append(finding.score * weight)

        # Take maximum and average
        max_score = max(weighted_scores) if weighted_scores else 0
        avg_score = np.mean(weighted_scores) if weighted_scores else 0

        # Combine: 60% max, 40% average
        overall = 0.6 * max_score + 0.4 * avg_score

        return min(overall, 1.0)

    def _get_statistical_summary(self, cycle_id: int) -> Dict:
        """Get statistical summary of evaluations"""
        evaluations = (
            self.db.query(Evaluation)
            .join(Assignment)
            .filter(Assignment.cycle_id == cycle_id, Evaluation.status == "submitted", Evaluation.rating.isnot(None))
            .all()
        )

        if not evaluations:
            return {"total_evaluations": 0, "total_raters": 0, "total_targets": 0, "mean_rating": 0, "std_rating": 0}

        ratings = [e.rating for e in evaluations]

        # Get unique raters and targets
        raters = set()
        targets = set()

        for eval in evaluations:
            assignment = self.db.query(Assignment).filter(Assignment.id == eval.assignment_id).first()
            if assignment:
                raters.add(assignment.rater_email)
                targets.add(assignment.target_email)

        return {
            "total_evaluations": len(evaluations),
            "total_raters": len(raters),
            "total_targets": len(targets),
            "mean_rating": float(np.mean(ratings)),
            "std_rating": float(np.std(ratings)),
            "min_rating": float(np.min(ratings)),
            "max_rating": float(np.max(ratings)),
            "median_rating": float(np.median(ratings)),
        }

    def _get_context_coverage(self, cycle_id: int) -> Dict:
        """Get coverage statistics by context"""
        assignments = self.db.query(Assignment).filter(Assignment.cycle_id == cycle_id).all()

        context_counts = defaultdict(int)
        context_targets = defaultdict(set)

        for assignment in assignments:
            context_counts[assignment.rater_context] += 1
            context_targets[assignment.rater_context].add(assignment.target_email)

        coverage = {}
        for context, count in context_counts.items():
            coverage[context] = {
                "total_assignments": count,
                "unique_targets": len(context_targets[context]),
                "avg_evaluations_per_target": count / len(context_targets[context]) if context_targets[context] else 0,
            }

        return coverage

    def _generate_recommendations(self, findings: List[BiasFinding], context_coverage: Dict) -> List[str]:
        """Generate overall recommendations based on findings"""
        recommendations = []

        # Count findings by type
        finding_types = defaultdict(int)
        for finding in findings:
            finding_types[finding.bias_type] += 1

        # Overall recommendations
        if finding_types.get("structural_incomplete_360", 0) > 0:
            recommendations.append(
                "CRITICAL: Ensure all targets receive complete 360-degree evaluations from all required perspectives"
            )

        if finding_types.get("role_bias", 0) > 0:
            recommendations.append("Implement rater calibration training to reduce role-based bias")

        if finding_types.get("harshness_bias", 0) > 0 or finding_types.get("leniency_bias", 0) > 0:
            recommendations.append("Provide individual feedback and training to raters showing harshness or leniency bias")

        if finding_types.get("similarity_bias_halo", 0) > 0:
            recommendations.append("Train raters on differentiated evaluation to reduce halo effect")

        if finding_types.get("temporal_bias", 0) > 0:
            recommendations.append("Implement measures to reduce recency bias in evaluations")

        # Check context coverage
        if context_coverage:
            total_contexts = len(context_coverage)
            if total_contexts < len(self.REQUIRED_360_CONTEXTS):
                recommendations.append(
                    f"Expand evaluation coverage: currently {total_contexts} contexts, need {len(self.REQUIRED_360_CONTEXTS)}"
                )

        if not recommendations:
            recommendations.append(
                "No significant bias patterns detected. Continue monitoring and maintain evaluation standards."
            )

        return recommendations

    def get_bias_summary_by_target(self, cycle_id: int, target_email: str) -> Dict:
        """
        Get bias summary for a specific target.

        Args:
            cycle_id: Evaluation cycle ID
            target_email: Target person email

        Returns:
            Dictionary with bias analysis for the target
        """
        evaluations = (
            self.db.query(Evaluation)
            .join(Assignment)
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
                "target_email": target_email,
                "status": "no_evaluations",
                "message": "No evaluations found for this target",
            }

        # Group by context
        context_ratings = defaultdict(list)
        for eval in evaluations:
            assignment = self.db.query(Assignment).filter(Assignment.id == eval.assignment_id).first()
            if assignment:
                context_ratings[assignment.rater_context].append(eval.rating)

        # Calculate statistics
        all_ratings = [e.rating for e in evaluations]

        # Check for missing contexts
        missing_contexts = self.REQUIRED_360_CONTEXTS - set(context_ratings.keys())

        # Calculate inter-rater reliability
        cv = np.std(all_ratings) / np.mean(all_ratings) if np.mean(all_ratings) > 0 else 0

        return {
            "target_email": target_email,
            "status": "analyzed",
            "total_evaluations": len(evaluations),
            "mean_rating": float(np.mean(all_ratings)),
            "std_rating": float(np.std(all_ratings)),
            "context_breakdown": {
                ctx: {"count": len(ratings), "mean": float(np.mean(ratings)), "std": float(np.std(ratings))}
                for ctx, ratings in context_ratings.items()
            },
            "missing_contexts": list(missing_contexts),
            "inter_rater_reliability": {
                "coefficient_of_variation": float(cv),
                "interpretation": "high" if cv < 0.2 else "medium" if cv < 0.4 else "low",
            },
            "is_complete_360": len(missing_contexts) == 0,
        }

    def export_report_to_dict(self, report: BiasReport) -> Dict:
        """Export bias report to dictionary for API responses"""
        return {
            "cycle_id": report.cycle_id,
            "overall_bias_score": report.overall_bias_score,
            "bias_level": self._score_to_level(report.overall_bias_score),
            "total_evaluations": report.total_evaluations,
            "total_raters": report.total_raters,
            "total_targets": report.total_targets,
            "findings_count": len(report.findings),
            "findings_by_type": self._group_findings_by_type(report.findings),
            "findings_by_severity": self._group_findings_by_severity(report.findings),
            "findings": [
                {
                    "bias_type": f.bias_type,
                    "severity": f.severity,
                    "score": f.score,
                    "description": f.description,
                    "affected_raters": f.affected_raters,
                    "affected_targets": f.affected_targets,
                    "recommendations": f.recommendations,
                }
                for f in report.findings
            ],
            "context_coverage": report.context_coverage,
            "statistical_summary": report.statistical_summary,
            "recommendations": report.recommendations,
            "generated_at": report.generated_at,
        }

    def _score_to_level(self, score: float) -> str:
        """Convert bias score to level"""
        if score >= 0.7:
            return "critical"
        elif score >= 0.5:
            return "high"
        elif score >= 0.3:
            return "medium"
        else:
            return "low"

    def _group_findings_by_type(self, findings: List[BiasFinding]) -> Dict:
        """Group findings by bias type"""
        grouped = defaultdict(int)
        for finding in findings:
            grouped[finding.bias_type] += 1
        return dict(grouped)

    def _group_findings_by_severity(self, findings: List[BiasFinding]) -> Dict:
        """Group findings by severity"""
        grouped = defaultdict(int)
        for finding in findings:
            grouped[finding.severity] += 1
        return dict(grouped)
