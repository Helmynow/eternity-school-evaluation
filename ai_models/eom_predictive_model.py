"""
EOM (Employee of the Month) Predictive Model
Uses machine learning to predict the probability of a candidate winning EOM.
"""
import numpy as np
from typing import Dict, List, Optional, Tuple
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from collections import defaultdict
from backend.database import Person, Evaluation, Assignment, Cycle, EOMNominee


class EOMPredictiveModel:
    """
    Predictive model for EOM (Employee of the Month) winners.
    Uses multiple features including nomination count, performance metrics,
    bias indicators, and engagement metrics.
    """
    
    features = [
        "nomination_count",
        "academic_term_performance",
        "peer_feedback_score",
        "manager_rating",
        # Bias indicators (expanded)
        "bias_score",
        "rating_consistency",
        "context_diversity",
        # Engagement metrics (expanded)
        "evaluation_count",
        "response_rate",
        "comment_engagement",
        "cross_context_recognition"
    ]
    
    def __init__(self, db_session=None, model=None):
        """
        Initialize the predictive model.
        
        Args:
            db_session: Database session for data retrieval
            model: Pre-trained model (if None, will use default RandomForest)
        """
        self.db = db_session
        self.model = model or RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            class_weight='balanced'
        )
        self.scaler = StandardScaler()
        self.is_trained = False
    
    def extract_features(self, candidate_data: Dict) -> np.ndarray:
        """
        Extract features from candidate data.
        
        Args:
            candidate_data: Dictionary containing candidate information
                Expected keys:
                - email: Candidate email
                - cycle_id: Current cycle ID
                - nomination_count: Number of nominations
                - academic_term_performance: Performance score (0-5)
                - peer_feedback_score: Average peer rating (0-5)
                - manager_rating: Manager's rating (0-5)
                - bias_score: Calculated bias score (0-1, lower is better)
                - rating_consistency: Standard deviation of ratings (lower is better)
                - context_diversity: Number of different evaluation contexts
                - evaluation_count: Total number of evaluations received
                - response_rate: Percentage of evaluations completed
                - comment_engagement: Number of comments received
                - cross_context_recognition: Number of different contexts that rated highly
        
        Returns:
            numpy array of feature values in the order of self.features
        """
        # Extract or calculate each feature
        feature_values = []
        
        for feature in self.features:
            if feature in candidate_data:
                value = candidate_data[feature]
            else:
                # Calculate from database if not provided
                value = self._calculate_feature(feature, candidate_data)
            
            # Handle None/missing values
            if value is None:
                value = 0.0
            
            feature_values.append(float(value))
        
        return np.array(feature_values).reshape(1, -1)
    
    def _calculate_feature(self, feature_name: str, candidate_data: Dict) -> float:
        """
        Calculate a feature value from database if not provided in candidate_data.
        
        Args:
            feature_name: Name of the feature to calculate
            candidate_data: Dictionary with at least 'email' and 'cycle_id'
        
        Returns:
            Calculated feature value
        """
        if not self.db or 'email' not in candidate_data or 'cycle_id' not in candidate_data:
            return 0.0
        
        email = candidate_data['email']
        cycle_id = candidate_data['cycle_id']
        
        # Get evaluations for this candidate in this cycle
        evaluations = self.db.query(Evaluation).join(Assignment).filter(
            Assignment.cycle_id == cycle_id,
            Assignment.target_email == email,
            Evaluation.status == 'submitted',
            Evaluation.rating.isnot(None)
        ).all()
        
        if not evaluations:
            return 0.0
        
        ratings = [float(eval.rating) for eval in evaluations]
        assignments = [
            self.db.query(Assignment).filter(Assignment.id == eval.assignment_id).first()
            for eval in evaluations
        ]
        assignments = [a for a in assignments if a is not None]
        
        if feature_name == "nomination_count":
            # Count EOM nominations
            nominations = self.db.query(EOMNominee).filter(
                EOMNominee.cycle_id == cycle_id,
                EOMNominee.nominee_email == email
            ).count()
            return float(nominations)
        
        elif feature_name == "academic_term_performance":
            # Average rating across all evaluations
            return float(np.mean(ratings)) if ratings else 0.0
        
        elif feature_name == "peer_feedback_score":
            # Average rating from peer reviews
            peer_ratings = [
                float(eval.rating) for eval, assignment in zip(evaluations, assignments)
                if assignment and assignment.rater_context == 'peer_review'
            ]
            return float(np.mean(peer_ratings)) if peer_ratings else 0.0
        
        elif feature_name == "manager_rating":
            # Average rating from manager reviews
            manager_ratings = [
                float(eval.rating) for eval, assignment in zip(evaluations, assignments)
                if assignment and assignment.rater_context == 'manager_review'
            ]
            return float(np.mean(manager_ratings)) if manager_ratings else 0.0
        
        elif feature_name == "bias_score":
            # Calculate bias score (lower is better, 0-1 scale)
            # Based on rating variance and context distribution
            if len(ratings) < 2:
                return 0.5  # Neutral if insufficient data
            
            rating_std = float(np.std(ratings))
            # Normalize to 0-1 (assuming max std of 2.0 for 5-point scale)
            bias_score = min(rating_std / 2.0, 1.0)
            return bias_score
        
        elif feature_name == "rating_consistency":
            # Standard deviation of ratings (lower is better)
            return float(np.std(ratings)) if len(ratings) > 1 else 0.0
        
        elif feature_name == "context_diversity":
            # Number of different evaluation contexts
            contexts = set(
                assignment.rater_context for assignment in assignments
                if assignment and assignment.rater_context
            )
            return float(len(contexts))
        
        elif feature_name == "evaluation_count":
            # Total number of evaluations
            return float(len(evaluations))
        
        elif feature_name == "response_rate":
            # Percentage of assigned evaluations that were completed
            total_assignments = self.db.query(Assignment).filter(
                Assignment.cycle_id == cycle_id,
                Assignment.target_email == email
            ).count()
            if total_assignments == 0:
                return 0.0
            return float(len(evaluations)) / float(total_assignments)
        
        elif feature_name == "comment_engagement":
            # Number of evaluations with comments
            comments_count = sum(
                1 for eval in evaluations if eval.comments and len(eval.comments.strip()) > 0
            )
            return float(comments_count)
        
        elif feature_name == "cross_context_recognition":
            # Number of different contexts that gave high ratings (>= 4.0)
            high_rating_contexts = set()
            for eval, assignment in zip(evaluations, assignments):
                if assignment and float(eval.rating) >= 4.0:
                    high_rating_contexts.add(assignment.rater_context)
            return float(len(high_rating_contexts))
        
        return 0.0
    
    def predict_winning_probability(self, candidate_data: Dict) -> Dict:
        """
        Predict the probability of a candidate winning EOM.
        
        Args:
            candidate_data: Dictionary containing candidate information
                Must include at least 'email' and 'cycle_id'
                Can optionally include pre-calculated feature values
        
        Returns:
            Dictionary with:
            - probability: Winning probability (0-1 scale, rounded to 3 decimals)
            - predicted_category: Predicted category ('high', 'medium', 'low')
            - confidence: Confidence level ('high', 'medium', 'low')
        """
        if not self.is_trained:
            # If model not trained, use a simple heuristic-based prediction
            return self._heuristic_prediction(candidate_data)
        
        # Extract features
        features = self.extract_features(candidate_data)
        
        # Scale features if scaler was fitted
        if hasattr(self.scaler, 'mean_'):
            features = self.scaler.transform(features)
        
        # Get probability prediction
        try:
            probability = self.model.predict_proba(features)[0][1]  # Probability of class 1 (winning)
        except (AttributeError, IndexError):
            # Fallback if model doesn't support predict_proba or has issues
            probability = self._heuristic_prediction(candidate_data)['probability']
        
        # Determine predicted category
        predicted_category = self._determine_category(probability)
        
        # Calculate confidence
        confidence = self._calculate_confidence(probability, candidate_data)
        
        return {
            'probability': round(probability, 3),
            'predicted_category': predicted_category,
            'confidence': confidence
        }
    
    def _determine_category(self, probability: float) -> str:
        """
        Determine predicted category based on probability.
        
        Args:
            probability: Winning probability (0-1)
        
        Returns:
            Category string: 'high', 'medium', or 'low'
        """
        if probability >= 0.7:
            return 'high'
        elif probability >= 0.4:
            return 'medium'
        else:
            return 'low'
    
    def _calculate_confidence(self, probability: float, candidate_data: Dict) -> str:
        """
        Calculate confidence level based on probability and data quality.
        
        Args:
            probability: Winning probability (0-1)
            candidate_data: Candidate data dictionary
        
        Returns:
            Confidence level: 'high', 'medium', or 'low'
        """
        # Confidence is higher when probability is extreme (very high or very low)
        # and when we have more data
        evaluation_count = candidate_data.get('evaluation_count', 0)
        if isinstance(evaluation_count, (int, float)) and evaluation_count > 0:
            data_quality_score = min(evaluation_count / 10.0, 1.0)
        else:
            data_quality_score = 0.5
        
        # Probability extremity (closer to 0 or 1 = more confident)
        probability_extremity = max(probability, 1 - probability)
        
        # Combined confidence score
        confidence_score = (probability_extremity * 0.6) + (data_quality_score * 0.4)
        
        if confidence_score >= 0.7:
            return 'high'
        elif confidence_score >= 0.5:
            return 'medium'
        else:
            return 'low'
    
    def _heuristic_prediction(self, candidate_data: Dict) -> Dict:
        """
        Fallback heuristic-based prediction when model is not trained.
        
        Args:
            candidate_data: Candidate data dictionary
        
        Returns:
            Dictionary with probability, predicted_category, and confidence
        """
        # Simple heuristic based on key metrics
        nomination_count = candidate_data.get('nomination_count', 0) or 0
        academic_term_performance = candidate_data.get('academic_term_performance', 0) or 0
        peer_feedback_score = candidate_data.get('peer_feedback_score', 0) or 0
        manager_rating = candidate_data.get('manager_rating', 0) or 0
        
        # Normalize to 0-1 scale (assuming 0-5 rating scale)
        performance_score = (academic_term_performance / 5.0) * 0.3
        peer_score = (peer_feedback_score / 5.0) * 0.3
        manager_score = (manager_rating / 5.0) * 0.2
        nomination_score = min(nomination_count / 5.0, 1.0) * 0.2  # Cap nominations at 5
        
        probability = performance_score + peer_score + manager_score + nomination_score
        probability = max(0.0, min(1.0, probability))  # Clamp to [0, 1]
        
        predicted_category = self._determine_category(probability)
        confidence = self._calculate_confidence(probability, candidate_data)
        
        return {
            'probability': round(probability, 3),
            'predicted_category': predicted_category,
            'confidence': confidence
        }
    
    def train(self, training_data: List[Dict], labels: List[int]) -> Dict:
        """
        Train the predictive model on historical data.
        
        Args:
            training_data: List of candidate data dictionaries
            labels: List of binary labels (1 = won EOM, 0 = did not win)
        
        Returns:
            Dictionary with training metrics:
            - train_accuracy: Training accuracy score
            - validation_accuracy: Validation accuracy score
            - feature_importance: Dictionary mapping feature names to importance scores
        """
        if len(training_data) != len(labels):
            raise ValueError("training_data and labels must have the same length")
        
        # Extract features for all training samples
        X = np.array([
            self.extract_features(candidate_data).flatten()
            for candidate_data in training_data
        ])
        y = np.array(labels)
        
        # Split data for validation
        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_val_scaled = self.scaler.transform(X_val)
        
        # Train model
        self.model.fit(X_train_scaled, y_train)
        
        # Calculate training accuracy
        train_score = self.model.score(X_train_scaled, y_train)
        val_score = self.model.score(X_val_scaled, y_val)
        
        self.is_trained = True
        
        return {
            'train_accuracy': round(train_score, 3),
            'validation_accuracy': round(val_score, 3),
            'feature_importance': dict(zip(self.features, self.model.feature_importances_))
        }
