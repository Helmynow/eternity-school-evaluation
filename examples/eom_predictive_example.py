"""
Example usage of the EOMPredictiveModel class.

This demonstrates how to:
1. Initialize the model
2. Make predictions for candidates
3. Train the model on historical data
"""
from ai_models.eom_predictive_model import EOMPredictiveModel
from backend.database import get_db_session


def example_basic_prediction():
    """Example of making a basic prediction with pre-calculated features."""
    
    # Initialize model (without database - using provided features)
    model = EOMPredictiveModel()
    
    # Candidate data with pre-calculated features
    candidate_data = {
        'email': 'john.doe@example.com',
        'cycle_id': 1,
        'nomination_count': 3,
        'academic_term_performance': 4.5,  # Out of 5.0
        'peer_feedback_score': 4.2,
        'manager_rating': 4.8,
        'bias_score': 0.2,  # Low bias (good)
        'rating_consistency': 0.3,  # Low std dev (consistent)
        'context_diversity': 4,  # Evaluated by 4 different contexts
        'evaluation_count': 8,
        'response_rate': 0.9,  # 90% response rate
        'comment_engagement': 6,  # 6 evaluations had comments
        'cross_context_recognition': 3  # 3 contexts gave high ratings
    }
    
    # Make prediction
    result = model.predict_winning_probability(candidate_data)
    
    print("Prediction Result:")
    print(f"  Probability: {result['probability']:.1%}")
    print(f"  Category: {result['predicted_category']}")
    print(f"  Confidence: {result['confidence']}")
    
    return result


def example_database_prediction(db_session):
    """Example of making a prediction using database to calculate features."""
    
    # Initialize model with database session
    model = EOMPredictiveModel(db_session=db_session)
    
    # Minimal candidate data - model will calculate features from database
    candidate_data = {
        'email': 'jane.smith@example.com',
        'cycle_id': 1
    }
    
    # Make prediction (features will be calculated from database)
    result = model.predict_winning_probability(candidate_data)
    
    print("Prediction Result (from database):")
    print(f"  Probability: {result['probability']:.1%}")
    print(f"  Category: {result['predicted_category']}")
    print(f"  Confidence: {result['confidence']}")
    
    return result


def example_training():
    """Example of training the model on historical data."""
    
    model = EOMPredictiveModel()
    
    # Historical training data (example)
    training_data = [
        {
            'email': 'candidate1@example.com',
            'cycle_id': 1,
            'nomination_count': 5,
            'academic_term_performance': 4.8,
            'peer_feedback_score': 4.5,
            'manager_rating': 4.9,
            'bias_score': 0.1,
            'rating_consistency': 0.2,
            'context_diversity': 5,
            'evaluation_count': 10,
            'response_rate': 1.0,
            'comment_engagement': 8,
            'cross_context_recognition': 5
        },
        {
            'email': 'candidate2@example.com',
            'cycle_id': 1,
            'nomination_count': 1,
            'academic_term_performance': 3.5,
            'peer_feedback_score': 3.2,
            'manager_rating': 3.8,
            'bias_score': 0.5,
            'rating_consistency': 0.8,
            'context_diversity': 2,
            'evaluation_count': 4,
            'response_rate': 0.6,
            'comment_engagement': 1,
            'cross_context_recognition': 1
        },
        # Add more training examples...
    ]
    
    # Labels: 1 = won EOM, 0 = did not win
    labels = [1, 0]  # candidate1 won, candidate2 did not
    
    # Train the model
    training_results = model.train(training_data, labels)
    
    print("Training Results:")
    print(f"  Training Accuracy: {training_results['train_accuracy']:.1%}")
    print(f"  Validation Accuracy: {training_results['validation_accuracy']:.1%}")
    print("\nFeature Importance:")
    for feature, importance in sorted(
        training_results['feature_importance'].items(),
        key=lambda x: x[1],
        reverse=True
    ):
        print(f"  {feature}: {importance:.3f}")
    
    return training_results


def example_batch_prediction(db_session, cycle_id: int):
    """Example of predicting probabilities for multiple candidates."""
    
    model = EOMPredictiveModel(db_session=db_session)
    
    # Get all nominees for a cycle (you would query from database)
    # This is a simplified example
    nominees = [
        {'email': 'candidate1@example.com', 'cycle_id': cycle_id},
        {'email': 'candidate2@example.com', 'cycle_id': cycle_id},
        {'email': 'candidate3@example.com', 'cycle_id': cycle_id},
    ]
    
    # Predict for each candidate
    predictions = []
    for nominee in nominees:
        result = model.predict_winning_probability(nominee)
        predictions.append({
            'email': nominee['email'],
            **result
        })
    
    # Sort by probability
    predictions.sort(key=lambda x: x['probability'], reverse=True)
    
    print("Batch Predictions (sorted by probability):")
    for i, pred in enumerate(predictions, 1):
        print(f"{i}. {pred['email']}")
        print(f"   Probability: {pred['probability']:.1%}")
        print(f"   Category: {pred['predicted_category']}")
        print(f"   Confidence: {pred['confidence']}")
    
    return predictions


if __name__ == '__main__':
    # Example 1: Basic prediction with provided features
    print("=" * 60)
    print("Example 1: Basic Prediction")
    print("=" * 60)
    example_basic_prediction()
    
    # Example 2: Training the model
    print("\n" + "=" * 60)
    print("Example 2: Training the Model")
    print("=" * 60)
    example_training()
    
    # Example 3: Database-based prediction (requires database connection)
    # print("\n" + "=" * 60)
    # print("Example 3: Database-based Prediction")
    # print("=" * 60)
    # db = get_db_session()
    # example_database_prediction(db)
    # db.close()
