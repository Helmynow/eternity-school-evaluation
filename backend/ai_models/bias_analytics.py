"""
Bias Analytics System
Comprehensive bias reporting with rater fairness scores, department heatmaps, trend analysis, and mitigation suggestions.
"""

import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from backend.bias_detection import BiasDetector
from backend.bias_detection_360 import Complete360BiasDetection
from backend.database import Assignment, Cycle, Evaluation, Person


class BiasAnalytics:
    """
    Comprehensive bias analytics system for generating detailed bias reports.

    Features:
    - Rater fairness scores
    - Department bias heat maps
    - Trend analysis over time (-1 to 1 scale)
    - Mitigation suggestions and remediation plans
    """

    def __init__(self, db_session):
        self.db = db_session
        self.logger = logging.getLogger(__name__)
        self.bias_detector = BiasDetector(db_session)
        self.complete_detector = Complete360BiasDetection(db_session)

    def generate_bias_report(self, cycle: str) -> Dict:
        """
        Generate comprehensive bias report for a cycle.

        Args:
            cycle: Cycle ID (int) or cycle code (str)

        Returns:
            Dictionary containing:
            - rater_bias_scores: Fairness scores for each rater
            - department_bias_heat_map: Heat map data by department
            - trend_analysis: Bias trends over time (-1 to 1 scale)
            - mitigation_suggestions: Remediation plan
        """
        # Resolve cycle ID
        cycle_id = self._resolve_cycle_id(cycle)
        if not cycle_id:
            return {"error": "Cycle not found", "cycle": cycle}

        # Load evaluation data
        df = self.bias_detector.load_evaluations_as_dataframe(cycle_id)

        if df.empty:
            return {"error": "No evaluation data found", "cycle_id": cycle_id}

        # Generate all components
        rater_scores = self.calculate_rater_fairness_scores(cycle_id, df)
        heat_map = self.generate_bias_heatmap(cycle_id, df)
        trends = self.analyze_bias_trends(cycle_id, df)
        mitigation = self.generate_bias_remediation_plan(cycle_id, df)

        return {
            "cycle_id": cycle_id,
            "cycle_code": self._get_cycle_code(cycle_id),
            "rater_bias_scores": rater_scores,
            "department_bias_heat_map": heat_map,
            "trend_analysis": trends,
            "mitigation_suggestions": mitigation,
            "generated_at": datetime.utcnow().isoformat(),
            "summary": self._generate_summary(rater_scores, heat_map, trends),
        }

    def calculate_rater_fairness_scores(self, cycle_id: int, df: Optional[pd.DataFrame] = None) -> Dict:
        """
        Calculate fairness scores for each rater.

        Returns:
            Dictionary with rater email as key and fairness metrics as value.
            Fairness score: 0-1 scale (1 = most fair, 0 = most biased)
        """
        if df is None:
            df = self.bias_detector.load_evaluations_as_dataframe(cycle_id)

        if df.empty or "rater_id" not in df.columns:
            return {"error": "Insufficient data for rater analysis"}

        rater_scores = {}

        # Get harshness/leniency bias
        harshness_result = self.bias_detector.detect_harshness_bias(cycle_id)
        rater_bias_data = harshness_result.get("rater_bias", {})

        # Get similarity bias (halo effect)
        similarity_result = self.bias_detector.detect_similarity_bias(cycle_id)
        bias_flags = {f.get("rater_id"): f for f in similarity_result.get("bias_flags", [])}

        # Calculate fairness for each rater
        for rater_id in df["rater_id"].unique():
            rater_data = df[df["rater_id"] == rater_id]

            if len(rater_data) < 2:
                continue

            # Base fairness score starts at 1.0
            fairness_score = 1.0
            issues = []

            # 1. Harshness/Leniency check
            bias_info = rater_bias_data.get(rater_id, {})
            if bias_info:
                bias_value = abs(bias_info.get("bias", 0))
                if bias_value > 0.5:
                    # Penalize for harshness or leniency
                    penalty = min(bias_value / 2.0, 0.3)  # Max 0.3 penalty
                    fairness_score -= penalty
                    issues.append(
                        {
                            "type": "harshness" if bias_info.get("bias", 0) < 0 else "leniency",
                            "severity": "high" if bias_value > 1.0 else "medium",
                            "bias_value": float(bias_info.get("bias", 0)),
                        }
                    )

            # 2. Halo effect check (low variance)
            halo_flag = bias_flags.get(rater_id)
            if halo_flag:
                variance = halo_flag.get("variance", 1.0)
                if variance < 0.5:
                    penalty = (0.5 - variance) / 0.5 * 0.2  # Max 0.2 penalty
                    fairness_score -= penalty
                    issues.append(
                        {"type": "halo_effect", "severity": halo_flag.get("severity", "medium"), "variance": float(variance)}
                    )

            # 3. Rating distribution check
            scores = rater_data["score"].tolist()
            score_std = np.std(scores)
            score_mean = np.mean(scores)

            # Check for centrality bias (all ratings similar)
            if score_std < 0.3:
                penalty = (0.3 - score_std) / 0.3 * 0.15  # Max 0.15 penalty
                fairness_score -= penalty
                issues.append({"type": "centrality_bias", "severity": "medium", "std": float(score_std)})

            # 4. Consistency check (compare with other raters for same targets)
            consistency_score = self._calculate_rater_consistency(rater_id, df)
            if consistency_score < 0.7:
                penalty = (0.7 - consistency_score) * 0.2  # Max 0.2 penalty
                fairness_score -= penalty
                issues.append({"type": "low_consistency", "severity": "medium", "consistency": float(consistency_score)})

            # Ensure score is between 0 and 1
            fairness_score = max(0.0, min(1.0, fairness_score))

            rater_scores[rater_id] = {
                "fairness_score": float(fairness_score),
                "fairness_rating": self._score_to_rating(fairness_score),
                "evaluation_count": len(rater_data),
                "mean_rating": float(score_mean),
                "std_rating": float(score_std),
                "issues": issues,
                "bias_info": bias_info,
            }

        return rater_scores

    def generate_bias_heatmap(self, cycle_id: int, df: Optional[pd.DataFrame] = None) -> Dict:
        """
        Generate department bias heat map.

        Returns:
            Dictionary with heat map data showing bias by department/segment.
            Values range from -1 (high negative bias) to 1 (high positive bias).
        """
        if df is None:
            df = self.bias_detector.load_evaluations_as_dataframe(cycle_id)

        if df.empty:
            return {"error": "No data available"}

        # Get department bias analysis
        dept_bias = self.bias_detector._detect_department_bias_from_df(df)

        if dept_bias.get("status") != "analyzed":
            return {"error": "Insufficient department data", "status": dept_bias.get("status")}

        departments = dept_bias.get("departments", {})
        overall_mean = dept_bias.get("overall_mean", 0)
        significant_deviations = dept_bias.get("significant_deviations", {})

        # Build heat map data
        heat_map = {}
        max_deviation = 0

        for dept, stats in departments.items():
            dept_mean = stats.get("mean", overall_mean)
            deviation = dept_mean - overall_mean

            # Normalize to -1 to 1 scale
            # Assuming max deviation of 2.0 points on a 5-point scale
            normalized_bias = max(-1.0, min(1.0, deviation / 2.0))

            max_deviation = max(max_deviation, abs(deviation))

            heat_map[dept] = {
                "bias_score": float(normalized_bias),  # -1 to 1
                "mean_rating": float(dept_mean),
                "overall_mean": float(overall_mean),
                "deviation": float(deviation),
                "count": stats.get("count", 0),
                "std": float(stats.get("std", 0)),
                "severity": significant_deviations.get(dept, {}).get("severity", "none"),
                "interpretation": self._interpret_bias_score(normalized_bias),
            }

        return {
            "departments": heat_map,
            "overall_mean": float(overall_mean),
            "max_deviation": float(max_deviation),
            "statistical_test": dept_bias.get("statistical_test"),
            "total_departments": len(heat_map),
        }

    def analyze_bias_trends(self, cycle_id: int, df: Optional[pd.DataFrame] = None) -> Dict:
        """
        Analyze bias trends over time.

        Returns:
            Dictionary with trend analysis on -1 to 1 scale:
            - -1: Strong negative bias trend (bias increasing)
            - 0: No trend (stable)
            - 1: Strong positive trend (bias decreasing/fairness improving)
        """
        if df is None:
            df = self.bias_detector.load_evaluations_as_dataframe(cycle_id)

        if df.empty or "submitted_at" not in df.columns:
            return {"error": "Insufficient temporal data", "trend_score": 0.0, "interpretation": "No trend data available"}

        # Get cycle dates
        cycle = self.db.query(Cycle).filter(Cycle.id == cycle_id).first()
        if not cycle or not cycle.start_date:
            return {"error": "Cycle dates not available", "trend_score": 0.0}

        # Clean and prepare data
        df_clean = df[df["submitted_at"].notna() & df["score"].notna()].copy()
        if len(df_clean) < 10:
            return {"error": "Insufficient data points", "trend_score": 0.0}

        # Convert timestamps
        df_clean["submitted_at"] = pd.to_datetime(df_clean["submitted_at"])
        df_clean = df_clean.sort_values("submitted_at")

        # Divide into time periods (e.g., weeks or thirds of cycle)
        cycle_start = pd.to_datetime(cycle.start_date)
        cycle_end = pd.to_datetime(cycle.end_date) if cycle.end_date else df_clean["submitted_at"].max()
        cycle_duration = (cycle_end - cycle_start).days

        if cycle_duration < 7:
            # Too short, use daily
            periods = ["early", "late"]
            period_days = cycle_duration / 2
        else:
            # Divide into 3 periods
            periods = ["early", "middle", "late"]
            period_days = cycle_duration / 3

        # Calculate bias metrics for each period
        period_metrics = {}

        for i, period in enumerate(periods):
            period_start = cycle_start + timedelta(days=i * period_days)
            period_end = cycle_start + timedelta(days=(i + 1) * period_days)

            if i == len(periods) - 1:
                period_end = cycle_end

            period_data = df_clean[(df_clean["submitted_at"] >= period_start) & (df_clean["submitted_at"] < period_end)]

            if len(period_data) < 3:
                continue

            # Calculate bias indicators for this period
            period_bias = self._calculate_period_bias(period_data)
            period_metrics[period] = period_bias

        # Calculate trend
        if len(period_metrics) < 2:
            return {"error": "Insufficient periods for trend analysis", "trend_score": 0.0}

        # Trend score: negative if bias increasing, positive if decreasing
        trend_score = self._calculate_trend_score(period_metrics)

        return {
            "bias_trends": period_metrics,
            "trend_score": float(trend_score),  # -1 to 1
            "interpretation": self._interpret_trend(trend_score),
            "periods_analyzed": len(period_metrics),
            "overall_direction": "improving" if trend_score > 0.1 else "worsening" if trend_score < -0.1 else "stable",
        }

    def generate_bias_remediation_plan(self, cycle_id: int, df: Optional[pd.DataFrame] = None) -> Dict:
        """
        Generate bias remediation plan with specific mitigation suggestions.

        Returns:
            Dictionary with prioritized mitigation actions.
        """
        if df is None:
            df = self.bias_detector.load_evaluations_as_dataframe(cycle_id)

        # Get comprehensive bias report
        complete_report = self.complete_detector.generate_complete_report(cycle_id)

        # Get rater scores
        rater_scores = self.calculate_rater_fairness_scores(cycle_id, df)

        # Get department heat map
        heat_map = self.generate_bias_heatmap(cycle_id, df)

        # Build remediation plan
        remediation_plan = {
            "priority_actions": [],
            "rater_training_needs": [],
            "department_interventions": [],
            "systemic_recommendations": [],
            "timeline": {},
        }

        # 1. Priority actions based on findings
        findings = complete_report.findings
        findings_by_severity = defaultdict(list)
        for finding in findings:
            findings_by_severity[finding.severity].append(finding)

        # Critical and high severity findings
        critical_findings = findings_by_severity.get("critical", []) + findings_by_severity.get("high", [])

        for finding in critical_findings[:5]:  # Top 5
            remediation_plan["priority_actions"].append(
                {
                    "action": finding.recommendations[0] if finding.recommendations else f"Address {finding.bias_type}",
                    "bias_type": finding.bias_type,
                    "severity": finding.severity,
                    "affected_count": len(finding.affected_raters) + len(finding.affected_targets),
                    "urgency": "high" if finding.severity in ["critical", "high"] else "medium",
                }
            )

        # 2. Rater-specific training needs
        low_fairness_raters = [
            (rater_id, data) for rater_id, data in rater_scores.items() if data.get("fairness_score", 1.0) < 0.7
        ]
        low_fairness_raters.sort(key=lambda x: x[1].get("fairness_score", 1.0))

        for rater_id, data in low_fairness_raters[:10]:  # Top 10
            issues = data.get("issues", [])
            training_needs = []

            for issue in issues:
                if issue["type"] == "harshness":
                    training_needs.append("Calibration training - harshness bias")
                elif issue["type"] == "leniency":
                    training_needs.append("Calibration training - leniency bias")
                elif issue["type"] == "halo_effect":
                    training_needs.append("Differentiated evaluation training")
                elif issue["type"] == "centrality_bias":
                    training_needs.append("Full scale usage training")

            if training_needs:
                remediation_plan["rater_training_needs"].append(
                    {
                        "rater_id": rater_id,
                        "fairness_score": data.get("fairness_score"),
                        "training_needs": list(set(training_needs)),
                        "priority": "high" if data.get("fairness_score", 1.0) < 0.5 else "medium",
                    }
                )

        # 3. Department interventions
        departments = heat_map.get("departments", {})
        biased_departments = [(dept, data) for dept, data in departments.items() if abs(data.get("bias_score", 0)) > 0.3]
        biased_departments.sort(key=lambda x: abs(x[1].get("bias_score", 0)), reverse=True)

        for dept, data in biased_departments:
            bias_score = data.get("bias_score", 0)
            intervention = {
                "department": dept,
                "bias_score": bias_score,
                "severity": data.get("severity", "medium"),
                "recommendations": [],
            }

            if bias_score > 0.3:
                intervention["recommendations"].append(
                    f"Review evaluation criteria - {dept} shows positive bias (higher ratings)"
                )
            elif bias_score < -0.3:
                intervention["recommendations"].append(
                    f"Review evaluation criteria - {dept} shows negative bias (lower ratings)"
                )

            intervention["recommendations"].append("Conduct department-wide calibration session")
            intervention["recommendations"].append("Review evaluation distribution and ensure balanced assignments")

            remediation_plan["department_interventions"].append(intervention)

        # 4. Systemic recommendations
        overall_bias_score = complete_report.overall_bias_score

        if overall_bias_score > 0.5:
            remediation_plan["systemic_recommendations"].extend(
                [
                    "Implement mandatory rater calibration training",
                    "Establish evaluation review committee",
                    "Create bias monitoring dashboard",
                    "Regular bias audits and reporting",
                ]
            )
        elif overall_bias_score > 0.3:
            remediation_plan["systemic_recommendations"].extend(
                [
                    "Provide optional rater calibration training",
                    "Quarterly bias reviews",
                    "Bias awareness training for all evaluators",
                ]
            )
        else:
            remediation_plan["systemic_recommendations"].extend(
                ["Maintain current evaluation standards", "Continue monitoring bias metrics", "Annual bias review"]
            )

        # 5. Timeline
        remediation_plan["timeline"] = {
            "immediate": [a["action"] for a in remediation_plan["priority_actions"][:2]],
            "short_term": [a["action"] for a in remediation_plan["priority_actions"][2:5]],
            "medium_term": [
                "Complete rater training programs",
                "Implement department interventions",
                "Establish monitoring systems",
            ],
            "long_term": remediation_plan["systemic_recommendations"],
        }

        return remediation_plan

    # Helper methods

    def _resolve_cycle_id(self, cycle: str) -> Optional[int]:
        """Resolve cycle ID from string or int"""
        if isinstance(cycle, int):
            return cycle

        # Try to find by code
        cycle_obj = self.db.query(Cycle).filter(Cycle.code == cycle).first()
        if cycle_obj:
            return cycle_obj.id

        # Try to parse as int
        try:
            return int(cycle)
        except:
            return None

    def _get_cycle_code(self, cycle_id: int) -> str:
        """Get cycle code from ID"""
        cycle = self.db.query(Cycle).filter(Cycle.id == cycle_id).first()
        return cycle.code if cycle else str(cycle_id)

    def _calculate_rater_consistency(self, rater_id: str, df: pd.DataFrame) -> float:
        """Calculate how consistent a rater is compared to others rating the same targets"""
        rater_data = df[df["rater_id"] == rater_id]

        if len(rater_data) < 2:
            return 1.0

        consistency_scores = []

        for target_id in rater_data["target_id"].unique():
            target_data = df[df["target_id"] == target_id]

            if len(target_data) < 2:
                continue

            rater_rating = rater_data[rater_data["target_id"] == target_id]["score"].iloc[0]
            other_ratings = target_data[target_data["rater_id"] != rater_id]["score"]

            if len(other_ratings) > 0:
                other_mean = other_ratings.mean()
                # Consistency: how close is this rater to others (1.0 = perfect, 0.0 = far off)
                diff = abs(rater_rating - other_mean)
                consistency = max(0.0, 1.0 - diff / 2.0)  # Assuming max diff of 2.0
                consistency_scores.append(consistency)

        return np.mean(consistency_scores) if consistency_scores else 1.0

    def _calculate_period_bias(self, period_data: pd.DataFrame) -> Dict:
        """Calculate bias metrics for a time period"""
        if len(period_data) < 3:
            return {"bias_score": 0.0}

        # Calculate multiple bias indicators
        scores = period_data["score"].tolist()

        # 1. Variance (low = halo effect)
        variance = np.var(scores)
        variance_score = min(1.0, variance / 0.5)  # Normalize

        # 2. Distribution (check for centrality)
        std = np.std(scores)
        expected_std = 1.29  # For uniform 1-5 scale
        distribution_score = min(1.0, std / expected_std)

        # 3. Department balance (if available)
        dept_balance = 1.0
        if "department" in period_data.columns:
            dept_counts = period_data["department"].value_counts()
            if len(dept_counts) > 1:
                # Check balance
                cv = dept_counts.std() / dept_counts.mean() if dept_counts.mean() > 0 else 0
                dept_balance = max(0.0, 1.0 - cv)

        # Composite bias score (lower = more bias)
        bias_score = variance_score * 0.4 + distribution_score * 0.4 + dept_balance * 0.2

        return {
            "bias_score": float(bias_score),
            "mean_rating": float(np.mean(scores)),
            "std_rating": float(std),
            "variance": float(variance),
            "count": len(scores),
        }

    def _calculate_trend_score(self, period_metrics: Dict) -> float:
        """Calculate trend score from period metrics (-1 to 1)"""
        if len(period_metrics) < 2:
            return 0.0

        periods = sorted(period_metrics.keys())
        bias_scores = [period_metrics[p].get("bias_score", 0.5) for p in periods]

        # Calculate trend: if bias_score is increasing, bias is decreasing (good trend)
        # If bias_score is decreasing, bias is increasing (bad trend)
        # Use linear regression slope
        n = len(bias_scores)
        x = np.arange(n)
        y = np.array(bias_scores)

        if n < 2:
            return 0.0

        # Calculate slope
        slope = np.polyfit(x, y, 1)[0]

        # Normalize to -1 to 1
        # Positive slope (bias_score increasing) = good trend (positive)
        # Negative slope (bias_score decreasing) = bad trend (negative)
        trend_score = max(-1.0, min(1.0, slope * 2.0))

        return float(trend_score)

    def _score_to_rating(self, score: float) -> str:
        """Convert fairness score to rating"""
        if score >= 0.9:
            return "excellent"
        elif score >= 0.7:
            return "good"
        elif score >= 0.5:
            return "fair"
        elif score >= 0.3:
            return "needs_improvement"
        else:
            return "poor"

    def _interpret_bias_score(self, score: float) -> str:
        """Interpret bias score (-1 to 1)"""
        if score > 0.3:
            return "positive_bias"
        elif score < -0.3:
            return "negative_bias"
        else:
            return "neutral"

    def _interpret_trend(self, trend_score: float) -> str:
        """Interpret trend score"""
        if trend_score > 0.3:
            return "Bias decreasing - fairness improving over time"
        elif trend_score < -0.3:
            return "Bias increasing - fairness declining over time"
        else:
            return "Stable - no significant trend detected"

    def _generate_summary(self, rater_scores: Dict, heat_map: Dict, trends: Dict) -> Dict:
        """Generate executive summary"""
        # Rater summary
        fairness_scores = [data.get("fairness_score", 1.0) for data in rater_scores.values()]
        avg_fairness = np.mean(fairness_scores) if fairness_scores else 1.0
        low_fairness_count = sum(1 for s in fairness_scores if s < 0.7)

        # Department summary
        dept_bias_scores = [abs(data.get("bias_score", 0)) for data in heat_map.get("departments", {}).values()]
        max_dept_bias = max(dept_bias_scores) if dept_bias_scores else 0.0
        biased_dept_count = sum(1 for s in dept_bias_scores if s > 0.3)

        # Trend summary
        trend_score = trends.get("trend_score", 0.0)

        return {
            "overall_fairness": float(avg_fairness),
            "raters_needing_training": low_fairness_count,
            "total_raters": len(rater_scores),
            "max_department_bias": float(max_dept_bias),
            "biased_departments": biased_dept_count,
            "trend_direction": trends.get("overall_direction", "stable"),
            "trend_score": float(trend_score),
            "overall_assessment": self._get_overall_assessment(avg_fairness, max_dept_bias, trend_score),
        }

    def _get_overall_assessment(self, avg_fairness: float, max_dept_bias: float, trend_score: float) -> str:
        """Get overall assessment"""
        if avg_fairness >= 0.8 and max_dept_bias < 0.3 and trend_score > 0:
            return "excellent"
        elif avg_fairness >= 0.7 and max_dept_bias < 0.5:
            return "good"
        elif avg_fairness >= 0.5:
            return "fair"
        else:
            return "needs_attention"
