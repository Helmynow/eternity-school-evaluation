"""
Weight matrix calculations for fair evaluation distribution.
Ensures balanced evaluation assignments across different contexts and groups.
"""

from collections import defaultdict
from typing import Dict, List, Tuple

import numpy as np

from backend.database import Assignment, Cycle, Person


class WeightMatrix:
    """Manages weight matrices for evaluation cycles"""

    def __init__(self, cycle_id: int, db_session):
        self.cycle_id = cycle_id
        self.db = db_session
        self.matrix = None
        self.rater_indices = {}
        self.target_indices = {}

    def build_matrix(self) -> np.ndarray:
        """
        Build a weight matrix where:
        - Rows = raters
        - Columns = targets
        - Values = assignment weights
        """
        assignments = self.db.query(Assignment).filter(Assignment.cycle_id == self.cycle_id).all()

        # Get unique raters and targets
        raters = sorted(set(a.rater_email for a in assignments))
        targets = sorted(set(a.target_email for a in assignments))

        # Create index mappings
        self.rater_indices = {email: idx for idx, email in enumerate(raters)}
        self.target_indices = {email: idx for idx, email in enumerate(targets)}

        # Initialize matrix
        matrix = np.zeros((len(raters), len(targets)))

        # Fill matrix with weights
        for assignment in assignments:
            rater_idx = self.rater_indices[assignment.rater_email]
            target_idx = self.target_indices[assignment.target_email]
            matrix[rater_idx, target_idx] = assignment.weight

        self.matrix = matrix
        return matrix

    def calculate_fairness_metrics(self) -> Dict:
        """
        Calculate fairness metrics:
        - Load balance: variance in number of evaluations per rater
        - Coverage: percentage of possible rater-target pairs
        - Distribution: balance across target groups
        """
        if self.matrix is None:
            self.build_matrix()

        metrics = {}

        # Load balance (raters)
        rater_loads = self.matrix.sum(axis=1)
        metrics["rater_load_mean"] = float(np.mean(rater_loads))
        metrics["rater_load_std"] = float(np.std(rater_loads))
        metrics["rater_load_cv"] = float(np.std(rater_loads) / np.mean(rater_loads)) if np.mean(rater_loads) > 0 else 0

        # Load balance (targets)
        target_loads = self.matrix.sum(axis=0)
        metrics["target_load_mean"] = float(np.mean(target_loads))
        metrics["target_load_std"] = float(np.std(target_loads))
        metrics["target_load_cv"] = float(np.std(target_loads) / np.mean(target_loads)) if np.mean(target_loads) > 0 else 0

        # Coverage
        total_possible = self.matrix.size
        assigned = np.count_nonzero(self.matrix)
        metrics["coverage"] = assigned / total_possible if total_possible > 0 else 0

        # Group distribution
        assignments = self.db.query(Assignment).filter(Assignment.cycle_id == self.cycle_id).all()

        group_counts = defaultdict(int)
        for a in assignments:
            group_counts[a.target_group] += 1

        metrics["group_distribution"] = dict(group_counts)

        return metrics

    def optimize_weights(self, target_load: float = None) -> np.ndarray:
        """
        Optimize assignment weights to balance loads.
        Uses iterative proportional fitting to balance rater and target loads.
        """
        if self.matrix is None:
            self.build_matrix()

        matrix = self.matrix.copy()

        # Target loads (how many evaluations each target should receive)
        if target_load is None:
            target_load = matrix.sum(axis=0).mean()

        # Iterative proportional fitting
        max_iterations = 100
        tolerance = 0.01

        for iteration in range(max_iterations):
            # Normalize rows (raters)
            row_sums = matrix.sum(axis=1, keepdims=True)
            row_sums[row_sums == 0] = 1  # Avoid division by zero
            matrix = matrix / row_sums * matrix.sum(axis=1, keepdims=True).mean()

            # Normalize columns (targets)
            col_sums = matrix.sum(axis=0, keepdims=True)
            col_sums[col_sums == 0] = 1
            matrix = matrix / col_sums * target_load

            # Check convergence
            if iteration > 0:
                if np.allclose(matrix, self.matrix, atol=tolerance):
                    break

        return matrix

    def get_imbalanced_assignments(self, threshold: float = 0.3) -> List[Dict]:
        """
        Identify assignments that contribute to imbalance.
        Returns list of assignments that should be adjusted.
        """
        if self.matrix is None:
            self.build_matrix()

        metrics = self.calculate_fairness_metrics()
        imbalanced = []

        # Find raters with high load variance
        rater_loads = self.matrix.sum(axis=1)
        mean_load = np.mean(rater_loads)
        std_load = np.std(rater_loads)

        for rater_email, idx in self.rater_indices.items():
            load = rater_loads[idx]
            if abs(load - mean_load) > threshold * std_load:
                imbalanced.append(
                    {
                        "type": "rater",
                        "email": rater_email,
                        "load": float(load),
                        "expected": float(mean_load),
                        "deviation": float(load - mean_load),
                    }
                )

        # Find targets with high load variance
        target_loads = self.matrix.sum(axis=0)
        mean_target_load = np.mean(target_loads)
        std_target_load = np.std(target_loads)

        for target_email, idx in self.target_indices.items():
            load = target_loads[idx]
            if abs(load - mean_target_load) > threshold * std_target_load:
                imbalanced.append(
                    {
                        "type": "target",
                        "email": target_email,
                        "load": float(load),
                        "expected": float(mean_target_load),
                        "deviation": float(load - mean_target_load),
                    }
                )

        return imbalanced
