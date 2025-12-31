"""
Weight Matrix Calculator for Eternity School Evaluation System.
Simplified calculator for applying weight matrix rules to evaluation scores.
"""
import numpy as np
from typing import Dict, List, Optional
import logging
from backend.weight_matrix_handler import WeightMatrixHandler


class WeightMatrixCalculator:
    """
    Calculator for applying Eternity School weight matrix rules to evaluation scores.
    
    This class provides a simplified interface for calculating weighted evaluations
    based on target group and rater context.
    """
    
    def __init__(self, weight_matrix_config: Optional[Dict] = None):
        """
        Initialize the weight matrix calculator.
        
        Args:
            weight_matrix_config: Dictionary with structure:
                {
                    'target_group': {
                        'rater_context': weight_value
                    }
                }
                Example:
                {
                    'academic': {
                        'CEO': 1.0,
                        'P&C': 0.8,
                        'QA': 0.9
                    },
                    'admin': {
                        'CEO': 1.0,
                        'P&C': 0.9,
                        'QA': 0.7
                    }
                }
                If None, uses default weight matrix from WeightMatrixHandler
        """
        if weight_matrix_config is None:
            # Use default weight matrix from WeightMatrixHandler
            self.config = WeightMatrixHandler.DEFAULT_WEIGHT_MATRIX.copy()
        else:
            self.config = weight_matrix_config
        self.logger = logging.getLogger(__name__)
    
    def calculate_weighted_evaluation(
        self, 
        target_group: str, 
        rater_context: str, 
        scores: Dict
    ) -> float:
        """
        Apply Eternity School weight matrix rules to calculate weighted evaluation.
        
        Args:
            target_group: Target group (e.g., 'academic', 'admin', 'peers')
            target_group: Target group identifier
            rater_context: Rater context (e.g., 'CEO', 'P&C', 'QA', 'peer_review')
            scores: Dictionary of scores to weight. Can be:
                - Single score: {'overall': 4.5}
                - Domain scores: {'teaching': 4.0, 'collaboration': 3.5, 'leadership': 4.2}
                - Context scores: {'peer_review': 4.0, 'manager_review': 3.8}
        
        Returns:
            Weighted evaluation score as float
        """
        # Normalize inputs
        target_group = (target_group or 'other').lower()
        rater_context = rater_context or 'peer_review'
        
        # Get weight value for this target group and rater context
        weight_value = self._get_weights(target_group, rater_context, scores)
        
        if weight_value is None:
            self.logger.warning(
                f"No weight found for target_group='{target_group}', "
                f"rater_context='{rater_context}'. Using default weight of 1.0"
            )
            # If no specific weight, use simple average
            return self._simple_average(scores)
        
        # If we have multiple scores, we can either:
        # 1. Apply the weight to the average (simpler)
        # 2. Distribute the weight across scores (more complex)
        # For now, we'll apply the weight to the weighted average of scores
        if len(scores) > 1:
            # Calculate average first, then apply context weight
            avg_score = self._simple_average(scores)
            return avg_score * weight_value
        else:
            # Single score - apply weight directly
            score_value = list(scores.values())[0]
            return score_value * weight_value
    
    def _get_weights(self, target_group: str, rater_context: str, scores: Optional[Dict] = None) -> Optional[float]:
        """
        Get weight value for a specific target group and rater context.
        
        Args:
            target_group: Normalized target group
            rater_context: Rater context
            scores: Optional scores dict to determine if we need to distribute weight
        
        Returns:
            Weight value (float), or None if not found
        """
        # Check if target group exists in config
        if target_group not in self.config:
            # Try to find 'other' as fallback
            if 'other' in self.config:
                target_group = 'other'
            else:
                return None
        
        group_config = self.config[target_group]
        
        # If group_config is a dict with rater_context keys, return the weight value
        if isinstance(group_config, dict):
            if rater_context in group_config:
                return float(group_config[rater_context])
            else:
                # Rater context not found, return None to use defaults
                return None
        
        return None
    
    def apply_weights(self, scores: Dict, weights: Dict) -> float:
        """
        Apply weights to scores and calculate weighted average.
        
        Args:
            scores: Dictionary mapping score names to values
                   Example: {'teaching': 4.0, 'collaboration': 3.5, 'leadership': 4.2}
            weights: Dictionary mapping score names to weights
                    Example: {'teaching': 0.4, 'collaboration': 0.3, 'leadership': 0.3}
                    OR single weight value for all scores
        
        Returns:
            Weighted average score
        """
        if not scores:
            self.logger.warning("No scores provided, returning 0.0")
            return 0.0
        
        # Handle case where weights is a single value
        if isinstance(weights, (int, float)):
            # Apply same weight to all scores
            weight_value = float(weights)
            score_values = list(scores.values())
            weighted_sum = sum(score_values) * weight_value
            return weighted_sum / len(score_values) if score_values else 0.0
        
        # Normalize weights dictionary - ensure all scores have weights
        normalized_weights = {}
        for key in scores.keys():
            if key in weights:
                normalized_weights[key] = weights[key]
            else:
                # Use default weight of 1.0 if not specified
                normalized_weights[key] = 1.0
                self.logger.debug(f"Weight not specified for '{key}', using default 1.0")
        
        # Use numpy for efficient vectorized calculation
        score_values = np.array([scores[key] for key in scores.keys()])
        weight_values = np.array([normalized_weights[key] for key in scores.keys()])
        
        # Calculate weighted average: sum(scores * weights) / sum(weights)
        total_weight = weight_values.sum()
        if total_weight == 0:
            self.logger.warning("Total weight is 0, returning simple average")
            return float(score_values.mean())
        
        weighted_sum = (score_values * weight_values).sum()
        return float(weighted_sum / total_weight)
    
    def _simple_average(self, scores: Dict) -> float:
        """
        Calculate simple average when weights are not available.
        
        Args:
            scores: Dictionary of scores
        
        Returns:
            Simple average of all scores
        """
        if not scores:
            return 0.0
        
        score_values = list(scores.values())
        return float(np.mean(score_values))
    
    def calculate_weighted_evaluation_batch(
        self,
        evaluations: List[Dict]
    ) -> List[Dict]:
        """
        Calculate weighted evaluations for a batch of evaluations.
        
        Args:
            evaluations: List of evaluation dictionaries, each containing:
                - target_group: str
                - rater_context: str
                - scores: Dict
        
        Returns:
            List of dictionaries with calculated weighted scores:
            [
                {
                    'target_group': 'academic',
                    'rater_context': 'CEO',
                    'scores': {...},
                    'weighted_score': 4.2,
                    'weights_applied': {...}
                },
                ...
            ]
        """
        results = []
        
        for eval_data in evaluations:
            target_group = eval_data.get('target_group', 'other')
            rater_context = eval_data.get('rater_context', 'peer_review')
            scores = eval_data.get('scores', {})
            
            # Get weight that was applied
            weight_value = self._get_weights(target_group.lower(), rater_context, scores)
            
            # Calculate weighted score
            weighted_score = self.calculate_weighted_evaluation(
                target_group,
                rater_context,
                scores
            )
            
            results.append({
                'target_group': target_group,
                'rater_context': rater_context,
                'scores': scores,
                'weighted_score': weighted_score,
                'weight_applied': weight_value if weight_value is not None else 1.0
            })
        
        return results
    
    def get_weight(self, target_group: str, rater_context: str) -> float:
        """
        Get the weight value for a specific target group and rater context.
        
        Args:
            target_group: Target group identifier
            rater_context: Rater context identifier
        
        Returns:
            Weight value (defaults to 1.0 if not found)
        """
        target_group = (target_group or 'other').lower()
        rater_context = rater_context or 'peer_review'
        
        if target_group in self.config:
            group_config = self.config[target_group]
            if isinstance(group_config, dict) and rater_context in group_config:
                return float(group_config[rater_context])
        
        # Fallback to 'other' if available
        if 'other' in self.config:
            other_config = self.config['other']
            if isinstance(other_config, dict) and rater_context in other_config:
                return float(other_config[rater_context])
        
        # Default weight
        return 1.0
    
    def update_config(self, target_group: str, rater_context: str, weight: float):
        """
        Update the weight matrix configuration.
        
        Args:
            target_group: Target group identifier
            rater_context: Rater context identifier
            weight: New weight value
        """
        target_group = target_group.lower()
        
        if target_group not in self.config:
            self.config[target_group] = {}
        
        if not isinstance(self.config[target_group], dict):
            self.config[target_group] = {}
        
        self.config[target_group][rater_context] = float(weight)
        self.logger.info(
            f"Updated weight: {target_group}/{rater_context} = {weight}"
        )
    
    def get_config(self) -> Dict:
        """
        Get the current weight matrix configuration.
        
        Returns:
            Copy of the current configuration
        """
        import copy
        return copy.deepcopy(self.config)

